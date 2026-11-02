"""Extract plain-text MCQs without guessing missing answers."""
import re
import shutil
import subprocess
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill


def read_word(path):
    path = Path(path)
    if path.suffix.lower() == '.doc':
        if not shutil.which('libreoffice'):
            raise ValueError('Máy chủ chưa có LibreOffice. Hãy Save As thành .docx rồi gửi lại.')
        with tempfile.TemporaryDirectory() as temp:
            subprocess.run(['libreoffice', '-env:UserInstallation=file://' + temp + '/profile',
                            '--headless', '--convert-to', 'docx', '--outdir', temp, str(path)],
                           check=True, timeout=45, capture_output=True)
            return read_word(Path(temp) / (path.stem + '.docx'))
    with zipfile.ZipFile(path) as archive:
        if sum(i.file_size for i in archive.infolist()) > 40_000_000:
            raise ValueError('File giải nén quá lớn (giới hạn 40 MB).')
    doc = Document(path)
    lines = []
    for child in doc.element.body:
        if child.tag == qn('w:p'):
            lines.append(Paragraph(child, doc).text)
        elif child.tag == qn('w:tbl'):
            for row in Table(child, doc).rows:
                seen = set()
                for cell in row.cells:
                    if cell._tc not in seen:
                        seen.add(cell._tc)
                        lines.append(cell.text)
    text = '\n'.join(lines).strip()
    if not text:
        raise ValueError('Không tìm thấy chữ. File ảnh/scan hoặc công thức dạng ảnh chưa được hỗ trợ.')
    if len(text) > 100_000:
        raise ValueError('File quá dài. Hãy chia thành các file dưới 100.000 ký tự.')
    return text


def parse_questions(text):
    # Numbered questions; options may be on one or multiple lines.
    chunks = re.split(r'(?im)^\s*(?:Câu\s*|Question\s*)?\d+\s*[.:)\-]\s*', text)
    rows = []
    for chunk in chunks[1:]:
        parts = re.split(r'(?m)(?:^|[ \t]+)\s*([ABCD])[.)：:]\s*', chunk.strip())
        if len(parts) != 9 or parts[1::2] != list('ABCD'):
            raise ValueError('Cần đúng bốn lựa chọn A–D cho mỗi câu. Thử nút Chuyển bằng Gemini.')
        row = [parts[0].strip()] + [v.strip() for v in parts[2::2]]
        # Do not put answer key in choice D.
        row[-1] = re.split(r'(?im)^\s*(?:Đáp án|Answer)\s*:', row[-1])[0].strip()
        rows.append(row)
    if not rows:
        raise ValueError('Chưa nhận ra câu hỏi đánh số. Thử nút Chuyển bằng Gemini.')
    return validate_rows(rows)


def validate_rows(rows):
    if not isinstance(rows, list) or not 1 <= len(rows) <= 1000:
        raise ValueError('Số câu không hợp lệ (1–1000).')
    for row in rows:
        if not isinstance(row, list) or len(row) != 5 or any(not isinstance(x, str) or not x.strip() or len(x) > 32000 for x in row):
            raise ValueError('Câu hỏi thiếu nội dung hoặc thiếu lựa chọn. Hãy kiểm tra lại file nguồn.')
    return rows


def make_excel(rows):
    validate_rows(rows)
    wb = Workbook()
    ws = wb.active
    ws.title = 'Questions'
    ws.append(['Question', 'A', 'B', 'C', 'D'])
    for row in rows:
        ws.append(row)
        for cell in ws[ws.max_row]:
            cell.data_type = 's'  # Formula injection protection; preserve literal text.
            cell.alignment = Alignment(wrap_text=True, vertical='top')
    for cell in ws[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill('solid', fgColor='16804A')
    ws.column_dimensions['A'].width = 65
    for col in 'BCDE':
        ws.column_dimensions[col].width = 32
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions
    result = BytesIO()
    wb.save(result)
    result.seek(0)
    return result

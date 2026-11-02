# KHAI Telegram Gemini Bot

Bot Python với menu nút bấm bên dưới tin nhắn, menu con, quay lại và phân trang danh sách lịch.

## Chức năng

- **Hỏi Gemini:** gửi tin nhắn bình thường; nhớ 6 lượt trao đổi gần nhất trong RAM. `/new` hoặc nút Xóa hội thoại để xóa ngữ cảnh. Không có tìm kiếm web trực tiếp.
- **Word → Excel:** gửi `.docx` hoặc `.doc`, tối đa 10 MB. Excel có đúng 5 cột: **A=Question, B=A, C=B, D=C, E=D**. Không thêm cột đáp án/giải thích.
- **Lịch hôm nay:** xem các buổi trong ngày theo giờ Việt Nam, đúng thứ và khoảng ngày hiệu lực.
- **Quản lý lịch:** thêm buổi học lặp hằng tuần, xem 5 buổi mỗi trang, xóa có xác nhận. Muốn sửa thì xóa và thêm lại.
- **Nhắc lịch:** bật/tắt, chọn giờ. Nhắc một lần mỗi ngày; thông báo không có lịch nếu hôm đó không có buổi học đã nhập.
- Lịch và cấu hình nhắc lưu SQLite. File Word/Excel chỉ xử lý tạm thời. Không lưu nội dung chat xuống đĩa.
- Chỉ cho phép Telegram ID được cấu hình; chỉ dùng trong chat riêng.

## 1. Tạo bot Telegram

1. Mở đúng tài khoản **@BotFather** trên Telegram.
2. Gửi `/newbot`, nhập tên hiển thị, rồi username kết thúc bằng `bot`.
3. Sao chép token vào biến `TELEGRAM_BOT_TOKEN` trên máy chạy bot. **Không đưa token vào GitHub, ảnh chụp màn hình hoặc tin nhắn chat.**
4. Nếu token lộ, dùng BotFather để thu hồi rồi cấp lại.

## 2. Lấy API key Gemini

1. Mở https://aistudio.google.com/apikey bằng tài khoản Google.
2. Tạo API key và đặt vào biến `GEMINI_API_KEY` trên máy chủ.
3. `GEMINI_MODEL=gemini-flash-latest` là mặc định; có thể thay bằng model mà tài khoản của bạn được phép gọi.
4. Hạn mức và phí phụ thuộc Google/model/tài khoản. Bot không tự thiết lập giới hạn chi phí trên Google.

## 3. Đưa dự án vào GitHub

1. Truy cập https://github.com/new, đặt tên **telegram-gemini-bot**, nên chọn **Private**.
2. Giải nén gói mã nguồn. Upload **nội dung bên trong** thư mục `telegram-gemini-bot` vào gốc repo. `Dockerfile`, `bot.py`, `requirements.txt` phải ở gốc repo.
3. Đưa cả `.github/workflows/tests.yml`, `.gitignore`, `.dockerignore`, `.env.example` lên repo; **không đưa file `.env`** lên.
4. Commit. Tab Actions chạy bộ kiểm thử. Workflow này chỉ kiểm thử, **không phải nơi chạy bot 24/7**.
5. Bạn có thể gửi URL repo cho ChatGPT để tiếp tục cập nhật mã nguồn trực tiếp qua GitHub.

## 4. Chạy 24/7 và tự cập nhật từ GitHub (Railway)

GitHub lưu mã; cần một máy chủ luôn chạy để bot trả lời và nhắc lịch khi bạn tắt máy cá nhân.

1. Đăng nhập https://railway.com, tạo Project → Deploy from GitHub repo, chọn repo bot.
2. Railway dùng `Dockerfile` trong repo. Nếu giao diện yêu cầu loại dịch vụ, chọn dịch vụ chạy liên tục; không dùng cron/serverless sleep.
3. Thêm các **Variables**:

   ```text
   TELEGRAM_BOT_TOKEN=<token từ BotFather>
   GEMINI_API_KEY=<key từ Google AI Studio>
   GEMINI_MODEL=gemini-flash-latest
   ALLOWED_USER_IDS=
   DB_PATH=/data/bot.db
   ```

4. Gắn một **Volume** vào service với mount path **`/data`**. Đây là bước bắt buộc để lịch không mất khi redeploy. Volume không thay thế backup; nên sao lưu định kỳ.
5. Deploy. Khi `ALLOWED_USER_IDS` còn trống, bot chỉ cho dùng `/id`. Mở bot của bạn, gửi `/id`, sao chép số trả về.
6. Điền số đó vào `ALLOWED_USER_IDS`, ví dụ `123456789`. Nhiều người dùng thì ngăn cách bằng dấu phẩy. Redeploy rồi gửi `/start`.
7. Giữ **một instance/replica**, tắt serverless/sleep nếu có. Không chạy bot trên máy cá nhân đồng thời với máy chủ bằng cùng token.
8. Kết nối nhánh `main` của repo làm nguồn deploy; bật autodeploy. Có thể bật **Wait for CI** để chờ kiểm thử trước khi deploy. Push code mới sẽ dựng lại service.
9. Không cần domain, public port hoặc webhook: bot nhận tin bằng long polling.

Railway có thể yêu cầu thanh toán. Kiểm tra giá/hạn mức trên tài khoản trước khi triển khai. Không có máy chủ hoạt động thì bot không nhắc đúng giờ. Sau khi máy chủ hoạt động lại, bot gửi bù lịch **của ngày hiện tại** nếu giờ nhắc đã qua, không gửi bù những ngày cũ.

## 5. Cách dùng các nút

```text
[ 💬 Hỏi Gemini       ] [ 📄 Word → Excel    ]
[ 📅 Lịch hôm nay     ] [ 🗓 Quản lý lịch    ]
[ ⏰ Cài giờ nhắc      ] [ 🧹 Xóa hội thoại   ]
[ ℹ️ Hướng dẫn        ] [ 🔄 Làm mới        ]
```

Nút nằm dưới tin nhắn; bấm mở menu con trong cùng tin nhắn, như video tham chiếu. Màu sắc do giao diện Telegram quyết định. Menu danh sách lịch có nút Trước/Sau khi có nhiều hơn 5 buổi.

### Chuyển Word

- Bấm **Word → Excel → Chuyển thường**, gửi file. Đây là chế độ mặc định, nội dung file không gửi Gemini.
- Mẫu nhận diện ổn định:

  ```text
  Câu 1: Thủ đô của Việt Nam là gì?
  A. Hà Nội
  B. Huế
  C. Đà Nẵng
  D. TP. Hồ Chí Minh
  ```

- Hỗ trợ `Câu 1:`, `Question 1:`, `1.`; A–D cùng dòng hoặc xuống dòng. Chữ trong bảng Word được đọc theo thứ tự hàng, từ trái sang phải.
- Khi bố cục khác: bấm **Dùng Gemini**, rồi gửi lại file. Việc chọn chế độ này đồng ý gửi phần chữ của file cho Google; chế độ được giữ đến khi chọn Chuyển thường hoặc bot khởi động lại.
- AI có thể nhận sai/bỏ sót, nên so số câu và nội dung với file gốc. Bot không tự bịa lựa chọn bị thiếu. Nếu một hàng thiếu lựa chọn, bản chuyển bị từ chối để bạn kiểm tra.
- Không hỗ trợ OCR ảnh/scan, hình vẽ, công thức Word phức tạp, hoặc file khóa mật khẩu. Nội dung không phải chữ thường có thể bị bỏ qua; phải đối chiếu file gốc.
- `.doc` cần LibreOffice: Dockerfile đã cài sẵn. Khi chạy Python trực tiếp trên Windows, hãy dùng `.docx` hoặc cài LibreOffice và đưa lệnh `libreoffice` vào PATH.
- Tối đa 100.000 ký tự chữ/40 MB dữ liệu giải nén/1.000 câu; Gemini có giới hạn đầu ra nên file dài có thể phải chia nhỏ.

### Thêm lịch và bật nhắc

1. **Quản lý lịch → Thêm buổi học**.
2. Gửi 7 trường cách nhau bằng `|`:

   ```text
   5 | 07:00 | 11:00 | Lập trình cơ bản | NDH204 | 2026-11-05 | 2026-11-12
   ```

   Đây là **ví dụ**, không phải thời khóa biểu đã xác nhận. `5` là thứ Năm; `CN` là Chủ nhật. Buổi lặp mỗi tuần từ ngày đầu tới ngày cuối, bao gồm hai đầu mốc. Giờ kết thúc phải sau giờ bắt đầu trong cùng ngày.
3. Các đợt học cách nhau: thêm từng đợt riêng. Các buổi khác giờ/phòng: thêm riêng. Chưa có nhập ảnh thời khóa biểu hoặc tự đồng bộ LMS.
4. **Cài giờ nhắc → Đổi giờ**, gửi `06:00`.
5. Bấm **Bật/Tắt**, kiểm tra trạng thái **BẬT**. Mặc định tắt để tránh gửi ngoài ý muốn.
6. Dùng **Lịch hôm nay** hoặc `/today` để kiểm tra ngay.

Bộ kiểm tra nhắc chạy mỗi 30 giây, nên có thể trễ khoảng 30 giây cộng thời gian mạng. Bot lưu dấu gửi sau khi Telegram xác nhận. Nếu tiến trình chết đúng giữa gửi thành công và ghi SQLite, có khả năng nhắc trùng một lần khi khởi động lại.

## Chạy trên máy tính

Python 3.11+ (khuyến nghị 3.12):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-lock.txt
Copy-Item .env.example .env
# Mở .env và điền giá trị, không commit .env.
python bot.py
```

Tắt cửa sổ terminal hoặc máy tính sẽ dừng bot. Với Docker có thể chạy `docker compose up -d --build`; dữ liệu nằm trong volume `bot-data`.

## Kiểm thử

```sh
python -m unittest discover -s tests -v
```

Kiểm thử không gọi API thật: kiểm tra chuyển câu hỏi, thứ tự bảng Word, cột Excel, chặn công thức, khoảng ngày lịch, cách ly người dùng, lưu qua restart và menu/khởi tạo ứng dụng. Sau triển khai cần thử thêm: `/start`, một câu hỏi Gemini, một file Word, thêm lịch thật và nhắc thực tế.

## Tệp chính

- `bot.py`: Telegram, menu, Gemini, nhắc lịch.
- `converter.py`: Word và Excel.
- `storage.py`: lịch và cài đặt SQLite.
- `Dockerfile`, `compose.yaml`: máy chủ chạy liên tục.
- `.github/workflows/tests.yml`: kiểm thử mỗi push/PR.

## Tài liệu API

- https://googleapis.github.io/python-genai/
- https://core.telegram.org/bots/api
- https://docs.python-telegram-bot.org/en/stable/
- https://docs.railway.com/deployments/github-autodeploys
- https://docs.railway.com/volumes

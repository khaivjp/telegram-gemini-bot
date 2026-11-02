import os
import tempfile
import unittest
from datetime import datetime, date
from pathlib import Path
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo
from docx import Document
from openpyxl import load_workbook
from converter import parse_questions, make_excel, read_word, validate_rows
from storage import Store


class ConverterTests(unittest.TestCase):
    def test_multiline_and_inline(self):
        text = 'Đề kiểm tra\nCâu 1: Thủ đô?\nA. Hà Nội\nB. Huế\nC. Đà Nẵng\nD. HCM\nCâu 2: 1+1? A. 1 B. 2 C. 3 D. 4'
        rows = parse_questions(text)
        self.assertEqual(rows, [['Thủ đô?', 'Hà Nội', 'Huế', 'Đà Nẵng', 'HCM'], ['1+1?', '1', '2', '3', '4']])

    def test_missing_option_rejected(self):
        with self.assertRaises(ValueError):
            parse_questions('1. Q\nA. a\nB. b\nC. c')

    def test_order_in_paragraphs_tables(self):
        with tempfile.TemporaryDirectory() as temp:
            d = Document()
            d.add_paragraph('Câu 1: Q')
            t = d.add_table(rows=1, cols=2)
            t.cell(0, 0).text = 'A. a\nB. b'
            t.cell(0, 1).text = 'C. c\nD. d'
            d.add_paragraph('Câu 2: Q2\nA. a2\nB. b2\nC. c2\nD. d2')
            path = Path(temp) / 'test.docx'
            d.save(path)
            rows = parse_questions(read_word(path))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0], ['Q', 'a', 'b', 'c', 'd'])

    def test_excel_exact_columns_and_literal_formula(self):
        wb = load_workbook(make_excel([['=1+1', '+a', '-b', '@c', 'd']]))
        ws = wb.active
        self.assertEqual(ws.max_column, 5)
        self.assertEqual([c.value for c in ws[1]], ['Question', 'A', 'B', 'C', 'D'])
        self.assertEqual(ws['A2'].value, '=1+1')
        self.assertEqual(ws['A2'].data_type, 's')

    def test_invalid_ai_result(self):
        for rows in [[], [['Q', 'a', 'b', '', 'd']], {'question': 'a'}]:
            with self.assertRaises(ValueError):
                validate_rows(rows)


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / 'bot.db')
        self.s = Store(self.path)
        self.s.add(1, '5 | 07:00 | 11:00 | Python | A1 | 2026-11-05 | 2026-11-12')

    def tearDown(self):
        self.s.db.close()
        self.temp.cleanup()

    def test_range_and_owner_isolation(self):
        for day in (5, 12):
            self.assertEqual(len(self.s.lessons(1, date(2026, 11, day))), 1)
        self.assertEqual(len(self.s.lessons(1, date(2026, 11, 19))), 0)
        self.assertEqual(len(self.s.lessons(2, date(2026, 11, 5))), 0)
        self.s.delete(2, self.s.lessons(1)[0]['id'])
        self.assertEqual(len(self.s.lessons(1)), 1)

    def test_restart_persistence_and_reminder(self):
        self.s.reminder(1, '06:00', True)
        self.s.db.close()
        self.s = Store(self.path)
        tz = ZoneInfo('Asia/Ho_Chi_Minh')
        self.assertFalse(self.s.due(datetime(2026, 11, 5, 5, 59, tzinfo=tz)))
        self.assertEqual(len(self.s.due(datetime(2026, 11, 5, 6, 0, tzinfo=tz))), 1)
        self.s.sent(1, '2026-11-05')
        self.assertFalse(self.s.due(datetime(2026, 11, 5, 8, 0, tzinfo=tz)))
        self.assertEqual(len(self.s.due(datetime(2026, 11, 6, 6, 0, tzinfo=tz))), 1)

    def test_invalid_schedule(self):
        for row in ['9 | 07:00 | 08:00 | Q | R | 2026-11-01 | 2026-12-01',
                    '2 | 11:00 | 07:00 | Q | R | 2026-11-01 | 2026-12-01',
                    '2 | 07:00 | 08:00 | Q | R | 2026-12-01 | 2026-11-01']:
            with self.assertRaises(ValueError):
                self.s.add(1, row)


class AppTests(unittest.TestCase):
    def test_application_build_and_handlers(self):
        from bot import build_app, menu
        with tempfile.TemporaryDirectory() as temp:
            with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': '123456:test-not-real', 'GEMINI_API_KEY': 'test-not-real', 'DB_PATH': temp+'/test.db', 'ALLOWED_USER_IDS': '123'}, clear=True):
                app = build_app()
                self.assertEqual(app.bot_data['allowed'], {123})
                self.assertEqual(len(app.job_queue.jobs()), 1)
                self.assertEqual(len(menu().inline_keyboard), 4)
                app.bot_data['store'].db.close()


class HandlerTests(unittest.IsolatedAsyncioTestCase):
    async def test_menu_navigation(self):
        from types import SimpleNamespace
        from bot import callback
        with tempfile.TemporaryDirectory() as temp:
            store = Store(temp + '/bot.db')
            query = SimpleNamespace(data='add', answer=AsyncMock(), edit_message_text=AsyncMock())
            update = SimpleNamespace(effective_user=SimpleNamespace(id=123),
                effective_chat=SimpleNamespace(type='private'), callback_query=query)
            context = SimpleNamespace(bot_data={'allowed': {123}, 'store': store}, user_data={})
            await callback(update, context)
            self.assertEqual(context.user_data['mode'], 'add')
            query.data = 'home'
            await callback(update, context)
            self.assertNotIn('mode', context.user_data)
            query.data = 'toggle'
            await callback(update, context)
            self.assertEqual(store.user(123)['enabled'], 1)
            store.db.close()

    async def test_chat_response_and_history(self):
        from types import SimpleNamespace
        from bot import text_message
        with tempfile.TemporaryDirectory() as temp:
            store = Store(temp + '/bot.db')
            msg = SimpleNamespace(text='Xin chào', reply_text=AsyncMock(),
                chat=SimpleNamespace(send_action=AsyncMock()))
            update = SimpleNamespace(effective_user=SimpleNamespace(id=123),
                effective_chat=SimpleNamespace(type='private'), message=msg, effective_message=msg)
            context = SimpleNamespace(bot_data={'allowed': {123}, 'store': store}, user_data={})
            with patch('bot.ask_gemini', new=AsyncMock(return_value=SimpleNamespace(text='Chào Khải'))):
                await text_message(update, context)
            msg.reply_text.assert_awaited_with('Chào Khải')
            self.assertEqual(len(context.user_data['history']), 2)
            store.db.close()

    async def test_denied_user_cannot_use_ai(self):
        from types import SimpleNamespace
        from bot import text_message
        msg = SimpleNamespace(text='Test', reply_text=AsyncMock())
        update = SimpleNamespace(effective_user=SimpleNamespace(id=999),
            effective_chat=SimpleNamespace(type='private'), message=msg,
            effective_message=msg, callback_query=None)
        context = SimpleNamespace(bot_data={'allowed': {123}}, user_data={})
        with patch('bot.ask_gemini', new=AsyncMock()) as ai:
            await text_message(update, context)
            ai.assert_not_awaited()


if __name__ == '__main__':
    unittest.main()

import sqlite3
from datetime import date, time
from pathlib import Path


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, reminder TEXT DEFAULT '06:00', enabled INTEGER DEFAULT 0, last_sent TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS lessons (id INTEGER PRIMARY KEY, user_id INTEGER, weekday INTEGER, start TEXT, end TEXT, subject TEXT, room TEXT, since TEXT, until TEXT);
        ''')

    def user(self, uid):
        self.db.execute('INSERT OR IGNORE INTO users(id) VALUES (?)', (uid,))
        self.db.commit()
        return self.db.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()

    def reminder(self, uid, clock=None, enabled=None):
        self.user(uid)
        if clock is not None:
            time.fromisoformat(clock)
            self.db.execute('UPDATE users SET reminder=? WHERE id=?', (clock, uid))
        if enabled is not None:
            self.db.execute('UPDATE users SET enabled=? WHERE id=?', (int(enabled), uid))
        self.db.commit()

    def add(self, uid, message):
        p = [x.strip() for x in message.split('|')]
        if len(p) != 7:
            raise ValueError('Cần 7 mục ngăn bởi dấu | như mẫu.')
        day, start, end, subject, room, since, until = p
        weekday = 6 if day.upper() == 'CN' else int(day) - 2
        if not 0 <= weekday <= 6 or day == '8':
            raise ValueError('Thứ: 2–7 hoặc CN.')
        start = time.fromisoformat(start).strftime('%H:%M')
        end = time.fromisoformat(end).strftime('%H:%M')
        if start >= end:
            raise ValueError('Giờ kết thúc phải sau giờ bắt đầu, trong cùng ngày.')
        since = date.fromisoformat(since).isoformat()
        until = date.fromisoformat(until).isoformat()
        if since > until:
            raise ValueError('Ngày kết thúc phải từ ngày bắt đầu trở đi.')
        if not subject or len(subject) > 150 or len(room) > 100:
            raise ValueError('Tên môn 1–150 ký tự; phòng tối đa 100 ký tự.')
        self.db.execute('INSERT INTO lessons(user_id,weekday,start,end,subject,room,since,until) VALUES (?,?,?,?,?,?,?,?)',
                        (uid, weekday, start, end, subject, room, since, until))
        self.db.commit()

    def lessons(self, uid, day=None):
        if day is None:
            return self.db.execute('SELECT * FROM lessons WHERE user_id=? ORDER BY weekday,start,id', (uid,)).fetchall()
        return self.db.execute('SELECT * FROM lessons WHERE user_id=? AND weekday=? AND since<=? AND until>=? ORDER BY start,id',
                               (uid, day.weekday(), day.isoformat(), day.isoformat())).fetchall()

    def delete(self, uid, lid):
        self.db.execute('DELETE FROM lessons WHERE user_id=? AND id=?', (uid, lid))
        self.db.commit()

    def due(self, now):
        return self.db.execute("SELECT * FROM users WHERE enabled=1 AND reminder<=? AND last_sent<>?", 
                               (now.strftime('%H:%M'), now.date().isoformat())).fetchall()

    def sent(self, uid, today):
        self.db.execute('UPDATE users SET last_sent=? WHERE id=?', (today, uid))
        self.db.commit()

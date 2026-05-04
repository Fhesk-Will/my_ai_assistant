import sqlite3
import os
import json
from datetime import datetime

from core.config import get_config


class MemoryManager:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = get_config().db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    media_paths TEXT,
                    timestamp DATETIME,
                    is_embedded INTEGER DEFAULT 0
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT,
                    updated_at DATETIME
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_timestamp ON chat_history(timestamp)')
            conn.commit()

    def add_message(self, role, content, session_id="default_session", media_paths=None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            media_json = json.dumps(media_paths) if media_paths else None
            cursor.execute('''
                INSERT INTO chat_history (session_id, role, content, media_paths, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, role, content, media_json, datetime.now()))
            conn.commit()

    def get_recent_history(self, limit=10, session_id="default_session"):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT role, content FROM (
                    SELECT role, content, timestamp FROM chat_history
                    WHERE session_id = ?
                    ORDER BY timestamp DESC LIMIT ?
                ) ORDER BY timestamp ASC
            ''', (session_id, limit))
            rows = cursor.fetchall()
            return [{"role": r[0], "content": r[1]} for r in rows]

    def get_all_sessions(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT session_id, title, updated_at FROM sessions ORDER BY updated_at DESC')
            return [{"id": r[0], "title": r[1], "time": r[2][:16] if r[2] else ""} for r in cursor.fetchall()]

    def update_session_meta(self, session_id, title=None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO sessions (session_id, title, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                title = COALESCE(?, title),
                updated_at = ?
            ''', (session_id, title or "新对话", now, title, now))
            conn.commit()

    def delete_session(self, session_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM chat_history WHERE session_id = ?', (session_id,))
            cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
            conn.commit()

    def rename_session(self, session_id, new_title):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE sessions SET title = ? WHERE session_id = ?', (new_title, session_id))
            conn.commit()

    def get_orphaned_sessions(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT session_id FROM chat_history
                WHERE session_id NOT IN (SELECT session_id FROM sessions)
            ''')
            return [r[0] for r in cursor.fetchall()]

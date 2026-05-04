import sqlite3
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EpisodicMemoryManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_tables()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    summary TEXT,
                    topics TEXT,
                    key_events TEXT,
                    mood TEXT,
                    created_at DATETIME
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    task_description TEXT,
                    status TEXT,
                    context TEXT,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS key_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    description TEXT,
                    source_session_id TEXT,
                    event_date DATETIME,
                    created_at DATETIME
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_summary_session ON session_summaries(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_status ON task_states(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON key_events(event_type)')
            conn.commit()

    def add_summary(self, session_id: str, summary: str, topics: list = None,
                    key_events: list = None, mood: str = None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO session_summaries (session_id, summary, topics, key_events, mood, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                summary,
                json.dumps(topics or [], ensure_ascii=False),
                json.dumps(key_events or [], ensure_ascii=False),
                mood,
                datetime.now(),
            ))
            conn.commit()
        logger.info("已保存会话摘要: session=%s, summary=%s", session_id, summary[:50])

    def get_recent_summaries(self, limit: int = 5) -> list:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT session_id, summary, topics, key_events, mood, created_at
                FROM session_summaries
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [{
                "session_id": r[0],
                "summary": r[1],
                "topics": json.loads(r[2]) if r[2] else [],
                "key_events": json.loads(r[3]) if r[3] else [],
                "mood": r[4],
                "created_at": r[5],
            } for r in rows]

    def add_task(self, session_id: str, description: str, status: str = "pending",
                 context: dict = None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            cursor.execute('''
                INSERT INTO task_states (session_id, task_description, status, context, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, description, status, json.dumps(context or {}, ensure_ascii=False), now, now))
            conn.commit()

    def update_task(self, task_id: int, status: str = None, context: dict = None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = ["updated_at = ?"]
            params = [datetime.now()]
            if status:
                updates.append("status = ?")
                params.append(status)
            if context is not None:
                updates.append("context = ?")
                params.append(json.dumps(context, ensure_ascii=False))
            params.append(task_id)
            cursor.execute(f"UPDATE task_states SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()

    def get_active_tasks(self) -> list:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, session_id, task_description, status, context, created_at, updated_at
                FROM task_states
                WHERE status IN ('pending', 'in_progress')
                ORDER BY updated_at DESC
            ''')
            rows = cursor.fetchall()
            return [{
                "id": r[0],
                "session_id": r[1],
                "task_description": r[2],
                "status": r[3],
                "context": json.loads(r[4]) if r[4] else {},
                "created_at": r[5],
                "updated_at": r[6],
            } for r in rows]

    def add_event(self, event_type: str, description: str, session_id: str = None,
                  event_date: str = None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO key_events (event_type, description, source_session_id, event_date, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (event_type, description, session_id, event_date, datetime.now()))
            conn.commit()
        logger.info("已记录关键事件: type=%s, desc=%s", event_type, description[:50])

    def get_events(self, event_type: str = None, limit: int = 10) -> list:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if event_type:
                cursor.execute('''
                    SELECT id, event_type, description, source_session_id, event_date, created_at
                    FROM key_events WHERE event_type = ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (event_type, limit))
            else:
                cursor.execute('''
                    SELECT id, event_type, description, source_session_id, event_date, created_at
                    FROM key_events ORDER BY created_at DESC LIMIT ?
                ''', (limit,))
            rows = cursor.fetchall()
            return [{
                "id": r[0],
                "event_type": r[1],
                "description": r[2],
                "source_session_id": r[3],
                "event_date": r[4],
                "created_at": r[5],
            } for r in rows]

    def get_context_for_prompt(self, session_id: str = None, limit: int = 5) -> str:
        parts = []

        summaries = self.get_recent_summaries(limit)
        if summaries:
            parts.append("【最近对话摘要】")
            for s in summaries:
                date = s["created_at"][:10] if s["created_at"] else ""
                parts.append(f"- [{date}] {s['summary']}")

        active_tasks = self.get_active_tasks()
        if active_tasks:
            parts.append("\n【进行中的任务】")
            for t in active_tasks:
                parts.append(f"- [{t['status']}] {t['task_description']}")

        events = self.get_events(limit=limit)
        if events:
            parts.append("\n【关键事件】")
            for e in events:
                date = e.get("event_date") or (e["created_at"][:10] if e["created_at"] else "")
                parts.append(f"- [{e['event_type']}] {e['description']} ({date})")

        if not parts:
            return ""

        return "\n".join(parts)

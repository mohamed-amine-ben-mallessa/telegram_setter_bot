import sqlite3
from pathlib import Path
from typing import List
from app.schemas.lead import LeadIn

class LeadStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Create directory if needed
        path = db_path.replace("sqlite:///", "")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        path = self.db_path.replace("sqlite:///", "")
        return sqlite3.connect(path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    telegram_user_id TEXT PRIMARY KEY,
                    telegram_handle TEXT,
                    display_name TEXT,
                    status TEXT,
                    score INTEGER,
                    tags TEXT,
                    last_message_text TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def upsert(self, lead: LeadIn, status: str, score: int, tags: List[str]):
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO leads (telegram_user_id, telegram_handle, display_name, status, score, tags, last_message_text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(telegram_user_id) DO UPDATE SET
                    telegram_handle=excluded.telegram_handle,
                    display_name=excluded.display_name,
                    status=excluded.status,
                    score=excluded.score,
                    tags=excluded.tags,
                    last_message_text=excluded.last_message_text,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    lead.telegram_user_id,
                    lead.telegram_handle,
                    lead.display_name,
                    status,
                    score,
                    ",".join(tags),
                    lead.message_text,
                ),
            )
            conn.commit()

    def get_lead(self, telegram_user_id: str):
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT telegram_user_id, telegram_handle, display_name, status, score, tags, last_message_text FROM leads WHERE telegram_user_id = ?",
                (telegram_user_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "telegram_user_id": row[0],
                    "telegram_handle": row[1],
                    "display_name": row[2],
                    "status": row[3],
                    "score": row[4],
                    "tags": row[5].split(",") if row[5] else [],
                    "last_message_text": row[6],
                }
            return None
"""SQLite storage for practice session history."""

import json
import sqlite3
import threading
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "app.db"

_lock = threading.Lock()


def _connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _lock, _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                mode TEXT NOT NULL,
                task_type TEXT,
                task_title TEXT,
                task_prompt TEXT,
                transcript TEXT,
                feedback_json TEXT,
                score_band INTEGER
            )
            """
        )
        conn.commit()


def insert_session(mode, task_type, task_title, task_prompt, transcript, feedback: dict, score_band=None):
    from datetime import datetime, timezone

    with _lock, _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO sessions (created_at, mode, task_type, task_title, task_prompt, transcript, feedback_json, score_band)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                mode,
                task_type,
                task_title,
                task_prompt,
                transcript,
                json.dumps(feedback),
                score_band,
            ),
        )
        conn.commit()
        return cur.lastrowid


def list_sessions(mode=None, limit=100):
    with _lock, _connect() as conn:
        if mode:
            rows = conn.execute(
                "SELECT id, created_at, mode, task_type, task_title, score_band FROM sessions WHERE mode = ? ORDER BY id DESC LIMIT ?",
                (mode, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, created_at, mode, task_type, task_title, score_band FROM sessions ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]


def get_session(session_id: int):
    with _lock, _connect() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if not row:
            return None
        result = dict(row)
        result["feedback"] = json.loads(result.pop("feedback_json") or "{}")
        return result


def toefl_score_trend():
    with _lock, _connect() as conn:
        rows = conn.execute(
            "SELECT id, created_at, task_type, score_band FROM sessions "
            "WHERE mode = 'toefl' AND score_band IS NOT NULL ORDER BY id ASC"
        ).fetchall()
        return [dict(r) for r in rows]

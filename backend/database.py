"""Local-first SQLite content library: shadowing passages and TOEFL prompts.

Deliberately separate from db.py (which owns user session/profile/XP state, in
data/app.db). This file owns *reference content* — the kind of data that gets
reseeded from seed_data.json as the question bank grows, independent of any
learner's history. Splitting them means content updates never touch user data
and vice versa.

Schema note on toefl_prompts: the real TOEFL iBT Speaking section (redesigned
January 2026) presents items in *sets* — 7 sentences submitted together for one
Listen-and-Repeat score, 4 questions together for one Interview score — not as
independent prompts. The five required columns (id, task_type, question_text,
preparation_time, response_time) are preserved exactly, with set_id/set_title/
item_index/picture_caption added so a set can be reassembled from its rows.
preparation_time is 0 for every row: the current format has no prep time on
either task.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "toefl_coach.db"

SHADOWING_DIFFICULTIES = ("beginner", "intermediate", "academic")
TOEFL_TASK_TYPES = ("listen_repeat", "interview")


@contextmanager
def get_connection():
    """Context-managed SQLite connection: commits on success, rolls back on error, always closes."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shadowing_library (
                id TEXT PRIMARY KEY,
                difficulty TEXT NOT NULL,
                topic TEXT NOT NULL,
                full_transcript TEXT NOT NULL,
                sentences TEXT NOT NULL,
                preferred_accent TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS toefl_prompts (
                id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                question_text TEXT NOT NULL,
                preparation_time INTEGER NOT NULL,
                response_time INTEGER NOT NULL,
                set_id TEXT NOT NULL,
                set_title TEXT NOT NULL,
                item_index INTEGER NOT NULL,
                picture_caption TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_shadowing_difficulty ON shadowing_library(difficulty)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_toefl_set ON toefl_prompts(task_type, set_id, item_index)")


# --- Seeding -----------------------------------------------------------------


def seed_shadowing(entries: list[dict]) -> int:
    """INSERT OR REPLACE shadowing_library rows from parsed seed_data.json entries."""
    with get_connection() as conn:
        for entry in entries:
            if entry["difficulty"] not in SHADOWING_DIFFICULTIES:
                raise ValueError(f"{entry['id']}: difficulty must be one of {SHADOWING_DIFFICULTIES}")
            sentences = entry["sentences"]
            conn.execute(
                """
                INSERT OR REPLACE INTO shadowing_library
                    (id, difficulty, topic, full_transcript, sentences, preferred_accent)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    entry["id"],
                    entry["difficulty"],
                    entry["topic"],
                    entry.get("full_transcript") or " ".join(sentences),
                    json.dumps(sentences),
                    entry.get("preferred_accent", "en-US"),
                ),
            )
        return len(entries)


def seed_toefl_prompts(sets: list[dict]) -> int:
    """INSERT OR REPLACE toefl_prompts rows, flattening each seed 'set' into its item rows."""
    count = 0
    with get_connection() as conn:
        for s in sets:
            if s["task_type"] not in TOEFL_TASK_TYPES:
                raise ValueError(f"{s['set_id']}: task_type must be one of {TOEFL_TASK_TYPES}")
            for i, item in enumerate(s["items"]):
                row_id = f"{s['set_id']}_{i}"
                conn.execute(
                    """
                    INSERT OR REPLACE INTO toefl_prompts
                        (id, task_type, question_text, preparation_time, response_time,
                         set_id, set_title, item_index, picture_caption)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row_id,
                        s["task_type"],
                        item["question_text"],
                        0,  # preparation_time: the current TOEFL format has none on either task
                        item["response_time"],
                        s["set_id"],
                        s["set_title"],
                        i,
                        s.get("picture_caption"),
                    ),
                )
                count += 1
    return count


# --- Shadowing fetch functions --------------------------------------------------


def _row_to_passage(row: sqlite3.Row) -> dict:
    sentences = json.loads(row["sentences"])
    return {
        "id": row["id"],
        "title": row["topic"],
        "difficulty": row["difficulty"],
        "category": row["topic"],
        "full_transcript": row["full_transcript"],
        "preferred_accent": row["preferred_accent"],
        "audio_url": None,
        "sentences": sentences,
    }


def fetch_all_shadowing_passages() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM shadowing_library ORDER BY id").fetchall()
        return [_row_to_passage(r) for r in rows]


def fetch_shadowing_passage(passage_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM shadowing_library WHERE id = ?", (passage_id,)).fetchone()
        return _row_to_passage(row) if row else None


def fetch_shadowing_lesson(difficulty: str) -> dict | None:
    """One random-ish (first-match) passage at the given difficulty, or None if the bank is empty."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM shadowing_library WHERE difficulty = ? ORDER BY RANDOM() LIMIT 1",
            (difficulty,),
        ).fetchone()
        return _row_to_passage(row) if row else None


# --- TOEFL fetch functions ---------------------------------------------------


def _rows_to_set(rows: list[sqlite3.Row]) -> dict:
    rows = sorted(rows, key=lambda r: r["item_index"])
    first = rows[0]
    task_type = first["set_id"], first["task_type"]
    key = "sentences" if first["task_type"] == "listen_repeat" else "questions"
    result = {
        "id": first["set_id"],
        "task": first["task_type"],
        "title": first["set_title"],
        key: [r["question_text"] for r in rows],
    }
    if first["task_type"] == "listen_repeat":
        result["picture_caption"] = first["picture_caption"]
    return result


def fetch_toefl_sets(task_type: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM toefl_prompts WHERE task_type = ? ORDER BY set_id, item_index",
            (task_type,),
        ).fetchall()
    by_set: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        by_set.setdefault(row["set_id"], []).append(row)
    return [_rows_to_set(group) for group in by_set.values()]


def fetch_toefl_set(task_type: str, set_id: str) -> dict | None:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM toefl_prompts WHERE task_type = ? AND set_id = ? ORDER BY item_index",
            (task_type, set_id),
        ).fetchall()
    return _rows_to_set(rows) if rows else None


def fetch_toefl_response_times(task_type: str) -> list[int]:
    """Per-item response-time schedule (all sets of a task type currently share one), used for the countdown UI."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT set_id FROM toefl_prompts WHERE task_type = ? LIMIT 1", (task_type,)
        ).fetchone()
        if not row:
            return []
        items = conn.execute(
            "SELECT response_time FROM toefl_prompts WHERE task_type = ? AND set_id = ? ORDER BY item_index",
            (task_type, row["set_id"]),
        ).fetchall()
        return [r["response_time"] for r in items]


def get_random_toefl_prompt(task_type: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT DISTINCT set_id FROM toefl_prompts WHERE task_type = ? ORDER BY RANDOM() LIMIT 1",
            (task_type,),
        ).fetchone()
        if not row:
            return None
    return fetch_toefl_set(task_type, row["set_id"])

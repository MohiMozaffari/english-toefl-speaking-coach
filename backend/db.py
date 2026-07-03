"""SQLite storage: profiles, practice sessions, skill-module results, XP activities, achievements.

Single-file local database. Migrations are additive only (CREATE IF NOT EXISTS +
ensure-column), so existing session history survives upgrades.
"""

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "app.db"

_lock = threading.Lock()


def _connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_column(conn, table: str, column: str, decl: str):
    cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db():
    with _lock, _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                daily_goal_xp INTEGER NOT NULL DEFAULT 50
            )
            """
        )
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
        _ensure_column(conn, "sessions", "metrics_json", "TEXT")
        _ensure_column(conn, "sessions", "profile_id", "INTEGER")
        _ensure_column(conn, "sessions", "prompt_ref", "TEXT")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                kind TEXT NOT NULL,
                ref TEXT,
                xp INTEGER NOT NULL DEFAULT 0,
                detail_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shadowing_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                passage_id TEXT NOT NULL,
                sentence_index INTEGER NOT NULL,
                target_text TEXT NOT NULL,
                transcript TEXT,
                accuracy REAL,
                fluency_score REAL,
                word_diff_json TEXT,
                metrics_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pair_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                pair_id TEXT NOT NULL,
                contrast TEXT NOT NULL,
                target_word TEXT NOT NULL,
                heard_word TEXT,
                correct INTEGER
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS listening_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                item_id TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                answers_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS earned_achievements (
                profile_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                earned_at TEXT NOT NULL,
                PRIMARY KEY (profile_id, achievement_id)
            )
            """
        )
        # Guarantee a default profile so the app works with zero setup.
        row = conn.execute("SELECT id FROM profiles ORDER BY id LIMIT 1").fetchone()
        if not row:
            conn.execute(
                "INSERT INTO profiles (name, created_at, daily_goal_xp) VALUES (?, ?, ?)",
                ("Learner", _now(), 50),
            )
        conn.commit()


# --- Profiles -----------------------------------------------------------------


def list_profiles():
    with _lock, _connect() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM profiles ORDER BY id")]


def get_profile(profile_id: int):
    with _lock, _connect() as conn:
        row = conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
        return dict(row) if row else None


def first_profile_id() -> int:
    with _lock, _connect() as conn:
        row = conn.execute("SELECT id FROM profiles ORDER BY id LIMIT 1").fetchone()
        return row["id"]


def create_profile(name: str, daily_goal_xp: int = 50) -> int:
    with _lock, _connect() as conn:
        cur = conn.execute(
            "INSERT INTO profiles (name, created_at, daily_goal_xp) VALUES (?, ?, ?)",
            (name, _now(), daily_goal_xp),
        )
        conn.commit()
        return cur.lastrowid


def update_profile(profile_id: int, name=None, daily_goal_xp=None):
    with _lock, _connect() as conn:
        if name is not None:
            conn.execute("UPDATE profiles SET name = ? WHERE id = ?", (name, profile_id))
        if daily_goal_xp is not None:
            conn.execute("UPDATE profiles SET daily_goal_xp = ? WHERE id = ?", (daily_goal_xp, profile_id))
        conn.commit()


# --- Practice sessions ----------------------------------------------------------


def insert_session(
    mode,
    task_type,
    task_title,
    task_prompt,
    transcript,
    feedback: dict,
    score_band=None,
    metrics: dict | None = None,
    profile_id: int | None = None,
    prompt_ref: str | None = None,
):
    with _lock, _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO sessions
                (created_at, mode, task_type, task_title, task_prompt, transcript,
                 feedback_json, score_band, metrics_json, profile_id, prompt_ref)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _now(),
                mode,
                task_type,
                task_title,
                task_prompt,
                transcript,
                json.dumps(feedback),
                score_band,
                json.dumps(metrics) if metrics else None,
                profile_id,
                prompt_ref,
            ),
        )
        conn.commit()
        return cur.lastrowid


def list_sessions(mode=None, limit=100, profile_id=None):
    query = "SELECT id, created_at, mode, task_type, task_title, score_band, prompt_ref FROM sessions"
    clauses, params = [], []
    if mode:
        clauses.append("mode = ?")
        params.append(mode)
    if profile_id is not None:
        clauses.append("(profile_id = ? OR profile_id IS NULL)")
        params.append(profile_id)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with _lock, _connect() as conn:
        return [dict(r) for r in conn.execute(query, params)]


def get_session(session_id: int):
    with _lock, _connect() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if not row:
            return None
        result = dict(row)
        result["feedback"] = json.loads(result.pop("feedback_json") or "{}")
        result["metrics"] = json.loads(result.pop("metrics_json") or "null")
        return result


def sessions_for_prompt(prompt_ref: str, profile_id=None, limit=20):
    """All attempts of the same prompt/set, oldest first — used for attempt comparison."""
    query = "SELECT id, created_at, score_band, metrics_json FROM sessions WHERE prompt_ref = ?"
    params = [prompt_ref]
    if profile_id is not None:
        query += " AND (profile_id = ? OR profile_id IS NULL)"
        params.append(profile_id)
    query += " ORDER BY id ASC LIMIT ?"
    params.append(limit)
    with _lock, _connect() as conn:
        rows = [dict(r) for r in conn.execute(query, params)]
    for r in rows:
        r["metrics"] = json.loads(r.pop("metrics_json") or "null")
    return rows


def toefl_score_trend(profile_id=None):
    query = (
        "SELECT id, created_at, task_type, score_band FROM sessions "
        "WHERE mode = 'toefl' AND score_band IS NOT NULL"
    )
    params = []
    if profile_id is not None:
        query += " AND (profile_id = ? OR profile_id IS NULL)"
        params.append(profile_id)
    query += " ORDER BY id ASC"
    with _lock, _connect() as conn:
        return [dict(r) for r in conn.execute(query, params)]


def recent_sessions_full(profile_id=None, limit=15):
    """Recent sessions with feedback + metrics, for coach memory building."""
    query = "SELECT * FROM sessions"
    params = []
    if profile_id is not None:
        query += " WHERE (profile_id = ? OR profile_id IS NULL)"
        params.append(profile_id)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with _lock, _connect() as conn:
        rows = [dict(r) for r in conn.execute(query, params)]
    for r in rows:
        r["feedback"] = json.loads(r.pop("feedback_json") or "{}")
        r["metrics"] = json.loads(r.pop("metrics_json") or "null")
    return rows


# --- Activities (XP log) --------------------------------------------------------


def insert_activity(profile_id: int, kind: str, xp: int, ref: str | None = None, detail: dict | None = None):
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO activities (profile_id, created_at, kind, ref, xp, detail_json) VALUES (?, ?, ?, ?, ?, ?)",
            (profile_id, _now(), kind, ref, xp, json.dumps(detail) if detail else None),
        )
        conn.commit()


def list_activities(profile_id: int, limit=1000):
    with _lock, _connect() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT created_at, kind, ref, xp FROM activities WHERE profile_id = ? ORDER BY id DESC LIMIT ?",
                (profile_id, limit),
            )
        ]


def total_xp(profile_id: int) -> int:
    with _lock, _connect() as conn:
        row = conn.execute("SELECT COALESCE(SUM(xp), 0) AS t FROM activities WHERE profile_id = ?", (profile_id,)).fetchone()
        return row["t"]


# --- Shadowing --------------------------------------------------------------


def insert_shadowing_attempt(
    profile_id, passage_id, sentence_index, target_text, transcript, accuracy, fluency_score, word_diff, metrics
):
    with _lock, _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO shadowing_attempts
                (profile_id, created_at, passage_id, sentence_index, target_text, transcript,
                 accuracy, fluency_score, word_diff_json, metrics_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                _now(),
                passage_id,
                sentence_index,
                target_text,
                transcript,
                accuracy,
                fluency_score,
                json.dumps(word_diff),
                json.dumps(metrics) if metrics else None,
            ),
        )
        conn.commit()
        return cur.lastrowid


def shadowing_progress(profile_id: int):
    """Best accuracy per passage sentence, plus attempt counts."""
    with _lock, _connect() as conn:
        rows = conn.execute(
            """
            SELECT passage_id, sentence_index, MAX(accuracy) AS best_accuracy, COUNT(*) AS attempts
            FROM shadowing_attempts WHERE profile_id = ?
            GROUP BY passage_id, sentence_index
            """,
            (profile_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def shadowing_stats(profile_id: int):
    with _lock, _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS attempts, AVG(accuracy) AS avg_accuracy FROM shadowing_attempts WHERE profile_id = ?",
            (profile_id,),
        ).fetchone()
        return {"attempts": row["attempts"], "avg_accuracy": round(row["avg_accuracy"], 1) if row["avg_accuracy"] else None}


# --- Pronunciation pairs -----------------------------------------------------


def insert_pair_attempt(profile_id, pair_id, contrast, target_word, heard_word, correct):
    """correct: True / False, or None when whisper heard neither word (unclear —
    stored for history but excluded from accuracy stats)."""
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO pair_attempts (profile_id, created_at, pair_id, contrast, target_word, heard_word, correct) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (profile_id, _now(), pair_id, contrast, target_word, heard_word,
             None if correct is None else (1 if correct else 0)),
        )
        conn.commit()


def pair_contrast_stats(profile_id: int):
    """Per-contrast accuracy over decisive attempts — the honest 'weak sounds' signal."""
    with _lock, _connect() as conn:
        rows = conn.execute(
            """
            SELECT contrast, COUNT(correct) AS attempts, COALESCE(SUM(correct), 0) AS correct
            FROM pair_attempts WHERE profile_id = ? AND correct IS NOT NULL
            GROUP BY contrast ORDER BY attempts DESC
            """,
            (profile_id,),
        ).fetchall()
        return [
            {
                "contrast": r["contrast"],
                "attempts": r["attempts"],
                "correct": r["correct"],
                "accuracy": round(r["correct"] / r["attempts"] * 100, 1),
            }
            for r in rows
            if r["attempts"] > 0
        ]


# --- Listening ---------------------------------------------------------------


def insert_listening_result(profile_id, item_id, score, total, answers):
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO listening_results (profile_id, created_at, item_id, score, total, answers_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (profile_id, _now(), item_id, score, total, json.dumps(answers)),
        )
        conn.commit()


def listening_history(profile_id: int, limit=50):
    with _lock, _connect() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT created_at, item_id, score, total FROM listening_results WHERE profile_id = ? "
                "ORDER BY id DESC LIMIT ?",
                (profile_id, limit),
            )
        ]


# --- Achievements ---------------------------------------------------------------


def earned_achievements(profile_id: int) -> dict:
    with _lock, _connect() as conn:
        rows = conn.execute(
            "SELECT achievement_id, earned_at FROM earned_achievements WHERE profile_id = ?", (profile_id,)
        ).fetchall()
        return {r["achievement_id"]: r["earned_at"] for r in rows}


def award_achievement(profile_id: int, achievement_id: str):
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO earned_achievements (profile_id, achievement_id, earned_at) VALUES (?, ?, ?)",
            (profile_id, achievement_id, _now()),
        )
        conn.commit()

"""Shadowing passages: fetched from the SQLite content library (database.py).

Sentence-by-sentence audio is generated via edge-tts (see tts_service.py) with a
per-passage preferred_accent, falling back to the browser's speechSynthesis if
edge-tts is unreachable. Content itself lives in data/toefl_coach.db, seeded from
seed_data.json via seed_db.py -- nothing here is hardcoded anymore.
"""

import database


def get_passages() -> list[dict]:
    """Summaries only (no full sentence list) -- what the passage browser needs."""
    return [
        {k: v for k, v in p.items() if k != "sentences"} | {"sentence_count": len(p["sentences"])}
        for p in database.fetch_all_shadowing_passages()
    ]


def get_passage(passage_id: str) -> dict | None:
    return database.fetch_shadowing_passage(passage_id)


def fetch_shadowing_lesson(difficulty: str) -> dict | None:
    """One passage at the given difficulty (beginner / intermediate / academic)."""
    return database.fetch_shadowing_lesson(difficulty)

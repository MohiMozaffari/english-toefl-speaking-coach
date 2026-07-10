"""Seed (or re-seed) the SQLite content library from seed_data.json.

Safe to run any number of times: every row is written with INSERT OR REPLACE,
keyed on primary key, so re-running after editing seed_data.json just updates
existing rows and adds new ones. It never touches user session data in
data/app.db -- this only writes to data/toefl_coach.db.

Usage:
    python seed_db.py
"""

import json
import sys
from pathlib import Path

import database

SEED_PATH = Path(__file__).parent / "seed_data.json"


def load_seed_data() -> dict:
    if not SEED_PATH.exists():
        print(f"ERROR: seed file not found at {SEED_PATH}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(SEED_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        print(f"ERROR: {SEED_PATH} is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(1)


def main():
    data = load_seed_data()
    database.init_db()

    shadowing_count = database.seed_shadowing(data.get("shadowing", []))
    toefl_row_count = database.seed_toefl_prompts(data.get("toefl_prompts", []))
    toefl_set_count = len(data.get("toefl_prompts", []))
    reading_row_count = database.seed_toefl_reading(data.get("toefl_reading", []))
    reading_set_count = len(data.get("toefl_reading", []))

    print(f"Seeded database at {database.DB_PATH}")
    print(f"  shadowing_library: {shadowing_count} passages")
    print(f"  toefl_prompts:     {toefl_row_count} rows across {toefl_set_count} sets")
    print(f"  toefl_reading:     {reading_row_count} items across {reading_set_count} sets")


if __name__ == "__main__":
    main()

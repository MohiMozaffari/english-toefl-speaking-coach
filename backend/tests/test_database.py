import importlib

import pytest


@pytest.fixture
def db(tmp_path, monkeypatch):
    """A fresh database module instance pointed at an isolated temp SQLite file."""
    import database as db_mod

    importlib.reload(db_mod)
    monkeypatch.setattr(db_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "test_toefl_coach.db")
    db_mod.init_db()
    yield db_mod


SHADOWING_ENTRY = {
    "id": "sh_test", "difficulty": "beginner", "topic": "Test Topic",
    "preferred_accent": "en-US", "sentences": ["First sentence.", "Second sentence."],
}

TOEFL_SET = {
    "set_id": "lr_test", "task_type": "listen_repeat", "set_title": "Test Set",
    "picture_caption": "A test picture",
    "items": [
        {"question_text": "Sentence one.", "response_time": 8},
        {"question_text": "Sentence two.", "response_time": 10},
    ],
}


def test_init_db_creates_empty_tables(db):
    assert db.fetch_all_shadowing_passages() == []
    assert db.fetch_toefl_sets("listen_repeat") == []


def test_init_db_is_idempotent(db):
    db.init_db()
    db.init_db()  # must not raise on existing tables
    assert db.fetch_all_shadowing_passages() == []


def test_seed_shadowing_roundtrip(db):
    count = db.seed_shadowing([SHADOWING_ENTRY])
    assert count == 1
    passage = db.fetch_shadowing_passage("sh_test")
    assert passage["title"] == "Test Topic"
    assert passage["sentences"] == ["First sentence.", "Second sentence."]
    assert passage["full_transcript"] == "First sentence. Second sentence."


def test_seed_shadowing_derives_transcript_when_absent(db):
    db.seed_shadowing([SHADOWING_ENTRY])
    passage = db.fetch_shadowing_passage("sh_test")
    assert passage["full_transcript"] == "First sentence. Second sentence."


def test_seed_shadowing_rejects_bad_difficulty(db):
    bad = dict(SHADOWING_ENTRY, difficulty="expert")
    with pytest.raises(ValueError):
        db.seed_shadowing([bad])


def test_seed_shadowing_insert_or_replace_is_idempotent(db):
    db.seed_shadowing([SHADOWING_ENTRY])
    updated = dict(SHADOWING_ENTRY, topic="Updated Topic")
    db.seed_shadowing([updated])
    assert len(db.fetch_all_shadowing_passages()) == 1
    assert db.fetch_shadowing_passage("sh_test")["title"] == "Updated Topic"


def test_fetch_shadowing_lesson_by_difficulty(db):
    db.seed_shadowing([SHADOWING_ENTRY, dict(SHADOWING_ENTRY, id="sh_test2", difficulty="academic")])
    lesson = db.fetch_shadowing_lesson("academic")
    assert lesson["id"] == "sh_test2"
    assert db.fetch_shadowing_lesson("intermediate") is None


def test_seed_toefl_prompts_roundtrip(db):
    count = db.seed_toefl_prompts([TOEFL_SET])
    assert count == 2  # two items flattened into two rows
    fetched = db.fetch_toefl_set("listen_repeat", "lr_test")
    assert fetched["title"] == "Test Set"
    assert fetched["sentences"] == ["Sentence one.", "Sentence two."]
    assert fetched["picture_caption"] == "A test picture"


def test_seed_toefl_prompts_preparation_time_is_always_zero(db):
    db.seed_toefl_prompts([TOEFL_SET])
    with db.get_connection() as conn:
        rows = conn.execute("SELECT preparation_time FROM toefl_prompts").fetchall()
    assert all(r["preparation_time"] == 0 for r in rows)


def test_seed_toefl_prompts_rejects_bad_task_type(db):
    bad = dict(TOEFL_SET, task_type="reading")
    with pytest.raises(ValueError):
        db.seed_toefl_prompts([bad])


def test_seed_toefl_prompts_row_ids_are_unique_per_item(db):
    db.seed_toefl_prompts([TOEFL_SET])
    with db.get_connection() as conn:
        ids = [r["id"] for r in conn.execute("SELECT id FROM toefl_prompts ORDER BY item_index")]
    assert ids == ["lr_test_0", "lr_test_1"]


def test_fetch_toefl_sets_groups_by_set_id(db):
    interview_set = {
        "set_id": "iv_test", "task_type": "interview", "set_title": "Interview Test",
        "items": [{"question_text": f"Q{i}", "response_time": 45} for i in range(4)],
    }
    db.seed_toefl_prompts([TOEFL_SET, interview_set])
    assert len(db.fetch_toefl_sets("listen_repeat")) == 1
    assert len(db.fetch_toefl_sets("interview")) == 1
    assert "questions" in db.fetch_toefl_sets("interview")[0]
    assert "sentences" in db.fetch_toefl_sets("listen_repeat")[0]


def test_fetch_toefl_response_times(db):
    db.seed_toefl_prompts([TOEFL_SET])
    assert db.fetch_toefl_response_times("listen_repeat") == [8, 10]
    assert db.fetch_toefl_response_times("interview") == []


def test_get_random_toefl_prompt(db):
    db.seed_toefl_prompts([TOEFL_SET])
    prompt = db.get_random_toefl_prompt("listen_repeat")
    assert prompt["id"] == "lr_test"
    assert db.get_random_toefl_prompt("interview") is None


def test_fetch_unknown_ids_return_none(db):
    assert db.fetch_shadowing_passage("nonexistent") is None
    assert db.fetch_toefl_set("listen_repeat", "nonexistent") is None

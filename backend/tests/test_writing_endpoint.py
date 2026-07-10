"""Endpoint-level coverage for the TOEFL Writing routes.

Build a Sentence is auto-graded locally, so it's tested against the real
endpoint end to end. Write an Email / Academic Discussion are LLM-graded --
only the too-short fallback path (which skips the LLM call entirely) and
input-validation paths are exercised here, mirroring test_toefl_endpoint.py's
approach of never calling a real LLM in tests.
"""

import importlib

import pytest
from fastapi.testclient import TestClient

BUILD_ITEM = {
    "id": "wr_build_test",
    "task_type": "build_sentence",
    "context_line": "I heard the library is closed today.",
    "words": ["it", "reopens", "tomorrow.", "I", "think"],
    "answer": ["I", "think", "it", "reopens", "tomorrow."],
    "explanation": "A hedged statement giving a likely answer.",
}

EMAIL_ITEM = {
    "id": "wr_email_test",
    "task_type": "write_email",
    "situation": "Test situation.",
    "email_prompt": "Write a test email.",
    "min_words": 90,
    "rubric_ref": "write_email",
}

DISCUSSION_ITEM = {
    "id": "wr_discussion_test",
    "task_type": "academic_discussion",
    "professor_prompt": "Test discussion question.",
    "classmate_posts": [
        {"name": "Alex", "text": "Test post one."},
        {"name": "Sam", "text": "Test post two."},
    ],
    "min_words": 100,
    "rubric_ref": "academic_discussion",
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    import database as database_mod
    import db as db_mod

    importlib.reload(db_mod)
    monkeypatch.setattr(db_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "app.db")

    importlib.reload(database_mod)
    monkeypatch.setattr(database_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(database_mod, "DB_PATH", tmp_path / "toefl_coach.db")
    database_mod.init_db()
    database_mod.seed_toefl_writing([BUILD_ITEM, EMAIL_ITEM, DISCUSSION_ITEM])

    import main

    with TestClient(main.app) as c:
        yield c


def test_build_sentence_submit_correct(client):
    resp = client.post(
        "/api/writing/build-sentence/submit",
        json={"item_id": "wr_build_test", "tokens": ["I", "think", "it", "reopens", "tomorrow."]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["correct"] is True
    assert body["answer"] == ["I", "think", "it", "reopens", "tomorrow."]


def test_build_sentence_submit_incorrect(client):
    resp = client.post(
        "/api/writing/build-sentence/submit",
        json={"item_id": "wr_build_test", "tokens": ["it", "I", "think", "reopens", "tomorrow."]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["correct"] is False
    assert body["explanation"]


def test_build_sentence_submit_unknown_item(client):
    resp = client.post("/api/writing/build-sentence/submit", json={"item_id": "nonexistent", "tokens": []})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_build_sentence_history_reflects_attempts(client):
    client.post(
        "/api/writing/build-sentence/submit",
        json={"item_id": "wr_build_test", "tokens": ["I", "think", "it", "reopens", "tomorrow."]},
    )
    history = client.get("/api/writing/build-sentence/history").json()
    assert len(history) == 1
    assert history[0]["item_id"] == "wr_build_test"
    assert history[0]["correct"] == 1


def test_writing_attempt_too_short_skips_llm_and_returns_fallback(client):
    resp = client.post(
        "/api/practice/writing/attempt",
        json={"item_id": "wr_email_test", "response_text": "Too short."},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["feedback"]["status"] == "too_short"
    assert body["feedback"]["score_band"] == 1
    assert body["feedback"]["model_answer"] == ""


def test_writing_attempt_discussion_too_short_also_falls_back(client):
    resp = client.post(
        "/api/practice/writing/attempt",
        json={"item_id": "wr_discussion_test", "response_text": "Nope."},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["feedback"]["status"] == "too_short"


def test_writing_attempt_unknown_item(client):
    resp = client.post(
        "/api/practice/writing/attempt",
        json={"item_id": "nonexistent", "response_text": "Whatever text goes here for this attempt."},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "bad_prompt_id"


def test_writing_attempt_rejects_build_sentence_item(client):
    """/api/practice/writing/attempt is only for the two LLM-graded tasks."""
    resp = client.post(
        "/api/practice/writing/attempt",
        json={"item_id": "wr_build_test", "response_text": "Whatever text goes here for this attempt."},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "bad_prompt_id"


def test_writing_attempt_prompt_ref_scoped_per_item(client):
    resp = client.post(
        "/api/practice/writing/attempt",
        json={"item_id": "wr_email_test", "response_text": "Too short."},
    )
    session_id = resp.json()["session_id"]
    detail = client.get(f"/api/sessions/{session_id}").json()
    assert detail["prompt_ref"] == "writing:wr_email_test"
    assert detail["mode"] == "writing"

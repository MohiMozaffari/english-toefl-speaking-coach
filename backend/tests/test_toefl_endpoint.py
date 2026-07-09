"""Endpoint-level regression coverage for the TOEFL attempt audio-count contract.

Pure-logic tests (test_stt_fallbacks.py, test_content.py, ...) can't catch a
frontend/backend contract mismatch on how many audio files an endpoint expects
per mode -- only an actual request against the app can. This is exactly the bug
class Practice mode hit: the frontend started sending one recording per item
(with item_index) while the endpoint still demanded the whole set every time.

Whisper is monkeypatched to a silent/too-short result so these run fast and
deterministically without loading the real model or calling FreeLLMAPI --
transcription accuracy itself is covered elsewhere.
"""

import importlib
import io

import pytest
from fastapi.testclient import TestClient

TOEFL_SET = {
    "set_id": "lr_test", "task_type": "listen_repeat", "set_title": "Test Set",
    "picture_caption": "A test picture",
    "items": [
        {"question_text": "Sentence one.", "response_time": 8},
        {"question_text": "Sentence two.", "response_time": 10},
        {"question_text": "Sentence three.", "response_time": 10},
    ],
}

INTERVIEW_SET = {
    "set_id": "iv_test", "task_type": "interview", "set_title": "Interview Test",
    "items": [{"question_text": f"Q{i}", "response_time": 45} for i in range(4)],
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    import database as database_mod
    import db as db_mod
    import whisper_service

    importlib.reload(db_mod)
    monkeypatch.setattr(db_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "app.db")

    importlib.reload(database_mod)
    monkeypatch.setattr(database_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(database_mod, "DB_PATH", tmp_path / "toefl_coach.db")
    database_mod.init_db()
    database_mod.seed_toefl_prompts([TOEFL_SET, INTERVIEW_SET])

    # Every uploaded clip "transcribes" to silence -- the audio-count contract is
    # what's under test here, not real speech-to-text.
    monkeypatch.setattr(
        whisper_service, "transcribe_rich",
        lambda path, model: {"text": "", "words": [], "duration": 0.5, "failed": False},
    )

    import main

    with TestClient(main.app) as c:
        yield c


def _clip(name="clip.webm"):
    return (name, io.BytesIO(b"fake-audio-bytes"), "audio/webm")


def test_practice_mode_accepts_exactly_one_recording(client):
    """The bug: Practice mode sends 1 clip + item_index; the endpoint must accept it."""
    resp = client.post(
        "/api/practice/toefl/attempt",
        files={"audio": _clip()},
        data={"task_type": "listen_repeat", "prompt_id": "lr_test", "item_index": "0"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["feedback"]["status"] == "too_short"
    assert len(body["feedback"]["items"]) == 1
    assert body["feedback"]["items"][0]["target"] == "Sentence one."


def test_practice_mode_resolves_the_correct_item_by_index(client):
    resp = client.post(
        "/api/practice/toefl/attempt",
        files={"audio": _clip()},
        data={"task_type": "listen_repeat", "prompt_id": "lr_test", "item_index": "2"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["feedback"]["items"][0]["target"] == "Sentence three."


def test_practice_mode_rejects_item_index_out_of_range(client):
    resp = client.post(
        "/api/practice/toefl/attempt",
        files={"audio": _clip()},
        data={"task_type": "listen_repeat", "prompt_id": "lr_test", "item_index": "99"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "bad_item_index"


def test_practice_mode_rejects_more_than_one_recording(client):
    """Sending the whole set while item_index is set must still fail loudly --
    it means the frontend and backend disagree about which mode is active."""
    resp = client.post(
        "/api/practice/toefl/attempt",
        files=[("audio", _clip("a.webm")), ("audio", _clip("b.webm")), ("audio", _clip("c.webm"))],
        data={"task_type": "listen_repeat", "prompt_id": "lr_test", "item_index": "0"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "item_count_mismatch"


def test_exam_mode_requires_the_whole_set(client):
    """No item_index -- Exam mode -- must receive one recording per item in the set."""
    resp = client.post(
        "/api/practice/toefl/attempt",
        files=[("audio", _clip("a.webm")), ("audio", _clip("b.webm")), ("audio", _clip("c.webm"))],
        data={"task_type": "listen_repeat", "prompt_id": "lr_test"},
    )
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["feedback"]["items"]) == 3


def test_exam_mode_rejects_a_single_recording_for_a_multi_item_set(client):
    resp = client.post(
        "/api/practice/toefl/attempt",
        files={"audio": _clip()},
        data={"task_type": "listen_repeat", "prompt_id": "lr_test"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "item_count_mismatch"


def test_interview_practice_mode_single_item(client):
    resp = client.post(
        "/api/practice/toefl/attempt",
        files={"audio": _clip()},
        data={"task_type": "interview", "prompt_id": "iv_test", "item_index": "1"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["feedback"]["items"][0]["question"] == "Q1"


def test_practice_mode_prompt_ref_is_per_item_not_per_set(client):
    """Each item's history/attempt-comparison must be scoped to that specific item,
    not lumped in with the other six sentences in the set."""
    resp = client.post(
        "/api/practice/toefl/attempt",
        files={"audio": _clip()},
        data={"task_type": "listen_repeat", "prompt_id": "lr_test", "item_index": "0"},
    )
    session_id = resp.json()["session_id"]
    detail = client.get(f"/api/sessions/{session_id}").json()
    assert detail["prompt_ref"] == "toefl:listen_repeat:lr_test:0"

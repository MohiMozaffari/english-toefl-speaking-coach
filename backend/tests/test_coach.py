import importlib

import pytest


@pytest.fixture
def db_module(tmp_path, monkeypatch):
    """A fresh db module instance pointed at an isolated temp SQLite file."""
    import db as db_mod

    importlib.reload(db_mod)
    monkeypatch.setattr(db_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "test.db")
    db_mod.init_db()
    return db_mod


@pytest.fixture
def coach_module(db_module, monkeypatch):
    """coach.py bound to the same isolated db instance as db_module."""
    import coach as coach_mod

    importlib.reload(coach_mod)
    monkeypatch.setattr(coach_mod, "db", db_module)
    return coach_mod


def test_band_advice_covers_every_band(coach_module):
    for band in range(1, 7):
        result = coach_module.band_advice(band)
        assert result["band"] == band
        assert result["cefr"]
        assert result["advice"]


def test_band_advice_clamps_out_of_range(coach_module):
    assert coach_module.band_advice(0)["band"] == 1
    assert coach_module.band_advice(9)["band"] == 6


def test_band_advice_matches_cefr_table(coach_module):
    expected_cefr = {1: "A1", 2: "A2", 3: "B1", 4: "B2", 5: "C1", 6: "C2"}
    for band, cefr in expected_cefr.items():
        assert coach_module.band_advice(band)["cefr"] == cefr


def test_current_band_advice_none_without_sessions(coach_module, db_module):
    profile_id = db_module.first_profile_id()
    assert coach_module.current_band_advice(profile_id) is None


def test_current_band_advice_uses_most_recent_score(coach_module, db_module):
    profile_id = db_module.first_profile_id()
    for score in (2, 4, 5):
        db_module.insert_session(
            mode="toefl", task_type="listen_repeat", task_title="Set", task_prompt="p",
            transcript="t", feedback={}, score_band=score, profile_id=profile_id,
        )
    advice = coach_module.current_band_advice(profile_id)
    assert advice["based_on_score"] == 5
    assert advice["band"] == 5
    assert advice["cefr"] == "C1"

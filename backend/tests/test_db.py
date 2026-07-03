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
    yield db_mod


def test_init_db_creates_default_profile(db_module):
    profiles = db_module.list_profiles()
    assert len(profiles) == 1
    assert profiles[0]["name"] == "Learner"


def test_init_db_is_idempotent(db_module):
    db_module.init_db()
    db_module.init_db()
    assert len(db_module.list_profiles()) == 1


def test_insert_and_get_session_roundtrip(db_module):
    profile_id = db_module.first_profile_id()
    session_id = db_module.insert_session(
        mode="general",
        task_type="g01",
        task_title="Talk about your hobby",
        task_prompt="Talk about your hobby",
        transcript="I like reading books.",
        feedback={"encouragement": "Nice job!"},
        score_band=None,
        metrics={"word_count": 5},
        profile_id=profile_id,
        prompt_ref="general:g01",
    )
    row = db_module.get_session(session_id)
    assert row["transcript"] == "I like reading books."
    assert row["feedback"]["encouragement"] == "Nice job!"
    assert row["metrics"]["word_count"] == 5


def test_get_session_missing_returns_none(db_module):
    assert db_module.get_session(99999) is None


def test_sessions_for_prompt_orders_oldest_first(db_module):
    profile_id = db_module.first_profile_id()
    ids = []
    for score in (2, 4, 5):
        sid = db_module.insert_session(
            mode="toefl", task_type="interview", task_title="Free Time", task_prompt="q",
            transcript="t", feedback={}, score_band=score, profile_id=profile_id,
            prompt_ref="toefl:interview:iv_01",
        )
        ids.append(sid)
    attempts = db_module.sessions_for_prompt("toefl:interview:iv_01", profile_id)
    assert [a["id"] for a in attempts] == ids
    assert [a["score_band"] for a in attempts] == [2, 4, 5]


def test_toefl_score_trend_only_includes_scored_toefl_sessions(db_module):
    profile_id = db_module.first_profile_id()
    db_module.insert_session(
        mode="general", task_type="g01", task_title="x", task_prompt="x",
        transcript="x", feedback={}, score_band=None, profile_id=profile_id,
    )
    db_module.insert_session(
        mode="toefl", task_type="interview", task_title="x", task_prompt="x",
        transcript="x", feedback={}, score_band=5, profile_id=profile_id,
    )
    trend = db_module.toefl_score_trend(profile_id)
    assert len(trend) == 1
    assert trend[0]["score_band"] == 5


def test_activity_and_xp_accumulate(db_module):
    profile_id = db_module.first_profile_id()
    db_module.insert_activity(profile_id, "general", 20, ref="session:1")
    db_module.insert_activity(profile_id, "toefl", 55, ref="session:2")
    assert db_module.total_xp(profile_id) == 75
    assert len(db_module.list_activities(profile_id)) == 2


def test_pair_attempt_stats_exclude_unclear_verdicts(db_module):
    profile_id = db_module.first_profile_id()
    db_module.insert_pair_attempt(profile_id, "mp_i_ii", "/i/ vs /ii/ (ship vs sheep)", "ship", "ship", True)
    db_module.insert_pair_attempt(profile_id, "mp_i_ii", "/i/ vs /ii/ (ship vs sheep)", "ship", "sheep", False)
    db_module.insert_pair_attempt(profile_id, "mp_i_ii", "/i/ vs /ii/ (ship vs sheep)", "ship", None, None)
    stats = db_module.pair_contrast_stats(profile_id)
    assert len(stats) == 1
    assert stats[0]["attempts"] == 2  # the "unclear" attempt is excluded
    assert stats[0]["correct"] == 1
    assert stats[0]["accuracy"] == 50.0


def test_achievement_award_is_idempotent(db_module):
    profile_id = db_module.first_profile_id()
    db_module.award_achievement(profile_id, "first_steps")
    db_module.award_achievement(profile_id, "first_steps")
    earned = db_module.earned_achievements(profile_id)
    assert list(earned.keys()) == ["first_steps"]


def test_create_profile_and_switch(db_module):
    new_id = db_module.create_profile("Second Learner", daily_goal_xp=80)
    profiles = db_module.list_profiles()
    assert len(profiles) == 2
    fetched = db_module.get_profile(new_id)
    assert fetched["name"] == "Second Learner"
    assert fetched["daily_goal_xp"] == 80

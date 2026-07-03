import gamification


def test_xp_for_known_and_unknown_kinds():
    assert gamification.xp_for("general") == 20
    assert gamification.xp_for("toefl") == 40
    assert gamification.xp_for("toefl", bonus=15) == 55
    assert gamification.xp_for("not_a_real_kind") == 0


def test_level_from_xp_zero():
    result = gamification.level_from_xp(0)
    assert result == {"level": 1, "xp_into_level": 0, "xp_for_next": 100}


def test_level_from_xp_within_level_one():
    result = gamification.level_from_xp(45)
    assert result["level"] == 1
    assert result["xp_into_level"] == 45


def test_level_from_xp_exact_level_up_boundary():
    result = gamification.level_from_xp(100)
    assert result == {"level": 2, "xp_into_level": 0, "xp_for_next": 200}


def test_level_from_xp_cumulative_thresholds():
    # Level 3 requires 100 + 200 = 300 cumulative XP.
    result = gamification.level_from_xp(300)
    assert result["level"] == 3
    assert result["xp_into_level"] == 0
    assert result["xp_for_next"] == 300


def test_level_from_xp_partway_into_level_two():
    result = gamification.level_from_xp(150)
    assert result["level"] == 2
    assert result["xp_into_level"] == 50


def test_streak_empty_history():
    result = gamification.compute_streak([], today="2026-07-03")
    assert result == {"current": 0, "best": 0, "active_today": False}


def test_streak_active_today_only():
    result = gamification.compute_streak(["2026-07-03"], today="2026-07-03")
    assert result["current"] == 1
    assert result["active_today"] is True


def test_streak_consecutive_days_including_today():
    dates = ["2026-07-01", "2026-07-02", "2026-07-03"]
    result = gamification.compute_streak(dates, today="2026-07-03")
    assert result["current"] == 3
    assert result["best"] == 3


def test_streak_yesterday_keeps_grace_period_alive():
    # Practiced yesterday but not yet today: streak should still show as current, not reset.
    result = gamification.compute_streak(["2026-07-02"], today="2026-07-03")
    assert result["current"] == 1
    assert result["active_today"] is False


def test_streak_gap_two_days_ago_breaks_current_streak():
    result = gamification.compute_streak(["2026-07-01"], today="2026-07-03")
    assert result["current"] == 0
    assert result["best"] == 1


def test_streak_best_survives_a_later_gap():
    # A 3-day run in the past, then an isolated day today with a gap between.
    dates = ["2026-06-20", "2026-06-21", "2026-06-22", "2026-07-03"]
    result = gamification.compute_streak(dates, today="2026-07-03")
    assert result["best"] == 3
    assert result["current"] == 1


def test_achievement_conditions_first_steps():
    snapshot = {
        "session_count": 1, "streak_best": 1, "total_xp": 20, "best_toefl_score": None,
        "shadowing_attempts": 0, "pair_attempts": 0, "pair_accuracy": None,
    }
    conditions = gamification._conditions(snapshot)
    assert conditions["first_steps"] is True
    assert conditions["getting_serious"] is False
    assert conditions["perfect_score"] is False


def test_achievement_conditions_perfect_score_requires_six():
    snapshot = {
        "session_count": 5, "streak_best": 2, "total_xp": 100, "best_toefl_score": 6,
        "shadowing_attempts": 0, "pair_attempts": 0, "pair_accuracy": None,
    }
    conditions = gamification._conditions(snapshot)
    assert conditions["high_score"] is True
    assert conditions["perfect_score"] is True


def test_achievement_conditions_sharp_ears_needs_volume_and_accuracy():
    low_volume = {
        "session_count": 1, "streak_best": 1, "total_xp": 0, "best_toefl_score": None,
        "shadowing_attempts": 0, "pair_attempts": 5, "pair_accuracy": 95,
    }
    assert gamification._conditions(low_volume)["sharp_ears"] is False

    qualifies = dict(low_volume, pair_attempts=25, pair_accuracy=92)
    assert gamification._conditions(qualifies)["sharp_ears"] is True


def test_every_achievement_has_a_condition():
    snapshot = {
        "session_count": 0, "streak_best": 0, "total_xp": 0, "best_toefl_score": None,
        "shadowing_attempts": 0, "pair_attempts": 0, "pair_accuracy": None,
    }
    conditions = gamification._conditions(snapshot)
    for achievement in gamification.ACHIEVEMENTS:
        assert achievement["id"] in conditions, f"missing condition for {achievement['id']}"

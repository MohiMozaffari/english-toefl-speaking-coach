"""XP, levels, streaks, daily goals, and achievements. All local, all deterministic."""

from __future__ import annotations

from datetime import datetime, timedelta

import db

# XP awarded per activity kind. Score bonuses are added by callers where relevant.
XP_RULES = {
    "general": 20,
    "toefl": 40,
    "shadowing_sentence": 3,
    "pronunciation_pair": 2,
    "pronunciation_line": 3,
    "listening_quiz": 10,
}


def xp_for(kind: str, bonus: int = 0) -> int:
    return XP_RULES.get(kind, 0) + bonus


def level_from_xp(total_xp: int) -> dict:
    """Level n needs 100*n XP beyond level n-1 (100, 200, 300, ... cumulative)."""
    level = 1
    remaining = total_xp
    need = 100
    while remaining >= need:
        remaining -= need
        level += 1
        need = 100 * level
    return {"level": level, "xp_into_level": remaining, "xp_for_next": need}


def _local_date(iso_utc: str) -> str:
    """Stored timestamps are UTC; streaks should follow the user's wall clock."""
    dt = datetime.fromisoformat(iso_utc)
    return dt.astimezone().date().isoformat()


def activity_dates(profile_id: int) -> list[str]:
    acts = db.list_activities(profile_id, limit=5000)
    return sorted({_local_date(a["created_at"]) for a in acts})


def compute_streak(dates: list[str], today: str | None = None) -> dict:
    """Current streak = consecutive days with activity ending today or yesterday
    (yesterday keeps the streak alive until the day is truly missed)."""
    if today is None:
        today = datetime.now().astimezone().date().isoformat()
    date_set = set(dates)
    today_d = datetime.fromisoformat(today).date()

    anchor = None
    if today in date_set:
        anchor = today_d
    elif (today_d - timedelta(days=1)).isoformat() in date_set:
        anchor = today_d - timedelta(days=1)

    current = 0
    if anchor:
        d = anchor
        while d.isoformat() in date_set:
            current += 1
            d -= timedelta(days=1)

    best = 0
    run = 0
    prev = None
    for ds in dates:
        d = datetime.fromisoformat(ds).date()
        run = run + 1 if prev is not None and d - prev == timedelta(days=1) else 1
        best = max(best, run)
        prev = d
    return {"current": current, "best": best, "active_today": today in date_set}


def today_xp(profile_id: int) -> int:
    today = datetime.now().astimezone().date().isoformat()
    return sum(a["xp"] for a in db.list_activities(profile_id, limit=500) if _local_date(a["created_at"]) == today)


def weekly_activity(profile_id: int) -> list[dict]:
    """XP and activity counts per day for the last 7 days (oldest first)."""
    acts = db.list_activities(profile_id, limit=2000)
    today = datetime.now().astimezone().date()
    days = [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    buckets = {d: {"date": d, "xp": 0, "activities": 0} for d in days}
    for a in acts:
        d = _local_date(a["created_at"])
        if d in buckets:
            buckets[d]["xp"] += a["xp"]
            buckets[d]["activities"] += 1
    return [buckets[d] for d in days]


# --- Achievements ----------------------------------------------------------------
# Conditions are pure functions over a stats snapshot so they're easy to test.

ACHIEVEMENTS = [
    {"id": "first_steps", "icon": "🎤", "title": "First Steps", "description": "Complete your first practice attempt."},
    {"id": "getting_serious", "icon": "📚", "title": "Getting Serious", "description": "Complete 10 practice attempts."},
    {"id": "marathon", "icon": "🏃", "title": "Marathon", "description": "Complete 50 practice attempts."},
    {"id": "streak_3", "icon": "🔥", "title": "On a Roll", "description": "Practice 3 days in a row."},
    {"id": "streak_7", "icon": "⚡", "title": "Unstoppable", "description": "Practice 7 days in a row."},
    {"id": "streak_30", "icon": "🌟", "title": "Habit Formed", "description": "Practice 30 days in a row."},
    {"id": "xp_500", "icon": "💎", "title": "XP Collector", "description": "Earn 500 total XP."},
    {"id": "xp_2000", "icon": "👑", "title": "XP Royalty", "description": "Earn 2,000 total XP."},
    {"id": "high_score", "icon": "🎯", "title": "High Scorer", "description": "Score 5 or higher on a TOEFL task."},
    {"id": "perfect_score", "icon": "🏆", "title": "Perfect Six", "description": "Score 6 on a TOEFL task."},
    {"id": "shadow_50", "icon": "🗣️", "title": "Echo Master", "description": "Shadow 50 sentences."},
    {"id": "sharp_ears", "icon": "👂", "title": "Sharp Ears", "description": "Reach 90% on 20+ minimal-pair drills."},
]


def _conditions(snapshot: dict):
    s = snapshot
    return {
        "first_steps": s["session_count"] >= 1,
        "getting_serious": s["session_count"] >= 10,
        "marathon": s["session_count"] >= 50,
        "streak_3": s["streak_best"] >= 3,
        "streak_7": s["streak_best"] >= 7,
        "streak_30": s["streak_best"] >= 30,
        "xp_500": s["total_xp"] >= 500,
        "xp_2000": s["total_xp"] >= 2000,
        "high_score": (s["best_toefl_score"] or 0) >= 5,
        "perfect_score": (s["best_toefl_score"] or 0) >= 6,
        "shadow_50": s["shadowing_attempts"] >= 50,
        "sharp_ears": s["pair_attempts"] >= 20 and (s["pair_accuracy"] or 0) >= 90,
    }


def evaluate_achievements(profile_id: int, snapshot: dict) -> list[str]:
    """Award any newly-met achievements; returns ids newly earned this call."""
    earned = db.earned_achievements(profile_id)
    newly = []
    for ach_id, met in _conditions(snapshot).items():
        if met and ach_id not in earned:
            db.award_achievement(profile_id, ach_id)
            newly.append(ach_id)
    return newly


def achievements_view(profile_id: int) -> list[dict]:
    earned = db.earned_achievements(profile_id)
    return [
        {**a, "earned": a["id"] in earned, "earned_at": earned.get(a["id"])}
        for a in ACHIEVEMENTS
    ]

"""Dashboard analytics: aggregates sessions, metrics, XP, and skill signals.

The skill radar blends the best local evidence available for each axis and is
deliberately transparent — every axis documents its formula. Axes are 0-100.
"""

from __future__ import annotations

import coach
import db
import gamification


def _scale(value: float, points: list[tuple[float, float]]) -> float:
    """Piecewise-linear map through (input, output) anchor points."""
    if value <= points[0][0]:
        return points[0][1]
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if value <= x2:
            return y1 + (value - x1) / (x2 - x1) * (y2 - y1)
    return points[-1][1]


def _avg(values: list[float]) -> float | None:
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def skill_radar(profile_id: int) -> list[dict]:
    sessions = db.recent_sessions_full(profile_id, limit=20)
    metrics_list = [s["metrics"] for s in sessions if s.get("metrics")]
    pair_stats = db.pair_contrast_stats(profile_id)
    shadow = db.shadowing_stats(profile_id)

    # Numeric sub-scores (1-6) from AI feedback, when present.
    def sub_scores(key: str) -> list[float]:
        return [
            s["feedback"]["category_scores"][key]
            for s in sessions
            if isinstance(s["feedback"].get("category_scores"), dict)
            and isinstance(s["feedback"]["category_scores"].get(key), (int, float))
        ]

    # Fluency: articulation rate mapped to naturalness, minus pause pressure.
    art = _avg([m.get("articulation_wpm") for m in metrics_list])
    fluency = None
    if art:
        fluency = _scale(art, [(50, 20), (90, 55), (120, 85), (170, 90), (220, 60)])
        total_words = sum(m.get("word_count", 0) for m in metrics_list) or 1
        long_pause_rate = sum(m.get("long_pause_count", 0) for m in metrics_list) / total_words * 10
        fluency = max(fluency - min(long_pause_rate * 20, 30), 0)
    llm_fluency = _avg(sub_scores("fluency"))
    if llm_fluency:
        fluency = _avg([fluency, llm_fluency / 6 * 100]) if fluency is not None else llm_fluency / 6 * 100

    # Pronunciation: whisper confidence blended with minimal-pair accuracy.
    conf = _avg([m.get("avg_word_confidence") for m in metrics_list])
    pron_parts = []
    if conf:
        pron_parts.append(_scale(conf, [(0.3, 20), (0.55, 50), (0.75, 75), (0.92, 95)]))
    decisive = [p for p in pair_stats if p["attempts"] >= 3]
    if decisive:
        pron_parts.append(_avg([p["accuracy"] for p in decisive]))
    pronunciation = _avg(pron_parts)

    # Vocabulary: type-token ratio mapped.
    ttr = _avg([m.get("type_token_ratio") for m in metrics_list])
    vocabulary = _scale(ttr, [(0.25, 25), (0.42, 50), (0.55, 75), (0.72, 95)]) if ttr else None

    # Accuracy: LLM accuracy sub-score, else shadowing word accuracy.
    acc_scores = sub_scores("accuracy")
    accuracy = _avg(acc_scores)
    accuracy = accuracy / 6 * 100 if accuracy else (shadow.get("avg_accuracy") or None)

    # Coherence: LLM coherence/topic sub-score only (no honest local proxy).
    coh = _avg(sub_scores("coherence"))
    coherence = coh / 6 * 100 if coh else None

    axes = [
        {"axis": "Fluency", "value": fluency},
        {"axis": "Pronunciation", "value": pronunciation},
        {"axis": "Vocabulary", "value": vocabulary},
        {"axis": "Accuracy", "value": accuracy},
        {"axis": "Coherence", "value": coherence},
    ]
    return [{"axis": a["axis"], "value": round(a["value"], 1) if a["value"] is not None else None} for a in axes]


def dashboard(profile_id: int) -> dict:
    profile = db.get_profile(profile_id) or {}
    sessions = db.recent_sessions_full(profile_id, limit=200)
    metrics_list = [s["metrics"] for s in sessions if s.get("metrics")]

    total_xp = db.total_xp(profile_id)
    dates = gamification.activity_dates(profile_id)
    streak = gamification.compute_streak(dates)
    today = gamification.today_xp(profile_id)

    minutes_spoken = sum(m.get("duration_seconds", 0) for m in metrics_list) / 60
    words_spoken = sum(m.get("word_count", 0) for m in metrics_list)

    trend_metrics = [
        {
            "created_at": s["created_at"],
            "wpm": s["metrics"].get("articulation_wpm"),
            "pauses": s["metrics"].get("long_pause_count"),
            "ttr": s["metrics"].get("type_token_ratio"),
            "confidence": s["metrics"].get("avg_word_confidence"),
        }
        for s in reversed(sessions)
        if s.get("metrics")
    ][-30:]

    snapshot = coach.build_learner_snapshot(profile_id)
    pair_stats = db.pair_contrast_stats(profile_id)
    shadow = db.shadowing_stats(profile_id)

    ach_snapshot = {
        "session_count": len(sessions),
        "streak_best": streak["best"],
        "total_xp": total_xp,
        "best_toefl_score": max((s["score_band"] for s in sessions if s.get("score_band")), default=None),
        "shadowing_attempts": shadow["attempts"],
        "pair_attempts": sum(p["attempts"] for p in pair_stats),
        "pair_accuracy": (
            sum(p["correct"] for p in pair_stats) / max(sum(p["attempts"] for p in pair_stats), 1) * 100
            if pair_stats
            else None
        ),
    }
    gamification.evaluate_achievements(profile_id, ach_snapshot)

    return {
        "profile": profile,
        "xp": {"total": total_xp, **gamification.level_from_xp(total_xp), "today": today,
               "daily_goal": profile.get("daily_goal_xp", 50)},
        "streak": streak,
        "totals": {
            "sessions": len(sessions),
            "minutes_spoken": round(minutes_spoken, 1),
            "words_spoken": words_spoken,
            "shadowing_attempts": shadow["attempts"],
            "pair_attempts": ach_snapshot["pair_attempts"],
        },
        "weekly": gamification.weekly_activity(profile_id),
        "score_trend": db.toefl_score_trend(profile_id),
        "radar": skill_radar(profile_id),
        "delivery_trend": trend_metrics,
        "weaknesses": coach.weaknesses_from_snapshot(snapshot),
        "recommendations": coach.recommendations(profile_id),
        "achievements": gamification.achievements_view(profile_id),
        "weak_contrasts": [p for p in pair_stats if p["attempts"] >= 3],
    }

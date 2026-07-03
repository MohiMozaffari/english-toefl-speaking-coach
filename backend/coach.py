"""The personalized coach: learner memory + rule-based recommendations.

Memory is built from real evidence in the local database — recent AI feedback,
delivery metrics, minimal-pair results — and is (a) injected into LLM prompts so
feedback references the learner's history, and (b) shown on the dashboard.

Recommendations are deterministic rules mapping observed weaknesses to specific
exercises inside the app. Rule-based on purpose: transparent, offline, testable.
"""

from __future__ import annotations

import db

# Thresholds for flagging a delivery habit as a weakness.
SLOW_WPM = 95
FAST_WPM = 190
HIGH_PAUSE_RATE = 0.5   # long pauses per 10 words
LOW_TTR = 0.42
HIGH_FILLER_RATE = 1.0  # fillers per 10 words
WEAK_PAIR_ACCURACY = 75
LOW_CONFIDENCE = 0.55


def build_learner_snapshot(profile_id: int) -> dict:
    """Aggregate recent evidence into a compact weakness/strength picture."""
    sessions = db.recent_sessions_full(profile_id, limit=15)
    pair_stats = db.pair_contrast_stats(profile_id)
    shadow = db.shadowing_stats(profile_id)

    focus_points = []
    for s in sessions:
        focus = s["feedback"].get("focus_next") or s["feedback"].get("overall_tip")
        if focus:
            focus_points.append(focus)

    metrics_list = [s["metrics"] for s in sessions if s.get("metrics")]
    n = len(metrics_list)
    avg = lambda key: sum(m.get(key, 0) for m in metrics_list) / n if n else 0  # noqa: E731

    total_words = sum(m.get("word_count", 0) for m in metrics_list)
    long_pause_rate = (
        sum(m.get("long_pause_count", 0) for m in metrics_list) / total_words * 10 if total_words else 0
    )
    filler_rate = sum(m.get("filler_count", 0) for m in metrics_list) / total_words * 10 if total_words else 0

    low_conf_words = []
    seen = set()
    for m in metrics_list:
        for entry in m.get("low_confidence_words", []):
            if entry["word"] not in seen:
                seen.add(entry["word"])
                low_conf_words.append(entry["word"])

    weak_contrasts = [p for p in pair_stats if p["attempts"] >= 4 and p["accuracy"] < WEAK_PAIR_ACCURACY]

    scores = [s["score_band"] for s in sessions if s.get("score_band")]

    return {
        "session_count": len(sessions),
        "recent_focus_points": focus_points[:5],
        "avg_wpm": round(avg("wpm"), 1),
        "avg_articulation_wpm": round(avg("articulation_wpm"), 1),
        "long_pause_rate": round(long_pause_rate, 2),
        "filler_rate": round(filler_rate, 2),
        "avg_ttr": round(avg("type_token_ratio"), 3),
        "avg_word_confidence": round(avg("avg_word_confidence"), 3),
        "tricky_words": low_conf_words[:10],
        "weak_contrasts": weak_contrasts,
        "recent_scores": scores[:8],
        "shadowing_avg_accuracy": shadow.get("avg_accuracy"),
    }


def weaknesses_from_snapshot(snap: dict) -> list[dict]:
    """Tagged weaknesses, each with evidence — feeds recommendations and the dashboard."""
    out = []
    if snap["session_count"] == 0:
        return out
    wpm = snap["avg_articulation_wpm"]
    if 0 < wpm < SLOW_WPM:
        out.append({"tag": "slow_pace", "label": "Slow speaking pace",
                    "evidence": f"Average articulation rate {wpm} words/min (natural range is 110-170)."})
    elif wpm > FAST_WPM:
        out.append({"tag": "rushed_pace", "label": "Rushed delivery",
                    "evidence": f"Average articulation rate {wpm} words/min — clarity suffers above ~180."})
    if snap["long_pause_rate"] > HIGH_PAUSE_RATE:
        out.append({"tag": "frequent_pauses", "label": "Frequent long pauses",
                    "evidence": f"{snap['long_pause_rate']} long pauses per 10 words spoken."})
    if snap["filler_rate"] > HIGH_FILLER_RATE:
        out.append({"tag": "fillers", "label": "Heavy filler-word use",
                    "evidence": f"{snap['filler_rate']} fillers (um, uh, like) per 10 words."})
    if 0 < snap["avg_ttr"] < LOW_TTR:
        out.append({"tag": "limited_vocabulary", "label": "Limited vocabulary range",
                    "evidence": f"Type-token ratio {snap['avg_ttr']} — answers reuse the same words."})
    if 0 < snap["avg_word_confidence"] < LOW_CONFIDENCE:
        out.append({"tag": "unclear_pronunciation", "label": "Words often unclear",
                    "evidence": "The speech recognizer frequently struggles with your words — a strong sign of pronunciation issues."})
    for contrast in snap["weak_contrasts"][:3]:
        out.append({
            "tag": f"pair:{contrast['contrast']}",
            "label": f"Weak sound contrast {contrast['contrast']}",
            "evidence": f"{contrast['accuracy']}% accuracy over {contrast['attempts']} minimal-pair drills.",
        })
    return out


# Maps weakness tags to concrete exercises in this app.
_RECOMMENDATION_RULES = {
    "slow_pace": {"module": "shadowing", "route": "/shadowing",
                  "action": "Shadow 2 passages today at normal speed — match the rhythm, not just the words."},
    "rushed_pace": {"module": "shadowing", "route": "/shadowing",
                    "action": "Shadow at 0.75x speed and force yourself to match the slower pacing exactly."},
    "frequent_pauses": {"module": "toefl", "route": "/toefl",
                        "action": "Do one Interview set daily — answering without prep time trains you to keep talking."},
    "fillers": {"module": "general", "route": "/general",
                "action": "Record a 1-minute answer and replace every 'um' with a silent breath. Repeat the same topic twice."},
    "limited_vocabulary": {"module": "general", "route": "/general",
                           "action": "Pick an Opinions topic and deliberately use 3 words you've never used before."},
    "unclear_pronunciation": {"module": "pronunciation", "route": "/pronunciation",
                              "action": "Run 10 minimal-pair drills to find exactly which sounds the recognizer mishears."},
}


def recommendations(profile_id: int) -> list[dict]:
    snap = build_learner_snapshot(profile_id)
    weaknesses = weaknesses_from_snapshot(snap)
    recs = []
    for w in weaknesses:
        if w["tag"].startswith("pair:"):
            recs.append({
                "title": f"Drill {w['tag'][5:]}",
                "reason": w["evidence"],
                "module": "pronunciation",
                "route": "/pronunciation",
                "action": f"Practice the {w['tag'][5:]} minimal pairs until you pass 85% accuracy.",
            })
        elif w["tag"] in _RECOMMENDATION_RULES:
            rule = _RECOMMENDATION_RULES[w["tag"]]
            recs.append({"title": w["label"], "reason": w["evidence"], **rule})
    if not recs:
        if snap["session_count"] == 0:
            recs.append({"title": "Start with a TOEFL baseline", "reason": "No attempts yet — a first score gives the coach something to work with.",
                         "module": "toefl", "route": "/toefl", "action": "Complete one Listen and Repeat set and one Interview set."})
        else:
            recs.append({"title": "Keep the streak going", "reason": "No standout weaknesses in recent sessions — consistency is now the multiplier.",
                         "module": "toefl", "route": "/toefl", "action": "Alternate task types daily and re-attempt an old set to compare scores."})
    return recs[:5]


def learner_context_for_llm(profile_id: int) -> str:
    """Compact history block injected into feedback prompts, so the AI coach
    remembers this learner. Empty string when there's nothing useful yet."""
    snap = build_learner_snapshot(profile_id)
    if snap["session_count"] == 0:
        return ""
    lines = ["Learner background (from their practice history — reference it when relevant):"]
    if snap["recent_scores"]:
        lines.append(f"- Recent TOEFL task scores (newest first): {snap['recent_scores']}")
    if snap["avg_articulation_wpm"]:
        lines.append(f"- Typical speaking rate: {snap['avg_articulation_wpm']} wpm; long pauses per 10 words: {snap['long_pause_rate']}; fillers per 10 words: {snap['filler_rate']}")
    if snap["recent_focus_points"]:
        lines.append(f"- Recent coaching focus points: {'; '.join(snap['recent_focus_points'][:3])}")
    if snap["tricky_words"]:
        lines.append(f"- Words the speech recognizer often struggles to catch from them: {', '.join(snap['tricky_words'][:6])}")
    if snap["weak_contrasts"]:
        contrasts = ", ".join(f"{c['contrast']} ({c['accuracy']}%)" for c in snap["weak_contrasts"][:3])
        lines.append(f"- Confirmed weak sound contrasts from minimal-pair drills: {contrasts}")
    lines.append("If a past focus point shows improvement in this attempt, acknowledge it explicitly.")
    return "\n".join(lines)

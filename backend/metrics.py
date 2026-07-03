"""Local speech-delivery metrics computed from faster-whisper word timestamps.

Everything here is pure computation on already-transcribed data — no network,
no models. These numbers feed the analytics dashboard and the coach memory:
speaking speed, pausing behaviour, vocabulary diversity, filler habits, and a
pronunciation-confidence proxy (whisper's per-word probability drops sharply on
mispronounced or garbled words, which makes low-probability words useful
"listen again" candidates even without a forced-alignment pipeline).
"""

from __future__ import annotations

import re
from typing import Iterable

# Hesitation fillers whisper commonly transcribes verbatim.
FILLER_WORDS = {"um", "uh", "er", "ah", "erm", "uhm", "hmm", "mm", "mhm"}
# Multi-word soft fillers, counted from the joined text.
SOFT_FILLER_PATTERNS = (r"\byou know\b", r"\bi mean\b", r"\bsort of\b", r"\bkind of\b")

PAUSE_THRESHOLD_S = 0.35
LONG_PAUSE_THRESHOLD_S = 1.0
LOW_CONFIDENCE_THRESHOLD = 0.45
MAX_LOW_CONFIDENCE_WORDS = 8


def _norm(word: str) -> str:
    # Keep digits — whisper sometimes emits numbers as "2024" rather than spelling
    # them out, and stripping digits would silently drop those words entirely.
    return re.sub(r"[^a-z0-9']", "", word.lower().strip())


def compute_metrics(words: list[dict], duration: float) -> dict:
    """Compute delivery metrics for one recording.

    `words` entries: {"word": str, "start": float, "end": float, "probability": float}
    `duration`: audio file duration in seconds.
    """
    norm_words = [w for w in ((_norm(w["word"]), w) for w in words) if w[0]]
    word_count = len(norm_words)
    if word_count == 0:
        return {
            "word_count": 0,
            "duration_seconds": round(duration, 2),
            "speech_span_seconds": 0.0,
            "wpm": 0.0,
            "articulation_wpm": 0.0,
            "pause_count": 0,
            "long_pause_count": 0,
            "total_pause_seconds": 0.0,
            "avg_pause_seconds": 0.0,
            "filler_count": 0,
            "type_token_ratio": 0.0,
            "unique_word_count": 0,
            "avg_word_confidence": 0.0,
            "low_confidence_words": [],
        }

    first_start = words[0]["start"]
    last_end = words[-1]["end"]
    span = max(last_end - first_start, 0.001)

    pauses = []
    for prev, cur in zip(words, words[1:]):
        gap = cur["start"] - prev["end"]
        if gap >= PAUSE_THRESHOLD_S:
            pauses.append(gap)
    total_pause = sum(pauses)
    long_pauses = [p for p in pauses if p >= LONG_PAUSE_THRESHOLD_S]

    speaking_time = max(span - total_pause, 0.001)

    filler_count = sum(1 for norm, _ in norm_words if norm in FILLER_WORDS)
    joined = " ".join(norm for norm, _ in norm_words)
    for pattern in SOFT_FILLER_PATTERNS:
        filler_count += len(re.findall(pattern, joined))

    content_words = [norm for norm, _ in norm_words if norm not in FILLER_WORDS]
    unique_words = set(content_words)
    ttr = len(unique_words) / len(content_words) if content_words else 0.0

    probs = [w.get("probability") for w in words if w.get("probability") is not None]
    avg_conf = sum(probs) / len(probs) if probs else 0.0

    low_conf = []
    seen = set()
    for norm, w in norm_words:
        prob = w.get("probability")
        if prob is not None and prob < LOW_CONFIDENCE_THRESHOLD and norm not in seen and norm not in FILLER_WORDS:
            seen.add(norm)
            low_conf.append({"word": norm, "confidence": round(prob, 2)})
        if len(low_conf) >= MAX_LOW_CONFIDENCE_WORDS:
            break

    return {
        "word_count": word_count,
        "duration_seconds": round(duration, 2),
        "speech_span_seconds": round(span, 2),
        "wpm": round(word_count / span * 60, 1),
        "articulation_wpm": round(word_count / speaking_time * 60, 1),
        "pause_count": len(pauses),
        "long_pause_count": len(long_pauses),
        "total_pause_seconds": round(total_pause, 2),
        "avg_pause_seconds": round(total_pause / len(pauses), 2) if pauses else 0.0,
        "filler_count": filler_count,
        "type_token_ratio": round(ttr, 3),
        "unique_word_count": len(unique_words),
        "avg_word_confidence": round(avg_conf, 3),
        "low_confidence_words": low_conf,
    }


def combine_metrics(metrics_list: Iterable[dict]) -> dict:
    """Aggregate per-item metrics from a multi-recording attempt into one summary.

    Rates are re-derived from summed words and summed speech spans, so short
    items don't get equal weight with long ones.
    """
    metrics_list = [m for m in metrics_list if m and m.get("word_count", 0) > 0]
    if not metrics_list:
        return compute_metrics([], 0.0)

    total_words = sum(m["word_count"] for m in metrics_list)
    total_span = sum(m["speech_span_seconds"] for m in metrics_list)
    total_duration = sum(m["duration_seconds"] for m in metrics_list)
    total_pause = sum(m["total_pause_seconds"] for m in metrics_list)
    pause_count = sum(m["pause_count"] for m in metrics_list)
    speaking_time = max(total_span - total_pause, 0.001)

    conf_weights = [(m["avg_word_confidence"], m["word_count"]) for m in metrics_list]
    avg_conf = sum(c * n for c, n in conf_weights) / total_words

    # TTR over the union isn't recoverable from summaries; use the word-weighted mean.
    ttr = sum(m["type_token_ratio"] * m["word_count"] for m in metrics_list) / total_words

    low_conf = []
    seen = set()
    for m in metrics_list:
        for entry in m.get("low_confidence_words", []):
            if entry["word"] not in seen:
                seen.add(entry["word"])
                low_conf.append(entry)
            if len(low_conf) >= MAX_LOW_CONFIDENCE_WORDS:
                break

    return {
        "word_count": total_words,
        "duration_seconds": round(total_duration, 2),
        "speech_span_seconds": round(total_span, 2),
        "wpm": round(total_words / max(total_span, 0.001) * 60, 1),
        "articulation_wpm": round(total_words / speaking_time * 60, 1),
        "pause_count": pause_count,
        "long_pause_count": sum(m["long_pause_count"] for m in metrics_list),
        "total_pause_seconds": round(total_pause, 2),
        "avg_pause_seconds": round(total_pause / pause_count, 2) if pause_count else 0.0,
        "filler_count": sum(m["filler_count"] for m in metrics_list),
        "type_token_ratio": round(ttr, 3),
        "unique_word_count": sum(m["unique_word_count"] for m in metrics_list),
        "avg_word_confidence": round(avg_conf, 3),
        "low_confidence_words": low_conf,
    }

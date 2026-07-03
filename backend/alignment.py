"""Word-level alignment between a target sentence and what the learner actually said.

Powers shadowing mode: matched / substituted / missing / extra words, an accuracy
percentage, and a timing comparison. Pure text logic — testable without audio.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

# Common contractions expanded so "I am" vs "I'm" counts as a match.
_EQUIVALENTS = {
    "i'm": "i am", "you're": "you are", "he's": "he is", "she's": "she is",
    "it's": "it is", "we're": "we are", "they're": "they are", "i've": "i have",
    "you've": "you have", "we've": "we have", "they've": "they have",
    "i'll": "i will", "you'll": "you will", "he'll": "he will", "she'll": "she will",
    "we'll": "we will", "they'll": "they will", "i'd": "i would", "you'd": "you would",
    "don't": "do not", "doesn't": "does not", "didn't": "did not", "can't": "cannot",
    "won't": "will not", "isn't": "is not", "aren't": "are not", "wasn't": "was not",
    "weren't": "were not", "haven't": "have not", "hasn't": "has not",
    "wouldn't": "would not", "couldn't": "could not", "shouldn't": "should not",
    "that's": "that is", "there's": "there is", "what's": "what is", "let's": "let us",
}


def normalize_words(text: str) -> list[str]:
    text = text.lower()
    for contraction, expansion in _EQUIVALENTS.items():
        text = re.sub(rf"\b{re.escape(contraction)}\b", expansion, text)
    words = re.findall(r"[a-z']+", text)
    return [w.strip("'") for w in words if w.strip("'")]


def _similar(a: str, b: str) -> bool:
    """Near-match for close-but-imperfect words (walked/walk, tomato/tomatoes)."""
    if a == b:
        return True
    if len(a) >= 4 and len(b) >= 4 and SequenceMatcher(None, a, b).ratio() >= 0.8:
        return True
    return False


def align(target_text: str, spoken_text: str) -> dict:
    """Align spoken words against the target sentence.

    Returns per-target-word statuses plus extra words and summary accuracy:
      target_words: [{"word", "status": matched|close|missing}]
      extra_words:  words said that aren't in the target
      accuracy:     % of target words matched (close counts as half)
    """
    target = normalize_words(target_text)
    spoken = normalize_words(spoken_text)

    sm = SequenceMatcher(None, target, spoken, autojunk=False)
    target_status = ["missing"] * len(target)
    extra = []

    for op, t1, t2, s1, s2 in sm.get_opcodes():
        if op == "equal":
            for i in range(t1, t2):
                target_status[i] = "matched"
        elif op == "replace":
            # Pair up replaced ranges; check near-matches.
            t_range = list(range(t1, t2))
            s_range = list(range(s1, s2))
            for offset in range(max(len(t_range), len(s_range))):
                ti = t_range[offset] if offset < len(t_range) else None
                si = s_range[offset] if offset < len(s_range) else None
                if ti is not None and si is not None:
                    target_status[ti] = "close" if _similar(target[ti], spoken[si]) else "missing"
                    if target_status[ti] == "missing":
                        extra.append(spoken[si])
                elif si is not None:
                    extra.append(spoken[si])
        elif op == "insert":
            extra.extend(spoken[s1:s2])
        # "delete" → target words stay "missing"

    matched = sum(1 for s in target_status if s == "matched")
    close = sum(1 for s in target_status if s == "close")
    accuracy = (matched + 0.5 * close) / len(target) * 100 if target else 0.0

    return {
        "target_words": [{"word": w, "status": s} for w, s in zip(target, target_status)],
        "extra_words": extra[:10],
        "matched": matched,
        "close": close,
        "missing": len(target) - matched - close,
        "accuracy": round(accuracy, 1),
    }


def fluency_score(metrics: dict, target_word_count: int) -> float:
    """0-100 delivery score for one shadowed sentence, from local metrics only.

    Rewards natural pace (110-170 WPM articulation) and penalizes long pauses
    and fillers. Transparent by design — not a hidden model.
    """
    if not metrics or metrics.get("word_count", 0) == 0:
        return 0.0
    score = 100.0
    wpm = metrics.get("articulation_wpm", 0)
    if wpm < 60:
        score -= 30
    elif wpm < 90:
        score -= 15
    elif wpm > 220:
        score -= 20
    elif wpm > 180:
        score -= 8
    score -= min(metrics.get("long_pause_count", 0) * 12, 36)
    score -= min(metrics.get("pause_count", 0) * 4, 20)
    score -= min(metrics.get("filler_count", 0) * 8, 24)
    # Saying far fewer words than the target also breaks flow.
    if target_word_count:
        coverage = metrics.get("word_count", 0) / target_word_count
        if coverage < 0.7:
            score -= 20
    return round(max(score, 0.0), 1)

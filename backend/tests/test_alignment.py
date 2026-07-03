import alignment


def test_exact_match_is_full_accuracy():
    diff = alignment.align("The cat sat on the mat.", "The cat sat on the mat.")
    assert diff["accuracy"] == 100.0
    assert all(w["status"] == "matched" for w in diff["target_words"])
    assert diff["extra_words"] == []


def test_completely_different_speech_is_all_missing():
    diff = alignment.align("The cat sat on the mat.", "Bananas are yellow fruit.")
    assert diff["accuracy"] < 30.0
    assert any(w["status"] == "missing" for w in diff["target_words"])


def test_contraction_equivalence():
    diff = alignment.align("I am happy today.", "I'm happy today.")
    assert diff["accuracy"] == 100.0


def test_near_miss_word_marked_close_not_missing():
    diff = alignment.align("I walked to the store.", "I walk to the store.")
    statuses = {w["word"]: w["status"] for w in diff["target_words"]}
    assert statuses["walked"] in ("close", "matched")
    assert diff["accuracy"] > 80.0


def test_extra_words_captured():
    diff = alignment.align("Hello there.", "Well hello there my friend.")
    assert "well" in diff["extra_words"] or "my" in diff["extra_words"] or "friend" in diff["extra_words"]


def test_empty_target_gives_zero_accuracy_not_error():
    diff = alignment.align("", "some words")
    assert diff["accuracy"] == 0.0
    assert diff["target_words"] == []


def test_normalize_words_strips_punctuation_and_lowercases():
    assert alignment.normalize_words("Hello, World! It's great.") == ["hello", "world", "it", "is", "great"]


def test_fluency_score_penalizes_slow_pace():
    slow_metrics = {"word_count": 10, "articulation_wpm": 40, "long_pause_count": 0, "pause_count": 0, "filler_count": 0}
    fast_metrics = {"word_count": 10, "articulation_wpm": 140, "long_pause_count": 0, "pause_count": 0, "filler_count": 0}
    assert alignment.fluency_score(slow_metrics, 10) < alignment.fluency_score(fast_metrics, 10)


def test_fluency_score_penalizes_long_pauses_and_fillers():
    clean = {"word_count": 10, "articulation_wpm": 140, "long_pause_count": 0, "pause_count": 0, "filler_count": 0}
    messy = {"word_count": 10, "articulation_wpm": 140, "long_pause_count": 2, "pause_count": 3, "filler_count": 4}
    assert alignment.fluency_score(messy, 10) < alignment.fluency_score(clean, 10)


def test_fluency_score_floor_is_zero():
    terrible = {"word_count": 10, "articulation_wpm": 20, "long_pause_count": 10, "pause_count": 10, "filler_count": 10}
    assert alignment.fluency_score(terrible, 10) >= 0.0


def test_fluency_score_empty_metrics_is_zero():
    assert alignment.fluency_score({}, 5) == 0.0
    assert alignment.fluency_score({"word_count": 0}, 5) == 0.0

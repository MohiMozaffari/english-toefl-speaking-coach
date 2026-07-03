import metrics


def _word(text, start, end, prob=0.95):
    return {"word": text, "start": start, "end": end, "probability": prob}


def test_empty_words_returns_zeroed_metrics():
    result = metrics.compute_metrics([], 3.0)
    assert result["word_count"] == 0
    assert result["wpm"] == 0.0
    assert result["low_confidence_words"] == []


def test_fluent_speech_no_pauses():
    # 5 words spoken back-to-back over 2 seconds -> 150 wpm, no pauses.
    words = [
        _word("this", 0.0, 0.4),
        _word("is", 0.4, 0.6),
        _word("a", 0.6, 0.7),
        _word("fluent", 0.7, 1.2),
        _word("sentence", 1.2, 2.0),
    ]
    result = metrics.compute_metrics(words, 2.0)
    assert result["word_count"] == 5
    assert result["pause_count"] == 0
    assert result["wpm"] == 150.0
    assert result["articulation_wpm"] == 150.0


def test_long_pause_detected():
    words = [
        _word("hello", 0.0, 0.5),
        _word("world", 2.0, 2.5),  # 1.5s gap: a long pause
    ]
    result = metrics.compute_metrics(words, 3.0)
    assert result["pause_count"] == 1
    assert result["long_pause_count"] == 1
    assert result["total_pause_seconds"] == 1.5


def test_short_gap_is_not_a_pause():
    words = [
        _word("hello", 0.0, 0.5),
        _word("world", 0.6, 1.0),  # 0.1s gap: below the 0.35s threshold
    ]
    result = metrics.compute_metrics(words, 1.0)
    assert result["pause_count"] == 0


def test_filler_words_counted_and_excluded_from_vocabulary():
    words = [_word(w, i, i + 0.3) for i, w in enumerate(["um", "i", "uh", "think", "so"])]
    result = metrics.compute_metrics(words, 3.0)
    assert result["filler_count"] == 2
    # Fillers shouldn't count toward unique/content vocabulary.
    assert "um" not in [w["word"] for w in result["low_confidence_words"]]


def test_soft_filler_phrase_detected():
    words = [_word(w, i, i + 0.3) for i, w in enumerate(["you", "know", "it", "was", "good"])]
    result = metrics.compute_metrics(words, 2.5)
    assert result["filler_count"] == 1


def test_type_token_ratio_counts_unique_content_words():
    words = [_word(w, i, i + 0.3) for i, w in enumerate(["the", "cat", "sat", "on", "the", "mat"])]
    result = metrics.compute_metrics(words, 3.0)
    assert result["unique_word_count"] == 5  # "the" repeats
    assert result["type_token_ratio"] == round(5 / 6, 3)


def test_low_confidence_words_flagged_and_capped():
    distinct_words = [
        "apple", "banana", "cactus", "dragon", "eagle", "falcon", "garden", "harbor",
        "island", "jungle", "kitten", "lemon", "mirror", "napkin", "ocean",
    ]
    words = [_word(w, i, i + 0.4, prob=0.2) for i, w in enumerate(distinct_words)]
    result = metrics.compute_metrics(words, 10.0)
    assert len(result["low_confidence_words"]) == metrics.MAX_LOW_CONFIDENCE_WORDS


def test_low_confidence_dedups_repeated_words():
    words = [_word("word", i, i + 0.4, prob=0.2) for i in range(5)]
    result = metrics.compute_metrics(words, 5.0)
    assert len(result["low_confidence_words"]) == 1


def test_numeric_words_are_not_dropped():
    words = [_word("2024", 0, 0.5, prob=0.9), _word("was", 0.5, 0.8, prob=0.9)]
    result = metrics.compute_metrics(words, 1.0)
    assert result["word_count"] == 2


def test_high_confidence_words_not_flagged():
    words = [_word("clear", 0, 0.4, prob=0.98), _word("speech", 0.4, 0.9, prob=0.95)]
    result = metrics.compute_metrics(words, 1.0)
    assert result["low_confidence_words"] == []


def test_combine_metrics_weights_by_word_count():
    short = metrics.compute_metrics([_word("hi", 0, 0.5, 0.9)], 0.5)
    longer = metrics.compute_metrics(
        [_word(w, i * 0.4, i * 0.4 + 0.3, 0.9) for i, w in enumerate(["one", "two", "three", "four"])], 1.6
    )
    combined = metrics.combine_metrics([short, longer])
    assert combined["word_count"] == short["word_count"] + longer["word_count"]
    assert combined["duration_seconds"] == round(short["duration_seconds"] + longer["duration_seconds"], 2)


def test_combine_metrics_skips_empty_items():
    empty = metrics.compute_metrics([], 2.0)
    real = metrics.compute_metrics([_word("hi", 0, 0.4, 0.9)], 0.5)
    combined = metrics.combine_metrics([empty, real])
    assert combined["word_count"] == 1

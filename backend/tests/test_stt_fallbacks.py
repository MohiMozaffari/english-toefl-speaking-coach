"""Graceful-degradation logic for crashed/too-short/silent audio (no real audio needed)."""

import llm_service
import whisper_service
from whisper_service import classify_transcription


def _rich(text="", duration=10.0, failed=False):
    return {"text": text, "words": [], "duration": duration, "failed": failed}


def test_crashed_transcription_is_too_short():
    assert classify_transcription(_rich(failed=True)) == "too_short"


def test_brief_and_empty_is_too_short():
    assert classify_transcription(_rich(text="", duration=2.0)) == "too_short"


def test_brief_but_real_words_is_ok_not_too_short():
    # A quick correct answer to a short Listen-and-Repeat sentence must NOT be
    # penalized just for being brief.
    assert classify_transcription(_rich(text="The library opens at eight.", duration=2.5)) == "ok"


def test_adequate_duration_but_empty_is_no_speech():
    assert classify_transcription(_rich(text="", duration=45.0)) == "no_speech"


def test_normal_transcript_is_ok():
    assert classify_transcription(_rich(text="This is a normal answer.", duration=12.0)) == "ok"


def test_custom_min_duration_threshold():
    assert classify_transcription(_rich(text="", duration=5.0), min_duration=3.0) == "no_speech"
    assert classify_transcription(_rich(text="", duration=2.0), min_duration=3.0) == "too_short"


def test_min_usable_audio_seconds_matches_shortest_real_toefl_item():
    # Listen-and-Repeat's shortest legitimate item is 8s; the threshold must sit
    # below that so real short-but-complete answers are never misclassified.
    assert whisper_service.MIN_USABLE_AUDIO_SECONDS < 8.0


def test_general_fallback_feedback_shapes():
    silence = llm_service.general_fallback_feedback("no_speech")
    assert silence["status"] == "no_speech"
    assert silence["message"] == "No speech detected"

    short = llm_service.general_fallback_feedback("too_short")
    assert short["status"] == "too_short"
    assert short["message"] == "Response too short"
    # Must carry every key the frontend's GeneralFeedback renderer reads.
    for key in ("encouragement", "grammar_feedback", "vocabulary_feedback", "clarity_feedback",
                "improved_version", "overall_tip"):
        assert key in short


def test_toefl_fallback_feedback_score_is_within_the_real_1_to_6_scale():
    fb = llm_service.toefl_fallback_feedback("no_speech", "interview", ["Q1", "Q2"])
    assert fb["score_band"] == 1  # the real floor -- never an out-of-scale 0


def test_toefl_fallback_feedback_listen_repeat_shape():
    sentences = ["First.", "Second.", "Third."]
    fb = llm_service.toefl_fallback_feedback("too_short", "listen_repeat", sentences)
    assert fb["status"] == "too_short"
    assert len(fb["items"]) == 3
    assert all(set(item.keys()) == {"target", "said", "match_quality", "tip"} for item in fb["items"])
    assert "pronunciation_delivery" in fb
    assert "pronunciation" in fb["category_scores"]


def test_toefl_fallback_feedback_interview_shape():
    questions = ["Q1", "Q2", "Q3", "Q4"]
    fb = llm_service.toefl_fallback_feedback("no_speech", "interview", questions)
    assert len(fb["items"]) == 4
    assert all(set(item.keys()) == {"question", "said", "better_response", "why"} for item in fb["items"])
    assert "coherence" in fb
    assert "coherence" in fb["category_scores"]

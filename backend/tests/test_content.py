import content
import listening_content
import pronunciation_content
import shadowing_content


def test_general_topics_meet_minimum_variety():
    topics = content.get_general_topics()
    assert len(topics) >= 20
    ids = [t["id"] for t in topics]
    assert len(ids) == len(set(ids)), "topic ids must be unique"
    categories = {t["category"] for t in topics}
    assert len(categories) >= 4


def test_toefl_task_sets_have_correct_item_counts():
    tasks = content.get_toefl_tasks()
    for lr_set in tasks["listen_repeat"]:
        assert len(lr_set["sentences"]) == 7, lr_set["id"]
        assert lr_set["picture_caption"]
    for iv_set in tasks["interview"]:
        assert len(iv_set["questions"]) == 4, iv_set["id"]


def test_toefl_timing_matches_official_2026_format():
    timing = content.get_toefl_timing()
    assert timing["listen_repeat"]["item_seconds"] == [8, 8, 10, 10, 10, 12, 12]
    assert timing["interview"]["item_seconds"] == [45, 45, 45, 45]


def test_find_toefl_prompt_roundtrip():
    tasks = content.get_toefl_tasks()
    first = tasks["listen_repeat"][0]
    found = content.find_toefl_prompt("listen_repeat", first["id"])
    assert found is not None
    assert found["id"] == first["id"]


def test_find_toefl_prompt_missing_id_returns_none():
    assert content.find_toefl_prompt("listen_repeat", "does-not-exist") is None
    assert content.find_toefl_prompt("bogus_task_type", "anything") is None


def test_get_random_toefl_prompt_returns_a_valid_set():
    prompt = content.get_random_toefl_prompt("interview")
    assert prompt is not None
    assert prompt["task"] == "interview"
    assert len(prompt["questions"]) == 4


def test_get_random_toefl_prompt_unknown_task_type_returns_none():
    assert content.get_random_toefl_prompt("bogus_task_type") is None


def test_shadowing_passages_have_no_empty_sentences():
    for summary in shadowing_content.get_passages():
        passage = shadowing_content.get_passage(summary["id"])
        assert passage["sentences"], passage["id"]
        for sentence in passage["sentences"]:
            assert sentence.strip(), f"empty sentence in {passage['id']}"


def test_shadowing_passages_meet_minimum_variety():
    summaries = shadowing_content.get_passages()
    assert len(summaries) >= 8
    difficulties = {p["difficulty"] for p in summaries}
    assert difficulties <= {"beginner", "intermediate", "academic"}
    assert len(difficulties) >= 3, "should have all three difficulty tiers represented"


def test_shadowing_passage_has_accent_and_transcript():
    summary = shadowing_content.get_passages()[0]
    assert summary["preferred_accent"] in ("en-US", "en-GB", "en-AU")
    assert summary["full_transcript"].strip()


def test_shadowing_get_passages_omits_full_sentence_list():
    summaries = shadowing_content.get_passages()
    assert all("sentences" not in p for p in summaries)
    assert all("sentence_count" in p for p in summaries)


def test_shadowing_get_passage_lookup():
    all_passages = shadowing_content.get_passages()
    found = shadowing_content.get_passage(all_passages[0]["id"])
    assert found is not None
    assert "sentences" in found
    assert shadowing_content.get_passage("nonexistent") is None


def test_minimal_pairs_are_actually_pairs():
    for pair_set in pronunciation_content.MINIMAL_PAIRS:
        assert pair_set["pairs"], pair_set["id"]
        for pair in pair_set["pairs"]:
            assert len(pair) == 2
            assert pair[0].lower() != pair[1].lower()


def test_lessons_have_practice_lines():
    for lesson in pronunciation_content.LESSONS:
        assert lesson["practice_lines"], lesson["id"]
        for line in lesson["practice_lines"]:
            assert line["text"].strip()


def test_find_pair_set_and_lesson_lookup():
    pair_set = pronunciation_content.MINIMAL_PAIRS[0]
    assert pronunciation_content.find_pair_set(pair_set["id"])["id"] == pair_set["id"]
    assert pronunciation_content.find_pair_set("nonexistent") is None

    lesson = pronunciation_content.LESSONS[0]
    assert pronunciation_content.find_lesson(lesson["id"])["id"] == lesson["id"]
    assert pronunciation_content.find_lesson("nonexistent") is None


def test_listening_items_have_answer_keys_within_range():
    for item in listening_content.LISTENING_ITEMS:
        for q in item["questions"]:
            assert 0 <= q["answer"] < len(q["options"]), f"{item['id']}: {q['q']}"


def test_listening_get_item_hides_answers_by_default():
    item_id = listening_content.LISTENING_ITEMS[0]["id"]
    public = listening_content.get_item(item_id)
    assert all("answer" not in q for q in public["questions"])
    full = listening_content.get_item(item_id, include_answers=True)
    assert all("answer" in q for q in full["questions"])


def test_listening_grade_scores_correctly():
    item = listening_content.LISTENING_ITEMS[0]
    correct_answers = [q["answer"] for q in item["questions"]]
    result = listening_content.grade(item["id"], correct_answers)
    assert result["score"] == result["total"] == len(item["questions"])
    assert all(d["correct"] for d in result["detail"])


def test_listening_grade_partial_and_missing_answers():
    item = listening_content.LISTENING_ITEMS[0]
    wrong_answers = [-1] * len(item["questions"])
    result = listening_content.grade(item["id"], wrong_answers)
    assert result["score"] == 0

    result_short = listening_content.grade(item["id"], [])
    assert result_short["score"] == 0
    assert result_short["total"] == len(item["questions"])


def test_listening_grade_unknown_item_returns_none():
    assert listening_content.grade("nonexistent", []) is None

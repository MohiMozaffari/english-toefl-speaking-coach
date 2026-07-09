# Content Schemas

Exact shapes for every content type. Field names and types are **not
negotiable** — the loader (`seed_db.py`) and content access layer read these
keys directly, and `tests/test_content.py` asserts they are well-formed.

## Table of contents
- [Existing today](#existing-today) — TOEFL Speaking, Shadowing
- [New TOEFL sections](#new-toefl-sections) — Reading, Listening, Writing
- [Migrated support content](#migrated-support-content) — General, Pronunciation, Listening comp.
- [ID conventions](#id-conventions)

---

## Existing today

These already exist in `backend/seed_data.json` and are SQLite-backed. Match
them exactly.

### `toefl_prompts` → `listen_repeat`

```json
{
  "set_id": "lr_07",
  "set_title": "Campus Bookstore",
  "task_type": "listen_repeat",
  "picture_caption": "A student paying at a university bookstore counter",
  "items": [
    { "question_text": "The bookstore is open until six.", "response_time": 8 },
    { "question_text": "You can pay with cash or a card.", "response_time": 8 },
    { "question_text": "Used textbooks are cheaper than new ones.", "response_time": 10 },
    { "question_text": "Please keep your receipt in case you need a refund.", "response_time": 10 },
    { "question_text": "The store offers a discount to students during the first week.", "response_time": 10 },
    { "question_text": "If a book is sold out, staff can order it for you online.", "response_time": 12 },
    { "question_text": "Remember that returns are only accepted within fourteen days of purchase.", "response_time": 12 }
  ]
}
```

Rules: exactly **7 items**; `response_time` climbs **8 → 12** seconds as
sentences get longer/harder; `picture_caption` describes a single everyday
scene the sentences relate to. No prep time exists in this task.

### `toefl_prompts` → `interview`

```json
{
  "set_id": "int_05",
  "set_title": "Weekend Routines",
  "task_type": "interview",
  "picture_caption": null,
  "items": [
    { "question_text": "How do you usually spend your weekends?", "response_time": 45 },
    { "question_text": "Do you prefer spending weekends alone or with other people? Why?", "response_time": 45 },
    { "question_text": "Some people say weekends should be for rest, not work. What do you think?", "response_time": 45 },
    { "question_text": "If you had one extra free day every week, how would you use it?", "response_time": 45 }
  ]
}
```

Rules: exactly **4 items** on **one familiar topic**; `response_time` is always
**45**; mix personal questions with one abstract/speculative question, matching
the real Take-an-Interview task. `picture_caption` is `null`.

### `shadowing`

```json
{
  "id": "sh_12",
  "topic": "Booking a Doctor's Appointment",
  "difficulty": "intermediate",
  "preferred_accent": "en-US",
  "sentences": [
    "I called the clinic to book an appointment for next week.",
    "The receptionist asked what the visit was about.",
    "I explained that I'd had a headache for several days.",
    "She offered me a slot on Wednesday afternoon.",
    "I confirmed the time and gave my phone number.",
    "Before hanging up, she reminded me to bring my insurance card."
  ]
}
```

Rules: `difficulty` is one of `beginner` | `intermediate` | `academic`;
`preferred_accent` is `en-US` | `en-GB` | `en-AU`; 5–8 natural, connected
sentences that tell one small story.

---

## New TOEFL sections

These tables/readers **do not exist in the repo yet**. When you generate them,
tell the user the loader and a content reader must be added (code + content).
Shapes below are the target design; keep them consistent with the existing
grouped-set pattern (`set_id` / `set_title` / `items`).

### `toefl_reading`

Three task types. All are auto-scored (multiple choice or letter-fill), so each
item carries its own `answer` and short `explanation`.

```json
{
  "set_id": "rd_complete_01",
  "task_type": "complete_words",
  "set_title": "Rainforests",
  "passage": "Rainforests are dense regions filled with tall trees and countless living things. They play a vital r___ in regulating the planet's clim___ ...",
  "items": [
    { "blank_id": "b1", "answer": "role", "explanation": "'play a vital role' is a fixed collocation." },
    { "blank_id": "b2", "answer": "climate", "explanation": "Context (regulating the planet's) requires 'climate'." }
  ]
}
```

```json
{
  "set_id": "rd_daily_01",
  "task_type": "read_daily_life",
  "set_title": "Dorm Move-In Email",
  "stimulus_kind": "email",
  "passage": "Subject: Move-in details\n\nHi Jordan, ...",
  "items": [
    {
      "question_text": "Why did the housing office send this email?",
      "options": ["To cancel move-in", "To give move-in instructions", "To request payment", "To change roommates"],
      "answer_index": 1,
      "explanation": "The email lists dates and what to bring — it explains move-in."
    }
  ]
}
```

```json
{
  "set_id": "rd_academic_01",
  "task_type": "read_academic",
  "set_title": "The Impact of Sports on Social Integration",
  "passage": "Full multi-paragraph academic passage (300–450 words) ...",
  "items": [
    {
      "question_text": "According to paragraph 2, what is the main benefit described?",
      "question_kind": "factual",
      "options": ["...", "...", "...", "..."],
      "answer_index": 0,
      "explanation": "One-line reason grounded in the passage."
    }
  ]
}
```

`question_kind` (for `read_academic`) is one of: `factual`, `negative_factual`,
`vocabulary`, `select_sentence`, `sentence_simplification`, `reference`,
`inference`, `rhetorical_purpose`, `insert_text`. Aim for a spread across a set.

### `toefl_listening`

Each item needs an audio **script** (the app's TTS reads it aloud) plus the
comprehension items. Never require a pre-recorded audio file — the script feeds
`speechSynthesis` / edge-tts.

```json
{
  "set_id": "ls_conv_01",
  "task_type": "conversation",
  "set_title": "Asking About a Late Assignment",
  "script": "STUDENT: Hi professor, I wanted to ask about the essay deadline...\nPROFESSOR: Of course, come in...",
  "items": [
    {
      "question_text": "Why does the student go to see the professor?",
      "question_kind": "main_idea",
      "options": ["...", "...", "...", "..."],
      "answer_index": 0,
      "explanation": "One-line reason."
    }
  ]
}
```

`task_type` is one of `listen_choose_response` (single short prompt + best
reply), `conversation`, `announcement`, `academic_talk`. `question_kind` is one
of `main_idea`, `factual`, `inference`, `purpose`, `method`, `attitude`.

### `toefl_writing`

```json
{
  "set_id": "wr_build_01",
  "task_type": "build_sentence",
  "prompt": "Make an appropriate sentence using the words below in the correct order.",
  "words": ["the", "library", "closes", "at", "nine", "on", "weekdays"],
  "answer": "The library closes at nine on weekdays.",
  "explanation": "Subject + verb + time expression order."
}
```

```json
{
  "set_id": "wr_email_01",
  "task_type": "write_email",
  "situation": "You received an email from your professor about a schedule change...",
  "email_prompt": "Full prompt email text the learner must respond to ...",
  "min_words": 90,
  "rubric_ref": "write_email",       // points app at the scoring guide; LLM grades
  "model_answer": "Optional sample response for the tips panel."
}
```

```json
{
  "set_id": "wr_discussion_01",
  "task_type": "academic_discussion",
  "professor_prompt": "The professor's discussion question ...",
  "classmate_posts": [
    { "name": "Andrew", "text": "..." },
    { "name": "Kelly", "text": "..." }
  ],
  "min_words": 100,
  "rubric_ref": "academic_discussion",
  "model_answer": "Optional sample response."
}
```

Writing tasks are graded by the LLM against the scoring guide named in
`rubric_ref` (see `task-specs.md`), so they don't carry a single `answer`.

---

## Migrated support content

Currently these live in Python files (`content.py`,
`pronunciation_content.py`, `listening_content.py`). Target state moves them
into `seed_data.json` so adding content is a data edit, not a code edit.

### `general_topics`

```json
{ "id": "gen_25", "category": "opinions", "prompt": "Do you think social media brings people closer together or pushes them apart? Explain." }
```

`category` ∈ `daily_life` | `opinions` | `past_experiences` | `future_plans` | `people_places`.

### `pronunciation`

```json
{
  "minimal_pairs": [
    { "id": "mp_13", "contrast": "ɪ vs iː", "word_a": "ship", "word_b": "sheep", "tip": "iː is longer and tenser; smile slightly." }
  ],
  "technique_lines": [
    { "id": "tl_07", "technique": "linking", "line": "Turn it off and on again.", "tip": "Link the final consonant to the next vowel: 'tur-ni-toff'." }
  ]
}
```

### `listening_items` (support comprehension module)

```json
{
  "id": "lc_07",
  "title": "Campus Recycling Announcement",
  "difficulty": "intermediate",
  "kind": "announcement",
  "script": "Attention students: starting Monday, new recycling bins ...",
  "quiz": [
    { "question_text": "What changes on Monday?", "options": ["...","...","...","..."], "answer_index": 0 }
  ]
}
```

---

## ID conventions

- One short prefix per type, zero-padded 2-digit counter: `lr_`, `int_`, `sh_`,
  `rd_`, `ls_`, `wr_`, `gen_`, `mp_`, `tl_`, `lc_`.
- **Always read the target file first** and continue the numbering. Duplicate
  ids make `seed_db.py`'s `INSERT OR REPLACE` silently overwrite existing
  content — a real data-loss bug.
- Keep ids stable once shipped; the session history references prompts by id.

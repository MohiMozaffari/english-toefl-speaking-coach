---
name: toefl-app-content
description: >-
  Author new practice content for the English & TOEFL Speaking Coach app
  (github.com/MohiMozaffari/english-toefl-speaking-coach). Use this skill
  WHENEVER the user wants to add, generate, expand, or edit practice material
  for the app — TOEFL Speaking sets (Listen and Repeat, Take an Interview),
  TOEFL Reading / Listening / Writing items, shadowing passages, general
  English topics, pronunciation minimal-pairs, or listening-comprehension
  items — even if they just say "add more questions", "make more sets", "I need
  more content for section X", "seed more prompts", or "the app needs more
  variety". It guarantees the output matches the app's exact seed_data.json /
  content schema, the January-2026 TOEFL format, the 1–6 CEFR scoring bands,
  and the app's tip style, so it loads cleanly via seed_db.py and passes the
  content-integrity tests. Trigger it before writing any practice item by hand.
---

# TOEFL App Content Authoring

This skill produces **large batches of original, correctly-formatted practice
content** for the local-first *English & TOEFL Speaking Coach* app. The single
biggest job on this project is "add much more content for every section," and
content only helps if it drops into the app's data files with the exact shape
the loader and tests expect. Get the schema wrong and `seed_db.py` fails or the
content-integrity tests break; get the task format wrong and the practice
doesn't match the real 2026 exam.

## Golden rules

1. **Original content only.** Generate fresh sentences, passages, questions, and
   topics. If the official ETS guide PDF is available in the repo or uploads,
   use it **as a reference for format, difficulty, and task rules only** — never
   copy its passages, questions, or answer text. This keeps the app free of
   copyright problems, which matters because the whole project must stay free
   and shareable.
2. **Match the schema exactly.** Every content type has a required shape. Read
   `references/schema.md` and copy the field names, types, and id conventions
   verbatim. Never invent new top-level keys without the user asking.
3. **Match the 2026 TOEFL format.** The test was redesigned on 21 January 2026:
   two Speaking tasks, 1–6 band scoring aligned to CEFR, no prep time on
   Speaking. Task rules, item counts, and timings live in
   `references/task-specs.md` — follow them.
4. **Write in the app's tip voice.** Tips are short, concrete, and actionable
   (never "practice more"). Coaching advice is grounded in the CEFR band
   descriptors. See `references/tips-style.md`.
5. **Stay loadable.** After generating, the content must survive
   `python seed_db.py` and `pytest tests/test_content.py`. Validate before
   handing it over (see "Validate" below).

## Workflow

### 1. Figure out what to generate

Ask (or infer from the request): which content type, how many items/sets, what
difficulty spread, and any topic constraints. A good default when the user says
"lots more" is a **balanced batch**: for TOEFL Speaking, e.g. 6 new Listen-and-
Repeat sets (2 easy / 2 medium / 2 hard) + 6 Take-an-Interview sets across
different familiar topics. Confirm the count if it's ambiguous — generating 50
items in the wrong shape wastes everyone's time.

### 2. Load the schema and specs

Read `references/schema.md` for the target file/table and its exact fields.
Read `references/task-specs.md` for the task's rules (counts, timings, scoring).
If writing tips or per-band coaching, read `references/tips-style.md`.

### 3. Generate

Produce the items as JSON that slots directly into `backend/seed_data.json`
(TOEFL Speaking + shadowing today) or the relevant content file. Key points:

- Give every set/passage a **unique, sequential id** following the existing
  convention (`lr_07`, `int_05`, `sh_12`, …). Never reuse an id already in the
  file — check the file first.
- Respect **increasing difficulty within a set** where the task calls for it
  (Listen and Repeat sentences get longer/harder across the 7 items).
- Keep vocabulary and topics **familiar and everyday** for Speaking/Interview
  (campus life, daily routines, opinions, plans) — the exam tests English, not
  domain knowledge.
- For anything with a correct answer (Reading/Listening/Writing items), include
  the answer key AND a one-line explanation, because the app shows explanations.

### 4. Validate before delivering

Never hand over content you haven't checked. Run a quick validation:

```bash
# From backend/, after adding your items to seed_data.json:
python -c "import json; json.load(open('seed_data.json'))"   # valid JSON?
python seed_db.py                                            # loads clean?
pytest tests/test_content.py -q                             # integrity passes?
```

If the app isn't runnable in your environment, at minimum parse the JSON and
check every required field is present and every id is unique. State clearly
which checks you ran.

### 5. Deliver

Hand back either the edited `seed_data.json` (or content file) or a clean JSON
snippet the user can paste, plus a one-line note on how to load it
(`python seed_db.py`). Tell them the id range you used so the next batch
continues the sequence.

## Content types at a glance

| Type | Where it lives | Task types |
| --- | --- | --- |
| TOEFL Speaking | `seed_data.json → toefl_prompts` | `listen_repeat`, `interview` |
| Shadowing | `seed_data.json → shadowing` | passages by difficulty |
| TOEFL Reading | `seed_data.json → toefl_reading` *(new)* | `complete_words`, `read_daily_life`, `read_academic` |
| TOEFL Listening | `seed_data.json → toefl_listening` *(new)* | `listen_choose_response`, `conversation`, `announcement`, `academic_talk` |
| TOEFL Writing | `seed_data.json → toefl_writing` *(new)* | `build_sentence`, `write_email`, `academic_discussion` |
| General English | `seed_data.json → general_topics` *(migrate)* | free-response topics |
| Pronunciation | `seed_data.json → pronunciation` *(migrate)* | `minimal_pairs`, `technique_lines` |
| Listening comp. | `seed_data.json → listening_items` *(migrate)* | audio + comprehension quiz |

Types marked *(new)* / *(migrate)* may not exist in the repo yet — when adding
them, follow the schema in `references/schema.md` and tell the user the loader
(`seed_db.py`) and content access layer need the matching table/reader, so this
is a code change plus content, not content alone.

## Reference files

- `references/schema.md` — exact JSON shapes, field types, and id conventions
  for every content type. **Read this before generating anything.**
- `references/task-specs.md` — the 2026 TOEFL task rules: counts, timings,
  1–6 CEFR scoring bands, and the practice-vs-exam-mode timing behaviour.
- `references/tips-style.md` — how to write in-app tips and per-band coaching
  advice grounded in the CEFR performance descriptors.

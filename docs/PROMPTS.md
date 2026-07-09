# Claude Code Prompts

Copy-paste prompts for building v2, one at a time. Let Claude Code finish and
run its tests before the next one. Commit after each green step.

The first prompt below assumes `CLAUDE.md` is in the repo root and the
`toefl-app-content` skill is in `.claude/skills/`. Both load automatically.

---

## Kickoff

```
Read CLAUDE.md and confirm you understand the guardrails (free/no-card,
local-first, single user, scores clamped 1–6, content in seed_data.json). Then
list the .claude/skills you can see. Don't change anything yet — just confirm.
```

## 1 · One user

```
Read CLAUDE.md. Make this single-user using the low-risk approach it describes:
keep the DB schema but auto-create and always use one implicit profile
(profile_id = 1) server-side; remove the /api/profiles routes; delete the
profile switcher/creator UI and the profile context in the frontend (keep the
theme context). Preserve all history. Run pytest tests/ and npm run typecheck
and fix what breaks. Summarize your changes.
```

## 2 · Practice vs Exam mode (Speaking)

```
Read CLAUDE.md and the toefl-app-content skill's references/task-specs.md
("Practice mode vs Exam mode"). Add a mode flag to the TOEFL Speaking flow —
same content pool and grading pipeline, the flag only toggles (a) countdown
enforcement, (b) tips visibility, (c) immediate vs deferred feedback.
Practice: timer shown but never cuts you off, question-by-question, re-dos
allowed, feedback per item. Exam: timer enforced, continuous, no re-dos,
feedback withheld until an end-of-test score report saved as one History entry.
Reuse useCountdown (add an "enforced" option) and the existing rubric JSON.
Don't duplicate grading. Run typecheck.
```

## 3 · Redesign + mobile

```
Read CLAUDE.md. Redesign pass, no functionality change: consistent design
tokens in one place, calm modern look, keep light/dark. Start with the Layout
shell, Dashboard, and TOEFL screens. Then make the app fully usable on a ~380px
phone: collapsing nav, large tap targets, every practice flow one-handed. Keep
desktop unchanged and don't touch API/data shapes. Run npm run typecheck.
```

## 4 · More content (repeatable)

```
Use the toefl-app-content skill. Read backend/seed_data.json first to continue
the id numbering. Generate 8 new Listen and Repeat sets (2 easy / 3 medium /
3 hard) and 8 new Take an Interview sets across different familiar topics.
Follow the schema and 2026 task rules exactly. Original content only. Add to
seed_data.json, run python seed_db.py, and run pytest tests/test_content.py.
Tell me the id ranges used.
```

Re-run with different counts/types (shadowing, general topics, later
reading/listening/writing) whenever you want more — the skill keeps the format
correct each time.

## 5 · More tips + coaching

```
Read the toefl-app-content skill's references/tips-style.md. Add a tips layer to
Practice mode only: 1–2 concrete task-specific tips before each item, one
focused improvement tip after, in the app's tip voice. Store tips as data, not
hardcoded. Then make coach.py's per-band advice match the CEFR descriptors in
tips-style.md, keeping it rule-based and evidence-backed (no LLM call). Run
pytest tests/ and npm run typecheck.
```

## 6 · Other sections (later, one at a time)

```
Read the toefl-app-content skill (schema.md "New TOEFL sections" + task-specs).
Add a TOEFL Reading practice module (complete_words, read_daily_life,
read_academic): add toefl_reading to seed_data.json with 3 original sets per
task type plus answer keys and one-line explanations; extend seed_db.py and
database.py; add a content reader, API routes, a Reading page with Practice/Exam
modes and instant scoring, types, and nav; extend tests/test_content.py. Run all
tests and typecheck. Keep it free and local.
```

Repeat the same pattern for Listening (`toefl_listening`) and Writing
(`toefl_writing`), then assemble a full chained Exam (Reading → Listening →
Writing → Speaking) with one combined score report.

---

**Tip:** if a prompt is too big, tell Claude Code "do part A only first."
Smaller diffs are easier to review and safer to roll back.

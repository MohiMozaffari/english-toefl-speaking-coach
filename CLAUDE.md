# CLAUDE.md

Project context for Claude Code. Read this before making changes.

## What this is

A **local-first English & TOEFL Speaking Coach** — a personal, free tool that
runs entirely on one machine. Speech-to-text (faster-whisper), delivery metrics,
scoring, gamification, and the dashboard are fully local; AI feedback text comes
from a local FreeLLMAPI instance. Shadowing's neural voices are the only cloud
call, and they fall back to the browser voice if offline.

**Non-negotiable constraints — apply to every change:**
- **Free and no card, ever.** Never add a paid API, a login wall, a
  subscription, telemetry, ads, or anything that needs a credit card. If a
  feature seems to need a paid service, find a local/free path or stop and ask.
- **Local-first.** Default to `localhost`. Any new outbound call must be
  optional, clearly noted, and degrade gracefully offline (see Shadowing's
  edge-tts fallback for the pattern).
- **Single user.** This is one person's machine (see "Single-user" below).

## Stack & layout

```
backend/    Python 3.10+ / FastAPI          (port 8001)
  main.py            all HTTP routes
  whisper_service.py faster-whisper STT (word timestamps, confidence, graceful failure)
  metrics.py         local delivery metrics (WPM, pauses, fillers, vocab)
  alignment.py       word-diff + fluency scoring (shadowing/pronunciation)
  llm_service.py     FreeLLMAPI client, prompts, strict-JSON parsing, fallbacks
  tts_service.py     edge-tts neural voices (accent rotation, disk cache)
  coach.py           learner memory + deterministic, evidence-based recommendations
  gamification.py    XP, levels, streaks, daily goals, achievements
  stats.py           dashboard aggregation (skill radar, trends, weaknesses)
  db.py              SQLite data/app.db: sessions + activity + results
  database.py        SQLite data/toefl_coach.db: content library
  seed_data.json     SOURCE OF TRUTH for content
  seed_db.py         loads seed_data.json into toefl_coach.db (INSERT OR REPLACE)
  content.py / shadowing_content.py / pronunciation_content.py / listening_content.py
  tests/             pytest, pure-logic modules

frontend/   React 18 + TypeScript + Vite    (port 5173)
  src/api.ts         typed fetch client       src/types.ts   shared API types
  src/contexts.tsx   theme + (currently) profile context
  src/components/     Layout (responsive shell), ui.tsx
  src/hooks/          useRecorder, useCountdown, useNeuralPlayer
  src/pages/          Dashboard, ToeflPractice, GeneralPractice, Shadowing,
                      PronunciationLab, Listening, History, SessionDetail, Settings
```

FreeLLMAPI runs separately (`docker compose up -d` in the user's freellmapi
folder) at `http://localhost:3001`. Everything except AI-feedback text works
without it.

## Run / test

```bash
# backend
cd backend && python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\Activate.ps1)
pip install -r requirements.txt
python seed_db.py                 # REQUIRED on fresh clone — DB is gitignored, derived from seed_data.json
uvicorn main:app --reload --port 8001

# frontend (second terminal)
cd frontend && npm install && npm run dev

# tests
cd backend && pip install -r requirements-dev.txt && pytest tests/ -v
cd frontend && npm run typecheck
```

After editing `seed_data.json`, always re-run `python seed_db.py`. It's
`INSERT OR REPLACE`, safe to re-run.

## Conventions & guardrails

- **Scores are always clamped 1–6** (CEFR-aligned), everywhere — DB column,
  charts, badges, LLM prompts. Silent/too-short attempts = band 1 with a
  `status` field (`too_short` / `no_speech`), never 0, never an error page.
- **STT failures never hard-error.** A 0-byte or sub-second recording returns a
  normal graded result and is saved to History. Preserve this.
- **LLM feedback is strict JSON.** `llm_service.py` parses a fixed schema and
  has fallbacks for no-speech / too-short / unreachable. Keep responses parseable
  and keep the fallbacks.
- **Coach recommendations are rule-based, not another LLM call** — deterministic,
  instant, free, explainable from measured evidence. Don't replace with an LLM.
- **Whisper confidence is a pronunciation *proxy*** — always labelled as such,
  never presented as ground truth.
- **Content lives in `seed_data.json`.** Add content there and re-seed; don't
  hardcode practice items in components. When you add content, use the
  `toefl-app-content` skill so the schema and 2026 task format stay correct.
- **en-US voice only** for `speechSynthesis` (never UK/AU/IN); Shadowing may
  offer US/UK/AU explicitly via edge-tts.

## Active direction (what we're building)

1. **Single-user.** Remove the multi-profile model. Recommended approach: keep
   the DB schema but auto-create and always use one implicit profile server-side
   (`profile_id = 1`); delete the profile switcher/creator UI and the profile
   context; drop `profile` from the API surface. This preserves all history and
   avoids a risky schema migration. (A later cleanup can drop the columns.)
2. **Two TOEFL modes — Practice and Exam.** Same content pool, same
   recording/grading pipeline; the mode is a flag toggling three things:
   (a) whether the countdown *enforces* cutoff, (b) whether tips render,
   (c) whether feedback shows immediately or is deferred to an end-of-test
   report. **Practice**: timer shown but not enforced, question-by-question,
   tips on, immediate feedback, free re-dos. **Exam**: timer enforced,
   continuous, no tips, one score report at the end (testinno-style). Do NOT
   fork content or scoring per mode.
3. **Redesign + mobile.** More polished UI and a proper mobile layout. Keep the
   responsive Layout shell; make every practice flow usable one-handed on a
   phone (recording, playback, navigation). Design tokens/theming stay in one
   place; light/dark preserved.
4. **Much more content, every section.** Expand Speaking first, then add
   Reading / Listening / Writing as practice modules (see the skill's
   `references/task-specs.md`). Ground new content in the official ETS guide PDF
   if present, but generate **original** items only — never copy passages.
5. **More/better tips** throughout practice mode, in the app's concrete,
   actionable tip voice (see the skill's `references/tips-style.md`).

## When adding a new content type or section

Content is a data edit; a new *type* is data + code. To add e.g. TOEFL Reading:
1. Add the `toefl_reading` block to `seed_data.json` (schema in the skill).
2. Extend `seed_db.py` + `database.py` with the matching table/loader.
3. Add a content reader (like `content.py`) and API routes in `main.py`.
4. Add a page under `src/pages/` + route + nav entry + types in `types.ts`.
5. Add content-integrity coverage in `tests/test_content.py`.
Keep the grouped-set pattern (`set_id` / `set_title` / `items`) consistent.

## Style

Match the existing code. Small, reviewable changes. Run `pytest` and
`npm run typecheck` before declaring done. Prefer editing `seed_data.json` +
re-seeding over hardcoding content.

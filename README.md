# English & TOEFL Speaking Coach

A local-first speaking-practice platform: TOEFL iBT Speaking simulation, free-form English conversation, shadowing,
a pronunciation lab, listening comprehension, and an analytics dashboard with a coach that remembers your history.
Speech-to-text runs entirely on your CPU (faster-whisper); AI feedback comes from your local FreeLLMAPI instance;
everything else — alignment scoring, delivery metrics, XP, streaks, achievements — runs locally with no network
calls at all.

## Contents

- [Architecture](#architecture)
- [Setup](#setup)
- [Where to paste your FreeLLMAPI key](#where-to-paste-your-freellmapi-key)
- [What's running where](#whats-running-where)
- [Features](#features)
- [Error handling you'll see in the app](#error-handling-youll-see-in-the-app)
- [Running the tests](#running-the-tests)
- [Design notes](#design-notes)

## Architecture

```
backend/                Python / FastAPI
  main.py                 all HTTP routes
  whisper_service.py       faster-whisper wrapper (word-level timestamps + confidence)
  metrics.py               local delivery metrics from those timestamps (WPM, pauses, fillers, vocabulary...)
  alignment.py              word-diff + fluency scoring for shadowing/pronunciation drills
  llm_service.py            FreeLLMAPI client, prompts, JSON parsing, error mapping
  coach.py                  learner memory (built from real history) + rule-based recommendations
  gamification.py           XP, levels, streaks, daily goals, achievements
  stats.py                  dashboard aggregation (skill radar, trends, weaknesses)
  db.py                     SQLite: profiles, sessions, shadowing/pair/listening results, activity log
  content.py, shadowing_content.py, pronunciation_content.py, listening_content.py
                             all practice content (topics, TOEFL sets, passages, IPA/minimal pairs, listening items)
  tests/                    pytest suite for every pure-logic module above

frontend/               React 18 + TypeScript + Vite
  src/api.ts               typed fetch client
  src/types.ts              shared API types
  src/contexts.tsx          theme (light/dark) + active-profile context
  src/components/           Layout (responsive sidebar shell), ui.tsx (shared components)
  src/pages/                Dashboard, ToeflPractice, GeneralPractice, Shadowing, PronunciationLab,
                             Listening, History, SessionDetail, Settings
```

Nothing here talks to the public internet except `npm install` / `pip install` during setup, and the one-time
faster-whisper model download. Once running, every request stays on `localhost`.

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- FreeLLMAPI already running locally at `http://localhost:3001` (via `docker compose up -d` in your freellmapi
  folder) with a unified key created on its Keys page. Everything except AI feedback text works without it —
  transcription, metrics, shadowing/pronunciation scoring, and the dashboard are all local.

### Backend

```bash
cd backend
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

This installs `faster-whisper` for you. If you ever need it manually: `pip install faster-whisper`.

```bash
uvicorn main:app --reload --port 8000
```

The first time you submit a recording, faster-whisper downloads the selected model (tiny/base/small) to a local
cache — one-time internet use, fully offline afterward.

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (default `http://localhost:5173`). `npm run typecheck` runs the TypeScript compiler
in `--noEmit` mode if you want to check types without starting the dev server.

## Where to paste your FreeLLMAPI key

Open the app → **Settings** (`http://localhost:5173/settings`) → paste your key (`freellmapi-xxxxxxxx`) into the
**"FreeLLMAPI unified key"** field → **Save settings**. It's written to `backend/data/config.json` on your machine
only, and is never printed to any log. Same page: base URL, model override, faster-whisper size, and your daily
XP goal.

## What's running where

| Component   | URL                        | Notes                                               |
|-------------|-----------------------------|------------------------------------------------------|
| Frontend    | http://localhost:5173       | React + Vite dev server                             |
| Backend     | http://localhost:8000       | FastAPI — whisper, metrics, alignment, coach, stats  |
| FreeLLMAPI  | http://localhost:3001       | Started separately by you (`docker compose up -d`)  |
| SQLite DB   | `backend/data/app.db`       | Profiles + every attempt, created automatically      |
| Settings    | `backend/data/config.json`  | Key/URL/model choices, local file only               |

## Features

### Dashboard
Streak flame, XP + level with a progress bar, a daily-goal ring, a weekly activity chart, TOEFL score trend, a
skill radar (Fluency / Pronunciation / Vocabulary / Accuracy / Coherence — each axis documents its own formula in
`stats.py`), speaking-speed trend, a coach "what's holding you back" panel with evidence, ranked recommendations
linking straight to the relevant practice module, and a 12-achievement grid.

### Profiles
Local, no-auth profiles (switch or create one from the sidebar). Each profile has its own history, XP, streaks,
daily goal, and coach memory — useful for separating "before VPN" test data from real practice, or multiple family
members sharing one machine.

### TOEFL Speaking
Matches the redesigned TOEFL iBT Speaking section (launched January 21, 2026): two tasks, no prep time, scored
1–6.
- **Listen and Repeat** — 7 sentences per set (tied to a picture), heard once, repeated back immediately;
  8–12 seconds per sentence, increasing difficulty.
- **Take an Interview** — 4 questions per set on one familiar topic, answered immediately; 45 seconds each.

Every attempt gets a strict-JSON rubric response: score band + reason, what went well, the single biggest
weakness (and *why* it costs points), category sub-scores, a sentence/question-by-question breakdown, concrete
"how to improve" steps with suggested exercises, and a focus point (auto-read aloud). Re-attempt any set and the
result view shows every previous score for that exact prompt so you can see real progress.

### General English Practice
24 everyday topics across daily life, opinions, past experiences, future plans, and people/places. Record any
length; get plain-language grammar/vocabulary/clarity feedback plus a rewritten "improved version" read aloud.

### Shadowing
Sentence-by-sentence playback from 8 passages (beginner → advanced, including a TOEFL-style campus announcement),
adjustable speed (0.5×–1.25×), a loop button for difficult sentences, and word-by-word diff highlighting
(matched / close / missing) after you record your repeat. Fluency scoring is a transparent local formula over pace,
pauses, and filler words — see `alignment.fluency_score()`. Per-passage progress is tracked and shown as you browse.

### Pronunciation Lab
American-English IPA chart (16 vowels/diphthongs, 12 consonants) — click any symbol to hear example words plus a
tip. 12 minimal-pair contrasts (ship/sheep, think/sink, light/right, etc.) — you're asked to say one specific word,
faster-whisper transcribes it, and whichever word it actually heard is the honest local verdict. Every attempt is
tracked per contrast, building a real "weak sounds" profile with no cloud service involved. Plus 6 technique
lessons (word stress, sentence stress/rhythm, intonation, linking, reductions, the American flap T) with scored
practice lines.

### Listening Practice
6 items — conversations, a campus announcement, a TED-style talk, an academic lecture, a podcast dialogue — across
three difficulty levels. Adjustable playback speed, an interactive transcript (click any line to replay just that
segment), and a scored comprehension quiz.

### Voice
Feedback, model answers, and lesson lines are read aloud via the browser's `speechSynthesis`, explicitly picking
an `en-US` voice (never UK/AU/IN) from `speechSynthesis.getVoices()`. A replay button sits next to every piece of
spoken feedback, including in History.

### History
Every session across every mode, reopenable with full feedback restored. TOEFL sessions show every other attempt
of the same prompt set for direct comparison.

## Error handling you'll see in the app

- **FreeLLMAPI unreachable** — "Could not reach FreeLLMAPI... run 'docker compose up -d' in your freellmapi
  folder." (Dashboard, Settings, and after a failed AI-feedback attempt. Health checks time out in ~4s so the UI
  never hangs waiting on this.)
- **Missing/invalid key** — "Your FreeLLMAPI unified key is missing or invalid... get one from the Keys page at
  http://localhost:3001."
- **Mic permission denied** — "Microphone permission was denied. Please allow microphone access for this site in
  your browser settings and try again."
- **faster-whisper not installed** — "faster-whisper is not installed. Run: pip install faster-whisper."

## Running the tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest tests/ -v
```

66 tests cover the pure-logic modules: metrics (WPM/pause/filler/vocabulary/confidence math), alignment (word diff,
contraction equivalence, fluency scoring), gamification (XP, levels, streak edge cases, achievement conditions),
content integrity (every practice bank is well-formed), and DB round-trips (isolated temp SQLite file per test —
never touches your real `app.db`).

```bash
cd frontend
npm run typecheck
```

## Design notes

- **Why rule-based recommendations, not another LLM call**: the coach's exercise recommendations
  (`coach.py:recommendations()`) are deterministic rules over measured evidence (pace, pauses, fillers,
  vocabulary ratio, minimal-pair accuracy). They're instant, free, reproducible, and you can read exactly why
  each one fired — no prompt-engineering a second model to explain itself.
- **Why whisper confidence as a pronunciation proxy**: without a phoneme-level forced-alignment pipeline, a
  speech recognizer's own per-word confidence is a surprisingly honest signal — it drops sharply on words it
  struggled to parse, which correlates with unclear pronunciation. It's flagged as a proxy everywhere it's used,
  not presented as ground truth.
- **Why the minimal-pair drill has no cloud "verdict"**: the test-taker is asked to say one specific word;
  whichever word faster-whisper actually transcribes is the result. If it doesn't match either word in the pair,
  the attempt is marked "unclear" and excluded from accuracy stats rather than guessed at.
- **Why profiles have no authentication**: this is a single-machine local tool. Profiles exist to separate
  histories (e.g. multiple learners), not to gate access.

# 2026 TOEFL Task Specs & Scoring

Grounded in the official ETS guide (Pocket Edition) and the redesigned TOEFL iBT
that launched **21 January 2026**. Use these rules so generated content matches
the real exam and so the app's two modes behave correctly.

## The 2026 exam in one screen

- Four sections, always in this order: **Reading → Listening → Writing →
  Speaking**. Whole test ≈ 1 hr 23 min.
- **1–6 band scoring** per section, aligned to CEFR. There is **no 0 band** —
  the app clamps every score to 1–6 (a silent/too-short attempt = band 1 with a
  `status` flag, never 0).
- Reading and Listening are **multistage adaptive** (module 2 difficulty depends
  on module 1). The app can imitate this later; content just needs an easy /
  medium / hard label so an adaptive selector has something to work with.

## Speaking (the app's core today)

No prep time on either task.

### Listen and Repeat
- Hear a sentence **once**, repeat it back immediately.
- **7 sentences** per set, tied to a picture, increasing difficulty.
- ~**8–12 seconds** to respond per sentence (shorter for short sentences).
- Scoring guide rewards: accurate reproduction, clear pronunciation, natural
  rhythm/intonation. Missing or garbled words cost points.

### Take an Interview
- A simulated interview: **4 questions** on **one familiar topic**, answered
  immediately, **45 seconds** each.
- Questions mix personal ("How do you…?") with abstract/speculative ("Some
  people think… what's your view?").
- Scoring guide rewards: relevant, developed answers; clear delivery; range and
  control of grammar/vocabulary; coherence. Off-topic or one-word answers cost
  points.

## Reading tasks
- **Complete the Words** — 70–100 word academic text with missing letters;
  fill them in. 2–3 per test.
- **Read in Daily Life** — an everyday text (email, ad, syllabus, post,
  instructions, review) + comprehension questions.
- **Read an Academic Passage** — a university-level passage + the classic TOEFL
  question types (factual, negative factual, vocabulary, select sentence,
  sentence simplification, reference, inference, rhetorical purpose, insert
  text).

## Listening tasks
- **Listen and Choose a Response** — short prompt, pick the best reply.
- **Listen to a Conversation / Announcement / Academic Talk** — longer audio +
  questions (main idea, factual, inference, purpose, method, attitude).
- Audio plays **once**; no replay of the whole clip (the app may allow
  segment-replay of the transcript in *practice* mode only).

## Writing tasks (each timed separately)
- **Build a Sentence** (~6 min total for the task) — order/complete words into a
  correct sentence. Auto-checkable.
- **Write an Email** (~7 min) — read a situation + prompt email, write a reply.
  LLM-graded against the Email scoring guide.
- **Write for an Academic Discussion** (~10 min) — professor question + two
  classmate posts, write your contribution. LLM-graded against the Academic
  Discussion scoring guide.

## Scoring guides for LLM grading (`rubric_ref`)

When the app asks the LLM to grade Writing (or Speaking), prompt it to return
**strict JSON** matching the app's existing rubric shape (band 1–6 + reason,
what went well, biggest weakness and why it costs points, category sub-scores,
per-item breakdown, concrete "how to improve" steps, one focus point). Ground
the band in these summaries:

- **Email:** full, on-topic response; appropriate tone/register; clear
  organisation; controlled grammar and vocabulary. Higher bands develop ideas
  and adapt tone precisely; lower bands are incomplete, off-register, or hard to
  follow.
- **Academic Discussion:** a relevant, well-developed contribution that engages
  with the professor and classmates; clear reasoning and examples; range and
  accuracy of language. Lower bands are short, vague, or only loosely connected
  to the prompt.
- **Speaking (both tasks):** intelligibility, accuracy, fluency, and (for
  Interview) relevance + development. Always flag whisper confidence as a
  *proxy* for pronunciation, never ground truth.

## Practice mode vs Exam mode (timing behaviour)

This is the behaviour the app's two TOEFL modes must implement. Content is the
same; only the timing/UX differs.

| | **Practice mode** | **Exam mode** |
| --- | --- | --- |
| Timer | **Shown but not enforced** — counts up/down for realism, but never cuts you off or auto-submits | **Enforced** — when time is up, recording stops / the task auto-advances, like the real test |
| Pace | **Question-by-question**, user advances manually; can pause, replay instructions, re-do an item | Continuous; no pausing, no re-dos, fixed order |
| Tips | Tips + strategy hints shown before/after each item | No tips during the test |
| Feedback | **Immediate** per-item feedback and score | Feedback withheld until the **end**, then a full section/score report (testinno-style) |
| Content pool | Pick any set, redo freely | A fresh assembled test (or full section), scored once |

Design note for whoever builds this: keep a single content pool and a single
recording/grading pipeline; the mode is just a flag that toggles (a) whether the
countdown enforces cutoff, (b) whether tips render, and (c) whether feedback
shows immediately or is deferred to an end-of-test report. Don't fork the
content or the scoring code per mode.

# Tip Voice & Per-Band Coaching

The app leans on tips heavily (the user asked for "more tips"). Two kinds of
guidance appear: **task tips** (shown in practice mode) and **coaching advice**
(the dashboard coach + end-of-attempt feedback). Both must be short, concrete,
and genuinely actionable.

## Task-tip voice

Rules:
- One idea per tip, ≤ 20 words, imperative.
- Concrete and checkable — the learner can *do* it right now.
- No filler ("just practice", "try your best", "believe in yourself").
- Tie the tip to the specific task, not generic advice.

**Good:**
- Listen and Repeat → "Hold the whole sentence in your head before you start —
  don't begin speaking until it finishes."
- Take an Interview → "Answer the actual question in your first sentence, then
  add one reason and one example."
- Build a Sentence → "Find the verb first, then decide what goes before and
  after it."
- Write an Email → "Open by stating why you're writing; match the tone of the
  email you received."

**Bad (don't do this):**
- "Practice speaking every day." (not task-specific, not checkable)
- "Pronunciation is very important." (states the obvious, no action)

## Per-band coaching advice (CEFR-aligned)

The official guide gives "Advice for Improvement" for each 1–6 band per section.
When the coach or feedback names a band, its advice should match that band's
real needs. Use these summaries (paraphrase into fresh wording — don't copy the
book):

| Band | CEFR | What the learner needs to hear |
| --- | --- | --- |
| 6 | C2 | Fine-tune precision and nuance; vary sentence structure and idiom; polish naturalness. |
| 5–5.5 | C1 | Tighten accuracy under pressure; develop ideas more fully; reduce small slips. |
| 4–4.5 | B2 | Build fluency and range; connect ideas with clearer linking; expand vocabulary beyond the everyday. |
| 3–3.5 | B1 | Focus on clear, complete sentences; answer the question directly; work on common grammar patterns. |
| 2–2.5 | A2 | Practise core sentence patterns and high-frequency vocabulary; slow down for clarity. |
| 1–1.5 | A1 | Build basic sentences and pronunciation of common words; short, correct answers first. |

Coaching should always name **one** highest-leverage focus, back it with
evidence the app measured (pace, pauses, fillers, minimal-pair accuracy, missed
words), and point to a specific practice module. That mirrors the existing
`coach.py` philosophy: deterministic, evidence-backed, one clear next step —
not a wall of generic encouragement.

## Focus-point line (read aloud)

Each attempt ends with a single "focus point" that the app reads aloud. Keep it
to one sentence, second person, and specific: e.g. "Next time, finish each
sentence with falling intonation so it sounds like a statement, not a question."

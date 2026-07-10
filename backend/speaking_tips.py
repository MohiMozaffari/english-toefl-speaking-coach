"""Practice-mode tips for TOEFL Speaking, shown before/after each item.

Tips are keyed by item index rather than by set, because every Listen and
Repeat set follows the same short -> medium -> long progression and every
Interview set follows the same personal -> abstract/speculative progression
(see the toefl-app-content skill's references/task-specs.md). That makes a
small, position-based bank cover every set in seed_data.json instead of
needing one tip per item per set.

Written in the app's tip voice (references/tips-style.md): one idea, <=20
words, imperative, checkable right now -- never generic encouragement.
"""

LISTEN_REPEAT_BEFORE: list[list[str]] = [
    ["Wait for the whole sentence to finish before you start speaking."],
    ["Match the speaker's stress and rhythm, not just the words."],
    [
        "Hold the full sentence in your head before you begin — don't start on the first word you catch.",
        "If you blank on one word, keep going — a full sentence with one gap scores higher than stopping early.",
    ],
    ["Pause where the sentence naturally pauses instead of running every word together."],
    ["Keep linking words like 'and' or 'before' — they show you caught the sentence's structure."],
    [
        "Split a long sentence into two chunks as you listen: the main clause, then the modifier.",
        "Don't rush the ending because the sentence was long — finish with the same clear pace you started with.",
    ],
    ["This is the hardest sentence in the set — prioritize the core meaning over every exact word."],
]

LISTEN_REPEAT_AFTER: list[str] = [
    "Notice if you started the instant the beep sounded, or hesitated first.",
    "Did your repetition sound flat, or did it match the speaker's rhythm?",
    "If a word slipped, it was probably a short function word like 'the' or 'to' — listen for those next time.",
    "Check whether you paused where the clauses actually break, not just where you ran out of breath.",
    "Listen for whether you kept the linking word — it's often the first thing dropped under pressure.",
    "On long sentences, accuracy usually drops near the end — focus on finishing cleanly.",
    "You just handled the hardest sentence in the set — notice which part you kept versus improvised.",
]

INTERVIEW_BEFORE: list[list[str]] = [
    ["Answer the actual question in your first sentence before adding anything else."],
    ["Add one concrete detail — a name, place, or number — instead of a general statement."],
    [
        "State your opinion in one sentence, then give exactly one reason and one example.",
        "It's fine to disagree with the premise of the question, as long as you explain why.",
    ],
    ["Answer the hypothetical directly ('I would...') before you explain your reasoning."],
]

INTERVIEW_AFTER: list[str] = [
    "Check that your first sentence directly answered the question, not just related to it.",
    "Did you include a specific detail, or did the answer stay general?",
    "Listen for whether you actually gave a reason — 'because...' is what earns development credit.",
    "Notice if you trailed off near the end — plan a short closing sentence for 45-second answers.",
]


def get_toefl_tips() -> dict:
    return {
        "listen_repeat": {"before": LISTEN_REPEAT_BEFORE, "after": LISTEN_REPEAT_AFTER},
        "interview": {"before": INTERVIEW_BEFORE, "after": INTERVIEW_AFTER},
    }

"""Pronunciation Lab content: American-English IPA catalog, minimal pairs, technique lessons.

The minimal-pair drill is the honest local pronunciation test: the learner is asked
to say one specific word of a pair, faster-whisper transcribes it, and whichever word
the recognizer heard is the verdict. Tracked per phoneme contrast, this builds a real
"weak sounds" profile with no cloud service and no black-box scoring.
"""

IPA_VOWELS = [
    {"symbol": "iː", "name": "FLEECE", "examples": ["see", "team", "believe"], "tip": "Long and tense — smile slightly, tongue high and forward."},
    {"symbol": "ɪ", "name": "KIT", "examples": ["sit", "gym", "busy"], "tip": "Short and relaxed — jaw slightly more open than /iː/."},
    {"symbol": "ɛ", "name": "DRESS", "examples": ["bed", "said", "friend"], "tip": "Mid-front vowel — mouth more open than /ɪ/."},
    {"symbol": "æ", "name": "TRAP", "examples": ["cat", "hand", "laugh"], "tip": "Open your jaw wide — this vowel barely exists in many languages."},
    {"symbol": "ʌ", "name": "STRUT", "examples": ["cup", "love", "enough"], "tip": "Short central sound — like a relaxed grunt, lips neutral."},
    {"symbol": "ə", "name": "schwa", "examples": ["about", "problem", "banana"], "tip": "The most common English sound — quick, weak, totally relaxed."},
    {"symbol": "ɜr", "name": "NURSE", "examples": ["her", "bird", "work"], "tip": "American r-colored vowel — curl the tongue tip back while voicing."},
    {"symbol": "ɑ", "name": "LOT / PALM", "examples": ["hot", "father", "car"], "tip": "Open back vowel — drop the jaw, tongue low."},
    {"symbol": "ɔ", "name": "THOUGHT", "examples": ["saw", "call", "bought"], "tip": "Many Americans merge this with /ɑ/ — both are acceptable."},
    {"symbol": "ʊ", "name": "FOOT", "examples": ["put", "good", "could"], "tip": "Short and relaxed — lips slightly rounded, not tight."},
    {"symbol": "uː", "name": "GOOSE", "examples": ["food", "blue", "school"], "tip": "Long and tense — round the lips firmly."},
    {"symbol": "eɪ", "name": "FACE", "examples": ["day", "rain", "eight"], "tip": "A glide from /e/ to /ɪ/ — don't flatten it into one sound."},
    {"symbol": "aɪ", "name": "PRICE", "examples": ["my", "time", "height"], "tip": "Start open /a/, glide up to /ɪ/."},
    {"symbol": "ɔɪ", "name": "CHOICE", "examples": ["boy", "coin", "enjoy"], "tip": "Round lips for /ɔ/, then glide to /ɪ/."},
    {"symbol": "aʊ", "name": "MOUTH", "examples": ["now", "house", "crowd"], "tip": "Start open, glide toward rounded /ʊ/."},
    {"symbol": "oʊ", "name": "GOAT", "examples": ["go", "boat", "though"], "tip": "American /oʊ/ is a glide — end with rounded lips."},
]

IPA_CONSONANTS = [
    {"symbol": "θ", "name": "voiceless TH", "examples": ["think", "birthday", "math"], "tip": "Tongue tip lightly between the teeth, push air — no voice."},
    {"symbol": "ð", "name": "voiced TH", "examples": ["this", "mother", "breathe"], "tip": "Same tongue position as /θ/ but with your voice on."},
    {"symbol": "r", "name": "American R", "examples": ["red", "sorry", "car"], "tip": "Curl the tongue back without touching the roof of the mouth."},
    {"symbol": "l", "name": "L", "examples": ["light", "yellow", "feel"], "tip": "Tongue tip touches the ridge behind your top teeth."},
    {"symbol": "v", "name": "V", "examples": ["very", "seven", "love"], "tip": "Top teeth on bottom lip with voice — don't round into /w/."},
    {"symbol": "w", "name": "W", "examples": ["west", "away", "quick"], "tip": "Round the lips tightly, no teeth contact at all."},
    {"symbol": "ŋ", "name": "NG", "examples": ["sing", "thinking", "long"], "tip": "Back of tongue up — and no extra /g/ or /k/ after it."},
    {"symbol": "ʃ", "name": "SH", "examples": ["ship", "nation", "wish"], "tip": "Lips slightly rounded, tongue pulled back from the teeth."},
    {"symbol": "ʒ", "name": "ZH", "examples": ["measure", "vision", "usually"], "tip": "Voiced /ʃ/ — rare at word start, common in the middle."},
    {"symbol": "tʃ", "name": "CH", "examples": ["chair", "teacher", "watch"], "tip": "A quick /t/ released into /ʃ/."},
    {"symbol": "dʒ", "name": "J", "examples": ["judge", "enjoy", "bridge"], "tip": "Voiced /tʃ/ — a quick /d/ released into /ʒ/."},
    {"symbol": "ɾ", "name": "Flap T", "examples": ["water", "better", "city"], "tip": "American T between vowels sounds like a fast, light D."},
]

# Minimal pairs: the learner is told to say one specific word; whisper judges which it heard.
MINIMAL_PAIRS = [
    {
        "id": "mp_i_ii", "contrast": "/ɪ/ vs /iː/", "label": "ship vs sheep",
        "description": "Short relaxed /ɪ/ against long tense /iː/ — the classic learner contrast.",
        "pairs": [["ship", "sheep"], ["bit", "beat"], ["sit", "seat"], ["fill", "feel"], ["live", "leave"], ["chip", "cheap"]],
    },
    {
        "id": "mp_ae_e", "contrast": "/æ/ vs /ɛ/", "label": "bad vs bed",
        "description": "Open your jaw wide for /æ/; /ɛ/ is closer and more relaxed.",
        "pairs": [["bad", "bed"], ["man", "men"], ["sat", "set"], ["pan", "pen"], ["axe", "ex"]],
    },
    {
        "id": "mp_ae_uh", "contrast": "/æ/ vs /ʌ/", "label": "cat vs cut",
        "description": "/æ/ is front and open; /ʌ/ is central and quick.",
        "pairs": [["cat", "cut"], ["bat", "but"], ["ran", "run"], ["cap", "cup"], ["fan", "fun"]],
    },
    {
        "id": "mp_th_s", "contrast": "/θ/ vs /s/", "label": "think vs sink",
        "description": "Tongue between the teeth for /θ/ — behind the teeth for /s/.",
        "pairs": [["think", "sink"], ["thick", "sick"], ["path", "pass"], ["worth", "worse"], ["mouth", "mouse"]],
    },
    {
        "id": "mp_th_t", "contrast": "/θ/ vs /t/", "label": "three vs tree",
        "description": "Air flows continuously through /θ/; /t/ is a full stop.",
        "pairs": [["three", "tree"], ["thin", "tin"], ["thank", "tank"], ["thought", "taught"]],
    },
    {
        "id": "mp_dh_d", "contrast": "/ð/ vs /d/", "label": "they vs day",
        "description": "Voiced TH keeps air flowing; /d/ blocks it completely.",
        "pairs": [["they", "day"], ["then", "den"], ["though", "dough"], ["there", "dare"]],
    },
    {
        "id": "mp_l_r", "contrast": "/l/ vs /r/", "label": "light vs right",
        "description": "Tongue touches the ridge for /l/; it curls back without contact for /r/.",
        "pairs": [["light", "right"], ["glass", "grass"], ["fly", "fry"], ["collect", "correct"], ["load", "road"]],
    },
    {
        "id": "mp_v_w", "contrast": "/v/ vs /w/", "label": "vest vs west",
        "description": "Teeth on lip for /v/; rounded lips with no teeth for /w/.",
        "pairs": [["vest", "west"], ["vine", "wine"], ["veil", "whale"], ["vow", "wow"], ["verse", "worse"]],
    },
    {
        "id": "mp_b_p", "contrast": "/b/ vs /p/", "label": "buy vs pie",
        "description": "Both use the lips — /b/ is voiced, /p/ has a puff of air.",
        "pairs": [["buy", "pie"], ["bear", "pear"], ["back", "pack"], ["cab", "cap"]],
    },
    {
        "id": "mp_sh_s", "contrast": "/ʃ/ vs /s/", "label": "she vs see",
        "description": "Pull the tongue back and round the lips slightly for /ʃ/.",
        "pairs": [["she", "see"], ["ship", "sip"], ["shelf", "self"], ["shine", "sign"]],
    },
    {
        "id": "mp_ch_sh", "contrast": "/tʃ/ vs /ʃ/", "label": "chair vs share",
        "description": "/tʃ/ starts with a stop; /ʃ/ flows from the first instant.",
        "pairs": [["chair", "share"], ["watch", "wash"], ["cheap", "sheep"], ["catch", "cash"], ["chip", "ship"]],
    },
    {
        "id": "mp_u_uu", "contrast": "/ʊ/ vs /uː/", "label": "full vs fool",
        "description": "Short relaxed /ʊ/ against long rounded /uː/.",
        "pairs": [["full", "fool"], ["pull", "pool"], ["look", "Luke"]],
    },
]

# Technique lessons. Practice lines are scored with the shadowing alignment engine
# plus delivery metrics, so learners get instant local feedback.
LESSONS = [
    {
        "id": "ls_word_stress",
        "title": "Word Stress",
        "focus": "Stressing the right syllable",
        "explanation": (
            "Every English word with two or more syllables has one syllable that is longer, "
            "louder, and higher in pitch. Stressing the wrong syllable confuses listeners more "
            "than almost any single-sound mistake, because stress is how English ears find words."
        ),
        "tips": [
            "Nouns usually stress early (PREsent, REcord); verbs often stress late (preSENT, reCORD).",
            "Stretch the stressed vowel — make it twice as long as you think you need.",
            "Weak syllables usually reduce to schwa /ə/.",
        ],
        "practice_lines": [
            {"text": "I'd like to present you with this present.", "note": "preSENT (verb) … PREsent (noun)"},
            {"text": "They record every record the band makes.", "note": "reCORD (verb) … REcord (noun)"},
            {"text": "The photographer took a photograph of the photography club.", "note": "phoTOGrapher … PHOtograph … phoTOGraphy"},
            {"text": "Economics is an important subject in the economy.", "note": "ecoNOMics … eCONomy"},
        ],
    },
    {
        "id": "ls_sentence_stress",
        "title": "Sentence Stress & Rhythm",
        "focus": "Stressing content words, reducing the rest",
        "explanation": (
            "English rhythm comes from stressing content words — nouns, main verbs, adjectives, "
            "adverbs — while grammar words (articles, prepositions, auxiliaries) get squeezed "
            "short. Giving every word equal weight sounds robotic and is hard to follow."
        ),
        "tips": [
            "Stress the words you would keep in a telegram: DOG ATE HOMEWORK.",
            "Function words like 'to', 'of', 'and', 'can' shrink to almost nothing.",
            "Keep the time between stressed words roughly equal — that's the English beat.",
        ],
        "practice_lines": [
            {"text": "The dog ate my homework on the way to school.", "note": "DOG ATE HOMEwork WAY SCHOOL"},
            {"text": "I've been waiting for an answer since Monday morning.", "note": "WAITing ANswer MONday MORning"},
            {"text": "She can speak three languages but she can't write them.", "note": "stress CAN'T, reduce can"},
            {"text": "We should have gone to the earlier show.", "note": "'should have' → 'should've'"},
        ],
    },
    {
        "id": "ls_intonation",
        "title": "Intonation",
        "focus": "Falling and rising pitch patterns",
        "explanation": (
            "Statements and wh-questions fall at the end; yes/no questions rise. Lists rise on "
            "each item and fall on the last. Flat intonation makes fluent grammar sound bored or "
            "unsure — pitch is where English carries attitude."
        ),
        "tips": [
            "Fall clearly at the end of statements — it signals confidence and completion.",
            "Rise on yes/no questions: 'Are you COMing?'",
            "Use fall-rise to sound polite when correcting or disagreeing.",
        ],
        "practice_lines": [
            {"text": "I grew up in a small town near the mountains.", "note": "fall at the end"},
            {"text": "Are you coming to the meeting this afternoon?", "note": "rise at the end"},
            {"text": "We need eggs, milk, bread, and coffee.", "note": "rise, rise, rise, fall"},
            {"text": "Where did you learn to cook like that?", "note": "wh-question: fall"},
        ],
    },
    {
        "id": "ls_linking",
        "title": "Linking",
        "focus": "Connecting words smoothly",
        "explanation": (
            "Native speakers don't pause between words — final consonants attach to the next "
            "word's vowel ('turn off' → 'tur-noff'), and identical sounds merge ('gas station' "
            "→ 'ga-station'). Linking is the difference between careful reading and real speech."
        ),
        "tips": [
            "Consonant + vowel: link them — 'an apple' sounds like 'a-napple'.",
            "Vowel + vowel: a tiny /w/ or /y/ appears — 'go on' → 'go-won'.",
            "Same consonant twice: say it once, slightly longer — 'big game'.",
        ],
        "practice_lines": [
            {"text": "Turn off the lights when you leave the office.", "note": "tur-noff … thee-office"},
            {"text": "Can I have an apple and an orange?", "note": "ca-nI … a-napple … a-norange"},
            {"text": "She works at a gas station on the edge of town.", "note": "ga-station … edge-of"},
            {"text": "Go on, tell us what happened next.", "note": "go-won … wha-thappened"},
        ],
    },
    {
        "id": "ls_reduction",
        "title": "Reductions",
        "focus": "gonna, wanna, and the disappearing sounds of fast speech",
        "explanation": (
            "In natural American speech, common word groups compress: 'going to' → 'gonna', "
            "'want to' → 'wanna', 'kind of' → 'kinda'. You don't have to use them in the TOEFL, "
            "but you must recognize them — and using light reductions makes you sound natural."
        ),
        "tips": [
            "'have to' → 'hafta', 'has to' → 'hasta' in everyday speech.",
            "Don't reduce in careful contexts — but never say 'going to' with equal stress on both words.",
            "Listen for 'didja', 'whaddaya' — they're 'did you' and 'what do you'.",
        ],
        "practice_lines": [
            {"text": "I'm going to call you when I get home.", "note": "gonna … when-I-get"},
            {"text": "Do you want to grab some lunch later?", "note": "wanna"},
            {"text": "I have to finish this report by Friday.", "note": "hafta"},
            {"text": "What do you think we should do about it?", "note": "whaddaya think"},
        ],
    },
    {
        "id": "ls_flap_t",
        "title": "The American Flap T",
        "focus": "Why 'water' sounds like 'wadder'",
        "explanation": (
            "When T sits between two vowel sounds and the second syllable is unstressed, "
            "Americans flap it — a fast, light D. 'Water' → 'wadder', 'better' → 'bedder', "
            "'meeting' → 'meeding'. A crisp T there actually sounds British or over-careful."
        ),
        "tips": [
            "Flap inside words: city, party, native, beautiful.",
            "Flap across words too: 'a lot of' → 'a lodda'.",
            "Keep the true T at the start of words and in stressed syllables: 'attack', 'return'.",
        ],
        "practice_lines": [
            {"text": "Can I get a little bit of water, please?", "note": "liddle biddof wadder"},
            {"text": "The meeting starts at eight thirty on Saturday.", "note": "meeding … Saderday"},
            {"text": "My daughter is a better writer than I am.", "note": "dawder … bedder … wrider"},
            {"text": "There's a lot of traffic in the city today.", "note": "a lodda … siddy"},
        ],
    },
]


def get_lab_content():
    return {
        "vowels": IPA_VOWELS,
        "consonants": IPA_CONSONANTS,
        "minimal_pairs": MINIMAL_PAIRS,
        "lessons": LESSONS,
    }


def find_pair_set(pair_set_id: str):
    for p in MINIMAL_PAIRS:
        if p["id"] == pair_set_id:
            return p
    return None


def find_lesson(lesson_id: str):
    for lesson in LESSONS:
        if lesson["id"] == lesson_id:
            return lesson
    return None

"""Listening practice items: transcripts, segments, and comprehension questions.

Playback is client-side. Each item supports an optional `audio_url` for freely
licensed real recordings (LibriVox, Tatoeba, CC-licensed podcasts) — when absent,
the browser's en-US speechSynthesis reads the segments (offline, adjustable speed,
distinct pitches per speaker in conversations). Quizzes are scored locally.
"""

LISTENING_ITEMS = [
    {
        "id": "li_01",
        "title": "Ordering at a Restaurant",
        "type": "conversation",
        "difficulty": "beginner",
        "audio_url": None,
        "segments": [
            {"speaker": "Server", "text": "Hi there! Welcome to Rosie's. Can I start you off with something to drink?"},
            {"speaker": "Customer", "text": "Yes, I'll have an iced tea, please. No sugar."},
            {"speaker": "Server", "text": "Sure thing. Are you ready to order, or do you need a few more minutes?"},
            {"speaker": "Customer", "text": "I think I'm ready. What comes with the grilled chicken sandwich?"},
            {"speaker": "Server", "text": "It comes with fries, but you can swap those for a side salad for a dollar more."},
            {"speaker": "Customer", "text": "Let's do the salad then. And could I get the dressing on the side?"},
            {"speaker": "Server", "text": "Absolutely. So that's a grilled chicken sandwich with a side salad, dressing on the side, and an unsweetened iced tea."},
            {"speaker": "Customer", "text": "Perfect, thank you!"},
        ],
        "questions": [
            {"q": "What does the customer order to drink?", "options": ["Coffee", "Iced tea with sugar", "Iced tea without sugar", "Lemonade"], "answer": 2},
            {"q": "What normally comes with the sandwich?", "options": ["A side salad", "Fries", "Soup", "Nothing"], "answer": 1},
            {"q": "How much extra does the salad swap cost?", "options": ["Nothing", "Fifty cents", "One dollar", "Two dollars"], "answer": 2},
        ],
    },
    {
        "id": "li_02",
        "title": "Campus Housing Voicemail",
        "type": "announcement",
        "difficulty": "beginner",
        "audio_url": None,
        "segments": [
            {"speaker": "Voicemail", "text": "Hello, this is a message from the University Housing Office."},
            {"speaker": "Voicemail", "text": "Our records show you haven't picked up your room key for the fall semester."},
            {"speaker": "Voicemail", "text": "Keys can be collected from the main office in Harmon Hall, Monday through Friday, between nine and five."},
            {"speaker": "Voicemail", "text": "Please bring your student ID card and a copy of your housing contract."},
            {"speaker": "Voicemail", "text": "If you no longer need campus housing, call us back at extension four-two-one-five before Friday to cancel without a fee."},
        ],
        "questions": [
            {"q": "What hasn't the student done yet?", "options": ["Paid tuition", "Picked up a room key", "Signed the contract", "Chosen a meal plan"], "answer": 1},
            {"q": "What TWO things must the student bring?", "options": ["ID card and housing contract", "Passport and photo", "Payment and ID card", "Contract and key deposit"], "answer": 0},
            {"q": "What happens if they cancel before Friday?", "options": ["They pay a small fee", "They lose their deposit", "There is no fee", "They must reapply"], "answer": 2},
        ],
    },
    {
        "id": "li_03",
        "title": "Why We Procrastinate",
        "type": "ted_style",
        "difficulty": "intermediate",
        "audio_url": None,
        "segments": [
            {"speaker": "Speaker", "text": "Everyone thinks procrastination is a time-management problem. It isn't."},
            {"speaker": "Speaker", "text": "Research shows procrastination is actually an emotion-management problem."},
            {"speaker": "Speaker", "text": "We delay tasks that trigger uncomfortable feelings — boredom, anxiety, self-doubt."},
            {"speaker": "Speaker", "text": "Checking your phone gives instant relief from those feelings, and the brain remembers that relief."},
            {"speaker": "Speaker", "text": "So the cycle strengthens: task, discomfort, escape, repeat."},
            {"speaker": "Speaker", "text": "The fix isn't a better calendar. It's lowering the emotional cost of starting."},
            {"speaker": "Speaker", "text": "Try committing to just two minutes of the task. Starting is the hard part — momentum usually does the rest."},
        ],
        "questions": [
            {"q": "According to the speaker, procrastination is really a problem of…", "options": ["time management", "emotion management", "laziness", "poor planning"], "answer": 1},
            {"q": "Why does phone-checking strengthen the cycle?", "options": ["It wastes time", "It gives instant relief the brain remembers", "It causes anxiety", "It improves mood permanently"], "answer": 1},
            {"q": "What fix does the speaker suggest?", "options": ["A better calendar", "Working longer hours", "Committing to two minutes of the task", "Removing all distractions"], "answer": 2},
        ],
    },
    {
        "id": "li_04",
        "title": "Advising Appointment",
        "type": "conversation",
        "difficulty": "intermediate",
        "audio_url": None,
        "segments": [
            {"speaker": "Advisor", "text": "So, you wanted to talk about switching your major from biology to psychology?"},
            {"speaker": "Student", "text": "Yes. I enjoyed my intro psych class way more than any of my bio courses."},
            {"speaker": "Advisor", "text": "That's a common path. The good news is most of your science credits will still count."},
            {"speaker": "Student", "text": "Really? I was worried I'd lose a whole year."},
            {"speaker": "Advisor", "text": "Not a year. But the statistics requirement is different — you'd need to take it next semester to stay on track."},
            {"speaker": "Student", "text": "Okay. Is that class hard to get into?"},
            {"speaker": "Advisor", "text": "It fills up fast. Registration opens Monday, so I'd sign up first thing that morning."},
            {"speaker": "Student", "text": "I'll set an alarm. Thanks — this feels a lot less scary now."},
        ],
        "questions": [
            {"q": "What change is the student considering?", "options": ["Transferring universities", "Switching from biology to psychology", "Dropping out", "Adding a second major"], "answer": 1},
            {"q": "What was the student worried about?", "options": ["Losing credits and time", "Higher tuition", "Disappointing parents", "Harder exams"], "answer": 0},
            {"q": "What does the advisor recommend doing Monday?", "options": ["Meeting again", "Emailing the professor", "Registering as early as possible", "Taking a placement test"], "answer": 2},
        ],
    },
    {
        "id": "li_05",
        "title": "The Honeybee Waggle Dance",
        "type": "academic",
        "difficulty": "advanced",
        "audio_url": None,
        "segments": [
            {"speaker": "Professor", "text": "When a honeybee scout finds a rich patch of flowers, she doesn't keep it to herself."},
            {"speaker": "Professor", "text": "She returns to the hive and performs what biologists call a waggle dance."},
            {"speaker": "Professor", "text": "The dance is a figure-eight, and its middle section — the waggle run — encodes remarkably precise information."},
            {"speaker": "Professor", "text": "The angle of the run relative to vertical tells the other bees the direction of the flowers relative to the sun."},
            {"speaker": "Professor", "text": "And the duration of the waggle communicates distance — roughly one second of dancing per kilometer of flight."},
            {"speaker": "Professor", "text": "What makes this extraordinary is that it's symbolic communication: the dance refers to something distant in space and time."},
            {"speaker": "Professor", "text": "For decades, some scientists doubted the dance hypothesis, until robotic bees programmed to dance successfully recruited real foragers."},
        ],
        "questions": [
            {"q": "What does the ANGLE of the waggle run communicate?", "options": ["Distance to the flowers", "Direction relative to the sun", "Quality of the nectar", "Time of day"], "answer": 1},
            {"q": "How is distance encoded?", "options": ["Duration of the waggle", "Number of figure-eights", "Loudness of buzzing", "Speed of walking"], "answer": 0},
            {"q": "How was the dance hypothesis eventually confirmed?", "options": ["Better cameras", "Robotic bees recruited real foragers", "Genetic analysis", "Observing wild hives"], "answer": 1},
            {"q": "Why does the professor call the dance 'extraordinary'?", "options": ["It is beautiful", "It refers to things distant in space and time", "It is very loud", "Only queens can do it"], "answer": 1},
        ],
    },
    {
        "id": "li_06",
        "title": "Podcast: The Four-Day Workweek",
        "type": "podcast",
        "difficulty": "advanced",
        "audio_url": None,
        "segments": [
            {"speaker": "Host", "text": "This week, dozens of companies wrapped up the largest four-day workweek trial ever conducted."},
            {"speaker": "Host", "text": "The headline result: revenue stayed flat or rose at most participating firms."},
            {"speaker": "Guest", "text": "Right, and what surprised researchers wasn't productivity — it was retention."},
            {"speaker": "Guest", "text": "Resignations dropped by more than half compared with the previous year."},
            {"speaker": "Host", "text": "So people weren't just as productive — they also stopped quitting."},
            {"speaker": "Guest", "text": "Exactly. Though we should be careful: companies that volunteered for the trial were probably flexible workplaces to begin with."},
            {"speaker": "Guest", "text": "A factory with fixed shifts can't compress output the way a marketing agency can."},
            {"speaker": "Host", "text": "So the honest conclusion is: promising, but not yet proven for every industry."},
        ],
        "questions": [
            {"q": "What was the headline business result of the trial?", "options": ["Revenue fell slightly", "Revenue stayed flat or rose", "Costs doubled", "Profits were not measured"], "answer": 1},
            {"q": "What result most surprised researchers?", "options": ["Productivity gains", "The drop in resignations", "Customer complaints", "Longer meetings"], "answer": 1},
            {"q": "What caution does the guest raise?", "options": ["The data was falsified", "Participating companies were probably already flexible", "The trial was too long", "Employees worked secretly on Fridays"], "answer": 1},
        ],
    },
]


def get_items():
    return [
        {k: v for k, v in item.items() if k not in ("segments", "questions")}
        | {"segment_count": len(item["segments"]), "question_count": len(item["questions"])}
        for item in LISTENING_ITEMS
    ]


def get_item(item_id: str, include_answers: bool = False):
    for item in LISTENING_ITEMS:
        if item["id"] == item_id:
            if include_answers:
                return item
            return {
                **{k: v for k, v in item.items() if k != "questions"},
                "questions": [{"q": q["q"], "options": q["options"]} for q in item["questions"]],
            }
    return None


def grade(item_id: str, answers: list) -> dict | None:
    item = get_item(item_id, include_answers=True)
    if not item:
        return None
    questions = item["questions"]
    detail = []
    score = 0
    for i, q in enumerate(questions):
        given = answers[i] if i < len(answers) else None
        correct = given == q["answer"]
        score += 1 if correct else 0
        detail.append({"question": q["q"], "given": given, "correct_answer": q["answer"], "correct": correct})
    return {"score": score, "total": len(questions), "detail": detail}

"""Shadowing passages: natural American-English texts split into sentences.

Sentence-by-sentence audio is produced client-side with speechSynthesis (offline,
en-US voice, adjustable rate). The structure supports an optional `audio_url` per
passage for freely-licensed real recordings (e.g. LibriVox / Tatoeba) if the user
adds them later — the player falls back to TTS when absent.
"""

SHADOWING_PASSAGES = [
    {
        "id": "sh_01",
        "title": "Morning Coffee Run",
        "difficulty": "beginner",
        "category": "Everyday life",
        "audio_url": None,
        "sentences": [
            "Every morning, I stop by the coffee shop on my way to work.",
            "The line is usually long, but it moves pretty fast.",
            "I always order a medium coffee with a little milk.",
            "The barista knows my name and my order by now.",
            "It costs about three dollars, which adds up over time.",
            "Still, that first sip makes the whole day feel easier.",
        ],
    },
    {
        "id": "sh_02",
        "title": "Asking for Directions",
        "difficulty": "beginner",
        "category": "Everyday life",
        "audio_url": None,
        "sentences": [
            "Excuse me, could you tell me how to get to the train station?",
            "Sure, go straight down this street for two blocks.",
            "Then turn left at the traffic light by the bank.",
            "You'll see the station entrance right across from the park.",
            "It's about a ten minute walk from here.",
            "You can't miss it — there's a big clock above the doors.",
        ],
    },
    {
        "id": "sh_03",
        "title": "The Study Group",
        "difficulty": "intermediate",
        "category": "Campus life",
        "audio_url": None,
        "sentences": [
            "Our professor suggested we form study groups before the midterm.",
            "At first, I wasn't sure it would actually help me.",
            "I usually prefer to review the material on my own.",
            "But explaining concepts to other people turned out to be powerful.",
            "When you teach something, you quickly discover what you don't understand.",
            "By the end of the semester, our group met twice a week.",
            "My grade improved, and I made three good friends along the way.",
        ],
    },
    {
        "id": "sh_04",
        "title": "A Job Interview Tip",
        "difficulty": "intermediate",
        "category": "Work & career",
        "audio_url": None,
        "sentences": [
            "Before any interview, research the company for at least an hour.",
            "Look at their website, their products, and their recent news.",
            "Prepare two or three thoughtful questions to ask at the end.",
            "Interviewers remember candidates who seem genuinely curious.",
            "Practice your answers out loud, not just in your head.",
            "Speaking the words changes how confident they sound in the room.",
        ],
    },
    {
        "id": "sh_05",
        "title": "Why Cities Plant Trees",
        "difficulty": "intermediate",
        "category": "Academic",
        "audio_url": None,
        "sentences": [
            "Many cities are planting thousands of trees along their streets.",
            "Trees provide shade, which lowers summer temperatures significantly.",
            "They also absorb rainwater and reduce the risk of flooding.",
            "Studies show that green streets encourage people to walk more.",
            "Property values often rise in neighborhoods with mature trees.",
            "For a relatively small cost, trees deliver decades of benefits.",
        ],
    },
    {
        "id": "sh_06",
        "title": "The Memory Lecture",
        "difficulty": "advanced",
        "category": "Academic",
        "audio_url": None,
        "sentences": [
            "Human memory doesn't work like a video recording of events.",
            "Instead, each time we recall something, we partially reconstruct it.",
            "That reconstruction can be influenced by our current emotions and beliefs.",
            "This is why two people remember the same conversation so differently.",
            "Researchers have even implanted entirely false memories in laboratory settings.",
            "Understanding this fragility should make us more humble about certainty.",
            "It also explains why eyewitness testimony is less reliable than juries assume.",
        ],
    },
    {
        "id": "sh_07",
        "title": "Negotiating the Rent",
        "difficulty": "advanced",
        "category": "Everyday life",
        "audio_url": None,
        "sentences": [
            "When my landlord announced a rent increase, I decided to negotiate.",
            "I gathered listings for comparable apartments in the neighborhood.",
            "Then I politely pointed out that I'd never paid late in three years.",
            "Reliable tenants are valuable, and replacing one is expensive.",
            "I proposed a smaller increase in exchange for signing a longer lease.",
            "To my surprise, she accepted the offer almost immediately.",
            "The whole conversation took fifteen minutes and saved me six hundred dollars.",
        ],
    },
    {
        "id": "sh_08",
        "title": "TOEFL-Style: Campus Announcement",
        "difficulty": "advanced",
        "category": "TOEFL practice",
        "audio_url": None,
        "sentences": [
            "The university library will extend its hours during final examination week.",
            "Beginning Monday, all three floors will remain open until two in the morning.",
            "Additional staff will be available at the research help desk each evening.",
            "Students are reminded to bring their identification cards for late entry.",
            "Free coffee and snacks will be provided in the lobby after ten.",
            "The administration hopes these changes will reduce stress during finals.",
        ],
    },
]


def get_passages():
    return [
        {k: v for k, v in p.items() if k != "sentences"} | {"sentence_count": len(p["sentences"])}
        for p in SHADOWING_PASSAGES
    ]


def get_passage(passage_id: str):
    for p in SHADOWING_PASSAGES:
        if p["id"] == passage_id:
            return p
    return None

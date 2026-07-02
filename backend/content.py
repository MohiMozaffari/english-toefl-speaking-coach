"""Static content banks: General English topics and TOEFL Speaking task prompts."""

GENERAL_TOPICS = [
    # Daily life
    {"id": "g01", "category": "Daily life", "prompt": "Describe your typical morning routine. What do you usually do before you leave the house?"},
    {"id": "g02", "category": "Daily life", "prompt": "Talk about your favorite meal of the day. What do you usually eat and why do you like it?"},
    {"id": "g03", "category": "Daily life", "prompt": "Describe how you usually spend your weekends."},
    {"id": "g04", "category": "Daily life", "prompt": "Talk about a typical day at your job or school."},
    {"id": "g05", "category": "Daily life", "prompt": "Describe your favorite hobby and why you enjoy it."},
    # Opinions
    {"id": "g06", "category": "Opinions", "prompt": "Do you think social media has a positive or negative effect on people's lives? Explain your opinion."},
    {"id": "g07", "category": "Opinions", "prompt": "What do you think is the best way to learn a new language?"},
    {"id": "g08", "category": "Opinions", "prompt": "Do you prefer living in a big city or a small town? Why?"},
    {"id": "g09", "category": "Opinions", "prompt": "Do you think it's important for children to learn to cook? Why or why not?"},
    {"id": "g10", "category": "Opinions", "prompt": "What do you think makes someone a good friend?"},
    # Past experiences
    {"id": "g11", "category": "Past experiences", "prompt": "Talk about a memorable trip you took. Where did you go and what did you do?"},
    {"id": "g12", "category": "Past experiences", "prompt": "Describe a time when you learned something new that was difficult at first."},
    {"id": "g13", "category": "Past experiences", "prompt": "Talk about a mistake you made and what you learned from it."},
    {"id": "g14", "category": "Past experiences", "prompt": "Describe a celebration or holiday you remember well."},
    {"id": "g15", "category": "Past experiences", "prompt": "Talk about a time you helped someone else."},
    # Future plans
    {"id": "g16", "category": "Future plans", "prompt": "What are your goals for the next five years?"},
    {"id": "g17", "category": "Future plans", "prompt": "If you could travel anywhere next year, where would you go and why?"},
    {"id": "g18", "category": "Future plans", "prompt": "Talk about a skill you would like to learn in the future."},
    {"id": "g19", "category": "Future plans", "prompt": "Describe your dream job. What would you do and why?"},
    {"id": "g20", "category": "Future plans", "prompt": "What changes would you like to make in your life this year?"},
    # Describing people/places
    {"id": "g21", "category": "People & places", "prompt": "Describe a person you admire. What makes them special to you?"},
    {"id": "g22", "category": "People & places", "prompt": "Describe your hometown to someone who has never been there."},
    {"id": "g23", "category": "People & places", "prompt": "Talk about a family member you are close to and what you like doing together."},
    {"id": "g24", "category": "People & places", "prompt": "Describe your favorite place to relax."},
]

# --- TOEFL Speaking content -------------------------------------------------
# Reflects the redesigned TOEFL iBT Speaking section that launched January 21, 2026:
# two tasks, ~8 minutes total, 11 items, no prep time on either task.
#   Listen and Repeat: 7 sentences per set, response time increases as sentences get longer.
#   Take an Interview: 4 questions per set on one familiar topic, 45s response each.

LISTEN_REPEAT_ITEM_SECONDS = [8, 8, 10, 10, 10, 12, 12]
INTERVIEW_ITEM_SECONDS = [45, 45, 45, 45]

LISTEN_AND_REPEAT_SETS = [
    {
        "id": "lr_01",
        "task": "listen_repeat",
        "title": "Campus Library",
        "picture_caption": "A university library reading room with students studying at desks",
        "sentences": [
            "The library opens at eight.",
            "Students can borrow books for three weeks.",
            "Please remember to return your books on time.",
            "The quiet study room is located on the second floor.",
            "Group study rooms must be reserved online in advance.",
            "If you need help finding a book, ask the librarian at the front desk.",
            "The library will be closed next Monday for the national holiday, so plan your visit accordingly.",
        ],
    },
    {
        "id": "lr_02",
        "task": "listen_repeat",
        "title": "Campus Cafeteria",
        "picture_caption": "A busy campus cafeteria with a salad bar and students in a lunch line",
        "sentences": [
            "Lunch starts at noon.",
            "The cafeteria accepts both cash and cards.",
            "Vegetarian options are available every day.",
            "The salad bar is next to the main entrance.",
            "Students can use their meal plan for breakfast and dinner.",
            "During finals week, the cafeteria stays open two hours later than usual.",
            "If you have a food allergy, please inform the staff before ordering your meal.",
        ],
    },
    {
        "id": "lr_03",
        "task": "listen_repeat",
        "title": "Dormitory Move-in Day",
        "picture_caption": "Students carrying boxes and suitcases into a dormitory on move-in day",
        "sentences": [
            "Move-in day is Saturday.",
            "Bring your student ID to check in.",
            "Volunteers will help carry your bags upstairs.",
            "Each room comes with a bed, desk, and closet.",
            "You can pick up your room key at the front office.",
            "Parking permits for move-in day must be requested one week in advance.",
            "New students should attend the orientation meeting in the main hall right after they finish unpacking.",
        ],
    },
]

INTERVIEW_SETS = [
    {
        "id": "iv_01",
        "task": "interview",
        "title": "Free Time and Hobbies",
        "questions": [
            "What do you usually do in your free time?",
            "How did you first become interested in that activity?",
            "Do you prefer doing this activity alone or with other people? Why?",
            "How has this hobby changed the way you spend your weekends?",
        ],
    },
    {
        "id": "iv_02",
        "task": "interview",
        "title": "Travel and New Places",
        "questions": [
            "Do you enjoy traveling to new places? Why or why not?",
            "Tell me about a trip that you remember well.",
            "Would you rather plan every detail of a trip in advance or travel spontaneously?",
            "What is one place you would love to visit in the future, and why?",
        ],
    },
    {
        "id": "iv_03",
        "task": "interview",
        "title": "School and Learning",
        "questions": [
            "What was your favorite subject in school?",
            "Describe a teacher who made a strong impression on you.",
            "Do you prefer studying alone or in a group? Why?",
            "What is something new you would like to learn?",
        ],
    },
]

TOEFL_TIMING = {
    "listen_repeat": {"item_seconds": LISTEN_REPEAT_ITEM_SECONDS},
    "interview": {"item_seconds": INTERVIEW_ITEM_SECONDS},
}


def get_general_topics():
    return GENERAL_TOPICS


def get_toefl_tasks():
    return {
        "listen_repeat": LISTEN_AND_REPEAT_SETS,
        "interview": INTERVIEW_SETS,
    }


def get_toefl_timing():
    return TOEFL_TIMING


def find_toefl_prompt(task_type: str, prompt_id: str):
    tasks = get_toefl_tasks()
    items = tasks.get(task_type, [])
    for item in items:
        if item["id"] == prompt_id:
            return item
    return None


def find_general_topic(topic_id: str):
    for item in GENERAL_TOPICS:
        if item["id"] == topic_id:
            return item
    return None

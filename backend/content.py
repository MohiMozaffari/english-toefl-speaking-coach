"""Content banks: General English topics (static) and TOEFL Speaking prompts (SQLite-backed).

General English topics stay as plain Python data -- they're not part of the TOEFL
prompt/shadowing migration requested for the content library (see database.py).
TOEFL prompts are fetched from data/toefl_coach.db, seeded via seed_db.py.
"""

import database

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


def get_general_topics() -> list[dict]:
    return GENERAL_TOPICS


def find_general_topic(topic_id: str) -> dict | None:
    for item in GENERAL_TOPICS:
        if item["id"] == topic_id:
            return item
    return None


# --- TOEFL Speaking content (SQLite-backed) -----------------------------------
# Reflects the redesigned TOEFL iBT Speaking section that launched January 21, 2026:
# two tasks, ~8 minutes total, 11 items, no prep time on either task.
#   Listen and Repeat: 7 sentences per set, response time increases as sentences get longer.
#   Take an Interview: 4 questions per set on one familiar topic, 45s response each.


def get_toefl_tasks() -> dict:
    return {
        "listen_repeat": database.fetch_toefl_sets("listen_repeat"),
        "interview": database.fetch_toefl_sets("interview"),
    }


def get_toefl_timing() -> dict:
    return {
        "listen_repeat": {"item_seconds": database.fetch_toefl_response_times("listen_repeat")},
        "interview": {"item_seconds": database.fetch_toefl_response_times("interview")},
    }


def find_toefl_prompt(task_type: str, prompt_id: str) -> dict | None:
    return database.fetch_toefl_set(task_type, prompt_id)


def get_random_toefl_prompt(task_type: str) -> dict | None:
    return database.get_random_toefl_prompt(task_type)

"""Local settings storage. Settings live in data/config.json on this machine only.
The API key is never logged or printed anywhere."""

import json
import threading
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
CONFIG_PATH = DATA_DIR / "config.json"

DEFAULT_CONFIG = {
    "base_url": "http://localhost:3001/v1",
    "api_key": "",
    "model": "auto",
    "whisper_model": "small",
    # Single-user preference (the daily XP goal shown on the dashboard). Lives here
    # rather than on a profile row now that the app is single-user.
    "daily_goal_xp": 50,
}

_lock = threading.RLock()


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    _ensure_data_dir()
    with _lock:
        if not CONFIG_PATH.exists():
            CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
            return dict(DEFAULT_CONFIG)
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
        merged = dict(DEFAULT_CONFIG)
        merged.update({k: v for k, v in data.items() if k in DEFAULT_CONFIG})
        return merged


def save_config(update: dict) -> dict:
    _ensure_data_dir()
    with _lock:
        current = load_config()
        for key in DEFAULT_CONFIG:
            if key in update and update[key] is not None:
                current[key] = update[key]
        CONFIG_PATH.write_text(json.dumps(current, indent=2), encoding="utf-8")
        return current

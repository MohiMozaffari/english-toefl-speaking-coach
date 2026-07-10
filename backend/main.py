import tempfile
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

import alignment
import coach
import content
import database
import db
import gamification
import listening_content
import llm_service
import metrics as metrics_mod
import pronunciation_content
import shadowing_content
import stats
import tts_service
import whisper_service
from config import load_config, save_config
from errors import AppError

app = FastAPI(title="English & TOEFL Speaking Coach API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    db.init_db()
    database.init_db()


@app.exception_handler(AppError)
def handle_app_error(_request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})


def _resolve_profile(profile_id: int | None) -> int:
    if profile_id is not None and db.get_profile(profile_id):
        return profile_id
    return db.first_profile_id()


# --- Settings & health -------------------------------------------------------


@app.get("/api/settings")
def get_settings():
    return load_config()


@app.post("/api/settings")
def update_settings(payload: dict):
    allowed = {"base_url", "api_key", "model", "whisper_model", "daily_goal_xp"}
    update = {k: v for k, v in payload.items() if k in allowed}
    if "daily_goal_xp" in update:
        try:
            update["daily_goal_xp"] = max(10, min(500, int(update["daily_goal_xp"])))
        except (TypeError, ValueError):
            del update["daily_goal_xp"]
    return save_config(update)


@app.get("/api/health")
def health():
    config = load_config()
    llm_status = llm_service.check_connection(config)
    whisper_ok = whisper_service.is_installed()
    return {
        "llm": llm_status,
        "whisper": {
            "installed": whisper_ok,
            "message": "faster-whisper is installed."
            if whisper_ok
            else f"faster-whisper is not installed. Run: {whisper_service.PIP_INSTALL_HINT}",
        },
    }


# --- Content -------------------------------------------------------------


@app.get("/api/topics/general")
def general_topics():
    return content.get_general_topics()


@app.get("/api/topics/toefl")
def toefl_topics():
    return {
        "tasks": content.get_toefl_tasks(),
        "timing": content.get_toefl_timing(),
        "tips": content.get_toefl_tips(),
    }


@app.get("/api/topics/toefl-reading")
def toefl_reading_topics():
    return content.get_toefl_reading()


@app.get("/api/shadowing/passages")
def shadowing_passages():
    return shadowing_content.get_passages()


@app.get("/api/shadowing/passages/{passage_id}")
def shadowing_passage(passage_id: str):
    passage = shadowing_content.get_passage(passage_id)
    if not passage:
        raise AppError("Passage not found.", code="not_found", status_code=404)
    return passage


@app.get("/api/shadowing/accents")
def shadowing_accents():
    return tts_service.VOICES_BY_ACCENT


@app.get("/api/shadowing/tts")
async def shadowing_tts(text: str, accent: str = tts_service.DEFAULT_ACCENT, voice: str | None = None):
    if accent not in tts_service.VOICES_BY_ACCENT:
        raise AppError(f"Unknown accent: {accent}", code="bad_accent")
    if voice and voice not in tts_service.ALL_VOICES:
        raise AppError(f"Unknown voice: {voice}", code="bad_voice")
    result = await tts_service.synthesize(text, accent, voice=voice)
    return FileResponse(
        result["audio_path"],
        media_type="audio/mpeg",
        headers={"Cache-Control": "public, max-age=31536000", "X-TTS-Voice": result["voice"]},
    )


@app.get("/api/pronunciation/content")
def pronunciation_lab():
    return pronunciation_content.get_lab_content()


@app.get("/api/listening/items")
def listening_items():
    return listening_content.get_items()


@app.get("/api/listening/items/{item_id}")
def listening_item(item_id: str):
    item = listening_content.get_item(item_id)
    if not item:
        raise AppError("Listening item not found.", code="not_found", status_code=404)
    return item


# --- Transcription helpers -------------------------------------------------------


async def _save_upload(audio: UploadFile) -> str:
    # A 0-byte upload (e.g. a MediaRecorder blip that never produced a chunk) is
    # just the extreme end of "too short" -- write it through and let
    # transcribe_rich() + classify_transcription() turn it into the same
    # graceful too-short result as a very brief real recording, instead of a
    # separate hard error path.
    suffix = Path(audio.filename or "audio.webm").suffix or ".webm"
    data = await audio.read()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(data)
    finally:
        tmp.close()
    return tmp.name


async def _transcribe_upload(audio: UploadFile, whisper_model: str) -> dict:
    tmp_path = await _save_upload(audio)
    try:
        return whisper_service.transcribe_rich(tmp_path, whisper_model)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# --- General practice --------------------------------------------------------


@app.post("/api/practice/general/attempt")
async def general_attempt(
    audio: UploadFile = File(...),
    topic_id: str = Form(...),
    topic_prompt: str = Form(...),
    profile_id: int | None = Form(None),
):
    config = load_config()
    pid = _resolve_profile(profile_id)
    rich = await _transcribe_upload(audio, config["whisper_model"])
    attempt_metrics = metrics_mod.compute_metrics(rich["words"], rich["duration"])
    status = whisper_service.classify_transcription(rich)

    if status == "ok":
        learner_context = coach.learner_context_for_llm(pid)
        feedback = llm_service.get_general_feedback(config, topic_prompt, rich["text"], learner_context)
    else:
        # Too-short/crashed audio or genuine silence: a real, gradeable (if very
        # low) outcome, not an error -- skip the LLM call, there's nothing to
        # evaluate, and return a normal 200 so it shows up in history like any
        # other attempt.
        feedback = llm_service.general_fallback_feedback(status)

    session_id = db.insert_session(
        mode="general",
        task_type=topic_id,
        task_title=topic_prompt,
        task_prompt=topic_prompt,
        transcript=rich["text"],
        feedback=feedback,
        score_band=None,
        metrics=attempt_metrics,
        profile_id=pid,
        prompt_ref=f"general:{topic_id}",
    )
    if status == "ok":
        db.insert_activity(pid, "general", gamification.xp_for("general"), ref=f"session:{session_id}")

    return {"session_id": session_id, "transcript": rich["text"], "feedback": feedback, "metrics": attempt_metrics}


# --- TOEFL practice (2026 format: Listen and Repeat + Take an Interview) ----------


@app.post("/api/practice/toefl/attempt")
async def toefl_attempt(
    audio: List[UploadFile] = File(...),
    task_type: str = Form(...),
    prompt_id: str = Form(...),
    item_index: int | None = Form(None),
    profile_id: int | None = Form(None),
):
    config = load_config()
    pid = _resolve_profile(profile_id)
    if task_type not in ("listen_repeat", "interview"):
        raise AppError(f"Unknown TOEFL task type: {task_type}", code="bad_task_type")

    prompt_item = content.find_toefl_prompt(task_type, prompt_id)
    if not prompt_item:
        raise AppError("Unknown TOEFL prompt id.", code="bad_prompt_id")

    all_items = prompt_item["sentences"] if task_type == "listen_repeat" else prompt_item["questions"]

    # Same content pool and grading pipeline for both modes; only the unit differs.
    # Exam mode (item_index is None) grades the whole set in one report saved as
    # one History entry. Practice mode (item_index set) grades a single item so it
    # can show immediate per-item feedback and be re-done, saved as its own entry.
    if item_index is not None:
        if not 0 <= item_index < len(all_items):
            raise AppError("Item index out of range.", code="bad_item_index")
        items = [all_items[item_index]]
        prompt_ref = f"toefl:{task_type}:{prompt_id}:{item_index}"
        unit = "sentence" if task_type == "listen_repeat" else "question"
        task_title = f"{prompt_item['title']} — {unit} {item_index + 1}"
    else:
        items = all_items
        prompt_ref = f"toefl:{task_type}:{prompt_id}"
        task_title = prompt_item["title"]

    if len(audio) != len(items):
        raise AppError(
            f"Expected {len(items)} recording(s) but received {len(audio)}.",
            code="item_count_mismatch",
        )

    transcripts = []
    item_metrics = []
    item_statuses = []
    for file in audio:
        rich = await _transcribe_upload(file, config["whisper_model"])
        item_metrics.append(metrics_mod.compute_metrics(rich["words"], rich["duration"]))
        item_status = whisper_service.classify_transcription(rich)
        item_statuses.append(item_status)
        if item_status == "ok":
            transcripts.append(rich["text"])
        else:
            # Keep a placeholder in the transcript sent to the LLM so a partially
            # unusable set (e.g. one dropped item out of seven) still reads
            # coherently, instead of an empty string next to real answers.
            transcripts.append("[No usable audio for this item]")

    combined_metrics = metrics_mod.combine_metrics(item_metrics)

    all_too_short = all(s == "too_short" for s in item_statuses)
    if all_too_short:
        feedback = llm_service.toefl_fallback_feedback("too_short", task_type, items)
    elif all(s != "ok" for s in item_statuses):
        # Every item was either silent or too short (but not literally every one
        # crashed) -- still a whole-set "nothing to score" outcome.
        feedback = llm_service.toefl_fallback_feedback("no_speech", task_type, items)
    else:
        learner_context = coach.learner_context_for_llm(pid)
        if task_type == "listen_repeat":
            feedback = llm_service.get_listen_repeat_feedback(
                config, prompt_item["title"], items, transcripts, learner_context
            )
        else:
            feedback = llm_service.get_interview_feedback(
                config, prompt_item["title"], items, transcripts, learner_context
            )

    combined_transcript = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(transcripts))
    session_id = db.insert_session(
        mode="toefl",
        task_type=task_type,
        task_title=task_title,
        task_prompt="; ".join(items),
        transcript=combined_transcript,
        feedback=feedback,
        score_band=feedback.get("score_band"),
        metrics=combined_metrics,
        profile_id=pid,
        prompt_ref=prompt_ref,
    )
    if any(s == "ok" for s in item_statuses):
        score_bonus = (feedback.get("score_band") or 0) * 5
        db.insert_activity(pid, "toefl", gamification.xp_for("toefl", score_bonus), ref=f"session:{session_id}")

    previous_attempts = db.sessions_for_prompt(prompt_ref, pid)

    return {
        "session_id": session_id,
        "transcript": combined_transcript,
        "feedback": feedback,
        "metrics": combined_metrics,
        "previous_attempts": previous_attempts,
    }


# --- Shadowing -----------------------------------------------------------------


@app.post("/api/shadowing/attempt")
async def shadowing_attempt(
    audio: UploadFile = File(...),
    passage_id: str = Form(...),
    sentence_index: int = Form(...),
    profile_id: int | None = Form(None),
):
    config = load_config()
    pid = _resolve_profile(profile_id)
    passage = shadowing_content.get_passage(passage_id)
    if not passage:
        raise AppError("Passage not found.", code="not_found", status_code=404)
    if not 0 <= sentence_index < len(passage["sentences"]):
        raise AppError("Sentence index out of range.", code="bad_index")

    target = passage["sentences"][sentence_index]
    rich = await _transcribe_upload(audio, config["whisper_model"])
    attempt_metrics = metrics_mod.compute_metrics(rich["words"], rich["duration"])

    diff = alignment.align(target, rich["text"])
    fluency = alignment.fluency_score(attempt_metrics, len(diff["target_words"]))

    db.insert_shadowing_attempt(
        pid, passage_id, sentence_index, target, rich["text"],
        diff["accuracy"], fluency, diff, attempt_metrics,
    )
    db.insert_activity(pid, "shadowing_sentence", gamification.xp_for("shadowing_sentence"),
                       ref=f"{passage_id}:{sentence_index}")

    return {
        "target": target,
        "transcript": rich["text"],
        "diff": diff,
        "accuracy": diff["accuracy"],
        "fluency_score": fluency,
        "metrics": attempt_metrics,
    }


@app.get("/api/shadowing/progress")
def get_shadowing_progress(profile_id: int | None = None):
    pid = _resolve_profile(profile_id)
    return db.shadowing_progress(pid)


# --- Pronunciation lab ------------------------------------------------------------


@app.post("/api/pronunciation/pair-attempt")
async def pair_attempt(
    audio: UploadFile = File(...),
    pair_set_id: str = Form(...),
    target_word: str = Form(...),
    profile_id: int | None = Form(None),
):
    config = load_config()
    pid = _resolve_profile(profile_id)
    pair_set = pronunciation_content.find_pair_set(pair_set_id)
    if not pair_set:
        raise AppError("Minimal pair set not found.", code="not_found", status_code=404)

    counterpart = None
    for a, b in pair_set["pairs"]:
        if target_word.lower() == a.lower():
            counterpart = b
            break
        if target_word.lower() == b.lower():
            counterpart = a
            break
    if counterpart is None:
        raise AppError("Word is not part of this pair set.", code="bad_word")

    rich = await _transcribe_upload(audio, config["whisper_model"])
    heard_words = alignment.normalize_words(rich["text"])

    target_norm = alignment.normalize_words(target_word)
    counter_norm = alignment.normalize_words(counterpart)
    said_target = any(w in heard_words for w in target_norm)
    said_counter = any(w in heard_words for w in counter_norm)

    if said_target and not said_counter:
        verdict, correct = "correct", True
        heard = target_word
    elif said_counter and not said_target:
        verdict, correct = "incorrect", False
        heard = counterpart
    elif said_target and said_counter:
        verdict, correct = "unclear", None
        heard = rich["text"]
    else:
        verdict, correct = "unclear", None
        heard = rich["text"] or None

    db.insert_pair_attempt(pid, pair_set_id, f"{pair_set['contrast']} ({pair_set['label']})",
                           target_word, heard, correct)
    if correct is not None:
        db.insert_activity(pid, "pronunciation_pair", gamification.xp_for("pronunciation_pair"),
                           ref=pair_set_id)

    return {
        "verdict": verdict,
        "target_word": target_word,
        "counterpart": counterpart,
        "heard": heard,
        "transcript": rich["text"],
    }


@app.post("/api/pronunciation/line-attempt")
async def line_attempt(
    audio: UploadFile = File(...),
    lesson_id: str = Form(...),
    line_index: int = Form(...),
    profile_id: int | None = Form(None),
):
    config = load_config()
    pid = _resolve_profile(profile_id)
    lesson = pronunciation_content.find_lesson(lesson_id)
    if not lesson:
        raise AppError("Lesson not found.", code="not_found", status_code=404)
    if not 0 <= line_index < len(lesson["practice_lines"]):
        raise AppError("Line index out of range.", code="bad_index")

    target = lesson["practice_lines"][line_index]["text"]
    rich = await _transcribe_upload(audio, config["whisper_model"])
    attempt_metrics = metrics_mod.compute_metrics(rich["words"], rich["duration"])
    diff = alignment.align(target, rich["text"])
    fluency = alignment.fluency_score(attempt_metrics, len(diff["target_words"]))

    db.insert_shadowing_attempt(
        pid, f"lesson:{lesson_id}", line_index, target, rich["text"],
        diff["accuracy"], fluency, diff, attempt_metrics,
    )
    db.insert_activity(pid, "pronunciation_line", gamification.xp_for("pronunciation_line"),
                       ref=f"{lesson_id}:{line_index}")

    return {
        "target": target,
        "transcript": rich["text"],
        "diff": diff,
        "accuracy": diff["accuracy"],
        "fluency_score": fluency,
        "metrics": attempt_metrics,
    }


@app.get("/api/pronunciation/stats")
def pronunciation_stats(profile_id: int | None = None):
    pid = _resolve_profile(profile_id)
    return db.pair_contrast_stats(pid)


# --- Listening -----------------------------------------------------------------


@app.post("/api/listening/submit")
def listening_submit(payload: dict):
    item_id = payload.get("item_id")
    answers = payload.get("answers") or []
    pid = _resolve_profile(payload.get("profile_id"))
    result = listening_content.grade(item_id, answers)
    if result is None:
        raise AppError("Listening item not found.", code="not_found", status_code=404)
    db.insert_listening_result(pid, item_id, result["score"], result["total"], answers)
    bonus = result["score"] * 2
    db.insert_activity(pid, "listening_quiz", gamification.xp_for("listening_quiz", bonus), ref=item_id)
    return result


@app.get("/api/listening/history")
def get_listening_history(profile_id: int | None = None):
    pid = _resolve_profile(profile_id)
    return db.listening_history(pid)


# --- TOEFL Reading ---------------------------------------------------------------


@app.post("/api/reading/submit")
def reading_submit(payload: dict):
    set_id = payload.get("set_id")
    answers = payload.get("answers") or []
    pid = _resolve_profile(payload.get("profile_id"))
    result = content.grade_toefl_reading(set_id, answers)
    if result is None:
        raise AppError("Reading set not found.", code="not_found", status_code=404)
    db.insert_reading_result(pid, set_id, result["task_type"], result["score"], result["total"], answers)
    bonus = result["score"] * 2
    db.insert_activity(pid, "reading_practice", gamification.xp_for("reading_practice", bonus), ref=set_id)
    return result


@app.get("/api/reading/history")
def get_reading_history(profile_id: int | None = None):
    pid = _resolve_profile(profile_id)
    return db.reading_history(pid)


# --- History & analytics -----------------------------------------------------


@app.get("/api/sessions")
def sessions(mode: str | None = None, limit: int = 100, profile_id: int | None = None):
    return db.list_sessions(mode=mode, limit=limit, profile_id=_resolve_profile(profile_id))


@app.get("/api/sessions/{session_id}")
def session_detail(session_id: int):
    row = db.get_session(session_id)
    if not row:
        raise AppError("Session not found.", code="not_found", status_code=404)
    if row.get("prompt_ref"):
        row["other_attempts"] = db.sessions_for_prompt(row["prompt_ref"], row.get("profile_id"))
    return row


@app.get("/api/stats/toefl")
def toefl_stats(profile_id: int | None = None):
    return db.toefl_score_trend(_resolve_profile(profile_id))


@app.get("/api/stats/dashboard")
def dashboard_stats(profile_id: int | None = None):
    return stats.dashboard(_resolve_profile(profile_id))


@app.get("/api/coach/recommendations")
def coach_recommendations(profile_id: int | None = None):
    return coach.recommendations(_resolve_profile(profile_id))

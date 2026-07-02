import tempfile
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import content
import db
import llm_service
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


@app.exception_handler(AppError)
def handle_app_error(_request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})


# --- Settings ----------------------------------------------------------------


@app.get("/api/settings")
def get_settings():
    return load_config()


@app.post("/api/settings")
def update_settings(payload: dict):
    allowed = {"base_url", "api_key", "model", "whisper_model"}
    update = {k: v for k, v in payload.items() if k in allowed}
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
    return {"tasks": content.get_toefl_tasks(), "timing": content.get_toefl_timing()}


# --- Helpers ---------------------------------------------------------------


async def _save_upload(audio: UploadFile) -> str:
    suffix = Path(audio.filename or "audio.webm").suffix or ".webm"
    data = await audio.read()
    if not data:
        raise AppError("No audio data received. Please record an answer before submitting.", code="empty_audio")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(data)
    finally:
        tmp.close()
    return tmp.name


# --- General practice --------------------------------------------------------


@app.post("/api/practice/general/attempt")
async def general_attempt(
    audio: UploadFile = File(...),
    topic_id: str = Form(...),
    topic_prompt: str = Form(...),
):
    config = load_config()
    tmp_path = await _save_upload(audio)
    try:
        transcript = whisper_service.transcribe(tmp_path, config["whisper_model"])
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if not transcript.strip():
        raise AppError(
            "No speech was detected in the recording. Please try again and speak clearly into the microphone.",
            code="empty_transcript",
        )

    feedback = llm_service.get_general_feedback(config, topic_prompt, transcript)

    session_id = db.insert_session(
        mode="general",
        task_type=topic_id,
        task_title=topic_prompt,
        task_prompt=topic_prompt,
        transcript=transcript,
        feedback=feedback,
        score_band=None,
    )

    return {"session_id": session_id, "transcript": transcript, "feedback": feedback}


# --- TOEFL practice (2026 format: Listen and Repeat + Take an Interview) ----------


@app.post("/api/practice/toefl/attempt")
async def toefl_attempt(
    audio: List[UploadFile] = File(...),
    task_type: str = Form(...),
    prompt_id: str = Form(...),
):
    config = load_config()
    if task_type not in ("listen_repeat", "interview"):
        raise AppError(f"Unknown TOEFL task type: {task_type}", code="bad_task_type")

    prompt_item = content.find_toefl_prompt(task_type, prompt_id)
    if not prompt_item:
        raise AppError("Unknown TOEFL prompt id.", code="bad_prompt_id")

    items = prompt_item["sentences"] if task_type == "listen_repeat" else prompt_item["questions"]
    if len(audio) != len(items):
        raise AppError(
            f"Expected {len(items)} recordings for this set but received {len(audio)}.",
            code="item_count_mismatch",
        )

    transcripts = []
    for file in audio:
        tmp_path = await _save_upload(file)
        try:
            transcripts.append(whisper_service.transcribe(tmp_path, config["whisper_model"]))
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    if not any(t.strip() for t in transcripts):
        raise AppError(
            "No speech was detected in any of the recordings. Please try again and speak clearly into the microphone.",
            code="empty_transcript",
        )

    if task_type == "listen_repeat":
        feedback = llm_service.get_listen_repeat_feedback(config, prompt_item["title"], items, transcripts)
    else:
        feedback = llm_service.get_interview_feedback(config, prompt_item["title"], items, transcripts)

    combined_transcript = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(transcripts))
    session_id = db.insert_session(
        mode="toefl",
        task_type=task_type,
        task_title=prompt_item["title"],
        task_prompt="; ".join(items),
        transcript=combined_transcript,
        feedback=feedback,
        score_band=feedback.get("score_band"),
    )

    return {"session_id": session_id, "transcript": combined_transcript, "feedback": feedback}


# --- History ---------------------------------------------------------------


@app.get("/api/sessions")
def sessions(mode: str | None = None, limit: int = 100):
    return db.list_sessions(mode=mode, limit=limit)


@app.get("/api/sessions/{session_id}")
def session_detail(session_id: int):
    row = db.get_session(session_id)
    if not row:
        raise AppError("Session not found.", code="not_found", status_code=404)
    return row


@app.get("/api/stats/toefl")
def toefl_stats():
    return db.toefl_score_trend()

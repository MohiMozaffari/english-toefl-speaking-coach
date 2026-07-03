"""Local speech-to-text using faster-whisper. Runs fully offline on CPU."""

import threading

from errors import AppError

_model_cache = {}
_cache_lock = threading.Lock()

PIP_INSTALL_HINT = "pip install faster-whisper"

VALID_SIZES = {"tiny", "base", "small"}

# Below this, faster-whisper occasionally throws on genuinely tiny/degenerate
# audio buffers (a few frames of a mic blip, a corrupted near-empty webm chunk).
# transcribe_rich() never lets that propagate as a 500; callers use the
# "failed"/"duration" fields to decide whether to treat it as "too short"
# rather than attempting to show real feedback on nothing.
MIN_USABLE_AUDIO_SECONDS = 7.0


def _get_model(size: str):
    if size not in VALID_SIZES:
        size = "small"

    with _cache_lock:
        if size in _model_cache:
            return _model_cache[size]

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise AppError(
                f"faster-whisper is not installed. Run: {PIP_INSTALL_HINT}",
                code="whisper_not_installed",
                status_code=500,
            ) from exc

        try:
            model = WhisperModel(size, device="cpu", compute_type="int8")
        except Exception as exc:  # noqa: BLE001
            raise AppError(
                f"Failed to load faster-whisper model '{size}': {exc}",
                code="whisper_load_failed",
                status_code=500,
            ) from exc

        _model_cache[size] = model
        return model


def is_installed() -> bool:
    try:
        import faster_whisper  # noqa: F401

        return True
    except ImportError:
        return False


def transcribe_rich(file_path: str, whisper_model_size: str) -> dict:
    """Transcribe with word-level timestamps and confidences.

    Returns {"text", "words", "duration", "failed"}. "words" feeds metrics.py
    (speaking rate, pauses, confidence proxy).

    Never raises for a failed transcription attempt itself -- very short or
    degenerate audio can trip up the STT engine, and a hard 500 there used to
    surface as a raw error instead of a gradeable (if very low) result. Callers
    use "failed" + "duration" to decide between a "too short" penalty and a
    genuine "no speech detected" outcome. Model load/install problems (a real
    setup issue, not a per-recording one) still raise AppError as before.
    """
    model = _get_model(whisper_model_size)
    try:
        segments, info = model.transcribe(
            file_path, beam_size=5, vad_filter=True, word_timestamps=True
        )
        words = []
        parts = []
        for seg in segments:
            parts.append(seg.text.strip())
            for w in seg.words or []:
                words.append(
                    {
                        "word": w.word.strip(),
                        "start": round(w.start, 3),
                        "end": round(w.end, 3),
                        "probability": round(w.probability, 4),
                    }
                )
        text = " ".join(p for p in parts if p).strip()
        duration = float(getattr(info, "duration", 0.0) or 0.0)
    except Exception:  # noqa: BLE001
        return {"text": "", "words": [], "duration": 0.0, "failed": True}
    return {"text": text, "words": words, "duration": duration, "failed": False}


def transcribe(file_path: str, whisper_model_size: str) -> str:
    return transcribe_rich(file_path, whisper_model_size)["text"]


def classify_transcription(rich: dict, min_duration: float = MIN_USABLE_AUDIO_SECONDS) -> str:
    """Sort a transcription result into "ok" | "too_short" | "no_speech".

    - "too_short": the STT engine failed outright, or the clip was both brief
      AND produced no recognizable words -- treat as unusable input, not a
      scoreable silent answer (a legitimate quick-but-correct answer to a short
      prompt still has real words and is NOT flagged here, even if brief).
    - "no_speech": a normal-length clip that came back completely empty --
      genuine silence.
    - "ok": anything with real transcribed words.
    """
    if rich.get("failed"):
        return "too_short"
    has_text = bool(rich["text"].strip())
    if not has_text and rich["duration"] < min_duration:
        return "too_short"
    if not has_text:
        return "no_speech"
    return "ok"

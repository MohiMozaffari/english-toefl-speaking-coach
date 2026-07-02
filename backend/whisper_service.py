"""Local speech-to-text using faster-whisper. Runs fully offline on CPU."""

import threading

from errors import AppError

_model_cache = {}
_cache_lock = threading.Lock()

PIP_INSTALL_HINT = "pip install faster-whisper"

VALID_SIZES = {"tiny", "base", "small"}


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


def transcribe(file_path: str, whisper_model_size: str) -> str:
    model = _get_model(whisper_model_size)
    try:
        segments, _info = model.transcribe(file_path, beam_size=5, vad_filter=True)
        text = " ".join(seg.text.strip() for seg in segments).strip()
    except Exception as exc:  # noqa: BLE001
        raise AppError(
            f"Transcription failed: {exc}",
            code="transcription_failed",
            status_code=500,
        ) from exc
    return text

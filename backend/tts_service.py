"""Multi-accent neural TTS for Shadowing mode, via edge-tts (Microsoft Edge's
online neural voices).

This is the one deliberate exception to the app's "fully local" design: edge-tts
calls Microsoft's cloud TTS service over the network on cache misses. Everything
else in the app (transcription, scoring, the AI coach, General/TOEFL feedback
playback) stays on faster-whisper + the browser's built-in speechSynthesis, which
work fully offline. Shadowing mode specifically wants "highly realistic" neural
voices with accent variety, which speechSynthesis's local voice bank can't
reliably provide across platforms -- so the frontend calls this endpoint for
shadowing playback and falls back to speechSynthesis if it's unreachable
(offline, or Microsoft's endpoint is blocked on this network).

Generated audio is cached to disk by (voice, text) so repeat playback of the same
sentence never re-hits the network.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import edge_tts

from errors import AppError

CACHE_DIR = Path(__file__).parent / "data" / "tts_cache"

VOICES_BY_ACCENT: dict[str, list[str]] = {
    "en-US": ["en-US-AriaNeural", "en-US-GuyNeural", "en-US-JennyNeural", "en-US-ChristopherNeural"],
    "en-GB": ["en-GB-SoniaNeural", "en-GB-RyanNeural"],
    "en-AU": ["en-AU-NatashaNeural", "en-AU-WilliamNeural"],
}

DEFAULT_ACCENT = "en-US"


def list_accents() -> list[str]:
    return list(VOICES_BY_ACCENT.keys())


def next_voice(accent: str, text: str) -> str:
    """Pick a neural voice for this accent, distributed across the accent's voice
    pool by hashing the text -- NOT a stateful round-robin. Determinism matters
    here: the same sentence must always resolve to the same voice, or every
    replay of "the same sentence" would (a) sound like a different speaker and
    (b) miss the cache and re-hit the network on every single playback. Hashing
    the text still spreads *different* sentences across the whole voice pool,
    which is the actual point of "rotation" -- variety across content, not
    randomness on repeat."""
    voices = VOICES_BY_ACCENT.get(accent) or VOICES_BY_ACCENT[DEFAULT_ACCENT]
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return voices[int(digest, 16) % len(voices)]


def _cache_path(voice: str, text: str) -> Path:
    digest = hashlib.sha256(f"{voice}:{text}".encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{digest}.mp3"


async def synthesize(text: str, accent: str = DEFAULT_ACCENT, voice: str | None = None) -> dict:
    """Generate (or fetch from cache) neural speech audio for one sentence.

    Returns {"audio_path": Path, "voice": str, "cached": bool}. Raises AppError
    with a clear, user-facing message if Microsoft's TTS service can't be reached.
    """
    if not text or not text.strip():
        raise AppError("No text provided to synthesize.", code="tts_empty_text")

    chosen_voice = voice or next_voice(accent, text)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(chosen_voice, text)

    if path.exists() and path.stat().st_size > 0:
        return {"audio_path": path, "voice": chosen_voice, "cached": True}

    try:
        communicate = edge_tts.Communicate(text, chosen_voice)
        await communicate.save(str(path))
    except Exception as exc:  # noqa: BLE001
        path.unlink(missing_ok=True)
        raise AppError(
            "Could not reach the neural voice service (edge-tts needs internet access to Microsoft's "
            "TTS endpoint). Falling back to your browser's built-in voice is recommended.",
            code="tts_unreachable",
            status_code=503,
        ) from exc

    if not path.exists() or path.stat().st_size == 0:
        path.unlink(missing_ok=True)
        raise AppError("The neural voice service returned no audio. Please try again.", code="tts_empty_result", status_code=502)

    return {"audio_path": path, "voice": chosen_voice, "cached": False}

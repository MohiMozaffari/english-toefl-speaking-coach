"""Talks to FreeLLMAPI's OpenAI-compatible endpoint. Never logs the API key."""

import json
import re

from openai import (
    APIConnectionError,
    AuthenticationError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)

from errors import AppError

GENERAL_SYSTEM_PROMPT = """You are an encouraging, friendly English speaking coach for a learner around \
A2-B1 CEFR level. You will be given a conversation topic/question and a transcript of the learner's \
spoken answer (produced by speech-to-text, so it may contain minor transcription errors — do not \
penalize obvious transcription artifacts). Give feedback in simple, plain, encouraging language that \
a learner at this level can easily understand.

Respond with ONLY valid JSON (no markdown code fences, no commentary before or after) matching \
EXACTLY this schema:
{
  "encouragement": "one warm, encouraging sentence about their effort",
  "what_went_well": "1-2 sentences naming the strongest things they did in THIS answer",
  "grammar_feedback": "2-4 simple sentences about grammar issues you noticed, if any",
  "vocabulary_feedback": "2-4 simple sentences about their vocabulary use and suggestions",
  "clarity_feedback": "2-4 simple sentences about how clear and organized their answer was",
  "improved_version": "a natural, correct rewritten version of roughly what they said, similar length",
  "overall_tip": "one specific, actionable tip for next time",
  "category_scores": {"fluency": 4, "accuracy": 4, "coherence": 4}
}
"category_scores" values are integers 1-6 (6 = native-like) rating this answer's fluency (flow/pace), \
accuracy (grammar+vocabulary correctness), and coherence (organization and relevance)."""

# Reflects the redesigned TOEFL iBT Speaking section (launched January 21, 2026): two tasks,
# automatically scored 1-6, no prep time. Listen and Repeat measures how closely the test-taker
# reproduces each sentence; Take an Interview measures fluency/accuracy/coherence on open answers.

LISTEN_REPEAT_SYSTEM_PROMPT = """You are an automated TOEFL iBT Speaking rater for the "Listen and \
Repeat" task (2026 redesigned format). The test-taker heard each target sentence once and had to repeat \
it back exactly, with no preparation time. You will receive the list of target sentences in order, each \
paired with a transcript of what the test-taker actually said (produced by speech-to-text, so minor \
transcription artifacts like missing punctuation are normal and should not be penalized — focus on \
actual word substitutions, omissions, or major restructuring).

Score using the official 1-6 automated scale, evaluating: Accuracy (how closely the wording matches \
the target sentence), Fluency (natural pacing/rhythm inferred from transcript smoothness and hesitation \
markers), and Pronunciation/Delivery (inferred proxy from transcript quality — garbled or nonsensical \
transcription segments suggest pronunciation trouble).

Respond with ONLY valid JSON (no markdown code fences, no commentary before or after) matching EXACTLY \
this schema:
{
  "score_band": 1,
  "score_reason": "one-line reason for the overall score",
  "what_went_well": "1-2 sentences naming the strongest parts of this attempt",
  "biggest_weakness": "the single most score-limiting problem, and WHY it costs points on this task",
  "accuracy": "1-2 sentences evaluating how closely wording matched the targets",
  "fluency": "1-2 sentences evaluating pacing and rhythm",
  "pronunciation_delivery": "1-2 sentences evaluating likely pronunciation/delivery based on the transcripts",
  "items": [
    {"target": "the exact target sentence", "said": "what the transcript shows they said", "match_quality": "exact, close, or different", "tip": "one short specific tip for this sentence"}
  ],
  "how_to_improve": "2-3 concrete practice steps, phrased as instructions",
  "suggested_exercises": ["1-3 short exercise suggestions, e.g. 'Shadow 5 sentences daily at 0.75x speed'"],
  "focus_next": "one clear, specific thing to focus on next time",
  "category_scores": {"fluency": 4, "accuracy": 4, "pronunciation": 4}
}
"score_band" must be an integer from 1 to 6. "category_scores" values are integers 1-6. "items" must \
contain exactly one entry per target sentence, in the same order given."""

INTERVIEW_SYSTEM_PROMPT = """You are an automated TOEFL iBT Speaking rater for the "Take an Interview" \
task (2026 redesigned format). The test-taker was asked 4 questions in a row about one familiar topic, \
with no preparation time, and had 45 seconds to answer each. You will receive the 4 questions in order, \
each paired with a transcript of the test-taker's spoken answer (produced by speech-to-text, so minor \
transcription errors may exist — do not penalize obvious transcription artifacts, but silence, filler \
words, or very short/incomplete answers should be scored honestly as a rater would).

Score using the official 1-6 automated scale, evaluating: Fluency (natural pacing, rhythm, minimal \
hesitation), Accuracy (grammar and vocabulary correctness and range), and Coherence (organized, relevant, \
complete answers to each question).

Respond with ONLY valid JSON (no markdown code fences, no commentary before or after) matching EXACTLY \
this schema:
{
  "score_band": 1,
  "score_reason": "one-line reason for the overall score",
  "what_went_well": "1-2 sentences naming the strongest parts of this attempt",
  "biggest_weakness": "the single most score-limiting problem, and WHY it costs points on this task",
  "fluency": "1-2 sentences evaluating fluency",
  "accuracy": "1-2 sentences evaluating grammar and vocabulary",
  "coherence": "1-2 sentences evaluating organization and relevance",
  "items": [
    {"question": "the interview question", "said": "what the transcript shows they said", "better_response": "a stronger sample answer to this specific question, sized for about 45 seconds", "why": "brief reason this is stronger"}
  ],
  "how_to_improve": "2-3 concrete practice steps, phrased as instructions",
  "suggested_exercises": ["1-3 short exercise suggestions, e.g. 'Answer one Interview set daily without pausing longer than 2 seconds'"],
  "focus_next": "one clear, specific thing to focus on next time",
  "category_scores": {"fluency": 4, "accuracy": 4, "coherence": 4}
}
"score_band" must be an integer from 1 to 6. "category_scores" values are integers 1-6. "items" must \
contain exactly one entry per question, in the same order given."""


def _client(config: dict, timeout: float = 90.0) -> OpenAI:
    api_key = config.get("api_key") or "no-key-set"
    base_url = config.get("base_url") or "http://localhost:3001/v1"
    return OpenAI(api_key=api_key, base_url=base_url, timeout=timeout, max_retries=0)


# Short timeout for reachability checks so the UI never hangs waiting on a health probe
# (the long timeout is reserved for actual feedback-generation calls, which can be slow).
HEALTH_CHECK_TIMEOUT = 4.0


def check_connection(config: dict) -> dict:
    """Best-effort reachability + key validity check. Never raises."""
    if not config.get("api_key"):
        return {"reachable": None, "key_valid": False, "message": "No FreeLLMAPI key set yet."}
    client = _client(config, timeout=HEALTH_CHECK_TIMEOUT)
    try:
        client.models.list()
        return {"reachable": True, "key_valid": True, "message": "Connected to FreeLLMAPI."}
    except AuthenticationError:
        return {
            "reachable": True,
            "key_valid": False,
            "message": "FreeLLMAPI is reachable but the unified key was rejected. Check the Keys page at http://localhost:3001.",
        }
    except APIConnectionError:
        return {
            "reachable": False,
            "key_valid": None,
            "message": "Could not reach FreeLLMAPI at the configured base URL. Run 'docker compose up -d' in your freellmapi folder.",
        }
    except OpenAIError as exc:  # noqa: BLE001
        return {"reachable": False, "key_valid": None, "message": f"FreeLLMAPI error: {exc}"}


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text.strip(), flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text.strip()).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise AppError(
                "The AI returned a response that wasn't valid JSON. Please try again.",
                code="llm_bad_json",
                status_code=502,
            ) from exc
    raise AppError(
        "The AI returned a response that wasn't valid JSON. Please try again.",
        code="llm_bad_json",
        status_code=502,
    )


def _chat(config: dict, system_prompt: str, user_prompt: str) -> str:
    client = _client(config)
    model = config.get("model") or "auto"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    try:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.4,
                response_format={"type": "json_object"},
            )
        except OpenAIError:
            # Router/model may not support response_format — retry without it.
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.4,
            )
    except AuthenticationError as exc:
        raise AppError(
            "Your FreeLLMAPI unified key is missing or invalid. Paste a valid key on the Settings page "
            "(get one from the Keys page at http://localhost:3001).",
            code="llm_auth",
            status_code=401,
        ) from exc
    except APIConnectionError as exc:
        raise AppError(
            "Could not reach FreeLLMAPI at the configured base URL. Make sure it's running: "
            "run 'docker compose up -d' in your freellmapi folder.",
            code="llm_unreachable",
            status_code=503,
        ) from exc
    except RateLimitError as exc:
        raise AppError(
            "FreeLLMAPI reported a rate limit. Wait a moment and try again, or pick a different model in Settings.",
            code="llm_rate_limited",
            status_code=429,
        ) from exc
    except OpenAIError as exc:
        raise AppError(f"FreeLLMAPI request failed: {exc}", code="llm_error", status_code=502) from exc

    if not resp.choices:
        raise AppError("The AI returned an empty response. Please try again.", code="llm_empty", status_code=502)
    content = resp.choices[0].message.content or ""
    if not content.strip():
        raise AppError("The AI returned an empty response. Please try again.", code="llm_empty", status_code=502)
    return content


def _with_context(system_prompt: str, learner_context: str) -> str:
    if learner_context:
        return f"{system_prompt}\n\n{learner_context}"
    return system_prompt


def get_general_feedback(config: dict, topic: str, transcript: str, learner_context: str = "") -> dict:
    user_prompt = f"Topic given to the learner:\n{topic}\n\nTranscript of the learner's spoken answer:\n{transcript}"
    raw = _chat(config, _with_context(GENERAL_SYSTEM_PROMPT, learner_context), user_prompt)
    return _clamp_categories(_extract_json(raw))


def get_listen_repeat_feedback(
    config: dict, set_title: str, sentences: list, transcripts: list, learner_context: str = ""
) -> dict:
    pairs = "\n".join(
        f"{i + 1}. Target: \"{s}\"\n   Test-taker said: \"{t}\"" for i, (s, t) in enumerate(zip(sentences, transcripts))
    )
    user_prompt = f"Listen and Repeat set: {set_title}\n\n{pairs}"
    raw = _chat(config, _with_context(LISTEN_REPEAT_SYSTEM_PROMPT, learner_context), user_prompt)
    return _clamp_categories(_clamp_score(_extract_json(raw)))


def get_interview_feedback(
    config: dict, set_title: str, questions: list, transcripts: list, learner_context: str = ""
) -> dict:
    pairs = "\n".join(
        f"{i + 1}. Question: \"{q}\"\n   Test-taker said: \"{t}\"" for i, (q, t) in enumerate(zip(questions, transcripts))
    )
    user_prompt = f"Take an Interview set: {set_title}\n\n{pairs}"
    raw = _chat(config, _with_context(INTERVIEW_SYSTEM_PROMPT, learner_context), user_prompt)
    return _clamp_categories(_clamp_score(_extract_json(raw)))


def _clamp_score(data: dict) -> dict:
    try:
        data["score_band"] = max(1, min(6, int(data.get("score_band", 1))))
    except (TypeError, ValueError):
        data["score_band"] = 1
    return data


def _clamp_categories(data: dict) -> dict:
    scores = data.get("category_scores")
    if isinstance(scores, dict):
        cleaned = {}
        for key, value in scores.items():
            try:
                cleaned[key] = max(1, min(6, int(value)))
            except (TypeError, ValueError):
                continue
        data["category_scores"] = cleaned
    else:
        data["category_scores"] = {}
    return data


# --- Graceful fallbacks for unusable audio (no LLM call) ---------------------
# Schema-compatible with the real feedback shapes above so the existing result
# UI renders them without special-casing. "status"/"message" mark why. TOEFL's
# score_band stays 1 (the real floor of this app's 1-6 scale) rather than an
# out-of-range 0 -- the score charts, badges, and DB column all assume 1-6.


def general_fallback_feedback(status: str) -> dict:
    message = "No speech detected" if status == "no_speech" else "Response too short"
    reason = (
        "No speech was detected in the recording."
        if status == "no_speech"
        else "The recording was too short to evaluate."
    )
    return {
        "status": status,
        "message": message,
        "encouragement": "No worries — let's try that again.",
        "what_went_well": "",
        "grammar_feedback": reason,
        "vocabulary_feedback": "",
        "clarity_feedback": "",
        "improved_version": "",
        "overall_tip": "Check that your microphone is working, then speak as soon as the recording starts.",
        "category_scores": {},
    }


def toefl_fallback_feedback(status: str, task_type: str, items: list[str]) -> dict:
    message = "No speech detected" if status == "no_speech" else "Response too short"
    reason = (
        "No speech was detected in your response."
        if status == "no_speech"
        else "The recording was too short to evaluate."
    )
    third_category = "pronunciation" if task_type == "listen_repeat" else "coherence"
    data = {
        "status": status,
        "message": message,
        "score_band": 1,
        "score_reason": reason,
        "what_went_well": "",
        "biggest_weakness": f"{message} — there was nothing to score.",
        "fluency": message,
        "accuracy": message,
        "how_to_improve": "Make sure your microphone is working, then try again and speak for the full response time.",
        "suggested_exercises": [
            "Test your microphone in Settings before starting a task.",
            "Try a Shadowing sentence first to confirm your mic is picking up your voice.",
        ],
        "focus_next": "Confirm your microphone is working, then retry this set.",
        "category_scores": {"fluency": 1, "accuracy": 1, third_category: 1},
    }
    if task_type == "listen_repeat":
        data["pronunciation_delivery"] = message
        data["items"] = [{"target": t, "said": "", "match_quality": "different", "tip": message} for t in items]
    else:
        data["coherence"] = message
        data["items"] = [{"question": q, "said": "", "better_response": "", "why": message} for q in items]
    return data

import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { useCountdown } from "../hooks/useCountdown";
import { useRecorder } from "../hooks/useRecorder";
import { playNeural, speak, stopSpeaking } from "../speech";
import { MetricChips, PageHeader, ReplayButton, ScoreBadge, scoreBadgeClass } from "../components/ui";
import type { InterviewItem, ListenRepeatItem, ToeflAttemptResponse, ToeflSet, ToeflTopics } from "../types";

const TASK_LABELS: Record<string, string> = {
  listen_repeat: "Listen and Repeat",
  interview: "Take an Interview",
};

const TASK_DESCRIPTIONS: Record<string, string> = {
  listen_repeat:
    "You'll hear 7 short sentences, one at a time, tied to a picture. Repeat each one back exactly as you heard it — no prep time, 8-12 seconds to respond per sentence.",
  interview:
    "You'll be asked 4 questions in a row about one familiar topic, like a simulated interview. No prep time — 45 seconds to answer each question.",
};

type Stage = "select_task" | "select_prompt" | "running" | "processing" | "result" | "error";
type TaskType = "listen_repeat" | "interview";

export default function ToeflPractice() {
  const [tasksData, setTasksData] = useState<ToeflTopics | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [taskType, setTaskType] = useState<TaskType | null>(null);
  const [promptSet, setPromptSet] = useState<ToeflSet | null>(null);
  const [stage, setStage] = useState<Stage>("select_task");
  const [phase, setPhase] = useState<"listening" | "recording">("listening");
  const [itemIndex, setItemIndex] = useState(0);
  const [result, setResult] = useState<ToeflAttemptResponse | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const recorder = useRecorder();
  const countdown = useCountdown();
  const stopEarlyRef = useRef<(() => void) | null>(null);
  const runIdRef = useRef(0);
  const playbackRef = useRef<{ stop: () => void } | null>(null);

  const stopPrompt = () => {
    playbackRef.current?.stop();
    stopSpeaking();
  };

  useEffect(() => {
    api.getToeflTopics().then(setTasksData).catch((err) => setLoadError(err.message));
    return () => stopPrompt();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const chooseTaskType = (tt: TaskType) => {
    setTaskType(tt);
    setPromptSet(null);
    setResult(null);
    setSubmitError(null);
    setStage("select_prompt");
  };

  const recordItem = (durationSec: number): Promise<Blob | null> =>
    new Promise((resolve) => {
      const finish = async () => {
        countdown.stop();
        const blob = await recorder.stop();
        resolve(blob);
      };
      stopEarlyRef.current = finish;
      countdown.start(durationSec, finish);
    });

  const runSet = async (set: ToeflSet) => {
    if (!tasksData || !taskType) return;
    const runId = ++runIdRef.current;
    setPromptSet(set);
    setResult(null);
    setSubmitError(null);
    const texts = "sentences" in set ? set.sentences : set.questions;
    const durations = tasksData.timing[taskType].item_seconds;
    const blobs: Blob[] = [];

    setStage("running");
    for (let i = 0; i < texts.length; i++) {
      if (runIdRef.current !== runId) return; // superseded by a newer run
      setItemIndex(i);
      setPhase("listening");
      // Play the exam prompt in the same realistic neural voice as Shadowing
      // (edge-tts), falling back to the browser voice if it's unreachable.
      // Real TOEFL iBT is American English.
      await new Promise<void>((resolve) => {
        playbackRef.current = playNeural(texts[i], { accent: "en-US", onEnd: resolve });
      });

      if (runIdRef.current !== runId) return;
      setPhase("recording");
      const ok = await recorder.start();
      if (!ok) {
        setSubmitError(recorder.error || "Could not access the microphone.");
        setStage("error");
        return;
      }
      const blob = await recordItem(durations[i]);
      // Always push one entry per item, even if the recorder produced nothing
      // (e.g. it was already inactive at timer-expiry). An empty Blob still
      // counts toward the set size the backend expects; the alternative --
      // silently dropping the item -- shrinks the array by one and makes the
      // *entire* submission get rejected for a count mismatch, losing every
      // other item's real audio along with it. The backend classifies an empty
      // item as "too short" for just that one item instead.
      blobs.push(blob && blob.size > 0 ? blob : new Blob([], { type: "audio/webm" }));
    }

    if (runIdRef.current !== runId) return;
    setStage("processing");
    try {
      const formData = new FormData();
      blobs.forEach((b, i) => formData.append("audio", b, `item_${i}.webm`));
      formData.append("task_type", taskType);
      formData.append("prompt_id", set.id);
      const data = await api.submitToeflAttempt(formData);
      setResult(data);
      setStage("result");
      speak(`${data.feedback.score_reason} ${data.feedback.focus_next}`);
    } catch (err) {
      setSubmitError((err as Error).message);
      setStage("error");
    }
  };

  const reset = () => {
    runIdRef.current += 1;
    stopPrompt();
    setTaskType(null);
    setPromptSet(null);
    setStage("select_task");
    setResult(null);
    setSubmitError(null);
  };

  const backToPrompts = () => {
    runIdRef.current += 1;
    stopPrompt();
    setPromptSet(null);
    setResult(null);
    setSubmitError(null);
    setStage("select_prompt");
  };

  if (loadError) return <div className="error-box">Could not load TOEFL content: {loadError}</div>;
  if (!tasksData) return <p className="muted">Loading…</p>;

  const totalItems = promptSet ? ("sentences" in promptSet ? promptSet.sentences : promptSet.questions).length : 0;

  return (
    <div>
      <PageHeader
        title="TOEFL Speaking Practice"
        subtitle="The redesigned TOEFL iBT Speaking section (2026): Listen and Repeat + Take an Interview, no prep time, scored 1-6."
      />

      {stage === "select_task" && (
        <div className="grid cols-2">
          {(Object.keys(TASK_LABELS) as TaskType[]).map((tt) => (
            <button key={tt} type="button" className="topic-item" onClick={() => chooseTaskType(tt)}>
              <div className="cat">{TASK_LABELS[tt]}</div>
              <div className="muted small">{TASK_DESCRIPTIONS[tt]}</div>
            </button>
          ))}
        </div>
      )}

      {stage === "select_prompt" && taskType && (
        <div className="card">
          <div className="flex-between">
            <p className="section-title" style={{ margin: 0 }}>{TASK_LABELS[taskType]}</p>
            <button type="button" onClick={() => setStage("select_task")}>← Change task type</button>
          </div>
          <div className="topic-list" style={{ marginTop: 14 }}>
            {tasksData.tasks[taskType].map((set) => (
              <button key={set.id} type="button" className="topic-item" onClick={() => runSet(set)}>
                <div className="cat">
                  {"sentences" in set ? `${set.sentences.length} sentences` : `${set.questions.length} questions`}
                </div>
                <div>{set.title}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {promptSet && stage === "running" && (
        <div className="card">
          <p className="section-title">
            {TASK_LABELS[taskType!]} — {promptSet.title}
          </p>
          <div className="row" aria-label="Progress">
            {Array.from({ length: totalItems }).map((_, i) => (
              <span
                key={i}
                className={`badge ${i < itemIndex ? "good" : i === itemIndex ? "info" : "neutral"}`}
              >
                {i + 1}
              </span>
            ))}
          </div>

          {"picture_caption" in promptSet && (
            <div className="transcript-box center" style={{ margin: "14px 0" }}>
              📷 {promptSet.picture_caption}
            </div>
          )}

          {recorder.error && <div className="error-box">{recorder.error}</div>}

          {phase === "listening" && (
            <div className="center" style={{ margin: "26px 0" }}>
              <div style={{ fontSize: "1.6rem" }}>🔊</div>
              <p className="muted">Listen carefully…</p>
            </div>
          )}

          {phase === "recording" && (
            <div className="center" style={{ margin: "18px 0" }}>
              <div className="timer-display speak">{countdown.secondsLeft}s</div>
              <p className="muted">
                <span className="recording-dot" aria-hidden="true" />
                {taskType === "listen_repeat" ? "Repeat the sentence now." : "Answer the question now."}
              </p>
              <button type="button" className="danger" onClick={() => stopEarlyRef.current?.()}>
                ⏹ Done early
              </button>
            </div>
          )}
        </div>
      )}

      {stage === "processing" && (
        <div className="card center">
          <p className="muted">Transcribing all recordings and scoring your response… this can take a minute on CPU.</p>
        </div>
      )}

      {stage === "error" && (
        <div className="card">
          <div className="error-box">{submitError}</div>
          <button type="button" onClick={backToPrompts}>← Back to prompts</button>
        </div>
      )}

      {stage === "result" && result && promptSet && (
        <ResultView result={result} taskType={taskType!} onRetry={() => runSet(promptSet)} onBack={backToPrompts} onChangeTask={reset} />
      )}
    </div>
  );
}

function ResultView({
  result,
  taskType,
  onRetry,
  onBack,
  onChangeTask,
}: {
  result: ToeflAttemptResponse;
  taskType: TaskType;
  onRetry: () => void;
  onBack: () => void;
  onChangeTask: () => void;
}) {
  const fb = result.feedback;
  const prevAttempts = result.previous_attempts.filter((a) => a.id !== result.session_id);

  return (
    <div className="pop-in">
      <div className="card">
        <div className="flex-between">
          <p className="section-title" style={{ margin: 0 }}>Score: {fb.score_band} / 6</p>
          <ScoreBadge score={fb.score_band} />
        </div>
        <p className="muted">{fb.score_reason}</p>
        <MetricChips metrics={result.metrics} />

        {prevAttempts.length > 0 && (
          <div className="card sub" style={{ marginTop: 14, marginBottom: 0 }}>
            <p className="section-title" style={{ marginBottom: 8 }}>📈 This set over time</p>
            <div className="row">
              {result.previous_attempts.map((a) => (
                <span
                  key={a.id}
                  className={`badge ${a.id === result.session_id ? "info" : scoreBadgeClass(a.score_band)}`}
                  title={new Date(a.created_at).toLocaleString()}
                >
                  {a.id === result.session_id ? `now: ${a.score_band}` : a.score_band}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="grid cols-2">
        <div className="card" style={{ margin: 0 }}>
          <p className="section-title">✅ What went well</p>
          <p className="small" style={{ margin: 0 }}>{fb.what_went_well || "—"}</p>
        </div>
        <div className="card" style={{ margin: 0 }}>
          <p className="section-title">⚠️ Biggest weakness</p>
          <p className="small" style={{ margin: 0 }}>{fb.biggest_weakness || "—"}</p>
        </div>
      </div>

      <div className="card" style={{ marginTop: 14 }}>
        <div className="grid cols-3">
          <div>
            <strong>Fluency</strong>
            <p className="muted small">{fb.fluency}</p>
          </div>
          <div>
            <strong>Accuracy</strong>
            <p className="muted small">{fb.accuracy}</p>
          </div>
          <div>
            <strong>{taskType === "listen_repeat" ? "Pronunciation / Delivery" : "Coherence"}</strong>
            <p className="muted small">{taskType === "listen_repeat" ? fb.pronunciation_delivery : fb.coherence}</p>
          </div>
        </div>
      </div>

      <div className="card">
        <p className="section-title">{taskType === "listen_repeat" ? "Sentence by sentence" : "Question by question"}</p>
        {(fb.items || []).map((item, i) => (
          <div className="correction-row" key={i}>
            {"target" in item ? (
              <>
                <p style={{ margin: "2px 0" }}><strong>Target:</strong> {(item as ListenRepeatItem).target}</p>
                <p style={{ margin: "2px 0" }}><span className="said">You said:</span> {(item as ListenRepeatItem).said}</p>
                <p className="muted small" style={{ margin: "2px 0" }}>
                  {(item as ListenRepeatItem).match_quality} — {(item as ListenRepeatItem).tip}
                </p>
              </>
            ) : (
              <>
                <p style={{ margin: "2px 0" }}><strong>Q:</strong> {(item as InterviewItem).question}</p>
                <p style={{ margin: "2px 0" }}><span className="said">You said:</span> {(item as InterviewItem).said}</p>
                <p style={{ margin: "2px 0" }}>
                  <span className="better">Stronger answer:</span> {(item as InterviewItem).better_response}
                  {"  "}
                  <ReplayButton text={(item as InterviewItem).better_response} label="🔊" />
                </p>
                <p className="muted small" style={{ margin: "2px 0" }}>{(item as InterviewItem).why}</p>
              </>
            )}
          </div>
        ))}
      </div>

      <div className="card sub">
        <p className="section-title">🧗 How to improve</p>
        <p className="small">{fb.how_to_improve || fb.focus_next}</p>
        {fb.suggested_exercises && fb.suggested_exercises.length > 0 && (
          <ul className="small muted" style={{ margin: "6px 0 0", paddingLeft: 18 }}>
            {fb.suggested_exercises.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        )}
        <div className="flex-between" style={{ marginTop: 12 }}>
          <p style={{ margin: 0 }}><strong>🎯 Focus next time:</strong> {fb.focus_next}</p>
          <ReplayButton text={`${fb.score_reason} ${fb.focus_next}`} label="🔊 Hear summary" />
        </div>
      </div>

      <div className="row" style={{ marginTop: 16 }}>
        <button type="button" className="primary" onClick={onRetry}>🔁 Retry this set</button>
        <button type="button" onClick={onBack}>Try another prompt</button>
        <button type="button" onClick={onChangeTask}>Change task type</button>
      </div>
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import { useRecorder } from "../hooks/useRecorder.js";
import { useCountdown } from "../hooks/useCountdown.js";
import { speak } from "../speech.js";
import ReplayButton from "../components/ReplayButton.jsx";

const TASK_LABELS = {
  listen_repeat: "Listen and Repeat",
  interview: "Take an Interview",
};

const TASK_DESCRIPTIONS = {
  listen_repeat:
    "You'll hear 7 short sentences, one at a time, tied to a picture. Repeat each one back exactly as you heard it — no prep time, 8-12 seconds to respond per sentence.",
  interview:
    "You'll be asked 4 questions in a row about one familiar topic, like a simulated interview. No prep time — 45 seconds to answer each question.",
};

function scoreBadgeClass(score) {
  if (score >= 5) return "good";
  if (score === 4) return "warn";
  return "bad";
}

export default function ToeflPractice() {
  const [tasksData, setTasksData] = useState(null);
  const [loadError, setLoadError] = useState(null);

  const [taskType, setTaskType] = useState(null);
  const [promptSet, setPromptSet] = useState(null);
  const [stage, setStage] = useState("select_task"); // select_task | select_prompt | running | processing | result | error
  const [phase, setPhase] = useState("listening"); // listening | recording (while stage === "running")
  const [itemIndex, setItemIndex] = useState(0);
  const [result, setResult] = useState(null);
  const [submitError, setSubmitError] = useState(null);

  const recorder = useRecorder();
  const countdown = useCountdown();
  const stopEarlyRef = useRef(null);
  const runIdRef = useRef(0);

  useEffect(() => {
    api
      .getToeflTopics()
      .then(setTasksData)
      .catch((err) => setLoadError(err.message));
  }, []);

  const chooseTaskType = (tt) => {
    setTaskType(tt);
    setPromptSet(null);
    setResult(null);
    setSubmitError(null);
    setStage("select_prompt");
  };

  const recordItem = (durationSec) =>
    new Promise((resolve) => {
      const finish = async () => {
        countdown.stop();
        const blob = await recorder.stop();
        resolve(blob);
      };
      stopEarlyRef.current = finish;
      countdown.start(durationSec, finish);
    });

  const stopEarly = () => {
    if (stopEarlyRef.current) stopEarlyRef.current();
  };

  const runSet = async (set) => {
    const runId = ++runIdRef.current;
    setPromptSet(set);
    setResult(null);
    setSubmitError(null);
    const texts = taskType === "listen_repeat" ? set.sentences : set.questions;
    const durations = tasksData.timing[taskType].item_seconds;
    const blobs = [];

    setStage("running");
    for (let i = 0; i < texts.length; i++) {
      if (runIdRef.current !== runId) return; // a newer run superseded this one
      setItemIndex(i);
      setPhase("listening");
      await new Promise((resolve) => speak(texts[i], { onEnd: resolve }));

      if (runIdRef.current !== runId) return;
      setPhase("recording");
      const ok = await recorder.start();
      if (!ok) {
        setSubmitError(recorder.error || "Could not access the microphone.");
        setStage("error");
        return;
      }
      const blob = await recordItem(durations[i]);
      blobs.push(blob);
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
      setSubmitError(err.message);
      setStage("error");
    }
  };

  const reset = () => {
    runIdRef.current += 1;
    setTaskType(null);
    setPromptSet(null);
    setStage("select_task");
    setResult(null);
    setSubmitError(null);
  };

  const backToPrompts = () => {
    runIdRef.current += 1;
    setPromptSet(null);
    setResult(null);
    setSubmitError(null);
    setStage("select_prompt");
  };

  if (loadError) {
    return <div className="error-box">Could not load TOEFL content: {loadError}</div>;
  }
  if (!tasksData) {
    return <p className="muted">Loading...</p>;
  }

  const totalItems = promptSet ? (promptSet.sentences || promptSet.questions || []).length : 0;

  return (
    <div>
      <div className="card">
        <p className="section-title">TOEFL Speaking Practice</p>
        <p className="muted">
          The redesigned TOEFL iBT Speaking section (2026): Listen and Repeat + Take an Interview, no prep time.
        </p>
      </div>

      {stage === "select_task" && (
        <div className="card">
          <p className="section-title">Choose a task type</p>
          <div className="grid cols-2">
            {Object.keys(TASK_LABELS).map((tt) => (
              <div key={tt} className="topic-item" onClick={() => chooseTaskType(tt)}>
                <div className="cat">{TASK_LABELS[tt]}</div>
                <div>{TASK_DESCRIPTIONS[tt]}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {stage === "select_prompt" && (
        <div className="card">
          <div className="flex-between">
            <p className="section-title" style={{ margin: 0 }}>
              {TASK_LABELS[taskType]}
            </p>
            <button type="button" onClick={() => setStage("select_task")}>
              ← Change task type
            </button>
          </div>
          <div className="topic-list" style={{ marginTop: 14 }}>
            {tasksData.tasks[taskType].map((set) => (
              <div key={set.id} className="topic-item" onClick={() => runSet(set)}>
                <div className="cat">
                  {taskType === "listen_repeat" ? `${set.sentences.length} sentences` : `${set.questions.length} questions`}
                </div>
                <div>{set.title}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {promptSet && stage === "running" && (
        <div className="card">
          <p className="section-title">
            {TASK_LABELS[taskType]} — {promptSet.title}
          </p>
          <p className="muted">
            {taskType === "listen_repeat" ? "Sentence" : "Question"} {itemIndex + 1} of {totalItems}
          </p>

          {taskType === "listen_repeat" && (
            <div className="transcript-box center" style={{ margin: "14px 0" }}>
              📷 {promptSet.picture_caption}
            </div>
          )}

          {recorder.error && <div className="error-box">{recorder.error}</div>}

          {phase === "listening" && (
            <div className="center" style={{ margin: "20px 0" }}>
              <div className="muted">🔊 Listen carefully...</div>
            </div>
          )}

          {phase === "recording" && (
            <div className="center" style={{ margin: "20px 0" }}>
              <div className="timer-display speak">{countdown.secondsLeft}s</div>
              <p className="muted">
                {taskType === "listen_repeat" ? "Repeat the sentence now." : "Answer the question now."}
              </p>
              <button type="button" className="danger" onClick={stopEarly}>
                ⏹ Stop Early
              </button>
            </div>
          )}
        </div>
      )}

      {stage === "processing" && (
        <div className="card center">
          <p className="muted">Transcribing and scoring your responses... this may take a moment.</p>
        </div>
      )}

      {stage === "error" && (
        <div className="card">
          <div className="error-box">{submitError}</div>
          <button type="button" onClick={() => setStage("select_prompt")}>
            ← Back to sets
          </button>
        </div>
      )}

      {stage === "result" && result && (
        <div className="card">
          <div className="flex-between">
            <p className="section-title" style={{ margin: 0 }}>
              Score: {result.feedback.score_band} / 6
            </p>
            <span className={`badge ${scoreBadgeClass(result.feedback.score_band)}`}>
              {result.feedback.score_band >= 5 ? "Strong" : result.feedback.score_band === 4 ? "Fair" : "Needs work"}
            </span>
          </div>
          <p className="muted">{result.feedback.score_reason}</p>

          <div className="grid cols-2" style={{ marginTop: 10 }}>
            <div>
              <strong>Fluency</strong>
              <p className="muted small">{result.feedback.fluency}</p>
            </div>
            <div>
              <strong>Accuracy</strong>
              <p className="muted small">{result.feedback.accuracy}</p>
            </div>
            {taskType === "listen_repeat" ? (
              <div>
                <strong>Pronunciation / Delivery</strong>
                <p className="muted small">{result.feedback.pronunciation_delivery}</p>
              </div>
            ) : (
              <div>
                <strong>Coherence</strong>
                <p className="muted small">{result.feedback.coherence}</p>
              </div>
            )}
          </div>

          <p className="section-title" style={{ marginTop: 20 }}>
            {taskType === "listen_repeat" ? "Sentence by sentence" : "Question by question"}
          </p>
          {(result.feedback.items || []).map((item, i) => (
            <div className="correction-row" key={i}>
              {taskType === "listen_repeat" ? (
                <>
                  <p style={{ margin: "2px 0" }}>
                    <strong>Target:</strong> {item.target}
                  </p>
                  <p style={{ margin: "2px 0" }}>
                    <span className="said">You said:</span> {item.said}
                  </p>
                  <p className="muted small" style={{ margin: "2px 0" }}>
                    {item.match_quality} — {item.tip}
                  </p>
                </>
              ) : (
                <>
                  <p style={{ margin: "2px 0" }}>
                    <strong>Q:</strong> {item.question}
                  </p>
                  <p style={{ margin: "2px 0" }}>
                    <span className="said">You said:</span> {item.said}
                  </p>
                  <p style={{ margin: "2px 0" }}>
                    <span className="better">Stronger answer:</span> {item.better_response}
                  </p>
                  <p className="muted small" style={{ margin: "2px 0" }}>
                    {item.why}
                  </p>
                </>
              )}
            </div>
          ))}

          <div className="card" style={{ background: "var(--panel-alt)", marginTop: 18 }}>
            <div className="flex-between">
              <p className="section-title" style={{ margin: 0 }}>
                Focus next time
              </p>
              <ReplayButton text={`${result.feedback.score_reason} ${result.feedback.focus_next}`} />
            </div>
            <p style={{ marginBottom: 0 }}>{result.feedback.focus_next}</p>
          </div>

          <div style={{ marginTop: 18, display: "flex", gap: 10 }}>
            <button type="button" className="primary" onClick={backToPrompts}>
              Try another set
            </button>
            <button type="button" onClick={reset}>
              Change task type
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import { api } from "../api.js";
import { useRecorder } from "../hooks/useRecorder.js";
import { speak } from "../speech.js";
import ReplayButton from "../components/ReplayButton.jsx";

function formatTime(totalSeconds) {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export default function GeneralPractice() {
  const [topics, setTopics] = useState([]);
  const [topicsError, setTopicsError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [phase, setPhase] = useState("select"); // select | ready | recording | processing | result
  const [result, setResult] = useState(null);
  const [submitError, setSubmitError] = useState(null);

  const recorder = useRecorder();

  useEffect(() => {
    api
      .getGeneralTopics()
      .then(setTopics)
      .catch((err) => setTopicsError(err.message));
  }, []);

  const pickTopic = (topic) => {
    setSelected(topic);
    setPhase("ready");
    setResult(null);
    setSubmitError(null);
    recorder.reset();
  };

  const pickRandom = () => {
    if (!topics.length) return;
    const t = topics[Math.floor(Math.random() * topics.length)];
    pickTopic(t);
  };

  const startRecording = async () => {
    setSubmitError(null);
    const ok = await recorder.start();
    if (ok) setPhase("recording");
  };

  const stopAndSubmit = async () => {
    const blob = await recorder.stop();
    if (!blob) return;
    setPhase("processing");
    try {
      const formData = new FormData();
      formData.append("audio", blob, "answer.webm");
      formData.append("topic_id", selected.id);
      formData.append("topic_prompt", selected.prompt);
      const data = await api.submitGeneralAttempt(formData);
      setResult(data);
      setPhase("result");
      if (data.feedback?.improved_version) {
        speak(data.feedback.improved_version);
      }
    } catch (err) {
      setSubmitError(err.message);
      setPhase("ready");
    }
  };

  const reset = () => {
    setSelected(null);
    setPhase("select");
    setResult(null);
    setSubmitError(null);
    recorder.reset();
  };

  return (
    <div>
      <div className="card">
        <p className="section-title">General English Practice</p>
        <p className="muted">Free conversation practice — record an answer of any length, then get feedback.</p>
      </div>

      {topicsError && <div className="error-box">Could not load topics: {topicsError}</div>}

      {phase === "select" && (
        <div className="card">
          <div className="flex-between">
            <p className="section-title" style={{ margin: 0 }}>
              Pick a topic
            </p>
            <button type="button" onClick={pickRandom} disabled={!topics.length}>
              🎲 Random topic
            </button>
          </div>
          <div className="topic-list" style={{ marginTop: 14 }}>
            {topics.map((t) => (
              <div key={t.id} className="topic-item" onClick={() => pickTopic(t)}>
                <div className="cat">{t.category}</div>
                <div>{t.prompt}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {selected && phase !== "select" && (
        <div className="card">
          <div className="cat" style={{ marginBottom: 6 }}>
            {selected.category}
          </div>
          <p style={{ fontSize: "1.15rem", marginTop: 0 }}>{selected.prompt}</p>

          {recorder.error && <div className="error-box">{recorder.error}</div>}
          {submitError && <div className="error-box">{submitError}</div>}

          {phase === "ready" && (
            <div className="center" style={{ marginTop: 18 }}>
              <button type="button" className="primary" onClick={startRecording}>
                🎙️ Start Recording
              </button>
            </div>
          )}

          {phase === "recording" && (
            <div className="center" style={{ marginTop: 18 }}>
              <div className="timer-display speak">{formatTime(recorder.elapsed)}</div>
              <p className="muted">Recording... speak as long as you like.</p>
              <button type="button" className="danger" onClick={stopAndSubmit}>
                ⏹ Stop & Get Feedback
              </button>
            </div>
          )}

          {phase === "processing" && (
            <div className="center" style={{ marginTop: 18 }}>
              <p className="muted">Transcribing and analyzing your answer... this may take a moment.</p>
            </div>
          )}

          {phase === "result" && result && (
            <div style={{ marginTop: 18 }}>
              <p className="section-title">Transcript</p>
              <div className="transcript-box">{result.transcript}</div>

              <p className="section-title" style={{ marginTop: 20 }}>
                Feedback
              </p>
              <p>💬 {result.feedback.encouragement}</p>
              <p>
                <strong>Grammar:</strong> {result.feedback.grammar_feedback}
              </p>
              <p>
                <strong>Vocabulary:</strong> {result.feedback.vocabulary_feedback}
              </p>
              <p>
                <strong>Clarity:</strong> {result.feedback.clarity_feedback}
              </p>

              <div className="card" style={{ background: "var(--panel-alt)", marginTop: 14 }}>
                <div className="flex-between">
                  <p className="section-title" style={{ margin: 0 }}>
                    Improved version
                  </p>
                  <ReplayButton text={result.feedback.improved_version} />
                </div>
                <p style={{ marginBottom: 0 }}>{result.feedback.improved_version}</p>
              </div>

              <p style={{ marginTop: 14 }}>
                <strong>🎯 Tip for next time:</strong> {result.feedback.overall_tip}
              </p>

              <div style={{ marginTop: 18, display: "flex", gap: 10 }}>
                <button type="button" className="primary" onClick={reset}>
                  Try another topic
                </button>
              </div>
            </div>
          )}

          {phase !== "select" && phase !== "result" && (
            <div className="center" style={{ marginTop: 14 }}>
              <button type="button" onClick={reset}>
                ← Back to topics
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

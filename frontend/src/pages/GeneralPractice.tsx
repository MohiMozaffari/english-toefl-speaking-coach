import { useEffect, useState } from "react";
import { api } from "../api";
import { useRecorder } from "../hooks/useRecorder";
import { speak } from "../speech";
import { MetricChips, PageHeader, ReplayButton } from "../components/ui";
import type { GeneralAttemptResponse, GeneralTopic } from "../types";

function formatTime(totalSeconds: number) {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

type Phase = "select" | "ready" | "recording" | "processing" | "result";

export default function GeneralPractice() {
  const [topics, setTopics] = useState<GeneralTopic[]>([]);
  const [topicsError, setTopicsError] = useState<string | null>(null);
  const [selected, setSelected] = useState<GeneralTopic | null>(null);
  const [phase, setPhase] = useState<Phase>("select");
  const [result, setResult] = useState<GeneralAttemptResponse | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const recorder = useRecorder();

  useEffect(() => {
    api.getGeneralTopics().then(setTopics).catch((err) => setTopicsError(err.message));
  }, []);

  const pickTopic = (topic: GeneralTopic) => {
    setSelected(topic);
    setPhase("ready");
    setResult(null);
    setSubmitError(null);
    recorder.reset();
  };

  const pickRandom = () => {
    if (!topics.length) return;
    pickTopic(topics[Math.floor(Math.random() * topics.length)]);
  };

  const startRecording = async () => {
    setSubmitError(null);
    const ok = await recorder.start();
    if (ok) setPhase("recording");
  };

  const stopAndSubmit = async () => {
    const blob = await recorder.stop();
    if (!blob || !selected) return;
    setPhase("processing");
    try {
      const formData = new FormData();
      formData.append("audio", blob, "answer.webm");
      formData.append("topic_id", selected.id);
      formData.append("topic_prompt", selected.prompt);
      const data = await api.submitGeneralAttempt(formData);
      setResult(data);
      setPhase("result");
      if (data.feedback?.improved_version) speak(data.feedback.improved_version);
    } catch (err) {
      setSubmitError((err as Error).message);
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
      <PageHeader
        title="General English Practice"
        subtitle="Free conversation practice — record an answer of any length, get friendly feedback."
      />

      {topicsError && <div className="error-box">Could not load topics: {topicsError}</div>}

      {phase === "select" && (
        <div className="card">
          <div className="flex-between">
            <p className="section-title" style={{ margin: 0 }}>Pick a topic</p>
            <button type="button" onClick={pickRandom} disabled={!topics.length}>🎲 Random topic</button>
          </div>
          <div className="topic-list" style={{ marginTop: 14 }}>
            {topics.map((t) => (
              <button key={t.id} type="button" className="topic-item" onClick={() => pickTopic(t)}>
                <div className="cat">{t.category}</div>
                <div>{t.prompt}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {selected && phase !== "select" && (
        <div className="card">
          <div className="cat" style={{ marginBottom: 6 }}>{selected.category}</div>
          <p style={{ fontSize: "1.15rem", marginTop: 0 }}>{selected.prompt}</p>

          {recorder.error && <div className="error-box">{recorder.error}</div>}
          {submitError && <div className="error-box">{submitError}</div>}

          {phase === "ready" && (
            <div className="center" style={{ marginTop: 18 }}>
              <button type="button" className="primary" onClick={startRecording}>🎙️ Start Recording</button>
            </div>
          )}

          {phase === "recording" && (
            <div className="center" style={{ marginTop: 18 }}>
              <div className="timer-display speak">{formatTime(recorder.elapsed)}</div>
              <p className="muted">
                <span className="recording-dot" aria-hidden="true" />
                Recording… speak as long as you like.
              </p>
              <button type="button" className="danger" onClick={stopAndSubmit}>⏹ Stop & Get Feedback</button>
            </div>
          )}

          {phase === "processing" && (
            <div className="center" style={{ marginTop: 18 }}>
              <p className="muted">Transcribing and analyzing your answer… this may take a moment.</p>
            </div>
          )}

          {phase === "result" && result && (
            <div style={{ marginTop: 18 }} className="pop-in">
              <p className="section-title">Transcript</p>
              <div className="transcript-box">{result.transcript}</div>
              <MetricChips metrics={result.metrics} />

              <p className="section-title" style={{ marginTop: 20 }}>Feedback</p>
              <p>💬 {result.feedback.encouragement}</p>
              {result.feedback.what_went_well && (
                <p><strong>✅ What went well:</strong> {result.feedback.what_went_well}</p>
              )}
              <p><strong>Grammar:</strong> {result.feedback.grammar_feedback}</p>
              <p><strong>Vocabulary:</strong> {result.feedback.vocabulary_feedback}</p>
              <p><strong>Clarity:</strong> {result.feedback.clarity_feedback}</p>

              <div className="card sub" style={{ marginTop: 14 }}>
                <div className="flex-between">
                  <p className="section-title" style={{ margin: 0 }}>Improved version</p>
                  <ReplayButton text={result.feedback.improved_version} />
                </div>
                <p style={{ marginBottom: 0 }}>{result.feedback.improved_version}</p>
              </div>

              <p style={{ marginTop: 14 }}>
                <strong>🎯 Tip for next time:</strong> {result.feedback.overall_tip}
              </p>

              <div className="row" style={{ marginTop: 18 }}>
                <button type="button" className="primary" onClick={reset}>Try another topic</button>
                <button type="button" onClick={() => { setPhase("ready"); setResult(null); }}>🔁 Same topic again</button>
              </div>
            </div>
          )}

          {phase !== "result" && (
            <div className="center" style={{ marginTop: 14 }}>
              <button type="button" className="ghost" onClick={reset}>← Back to topics</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

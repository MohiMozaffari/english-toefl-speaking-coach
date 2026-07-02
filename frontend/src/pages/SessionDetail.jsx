import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api.js";
import ReplayButton from "../components/ReplayButton.jsx";

function scoreBadgeClass(score) {
  if (score >= 5) return "good";
  if (score === 4) return "warn";
  return "bad";
}

export default function SessionDetail() {
  const { id } = useParams();
  const [session, setSession] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setSession(null);
    setError(null);
    api
      .getSession(id)
      .then(setSession)
      .catch((err) => setError(err.message));
  }, [id]);

  if (error) return <div className="error-box">{error}</div>;
  if (!session) return <p className="muted">Loading...</p>;

  const { feedback, mode } = session;

  return (
    <div>
      <p>
        <Link to="/history">← Back to history</Link>
      </p>

      <div className="card">
        <div className="flex-between">
          <p className="section-title" style={{ margin: 0 }}>
            {session.task_title}
          </p>
          {mode === "toefl" && (
            <span className={`badge ${scoreBadgeClass(session.score_band)}`}>{session.score_band} / 6</span>
          )}
        </div>
        <p className="muted small">
          {new Date(session.created_at).toLocaleString()} · {mode === "toefl" ? session.task_type : "General"}
        </p>

        <p className="section-title" style={{ marginTop: 20 }}>
          Transcript
        </p>
        <div className="transcript-box">{session.transcript}</div>

        {mode === "general" ? (
          <>
            <p className="section-title" style={{ marginTop: 20 }}>
              Feedback
            </p>
            <p>💬 {feedback.encouragement}</p>
            <p>
              <strong>Grammar:</strong> {feedback.grammar_feedback}
            </p>
            <p>
              <strong>Vocabulary:</strong> {feedback.vocabulary_feedback}
            </p>
            <p>
              <strong>Clarity:</strong> {feedback.clarity_feedback}
            </p>

            <div className="card" style={{ background: "var(--panel-alt)", marginTop: 14 }}>
              <div className="flex-between">
                <p className="section-title" style={{ margin: 0 }}>
                  Improved version
                </p>
                <ReplayButton text={feedback.improved_version} />
              </div>
              <p style={{ marginBottom: 0 }}>{feedback.improved_version}</p>
            </div>

            <p style={{ marginTop: 14 }}>
              <strong>🎯 Tip:</strong> {feedback.overall_tip}
            </p>
          </>
        ) : (
          <>
            <p className="muted" style={{ marginTop: 20 }}>
              {feedback.score_reason}
            </p>
            <div className="grid cols-2">
              <div>
                <strong>Fluency</strong>
                <p className="muted small">{feedback.fluency}</p>
              </div>
              <div>
                <strong>Accuracy</strong>
                <p className="muted small">{feedback.accuracy}</p>
              </div>
              {session.task_type === "listen_repeat" ? (
                <div>
                  <strong>Pronunciation / Delivery</strong>
                  <p className="muted small">{feedback.pronunciation_delivery}</p>
                </div>
              ) : (
                <div>
                  <strong>Coherence</strong>
                  <p className="muted small">{feedback.coherence}</p>
                </div>
              )}
            </div>

            <p className="section-title" style={{ marginTop: 20 }}>
              {session.task_type === "listen_repeat" ? "Sentence by sentence" : "Question by question"}
            </p>
            {(feedback.items || []).map((item, i) => (
              <div className="correction-row" key={i}>
                {session.task_type === "listen_repeat" ? (
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
                <ReplayButton text={`${feedback.score_reason} ${feedback.focus_next}`} />
              </div>
              <p style={{ marginBottom: 0 }}>{feedback.focus_next}</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { MetricChips, PageHeader, ReplayButton, ScoreBadge, scoreBadgeClass } from "../components/ui";
import type { InterviewItem, ListenRepeatItem, SessionDetailData } from "../types";

export default function SessionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState<SessionDetailData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSession(null);
    setError(null);
    if (!id) return;
    api.getSession(id).then(setSession).catch((err) => setError(err.message));
  }, [id]);

  if (error) return <div className="error-box">{error}</div>;
  if (!session) return <p className="muted">Loading…</p>;

  const { feedback: fb, mode } = session;
  const otherAttempts = (session.other_attempts ?? []).filter((a) => a.id !== session.id);

  return (
    <div>
      <PageHeader
        title={session.task_title}
        subtitle={`${new Date(session.created_at).toLocaleString()} · ${mode === "toefl" ? session.task_type : "General English"}`}
        actions={
          <>
            <Link to="/history" className="btn">← History</Link>
            {mode === "toefl" && <ScoreBadge score={session.score_band} />}
          </>
        }
      />

      {otherAttempts.length > 0 && (
        <div className="card sub">
          <p className="section-title" style={{ marginBottom: 8 }}>📈 All attempts of this prompt</p>
          <div className="row">
            {(session.other_attempts ?? []).map((a) => (
              <button
                key={a.id}
                type="button"
                className={`badge ${a.id === session.id ? "info" : scoreBadgeClass(a.score_band)}`}
                style={{ cursor: a.id === session.id ? "default" : "pointer", border: "none", fontFamily: "inherit" }}
                title={new Date(a.created_at).toLocaleString()}
                onClick={() => a.id !== session.id && navigate(`/history/${a.id}`)}
              >
                {a.score_band != null ? `${a.score_band}/6` : "—"}
                {a.id === session.id ? " (this)" : ""}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <p className="section-title">Transcript</p>
        <div className="transcript-box">{session.transcript}</div>
        <MetricChips metrics={session.metrics} />

        {mode === "general" ? (
          <>
            <p className="section-title" style={{ marginTop: 20 }}>Feedback</p>
            <p>💬 {fb.encouragement}</p>
            {fb.what_went_well && <p><strong>✅ What went well:</strong> {fb.what_went_well}</p>}
            <p><strong>Grammar:</strong> {fb.grammar_feedback}</p>
            <p><strong>Vocabulary:</strong> {fb.vocabulary_feedback}</p>
            <p><strong>Clarity:</strong> {fb.clarity_feedback}</p>

            <div className="card sub" style={{ marginTop: 14 }}>
              <div className="flex-between">
                <p className="section-title" style={{ margin: 0 }}>Improved version</p>
                <ReplayButton text={fb.improved_version} />
              </div>
              <p style={{ marginBottom: 0 }}>{fb.improved_version}</p>
            </div>

            <p style={{ marginTop: 14 }}><strong>🎯 Tip:</strong> {fb.overall_tip}</p>
          </>
        ) : (
          <>
            <p className="muted" style={{ marginTop: 20 }}>{fb.score_reason}</p>
            {(fb.what_went_well || fb.biggest_weakness) && (
              <div className="grid cols-2" style={{ margin: "10px 0" }}>
                {fb.what_went_well && (
                  <div>
                    <strong>✅ What went well</strong>
                    <p className="muted small">{fb.what_went_well}</p>
                  </div>
                )}
                {fb.biggest_weakness && (
                  <div>
                    <strong>⚠️ Biggest weakness</strong>
                    <p className="muted small">{fb.biggest_weakness}</p>
                  </div>
                )}
              </div>
            )}
            <div className="grid cols-3">
              <div>
                <strong>Fluency</strong>
                <p className="muted small">{fb.fluency}</p>
              </div>
              <div>
                <strong>Accuracy</strong>
                <p className="muted small">{fb.accuracy}</p>
              </div>
              {session.task_type === "listen_repeat" ? (
                <div>
                  <strong>Pronunciation / Delivery</strong>
                  <p className="muted small">{fb.pronunciation_delivery}</p>
                </div>
              ) : (
                <div>
                  <strong>Coherence</strong>
                  <p className="muted small">{fb.coherence}</p>
                </div>
              )}
            </div>

            <p className="section-title" style={{ marginTop: 20 }}>
              {session.task_type === "listen_repeat" ? "Sentence by sentence" : "Question by question"}
            </p>
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
                    </p>
                    <p className="muted small" style={{ margin: "2px 0" }}>{(item as InterviewItem).why}</p>
                  </>
                )}
              </div>
            ))}

            {(fb.how_to_improve || fb.suggested_exercises?.length) && (
              <div className="card sub" style={{ marginTop: 14 }}>
                <p className="section-title">🧗 How to improve</p>
                {fb.how_to_improve && <p className="small">{fb.how_to_improve}</p>}
                {fb.suggested_exercises && (
                  <ul className="small muted" style={{ margin: "6px 0 0", paddingLeft: 18 }}>
                    {fb.suggested_exercises.map((e, i) => (
                      <li key={i}>{e}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            <div className="flex-between" style={{ marginTop: 14 }}>
              <p style={{ margin: 0 }}><strong>🎯 Focus next time:</strong> {fb.focus_next}</p>
              <ReplayButton text={`${fb.score_reason} ${fb.focus_next}`} label="🔊 Hear summary" />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { EmptyState, PageHeader, ScoreBadge } from "../components/ui";
import type { SessionSummary } from "../types";

const TASK_LABEL: Record<string, string> = {
  listen_repeat: "Listen & Repeat",
  interview: "Interview",
};

export default function History() {
  const [filter, setFilter] = useState("all");
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const mode = filter === "all" ? undefined : filter;
    api
      .getSessions(mode)
      .then(setSessions)
      .catch((err) => setError(err.message));
  }, [filter]);

  return (
    <div>
      <PageHeader title="Practice History" subtitle="Every attempt is saved locally — reopen any session to review its full feedback." />

      <div className="card">
        <div className="flex-between">
          <div className="row">
            {["all", "toefl", "general"].map((f) => (
              <button key={f} type="button" className={`small ${filter === f ? "primary" : ""}`} onClick={() => setFilter(f)}>
                {f === "all" ? "All" : f === "toefl" ? "TOEFL" : "General"}
              </button>
            ))}
          </div>
          <span className="muted small">{sessions.length} sessions</span>
        </div>

        {error && <div className="error-box">{error}</div>}

        {sessions.length === 0 && !error ? (
          <EmptyState icon="🕘" title="No sessions yet" hint="Complete a practice attempt and it will appear here." />
        ) : (
          <div style={{ marginTop: 10 }}>
            {sessions.map((s) => (
              <button key={s.id} type="button" className="session-row" onClick={() => navigate(`/history/${s.id}`)}>
                <div>
                  <div style={{ fontWeight: 600 }}>{s.task_title}</div>
                  <div className="muted small">
                    {new Date(s.created_at).toLocaleString()} ·{" "}
                    {s.mode === "toefl" ? TASK_LABEL[s.task_type] ?? s.task_type : "General English"}
                  </div>
                </div>
                <ScoreBadge score={s.score_band} />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

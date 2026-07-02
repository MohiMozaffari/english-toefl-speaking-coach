import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api.js";
import ScoreChart from "../components/ScoreChart.jsx";

function scoreBadgeClass(score) {
  if (score >= 5) return "good";
  if (score === 4) return "warn";
  return "bad";
}

export default function History() {
  const [filter, setFilter] = useState("all");
  const [sessions, setSessions] = useState([]);
  const [stats, setStats] = useState([]);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const mode = filter === "all" ? undefined : filter;
    api
      .getSessions(mode)
      .then(setSessions)
      .catch((err) => setError(err.message));
  }, [filter]);

  useEffect(() => {
    api
      .getToeflStats()
      .then(setStats)
      .catch(() => setStats([]));
  }, []);

  return (
    <div>
      <div className="card">
        <p className="section-title">TOEFL Score Trend</p>
        <ScoreChart data={stats} />
      </div>

      <div className="card">
        <div className="flex-between">
          <p className="section-title" style={{ margin: 0 }}>
            Session History
          </p>
          <div style={{ display: "flex", gap: 8 }}>
            <button type="button" onClick={() => setFilter("all")} className={filter === "all" ? "primary" : ""}>
              All
            </button>
            <button
              type="button"
              onClick={() => setFilter("general")}
              className={filter === "general" ? "primary" : ""}
            >
              General
            </button>
            <button type="button" onClick={() => setFilter("toefl")} className={filter === "toefl" ? "primary" : ""}>
              TOEFL
            </button>
          </div>
        </div>

        {error && <div className="error-box">{error}</div>}

        {sessions.length === 0 && !error && (
          <p className="muted" style={{ marginTop: 14 }}>
            No sessions yet. Complete a practice attempt to see it here.
          </p>
        )}

        <div style={{ marginTop: 10 }}>
          {sessions.map((s) => (
            <div className="session-row" key={s.id} onClick={() => navigate(`/history/${s.id}`)}>
              <div>
                <div>{s.task_title}</div>
                <div className="muted small">
                  {new Date(s.created_at).toLocaleString()} · {s.mode === "toefl" ? s.task_type : "General"}
                </div>
              </div>
              {s.mode === "toefl" && s.score_band !== null && (
                <span className={`badge ${scoreBadgeClass(s.score_band)}`}>{s.score_band} / 6</span>
              )}
            </div>
          ))}
        </div>
      </div>

      <p>
        <Link to="/">← Back to home</Link>
      </p>
    </div>
  );
}

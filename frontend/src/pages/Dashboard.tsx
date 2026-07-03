import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api";
import { useProfile } from "../contexts";
import { EmptyState, LoadingCard, PageHeader, ProgressRing, Stat } from "../components/ui";
import type { DashboardData } from "../types";

const chartTooltipStyle = {
  background: "var(--panel)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  color: "var(--text)",
  fontSize: 13,
};

export default function Dashboard() {
  const { profile } = useProfile();
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setData(null);
    api
      .getDashboard(profile?.id)
      .then(setData)
      .catch((err) => setError(err.message));
  }, [profile?.id]);

  if (error) {
    return (
      <div className="error-box">
        Could not load the dashboard. Is the backend running on http://localhost:8001? {"\n"}
        {error}
      </div>
    );
  }
  if (!data) return <LoadingCard lines={5} />;

  const { xp, streak, totals, weekly, score_trend, radar, delivery_trend, weaknesses, recommendations, achievements } =
    data;
  const goalFraction = xp.daily_goal ? xp.today / xp.daily_goal : 0;
  const radarData = radar.filter((r) => r.value !== null);
  const earned = achievements.filter((a) => a.earned);
  const hasAnyData = totals.sessions > 0 || totals.shadowing_attempts > 0 || totals.pair_attempts > 0;

  return (
    <div>
      <PageHeader
        title={`Welcome back, ${data.profile.name}`}
        subtitle="Your speaking progress at a glance."
      />

      {/* Top row: streak / XP / goal */}
      <div className="grid cols-3" style={{ marginBottom: 18 }}>
        <div className="card flat" style={{ margin: 0, display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ fontSize: "2.2rem" }} aria-hidden="true">🔥</div>
          <div>
            <div style={{ fontSize: "1.55rem", fontWeight: 800 }}>{streak.current} day{streak.current === 1 ? "" : "s"}</div>
            <div className="muted small">
              Current streak · best {streak.best}
              {streak.active_today ? " · practiced today ✓" : ""}
            </div>
          </div>
        </div>
        <div className="card flat" style={{ margin: 0, display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ fontSize: "2.2rem" }} aria-hidden="true">⭐</div>
          <div>
            <div style={{ fontSize: "1.55rem", fontWeight: 800 }}>Level {xp.level}</div>
            <div className="muted small">
              {xp.total} XP total · {xp.xp_into_level}/{xp.xp_for_next} to next level
            </div>
            <div className="progress-track" style={{ marginTop: 6, width: 160 }}>
              <div className="progress-fill" style={{ width: `${(xp.xp_into_level / xp.xp_for_next) * 100}%` }} />
            </div>
          </div>
        </div>
        <div className="card flat" style={{ margin: 0, display: "flex", alignItems: "center", gap: 16 }}>
          <ProgressRing
            fraction={goalFraction}
            label={`${Math.min(Math.round(goalFraction * 100), 999)}%`}
            sublabel="daily goal"
            size={84}
          />
          <div>
            <div style={{ fontWeight: 700 }}>{xp.today} / {xp.daily_goal} XP today</div>
            <div className="muted small">{goalFraction >= 1 ? "Goal reached — nice work! 🎉" : "Keep going!"}</div>
          </div>
        </div>
      </div>

      {!hasAnyData && (
        <div className="card">
          <EmptyState
            icon="🎤"
            title="No practice data yet"
            hint="Complete your first TOEFL set or shadowing session and this dashboard comes alive."
            action={<Link className="btn primary" to="/toefl">Start TOEFL practice</Link>}
          />
        </div>
      )}

      {/* Totals */}
      <div className="grid cols-4" style={{ marginBottom: 18 }}>
        <Stat value={totals.sessions} label="Practice sessions" />
        <Stat value={totals.minutes_spoken} label="Minutes spoken" />
        <Stat value={totals.words_spoken.toLocaleString()} label="Words spoken" />
        <Stat value={`${totals.shadowing_attempts + totals.pair_attempts}`} label="Skill drills done" />
      </div>

      <div className="grid cols-2">
        {/* Weekly activity */}
        <div className="card" style={{ margin: 0 }}>
          <p className="section-title">This week</p>
          <ResponsiveContainer width="100%" height={190}>
            <BarChart data={weekly} margin={{ top: 5, right: 5, left: -22, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                dataKey="date"
                stroke="var(--text-faint)"
                tick={{ fontSize: 11 }}
                tickFormatter={(d: string) => d.slice(5)}
              />
              <YAxis stroke="var(--text-faint)" tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip contentStyle={chartTooltipStyle} formatter={(v: number) => [`${v} XP`, "Earned"]} />
              <Bar dataKey="xp" fill="var(--accent)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Skill radar */}
        <div className="card" style={{ margin: 0 }}>
          <p className="section-title">Skill radar</p>
          {radarData.length >= 3 ? (
            <ResponsiveContainer width="100%" height={190}>
              <RadarChart data={radarData} outerRadius="72%">
                <PolarGrid stroke="var(--border)" />
                <PolarAngleAxis dataKey="axis" tick={{ fontSize: 11, fill: "var(--text-dim)" }} />
                <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                <Radar dataKey="value" stroke="var(--accent)" fill="var(--accent)" fillOpacity={0.35} />
                <Tooltip contentStyle={chartTooltipStyle} formatter={(v: number) => [`${v}/100`]} />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState icon="🕸️" title="Not enough signal yet" hint="A few more practice sessions unlock your skill radar." />
          )}
        </div>
      </div>

      <div className="grid cols-2" style={{ marginTop: 14 }}>
        {/* TOEFL score trend */}
        <div className="card" style={{ margin: 0 }}>
          <p className="section-title">TOEFL score trend</p>
          {score_trend.length ? (
            <ResponsiveContainer width="100%" height={190}>
              <LineChart
                data={score_trend.map((s, i) => ({ attempt: i + 1, score: s.score_band, task: s.task_type }))}
                margin={{ top: 5, right: 8, left: -28, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="attempt" stroke="var(--text-faint)" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 6]} ticks={[1, 2, 3, 4, 5, 6]} stroke="var(--text-faint)" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={chartTooltipStyle}
                  formatter={(v: number) => [`${v} / 6`, "Score"]}
                  labelFormatter={(l) => `Attempt ${l}`}
                />
                <Line type="monotone" dataKey="score" stroke="var(--good)" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState icon="🎓" title="No TOEFL attempts yet" action={<Link className="btn" to="/toefl">Take a task</Link>} />
          )}
        </div>

        {/* Delivery trend */}
        <div className="card" style={{ margin: 0 }}>
          <p className="section-title">Speaking speed over time</p>
          {delivery_trend.length >= 2 ? (
            <ResponsiveContainer width="100%" height={190}>
              <LineChart
                data={delivery_trend.map((d, i) => ({ ...d, n: i + 1 }))}
                margin={{ top: 5, right: 8, left: -22, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="n" stroke="var(--text-faint)" tick={{ fontSize: 11 }} />
                <YAxis stroke="var(--text-faint)" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={chartTooltipStyle}
                  formatter={(v: number, name: string) => [v, name === "wpm" ? "Words/min" : name]}
                  labelFormatter={(l) => `Session ${l}`}
                />
                <Line type="monotone" dataKey="wpm" stroke="var(--violet)" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState icon="⏱️" title="Speak a bit more" hint="Speed, pauses, and vocabulary trends appear after a couple of recorded sessions." />
          )}
        </div>
      </div>

      {/* Coach: weaknesses + recommendations */}
      <div className="grid cols-2" style={{ marginTop: 14 }}>
        <div className="card" style={{ margin: 0 }}>
          <p className="section-title">🩺 What's holding you back</p>
          {weaknesses.length ? (
            weaknesses.map((w) => (
              <div key={w.tag} className="correction-row">
                <strong>{w.label}</strong>
                <p className="muted small" style={{ margin: "3px 0 0" }}>{w.evidence}</p>
              </div>
            ))
          ) : (
            <p className="muted small">No standout weaknesses detected yet — the coach needs a few sessions of evidence.</p>
          )}
        </div>

        <div className="card" style={{ margin: 0 }}>
          <p className="section-title">🧭 Coach recommendations</p>
          {recommendations.map((r, i) => (
            <div key={i} className="correction-row">
              <div className="flex-between">
                <strong>{r.title}</strong>
                <Link to={r.route} className="btn small">Go →</Link>
              </div>
              <p className="muted small" style={{ margin: "3px 0 0" }}>{r.action}</p>
              <p className="faint small" style={{ margin: "2px 0 0" }}>{r.reason}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Achievements */}
      <div className="card" style={{ marginTop: 14 }}>
        <div className="flex-between">
          <p className="section-title" style={{ margin: 0 }}>🏆 Achievements</p>
          <span className="badge info">{earned.length} / {achievements.length}</span>
        </div>
        <div className="grid cols-3" style={{ marginTop: 14 }}>
          {achievements.map((a) => (
            <div key={a.id} className={`achievement ${a.earned ? "pop-in" : "locked"}`}>
              <div className="icon" aria-hidden="true">{a.icon}</div>
              <div>
                <strong style={{ fontSize: "0.9rem" }}>{a.title}</strong>
                <p className="muted small" style={{ margin: "2px 0 0" }}>{a.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

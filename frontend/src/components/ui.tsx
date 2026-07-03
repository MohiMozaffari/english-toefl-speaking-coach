import { useState } from "react";
import type { ReactNode } from "react";
import { speak, stopSpeaking } from "../speech";
import type { Metrics, WordDiff } from "../types";

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="flex-between" style={{ marginBottom: 18 }}>
      <div>
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle" style={{ marginBottom: 0 }}>{subtitle}</p>}
      </div>
      {actions && <div className="row">{actions}</div>}
    </div>
  );
}

export function Stat({ value, label, hint }: { value: ReactNode; label: string; hint?: string }) {
  return (
    <div className="stat" title={hint}>
      <div className="value">{value}</div>
      <div className="label">{label}</div>
    </div>
  );
}

export function ProgressRing({
  fraction,
  size = 92,
  stroke = 9,
  label,
  sublabel,
}: {
  fraction: number;
  size?: number;
  stroke?: number;
  label: string;
  sublabel?: string;
}) {
  const clamped = Math.max(0, Math.min(1, fraction));
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  return (
    <div style={{ position: "relative", width: size, height: size }} role="img" aria-label={`${label} ${sublabel ?? ""}`}>
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--bg-soft)" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={clamped >= 1 ? "var(--good)" : "var(--accent)"}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - clamped)}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: "stroke-dashoffset 0.5s ease" }}
        />
      </svg>
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <strong style={{ fontSize: size / 5.2 }}>{label}</strong>
        {sublabel && <span className="faint" style={{ fontSize: size / 8.5 }}>{sublabel}</span>}
      </div>
    </div>
  );
}

export function scoreBadgeClass(score: number | null | undefined): string {
  if (score == null) return "neutral";
  if (score >= 5) return "good";
  if (score === 4) return "warn";
  return "bad";
}

export function ScoreBadge({ score }: { score: number | null | undefined }) {
  if (score == null) return null;
  return <span className={`badge ${scoreBadgeClass(score)}`}>{score} / 6</span>;
}

export function DiffText({ diff }: { diff: WordDiff }) {
  return (
    <div aria-label="Word-by-word comparison">
      {diff.target_words.map((w, i) => (
        <span key={i} className={`diff-word ${w.status}`}>
          {w.word}
        </span>
      ))}
      {diff.extra_words.length > 0 && (
        <p className="muted small" style={{ marginBottom: 0 }}>
          Extra words you added: {diff.extra_words.join(", ")}
        </p>
      )}
    </div>
  );
}

export function MetricChips({ metrics }: { metrics: Metrics | null | undefined }) {
  if (!metrics || !metrics.word_count) return null;
  const chips = [
    { label: `${metrics.articulation_wpm} wpm`, hint: "Speaking rate while talking (excludes pauses)" },
    { label: `${metrics.word_count} words`, hint: "Total words spoken" },
    { label: `${metrics.long_pause_count} long pauses`, hint: "Pauses of 1 second or more" },
    { label: `${metrics.filler_count} fillers`, hint: "um, uh, like, you know…" },
    { label: `${Math.round(metrics.type_token_ratio * 100)}% variety`, hint: "Unique words / total words" },
    { label: `${Math.round(metrics.avg_word_confidence * 100)}% clarity`, hint: "How confidently the recognizer heard you" },
  ];
  return (
    <div className="row" style={{ marginTop: 10 }}>
      {chips.map((chip) => (
        <span key={chip.label} className="badge neutral" title={chip.hint}>
          {chip.label}
        </span>
      ))}
    </div>
  );
}

export function ReplayButton({ text, label = "🔊 Listen", rate = 1 }: { text: string | undefined; label?: string; rate?: number }) {
  const [speaking, setSpeaking] = useState(false);
  if (!text) return null;

  const handleClick = async () => {
    if (speaking) {
      stopSpeaking();
      setSpeaking(false);
      return;
    }
    setSpeaking(true);
    await speak(text, { rate, onEnd: () => setSpeaking(false) });
  };

  return (
    <button type="button" onClick={handleClick} aria-label={speaking ? "Stop audio" : "Play audio"}>
      {speaking ? "⏹ Stop" : label}
    </button>
  );
}

export function EmptyState({ icon, title, hint, action }: { icon: string; title: string; hint?: string; action?: ReactNode }) {
  return (
    <div className="center" style={{ padding: "34px 10px" }}>
      <div style={{ fontSize: "2.2rem" }}>{icon}</div>
      <p style={{ fontWeight: 700, margin: "10px 0 4px" }}>{title}</p>
      {hint && <p className="muted small" style={{ margin: 0 }}>{hint}</p>}
      {action && <div style={{ marginTop: 14 }}>{action}</div>}
    </div>
  );
}

export function Skeleton({ height = 14, width = "100%", style }: { height?: number; width?: number | string; style?: React.CSSProperties }) {
  return <div className="skeleton" style={{ height, width, ...style }} aria-hidden="true" />;
}

export function LoadingCard({ lines = 3 }: { lines?: number }) {
  return (
    <div className="card" aria-busy="true" aria-label="Loading">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} style={{ marginBottom: 10, width: `${100 - i * 18}%` }} />
      ))}
    </div>
  );
}

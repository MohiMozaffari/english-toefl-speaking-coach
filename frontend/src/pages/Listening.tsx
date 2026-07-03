import { useEffect, useState } from "react";
import { api } from "../api";
import { useProfile } from "../contexts";
import { speak, speakConversation, stopSpeaking } from "../speech";
import { LoadingCard, PageHeader } from "../components/ui";
import type { ListeningItem, ListeningItemSummary, QuizResult } from "../types";

const RATES = [0.75, 1, 1.25];
const DIFF_BADGE: Record<string, string> = { beginner: "good", intermediate: "warn", advanced: "bad" };
const TYPE_LABEL: Record<string, string> = {
  conversation: "💬 Conversation",
  announcement: "📢 Announcement",
  ted_style: "🎤 TED-style talk",
  academic: "🎓 Academic lecture",
  podcast: "🎙️ Podcast",
};

export default function Listening() {
  const { profile } = useProfile();
  const [items, setItems] = useState<ListeningItemSummary[]>([]);
  const [filter, setFilter] = useState("all");
  const [item, setItem] = useState<ListeningItem | null>(null);
  const [showTranscript, setShowTranscript] = useState(false);
  const [playingIdx, setPlayingIdx] = useState<number | null>(null);
  const [playingAll, setPlayingAll] = useState(false);
  const [rate, setRate] = useState(1);
  const [answers, setAnswers] = useState<(number | null)[]>([]);
  const [result, setResult] = useState<QuizResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getListeningItems().then(setItems).catch((err) => setError(err.message));
    return () => stopSpeaking();
  }, []);

  const open = async (id: string) => {
    try {
      const full = await api.getListeningItem(id);
      setItem(full);
      setAnswers(new Array(full.questions.length).fill(null));
      setResult(null);
      setShowTranscript(false);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const playAll = async () => {
    if (!item) return;
    stopSpeaking();
    setPlayingAll(true);
    await speakConversation(
      item.segments.map((s) => ({ speaker: s.speaker, line: s.text })),
      { rate, announceSpeaker: item.segments.some((s, i, all) => i > 0 && s.speaker !== all[i - 1].speaker) }
    );
    setPlayingAll(false);
  };

  const playSegment = async (i: number) => {
    if (!item) return;
    stopSpeaking();
    setPlayingIdx(i);
    await speak(item.segments[i].text, { rate, onEnd: () => setPlayingIdx(null) });
  };

  const submit = async () => {
    if (!item) return;
    setError(null);
    try {
      const res = await api.submitListeningQuiz(item.id, answers, profile?.id);
      setResult(res);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  // ---- Browser ----
  if (!item) {
    const filtered = items.filter((i) => filter === "all" || i.difficulty === filter);
    return (
      <div>
        <PageHeader
          title="Listening Practice"
          subtitle="Lectures, conversations, and announcements with interactive transcripts and comprehension checks."
        />
        {error && <div className="error-box">{error}</div>}
        <div className="row" style={{ marginBottom: 14 }}>
          {["all", "beginner", "intermediate", "advanced"].map((d) => (
            <button key={d} type="button" className={`small ${filter === d ? "primary" : ""}`} onClick={() => setFilter(d)}>
              {d === "all" ? "All levels" : d}
            </button>
          ))}
        </div>
        {!items.length ? (
          <LoadingCard />
        ) : (
          <div className="grid cols-2">
            {filtered.map((i) => (
              <button key={i.id} type="button" className="topic-item" onClick={() => open(i.id)}>
                <div className="flex-between">
                  <div className="cat">{TYPE_LABEL[i.type] ?? i.type}</div>
                  <span className={`badge ${DIFF_BADGE[i.difficulty]}`}>{i.difficulty}</span>
                </div>
                <div style={{ fontWeight: 700 }}>{i.title}</div>
                <div className="muted small" style={{ marginTop: 4 }}>
                  {i.segment_count} segments · {i.question_count} questions
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ---- Player + quiz ----
  const answeredAll = answers.every((a) => a !== null);

  return (
    <div>
      <PageHeader
        title={item.title}
        subtitle={`${TYPE_LABEL[item.type] ?? item.type} · ${item.difficulty}`}
        actions={<button type="button" onClick={() => { stopSpeaking(); setItem(null); }}>← All items</button>}
      />

      <div className="card">
        <div className="row">
          <button type="button" className="primary" onClick={playAll} disabled={playingAll}>
            {playingAll ? "🔊 Playing…" : "▶ Play audio"}
          </button>
          <div className="row" role="group" aria-label="Playback speed">
            {RATES.map((r) => (
              <button key={r} type="button" className={`small ${rate === r ? "primary" : ""}`} onClick={() => setRate(r)}>
                {r}x
              </button>
            ))}
          </div>
          <button type="button" onClick={() => setShowTranscript((s) => !s)}>
            {showTranscript ? "🙈 Hide transcript" : "📜 Show transcript"}
          </button>
        </div>
        <p className="muted small" style={{ marginBottom: 0 }}>
          Real-exam tip: listen once without the transcript, answer the questions, then re-listen with it to check what you missed.
        </p>

        {showTranscript && (
          <div style={{ marginTop: 14 }}>
            {item.segments.map((seg, i) => (
              <button
                key={i}
                type="button"
                className={`seg-row ${playingIdx === i ? "playing" : ""}`}
                onClick={() => playSegment(i)}
                aria-label={`Play segment ${i + 1}`}
              >
                <span className="seg-speaker">{seg.speaker}</span>
                <span>{seg.text}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <p className="section-title">Comprehension check</p>
        {item.questions.map((q, qi) => {
          const detail = result?.detail[qi];
          return (
            <fieldset key={qi} style={{ border: "none", padding: 0, margin: "0 0 18px" }}>
              <legend style={{ fontWeight: 650, marginBottom: 8, padding: 0 }}>
                {qi + 1}. {q.q}
              </legend>
              {q.options.map((opt, oi) => {
                let cls = "";
                if (result && detail) {
                  if (oi === detail.correct_answer) cls = "good";
                  else if (detail.given === oi && !detail.correct) cls = "bad";
                }
                return (
                  <label
                    key={oi}
                    className="row"
                    style={{
                      margin: "4px 0",
                      padding: "8px 12px",
                      borderRadius: 8,
                      cursor: result ? "default" : "pointer",
                      background: cls === "good" ? "var(--good-soft)" : cls === "bad" ? "var(--bad-soft)" : "var(--panel-alt)",
                      border: `1px solid ${cls === "good" ? "var(--good)" : cls === "bad" ? "var(--bad)" : "var(--border)"}`,
                    }}
                  >
                    <input
                      type="radio"
                      name={`q${qi}`}
                      style={{ width: "auto" }}
                      disabled={!!result}
                      checked={answers[qi] === oi}
                      onChange={() => setAnswers((prev) => prev.map((a, i) => (i === qi ? oi : a)))}
                    />
                    <span>{opt}</span>
                  </label>
                );
              })}
            </fieldset>
          );
        })}

        {error && <div className="error-box">{error}</div>}

        {!result ? (
          <button type="button" className="primary" onClick={submit} disabled={!answeredAll}>
            {answeredAll ? "Check answers" : "Answer all questions first"}
          </button>
        ) : (
          <div className="pop-in">
            <div className={result.score === result.total ? "success-box" : "card sub"} style={{ marginTop: 4 }}>
              {result.score === result.total ? "🎉 " : "📌 "}You got <strong>{result.score} / {result.total}</strong> correct
              {result.score < result.total && " — replay the audio with the transcript open and find what you missed."}
            </div>
            <div className="row">
              <button type="button" onClick={() => { setResult(null); setAnswers(new Array(item.questions.length).fill(null)); }}>
                🔁 Try again
              </button>
              <button type="button" className="primary" onClick={() => { stopSpeaking(); setItem(null); }}>
                Next item →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { useNeuralPlayer } from "../hooks/useNeuralPlayer";
import { useRecorder } from "../hooks/useRecorder";
import { DiffText, LoadingCard, MetricChips, PageHeader } from "../components/ui";
import type {
  ContrastStats,
  IpaSound,
  Lesson,
  MinimalPairSet,
  PairVerdict,
  PronunciationContent,
  ShadowingResult,
} from "../types";

type Tab = "sounds" | "pairs" | "lessons";

export default function PronunciationLab() {
  const [content, setContent] = useState<PronunciationContent | null>(null);
  const [stats, setStats] = useState<ContrastStats[]>([]);
  const [tab, setTab] = useState<Tab>("sounds");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getPronunciationContent().then(setContent).catch((err) => setError(err.message));
    refreshStats();
    // Each tab plays audio through its own useNeuralPlayer, which stops on unmount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refreshStats = () => {
    api.getPronunciationStats().then(setStats).catch(() => {});
  };

  if (error) return <div className="error-box">{error}</div>;
  if (!content) return <LoadingCard lines={5} />;

  return (
    <div>
      <PageHeader
        title="Pronunciation Lab"
        subtitle="American English sounds, minimal-pair drills judged by the local speech recognizer, and delivery technique lessons."
      />
      <div className="row" style={{ marginBottom: 16 }}>
        {(
          [
            ["sounds", "🔤 IPA Sounds"],
            ["pairs", "👂 Minimal Pairs"],
            ["lessons", "🎼 Technique Lessons"],
          ] as [Tab, string][]
        ).map(([t, label]) => (
          <button key={t} type="button" className={tab === t ? "primary" : ""} onClick={() => setTab(t)}>
            {label}
          </button>
        ))}
      </div>

      {tab === "sounds" && <SoundsTab vowels={content.vowels} consonants={content.consonants} />}
      {tab === "pairs" && <PairsTab sets={content.minimal_pairs} stats={stats} onAttempt={refreshStats} />}
      {tab === "lessons" && <LessonsTab lessons={content.lessons} />}
    </div>
  );
}

// --- IPA sounds -----------------------------------------------------------------

function SoundsTab({ vowels, consonants }: { vowels: IpaSound[]; consonants: IpaSound[] }) {
  const [selected, setSelected] = useState<IpaSound | null>(null);
  const player = useNeuralPlayer();

  const hear = (sound: IpaSound) => {
    setSelected(sound);
    player.play(`${sound.examples[0]}. ${sound.examples[1]}. ${sound.examples[2]}.`, 0.85);
  };

  const Chart = ({ title, sounds }: { title: string; sounds: IpaSound[] }) => (
    <div className="card">
      <p className="section-title">{title}</p>
      <div className="row">
        {sounds.map((s) => (
          <button
            key={s.symbol}
            type="button"
            className="ipa-chip"
            onClick={() => hear(s)}
            aria-label={`${s.name}, hear examples`}
            style={{ minWidth: 74, borderColor: selected?.symbol === s.symbol ? "var(--accent)" : undefined }}
          >
            <span className="symbol">/{s.symbol}/</span>
            <span className="name">{s.name}</span>
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <div>
      {selected && (
        <div className="card sub pop-in">
          <div className="flex-between">
            <p className="section-title" style={{ margin: 0 }}>
              /{selected.symbol}/ — {selected.name}
            </p>
            <button type="button" className="small" onClick={() => hear(selected)}>
              🔊 Hear again
            </button>
          </div>
          <p style={{ margin: "8px 0 4px" }}>
            {selected.examples.map((w, i) => (
              <span key={w}>
                {i > 0 && " · "}
                <strong>{w}</strong>
              </span>
            ))}
          </p>
          <p className="muted small" style={{ margin: 0 }}>💡 {selected.tip}</p>
        </div>
      )}
      <Chart title="Vowels & Diphthongs" sounds={vowels} />
      <Chart title="Tricky Consonants" sounds={consonants} />
    </div>
  );
}

// --- Minimal pairs drill ----------------------------------------------------------

function PairsTab({
  sets,
  stats,
  onAttempt,
}: {
  sets: MinimalPairSet[];
  stats: ContrastStats[];
  onAttempt: () => void;
}) {
  const [activeSet, setActiveSet] = useState<MinimalPairSet | null>(null);
  const [target, setTarget] = useState<string | null>(null);
  const [verdict, setVerdict] = useState<PairVerdict | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [drillCount, setDrillCount] = useState(0);
  const recorder = useRecorder();
  const player = useNeuralPlayer();

  const statFor = (set: MinimalPairSet) =>
    stats.find((s) => s.contrast === `${set.contrast} (${set.label})`);

  const nextWord = (set: MinimalPairSet) => {
    const pair = set.pairs[Math.floor(Math.random() * set.pairs.length)];
    const word = pair[Math.floor(Math.random() * 2)];
    setTarget(word);
    setVerdict(null);
    recorder.reset();
  };

  const startSet = (set: MinimalPairSet) => {
    setActiveSet(set);
    setDrillCount(0);
    setError(null);
    nextWord(set);
  };

  const submit = async () => {
    const blob = await recorder.stop();
    if (!blob || !activeSet || !target) return;
    setBusy(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("audio", blob, "pair.webm");
      formData.append("pair_set_id", activeSet.id);
      formData.append("target_word", target);
      const res = await api.submitPairAttempt(formData);
      setVerdict(res);
      setDrillCount((c) => c + 1);
      onAttempt();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  if (!activeSet) {
    return (
      <div>
        {stats.length > 0 && (
          <div className="card sub">
            <p className="section-title">Your contrast accuracy</p>
            {stats.map((s) => (
              <div key={s.contrast} className="flex-between" style={{ padding: "6px 0" }}>
                <span className="small">{s.contrast}</span>
                <span className={`badge ${s.accuracy >= 85 ? "good" : s.accuracy >= 65 ? "warn" : "bad"}`}>
                  {s.accuracy}% · {s.attempts} tries
                </span>
              </div>
            ))}
          </div>
        )}
        <div className="grid cols-2">
          {sets.map((set) => {
            const s = statFor(set);
            return (
              <button key={set.id} type="button" className="topic-item" onClick={() => startSet(set)}>
                <div className="flex-between">
                  <div className="cat">{set.contrast}</div>
                  {s && (
                    <span className={`badge ${s.accuracy >= 85 ? "good" : s.accuracy >= 65 ? "warn" : "bad"}`}>
                      {s.accuracy}%
                    </span>
                  )}
                </div>
                <div style={{ fontWeight: 700 }}>{set.label}</div>
                <div className="muted small" style={{ marginTop: 4 }}>{set.description}</div>
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex-between">
        <p className="section-title" style={{ margin: 0 }}>
          {activeSet.contrast} — {activeSet.label}
        </p>
        <button type="button" onClick={() => setActiveSet(null)}>← All contrasts</button>
      </div>
      <p className="muted small">{activeSet.description}</p>
      <p className="muted small">
        Words in this set:{" "}
        {activeSet.pairs.map(([a, b], i) => (
          <span key={i}>
            {i > 0 && " · "}
            {a}/{b}
          </span>
        ))}
      </p>

      <div className="card sub center" style={{ margin: "16px 0" }}>
        <p className="muted small" style={{ marginTop: 0 }}>Say this word clearly:</p>
        <p style={{ fontSize: "2.3rem", fontWeight: 800, margin: "4px 0 10px" }}>{target}</p>
        <div className="row" style={{ justifyContent: "center" }}>
          <button type="button" className="small" onClick={() => player.play(target!, 0.8)}>
            🔊 Hear it first
          </button>
          {recorder.status !== "recording" ? (
            <button type="button" className="primary" onClick={() => { player.stop(); setVerdict(null); recorder.start(); }} disabled={busy}>
              🎙️ Record
            </button>
          ) : (
            <button type="button" className="danger" onClick={submit}>
              <span className="recording-dot" aria-hidden="true" /> Stop
            </button>
          )}
        </div>
        {busy && <p className="muted small">Listening back…</p>}
      </div>

      {recorder.error && <div className="error-box">{recorder.error}</div>}
      {error && <div className="error-box">{error}</div>}

      {verdict && (
        <div className="pop-in">
          {verdict.verdict === "correct" && (
            <div className="success-box">✅ The recognizer heard “{verdict.target_word}” — exactly right!</div>
          )}
          {verdict.verdict === "incorrect" && (
            <div className="error-box">
              ❌ You were asked to say “{verdict.target_word}”, but it heard “{verdict.heard}”. That's the {activeSet.contrast} contrast slipping.
            </div>
          )}
          {verdict.verdict === "unclear" && (
            <div className="card sub" style={{ margin: "14px 0" }}>
              🤔 Couldn't clearly hear either word (it heard: “{verdict.transcript || "nothing"}”). Not scored — try again closer to the microphone.
            </div>
          )}
          <div className="row">
            <button type="button" className="primary" onClick={() => nextWord(activeSet)}>
              Next word → <span className="badge neutral">{drillCount} done</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// --- Technique lessons -------------------------------------------------------------

function LessonsTab({ lessons }: { lessons: Lesson[] }) {
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [lineIndex, setLineIndex] = useState(0);
  const [result, setResult] = useState<ShadowingResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recorder = useRecorder();
  const player = useNeuralPlayer();

  const line = useMemo(() => lesson?.practice_lines[lineIndex], [lesson, lineIndex]);

  const open = (l: Lesson) => {
    setLesson(l);
    setLineIndex(0);
    setResult(null);
    recorder.reset();
  };

  const submit = async () => {
    const blob = await recorder.stop();
    if (!blob || !lesson) return;
    setBusy(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("audio", blob, "line.webm");
      formData.append("lesson_id", lesson.id);
      formData.append("line_index", String(lineIndex));
      const res = await api.submitLineAttempt(formData);
      setResult(res);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  if (!lesson) {
    return (
      <div className="grid cols-2">
        {lessons.map((l) => (
          <button key={l.id} type="button" className="topic-item" onClick={() => open(l)}>
            <div className="cat">{l.focus}</div>
            <div style={{ fontWeight: 700 }}>{l.title}</div>
            <div className="muted small" style={{ marginTop: 4 }}>{l.practice_lines.length} practice lines</div>
          </button>
        ))}
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <div className="flex-between">
          <p className="section-title" style={{ margin: 0 }}>{lesson.title}</p>
          <button type="button" onClick={() => setLesson(null)}>← All lessons</button>
        </div>
        <p style={{ marginBottom: 8 }}>{lesson.explanation}</p>
        <ul className="muted small" style={{ margin: 0, paddingLeft: 18 }}>
          {lesson.tips.map((t, i) => (
            <li key={i}>{t}</li>
          ))}
        </ul>
      </div>

      <div className="card">
        <p className="section-title">
          Practice line {lineIndex + 1} of {lesson.practice_lines.length}
        </p>
        <p style={{ fontSize: "1.12rem", margin: "0 0 4px" }}>{line?.text}</p>
        <p className="muted small" style={{ marginTop: 0 }}>🎯 {line?.note}</p>

        <div className="row">
          <button type="button" onClick={() => player.play(line!.text, 0.9)}>▶ Hear it</button>
          {recorder.status !== "recording" ? (
            <button type="button" className="primary" onClick={() => { player.stop(); setResult(null); recorder.start(); }} disabled={busy}>
              🎙️ Record
            </button>
          ) : (
            <button type="button" className="danger" onClick={submit}>
              <span className="recording-dot" aria-hidden="true" /> Stop & score
            </button>
          )}
          {busy && <span className="muted small">Scoring…</span>}
        </div>

        {recorder.error && <div className="error-box">{recorder.error}</div>}
        {error && <div className="error-box">{error}</div>}

        {result && (
          <div style={{ marginTop: 14 }} className="pop-in">
            <div className="row">
              <span className={`badge ${result.accuracy >= 85 ? "good" : result.accuracy >= 60 ? "warn" : "bad"}`}>
                {result.accuracy}% words
              </span>
              <span className={`badge ${result.fluency_score >= 75 ? "good" : "warn"}`}>{result.fluency_score}/100 flow</span>
            </div>
            <div style={{ marginTop: 10 }}>
              <DiffText diff={result.diff} />
            </div>
            <MetricChips metrics={result.metrics} />
            <div className="row" style={{ marginTop: 12 }}>
              <button type="button" onClick={() => { setResult(null); recorder.start(); }}>🔁 Again</button>
              {lineIndex < lesson.practice_lines.length - 1 && (
                <button
                  type="button"
                  className="primary"
                  onClick={() => { setLineIndex((i) => i + 1); setResult(null); recorder.reset(); }}
                >
                  Next line →
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

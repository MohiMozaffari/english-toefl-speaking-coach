import { useEffect, useMemo, useRef, useState } from "react";
import { api, ttsUrl } from "../api";
import { useRecorder } from "../hooks/useRecorder";
import { speak, stopSpeaking } from "../speech";
import { DiffText, LoadingCard, MetricChips, PageHeader } from "../components/ui";
import type { Accent, Passage, PassageSummary, ShadowingProgressRow, ShadowingResult } from "../types";

const RATES = [0.5, 0.75, 1, 1.25];
const ACCENTS: { value: Accent; label: string }[] = [
  { value: "en-US", label: "🇺🇸 US" },
  { value: "en-GB", label: "🇬🇧 UK" },
  { value: "en-AU", label: "🇦🇺 AU" },
];

const DIFF_BADGE: Record<string, string> = { beginner: "good", intermediate: "warn", academic: "bad" };

export default function Shadowing() {
  const [passages, setPassages] = useState<PassageSummary[]>([]);
  const [progress, setProgress] = useState<ShadowingProgressRow[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [passage, setPassage] = useState<Passage | null>(null);
  const [index, setIndex] = useState(0);
  const [rate, setRate] = useState(1);
  const [accent, setAccent] = useState<Accent>("en-US");
  const [loop, setLoop] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [usingFallbackVoice, setUsingFallbackVoice] = useState(false);
  const [result, setResult] = useState<ShadowingResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const recorder = useRecorder();
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const playTokenRef = useRef(0);

  useEffect(() => {
    api.getPassages().then(setPassages).catch((err) => setError(err.message));
    refreshProgress();
    return () => {
      stopSpeaking();
      audioRef.current?.pause();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refreshProgress = () => {
    api.getShadowingProgress().then(setProgress).catch(() => {});
  };

  const progressFor = (passageId: string) => {
    const rows = progress.filter((p) => p.passage_id === passageId);
    if (!rows.length) return null;
    const avg = rows.reduce((sum, r) => sum + r.best_accuracy, 0) / rows.length;
    return { practiced: rows.length, avgBest: Math.round(avg) };
  };

  const filtered = useMemo(
    () => passages.filter((p) => filter === "all" || p.difficulty === filter),
    [passages, filter]
  );

  const openPassage = async (id: string) => {
    setError(null);
    try {
      const full = await api.getPassage(id);
      setPassage(full);
      setAccent(full.preferred_accent);
      setIndex(0);
      setResult(null);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const sentence = passage?.sentences[index] ?? "";

  // Plays one sentence via the neural-voice endpoint (real Microsoft neural
  // voices, picked per accent). Falls back to the browser's speechSynthesis if
  // that endpoint can't be reached (offline, or edge-tts blocked on this
  // network) so shadowing still works without internet.
  const playOnceNeural = (): Promise<void> =>
    new Promise((resolve) => {
      const audio = audioRef.current;
      if (!audio) {
        resolve();
        return;
      }
      audio.src = ttsUrl(sentence, accent);
      audio.playbackRate = rate;
      const onDone = () => {
        audio.removeEventListener("ended", onDone);
        audio.removeEventListener("error", onError);
        resolve();
      };
      const onError = () => {
        audio.removeEventListener("ended", onDone);
        audio.removeEventListener("error", onError);
        setUsingFallbackVoice(true);
        speak(sentence, { rate, onEnd: resolve });
      };
      audio.addEventListener("ended", onDone);
      audio.addEventListener("error", onError);
      audio.play().catch(onError);
    });

  const playLooped = async () => {
    stopSpeaking();
    audioRef.current?.pause();
    setUsingFallbackVoice(false);
    setPlaying(true);
    const token = ++playTokenRef.current;
    // Loop plays up to 5 repeats; a plain play is a single pass.
    const repeats = loop ? 5 : 1;
    for (let i = 0; i < repeats; i++) {
      await playOnceNeural();
      if (playTokenRef.current !== token) return; // superseded (user navigated away)
      if (!loop) break;
    }
    setPlaying(false);
  };

  const startRecording = async () => {
    stopSpeaking();
    audioRef.current?.pause();
    playTokenRef.current++;
    setPlaying(false);
    setResult(null);
    setError(null);
    await recorder.start();
  };

  const stopAndScore = async () => {
    const blob = await recorder.stop();
    if (!blob || !passage) return;
    setBusy(true);
    try {
      const formData = new FormData();
      formData.append("audio", blob, "shadow.webm");
      formData.append("passage_id", passage.id);
      formData.append("sentence_index", String(index));
      const res = await api.submitShadowingAttempt(formData);
      setResult(res);
      refreshProgress();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const goTo = (i: number) => {
    stopSpeaking();
    audioRef.current?.pause();
    playTokenRef.current++;
    setPlaying(false);
    setIndex(i);
    setResult(null);
    recorder.reset();
  };

  // ---- Passage browser ----
  if (!passage) {
    return (
      <div>
        <PageHeader
          title="Shadowing"
          subtitle="Listen to a sentence, repeat it immediately, and get word-by-word feedback on accuracy and flow."
        />
        {error && <div className="error-box">{error}</div>}
        <div className="row" style={{ marginBottom: 14 }}>
          {["all", "beginner", "intermediate", "academic"].map((d) => (
            <button key={d} type="button" className={filter === d ? "primary small" : "small"} onClick={() => setFilter(d)}>
              {d === "all" ? "All levels" : d}
            </button>
          ))}
        </div>
        {!passages.length ? (
          <LoadingCard />
        ) : (
          <div className="grid cols-2">
            {filtered.map((p) => {
              const prog = progressFor(p.id);
              return (
                <button key={p.id} type="button" className="topic-item" onClick={() => openPassage(p.id)}>
                  <div className="flex-between">
                    <div className="cat">{p.category}</div>
                    <span className={`badge ${DIFF_BADGE[p.difficulty]}`}>{p.difficulty}</span>
                  </div>
                  <div style={{ fontWeight: 700 }}>{p.title}</div>
                  <div className="muted small" style={{ marginTop: 4 }}>
                    {p.sentence_count} sentences
                    {prog && ` · practiced ${prog.practiced}/${p.sentence_count} · best avg ${prog.avgBest}%`}
                  </div>
                  {prog && (
                    <div className="progress-track" style={{ marginTop: 8 }}>
                      <div
                        className={`progress-fill ${prog.avgBest >= 85 ? "good" : ""}`}
                        style={{ width: `${(prog.practiced / p.sentence_count) * 100}%` }}
                      />
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  // ---- Player ----
  const doneRow = progress.filter((p) => p.passage_id === passage.id);
  const bestForCurrent = doneRow.find((p) => p.sentence_index === index)?.best_accuracy;

  return (
    <div>
      <PageHeader
        title={passage.title}
        subtitle={`Sentence ${index + 1} of ${passage.sentences.length}`}
        actions={
          <button type="button" onClick={() => { stopSpeaking(); audioRef.current?.pause(); setPassage(null); refreshProgress(); }}>
            ← All passages
          </button>
        }
      />

      {/* Sentence dots */}
      <div className="row" style={{ marginBottom: 14 }}>
        {passage.sentences.map((_, i) => {
          const best = doneRow.find((p) => p.sentence_index === i)?.best_accuracy;
          const cls = best == null ? "neutral" : best >= 85 ? "good" : best >= 60 ? "warn" : "bad";
          return (
            <button
              key={i}
              type="button"
              className={`badge ${cls}`}
              style={{ cursor: "pointer", border: i === index ? "1px solid var(--accent)" : "1px solid transparent" }}
              onClick={() => goTo(i)}
              aria-label={`Go to sentence ${i + 1}${best != null ? `, best ${best}%` : ""}`}
            >
              {i + 1}
            </button>
          );
        })}
      </div>

      <div className="card">
        <audio ref={audioRef} preload="none" style={{ display: "none" }} />
        <p style={{ fontSize: "1.18rem", lineHeight: 1.6, marginTop: 0 }}>{sentence}</p>
        {bestForCurrent != null && (
          <p className="muted small">Your best on this sentence: {bestForCurrent}%</p>
        )}

        <div className="row" style={{ marginTop: 10 }}>
          <button type="button" className="primary" onClick={playLooped} disabled={playing || recorder.status === "recording"}>
            {playing ? "🔊 Playing…" : "▶ Play"}
          </button>
          <div className="row" role="group" aria-label="Voice accent">
            {ACCENTS.map((a) => (
              <button
                key={a.value}
                type="button"
                className={`small ${accent === a.value ? "primary" : ""}`}
                onClick={() => setAccent(a.value)}
              >
                {a.label}
              </button>
            ))}
          </div>
          <div className="row" role="group" aria-label="Playback speed">
            {RATES.map((r) => (
              <button key={r} type="button" className={`small ${rate === r ? "primary" : ""}`} onClick={() => setRate(r)}>
                {r}x
              </button>
            ))}
          </div>
          <label className="row small muted" style={{ margin: 0, cursor: "pointer" }}>
            <input type="checkbox" checked={loop} onChange={(e) => setLoop(e.target.checked)} style={{ width: "auto" }} />
            Loop
          </label>
        </div>
        {usingFallbackVoice && (
          <p className="faint small" style={{ marginTop: 6, marginBottom: 0 }}>
            Neural voice service unreachable — using your browser's built-in voice instead.
          </p>
        )}

        {recorder.error && <div className="error-box">{recorder.error}</div>}
        {error && <div className="error-box">{error}</div>}

        <div className="row" style={{ marginTop: 16 }}>
          {recorder.status !== "recording" ? (
            <button type="button" onClick={startRecording} disabled={busy}>
              🎙️ Record my repeat
            </button>
          ) : (
            <button type="button" className="danger" onClick={stopAndScore}>
              <span className="recording-dot" aria-hidden="true" /> Stop & score ({recorder.elapsed}s)
            </button>
          )}
          {busy && <span className="muted small">Scoring…</span>}
        </div>

        {result && (
          <div style={{ marginTop: 18 }} className="pop-in">
            <div className="row">
              <span className={`badge ${result.accuracy >= 85 ? "good" : result.accuracy >= 60 ? "warn" : "bad"}`}>
                {result.accuracy}% word accuracy
              </span>
              <span className={`badge ${result.fluency_score >= 75 ? "good" : result.fluency_score >= 50 ? "warn" : "bad"}`}>
                {result.fluency_score}/100 flow
              </span>
              {result.metrics.speech_span_seconds > 0 && (
                <span className="badge neutral">your take: {result.metrics.speech_span_seconds}s</span>
              )}
            </div>
            <div style={{ marginTop: 12 }}>
              <DiffText diff={result.diff} />
            </div>
            <p className="muted small" style={{ marginBottom: 0 }}>
              Heard: “{result.transcript || "—"}”
            </p>
            <MetricChips metrics={result.metrics} />
            <div className="row" style={{ marginTop: 14 }}>
              <button type="button" onClick={startRecording}>🔁 Try again</button>
              {index < passage.sentences.length - 1 ? (
                <button type="button" className="primary" onClick={() => goTo(index + 1)}>
                  Next sentence →
                </button>
              ) : (
                <button type="button" className="primary" onClick={() => { setPassage(null); refreshProgress(); }}>
                  ✅ Finish passage
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

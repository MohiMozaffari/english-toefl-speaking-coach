import { useEffect, useState } from "react";
import { api } from "../api";
import { useCountdown } from "../hooks/useCountdown";
import { LoadingCard, PageHeader } from "../components/ui";
import type { ReadingBlankItem, ReadingMCItem, ReadingResult, ReadingSet, ReadingTaskType, ToeflReadingTopics } from "../types";

const TASK_LABELS: Record<ReadingTaskType, string> = {
  complete_words: "Complete the Words",
  read_daily_life: "Read in Daily Life",
  read_academic: "Read an Academic Passage",
};

const TASK_DESCRIPTIONS: Record<ReadingTaskType, string> = {
  complete_words: "A short academic paragraph with 10 missing words. Type the full word for each blank using the letters shown as a hint.",
  read_daily_life: "A short everyday text -- an email, notice, or post -- followed by 2-3 comprehension questions.",
  read_academic: "A roughly 200-word academic passage followed by 5 comprehension questions covering the classic TOEFL question types.",
};

// Exam mode: an enforced time budget per set, loosely matched to real pacing.
// Practice mode has no timer at all.
const EXAM_SECONDS: Record<ReadingTaskType, number> = {
  complete_words: 180,
  read_daily_life: 180,
  read_academic: 480,
};

// Shown once per task type in Practice mode only, before the passage.
const PRACTICE_TIPS: Record<ReadingTaskType, string> = {
  complete_words: "Read the intact first sentence carefully -- it sets the topic and tone for every blank that follows.",
  read_daily_life: "Note the text type and purpose first, then scan for the specific detail each question asks about.",
  read_academic: "Read the whole passage once before answering -- note what each paragraph covers so you can find details fast.",
};

const STIMULUS_ICON: Record<string, string> = {
  email: "📧",
  notice: "📌",
  social_post: "📱",
};

type Mode = "practice" | "exam";
type Stage = "select_task" | "select_set" | "running" | "result";

// Splits a complete_words passage on {{b1}}, {{b2}}, ... tokens into alternating
// plain-text and blank-id segments, so blanks can be rendered as inline inputs.
function splitPassage(passage: string): (string | { blankId: string })[] {
  const parts: (string | { blankId: string })[] = [];
  const re = /\{\{(b\d+)\}\}/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = re.exec(passage))) {
    if (match.index > lastIndex) parts.push(passage.slice(lastIndex, match.index));
    parts.push({ blankId: match[1] });
    lastIndex = re.lastIndex;
  }
  if (lastIndex < passage.length) parts.push(passage.slice(lastIndex));
  return parts;
}

export default function Reading() {
  const [topics, setTopics] = useState<ToeflReadingTopics | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [mode, setMode] = useState<Mode>("practice");
  const [taskType, setTaskType] = useState<ReadingTaskType | null>(null);
  const [activeSet, setActiveSet] = useState<ReadingSet | null>(null);
  const [stage, setStage] = useState<Stage>("select_task");
  const [answers, setAnswers] = useState<(string | number | null)[]>([]);
  const [result, setResult] = useState<ReadingResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const countdown = useCountdown();

  useEffect(() => {
    api.getToeflReadingTopics().then(setTopics).catch((err) => setLoadError(err.message));
  }, []);

  const chooseTaskType = (tt: ReadingTaskType) => {
    setTaskType(tt);
    setStage("select_set");
  };

  const openSet = (set: ReadingSet) => {
    setActiveSet(set);
    setAnswers(new Array(set.items.length).fill(null));
    setResult(null);
    setError(null);
    setStage("running");
    if (mode === "exam") {
      countdown.start(EXAM_SECONDS[set.task_type], () => submit(set, undefined), true);
    }
  };

  const submit = async (set: ReadingSet, currentAnswers = answers) => {
    countdown.stop();
    setError(null);
    try {
      const res = await api.submitReadingAttempt(set.set_id, currentAnswers);
      setResult(res);
      setStage("result");
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const backToSets = () => {
    countdown.stop();
    setActiveSet(null);
    setResult(null);
    setStage("select_set");
  };

  const reset = () => {
    countdown.stop();
    setTaskType(null);
    setActiveSet(null);
    setResult(null);
    setStage("select_task");
  };

  if (loadError) return <div className="error-box">Could not load Reading content: {loadError}</div>;
  if (!topics) return <LoadingCard lines={4} />;

  const modeToggle = (
    <div className="row" role="group" aria-label="Practice or Exam mode">
      <button type="button" className={mode === "practice" ? "primary small" : "small"} onClick={() => setMode("practice")}>
        📝 Practice
      </button>
      <button type="button" className={mode === "exam" ? "primary small" : "small"} onClick={() => setMode("exam")}>
        ⏱️ Exam
      </button>
    </div>
  );

  const modeHint =
    mode === "practice"
      ? "Practice: no timer, tips before the passage, full answer key and explanations after you submit."
      : "Exam: the timer is enforced and auto-submits your answers, no tips, and explanations are withheld -- only your score is shown.";

  return (
    <div>
      <PageHeader
        title="TOEFL Reading Practice"
        subtitle="The redesigned TOEFL iBT Reading section (2026): Complete the Words, Read in Daily Life, Read an Academic Passage."
      />

      {(stage === "select_task" || stage === "select_set") && (
        <div className="card">
          <div className="flex-between">
            <p className="section-title" style={{ margin: 0 }}>Mode</p>
            {modeToggle}
          </div>
          <p className="muted small" style={{ marginBottom: 0 }}>{modeHint}</p>
        </div>
      )}

      {stage === "select_task" && (
        <div className="grid cols-2">
          {(Object.keys(TASK_LABELS) as ReadingTaskType[]).map((tt) => (
            <button key={tt} type="button" className="topic-item" onClick={() => chooseTaskType(tt)}>
              <div className="cat">{TASK_LABELS[tt]}</div>
              <div className="muted small">{TASK_DESCRIPTIONS[tt]}</div>
            </button>
          ))}
        </div>
      )}

      {stage === "select_set" && taskType && (
        <div className="card">
          <div className="flex-between">
            <p className="section-title" style={{ margin: 0 }}>{TASK_LABELS[taskType]}</p>
            <button type="button" onClick={() => setStage("select_task")}>← Change task type</button>
          </div>
          <div className="topic-list" style={{ marginTop: 14 }}>
            {topics[taskType].map((set) => (
              <button key={set.set_id} type="button" className="topic-item" onClick={() => openSet(set)}>
                <div className="cat">{set.items.length} {taskType === "complete_words" ? "blanks" : "questions"}</div>
                <div>{set.set_title}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {activeSet && stage === "running" && (
        <RunningSet
          set={activeSet}
          mode={mode}
          answers={answers}
          setAnswers={setAnswers}
          error={error}
          secondsLeft={countdown.secondsLeft}
          running={countdown.running}
          onBack={backToSets}
          onSubmit={() => submit(activeSet)}
        />
      )}

      {stage === "result" && result && activeSet && (
        <ResultView
          set={activeSet}
          result={result}
          mode={mode}
          onRetry={() => openSet(activeSet)}
          onBackToSets={backToSets}
          onChangeTaskType={reset}
        />
      )}
    </div>
  );
}

function RunningSet({
  set,
  mode,
  answers,
  setAnswers,
  error,
  secondsLeft,
  running,
  onBack,
  onSubmit,
}: {
  set: ReadingSet;
  mode: Mode;
  answers: (string | number | null)[];
  setAnswers: (fn: (prev: (string | number | null)[]) => (string | number | null)[]) => void;
  error: string | null;
  secondsLeft: number;
  running: boolean;
  onBack: () => void;
  onSubmit: () => void;
}) {
  const answeredAll = answers.every((a) => a !== null && a !== "");

  return (
    <div className="card">
      <div className="flex-between">
        <p className="section-title" style={{ margin: 0 }}>
          {TASK_LABELS[set.task_type]} — {set.set_title}
        </p>
        <div className="row">
          {mode === "exam" && running && <span className="badge info">⏱️ {secondsLeft}s</span>}
          <button type="button" onClick={onBack}>← Back</button>
        </div>
      </div>

      {mode === "practice" && (
        <div className="card sub" style={{ margin: "12px 0" }}>
          💡 <strong>Tip:</strong> {PRACTICE_TIPS[set.task_type]}
        </div>
      )}

      {set.task_type === "complete_words" ? (
        <CompleteWordsPassage set={set} answers={answers} setAnswers={setAnswers} />
      ) : (
        <McPassage set={set} answers={answers} setAnswers={setAnswers} />
      )}

      {error && <div className="error-box">{error}</div>}

      <button type="button" className="primary" onClick={onSubmit} disabled={!answeredAll} style={{ marginTop: 14 }}>
        {answeredAll ? "Check answers" : set.task_type === "complete_words" ? "Fill in every blank first" : "Answer every question first"}
      </button>
    </div>
  );
}

function CompleteWordsPassage({
  set,
  answers,
  setAnswers,
}: {
  set: ReadingSet;
  answers: (string | number | null)[];
  setAnswers: (fn: (prev: (string | number | null)[]) => (string | number | null)[]) => void;
}) {
  const items = set.items as ReadingBlankItem[];
  const indexByBlankId: Record<string, number> = {};
  items.forEach((item, i) => { indexByBlankId[item.blank_id] = i; });
  const segments = splitPassage(set.passage);

  return (
    <div className="transcript-box" style={{ lineHeight: 2.1 }}>
      {segments.map((seg, i) => {
        if (typeof seg === "string") return <span key={i}>{seg}</span>;
        const idx = indexByBlankId[seg.blankId];
        const item = items[idx];
        return (
          <input
            key={i}
            type="text"
            value={(answers[idx] as string) ?? ""}
            placeholder={item?.hint ?? ""}
            onChange={(e) => {
              const v = e.target.value;
              setAnswers((prev) => prev.map((a, j) => (j === idx ? v : a)));
            }}
            style={{ width: `${Math.max(6, (item?.hint?.length ?? 6) + 2)}ch`, margin: "0 4px", textAlign: "center" }}
          />
        );
      })}
    </div>
  );
}

function McPassage({
  set,
  answers,
  setAnswers,
}: {
  set: ReadingSet;
  answers: (string | number | null)[];
  setAnswers: (fn: (prev: (string | number | null)[]) => (string | number | null)[]) => void;
}) {
  const items = set.items as ReadingMCItem[];

  return (
    <>
      <div className="transcript-box" style={{ whiteSpace: "pre-wrap", margin: "14px 0" }}>
        {set.stimulus_kind && <div className="muted small" style={{ marginBottom: 6 }}>{STIMULUS_ICON[set.stimulus_kind] ?? "📄"} {set.stimulus_kind.replace("_", " ")}</div>}
        {set.passage}
      </div>
      {items.map((item, qi) => (
        <fieldset key={qi} style={{ border: "none", padding: 0, margin: "0 0 18px" }}>
          <legend style={{ fontWeight: 650, marginBottom: 8, padding: 0 }}>
            {qi + 1}. {item.question_text}
          </legend>
          {item.options.map((opt, oi) => (
            <label
              key={oi}
              className="row"
              style={{
                margin: "4px 0",
                padding: "8px 12px",
                borderRadius: 8,
                cursor: "pointer",
                background: "var(--panel-alt)",
                border: "1px solid var(--border)",
              }}
            >
              <input
                type="radio"
                name={`q${qi}`}
                style={{ width: "auto" }}
                checked={answers[qi] === oi}
                onChange={() => setAnswers((prev) => prev.map((a, j) => (j === qi ? oi : a)))}
              />
              <span>{opt}</span>
            </label>
          ))}
        </fieldset>
      ))}
    </>
  );
}

function ResultView({
  set,
  result,
  mode,
  onRetry,
  onBackToSets,
  onChangeTaskType,
}: {
  set: ReadingSet;
  result: ReadingResult;
  mode: Mode;
  onRetry: () => void;
  onBackToSets: () => void;
  onChangeTaskType: () => void;
}) {
  return (
    <div className="pop-in">
      <div className="card">
        <div className={result.score === result.total ? "success-box" : "card sub"} style={{ margin: 0 }}>
          {result.score === result.total ? "🎉 " : "📌 "}You got <strong>{result.score} / {result.total}</strong> correct
        </div>
      </div>

      <div className="card">
        <p className="section-title">{set.task_type === "complete_words" ? "Blank by blank" : "Question by question"}</p>
        {result.detail.map((d, i) => {
          const options = set.task_type === "complete_words" ? null : (set.items[i] as ReadingMCItem).options;
          const label = (v: string | number | null) => {
            if (v === null || v === "") return "(blank)";
            if (options && typeof v === "number") return options[v] ?? String(v);
            return String(v);
          };
          return (
            <div className="correction-row" key={i}>
              <div className="flex-between">
                <strong>{d.blank_id ? `Blank ${i + 1}` : `${i + 1}. ${d.question_text}`}</strong>
                <span className={`badge ${d.correct ? "good" : "bad"}`}>{d.correct ? "Correct" : "Incorrect"}</span>
              </div>
              <p className="small" style={{ margin: "4px 0 0" }}>
                <span className="said">Your answer:</span> {label(d.given)}
                {!d.correct && <> — <span className="better">Correct answer:</span> {label(d.correct_answer)}</>}
              </p>
              {mode === "practice" && <p className="muted small" style={{ margin: "2px 0 0" }}>{d.explanation}</p>}
            </div>
          );
        })}
      </div>

      <div className="row" style={{ marginTop: 16 }}>
        <button type="button" className="primary" onClick={onRetry}>🔁 Try again</button>
        <button type="button" onClick={onBackToSets}>← Another set</button>
        <button type="button" onClick={onChangeTaskType}>Change task type</button>
      </div>
    </div>
  );
}

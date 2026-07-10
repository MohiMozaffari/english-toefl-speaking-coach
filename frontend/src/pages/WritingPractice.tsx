import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { LoadingCard, PageHeader, ReplayButton, ScoreBadge, scoreBadgeClass } from "../components/ui";
import type {
  AcademicDiscussionItem,
  BuildSentenceItem,
  BuildSentenceResult,
  ToeflWritingTopics,
  WriteEmailItem,
  WritingAttemptResponse,
  WritingTaskType,
} from "../types";

const TASK_LABELS: Record<WritingTaskType, string> = {
  build_sentence: "Build a Sentence",
  write_email: "Write an Email",
  academic_discussion: "Write for an Academic Discussion",
};

const TASK_DESCRIPTIONS: Record<WritingTaskType, string> = {
  build_sentence: "You'll see a short exchange with the second line scrambled into word chips. Tap them in order to build a grammatically correct, contextually appropriate sentence. Auto-scored, correct or incorrect.",
  write_email: "You'll read a short campus-life scenario and a list of required points, then write an email response. Graded by AI against the real TOEFL rubric, with a full model answer.",
  academic_discussion: "You'll read a professor's discussion question and two classmates' posts, then write your own contribution. Graded by AI against the real TOEFL rubric, with a full model answer.",
};

type Stage = "select_task" | "select_item";

export default function WritingPractice() {
  const [topics, setTopics] = useState<ToeflWritingTopics | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [taskType, setTaskType] = useState<WritingTaskType | null>(null);
  const [stage, setStage] = useState<Stage>("select_task");

  useEffect(() => {
    api.getToeflWritingTopics().then(setTopics).catch((err) => setLoadError(err.message));
  }, []);

  const chooseTaskType = (tt: WritingTaskType) => {
    setTaskType(tt);
    setStage("select_item");
  };

  if (loadError) return <div className="error-box">Could not load Writing content: {loadError}</div>;
  if (!topics) return <LoadingCard lines={4} />;

  return (
    <div>
      <PageHeader
        title="TOEFL Writing Practice"
        subtitle="The redesigned TOEFL iBT Writing section (2026): Build a Sentence, Write an Email, Write for an Academic Discussion."
      />

      {stage === "select_task" && (
        <div className="grid cols-2">
          {(Object.keys(TASK_LABELS) as WritingTaskType[]).map((tt) => (
            <button key={tt} type="button" className="topic-item" onClick={() => chooseTaskType(tt)}>
              <div className="cat">{TASK_LABELS[tt]}</div>
              <div className="muted small">{TASK_DESCRIPTIONS[tt]}</div>
            </button>
          ))}
        </div>
      )}

      {stage === "select_item" && taskType && (
        <ItemPicker taskType={taskType} topics={topics} onChangeTaskType={() => setStage("select_task")} />
      )}
    </div>
  );
}

function ItemPicker({
  taskType,
  topics,
  onChangeTaskType,
}: {
  taskType: WritingTaskType;
  topics: ToeflWritingTopics;
  onChangeTaskType: () => void;
}) {
  const [activeId, setActiveId] = useState<string | null>(null);

  if (activeId) {
    if (taskType === "build_sentence") {
      const item = topics.build_sentence.find((i) => i.id === activeId)!;
      return (
        <BuildSentenceRunner
          item={item}
          onDone={() => setActiveId(null)}
          onChangeTaskType={onChangeTaskType}
        />
      );
    }
    const item =
      taskType === "write_email"
        ? topics.write_email.find((i) => i.id === activeId)!
        : topics.academic_discussion.find((i) => i.id === activeId)!;
    return (
      <EssayRunner
        taskType={taskType}
        item={item}
        onDone={() => setActiveId(null)}
        onChangeTaskType={onChangeTaskType}
      />
    );
  }

  const items =
    taskType === "build_sentence" ? topics.build_sentence : taskType === "write_email" ? topics.write_email : topics.academic_discussion;

  return (
    <div className="card">
      <div className="flex-between">
        <p className="section-title" style={{ margin: 0 }}>{TASK_LABELS[taskType]}</p>
        <button type="button" onClick={onChangeTaskType}>← Change task type</button>
      </div>
      <div className="topic-list" style={{ marginTop: 14 }}>
        {items.map((item) => (
          <button key={item.id} type="button" className="topic-item" onClick={() => setActiveId(item.id)}>
            <div className="cat">{taskType === "build_sentence" ? "Rearrange the words" : "Write a response"}</div>
            <div>
              {taskType === "build_sentence"
                ? (item as BuildSentenceItem).context_line
                : taskType === "write_email"
                  ? (item as WriteEmailItem).situation
                  : (item as AcademicDiscussionItem).professor_prompt}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

// --- Build a Sentence: tap word chips in order, auto-scored ---------------------

function BuildSentenceRunner({
  item,
  onDone,
  onChangeTaskType,
}: {
  item: BuildSentenceItem;
  onDone: () => void;
  onChangeTaskType: () => void;
}) {
  const [picked, setPicked] = useState<number[]>([]); // indices into item.words, in pick order
  const [result, setResult] = useState<BuildSentenceResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const pick = (idx: number) => setPicked((prev) => [...prev, idx]);
  const unpick = (posInPicked: number) => setPicked((prev) => prev.filter((_, i) => i !== posInPicked));
  const clear = () => setPicked([]);

  const submit = async () => {
    setError(null);
    try {
      const tokens = picked.map((i) => item.words[i]);
      const res = await api.submitBuildSentence(item.id, tokens);
      setResult(res);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const remainingIdx = item.words.map((_, i) => i).filter((i) => !picked.includes(i));

  return (
    <div className="card">
      <div className="flex-between">
        <p className="section-title" style={{ margin: 0 }}>Build a Sentence</p>
        <button type="button" onClick={onDone}>← Back to list</button>
      </div>

      <div className="transcript-box" style={{ margin: "14px 0" }}>{item.context_line}</div>

      <p className="muted small">Tap the words in order to build the reply:</p>
      <div className="row" style={{ minHeight: 40, flexWrap: "wrap" }}>
        {picked.length === 0 && <span className="muted small">(nothing picked yet)</span>}
        {picked.map((idx, pos) => (
          <button
            key={pos}
            type="button"
            className="badge info"
            style={{ cursor: result ? "default" : "pointer" }}
            onClick={() => !result && unpick(pos)}
            disabled={!!result}
          >
            {item.words[idx]}
          </button>
        ))}
      </div>

      <p className="muted small" style={{ marginTop: 14 }}>Word bank (one word may be extra and not needed):</p>
      <div className="row" style={{ flexWrap: "wrap" }}>
        {remainingIdx.map((idx) => (
          <button key={idx} type="button" className="badge neutral" onClick={() => pick(idx)} disabled={!!result}>
            {item.words[idx]}
          </button>
        ))}
      </div>

      {error && <div className="error-box">{error}</div>}

      {!result ? (
        <div className="row" style={{ marginTop: 16 }}>
          <button type="button" className="primary" onClick={submit} disabled={picked.length === 0}>
            Check answer
          </button>
          <button type="button" onClick={clear} disabled={picked.length === 0}>Reset</button>
        </div>
      ) : (
        <div className="pop-in" style={{ marginTop: 16 }}>
          <div className={result.correct ? "success-box" : "card sub"}>
            {result.correct ? "🎉 Correct!" : "📌 Not quite."}
          </div>
          {!result.correct && (
            <p className="small" style={{ marginTop: 8 }}>
              <span className="better">Correct order:</span> {result.answer.join(" ")}
            </p>
          )}
          <p className="muted small" style={{ marginTop: 8 }}>{result.explanation}</p>
          <div className="row" style={{ marginTop: 12 }}>
            <button type="button" className="primary" onClick={() => { setResult(null); clear(); }}>🔁 Try again</button>
            <button type="button" onClick={onDone}>Next item →</button>
            <button type="button" onClick={onChangeTaskType}>Change task type</button>
          </div>
        </div>
      )}
    </div>
  );
}

// --- Write an Email / Academic Discussion: textarea, LLM-graded ------------------

function EssayRunner({
  taskType,
  item,
  onDone,
  onChangeTaskType,
}: {
  taskType: "write_email" | "academic_discussion";
  item: WriteEmailItem | AcademicDiscussionItem;
  onDone: () => void;
  onChangeTaskType: () => void;
}) {
  const [text, setText] = useState("");
  const [result, setResult] = useState<WritingAttemptResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const minWords = item.min_words;

  const submit = async () => {
    setError(null);
    setSubmitting(true);
    try {
      const res = await api.submitWritingAttempt(item.id, text);
      setResult(res);
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    return (
      <WritingResultView
        taskType={taskType}
        result={result}
        onRetry={() => { setResult(null); setText(""); }}
        onDone={onDone}
        onChangeTaskType={onChangeTaskType}
      />
    );
  }

  return (
    <div className="card">
      <div className="flex-between">
        <p className="section-title" style={{ margin: 0 }}>{TASK_LABELS[taskType]}</p>
        <button type="button" onClick={onDone}>← Back to list</button>
      </div>

      {taskType === "write_email" ? (
        <>
          <div className="transcript-box" style={{ margin: "14px 0" }}>{(item as WriteEmailItem).situation}</div>
          <div className="card sub" style={{ whiteSpace: "pre-wrap" }}>{(item as WriteEmailItem).email_prompt}</div>
        </>
      ) : (
        <>
          <div className="transcript-box" style={{ margin: "14px 0" }}>{(item as AcademicDiscussionItem).professor_prompt}</div>
          {(item as AcademicDiscussionItem).classmate_posts.map((p, i) => (
            <div className="card sub" key={i} style={{ marginBottom: 8 }}>
              <strong>{p.name}</strong>
              <p className="small" style={{ margin: "4px 0 0" }}>{p.text}</p>
            </div>
          ))}
        </>
      )}

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={10}
        placeholder="Write your response here…"
        style={{ width: "100%", marginTop: 14, fontFamily: "inherit", fontSize: "1em" }}
      />
      <p className="muted small" style={{ marginTop: 4 }}>
        {wordCount} words {wordCount < minWords && `(aim for at least ${minWords})`}
      </p>

      {error && <div className="error-box">{error}</div>}

      <button type="button" className="primary" onClick={submit} disabled={submitting || wordCount === 0} style={{ marginTop: 10 }}>
        {submitting ? "Grading…" : "Submit for AI feedback"}
      </button>
    </div>
  );
}

function WritingResultView({
  taskType,
  result,
  onRetry,
  onDone,
  onChangeTaskType,
}: {
  taskType: "write_email" | "academic_discussion";
  result: WritingAttemptResponse;
  onRetry: () => void;
  onDone: () => void;
  onChangeTaskType: () => void;
}) {
  const fb = result.feedback;
  const prevAttempts = result.previous_attempts.filter((a) => a.id !== result.session_id);

  return (
    <div className="pop-in">
      <div className="card">
        <div className="flex-between">
          <p className="section-title" style={{ margin: 0 }}>Score: {fb.score_band} / 6</p>
          <ScoreBadge score={fb.score_band} />
        </div>
        <p className="muted">{fb.score_reason}</p>

        {prevAttempts.length > 0 && (
          <div className="card sub" style={{ marginTop: 14, marginBottom: 0 }}>
            <p className="section-title" style={{ marginBottom: 8 }}>📈 Over time</p>
            <div className="row">
              {result.previous_attempts.map((a) => (
                <span
                  key={a.id}
                  className={`badge ${a.id === result.session_id ? "info" : scoreBadgeClass(a.score_band)}`}
                  title={new Date(a.created_at).toLocaleString()}
                >
                  {a.id === result.session_id ? `now: ${a.score_band}` : a.score_band}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="grid cols-2">
        <div className="card" style={{ margin: 0 }}>
          <p className="section-title">✅ What went well</p>
          <p className="small" style={{ margin: 0 }}>{fb.what_went_well || "—"}</p>
        </div>
        <div className="card" style={{ margin: 0 }}>
          <p className="section-title">⚠️ Biggest weakness</p>
          <p className="small" style={{ margin: 0 }}>{fb.biggest_weakness || "—"}</p>
        </div>
      </div>

      <div className="card" style={{ marginTop: 14 }}>
        <div className="grid cols-3">
          <div>
            <strong>Task achievement</strong>
            <p className="muted small">{fb.task_achievement}</p>
          </div>
          <div>
            <strong>Language use</strong>
            <p className="muted small">{fb.language_use}</p>
          </div>
          <div>
            <strong>Organization</strong>
            <p className="muted small">{fb.organization}</p>
          </div>
        </div>
      </div>

      {fb.model_answer && (
        <div className="card sub">
          <div className="flex-between">
            <p className="section-title" style={{ margin: 0 }}>🏆 Band-6 model answer</p>
            <ReplayButton text={fb.model_answer} />
          </div>
          <p className="small" style={{ whiteSpace: "pre-wrap" }}>{fb.model_answer}</p>
        </div>
      )}

      <div className="card sub">
        <p className="section-title">🧗 How to improve</p>
        <p className="small">{fb.how_to_improve}</p>
        {fb.suggested_exercises && fb.suggested_exercises.length > 0 && (
          <ul className="small muted" style={{ margin: "6px 0 0", paddingLeft: 18 }}>
            {fb.suggested_exercises.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        )}
        <p style={{ marginTop: 12 }}><strong>🎯 Focus next time:</strong> {fb.focus_next}</p>
      </div>

      <div className="row" style={{ marginTop: 16 }}>
        <button type="button" className="primary" onClick={onRetry}>🔁 Redo this prompt</button>
        <button type="button" onClick={onDone}>Try another prompt</button>
        <button type="button" onClick={onChangeTaskType}>Change task type ({TASK_LABELS[taskType]})</button>
      </div>
    </div>
  );
}

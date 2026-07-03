// Shared API types mirroring the FastAPI backend's JSON shapes.

export interface Metrics {
  word_count: number;
  duration_seconds: number;
  speech_span_seconds: number;
  wpm: number;
  articulation_wpm: number;
  pause_count: number;
  long_pause_count: number;
  total_pause_seconds: number;
  avg_pause_seconds: number;
  filler_count: number;
  type_token_ratio: number;
  unique_word_count: number;
  avg_word_confidence: number;
  low_confidence_words: { word: string; confidence: number }[];
}

export interface CategoryScores {
  [key: string]: number;
}

export interface GeneralFeedback {
  encouragement: string;
  what_went_well?: string;
  grammar_feedback: string;
  vocabulary_feedback: string;
  clarity_feedback: string;
  improved_version: string;
  overall_tip: string;
  category_scores?: CategoryScores;
}

export interface ListenRepeatItem {
  target: string;
  said: string;
  match_quality: string;
  tip: string;
}

export interface InterviewItem {
  question: string;
  said: string;
  better_response: string;
  why: string;
}

export interface ToeflFeedback {
  score_band: number;
  score_reason: string;
  what_went_well?: string;
  biggest_weakness?: string;
  accuracy?: string;
  fluency?: string;
  coherence?: string;
  pronunciation_delivery?: string;
  items?: (ListenRepeatItem | InterviewItem)[];
  how_to_improve?: string;
  suggested_exercises?: string[];
  focus_next: string;
  category_scores?: CategoryScores;
}

export interface GeneralTopic {
  id: string;
  category: string;
  prompt: string;
}

export interface ListenRepeatSet {
  id: string;
  task: "listen_repeat";
  title: string;
  picture_caption: string;
  sentences: string[];
}

export interface InterviewSet {
  id: string;
  task: "interview";
  title: string;
  questions: string[];
}

export type ToeflSet = ListenRepeatSet | InterviewSet;

export interface ToeflTopics {
  tasks: { listen_repeat: ListenRepeatSet[]; interview: InterviewSet[] };
  timing: { listen_repeat: { item_seconds: number[] }; interview: { item_seconds: number[] } };
}

export interface AttemptSummary {
  id: number;
  created_at: string;
  score_band: number | null;
  metrics: Metrics | null;
}

export interface ToeflAttemptResponse {
  session_id: number;
  transcript: string;
  feedback: ToeflFeedback;
  metrics: Metrics;
  previous_attempts: AttemptSummary[];
}

export interface GeneralAttemptResponse {
  session_id: number;
  transcript: string;
  feedback: GeneralFeedback;
  metrics: Metrics;
}

export interface SessionSummary {
  id: number;
  created_at: string;
  mode: "general" | "toefl";
  task_type: string;
  task_title: string;
  score_band: number | null;
  prompt_ref: string | null;
}

export interface SessionDetailData extends SessionSummary {
  task_prompt: string;
  transcript: string;
  feedback: GeneralFeedback & ToeflFeedback;
  metrics: Metrics | null;
  other_attempts?: AttemptSummary[];
}

export interface Profile {
  id: number;
  name: string;
  created_at: string;
  daily_goal_xp: number;
}

export interface Achievement {
  id: string;
  icon: string;
  title: string;
  description: string;
  earned: boolean;
  earned_at: string | null;
}

export interface Weakness {
  tag: string;
  label: string;
  evidence: string;
}

export interface Recommendation {
  title: string;
  reason: string;
  module: string;
  route: string;
  action: string;
}

export interface DashboardData {
  profile: Profile;
  xp: { total: number; level: number; xp_into_level: number; xp_for_next: number; today: number; daily_goal: number };
  streak: { current: number; best: number; active_today: boolean };
  totals: { sessions: number; minutes_spoken: number; words_spoken: number; shadowing_attempts: number; pair_attempts: number };
  weekly: { date: string; xp: number; activities: number }[];
  score_trend: { id: number; created_at: string; task_type: string; score_band: number }[];
  radar: { axis: string; value: number | null }[];
  delivery_trend: { created_at: string; wpm: number; pauses: number; ttr: number; confidence: number }[];
  weaknesses: Weakness[];
  recommendations: Recommendation[];
  achievements: Achievement[];
  weak_contrasts: { contrast: string; attempts: number; correct: number; accuracy: number }[];
}

export type Accent = "en-US" | "en-GB" | "en-AU";

export interface PassageSummary {
  id: string;
  title: string;
  difficulty: "beginner" | "intermediate" | "academic";
  category: string;
  full_transcript: string;
  preferred_accent: Accent;
  audio_url: string | null;
  sentence_count: number;
}

export interface Passage extends Omit<PassageSummary, "sentence_count"> {
  sentences: string[];
}

export interface WordDiff {
  target_words: { word: string; status: "matched" | "close" | "missing" }[];
  extra_words: string[];
  matched: number;
  close: number;
  missing: number;
  accuracy: number;
}

export interface ShadowingResult {
  target: string;
  transcript: string;
  diff: WordDiff;
  accuracy: number;
  fluency_score: number;
  metrics: Metrics;
}

export interface ShadowingProgressRow {
  passage_id: string;
  sentence_index: number;
  best_accuracy: number;
  attempts: number;
}

export interface IpaSound {
  symbol: string;
  name: string;
  examples: string[];
  tip: string;
}

export interface MinimalPairSet {
  id: string;
  contrast: string;
  label: string;
  description: string;
  pairs: [string, string][];
}

export interface Lesson {
  id: string;
  title: string;
  focus: string;
  explanation: string;
  tips: string[];
  practice_lines: { text: string; note: string }[];
}

export interface PronunciationContent {
  vowels: IpaSound[];
  consonants: IpaSound[];
  minimal_pairs: MinimalPairSet[];
  lessons: Lesson[];
}

export interface PairVerdict {
  verdict: "correct" | "incorrect" | "unclear";
  target_word: string;
  counterpart: string;
  heard: string | null;
  transcript: string;
}

export interface ContrastStats {
  contrast: string;
  attempts: number;
  correct: number;
  accuracy: number;
}

export interface ListeningItemSummary {
  id: string;
  title: string;
  type: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  audio_url: string | null;
  segment_count: number;
  question_count: number;
}

export interface ListeningItem extends Omit<ListeningItemSummary, "segment_count" | "question_count"> {
  segments: { speaker: string; text: string }[];
  questions: { q: string; options: string[] }[];
}

export interface QuizResult {
  score: number;
  total: number;
  detail: { question: string; given: number | null; correct_answer: number; correct: boolean }[];
}

export interface HealthStatus {
  llm: { reachable: boolean | null; key_valid: boolean | null; message: string };
  whisper: { installed: boolean; message: string };
}

export interface Settings {
  base_url: string;
  api_key: string;
  model: string;
  whisper_model: string;
}

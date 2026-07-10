import type {
  ContrastStats,
  DashboardData,
  GeneralAttemptResponse,
  GeneralTopic,
  HealthStatus,
  ListeningItem,
  ListeningItemSummary,
  PairVerdict,
  Passage,
  PassageSummary,
  PronunciationContent,
  QuizResult,
  ReadingResult,
  Recommendation,
  SessionDetailData,
  SessionSummary,
  Settings,
  ShadowingProgressRow,
  ShadowingResult,
  ToeflAttemptResponse,
  ToeflReadingTopics,
  ToeflTopics,
} from "./types";

const BASE_URL = "http://localhost:8001";

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(message: string, code: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.ok) {
    return res.json() as Promise<T>;
  }
  let body: { error?: { message?: string; code?: string } } | undefined;
  try {
    body = await res.json();
  } catch {
    throw new ApiError(`Request failed with status ${res.status}`, "unknown", res.status);
  }
  const err = body?.error;
  throw new ApiError(err?.message || "Request failed", err?.code || "unknown", res.status);
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);
  return handleResponse<T>(res);
}

async function postJson<T>(path: string, data: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<T>(res);
}

async function postForm<T>(path: string, formData: FormData): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, { method: "POST", body: formData });
  return handleResponse<T>(res);
}

/** URL for an <audio> element to fetch neural TTS directly (GET, browser-cacheable).
 *  Pass an explicit `voice` to override the accent's default (e.g. to give each
 *  speaker in a conversation a distinct voice). */
function ttsUrl(text: string, accent: string, voice?: string): string {
  const params = new URLSearchParams({ text, accent });
  if (voice) params.set("voice", voice);
  return `${BASE_URL}/api/shadowing/tts?${params.toString()}`;
}

export const api = {
  // Settings & health
  getSettings: () => get<Settings>("/api/settings"),
  saveSettings: (settings: Partial<Settings>) => postJson<Settings>("/api/settings", settings),
  getHealth: () => get<HealthStatus>("/api/health"),

  // Content
  getGeneralTopics: () => get<GeneralTopic[]>("/api/topics/general"),
  getToeflTopics: () => get<ToeflTopics>("/api/topics/toefl"),
  getPassages: () => get<PassageSummary[]>("/api/shadowing/passages"),
  getPassage: (id: string) => get<Passage>(`/api/shadowing/passages/${id}`),
  getPronunciationContent: () => get<PronunciationContent>("/api/pronunciation/content"),
  getListeningItems: () => get<ListeningItemSummary[]>("/api/listening/items"),
  getListeningItem: (id: string) => get<ListeningItem>(`/api/listening/items/${id}`),
  getToeflReadingTopics: () => get<ToeflReadingTopics>("/api/topics/toefl-reading"),

  // Practice
  submitGeneralAttempt: (formData: FormData) =>
    postForm<GeneralAttemptResponse>("/api/practice/general/attempt", formData),
  submitToeflAttempt: (formData: FormData) =>
    postForm<ToeflAttemptResponse>("/api/practice/toefl/attempt", formData),
  submitShadowingAttempt: (formData: FormData) => postForm<ShadowingResult>("/api/shadowing/attempt", formData),
  submitPairAttempt: (formData: FormData) => postForm<PairVerdict>("/api/pronunciation/pair-attempt", formData),
  submitLineAttempt: (formData: FormData) => postForm<ShadowingResult>("/api/pronunciation/line-attempt", formData),
  submitListeningQuiz: (itemId: string, answers: (number | null)[]) =>
    postJson<QuizResult>("/api/listening/submit", { item_id: itemId, answers }),
  submitReadingAttempt: (setId: string, answers: (string | number | null)[]) =>
    postJson<ReadingResult>("/api/reading/submit", { set_id: setId, answers }),

  // Progress & analytics
  getShadowingProgress: () => get<ShadowingProgressRow[]>("/api/shadowing/progress"),
  getPronunciationStats: () => get<ContrastStats[]>("/api/pronunciation/stats"),
  getSessions: (mode?: string) => get<SessionSummary[]>(`/api/sessions${mode ? `?mode=${mode}` : ""}`),
  getSession: (id: string | number) => get<SessionDetailData>(`/api/sessions/${id}`),
  getDashboard: () => get<DashboardData>("/api/stats/dashboard"),
  getRecommendations: () => get<Recommendation[]>("/api/coach/recommendations"),
};

export { BASE_URL, ttsUrl };

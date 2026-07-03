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
  Profile,
  PronunciationContent,
  QuizResult,
  Recommendation,
  SessionDetailData,
  SessionSummary,
  Settings,
  ShadowingProgressRow,
  ShadowingResult,
  ToeflAttemptResponse,
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

const profileQS = (profileId?: number) => (profileId ? `?profile_id=${profileId}` : "");

/** URL for an <audio> element to fetch neural TTS directly (GET, browser-cacheable). */
function ttsUrl(text: string, accent: string): string {
  const params = new URLSearchParams({ text, accent });
  return `${BASE_URL}/api/shadowing/tts?${params.toString()}`;
}

export const api = {
  // Settings & health
  getSettings: () => get<Settings>("/api/settings"),
  saveSettings: (settings: Partial<Settings>) => postJson<Settings>("/api/settings", settings),
  getHealth: () => get<HealthStatus>("/api/health"),

  // Profiles
  getProfiles: () => get<Profile[]>("/api/profiles"),
  createProfile: (name: string) => postJson<Profile>("/api/profiles", { name }),
  updateProfile: (id: number, data: { name?: string; daily_goal_xp?: number }) =>
    postJson<Profile>(`/api/profiles/${id}`, data),

  // Content
  getGeneralTopics: () => get<GeneralTopic[]>("/api/topics/general"),
  getToeflTopics: () => get<ToeflTopics>("/api/topics/toefl"),
  getPassages: () => get<PassageSummary[]>("/api/shadowing/passages"),
  getPassage: (id: string) => get<Passage>(`/api/shadowing/passages/${id}`),
  getPronunciationContent: () => get<PronunciationContent>("/api/pronunciation/content"),
  getListeningItems: () => get<ListeningItemSummary[]>("/api/listening/items"),
  getListeningItem: (id: string) => get<ListeningItem>(`/api/listening/items/${id}`),

  // Practice
  submitGeneralAttempt: (formData: FormData) =>
    postForm<GeneralAttemptResponse>("/api/practice/general/attempt", formData),
  submitToeflAttempt: (formData: FormData) =>
    postForm<ToeflAttemptResponse>("/api/practice/toefl/attempt", formData),
  submitShadowingAttempt: (formData: FormData) => postForm<ShadowingResult>("/api/shadowing/attempt", formData),
  submitPairAttempt: (formData: FormData) => postForm<PairVerdict>("/api/pronunciation/pair-attempt", formData),
  submitLineAttempt: (formData: FormData) => postForm<ShadowingResult>("/api/pronunciation/line-attempt", formData),
  submitListeningQuiz: (itemId: string, answers: (number | null)[], profileId?: number) =>
    postJson<QuizResult>("/api/listening/submit", { item_id: itemId, answers, profile_id: profileId }),

  // Progress & analytics
  getShadowingProgress: (profileId?: number) =>
    get<ShadowingProgressRow[]>(`/api/shadowing/progress${profileQS(profileId)}`),
  getPronunciationStats: (profileId?: number) =>
    get<ContrastStats[]>(`/api/pronunciation/stats${profileQS(profileId)}`),
  getSessions: (mode?: string, profileId?: number) => {
    const params = new URLSearchParams();
    if (mode) params.set("mode", mode);
    if (profileId) params.set("profile_id", String(profileId));
    const qs = params.toString();
    return get<SessionSummary[]>(`/api/sessions${qs ? `?${qs}` : ""}`);
  },
  getSession: (id: string | number) => get<SessionDetailData>(`/api/sessions/${id}`),
  getDashboard: (profileId?: number) => get<DashboardData>(`/api/stats/dashboard${profileQS(profileId)}`),
  getRecommendations: (profileId?: number) =>
    get<Recommendation[]>(`/api/coach/recommendations${profileQS(profileId)}`),
};

export { BASE_URL, ttsUrl };

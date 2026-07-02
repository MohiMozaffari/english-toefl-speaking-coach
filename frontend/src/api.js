const BASE_URL = "http://localhost:8000";

class ApiError extends Error {
  constructor(message, code, status) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

async function handleResponse(res) {
  if (res.ok) {
    if (res.status === 204) return null;
    return res.json();
  }
  let body;
  try {
    body = await res.json();
  } catch {
    throw new ApiError(`Request failed with status ${res.status}`, "unknown", res.status);
  }
  const err = body?.error;
  throw new ApiError(err?.message || "Request failed", err?.code || "unknown", res.status);
}

async function get(path) {
  const res = await fetch(`${BASE_URL}${path}`);
  return handleResponse(res);
}

async function postJson(path, data) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

async function postForm(path, formData) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    body: formData,
  });
  return handleResponse(res);
}

export const api = {
  getSettings: () => get("/api/settings"),
  saveSettings: (settings) => postJson("/api/settings", settings),
  getHealth: () => get("/api/health"),
  getGeneralTopics: () => get("/api/topics/general"),
  getToeflTopics: () => get("/api/topics/toefl"),
  submitGeneralAttempt: (formData) => postForm("/api/practice/general/attempt", formData),
  submitToeflAttempt: (formData) => postForm("/api/practice/toefl/attempt", formData),
  getSessions: (mode) => get(`/api/sessions${mode ? `?mode=${mode}` : ""}`),
  getSession: (id) => get(`/api/sessions/${id}`),
  getToeflStats: () => get("/api/stats/toefl"),
};

export { ApiError, BASE_URL };

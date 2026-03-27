const envBase = import.meta.env.VITE_API_BASE_URL;
const isLocalhost =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1";

const API_BASE = (
  envBase || (isLocalhost ? "http://localhost:8000" : "https://sql-coach-app.onrender.com")
).replace(/\/$/, "");

async function handleJson(res, fallbackMessage) {
  if (!res.ok) {
    let err = {};
    try {
      err = await res.json();
    } catch {
      // ignore parse failure
    }
    throw new Error(err.detail || fallbackMessage);
  }
  return res.json();
}

function fetchWithTimeout(url, options = {}, timeout = 15000) {
  return Promise.race([
    fetch(url, options),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error("Request timed out")), timeout)
    ),
  ]);
}

export async function startSession() {
  const res = await fetchWithTimeout(`${API_BASE}/start`, {
    method: "POST",
  });
  return handleJson(res, "Could not start session");
}

export async function getConceptIntro(sessionId) {
  const res = await fetchWithTimeout(`${API_BASE}/concept-intro/${sessionId}`, {
    method: "POST",
  });
  return handleJson(res, "Could not load concept intro");
}

export async function submitTurn(sessionId, payload) {
  const res = await fetchWithTimeout(`${API_BASE}/submit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
      message: payload,
    }),
  });
  return handleJson(res, "Submission failed");
}

export async function resumeSession(sessionId) {
  const res = await fetchWithTimeout(`${API_BASE}/resume/${sessionId}`);
  return handleJson(res, "Could not resume session");
}

export async function resumeFromReport(reportText) {
  const res = await fetchWithTimeout(`${API_BASE}/resume-from-report`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: "",
      saved_report_text: reportText,
    }),
  });
  return handleJson(res, "Could not resume from report");
}

export async function getReport(sessionId) {
  const res = await fetchWithTimeout(`${API_BASE}/report/${sessionId}`);
  return handleJson(res, "Could not load report");
}

export async function sendSupportChat(payload) {
  const res = await fetchWithTimeout(`${API_BASE}/support-chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return handleJson(res, "Could not get support chat response");
}
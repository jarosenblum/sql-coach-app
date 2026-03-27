const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function handleJson(res, fallbackMessage) {
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || fallbackMessage);
  }
  return res.json();
}

export async function startSession() {
  const res = await fetch(`${API_BASE}/start`, {
    method: "POST",
  });
  return handleJson(res, "Could not start session");
}

export async function getConceptIntro(sessionId) {
  const res = await fetch(`${API_BASE}/concept-intro/${sessionId}`, {
    method: "POST",
  });
  return handleJson(res, "Could not load concept intro");
}

export async function submitTurn(sessionId, payload) {
  const res = await fetch(`${API_BASE}/submit`, {
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
  const res = await fetch(`${API_BASE}/resume/${sessionId}`);
  return handleJson(res, "Could not resume session");
}

export async function resumeFromReport(reportText) {
  const res = await fetch(`${API_BASE}/resume-from-report`, {
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
  const res = await fetch(`${API_BASE}/report/${sessionId}`);
  return handleJson(res, "Could not load report");
}
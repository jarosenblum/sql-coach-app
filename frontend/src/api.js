const API_BASE = "http://localhost:8000";

export async function startSession() {
  const res = await fetch(`${API_BASE}/start`, { method: "POST" });
  return res.json();
}

export async function getConceptIntro(sessionId) {
  const res = await fetch(`${API_BASE}/concept-intro/${sessionId}`, { method: "POST" });
  return res.json();
}

export async function submitTurn(sessionId, payload) {
  const res = await fetch("http://localhost:8000/submit", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
      message: payload,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Submission failed");
  }

  return res.json();
}

export async function resumeSession(sessionId) {
  const res = await fetch(`http://localhost:8000/resume/${sessionId}`);

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Could not resume session");
  }

  return res.json();
}

export async function resumeFromReport(reportText) {
  const res = await fetch("http://localhost:8000/resume-from-report", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: "",
      saved_report_text: reportText,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Could not resume from report");
  }

  return res.json();
}

export async function getReport(sessionId) {
  const res = await fetch(`${API_BASE}/report/${sessionId}`);
  return res.json();
}
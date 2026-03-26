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
  const res = await fetch(`${API_BASE}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message: payload })
  });
  return res.json();
}

export async function getReport(sessionId) {
  const res = await fetch(`${API_BASE}/report/${sessionId}`);
  return res.json();
}
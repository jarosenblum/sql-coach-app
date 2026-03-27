import React, { useEffect, useState } from "react";
import { submitTurn } from "../api";

export default function ChatPanel({
  sessionId,
  currentQuestionId,
  onSubmitResponse,
}) {
  const [sql, setSql] = useState("");
  const [result, setResult] = useState("");
  const [explanation, setExplanation] = useState("");
  const [lastQuestionId, setLastQuestionId] = useState(currentQuestionId || "");
  const [loading, setLoading] = useState(false);

  // Reset ONLY when question changes
  useEffect(() => {
    if (currentQuestionId && currentQuestionId !== lastQuestionId) {
      setSql("");
      setResult("");
      setExplanation("");
      setLastQuestionId(currentQuestionId);
    }
  }, [currentQuestionId, lastQuestionId]);

  async function handleSubmit() {
    if (loading) return;

    setLoading(true);

    try {
      const payload = `SQL:::${sql}\nRESULT:::${result}\nEXPLANATION:::${explanation}`;
      const data = await submitTurn(sessionId, payload);
      onSubmitResponse(data);
    } catch (err) {
      console.error("Submit failed:", err);
      alert(err?.message || "Submission failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div>
        <div>SQL</div>
        <textarea
          value={sql}
          onChange={(e) => setSql(e.target.value)}
          rows={4}
          style={{ width: "100%" }}
        />
      </div>

      <div>
        <div>What you observed in W3Schools</div>
        <textarea
          value={result}
          onChange={(e) => setResult(e.target.value)}
          rows={3}
          style={{ width: "100%" }}
        />
      </div>

      <div>
        <div>Explanation</div>
        <textarea
          value={explanation}
          onChange={(e) => setExplanation(e.target.value)}
          rows={3}
          style={{ width: "100%" }}
        />
      </div>

      <button onClick={handleSubmit} disabled={loading}>
        {loading ? "⏳ Processing..." : "Submit Turn"}
      </button>
    </div>
  );
}
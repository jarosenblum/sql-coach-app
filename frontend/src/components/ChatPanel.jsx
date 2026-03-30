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

    if (document.activeElement instanceof HTMLElement) {
      document.activeElement.blur();
    }

    setLoading(true);

    // ⏱ delay scroll so user sees button change
    setTimeout(() => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }, 600); // 400–800ms is ideal

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
    <div
      style={{
        padding: 18,
        background: "#fcfcfd",
        border: "2px solid #d8dde8",
        borderRadius: 14,
        marginTop: 16,
        boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
      }}
    >
      {/* Header */}
      <div
        style={{
          fontWeight: 800,
          fontSize: 18,
          marginBottom: 12,
          color: "#1f1f1f",
        }}
      >
        Student Submission Area
      </div>

      <div
        style={{
          marginBottom: 16,
          color: "#555",
          lineHeight: 1.5,
        }}
      >
        Write your SQL, describe what happened, and explain your reasoning before submitting.
      </div>

      {/* SQL */}
      <div style={{ marginBottom: 14 }}>
      <div style={{ fontWeight: 700, marginBottom: 6 }}>SQL</div>

      <div
        style={{
          fontSize: 13,
          color: "#666",
          marginBottom: 8,
          lineHeight: 1.4,
        }}
      >
        ⚠️ For now, write your SQL query on a single line (no line breaks).
      </div>

      <textarea
        value={sql}
        onChange={(e) => setSql(e.target.value)}
        rows={4}
        style={{
          width: "100%",
          padding: 12,
          border: "1px solid #bfc7d8",
          borderRadius: 10,
          fontFamily: "monospace",
          fontSize: 15,
          background: "#ffffff",
        }}
      />
    </div>

      {/* Result */}
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontWeight: 700, marginBottom: 6 }}>
          What you observed in W3Schools
        </div>
        <textarea
          value={result}
          onChange={(e) => setResult(e.target.value)}
          rows={3}
          style={{
            width: "100%",
            padding: 12,
            border: "1px solid #cfd6e2",
            borderRadius: 10,
            background: "#ffffff",
            lineHeight: 1.5,
          }}
        />
      </div>

      {/* Explanation */}
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontWeight: 700, marginBottom: 6 }}>
          Explanation
        </div>

        <div
          style={{
            fontSize: 14,
            color: "#555",
            marginBottom: 8,
            lineHeight: 1.4,
          }}
        >
          Describe in your own words what this query is doing. Be sure to include a reference to the SQL commands used.
        </div>

        <textarea
          value={explanation}
          onChange={(e) => setExplanation(e.target.value)}
          rows={3}
          style={{
            width: "100%",
            padding: 12,
            border: "1px solid #cfd6e2",
            borderRadius: 10,
            background: "#ffffff",
            lineHeight: 1.5,
          }}
        />
      </div>

      {/* Submit */}
      <div
        style={{
          marginTop: 14,
          paddingTop: 12,
          borderTop: "1px solid #e1e5ec",
          display: "flex",
          gap: 10,
        }}
      >
        <button
          onClick={handleSubmit}
          disabled={loading}
          style={{
            padding: "10px 16px",
            borderRadius: 8,
            border: "1px solid #3b6edc",
            background: "#4a78d3",
            color: "#fff",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          {loading ? "⏳ Processing..." : "Submit Turn"}
        </button>
      </div>
    </div>
  );
}
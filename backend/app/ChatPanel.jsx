import React, { useState } from "react";
import { submitTurn } from "../api";

export default function ChatPanel({ sessionId, onSubmitResponse }) {
  const [sql, setSql] = useState("");
  const [result, setResult] = useState("");
  const [explanation, setExplanation] = useState("");

  async function handleSubmit() {
    try {
      const payload =
        `SQL:::${sql}\nRESULT:::${result}\nEXPLANATION:::${explanation}`;

      const data = await submitTurn(sessionId, payload);

      // IMPORTANT: pass the full backend response object back to App.jsx
      onSubmitResponse(data);
    } catch (err) {
      console.error("Submit failed:", err);
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
        <div>Sandbox Result</div>
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

      <button onClick={handleSubmit}>Submit Turn</button>
    </div>
  );
}
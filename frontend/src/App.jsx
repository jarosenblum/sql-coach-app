import { useState } from "react";
import { getConceptIntro, getReport, startSession } from "./api";
import ChatPanel from "./components/ChatPanel";
import ReportView from "./components/ReportView";
import SessionHeader from "./components/SessionHeader";

export default function App() {
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState([]);
  const [reportText, setReportText] = useState("");

  async function handleStart() {
    const data = await startSession();
    setSessionId(data.session_id);
    setMessages((m) => [...m, data.message, `Menu: ${data.menu.join(" | ")}`]);
  }

  async function handleConceptIntro() {
    if (!sessionId) return;
    const data = await getConceptIntro(sessionId);
    setMessages((m) => [...m, data.assistant_message]);
  }

  async function handleGetReport() {
    if (!sessionId) return;
    const data = await getReport(sessionId);
    setReportText(data.report_text);
  }

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: 24 }}>
      <h1>SQL Coach</h1>
      <SessionHeader sessionId={sessionId} />
      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <button onClick={handleStart}>Start SQL Coach</button>
        <button onClick={handleConceptIntro} disabled={!sessionId}>Start Assignment Walkthrough</button>
        <button onClick={handleGetReport} disabled={!sessionId}>Print Session Report</button>
      </div>

      <div style={{ background: "#fafafa", padding: 12, borderRadius: 8, marginBottom: 16 }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{ marginBottom: 10, whiteSpace: "pre-wrap" }}>{msg}</div>
        ))}
      </div>

      {sessionId && <ChatPanel sessionId={sessionId} onAssistantMessage={(msg) => setMessages((m) => [...m, msg])} />}
      <ReportView reportText={reportText} />
    </div>
  );
}
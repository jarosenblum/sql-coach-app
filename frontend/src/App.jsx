import React, { useEffect, useState } from "react";
import {
  getConceptIntro,
  getReport,
  resumeFromReport,
  resumeSession,
  sendSupportChat,
  startSession,
} from "./api";
import ChatPanel from "./components/ChatPanel";
import ReportView from "./components/ReportView";
import SessionHeader from "./components/SessionHeader";

function renderIntroSections(rawText) {
  if (!rawText) return null;

  const lines = rawText
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);

  const items = [];
  let current = null;

  for (const line of lines) {
    const numbered = line.match(/^(\d+)\.\s*\*?\*?(.+?)\*?\*?:\s*(.*)$/);
    if (numbered) {
      if (current) items.push(current);
      current = {
        heading: numbered[2].trim(),
        body: numbered[3] ? [numbered[3].trim()] : [],
      };
    } else if (current) {
      current.body.push(line);
    }
  }

  if (current) items.push(current);

  if (items.length === 0) {
    return (
      <div
        style={{
          padding: 12,
          background: "#ffffff",
          border: "1px solid #d9d9d9",
          borderRadius: 6,
          marginBottom: 12,
          whiteSpace: "pre-wrap",
          lineHeight: 1.5,
        }}
      >
        {rawText.replace(/```sql|```|`/g, "")}
      </div>
    );
  }

  return (
    <div
      style={{
        padding: 14,
        background: "#f5f5f5",
        borderRadius: 8,
        marginBottom: 12,
      }}
    >
      {items.map((item, idx) => {
        const bodyText = item.body.join("\n");
        const cleanedBody = bodyText.replace(/```sql|```|`/g, "");
        const headingLower = item.heading.toLowerCase();

        const looksLikeSqlBlock =
          bodyText.includes("```") ||
          headingLower.includes("syntax") ||
          headingLower.includes("blueprint") ||
          headingLower.includes("scaffold");

        const isAssignmentInstructions =
          headingLower.includes("assignment instructions");

        return (
          <div key={idx} style={{ marginBottom: 16 }}>
            <div style={{ fontWeight: 700, marginBottom: 6 }}>
              {item.heading}
            </div>

            {isAssignmentInstructions ? (
              <div
                style={{
                  background: "#fffaf0",
                  border: "1px solid #e6d39b",
                  borderLeft: "6px solid #d4a72c",
                  borderRadius: 8,
                  padding: "12px 14px",
                  whiteSpace: "pre-wrap",
                  lineHeight: 1.5,
                  boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
                }}
              >
                {cleanedBody}
              </div>
            ) : looksLikeSqlBlock ? (
              <pre
                style={{
                  background: "#ffffff",
                  border: "1px solid #d9d9d9",
                  padding: 10,
                  borderRadius: 6,
                  overflowX: "auto",
                  whiteSpace: "pre-wrap",
                  fontFamily: "monospace",
                  margin: 0,
                }}
              >
                {cleanedBody}
              </pre>
            ) : (
              <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
                {cleanedBody}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function renderMessageWithLinks(text) {
  if (!text) return null;

  const url =
    "https://www.w3schools.com/sql/trysql.asp?filename=trysql_select_all";

  if (text.includes("W3Schools SQL Try-It sandbox")) {
    return (
      <>
        Session started. Open the{" "}
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: "#2a5bd7", textDecoration: "underline" }}
        >
          W3Schools SQL Try-It sandbox
        </a>{" "}
        in a new tab.
      </>
    );
  }

  return text;
}

export default function App() {
  const [lastFeedback, setLastFeedback] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState([]);
  const [reportText, setReportText] = useState("");
  const [assistantMessage, setAssistantMessage] = useState("");
  const [currentQuestionId, setCurrentQuestionId] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingMessage, setProcessingMessage] = useState("");
  const [showResumePanel, setShowResumePanel] = useState(false);
  const [resumeReportText, setResumeReportText] = useState("");
  const [supportMessages, setSupportMessages] = useState([]);
  const [supportInput, setSupportInput] = useState("");
  const [isSupportLoading, setIsSupportLoading] = useState(false);

  useEffect(() => {
    const savedSessionId = localStorage.getItem("sqlcoach_session_id");
    if (!savedSessionId) return;

    async function restore() {
      setSupportMessages([]);
      setSupportInput("");
      try {
        const data = await resumeSession(savedSessionId);
        setSessionId(data.session_id);
        setAssistantMessage(data.assistant_message || "");
        setCurrentQuestionId(data.current_question_id || "");
        setMessages(["Resumed previous session."]);
      } catch (err) {
        console.error("Failed to auto-resume session:", err);
        localStorage.removeItem("sqlcoach_session_id");
      }
    }

    restore();
  }, []);

  async function handleResumeFromReport() {
    setSupportMessages([]);
    setSupportInput("");
    if (!resumeReportText.trim()) {
      alert("Paste a saved session report first.");
      return;
    }

    try {
      const data = await resumeFromReport(resumeReportText);
      setSessionId(data.session_id);
      localStorage.setItem("sqlcoach_session_id", data.session_id);
      setAssistantMessage(data.assistant_message || "");
      setCurrentQuestionId(data.current_question_id || "");
      setMessages(["Resumed previous session from saved report."]);
      setLastFeedback("");
      setShowResumePanel(false);
      setResumeReportText("");
    } catch (err) {
      console.error("Failed to resume from report:", err);
      alert(err.message || "Could not resume from saved report.");
    }
  }

  async function handleStart() {
  try {
    const data = await startSession();

    setSessionId(data.session_id);
    localStorage.setItem("sqlcoach_session_id", data.session_id);
    setMessages([data.message]);
    setAssistantMessage("");
    setCurrentQuestionId("");
    setReportText("");
    setLastFeedback("");
    setShowResumePanel(false);
    setSupportMessages([]);
    setSupportInput("");

    const intro = await getConceptIntro(data.session_id);
    setAssistantMessage(intro.assistant_message);
    setCurrentQuestionId(intro.current_question_id);
  } catch (err) {
    console.error("Failed to start SQL Coach:", err);
    setMessages([
      "Could not start SQL Coach. Check that the backend is running.",
    ]);
  }
}
async function handleContinuePreviousSession() {
  const savedSessionId = localStorage.getItem("sqlcoach_session_id");
  setSupportMessages([]);
  setSupportInput("");

  if (savedSessionId) {
    try {
      const data = await resumeSession(savedSessionId);
      setSessionId(data.session_id);
      setAssistantMessage(data.assistant_message || "");
      setCurrentQuestionId(data.current_question_id || "");
      setMessages(["Resumed previous session from this browser."]);
      setLastFeedback("");
      setShowResumePanel(false);
      return;
    } catch (err) {
      console.error("Failed to continue previous browser session:", err);
    }
  }

  setShowResumePanel(true);
}

  async function handleSendSupportChat() {
  if (!supportInput.trim() || !sessionId || !currentQuestionId || currentQuestionId === "COMPLETE") {
    return;
  }

  const userMessage = supportInput.trim();

  setSupportMessages((msgs) => [
    ...msgs,
    { role: "user", content: userMessage },
  ]);
  setSupportInput("");
  setIsSupportLoading(true);

  try {
    const data = await sendSupportChat({
      session_id: sessionId,
      question_id: currentQuestionId,
      student_message: userMessage,
      last_feedback: lastFeedback || "",
      current_sql: "",
    });

    setSupportMessages((msgs) => [
      ...msgs,
      { role: "assistant", content: data.assistant_message || "" },
    ]);
  } catch (err) {
    console.error("Support chat failed:", err);
    setSupportMessages((msgs) => [
      ...msgs,
      {
        role: "assistant",
        content: "Sorry — support chat is unavailable right now.",
      },
    ]);
  } finally {
    setIsSupportLoading(false);
  }
}

  async function handleGetReport() {
    if (!sessionId) return;

    try {
      const data = await getReport(sessionId);
      setReportText(data.report_text);
    } catch (err) {
      console.error("Failed to load report:", err);
      setMessages((m) => [...m, "Could not load the session report."]);
    }
  }

async function handleSubmitResponse(data) {
  if (data.session_id) {
    localStorage.setItem("sqlcoach_session_id", data.session_id);
  }

  setLastFeedback(data.assistant_message || "");

  if (data.current_question_id === "COMPLETE") {
    setCurrentQuestionId("COMPLETE");
    setAssistantMessage("");
    return;
  }

  const activeSessionId = data.session_id || sessionId;
  const nextQuestionId = data.current_question_id || currentQuestionId;

  // If backend has already advanced the session, load the next intro
  // even if should_advance is false because of legacy checkpoint behavior.
  if (nextQuestionId !== currentQuestionId) {
    setIsProcessing(true);
    setProcessingMessage("Loading next question...");

    try {
      const intro = await getConceptIntro(activeSessionId);
      setAssistantMessage(intro.assistant_message);
      setCurrentQuestionId(nextQuestionId);
      setLastFeedback("");
    } catch (err) {
      console.error("Failed to refresh current question after submit:", err);
    } finally {
      setIsProcessing(false);
      setProcessingMessage("");
    }
    return;
  }

  if (!data.should_advance) {
    setCurrentQuestionId((prev) => data.current_question_id || prev);
    return;
  }

  setIsProcessing(true);
  setProcessingMessage("Loading next question...");

  try {
    const intro = await getConceptIntro(activeSessionId);
    setAssistantMessage(intro.assistant_message);
    setCurrentQuestionId(nextQuestionId);
    setLastFeedback("");
  } catch (err) {
    console.error("Failed to refresh current question after submit:", err);
  } finally {
    setIsProcessing(false);
    setProcessingMessage("");
  }
}
return (
  <div style={{ maxWidth: 900, margin: "0 auto", padding: 24 }}>
    <h1>SQL Coach</h1>
    <SessionHeader sessionId={sessionId} />

    <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
      <button onClick={handleStart}>Start SQL Coach</button>
      <button onClick={handleContinuePreviousSession}>
        Continue Previous Session
      </button>
      <button onClick={() => setShowResumePanel(true)}>
        Resume from Saved Report
      </button>
      <button onClick={handleGetReport} disabled={!sessionId}>
        Print Session Report
      </button>
    </div>

    {showResumePanel && (
      <div
        style={{
          padding: 12,
          background: "#f8f8ff",
          border: "1px solid #cfd4ea",
          borderRadius: 6,
          marginBottom: 16,
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: 8 }}>
          Resume from Saved Session Report
        </div>
        <div style={{ marginBottom: 8 }}>
          Copy the text from a previously saved session report, paste it below,
          then click <strong>Resume from Report</strong>.
        </div>
        <textarea
          value={resumeReportText}
          onChange={(e) => setResumeReportText(e.target.value)}
          rows={8}
          style={{ width: "100%", marginBottom: 10 }}
          placeholder="Paste your saved session report here..."
        />
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={handleResumeFromReport}>Resume from Report</button>
          <button onClick={() => setShowResumePanel(false)}>Cancel</button>
        </div>
      </div>
    )}

    <div
      style={{
        background: "#fafafa",
        padding: 12,
        borderRadius: 8,
        marginBottom: 16,
      }}
    >
      {messages.map((msg, idx) => (
        <div key={idx} style={{ marginBottom: 10, whiteSpace: "pre-wrap" }}>
          {renderMessageWithLinks(msg)}
        </div>
      ))}
    </div>

    {currentQuestionId && currentQuestionId !== "COMPLETE" && (
      <div style={{ marginBottom: 10 }}>
        <strong>Current Question:</strong> {currentQuestionId}
      </div>
    )}

    {currentQuestionId === "COMPLETE" && (
      <div
        style={{
          padding: 12,
          background: "#eef8ee",
          border: "1px solid #b7d8b7",
          borderRadius: 6,
          marginBottom: 12,
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: 6 }}>Assignment Complete</div>
        <div style={{ marginBottom: 10 }}>
          Click <strong>Print Session Report</strong> now to save your final work.
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={handleGetReport} disabled={!sessionId}>
            Print Session Report
          </button>
        </div>
      </div>
    )}

    {assistantMessage && renderIntroSections(assistantMessage)}

    {isProcessing && (
      <div
        style={{
          padding: 10,
          background: "#eef3ff",
          border: "1px solid #b7c7ff",
          borderRadius: 6,
          marginBottom: 12,
          display: "flex",
          alignItems: "center",
          fontStyle: "italic",
        }}
      >
        <span className="spinner"></span>
        {processingMessage}
      </div>
    )}

    {lastFeedback && (
      <div
        style={{
          padding: 12,
          background: "#fff8e8",
          border: "1px solid #e6d39b",
          borderRadius: 6,
          marginBottom: 12,
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: 4 }}>Feedback</div>
        <div style={{ whiteSpace: "pre-wrap" }}>{lastFeedback}</div>
      </div>
    )}

    {currentQuestionId === "Q6" && (
      <div
        style={{
          padding: 12,
          background: "#eef8ee",
          border: "1px solid #b7d8b7",
          borderRadius: 6,
          marginBottom: 12,
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: 6 }}>Good stopping point</div>
        <div style={{ marginBottom: 10 }}>
          Print your session report if you want to save progress.
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={handleGetReport} disabled={!sessionId}>
            Print Session Report
          </button>
        </div>
      </div>
    )}

    {sessionId && currentQuestionId && currentQuestionId !== "COMPLETE" && (
      <div
        style={{
          padding: 12,
          background: "#f8f8ff",
          border: "1px solid #cfd4ea",
          borderRadius: 8,
          marginBottom: 12,
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: 8 }}>Support Chat</div>
        <div style={{ marginBottom: 10, lineHeight: 1.5 }}>
          Ask for concept help, debugging guidance, or hints for the current question.
        </div>

        <div
          style={{
            maxHeight: 220,
            overflowY: "auto",
            background: "#ffffff",
            border: "1px solid #e2e2e2",
            borderRadius: 6,
            padding: 10,
            marginBottom: 10,
          }}
        >
          {supportMessages.length === 0 ? (
            <div style={{ color: "#666" }}>
              No support messages yet.
            </div>
          ) : (
            supportMessages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  marginBottom: 10,
                  whiteSpace: "pre-wrap",
                }}
              >
                <strong>{msg.role === "user" ? "You" : "Support"}</strong>
                <div>{msg.content}</div>
              </div>
            ))
          )}
        </div>

        <textarea
          value={supportInput}
          onChange={(e) => setSupportInput(e.target.value)}
          rows={3}
          style={{ width: "100%", marginBottom: 10 }}
          placeholder="Ask for help with the current concept or your debugging process..."
        />

        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={handleSendSupportChat} disabled={isSupportLoading}>
            {isSupportLoading ? "Thinking..." : "Ask Support Chat"}
          </button>
        </div>
      </div>
    )}

    {sessionId && currentQuestionId !== "COMPLETE" && (
      <ChatPanel
        sessionId={sessionId}
        currentQuestionId={currentQuestionId}
        onSubmitResponse={handleSubmitResponse}
      />
    )}

    <ReportView reportText={reportText} />
  </div>
);
}
export default function SessionHeader({ sessionId }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <strong>Session ID:</strong> {sessionId || "Not started"}
    </div>
  );
}
import React from "react";
export default function ReportView({ reportText }) {
  if (!reportText) return null;
  return (
    <pre style={{ whiteSpace: "pre-wrap", background: "#f5f5f5", padding: 12, borderRadius: 8 }}>
      {reportText}
    </pre>
  );
}
import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";

export default function ErrorAlert({ message = "Unable to load data.", onRetry }) {
  return (
    <div className="error-box">
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }}>
        <AlertCircle size={24} />
        <h3 style={{ fontSize: "1.05rem", fontWeight: 600 }}>Error Encountered</h3>
      </div>
      <p style={{ marginBottom: onRetry ? "1rem" : 0 }}>{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary" style={{ color: "#be123c", borderColor: "#fecdd3" }}>
          <RefreshCw size={16} /> Try Again
        </button>
      )}
    </div>
  );
}

import React from "react";
import RiskBadge from "../common/RiskBadge";
import { ShieldCheck, AlertTriangle } from "lucide-react";

export default function RiskOverviewCard({ riskData }) {
  if (!riskData) return null;

  const {
    dropout_probability = 0,
    retention_probability = 0,
    risk_level = "LOW",
    semester = 1,
  } = riskData;

  const probPct = (dropout_probability * 100).toFixed(2);
  const retPct = (retention_probability * 100).toFixed(2);

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
      <div className="card-header" style={{ marginBottom: "0.5rem" }}>
        <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em" }}>
          STUDENT SUCCESS RISK (SEM {semester})
        </span>
        <RiskBadge level={risk_level} />
      </div>

      <div style={{ margin: "1rem 0" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem" }}>
          <span style={{ fontSize: "3rem", fontWeight: 800, color: risk_level === "HIGH" ? "#be123c" : risk_level === "MEDIUM" ? "#b45309" : "#047857", lineHeight: 1 }}>
            {probPct}%
          </span>
          <span style={{ fontSize: "0.9rem", color: "#64748b", fontWeight: 500 }}>
            Future Dropout Probability
          </span>
        </div>

        {/* Risk Progress Bar */}
        <div style={{ width: "100%", height: "8px", backgroundColor: "#e2e8f0", borderRadius: "4px", marginTop: "1rem", overflow: "hidden" }}>
          <div
            style={{
              width: `${Math.min(100, Math.max(5, probPct))}%`,
              height: "100%",
              backgroundColor: risk_level === "HIGH" ? "#e11d48" : risk_level === "MEDIUM" ? "#d97706" : "#059669",
              transition: "width 0.5s ease",
            }}
          />
        </div>
      </div>

      <div style={{ paddingTop: "1rem", borderTop: "1px solid #f1f5f9", display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.9rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", color: "#047857", fontWeight: 600 }}>
          <ShieldCheck size={18} />
          <span>Retention Probability: {retPct}%</span>
        </div>

        <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
          Calibrated Operational Model
        </span>
      </div>
    </div>
  );
}

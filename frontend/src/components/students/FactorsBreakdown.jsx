import React from "react";
import { AlertTriangle, ShieldCheck } from "lucide-react";

export default function FactorsBreakdown({ riskFactors = [], protectiveFactors = [] }) {
  const formatFeatureName = (feat) => {
    return feat
      .replace(/_/g, " ")
      .replace(/\b\w/g, (l) => l.toUpperCase());
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1.5rem" }}>
      {/* Top Risk Factors */}
      <div className="card">
        <div className="card-header">
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "#be123c" }}>
            <AlertTriangle size={20} />
            <h3 className="card-title" style={{ color: "#be123c" }}>Top Factors Increasing Dropout Risk</h3>
          </div>
        </div>

        {riskFactors && riskFactors.length > 0 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
            {riskFactors.map((factor, idx) => (
              <div key={idx} style={{ padding: "0.75rem", backgroundColor: "#fff1f2", borderRadius: "0.5rem", border: "1px solid #fecdd3" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.25rem" }}>
                  <span style={{ fontWeight: 600, color: "#9f1239", fontSize: "0.9rem" }}>
                    {formatFeatureName(factor.feature)}
                  </span>
                  <span style={{ fontWeight: 700, color: "#be123c", fontSize: "0.85rem" }}>
                    Value: {factor.value}
                  </span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.8rem", color: "#881337" }}>
                  <span>Contribution: +{Number(factor.contribution).toFixed(4)}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: "#64748b", fontSize: "0.9rem", padding: "1rem 0" }}>
            No significant risk factors identified for this record.
          </p>
        )}
      </div>

      {/* Top Protective Factors */}
      <div className="card">
        <div className="card-header">
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "#047857" }}>
            <ShieldCheck size={20} />
            <h3 className="card-title" style={{ color: "#047857" }}>Top Protective Factors Reducing Risk</h3>
          </div>
        </div>

        {protectiveFactors && protectiveFactors.length > 0 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
            {protectiveFactors.map((factor, idx) => (
              <div key={idx} style={{ padding: "0.75rem", backgroundColor: "#ecfdf5", borderRadius: "0.5rem", border: "1px solid #a7f3d0" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.25rem" }}>
                  <span style={{ fontWeight: 600, color: "#065f46", fontSize: "0.9rem" }}>
                    {formatFeatureName(factor.feature)}
                  </span>
                  <span style={{ fontWeight: 700, color: "#047857", fontSize: "0.85rem" }}>
                    Value: {factor.value}
                  </span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.8rem", color: "#064e3b" }}>
                  <span>Contribution: {Number(factor.contribution).toFixed(4)}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: "#64748b", fontSize: "0.9rem", padding: "1rem 0" }}>
            No significant protective factors identified for this record.
          </p>
        )}
      </div>
    </div>
  );
}

import React from "react";
import { AlertTriangle, CheckCircle, Info } from "lucide-react";

export default function RiskBadge({ level = "LOW" }) {
  const normalized = (level || "LOW").toUpperCase();

  const icons = {
    LOW: <CheckCircle size={14} />,
    MEDIUM: <Info size={14} />,
    HIGH: <AlertTriangle size={14} />,
  };

  return (
    <span className={`risk-badge ${normalized}`}>
      {icons[normalized] || <Info size={14} />}
      {normalized} RISK
    </span>
  );
}

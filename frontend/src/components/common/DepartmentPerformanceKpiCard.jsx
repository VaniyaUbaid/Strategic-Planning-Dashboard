import React from "react";

export default function DepartmentPerformanceKpiCard({ label, value, icon: Icon, tone = "blue" }) {
  return (
    <article className="card department-performance-kpi">
      <div>
        <span className="department-performance-kpi-label">{label}</span>
        <strong className="department-performance-kpi-value">{value}</strong>
      </div>
      {Icon && (
        <span className={`department-performance-kpi-icon ${tone}`}>
          <Icon size={21} />
        </span>
      )}
    </article>
  );
}

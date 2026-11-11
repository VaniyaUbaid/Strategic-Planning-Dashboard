import React from "react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from "recharts";
import { DepartmentRiskComparisonChart } from "./DepartmentCharts";

export default function AdminCharts({ overviewData }) {
  if (!overviewData) return null;

  const departmentData = overviewData.department_chart || [];
  const riskDistribution = overviewData.risk_distribution || {
    high_count: 0,
    medium_count: 0,
    low_count: 0,
  };
  const pieData = [
    { name: "High Risk (≥60%)", value: riskDistribution.high_count, color: "#ef4444" },
    { name: "Medium Risk (40-59%)", value: riskDistribution.medium_count, color: "#f59e0b" },
    { name: "Low Risk (<40%)", value: riskDistribution.low_count, color: "#10b981" },
  ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 360px), 1fr))", gap: "1.5rem", marginBottom: "2rem" }}>
      <div className="card">
        <DepartmentRiskComparisonChart data={departmentData} />
      </div>
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: "1rem" }}>
          Institutional Risk-Level Distribution
        </h3>
        <p className="department-performance-note">
          Share of filtered unique students in each model probability band. Percentages use the same student population as the Overview risk KPIs.
        </p>
        <div style={{ width: "100%", height: 280, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <ResponsiveContainer>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={95}
                paddingAngle={4}
                dataKey="value"
                label={({ percent }) => `${(percent * 100).toFixed(1)}%`}
              >
                {pieData.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value, name) => [Number(value).toLocaleString(), `${name} students`]} contentStyle={{ backgroundColor: "#ffffff", borderRadius: "0.5rem", border: "1px solid #cbd5e1" }} />
              <Legend wrapperStyle={{ fontSize: "0.8rem" }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

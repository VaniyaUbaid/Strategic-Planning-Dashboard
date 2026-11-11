import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "../common/DepartmentPerformance.css";

const AXIS_STYLE = { fontSize: "0.75rem" };
const TOOLTIP_STYLE = {
  backgroundColor: "#ffffff",
  borderRadius: "0.5rem",
  border: "1px solid #cbd5e1",
};

function getChartData(data = []) {
  return data.map((department) => ({
    ...department,
    high_risk_percentage: department.total_students > 0
      ? (department.high_risk_count / department.total_students) * 100
      : 0,
  }));
}

export function DepartmentRiskComparisonChart({ data = [] }) {
  const chartData = getChartData(data);

  return (
    <>
      <h3 className="card-title" style={{ marginBottom: "1rem" }}>
        Students & High-Risk Percentage by Department
      </h3>
      <p className="department-performance-note">
        Bars show latest-record student counts; the line shows high-risk students as a share of each department's filtered student total.
      </p>
      <div style={{ width: "100%", height: 300 }}>
        <ResponsiveContainer>
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -15, bottom: 25 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="department_id"
              stroke="#64748b"
              style={AXIS_STYLE}
              interval={0}
              angle={-30}
              textAnchor="end"
              label={{ value: "Department", position: "insideBottom", offset: -18 }}
            />
            <YAxis yAxisId="students" stroke="#64748b" style={AXIS_STYLE} label={{ value: "Students", angle: -90, position: "insideLeft" }} />
            <YAxis
              yAxisId="percentage"
              orientation="right"
              domain={[0, 100]}
              tickFormatter={(value) => `${value}%`}
              stroke="#64748b"
              style={AXIS_STYLE}
              label={{ value: "High-risk students (%)", angle: 90, position: "insideRight" }}
            />
            <Tooltip
              contentStyle={TOOLTIP_STYLE}
              formatter={(value, name) => (
                name === "High-risk percentage"
                  ? [`${Number(value).toFixed(1)}%`, name]
                  : [Number(value).toLocaleString(), name]
              )}
            />
            <Bar
              yAxisId="students"
              dataKey="total_students"
              name="Total Students"
              fill="#3b82f6"
              radius={[4, 4, 0, 0]}
            />
            <Bar
              yAxisId="students"
              dataKey="high_risk_count"
              name="High Risk Students"
              fill="#f97316"
              radius={[4, 4, 0, 0]}
            />
            <Line
              yAxisId="percentage"
              dataKey="high_risk_percentage"
              name="High-risk percentage"
              stroke="#ef4444"
              strokeWidth={2}
              dot={{ r: 4 }}
            />
            <Legend wrapperStyle={{ fontSize: "0.8rem" }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}

export default function DepartmentPerformanceCharts({ data = [] }) {
  const chartData = getChartData(data);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 360px), 1fr))", gap: "1.5rem", marginBottom: "2rem" }}>
      <div className="card">
        <DepartmentRiskComparisonChart data={data} />
      </div>
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: "1rem" }}>
          Average Cumulative GPA by Department
        </h3>
        <p className="department-performance-note">
          Mean cumulative GPA for filtered student records; the 0–10 scale starts at zero.
        </p>
        <div style={{ width: "100%", height: 300 }}>
          <ResponsiveContainer>
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -15, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="department_id" stroke="#64748b" style={AXIS_STYLE} interval={0} angle={-30} textAnchor="end" label={{ value: "Department", position: "insideBottom", offset: -18 }} />
              <YAxis domain={[0, 10]} stroke="#64748b" style={AXIS_STYLE} label={{ value: "Average GPA (0–10)", angle: -90, position: "insideLeft" }} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Bar dataKey="avg_gpa" name="Average GPA" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: "1rem" }}>
          Average Attendance by Department
        </h3>
        <p className="department-performance-note">
          Mean attendance for filtered student records, shown on the full 0–100% scale.
        </p>
        <div style={{ width: "100%", height: 300 }}>
          <ResponsiveContainer>
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -15, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="department_id" stroke="#64748b" style={AXIS_STYLE} interval={0} angle={-30} textAnchor="end" label={{ value: "Department", position: "insideBottom", offset: -18 }} />
              <YAxis domain={[0, 100]} tickFormatter={(value) => `${value}%`} stroke="#64748b" style={AXIS_STYLE} label={{ value: "Average attendance (%)", angle: -90, position: "insideLeft" }} />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                formatter={(value, name) => [`${Number(value).toFixed(1)}%`, name]}
              />
              <Bar dataKey="avg_attendance" name="Average Attendance" fill="#d97706" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

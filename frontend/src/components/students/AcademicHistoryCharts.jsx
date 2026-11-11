import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

export default function AcademicHistoryCharts({ history = [] }) {
  if (!history || history.length === 0) return null;

  const chartData = history.map((item) => ({
    name: `Sem ${item.semester}`,
    semester_gpa: item.semester_gpa,
    cumulative_gpa: item.cumulative_gpa,
    attendance: item.attendance_percentage,
  }));

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(350px, 1fr))", gap: "1.5rem", marginBottom: "1.5rem" }}>
      {/* GPA Progression Chart */}
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: "1rem" }}>GPA Progression Over Semesters</h3>
        <p style={{ color: "#64748b", fontSize: "0.85rem", margin: "0 0 0.75rem" }}>
          Semester and cumulative GPA from this student's academic history, on the full 0-10 scale.
        </p>
        <div style={{ width: "100%", height: 260 }}>
          <ResponsiveContainer>
            <LineChart data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" stroke="#64748b" style={{ fontSize: "0.8rem" }} label={{ value: "Semester", position: "insideBottom", offset: -3 }} />
              <YAxis domain={[0, 10]} stroke="#64748b" style={{ fontSize: "0.8rem" }} label={{ value: "GPA (0-10)", angle: -90, position: "insideLeft" }} />
              <Tooltip
                contentStyle={{ backgroundColor: "#ffffff", borderRadius: "0.5rem", border: "1px solid #cbd5e1" }}
              />
              <Legend wrapperStyle={{ paddingTop: "5px", fontSize: "0.85rem" }} />
              <Line type="monotone" dataKey="semester_gpa" name="Semester GPA" stroke="#2563eb" strokeWidth={2} dot={{ r: 4 }} />
              <Line type="monotone" dataKey="cumulative_gpa" name="Cumulative GPA" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Attendance Trend Chart */}
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: "1rem" }}>Attendance Trend (%)</h3>
        <p style={{ color: "#64748b", fontSize: "0.85rem", margin: "0 0 0.75rem" }}>
          Recorded attendance by semester, shown on the full 0-100% scale.
        </p>
        <div style={{ width: "100%", height: 260 }}>
          <ResponsiveContainer>
            <LineChart data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" stroke="#64748b" style={{ fontSize: "0.8rem" }} label={{ value: "Semester", position: "insideBottom", offset: -3 }} />
              <YAxis domain={[0, 100]} unit="%" stroke="#64748b" style={{ fontSize: "0.8rem" }} label={{ value: "Attendance (%)", angle: -90, position: "insideLeft" }} />
              <Tooltip
                contentStyle={{ backgroundColor: "#ffffff", borderRadius: "0.5rem", border: "1px solid #cbd5e1" }}
              />
              <Legend wrapperStyle={{ paddingTop: "5px", fontSize: "0.85rem" }} />
              <Line type="monotone" dataKey="attendance" name="Attendance %" stroke="#d97706" strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

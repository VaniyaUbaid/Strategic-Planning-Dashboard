import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { formatINR } from "../../utils/currency";

export default function HodDepartmentView({ hodData }) {
  if (!hodData) return null;

  const riskDist = hodData.risk_distribution || { high_count: 0, medium_count: 0, low_count: 0 };
  const semBreakdown = hodData.semester_breakdown || [];
  const pieData = [
    { name: "High Risk (≥60%)", value: riskDist.high_count, color: "#ef4444" },
    { name: "Medium Risk (40-59%)", value: riskDist.medium_count, color: "#f59e0b" },
    { name: "Low Risk (<40%)", value: riskDist.low_count, color: "#10b981" },
  ];

  return (
    <div>
      {/* Department Banner */}
      <div
        className="card"
        style={{
          padding: "1.25rem 1.5rem",
          marginBottom: "1.5rem",
          background: "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)",
          color: "#ffffff",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              HEAD OF DEPARTMENT (HOD) VIEW
            </span>
            <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginTop: "0.2rem", color: "#f8fafc" }}>
              {hodData.department_name} ({hodData.department_id})
            </h2>
            <p style={{ fontSize: "0.85rem", color: "#cbd5e1", marginTop: "0.25rem" }}>
              Enforced Departmental Scope & Dynamic Academic Progression Control
            </p>
          </div>

          <div style={{ display: "flex", gap: "0.75rem" }}>
            <div style={{ backgroundColor: "rgba(255,255,255,0.1)", padding: "0.5rem 1rem", borderRadius: "0.5rem", textAlign: "center" }}>
              <span style={{ fontSize: "0.7rem", color: "#94a3b8", display: "block" }}>ACADEMIC YEARS</span>
              <span style={{ fontSize: "1.1rem", fontWeight: 700, color: "#38bdf8" }}>
                {hodData.available_years?.length || 0} Years
              </span>
            </div>
            <div style={{ backgroundColor: "rgba(255,255,255,0.1)", padding: "0.5rem 1rem", borderRadius: "0.5rem", textAlign: "center" }}>
              <span style={{ fontSize: "0.7rem", color: "#94a3b8", display: "block" }}>SEMESTERS</span>
              <span style={{ fontSize: "1.1rem", fontWeight: 700, color: "#4ade80" }}>
                {hodData.available_semesters?.length || 0} Semesters
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* HOD Metrics Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1.25rem", marginBottom: "1.5rem" }}>
        <div className="card" style={{ padding: "1.25rem" }}>
          <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700 }}>DEPARTMENT STUDENTS</span>
          <h3 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#0f172a", marginTop: "0.2rem" }}>
            {hodData.total_students.toLocaleString()}
          </h3>
          <span style={{ fontSize: "0.75rem", color: "#059669", fontWeight: 600 }}>Active Enrolled</span>
        </div>

        <div className="card" style={{ padding: "1.25rem" }}>
          <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700 }}>AVERAGE GPA</span>
          <h3 style={{ fontSize: "1.75rem", fontWeight: 700, color: hodData.avg_gpa >= 7.0 ? "#047857" : "#b45309", marginTop: "0.2rem" }}>
            {hodData.avg_gpa.toFixed(2)}
          </h3>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Scale 0.0 - 10.0</span>
        </div>

        <div className="card" style={{ padding: "1.25rem" }}>
          <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700 }}>AVG ATTENDANCE</span>
          <h3 style={{ fontSize: "1.75rem", fontWeight: 700, color: hodData.avg_attendance >= 75 ? "#047857" : "#be123c", marginTop: "0.2rem" }}>
            {hodData.avg_attendance.toFixed(1)}%
          </h3>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Target ≥75%</span>
        </div>

        <div className="card" style={{ padding: "1.25rem" }}>
          <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700 }}>STUDENTS AT RISK</span>
          <h3 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#be123c", marginTop: "0.2rem" }}>
            {hodData.students_at_risk.toLocaleString()}
          </h3>
          <span style={{ fontSize: "0.75rem", color: "#be123c", fontWeight: 600 }}>
            {hodData.high_risk_count} High / {hodData.medium_risk_count} Med
          </span>
        </div>

        <div className="card" style={{ padding: "1.25rem" }}>
          <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700 }}>BACKLOG STATS</span>
          <h3 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#0f172a", marginTop: "0.2rem" }}>
            {hodData.students_with_backlogs.toLocaleString()}
          </h3>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Students with Backlogs</span>
        </div>

        <div className="card" style={{ padding: "1.25rem" }}>
          <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700 }}>FEE PENDING STATS</span>
          <h3 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#b45309", marginTop: "0.2rem" }}>
            {hodData.students_fee_pending.toLocaleString()}
          </h3>
          <span style={{ fontSize: "0.75rem", color: "#b45309", fontWeight: 600 }}>
            {formatINR(hodData.total_fee_pending_amount)} Pending
          </span>
        </div>
      </div>

      {/* Recharts Visualizations for HOD */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "1.5rem", marginBottom: "2rem" }}>
        {/* Risk Distribution Donut */}
        <div className="card">
          <h3 className="card-title" style={{ marginBottom: "1rem" }}>Department Dropout Risk Distribution</h3>
          <p style={{ color: "#64748b", fontSize: "0.85rem", margin: "0 0 0.75rem" }}>
            Share of the filtered department student population in each model probability band.
          </p>
          <div style={{ width: "100%", height: 260 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={90}
                  paddingAngle={4}
                  dataKey="value"
                  label={({ percent }) => `${(percent * 100).toFixed(1)}%`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: "#ffffff", borderRadius: "0.5rem", border: "1px solid #cbd5e1" }} />
                <Legend wrapperStyle={{ fontSize: "0.8rem" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Semester Progression Chart */}
        <div className="card">
          <h3 className="card-title" style={{ marginBottom: "1rem" }}>Semester-wise Enrollment & Risk Breakdown</h3>
          <p style={{ color: "#64748b", fontSize: "0.85rem", margin: "0 0 0.75rem" }}>
            Student counts grouped by each student's latest matching semester record; this is a current distribution, not a longitudinal trend.
          </p>
          <div style={{ width: "100%", height: 260 }}>
            <ResponsiveContainer>
              <BarChart data={semBreakdown} margin={{ top: 10, right: 10, left: -15, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="semester" stroke="#64748b" style={{ fontSize: "0.8rem" }} tickFormatter={(s) => `Sem ${s}`} label={{ value: "Latest matching semester", position: "insideBottom", offset: -3 }} />
                <YAxis stroke="#64748b" style={{ fontSize: "0.8rem" }} allowDecimals={false} label={{ value: "Students", angle: -90, position: "insideLeft" }} />
                <Tooltip contentStyle={{ backgroundColor: "#ffffff", borderRadius: "0.5rem", border: "1px solid #cbd5e1" }} />
                <Legend wrapperStyle={{ fontSize: "0.8rem" }} />
                <Bar dataKey="total_students" name="Total Students" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="high_risk_count" name="High Risk" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Hierarchy Cards: Academic Years & Semesters within HOD Department */}
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: "1rem" }}>
          Department Hierarchy Breakdown (Semesters & Academic Years)
        </h3>
        
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" }}>
          {semBreakdown.map((item) => (
            <div
              key={item.semester}
              style={{
                padding: "1rem",
                borderRadius: "0.5rem",
                backgroundColor: "#f8fafc",
                border: "1px solid #cbd5e1",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                <span style={{ fontWeight: 700, color: "#0f172a", fontSize: "0.95rem" }}>Semester {item.semester}</span>
                <span style={{ fontSize: "0.75rem", backgroundColor: "#e2e8f0", padding: "0.15rem 0.4rem", borderRadius: "0.25rem", fontWeight: 600 }}>
                  {item.total_students} Students
                </span>
              </div>
              <div style={{ fontSize: "0.8rem", color: "#475569" }}>
                <div>Avg GPA: <strong>{item.avg_gpa.toFixed(2)}</strong></div>
                <div>Avg Attendance: <strong>{item.avg_attendance.toFixed(1)}%</strong></div>
                <div style={{ marginTop: "0.4rem", display: "flex", gap: "0.3rem", fontSize: "0.7rem", fontWeight: 700 }}>
                  <span style={{ color: "#ef4444", backgroundColor: "#fff1f2", padding: "0.1rem 0.3rem", borderRadius: "0.2rem" }}>
                    High: {item.high_risk_count}
                  </span>
                  <span style={{ color: "#f59e0b", backgroundColor: "#fffbeb", padding: "0.1rem 0.3rem", borderRadius: "0.2rem" }}>
                    Med: {item.medium_risk_count}
                  </span>
                  <span style={{ color: "#10b981", backgroundColor: "#ecfdf5", padding: "0.1rem 0.3rem", borderRadius: "0.2rem" }}>
                    Low: {item.low_risk_count}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

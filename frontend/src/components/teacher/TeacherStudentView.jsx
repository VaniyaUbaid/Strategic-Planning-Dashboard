import React from "react";
import { useNavigate } from "react-router-dom";
import { ChevronRight, ShieldAlert, BookOpen, UserCheck, AlertCircle } from "lucide-react";

export default function TeacherStudentView({ students = [], onResetFilters }) {
  const navigate = useNavigate();

  if (!students || students.length === 0) {
    return (
      <div className="card" style={{ padding: "3rem", textAlign: "center", color: "#64748b" }}>
        <AlertCircle size={36} style={{ color: "#94a3b8", marginBottom: "0.75rem" }} />
        <h4 style={{ fontSize: "1.1rem", fontWeight: 600, color: "#334155", marginBottom: "0.35rem" }}>
          No student records found for the selected filters.
        </h4>
        <p style={{ fontSize: "0.875rem", color: "#64748b", marginBottom: "1rem" }}>
          Try adjusting or clearing your department, academic year, semester, or risk level filters.
        </p>
        {onResetFilters && (
          <button className="btn-secondary" onClick={onResetFilters}>
            Reset Filters
          </button>
        )}
      </div>
    );
  }

  const getRiskBadgeStyle = (level) => {
    switch (level) {
      case "HIGH":
        return { backgroundColor: "#fff1f2", color: "#be123c", border: "1px solid #fecdd3" };
      case "MEDIUM":
        return { backgroundColor: "#fffbeb", color: "#b45309", border: "1px solid #fef3c7" };
      case "LOW":
        return { backgroundColor: "#ecfdf5", color: "#047857", border: "1px solid #a7f3d0" };
      default:
        return { backgroundColor: "#f1f5f9", color: "#475569", border: "1px solid #cbd5e1" };
    }
  };

  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>Student ID</th>
            <th>Program</th>
            <th>Department</th>
            <th>Sem</th>
            <th>Academic Year</th>
            <th>GPA</th>
            <th>Attendance</th>
            <th>Backlogs</th>
            <th>Dropout Prob</th>
            <th>Risk Level</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {students.map((s) => (
            <tr
              key={s.student_id}
              className="clickable"
              onClick={() => navigate(`/students/${s.student_id}`)}
            >
              <td style={{ fontWeight: 700, color: "#0f172a" }}>{s.student_id}</td>
              <td>{s.program || "N/A"}</td>
              <td>{s.department_id}</td>
              <td>Sem {s.semester}</td>
              <td>{s.academic_year}</td>
              <td style={{ fontWeight: 600, color: s.gpa >= 7.0 ? "#047857" : "#b45309" }}>
                {s.gpa.toFixed(2)}
              </td>
              <td style={{ fontWeight: 600, color: s.attendance_percentage >= 75 ? "#047857" : "#be123c" }}>
                {s.attendance_percentage.toFixed(1)}%
              </td>
              <td style={{ fontWeight: s.backlog_count > 0 ? 700 : 400, color: s.backlog_count > 0 ? "#be123c" : "#475569" }}>
                {s.backlog_count}
              </td>
              <td style={{ fontWeight: 700, color: s.dropout_probability >= 0.60 ? "#be123c" : s.dropout_probability >= 0.40 ? "#b45309" : "#047857" }}>
                {(s.dropout_probability * 100).toFixed(1)}%
              </td>
              <td>
                <span
                  style={{
                    fontSize: "0.75rem",
                    fontWeight: 700,
                    padding: "0.2rem 0.5rem",
                    borderRadius: "0.25rem",
                    display: "inline-block",
                    ...getRiskBadgeStyle(s.risk_level),
                  }}
                >
                  {s.risk_level}
                </span>
              </td>
              <td>
                <button
                  className="btn-secondary"
                  style={{ padding: "0.3rem 0.6rem", fontSize: "0.8rem" }}
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/students/${s.student_id}`);
                  }}
                >
                  Analyze <ChevronRight size={14} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

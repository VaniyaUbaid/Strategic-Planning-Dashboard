import React from "react";

export default function AcademicHistoryTable({ history = [] }) {
  if (!history || history.length === 0) {
    return (
      <div style={{ padding: "2rem", textAlign: "center", color: "#64748b" }}>
        No historical academic records available for this student.
      </div>
    );
  }

  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>Semester</th>
            <th>Year</th>
            <th>Attendance %</th>
            <th>Sem GPA</th>
            <th>Cum GPA</th>
            <th>Backlogs</th>
            <th>Failed</th>
            <th>Passed</th>
            <th>Internal %</th>
            <th>Assignments %</th>
            <th>Pending Fee</th>
            <th>Hist Label</th>
          </tr>
        </thead>
        <tbody>
          {history.map((record) => (
            <tr key={record.semester}>
              <td style={{ fontWeight: 600 }}>Semester {record.semester}</td>
              <td>{record.academic_year}</td>
              <td>
                <span style={{ color: record.attendance_percentage < 75 ? "#be123c" : "#047857", fontWeight: 600 }}>
                  {record.attendance_percentage}%
                </span>
              </td>
              <td>{record.semester_gpa}</td>
              <td style={{ fontWeight: 600 }}>{record.cumulative_gpa}</td>
              <td>
                {record.backlog_count > 0 ? (
                  <span style={{ color: "#be123c", fontWeight: 700 }}>{record.backlog_count}</span>
                ) : (
                  <span>0</span>
                )}
              </td>
              <td>
                {record.courses_failed > 0 ? (
                  <span style={{ color: "#be123c", fontWeight: 700 }}>{record.courses_failed}</span>
                ) : (
                  <span>0</span>
                )}
              </td>
              <td>{record.courses_passed}</td>
              <td>{record.internal_marks_percentage}%</td>
              <td>{record.assignments_completed_pct}%</td>
              <td>₹{Number(record.fee_pending_amount).toLocaleString()}</td>
              <td>
                {record.historical_dropout_label === 1 ? (
                  <span style={{ fontSize: "0.75rem", padding: "0.2rem 0.5rem", borderRadius: "0.25rem", backgroundColor: "#fff1f2", color: "#be123c", fontWeight: 700 }}>
                    Dropout Event
                  </span>
                ) : (
                  <span style={{ fontSize: "0.75rem", padding: "0.2rem 0.5rem", borderRadius: "0.25rem", backgroundColor: "#f1f5f9", color: "#475569" }}>
                    Enrolled
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

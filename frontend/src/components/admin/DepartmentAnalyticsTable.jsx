import React from "react";
import { Building2 } from "lucide-react";
import { formatINR } from "../../utils/currency";

export default function DepartmentAnalyticsTable({ deptData = [] }) {
  if (!deptData || deptData.length === 0) {
    return (
      <div style={{ padding: "2rem", textAlign: "center", color: "#64748b" }}>
        No department analytics available for the selected filters.
      </div>
    );
  }

  return (
    <div className="card" style={{ marginBottom: "2rem" }}>
      <div className="card-header">
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Building2 size={20} className="text-blue-600" />
          <h3 className="card-title">Department Performance & Risk Breakdown</h3>
        </div>
        <span style={{ fontSize: "0.8rem", color: "#64748b" }}>
          {deptData.length} Active Departments
        </span>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Department</th>
              <th>Total Students</th>
              <th>Avg GPA</th>
              <th>Avg Attendance</th>
              <th>High Risk</th>
              <th>High Risk %</th>
              <th>Medium Risk</th>
              <th>Low Risk</th>
              <th>Students with Backlogs</th>
              <th>Pending Fees Count</th>
              <th>Total Pending Fees</th>
            </tr>
          </thead>
          <tbody>
            {deptData.map((dept) => (
              <tr key={dept.department_id}>
                <td style={{ fontWeight: 700, color: "#0f172a" }}>
                  <div>{dept.department_name}</div>
                  <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 600 }}>
                    ID: {dept.department_id}
                  </span>
                </td>
                <td style={{ fontWeight: 600 }}>{dept.total_students.toLocaleString()}</td>
                <td style={{ fontWeight: 600, color: dept.avg_gpa >= 7.0 ? "#047857" : "#b45309" }}>
                  {dept.avg_gpa.toFixed(2)}
                </td>
                <td style={{ fontWeight: 600, color: dept.avg_attendance >= 75 ? "#047857" : "#be123c" }}>
                  {dept.avg_attendance.toFixed(1)}%
                </td>
                <td>
                  <span
                    style={{
                      fontWeight: 700,
                      color: "#be123c",
                      backgroundColor: "#fff1f2",
                      padding: "0.2rem 0.5rem",
                      borderRadius: "0.25rem",
                    }}
                  >
                    {dept.high_risk_count.toLocaleString()}
                  </span>
                </td>
                <td style={{ fontWeight: 700 }}>
                  {dept.total_students > 0
                    ? `${((dept.high_risk_count / dept.total_students) * 100).toFixed(1)}%`
                    : "—"}
                </td>
                <td>
                  <span
                    style={{
                      fontWeight: 700,
                      color: "#b45309",
                      backgroundColor: "#fffbeb",
                      padding: "0.2rem 0.5rem",
                      borderRadius: "0.25rem",
                    }}
                  >
                    {dept.medium_risk_count.toLocaleString()}
                  </span>
                </td>
                <td style={{ fontWeight: 600, color: "#047857" }}>
                  {dept.low_risk_count.toLocaleString()}
                </td>
                <td>{dept.students_with_backlogs.toLocaleString()}</td>
                <td>{dept.students_fee_pending.toLocaleString()}</td>
                <td style={{ fontWeight: 600, color: dept.total_fee_pending > 0 ? "#b45309" : "#047857" }}>
                  {formatINR(dept.total_fee_pending)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

import React from "react";
import { useNavigate } from "react-router-dom";
import { ChevronRight, Award, Home } from "lucide-react";

export default function StudentTable({ students = [] }) {
  const navigate = useNavigate();

  if (!students || students.length === 0) {
    return (
      <div style={{ padding: "3rem", textAlign: "center", color: "#64748b" }}>
        No student records match the search filter.
      </div>
    );
  }

  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>Student ID</th>
            <th>Program</th>
            <th>Department</th>
            <th>Latest Sem</th>
            <th>Academic Year</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {students.map((student) => (
            <tr
              key={student.student_id}
              className="clickable"
              onClick={() => navigate(`/students/${student.student_id}`)}
            >
              <td style={{ fontWeight: 600, color: "#1e293b" }}>{student.student_id}</td>
              <td>{student.program || "N/A"}</td>
              <td>{student.department_id || "N/A"}</td>
              <td>Sem {student.latest_semester}</td>
              <td>{student.latest_academic_year}</td>
              <td>
                <button
                  className="btn-secondary"
                  style={{ padding: "0.3rem 0.6rem", fontSize: "0.8rem" }}
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/students/${student.student_id}`);
                  }}
                >
                  Analyze Risk <ChevronRight size={14} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

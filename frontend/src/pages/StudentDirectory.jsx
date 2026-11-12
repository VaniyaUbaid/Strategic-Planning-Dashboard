import React, { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowDownToLine, ChevronLeft, ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import DepartmentPerformanceHeader from "../components/common/DepartmentPerformanceHeader";
import ErrorAlert from "../components/common/ErrorAlert";
import FilterBar from "../components/common/FilterBar";
import LoadingSpinner from "../components/common/LoadingSpinner";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import "./StudentDirectory.css";

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

export default function StudentDirectory() {
  const navigate = useNavigate();
  const { role, department } = useAuth();
  const isHod = role === "HOD";
  const [filters, setFilters] = useState({
    department: isHod ? department || "" : "",
    academicYear: "",
    semester: "",
    riskLevel: "",
    program: "",
    search: "",
  });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [studentData, setStudentData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  const effectiveFilters = useMemo(
    () => (isHod ? { ...filters, department: department || "" } : filters),
    [department, filters, isHod],
  );

  const requestFilters = useMemo(() => ({
    department: effectiveFilters.department,
    program: effectiveFilters.program,
    academic_year: effectiveFilters.academicYear,
    semester: effectiveFilters.semester,
    risk_level: effectiveFilters.riskLevel,
    search: effectiveFilters.search,
  }), [effectiveFilters]);

  const fetchStudents = useCallback(() => api.getStudentDirectory(page, pageSize, requestFilters), [
    page,
    pageSize,
    requestFilters,
  ]);

  useEffect(() => {
    let cancelled = false;
    const timer = window.setTimeout(() => {
      setLoading(true);
      setError(null);
      fetchStudents()
        .then((data) => {
          if (cancelled) return;
          setStudentData(data);
          setError(null);
        })
        .catch((requestError) => {
          if (cancelled) return;
          setError(requestError.message || "Failed to load the enrolled student directory.");
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }, filters.search ? 250 : 0);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [fetchStudents, filters.search, reloadKey]);

  const handleFilterChange = (nextFilters) => {
    setFilters(nextFilters);
    setPage(1);
    setLoading(true);
    setError(null);
  };

  const exportFilteredRecords = async () => {
    setExporting(true);
    setExportError(null);
    try {
      const csv = await api.downloadStudentsCsv(requestFilters);
      const url = URL.createObjectURL(csv);
      const link = document.createElement("a");
      link.href = url;
      link.download = "enrolled-students.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 0);
    } catch (exportRequestError) {
      setExportError(exportRequestError.message || "Could not export the filtered student records.");
    } finally {
      setExporting(false);
    }
  };

  const totalStudents = studentData?.total_students || 0;
  const totalPages = studentData?.total_pages || 0;
  const currentPage = studentData?.page || 1;
  const firstRecord = totalStudents === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const lastRecord = Math.min(currentPage * pageSize, totalStudents);

  return (
    <div className="student-directory-page">
      <DepartmentPerformanceHeader
        title="Enrolled Students Directory"
        description="Search and review the latest matching academic and dropout-risk record for each student."
        backTo="/students"
        backLabel="Back to Student Success Dashboard"
      />

      <FilterBar
        filters={effectiveFilters}
        onFilterChange={handleFilterChange}
        showRiskFilter
        showSearch
        showProgramFilter
      />

      <section className="card student-directory-card" aria-label="Enrolled students">
        <div className="student-directory-toolbar">
          <div>
            <h2 className="card-title">Student Records</h2>
            <p className="student-directory-count">
              {loading
                ? "Updating results..."
                : `${totalStudents.toLocaleString()} matching students`}
            </p>
          </div>
          <div className="student-directory-actions">
            <label className="student-directory-page-size">
              <span>Rows per page</span>
              <select
                value={pageSize}
                onChange={(event) => {
                  setLoading(true);
                  setPageSize(Number(event.target.value));
                  setPage(1);
                }}
              >
                {PAGE_SIZE_OPTIONS.map((size) => (
                  <option key={size} value={size}>{size}</option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="btn-primary"
              onClick={exportFilteredRecords}
              disabled={loading || exporting || totalStudents === 0}
            >
              <ArrowDownToLine size={16} />
              {exporting ? "Preparing CSV..." : "Export filtered CSV"}
            </button>
          </div>
        </div>

        {exportError && <p className="student-directory-export-error" role="alert">{exportError}</p>}

        {loading ? (
          <LoadingSpinner message="Loading enrolled student records..." />
        ) : error ? (
          <ErrorAlert message={error} onRetry={() => setReloadKey((value) => value + 1)} />
        ) : totalStudents === 0 ? (
          <div className="student-directory-empty" role="status">
            <h3>No student records match these filters.</h3>
            <p>Try changing the search, department, program, academic year, semester, or risk level.</p>
          </div>
        ) : (
          <>
            <div className="table-container student-directory-table-container">
              <table className="data-table student-directory-table">
                <thead>
                  <tr>
                    <th>Student ID</th>
                    <th>Program</th>
                    <th>Department</th>
                    <th>Semester</th>
                    <th>Academic Year</th>
                    <th>GPA</th>
                    <th>Attendance</th>
                    <th>Backlogs</th>
                    <th>Dropout Probability</th>
                    <th>Risk Level</th>
                  </tr>
                </thead>
                <tbody>
                  {studentData.students.map((student) => (
                    <tr
                      key={student.student_id}
                      className="clickable"
                      onClick={() => navigate(`/students/${encodeURIComponent(student.student_id)}`)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") {
                          navigate(`/students/${encodeURIComponent(student.student_id)}`);
                        }
                      }}
                      tabIndex={0}
                    >
                      <td className="student-directory-id">{student.student_id}</td>
                      <td>{student.program || "N/A"}</td>
                      <td>{student.department_name || student.department_id}</td>
                      <td>Semester {student.semester}</td>
                      <td>{student.academic_year}</td>
                      <td>{Number(student.gpa).toFixed(2)}</td>
                      <td>{Number(student.attendance_percentage).toFixed(1)}%</td>
                      <td>{student.backlog_count}</td>
                      <td>{(Number(student.dropout_probability) * 100).toFixed(1)}%</td>
                      <td>
                        <span className={`student-directory-risk ${student.risk_level.toLowerCase()}`}>
                          {student.risk_level}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="student-directory-pagination">
              <span>
                Showing {firstRecord.toLocaleString()}–{lastRecord.toLocaleString()} of {totalStudents.toLocaleString()}
              </span>
              <div className="student-directory-page-controls">
                <button
                  type="button"
                  className="btn-secondary"
                  disabled={currentPage <= 1}
                  onClick={() => {
                    setLoading(true);
                    setPage((value) => Math.max(1, value - 1));
                  }}
                >
                  <ChevronLeft size={16} /> Previous
                </button>
                <span>Page {currentPage.toLocaleString()} of {totalPages.toLocaleString()}</span>
                <button
                  type="button"
                  className="btn-secondary"
                  disabled={currentPage >= totalPages}
                  onClick={() => {
                    setLoading(true);
                    setPage((value) => Math.min(totalPages, value + 1));
                  }}
                >
                  Next <ChevronRight size={16} />
                </button>
              </div>
            </div>
          </>
        )}
      </section>
    </div>
  );
}

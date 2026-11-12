import React, { useState, useEffect } from "react";
import { Filter, Search, RotateCcw, Lock, Building2, Calendar, BookOpen, ShieldAlert } from "lucide-react";
import { api } from "../../services/api";
import { useRole } from "../../context/RoleContext";

export default function FilterBar({
  filters = {},
  onFilterChange,
  showRiskFilter = true,
  showSearch = true,
  showProgramFilter = false,
}) {
  const { activeRole, userDepartment } = useRole();

  const [departments, setDepartments] = useState([]);
  const [academicYears, setAcademicYears] = useState([]);
  const [semesters, setSemesters] = useState([]);
  const [programs, setPrograms] = useState([]);

  const isDepartmentLocked = activeRole === "HOD" || activeRole === "PROFESSOR";

  // Fetch departments on mount & role change
  useEffect(() => {
    api
      .getAccessibleDepartments()
      .then((data) => setDepartments(data || []))
      .catch((err) => {
        console.warn("Could not fetch departments:", err);
      });
  }, [activeRole, userDepartment]);

  // Fetch dynamic dependent years when department changes
  useEffect(() => {
    const deptToUse = isDepartmentLocked ? userDepartment : filters.department;
    api
      .getAccessibleYears(deptToUse)
      .then((data) => setAcademicYears(data || []))
      .catch((err) => console.warn("Could not fetch years:", err));
  }, [filters.department, activeRole, userDepartment, isDepartmentLocked]);

  // Fetch dynamic dependent semesters when department or academic year changes
  useEffect(() => {
    const deptToUse = isDepartmentLocked ? userDepartment : filters.department;
    api
      .getAccessibleSemesters(deptToUse, filters.academicYear)
      .then((data) => setSemesters(data || []))
      .catch((err) => console.warn("Could not fetch semesters:", err));
  }, [filters.department, filters.academicYear, activeRole, userDepartment, isDepartmentLocked]);

  useEffect(() => {
    if (!showProgramFilter) return undefined;
    const deptToUse = isDepartmentLocked ? userDepartment : filters.department;
    api
      .getStudentFilters({ department: deptToUse, academic_year: filters.academicYear })
      .then((data) => setPrograms(data.programs || []))
      .catch((err) => {
        console.warn("Could not fetch programs:", err);
        setPrograms([]);
      });
    return undefined;
  }, [showProgramFilter, filters.department, filters.academicYear, activeRole, userDepartment, isDepartmentLocked]);

  const handleChange = (key, value) => {
    const nextFilters = { ...filters, [key]: value };

    // Reset dependent filters if parent changes
    if (key === "department") {
      nextFilters.academicYear = "";
      nextFilters.semester = "";
      nextFilters.program = "";
    } else if (key === "academicYear") {
      nextFilters.semester = "";
      nextFilters.program = "";
    }

    onFilterChange(nextFilters);
  };

  const handleReset = () => {
    onFilterChange({
      department: isDepartmentLocked ? userDepartment : "",
      academicYear: "",
      semester: "",
      riskLevel: "",
      search: "",
      program: "",
    });
  };

  return (
    <div
      className="card"
      style={{
        padding: "1rem 1.25rem",
        marginBottom: "1.5rem",
        backgroundColor: "#ffffff",
        borderColor: "#cbd5e1",
        boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.75rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "#1e293b", fontWeight: 700, fontSize: "0.95rem" }}>
          <Filter size={18} className="text-blue-600" />
          <span>Dynamic Hierarchical Data Filters</span>
        </div>

        {isDepartmentLocked && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.35rem",
              fontSize: "0.75rem",
              fontWeight: 700,
              backgroundColor: "#fef3c7",
              color: "#92400e",
              padding: "0.25rem 0.6rem",
              borderRadius: "0.25rem",
              border: "1px solid #fcd34d",
            }}
          >
            <Lock size={12} />
            <span>Scope Locked: {userDepartment} Department</span>
          </div>
        )}
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "1rem",
          alignItems: "end",
        }}
      >
        {/* Department Filter */}
        <div>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 700, color: "#475569", marginBottom: "0.35rem" }}>
            <Building2 size={13} style={{ display: "inline", marginRight: "0.25rem" }} /> DEPARTMENT
          </label>
          {isDepartmentLocked ? (
            <div
              style={{
                padding: "0.5rem 0.75rem",
                borderRadius: "0.5rem",
                backgroundColor: "#f1f5f9",
                border: "1px solid #cbd5e1",
                fontSize: "0.875rem",
                fontWeight: 600,
                color: "#334155",
                display: "flex",
                alignItems: "center",
                justifySpace: "between",
              }}
            >
              <span>{departments.find((d) => d.id === userDepartment)?.name || userDepartment}</span>
              <Lock size={14} style={{ color: "#64748b", marginLeft: "auto" }} />
            </div>
          ) : (
            <select
              value={filters.department || ""}
              onChange={(e) => handleChange("department", e.target.value)}
              style={{
                width: "100%",
                padding: "0.5rem 0.75rem",
                borderRadius: "0.5rem",
                border: "1px solid #cbd5e1",
                fontSize: "0.875rem",
                backgroundColor: "#ffffff",
                outline: "none",
              }}
            >
              <option value="">All Departments</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.id})
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Academic Year Filter */}
        <div>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 700, color: "#475569", marginBottom: "0.35rem" }}>
            <Calendar size={13} style={{ display: "inline", marginRight: "0.25rem" }} /> ACADEMIC YEAR
          </label>
          <select
            value={filters.academicYear || ""}
            onChange={(e) => handleChange("academicYear", e.target.value)}
            style={{
              width: "100%",
              padding: "0.5rem 0.75rem",
              borderRadius: "0.5rem",
              border: "1px solid #cbd5e1",
              fontSize: "0.875rem",
              backgroundColor: "#ffffff",
              outline: "none",
            }}
          >
            <option value="">All Academic Years</option>
            {academicYears.map((yr) => (
              <option key={yr} value={yr}>
                Academic Year {yr}
              </option>
            ))}
          </select>
        </div>

        {/* Semester Filter */}
        <div>
          <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 700, color: "#475569", marginBottom: "0.35rem" }}>
            <BookOpen size={13} style={{ display: "inline", marginRight: "0.25rem" }} /> SEMESTER
          </label>
          <select
            value={filters.semester || ""}
            onChange={(e) => handleChange("semester", e.target.value)}
            style={{
              width: "100%",
              padding: "0.5rem 0.75rem",
              borderRadius: "0.5rem",
              border: "1px solid #cbd5e1",
              fontSize: "0.875rem",
              backgroundColor: "#ffffff",
              outline: "none",
            }}
          >
            <option value="">All Semesters</option>
            {semesters.map((sem) => (
              <option key={sem} value={sem}>
                Semester {sem}
              </option>
            ))}
          </select>
        </div>

        {/* Risk Level Filter */}
        {showRiskFilter && (
          <div>
            <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 700, color: "#475569", marginBottom: "0.35rem" }}>
              <ShieldAlert size={13} style={{ display: "inline", marginRight: "0.25rem" }} /> RISK LEVEL
            </label>
            <select
              value={filters.riskLevel || ""}
              onChange={(e) => handleChange("riskLevel", e.target.value)}
              style={{
                width: "100%",
                padding: "0.5rem 0.75rem",
                borderRadius: "0.5rem",
                border: "1px solid #cbd5e1",
                fontSize: "0.875rem",
                backgroundColor: "#ffffff",
                outline: "none",
              }}
            >
              <option value="">All Risk Levels</option>
              <option value="HIGH">🔴 High Risk (≥60%)</option>
              <option value="MEDIUM">🟡 Medium Risk (40-59%)</option>
              <option value="LOW">🟢 Low Risk (&lt;40%)</option>
            </select>
          </div>
        )}

        {showProgramFilter && (
          <div>
            <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 700, color: "#475569", marginBottom: "0.35rem" }}>
              <BookOpen size={13} style={{ display: "inline", marginRight: "0.25rem" }} /> PROGRAM
            </label>
            <select
              value={filters.program || ""}
              onChange={(e) => handleChange("program", e.target.value)}
              style={{
                width: "100%",
                padding: "0.5rem 0.75rem",
                borderRadius: "0.5rem",
                border: "1px solid #cbd5e1",
                fontSize: "0.875rem",
                backgroundColor: "#ffffff",
                outline: "none",
              }}
            >
              <option value="">All Programs</option>
              {programs.map((program) => (
                <option key={program} value={program}>{program}</option>
              ))}
            </select>
          </div>
        )}

        {/* Search Input */}
        {showSearch && (
          <div style={{ position: "relative" }}>
            <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 700, color: "#475569", marginBottom: "0.35rem" }}>
              SEARCH STUDENT ID
            </label>
            <div style={{ position: "relative" }}>
              <Search
                size={14}
                style={{ position: "absolute", left: "0.6rem", top: "50%", transform: "translateY(-50%)", color: "#94a3b8" }}
              />
              <input
                type="text"
                placeholder="STU00042..."
                value={filters.search || ""}
                onChange={(e) => handleChange("search", e.target.value)}
                style={{
                  width: "100%",
                  padding: "0.45rem 0.6rem 0.45rem 2rem",
                  borderRadius: "0.5rem",
                  border: "1px solid #cbd5e1",
                  fontSize: "0.875rem",
                  outline: "none",
                }}
              />
            </div>
          </div>
        )}

        {/* Reset Button */}
        <div>
          <button
            onClick={handleReset}
            className="btn-secondary"
            style={{ width: "100%", justifyContent: "center", padding: "0.5rem" }}
          >
            <RotateCcw size={14} /> Reset Filters
          </button>
        </div>
      </div>
    </div>
  );
}

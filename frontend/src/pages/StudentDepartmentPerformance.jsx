import React, { useCallback, useEffect, useState } from "react";
import { Activity, AlertTriangle, GraduationCap, ShieldAlert, TrendingUp } from "lucide-react";
import { Navigate } from "react-router-dom";
import DepartmentAnalyticsTable from "../components/admin/DepartmentAnalyticsTable";
import DepartmentPerformanceCharts from "../components/admin/DepartmentCharts";
import DepartmentPerformanceHeader from "../components/common/DepartmentPerformanceHeader";
import DepartmentPerformanceKpiCard from "../components/common/DepartmentPerformanceKpiCard";
import "../components/common/DepartmentPerformance.css";
import ErrorAlert from "../components/common/ErrorAlert";
import FilterBar from "../components/common/FilterBar";
import LoadingSpinner from "../components/common/LoadingSpinner";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";

export default function StudentDepartmentPerformance() {
  const { role, department } = useAuth();
  const isHod = role === "HOD";
  const assignedDepartment = isHod ? (department || "CSE") : "";
  const [filters, setFilters] = useState({
    department: assignedDepartment,
    academicYear: "",
    semester: "",
    riskLevel: "",
    search: "",
  });
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isHod) {
      setFilters((current) => ({ ...current, department: assignedDepartment }));
    }
  }, [assignedDepartment, isHod]);

  const fetchDepartmentData = useCallback(() => api.getOverview({
    department: isHod ? assignedDepartment : filters.department,
    academic_year: filters.academicYear,
    semester: filters.semester,
    risk_level: filters.riskLevel,
  }), [assignedDepartment, filters, isHod]);

  useEffect(() => {
    let cancelled = false;
    fetchDepartmentData()
      .then((data) => {
        if (cancelled) return;
        setOverview(data);
        setError(null);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.message || "Failed to load student department performance.");
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [fetchDepartmentData]);

  if (role !== "ADMINISTRATOR" && !isHod) return <Navigate to="/students" replace />;

  const departments = overview?.department_chart || [];
  const totalStudents = overview?.total_students || 0;
  const handleFilterChange = (nextFilters) => {
    setFilters(nextFilters);
    setLoading(true);
    setError(null);
  };

  return (
    <div className="department-performance-page">
      <DepartmentPerformanceHeader
        title="Student Department Performance"
        description="Compare student risk and academic outcomes using the latest matching record for each student."
        backTo="/students"
        backLabel="Back to Student Dashboard"
      />

      <FilterBar filters={filters} onFilterChange={handleFilterChange} showRiskFilter showSearch={false} />

      {loading ? (
        <LoadingSpinner message="Loading student department performance..." />
      ) : error ? (
        <ErrorAlert message={error} onRetry={() => {
          setLoading(true);
          fetchDepartmentData()
            .then((data) => {
              setOverview(data);
              setLoading(false);
            })
            .catch((err) => {
              setError(err.message || "Failed to load student department performance.");
              setLoading(false);
            });
        }} />
      ) : totalStudents === 0 ? (
        <div className="card" style={{ padding: "2rem", textAlign: "center", color: "#64748b" }} role="status">
          No student records are available for the selected filters.
        </div>
      ) : (
        <>
          <section className="department-performance-kpis" aria-label="Student department performance indicators">
            <DepartmentPerformanceKpiCard label="TOTAL STUDENTS" value={totalStudents.toLocaleString()} icon={GraduationCap} />
            <DepartmentPerformanceKpiCard label="HIGH-RISK STUDENTS" value={(overview?.high_risk_count || 0).toLocaleString()} icon={AlertTriangle} tone="red" />
            <DepartmentPerformanceKpiCard label="MEDIUM-RISK STUDENTS" value={(overview?.medium_risk_count || 0).toLocaleString()} icon={ShieldAlert} tone="amber" />
            <DepartmentPerformanceKpiCard label="LOW-RISK STUDENTS" value={(overview?.low_risk_count || 0).toLocaleString()} icon={ShieldAlert} tone="teal" />
            <DepartmentPerformanceKpiCard label="HIGH-RISK SHARE" value={`${Number(overview?.risk_distribution?.high_pct || 0).toFixed(1)}%`} icon={ShieldAlert} tone="amber" />
            <DepartmentPerformanceKpiCard label="AVERAGE GPA" value={Number(overview?.average_gpa || 0).toFixed(2)} icon={TrendingUp} tone="teal" />
            <DepartmentPerformanceKpiCard label="AVERAGE ATTENDANCE" value={`${Number(overview?.average_attendance || 0).toFixed(1)}%`} icon={Activity} />
            <DepartmentPerformanceKpiCard label="AVERAGE DROPOUT PROBABILITY" value={`${(Number(overview?.average_dropout_probability || 0) * 100).toFixed(1)}%`} icon={Activity} tone="amber" />
            <DepartmentPerformanceKpiCard label="STUDENTS WITH BACKLOGS" value={(overview?.students_with_backlogs || 0).toLocaleString()} icon={AlertTriangle} tone="amber" />
          </section>

          <p className="department-performance-note">
            Risk rates use the same filtered latest-per-student population as the KPI totals. GPA and attendance are student averages, not semester-record totals.
          </p>
          <DepartmentPerformanceCharts data={departments} />
          <DepartmentAnalyticsTable deptData={departments} />
        </>
      )}
    </div>
  );
}

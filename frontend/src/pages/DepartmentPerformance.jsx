import React, { useCallback, useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { Link, Navigate } from "react-router-dom";
import DepartmentAnalyticsTable from "../components/admin/DepartmentAnalyticsTable";
import DepartmentPerformanceCharts from "../components/admin/DepartmentCharts";
import ErrorAlert from "../components/common/ErrorAlert";
import FilterBar from "../components/common/FilterBar";
import LoadingSpinner from "../components/common/LoadingSpinner";
import { useRole } from "../context/RoleContext";
import { api } from "../services/api";

export default function DepartmentPerformance() {
  const { activeRole, userDepartment } = useRole();
  const [filters, setFilters] = useState({
    department: activeRole === "ADMINISTRATOR" ? "" : userDepartment,
    academicYear: "",
    semester: "",
    riskLevel: "",
    search: "",
  });
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDepartmentData = useCallback(() => api.getOverview({
      department: activeRole === "ADMINISTRATOR" ? filters.department : userDepartment,
      academic_year: filters.academicYear,
      semester: filters.semester,
      risk_level: filters.riskLevel,
    }), [activeRole, filters, userDepartment]);

  useEffect(() => {
    if (activeRole !== "ADMINISTRATOR" && activeRole !== "HOD") return undefined;

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
        setError(err.message || "Failed to load department performance.");
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [activeRole, fetchDepartmentData]);

  if (activeRole !== "ADMINISTRATOR" && activeRole !== "HOD") {
    return <Navigate to="/" replace />;
  }

  const departmentData = overview?.department_chart || [];
  const handleFilterChange = (nextFilters) => {
    setLoading(true);
    setError(null);
    setFilters(nextFilters);
  };
  const handleRetry = () => {
    setLoading(true);
    setError(null);
    fetchDepartmentData()
      .then((data) => {
        setOverview(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load department performance.");
        setLoading(false);
      });
  };

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem", marginBottom: "1.25rem" }}>
        <div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#0f172a", marginBottom: "0.25rem" }}>
            Department Performance
          </h1>
          <p style={{ color: "#475569", fontSize: "0.95rem" }}>
            Performance and risk breakdown for the selected department scope.
          </p>
        </div>
        <Link to="/" className="btn-secondary">
          <ArrowLeft size={16} /> Back to Overview
        </Link>
      </div>

      <FilterBar filters={filters} onFilterChange={handleFilterChange} showRiskFilter showSearch={false} />

      {loading ? (
        <LoadingSpinner message="Loading department performance..." />
      ) : error ? (
        <ErrorAlert message={error} onRetry={handleRetry} />
      ) : (
        <>
          <DepartmentPerformanceCharts data={departmentData} />
          <DepartmentAnalyticsTable deptData={departmentData} />
        </>
      )}
    </div>
  );
}

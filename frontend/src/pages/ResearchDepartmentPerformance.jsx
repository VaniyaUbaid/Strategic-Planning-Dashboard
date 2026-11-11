import React, { useCallback, useEffect, useState } from "react";
import { Activity, BookOpen, GraduationCap, Users } from "lucide-react";
import { Navigate } from "react-router-dom";
import ErrorAlert from "../components/common/ErrorAlert";
import DepartmentPerformanceHeader from "../components/common/DepartmentPerformanceHeader";
import DepartmentPerformanceKpiCard from "../components/common/DepartmentPerformanceKpiCard";
import LoadingSpinner from "../components/common/LoadingSpinner";
import ResearchDepartmentAnalytics from "../components/research/ResearchDepartmentAnalytics";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import "../components/common/DepartmentPerformance.css";
import "./Research.css";

const numberFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const decimalFormat = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function ResearchDepartmentPerformance() {
  const { role, department } = useAuth();
  const isHod = role === "HOD";
  const assignedDepartment = isHod ? (department || "CSE") : "";
  const [filterOptions, setFilterOptions] = useState({ departments: [], programs: [], admission_years: [] });
  const [filters, setFilters] = useState({
    department: assignedDepartment,
    program: "",
    admission_year: "",
  });
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterError, setFilterError] = useState(null);

  useEffect(() => {
    if (isHod) {
      setFilters((current) => ({ ...current, department: assignedDepartment }));
    }
  }, [assignedDepartment, isHod]);

  const fetchFilterOptions = useCallback(() => api.getResearchFilters()
    .then((options) => {
      setFilterOptions(options);
      setFilterError(null);
    })
    .catch((err) => setFilterError(err.message || "Unable to load research filters.")), []);

  useEffect(() => {
    fetchFilterOptions();
  }, [fetchFilterOptions]);

  const fetchDepartmentData = useCallback(() => {
    const params = {
      department: isHod ? assignedDepartment : filters.department,
      program: filters.program,
      admission_year: filters.admission_year,
    };
    return Promise.all([
      api.getResearchOverview(params),
      api.getResearchDepartments(params),
    ]).then(([overview, departmentResponse]) => ({
      overview,
      departments: departmentResponse.departments || [],
    }));
  }, [assignedDepartment, filters, isHod]);

  useEffect(() => {
    let cancelled = false;
    fetchDepartmentData()
      .then((result) => {
        if (cancelled) return;
        setAnalytics(result);
        setError(null);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.message || "Failed to load research department performance.");
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [fetchDepartmentData]);

  if (role !== "ADMINISTRATOR" && !isHod) return <Navigate to="/research" replace />;

  const handleFilterChange = (key, value) => {
    setFilters((current) => ({ ...current, [key]: value }));
    setLoading(true);
    setError(null);
  };
  const retry = () => {
    setLoading(true);
    setError(null);
    fetchDepartmentData()
      .then((result) => {
        setAnalytics(result);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load research department performance.");
        setLoading(false);
      });
  };

  return (
    <div className="department-performance-page">
      <DepartmentPerformanceHeader
        title="Research Department Performance"
        description="Compare research participation and publication productivity using department-level student records."
        backTo="/research"
        backLabel="Back to Research Dashboard"
      />

      <section className="card research-filter-card" aria-label="Research department performance filters">
        <div className="research-filter-title"><Activity size={18} color="#2563eb" /> Research data filters</div>
        {filterError ? (
          <ErrorAlert message={filterError} onRetry={fetchFilterOptions} />
        ) : (
          <div className="research-filter-grid">
            <label className="research-filter-field">
              Department
              {isHod ? (
                <div className="department-scope-lock">{assignedDepartment} (Assigned Department)</div>
              ) : (
                <select value={filters.department} onChange={(event) => handleFilterChange("department", event.target.value)}>
                  <option value="">All departments</option>
                  {filterOptions.departments.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              )}
            </label>
            <label className="research-filter-field">
              Program
              <select value={filters.program} onChange={(event) => handleFilterChange("program", event.target.value)}>
                <option value="">All programs</option>
                {filterOptions.programs.map((program) => <option key={program} value={program}>{program}</option>)}
              </select>
            </label>
            <label className="research-filter-field">
              Admission year
              <select value={filters.admission_year} onChange={(event) => handleFilterChange("admission_year", event.target.value)}>
                <option value="">All admission years</option>
                {filterOptions.admission_years.map((year) => <option key={year} value={year}>{year}</option>)}
              </select>
            </label>
          </div>
        )}
      </section>

      {loading ? (
        <LoadingSpinner message="Loading research department performance..." />
      ) : error ? (
        <ErrorAlert message={error} onRetry={retry} />
      ) : analytics?.overview.total_students === 0 ? (
        <div className="card research-empty" role="status">No research data available for the selected filters.</div>
      ) : (
        <>
          <section className="department-performance-kpis" aria-label="Research department indicators">
            <DepartmentPerformanceKpiCard label="TOTAL STUDENTS" value={numberFormat.format(analytics.overview.total_students)} icon={GraduationCap} />
            <DepartmentPerformanceKpiCard label="RESEARCH PARTICIPANTS" value={numberFormat.format(analytics.overview.research_participants)} icon={Users} tone="teal" />
            <DepartmentPerformanceKpiCard label="PARTICIPATION RATE" value={`${decimalFormat.format(analytics.overview.research_participation_rate)}%`} icon={Activity} />
            <DepartmentPerformanceKpiCard label="TOTAL PUBLICATIONS" value={numberFormat.format(analytics.overview.total_publications)} icon={BookOpen} />
            <DepartmentPerformanceKpiCard label="AVG PUBLICATIONS*" value={decimalFormat.format(analytics.overview.average_publications)} icon={BookOpen} tone="amber" />
          </section>
          <p className="department-performance-note">
            Publication totals include reported values. The average excludes missing publication counts; no funding data is available in this dataset.
          </p>
          <ResearchDepartmentAnalytics departments={analytics.departments} />
        </>
      )}
    </div>
  );
}

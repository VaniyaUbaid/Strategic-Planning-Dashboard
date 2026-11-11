import React, { useCallback, useEffect, useState } from "react";
import {
  Activity,
  BookOpen,
  Building2,
  Filter,
  GraduationCap,
  Lock,
  RotateCcw,
  Users,
  ArrowRight,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Link } from "react-router-dom";

import ErrorAlert from "../components/common/ErrorAlert";
import LoadingSpinner from "../components/common/LoadingSpinner";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import "./Research.css";

const PARTICIPATION_COLORS = ["#2563eb", "#94a3b8", "#f59e0b", "#8b5cf6"];
const numberFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const decimalFormat = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function EmptyChart({ message = "No research data available for the selected filters." }) {
  return <div className="research-empty">{message}</div>;
}

function KpiCard({ label, value, icon: Icon }) {
  return (
    <div className="card research-kpi">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.75rem" }}>
        <div style={{ minWidth: 0 }}>
          <span className="research-kpi-label">{label}</span>
          <div className="research-kpi-value">{value}</div>
        </div>
        <span className="research-kpi-icon"><Icon size={21} /></span>
      </div>
    </div>
  );
}

export default function Research() {
  const { role, department } = useAuth();
  const isHod = role === "HOD";
  const userDept = isHod ? (department || "CSE") : "";

  const [filterOptions, setFilterOptions] = useState({ departments: [], programs: [], admission_years: [] });
  const [filters, setFilters] = useState({
    department: userDept,
    program: "",
    admission_year: "",
  });

  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [optionsError, setOptionsError] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (isHod) {
      setFilters((prev) => ({ ...prev, department: userDept }));
    }
  }, [isHod, userDept]);

  const fetchFilterOptions = useCallback(() => {
    setOptionsError(false);
    return api.getResearchFilters()
      .then((options) => setFilterOptions(options))
      .catch(() => setOptionsError(true));
  }, []);

  useEffect(() => {
    fetchFilterOptions();
  }, [fetchFilterOptions]);

  const fetchAnalytics = useCallback(() => {
    setLoading(true);
    setError(false);
    const params = {
      department: isHod ? userDept : filters.department,
      program: filters.program,
      admission_year: filters.admission_year,
    };
    Promise.all([
      api.getResearchOverview(params),
      api.getResearchPublications(params),
      api.getResearchParticipation(params),
    ])
      .then(([overview, publications, participation]) => {
        setAnalytics({
          overview,
          publications: publications.distribution,
          participation: participation.distribution,
        });
      })
      .catch(() => {
        setAnalytics(null);
        setError(true);
      })
      .finally(() => setLoading(false));
  }, [filters, isHod, userDept]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const resetFilters = () =>
    setFilters({
      department: isHod ? userDept : "",
      program: "",
      admission_year: "",
    });

  const isEmpty = analytics?.overview.total_students === 0;
  const participationData = (analytics?.participation || []).map((item, index) => ({
    ...item,
    color: PARTICIPATION_COLORS[index % PARTICIPATION_COLORS.length],
  }));
  return (
    <div className="research-page">
      <header className="research-heading">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <h1>Research Profile Dashboard</h1>
            <p>
              {isHod
                ? `Department Research Analytics for ${userDept}`
                : "Institutional research participation, publication output, and research profile."}
            </p>
          </div>
          {(role === "ADMINISTRATOR" || isHod) && (
            <Link to="/research/department-performance" className="btn-primary">
              View Department Performance <ArrowRight size={17} />
            </Link>
          )}
        </div>
      </header>

      <section className="card research-filter-card" aria-label="Research filters">
        <div className="research-filter-title"><Filter size={18} color="#2563eb" /> Research data filters</div>
        {optionsError ? (
          <ErrorAlert message="Unable to load research filters." onRetry={fetchFilterOptions} />
        ) : (
          <div className="research-filter-grid">
            <label className="research-filter-field">
              Department
              {isHod ? (
                <div
                  style={{
                    padding: "0.55rem 0.75rem",
                    borderRadius: "0.375rem",
                    border: "1px solid #cbd5e1",
                    backgroundColor: "#f8fafc",
                    fontWeight: 700,
                    color: "#0f172a",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                >
                  <Lock size={14} className="text-amber-600" />
                  {userDept} (Assigned Department)
                </div>
              ) : (
                <select
                  value={filters.department}
                  onChange={(event) => setFilters((current) => ({ ...current, department: event.target.value }))}
                >
                  <option value="">All departments</option>
                  {filterOptions.departments.map((dep) => (
                    <option key={dep} value={dep}>
                      {dep}
                    </option>
                  ))}
                </select>
              )}
            </label>

            <label className="research-filter-field">
              Program
              <select
                value={filters.program}
                onChange={(event) => setFilters((current) => ({ ...current, program: event.target.value }))}
              >
                <option value="">All programs</option>
                {filterOptions.programs.map((prog) => (
                  <option key={prog} value={prog}>
                    {prog}
                  </option>
                ))}
              </select>
            </label>

            <label className="research-filter-field">
              Admission year
              <select
                value={filters.admission_year}
                onChange={(event) => setFilters((current) => ({ ...current, admission_year: event.target.value }))}
              >
                <option value="">All admission years</option>
                {filterOptions.admission_years.map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </label>

            <div className="research-filter-actions">
              <button type="button" className="btn-secondary" onClick={resetFilters}>
                <RotateCcw size={15} /> Reset filters
              </button>
            </div>
          </div>
        )}
      </section>

      {loading ? (
        <LoadingSpinner message="Loading research analytics..." />
      ) : error ? (
        <ErrorAlert message="Unable to load research data." onRetry={fetchAnalytics} />
      ) : isEmpty ? (
        <div className="card research-empty" role="status">No research data available for the selected filters.</div>
      ) : (
        <>
          <section className="research-kpis" aria-label="Research key performance indicators">
            <KpiCard label="TOTAL STUDENTS" value={numberFormat.format(analytics.overview.total_students)} icon={GraduationCap} />
            <KpiCard label="RESEARCH PARTICIPANTS" value={numberFormat.format(analytics.overview.research_participants)} icon={Users} />
            <KpiCard label="PARTICIPATION RATE" value={`${decimalFormat.format(analytics.overview.research_participation_rate)}%`} icon={Activity} />
            <KpiCard label="TOTAL PUBLICATIONS" value={numberFormat.format(analytics.overview.total_publications)} icon={BookOpen} />
            <KpiCard label="AVERAGE PUBLICATIONS" value={decimalFormat.format(analytics.overview.average_publications)} icon={BookOpen} />
            <KpiCard label="AVG FACULTY RATING" value={analytics.overview.average_faculty_rating == null ? "—" : decimalFormat.format(analytics.overview.average_faculty_rating)} icon={Users} />
            <KpiCard label="AVG MENTORSHIP SCORE" value={analytics.overview.average_mentorship_score == null ? "—" : decimalFormat.format(analytics.overview.average_mentorship_score)} icon={Users} />
            <KpiCard label="AVG INFRASTRUCTURE RATING" value={analytics.overview.average_infrastructure_rating == null ? "—" : decimalFormat.format(analytics.overview.average_infrastructure_rating)} icon={Building2} />
          </section>

          <section className="research-chart-grid" aria-label="Research analytics charts">
            <article className="card research-chart-card">
              <h2 className="card-title" style={{ marginBottom: "0.75rem" }}>Research participation</h2>
              <p className="department-performance-note">
                Counts of student records grouped by reported participation status; these are counts, not percentages of the student population.
              </p>
              {participationData.length ? (
                <div className="research-chart">
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie data={participationData} dataKey="count" nameKey="category" cx="50%" cy="50%" innerRadius={58} outerRadius={94} paddingAngle={3}>
                        {participationData.map((entry, index) => <Cell key={`${entry.category}-${index}`} fill={entry.color} />)}
                      </Pie>
                      <Tooltip formatter={(value) => [numberFormat.format(value), "Student records"]} contentStyle={{ borderRadius: "0.5rem", border: "1px solid #cbd5e1" }} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              ) : <EmptyChart />}
            </article>

            <article className="card research-chart-card">
              <h2 className="card-title" style={{ marginBottom: "0.75rem" }}>Publication distribution</h2>
              <p className="department-performance-note">
                Student-record counts by publication-count range. The average publication KPI excludes records without a reported publication value.
              </p>
              {analytics.publications.length ? (
                <div className="research-chart">
                  <ResponsiveContainer>
                    <BarChart data={analytics.publications} margin={{ top: 8, right: 10, left: -16, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="bucket" stroke="#64748b" tick={{ fontSize: 11 }} label={{ value: "Publications per student record", position: "insideBottom", offset: -3 }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 12 }} allowDecimals={false} label={{ value: "Student records", angle: -90, position: "insideLeft" }} />
                      <Tooltip formatter={(value) => [numberFormat.format(value), "Student records"]} contentStyle={{ borderRadius: "0.5rem", border: "1px solid #cbd5e1" }} />
                      <Bar dataKey="count" name="Student records" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : <EmptyChart />}
            </article>
          </section>

        </>
      )}
    </div>
  );
}

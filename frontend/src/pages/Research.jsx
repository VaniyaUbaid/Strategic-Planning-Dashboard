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
  CircleHelp,
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
import FacultyResearchAnalytics from "../components/research/FacultyResearchAnalytics";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import "./Research.css";

const PARTICIPATION_COLORS = ["#2563eb", "#94a3b8", "#f59e0b", "#8b5cf6"];
const numberFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const decimalFormat = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function EmptyChart({ message = "No research data available for the selected filters." }) {
  return <div className="research-empty">{message}</div>;
}

function KpiCard({ label, value, icon: Icon, definition = "" }) {
  return (
    <div className="card research-kpi">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.75rem" }}>
        <div style={{ minWidth: 0 }}>
          <div className="research-kpi-label-row">
            <span className="research-kpi-label">{label}</span>
            <span className="research-info" title={definition} aria-label={`${label} definition`}>
              <CircleHelp size={15} />
            </span>
          </div>
          <div className="research-kpi-value">{value}</div>
        </div>
        <span className="research-kpi-icon"><Icon size={21} /></span>
      </div>
    </div>
  );
}

const studentMetricDefinitions = {
  "TOTAL STUDENTS": "Count of student records in the selected department, program, and admission-year scope.",
  "RESEARCH PARTICIPANTS": "Count of student records with a normalized research participation status of Participating.",
  "STUDENT PARTICIPATION RATE": "Participating student records divided by all student records in scope, multiplied by 100. Unknown participation statuses remain in the denominator.",
  "STUDENT PUBLICATIONS": "Sum of non-missing Publications values across student records in the selected scope.",
  "AVG PUBLICATIONS / STUDENT RECORD": "Mean of non-missing Publications values across student records. The denominator is records with reported publication values, not distinct students.",
  "AVG STUDENT FACULTY RATING": "Mean of valid Faculty_Rating values attached to student research records; missing ratings are excluded. This is not a faculty performance rating.",
  "AVG STUDENT MENTORSHIP SCORE": "Mean of valid Mentorship_Score values attached to student research records; missing values are excluded.",
  "AVG INFRASTRUCTURE RATING": "Mean of valid Infrastructure_Rating values attached to student research records; missing values are excluded.",
};

export default function Research() {
  const { role, department } = useAuth();
  const isHod = role === "HOD";
  const userDept = isHod ? (department || "CSE") : "";

  const [filterOptions, setFilterOptions] = useState({ departments: [], programs: [], admission_years: [] });
  const [filters, setFilters] = useState({
    department: userDept,
    program: "",
    admission_year: "",
    academic_year: "",
  });

  const [analytics, setAnalytics] = useState(null);
  const [facultyAnalytics, setFacultyAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [facultyLoading, setFacultyLoading] = useState(true);
  const [optionsError, setOptionsError] = useState(false);
  const [error, setError] = useState(false);
  const [facultyError, setFacultyError] = useState("");

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
      api.getResearchDepartments(params),
    ])
      .then(([overview, publications, participation, departments]) => {
        setAnalytics({
          overview,
          publications: publications.distribution,
          participation: participation.distribution,
          departments: departments.departments,
        });
      })
      .catch(() => {
        setAnalytics(null);
        setError(true);
      })
      .finally(() => setLoading(false));
  }, [
    filters.admission_year,
    filters.department,
    filters.program,
    isHod,
    userDept,
  ]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const fetchFacultyAnalytics = useCallback(() => {
    setFacultyLoading(true);
    setFacultyError("");
    api.getFacultyResearchAnalytics({
      department: isHod ? userDept : filters.department,
      academic_year: filters.academic_year,
    })
      .then(setFacultyAnalytics)
      .catch((err) => {
        setFacultyAnalytics(null);
        setFacultyError(
          err.message || "Unable to load faculty research analytics. Check your Supabase session and access permissions."
        );
      })
      .finally(() => setFacultyLoading(false));
  }, [filters.academic_year, filters.department, isHod, userDept]);

  useEffect(() => {
    fetchFacultyAnalytics();
  }, [fetchFacultyAnalytics]);

  const resetFilters = () =>
    setFilters({
      department: isHod ? userDept : "",
      program: "",
      admission_year: "",
      academic_year: "",
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
            <h1>Faculty-Centric Research Dashboard</h1>
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
              Student admission year
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

            <label className="research-filter-field">
              Faculty academic year
              <select
                value={filters.academic_year}
                onChange={(event) => setFilters((current) => ({ ...current, academic_year: event.target.value }))}
              >
                <option value="">All reporting years</option>
                {(facultyAnalytics?.academic_years || []).map((year) => (
                  <option key={year} value={year}>{year}</option>
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

      {facultyLoading ? (
        <LoadingSpinner message="Loading faculty research analytics..." />
      ) : facultyError ? (
        <ErrorAlert
          message={facultyError}
          onRetry={fetchFacultyAnalytics}
        />
      ) : (
        <FacultyResearchAnalytics data={facultyAnalytics} />
      )}

      <section className="student-research-section" aria-label="Student research participation">
        <header className="student-research-heading">
          <div>
            <h2>Student Research Participation</h2>
            <p>Student-level participation and publication indicators remain separate from faculty output.</p>
          </div>
        </header>
        {loading ? (
          <LoadingSpinner message="Loading student research analytics..." />
        ) : error ? (
          <ErrorAlert message="Unable to load student research data." onRetry={fetchAnalytics} />
        ) : isEmpty ? (
          <div className="card research-empty" role="status">No student research data available for the selected filters.</div>
        ) : (
          <>
            <div className="research-kpis" aria-label="Student research key performance indicators">
              <KpiCard label="TOTAL STUDENTS" value={numberFormat.format(analytics.overview.total_students)} icon={GraduationCap} definition={studentMetricDefinitions["TOTAL STUDENTS"]} />
              <KpiCard label="RESEARCH PARTICIPANTS" value={numberFormat.format(analytics.overview.research_participants)} icon={Users} definition={studentMetricDefinitions["RESEARCH PARTICIPANTS"]} />
              <KpiCard label="STUDENT PARTICIPATION RATE" value={`${decimalFormat.format(analytics.overview.research_participation_rate)}%`} icon={Activity} definition={studentMetricDefinitions["STUDENT PARTICIPATION RATE"]} />
              <KpiCard label="STUDENT PUBLICATIONS" value={numberFormat.format(analytics.overview.total_publications)} icon={BookOpen} definition={studentMetricDefinitions["STUDENT PUBLICATIONS"]} />
              <KpiCard label="AVG PUBLICATIONS / STUDENT RECORD" value={decimalFormat.format(analytics.overview.average_publications)} icon={BookOpen} definition={studentMetricDefinitions["AVG PUBLICATIONS / STUDENT RECORD"]} />
              <KpiCard label="AVG STUDENT FACULTY RATING" value={analytics.overview.average_faculty_rating == null ? "—" : decimalFormat.format(analytics.overview.average_faculty_rating)} icon={Users} definition={studentMetricDefinitions["AVG STUDENT FACULTY RATING"]} />
              <KpiCard label="AVG STUDENT MENTORSHIP SCORE" value={analytics.overview.average_mentorship_score == null ? "—" : decimalFormat.format(analytics.overview.average_mentorship_score)} icon={Users} definition={studentMetricDefinitions["AVG STUDENT MENTORSHIP SCORE"]} />
              <KpiCard label="AVG INFRASTRUCTURE RATING" value={analytics.overview.average_infrastructure_rating == null ? "—" : decimalFormat.format(analytics.overview.average_infrastructure_rating)} icon={Building2} definition={studentMetricDefinitions["AVG INFRASTRUCTURE RATING"]} />
            </div>

            <section className="research-chart-grid" aria-label="Student research analytics charts">
            <article className="card research-chart-card">
              <h2 className="card-title" style={{ marginBottom: "0.75rem" }}>Research participation</h2>
              <p className="department-performance-note">
                Counts of student records grouped by reported participation status; these are counts, not percentages of the student population.
              </p>
              {participationData.length ? (
                <div className="research-chart">
                  <ResponsiveContainer>
                    <PieChart margin={{ top: 8, right: 12, bottom: 8, left: 12 }}>
                      <Pie data={participationData} dataKey="count" nameKey="category" cx="50%" cy="43%" innerRadius={54} outerRadius={86} paddingAngle={3}>
                        {participationData.map((entry, index) => <Cell key={`${entry.category}-${index}`} fill={entry.color} />)}
                      </Pie>
                      <Tooltip formatter={(value) => [numberFormat.format(value), "Student records"]} contentStyle={{ borderRadius: "0.5rem", border: "1px solid #cbd5e1" }} />
                      <Legend verticalAlign="bottom" height={48} />
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
                    <BarChart data={analytics.publications} margin={{ top: 30, right: 16, left: 18, bottom: 42 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="bucket" stroke="#64748b" tick={{ fontSize: 11 }} interval={0} label={{ value: "Publications per student record", position: "insideBottom", offset: -30 }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 12 }} allowDecimals={false} width={58} label={{ value: "Student records", angle: -90, position: "insideLeft", offset: 8 }} />
                      <Tooltip formatter={(value) => [numberFormat.format(value), "Student records"]} contentStyle={{ borderRadius: "0.5rem", border: "1px solid #cbd5e1" }} />
                      <Legend verticalAlign="top" height={24} />
                      <Bar dataKey="count" name="Student records" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : <EmptyChart />}
            </article>

            <article className="card research-chart-card">
              <h2 className="card-title" style={{ marginBottom: "0.75rem" }}>Student research participation by department</h2>
              <p className="department-performance-note">
                Participating student records divided by all student records in each department. Unknown participation statuses remain in the denominator.
              </p>
              {analytics.departments.length ? (
                <div className="research-chart">
                  <ResponsiveContainer>
                    <BarChart data={analytics.departments} margin={{ top: 30, right: 16, left: 18, bottom: 42 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="department" stroke="#64748b" tick={{ fontSize: 11 }} interval={0} label={{ value: "Department", position: "insideBottom", offset: -30 }} />
                      <YAxis domain={[0, 100]} tickFormatter={(value) => `${value}%`} stroke="#64748b" width={58} label={{ value: "Participating students (%)", angle: -90, position: "insideLeft", offset: 8 }} />
                      <Tooltip
                        formatter={(value, _name, item) => [
                          `${decimalFormat.format(value)}% (${numberFormat.format(item.payload.research_participants)}/${numberFormat.format(item.payload.total_students)} records)`,
                          "Participation rate",
                        ]}
                        contentStyle={{ borderRadius: "0.5rem", border: "1px solid #cbd5e1" }}
                      />
                      <Legend verticalAlign="top" height={24} />
                      <Bar dataKey="participation_rate" name="Student participation rate" fill="#0d9488" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : <EmptyChart />}
            </article>
          </section>
          </>
        )}
      </section>
    </div>
  );
}

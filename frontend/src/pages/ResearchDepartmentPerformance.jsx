import React, { useEffect, useMemo, useState } from "react";
import { Activity, Banknote, BookOpen, CircleHelp, Users } from "lucide-react";
import { Navigate } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import ErrorAlert from "../components/common/ErrorAlert";
import DepartmentPerformanceHeader from "../components/common/DepartmentPerformanceHeader";
import LoadingSpinner from "../components/common/LoadingSpinner";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import "../components/common/DepartmentPerformance.css";
import "./Research.css";

const numberFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const decimalFormat = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const currencyFormat = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});
const chartColors = ["#2563eb", "#0d9488", "#f59e0b", "#8b5cf6", "#ef4444", "#64748b"];
const tooltipStyle = { borderRadius: "0.5rem", border: "1px solid #cbd5e1" };

function PerformanceKpi({ label, value, icon: Icon, definition }) {
  return (
    <article className="card research-kpi">
      <div className="research-kpi-content">
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
    </article>
  );
}

function ChartCard({ title, description, children }) {
  return (
    <article className="card research-chart-card">
      <h2 className="card-title">{title}</h2>
      <p className="department-performance-note">{description}</p>
      {children}
    </article>
  );
}

export default function ResearchDepartmentPerformance() {
  const { role, department } = useAuth();
  const isHod = role === "HOD";
  const assignedDepartment = isHod ? (department || "") : "";
  const [filters, setFilters] = useState({ department: assignedDepartment, academic_year: "" });
  const [retryCount, setRetryCount] = useState(0);
  const queryParams = useMemo(() => ({
      department: isHod ? assignedDepartment : filters.department,
      academic_year: filters.academic_year,
    }), [assignedDepartment, filters.academic_year, filters.department, isHod]);
  const requestKey = JSON.stringify(queryParams);
  const [result, setResult] = useState({ key: "", data: null, error: "" });

  useEffect(() => {
    let cancelled = false;
    api.getFacultyResearchAnalytics(queryParams)
      .then((data) => {
        if (!cancelled) setResult({ key: requestKey, data, error: "" });
      })
      .catch((err) => {
        if (!cancelled) {
          setResult({
            key: requestKey,
            data: null,
            error: err.message || "Unable to load faculty department performance.",
          });
        }
      });
    return () => { cancelled = true; };
  }, [queryParams, requestKey, retryCount]);

  const loading = result.key !== requestKey;
  const analytics = loading ? null : result.data;
  const error = loading ? "" : result.error;
  const departments = analytics?.departments || [];
  const trendData = useMemo(() => {
    const trendRows = analytics?.department_publication_trends || [];
    const years = [...new Set(trendRows.map((item) => item.academic_year))].sort();
    return years.map((academicYear) => {
      const row = { academic_year: academicYear };
      trendRows
        .filter((item) => item.academic_year === academicYear)
        .forEach((item) => { row[item.department] = item.publications; });
      return row;
    });
  }, [analytics]);

  if (role !== "ADMINISTRATOR" && !isHod) return <Navigate to="/research" replace />;

  const handleFilterChange = (key, value) => {
    setFilters((current) => ({ ...current, [key]: value }));
  };
  const resetFilters = () => setFilters({ department: assignedDepartment, academic_year: "" });
  const retry = () => setRetryCount((count) => count + 1);

  return (
    <div className="department-performance-page">
      <DepartmentPerformanceHeader
        title="Faculty Research Department Performance"
        description="Compare faculty research participation, publication output, citations, and grants across departments."
        backTo="/research"
        backLabel="Back to Research Dashboard"
      />

      <section className="card research-filter-card" aria-label="Faculty research department filters">
        <div className="research-filter-title"><Activity size={18} color="#2563eb" /> Faculty research filters</div>
        <div className="research-filter-grid">
          <label className="research-filter-field">
            Department
            {isHod ? (
              <div className="department-scope-lock">{assignedDepartment || "Assigned department unavailable"}</div>
            ) : (
              <select value={filters.department} onChange={(event) => handleFilterChange("department", event.target.value)}>
                <option value="">All departments</option>
                {(analytics?.available_departments || []).map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            )}
          </label>
          <label className="research-filter-field">
            Faculty academic year
            <select value={filters.academic_year} onChange={(event) => handleFilterChange("academic_year", event.target.value)}>
              <option value="">All reporting years</option>
              {(analytics?.academic_years || []).map((year) => <option key={year} value={year}>{year}</option>)}
            </select>
          </label>
          <div className="research-filter-actions">
            <button type="button" className="btn-secondary" onClick={resetFilters}>Reset filters</button>
          </div>
        </div>
      </section>

      {loading ? (
        <LoadingSpinner message="Loading faculty research department performance..." />
      ) : error ? (
        <ErrorAlert message={error} onRetry={retry} />
      ) : analytics?.overview.total_faculty === 0 ? (
        <div className="card research-empty" role="status">No active faculty records are available for the selected filters.</div>
      ) : (
        <>
          <section className="department-performance-kpis" aria-label="Faculty research department indicators">
            <PerformanceKpi
              label="TOTAL ACTIVE FACULTY"
              value={numberFormat.format(analytics.overview.total_faculty)}
              icon={Users}
              definition="Count of distinct active faculty members in the selected department and reporting period. Faculty with no annual research row remain included."
            />
            <PerformanceKpi
              label="FACULTY RESEARCHERS"
              value={numberFormat.format(analytics.overview.faculty_researchers)}
              icon={Activity}
              definition="Distinct active faculty with at least one publication in the selected academic year or all reporting years."
            />
            <PerformanceKpi
              label="FACULTY PUBLICATIONS"
              value={numberFormat.format(analytics.overview.total_publications)}
              icon={BookOpen}
              definition="Sum of publication counts in annual faculty research records for the selected scope and reporting period."
            />
            <PerformanceKpi
              label="AVG PUBLICATIONS / FACULTY"
              value={decimalFormat.format(analytics.overview.average_publications_per_faculty)}
              icon={BookOpen}
              definition="Total publications divided by distinct active faculty in scope. Faculty with zero publications or no annual research row are included in the denominator."
            />
            <PerformanceKpi
              label="FACULTY PARTICIPATION"
              value={`${decimalFormat.format(analytics.overview.faculty_participation_rate)}%`}
              icon={Activity}
              definition="Distinct active faculty with at least one publication divided by all distinct active faculty in scope, multiplied by 100."
            />
            <PerformanceKpi
              label="RESEARCH GRANTS"
              value={currencyFormat.format(analytics.overview.total_research_grants)}
              icon={Banknote}
              definition="Sum of grant amounts recorded in faculty research records for the selected period. Values are synthetic only when identified as such in the dataset."
            />
          </section>

          {analytics.is_synthetic && (
            <p className="department-performance-note">
              This dataset is marked synthetic; grant and publication figures are illustrative, not actual institutional records.
            </p>
          )}

          <section className="research-chart-grid" aria-label="Faculty department comparisons">
            <ChartCard title="Faculty Publications by Department" description="Annual faculty publication counts for the selected academic year or all available years.">
              <div className="research-chart">
                <ResponsiveContainer>
                  <BarChart data={departments} margin={{ top: 8, right: 12, left: 0, bottom: 24 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="department" label={{ value: "Department", position: "insideBottom", offset: -14 }} />
                    <YAxis allowDecimals={false} label={{ value: "Publications", angle: -90, position: "insideLeft" }} />
                    <Tooltip formatter={(value) => [numberFormat.format(value), "Faculty publications"]} contentStyle={tooltipStyle} />
                    <Legend />
                    <Bar dataKey="publications" name="Faculty publications" fill="#2563eb" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>

            <ChartCard title="Faculty Participation Rate by Department" description="Publishing faculty as a share of all active faculty in each department.">
              <div className="research-chart">
                <ResponsiveContainer>
                  <BarChart data={departments} margin={{ top: 8, right: 12, left: 0, bottom: 24 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="department" label={{ value: "Department", position: "insideBottom", offset: -14 }} />
                    <YAxis domain={[0, 100]} tickFormatter={(value) => `${value}%`} label={{ value: "Participation (%)", angle: -90, position: "insideLeft" }} />
                    <Tooltip
                      formatter={(value, _name, item) => [
                        `${decimalFormat.format(value)}% (${item.payload.faculty_researchers}/${item.payload.total_faculty})`,
                        "Faculty participation",
                      ]}
                      contentStyle={tooltipStyle}
                    />
                    <Legend />
                    <Bar dataKey="participation_rate" name="Faculty participation" fill="#0d9488" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>

            <ChartCard title="Average Publications per Faculty" description="Department publication totals divided by the distinct active faculty count, including zero-output faculty.">
              <div className="research-chart">
                <ResponsiveContainer>
                  <BarChart data={departments} margin={{ top: 8, right: 12, left: 0, bottom: 24 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="department" label={{ value: "Department", position: "insideBottom", offset: -14 }} />
                    <YAxis label={{ value: "Publications per faculty", angle: -90, position: "insideLeft" }} />
                    <Tooltip formatter={(value) => [decimalFormat.format(value), "Publications per faculty"]} contentStyle={tooltipStyle} />
                    <Legend />
                    <Bar dataKey="average_publications_per_faculty" name="Average publications per faculty" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>

            <ChartCard title="Faculty Publication Trends by Department" description="Annual publication totals grouped by department. The selected academic-year filter narrows the chart to that year.">
              {trendData.length ? (
                <div className="research-chart">
                  <ResponsiveContainer>
                    <LineChart data={trendData} margin={{ top: 8, right: 12, left: 0, bottom: 8 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="academic_year" label={{ value: "Academic year", position: "insideBottom", offset: -3 }} />
                      <YAxis allowDecimals={false} label={{ value: "Publications", angle: -90, position: "insideLeft" }} />
                      <Tooltip formatter={(value) => [numberFormat.format(value), "Faculty publications"]} contentStyle={tooltipStyle} />
                      <Legend />
                      {(analytics.available_departments || []).map((item, index) => (
                        <Line key={item} type="monotone" dataKey={item} name={item} stroke={chartColors[index % chartColors.length]} strokeWidth={2} />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="research-empty" role="status">No faculty publication trends are available for this reporting period.</div>
              )}
            </ChartCard>
          </section>

          <section className="card research-table-card" aria-label="Faculty research department comparison table">
            <div className="card-header">
              <h2 className="card-title">Department Comparison</h2>
              {analytics.is_synthetic && <span className="synthetic-data-badge">Synthetic sample data</span>}
            </div>
            {departments.length ? (
              <div className="table-container">
                <table className="data-table faculty-research-table">
                  <thead>
                    <tr>
                      <th>Department</th>
                      <th>Faculty</th>
                      <th>Faculty Researchers</th>
                      <th>Participation Rate</th>
                      <th>Publications</th>
                      <th>Avg Publications / Faculty</th>
                      <th>Citations</th>
                      <th>Research Grants</th>
                    </tr>
                  </thead>
                  <tbody>
                    {departments.map((item) => (
                      <tr key={item.department}>
                        <td>{item.department}</td>
                        <td>{numberFormat.format(item.total_faculty)}</td>
                        <td>{numberFormat.format(item.faculty_researchers)}</td>
                        <td>{decimalFormat.format(item.participation_rate)}%</td>
                        <td>{numberFormat.format(item.publications)}</td>
                        <td>{decimalFormat.format(item.average_publications_per_faculty)}</td>
                        <td>{numberFormat.format(item.total_citations)}</td>
                        <td>{currencyFormat.format(item.research_grants)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="research-empty" role="status">No department comparisons are available for the selected filters.</div>
            )}
          </section>
        </>
      )}
    </div>
  );
}

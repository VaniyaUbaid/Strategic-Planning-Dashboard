import React, { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Award,
  BookOpen,
  Building2,
  DollarSign,
  ArrowRight,
  Filter,
  Lock,
  PieChart as PieChartIcon,
  RotateCcw,
  ShieldAlert,
  Wallet,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Link } from "react-router-dom";

import ErrorAlert from "../components/common/ErrorAlert";
import LoadingSpinner from "../components/common/LoadingSpinner";
import RiskBadge from "../components/common/RiskBadge";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import { formatINR, formatINRPrecise } from "../utils/currency";
import "./Finance.css";

const CHART_COLORS = ["#2563eb", "#0d9488", "#d97706", "#8b5cf6", "#ec4899", "#6366f1"];

function KpiCard({ label, value, subtext, icon: Icon, valueColor }) {
  return (
    <div className="card finance-kpi">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.75rem" }}>
        <div style={{ minWidth: 0 }}>
          <span className="finance-kpi-label">{label}</span>
          <div className="finance-kpi-value" style={{ color: valueColor || "#0f172a" }}>
            {value}
          </div>
          {subtext && <div className="finance-kpi-sub">{subtext}</div>}
        </div>
        <span className="finance-kpi-icon">
          <Icon size={22} />
        </span>
      </div>
    </div>
  );
}

export default function Finance() {
  const { role, department } = useAuth();
  const isHod = role === "HOD";
  const userDept = isHod ? (department || "CSE") : "";

  const [filterOptions, setFilterOptions] = useState({ departments: [], academic_years: [], semesters: [] });
  const [filters, setFilters] = useState({
    department_id: userDept,
    academic_year: "",
    semester: "",
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterError, setFilterError] = useState(false);

  const [overview, setOverview] = useState(null);
  const [scholarships, setScholarships] = useState(null);
  const [risk, setRisk] = useState(null);

  // Keep department filter synced if user role or department changes
  useEffect(() => {
    if (isHod) {
      setFilters((prev) => ({ ...prev, department_id: userDept }));
    }
  }, [isHod, userDept]);

  const fetchFilters = useCallback(() => {
    setFilterError(false);
    api
      .getFinanceFilters()
      .then((res) => setFilterOptions(res))
      .catch(() => setFilterError(true));
  }, []);

  useEffect(() => {
    fetchFilters();
  }, [fetchFilters]);

  const fetchDashboardData = useCallback(() => {
    setLoading(true);
    setError(null);

    const activeDept = isHod ? userDept : filters.department_id;

    const params = {
      department_id: activeDept,
      academic_year: filters.academic_year,
      semester: filters.semester,
    };

    Promise.all([
      api.getFinanceOverview(params),
      api.getFinanceScholarships(params),
      api.getFinanceRisk(params),
    ])
      .then(([ovRes, schRes, riskRes]) => {
        setOverview(ovRes);
        setScholarships(schRes);
        setRisk(riskRes);
      })
      .catch((err) => {
        setError(err.message || "Failed to load financial intelligence analytics.");
      })
      .finally(() => setLoading(false));
  }, [filters, isHod, userDept]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const resetFilters = () =>
    setFilters({
      department_id: isHod ? userDept : "",
      academic_year: "",
      semester: "",
    });

  const scholarshipTypeData = (scholarships?.by_type || []).map((st, i) => ({
    ...st,
    color: CHART_COLORS[i % CHART_COLORS.length],
  }));

  return (
    <div className="finance-page">
      {/* Header */}
      <header className="finance-heading">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <div style={{ padding: "0.6rem", borderRadius: "0.5rem", backgroundColor: "#eff6ff", color: "#2563eb" }}>
            <DollarSign size={28} />
          </div>
          <div>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#0f172a" }}>
              Financial Intelligence Dashboard
            </h1>
            <p style={{ color: "#475569", fontSize: "0.95rem" }}>
              {isHod
                ? `Department Financial Analytics for ${userDept}`
                  : "Institutional financial KPIs, fee collection, scholarship disbursal, and rule-based financial risk."}
            </p>
          </div>
          </div>
          {(role === "ADMINISTRATOR" || isHod) && (
            <Link to="/finance/department-performance" className="btn-primary">
              View Department Performance <ArrowRight size={17} />
            </Link>
          )}
        </div>
      </header>

      {/* Filter Bar */}
      <section className="card finance-filter-card" aria-label="Finance filters">
        <div className="finance-filter-title">
          <Filter size={18} color="#2563eb" />
          Financial Data Filters
        </div>
        {filterError ? (
          <ErrorAlert message="Unable to load financial filters." onRetry={fetchFilters} />
        ) : (
          <div className="finance-filter-grid">
            <label className="finance-filter-field">
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
                  value={filters.department_id}
                  onChange={(e) => setFilters((prev) => ({ ...prev, department_id: e.target.value }))}
                >
                  <option value="">All Departments</option>
                  {filterOptions.departments.map((dept) => (
                    <option key={dept} value={dept}>
                      {dept}
                    </option>
                  ))}
                </select>
              )}
            </label>

            <label className="finance-filter-field">
              Academic Year
              <select
                value={filters.academic_year}
                onChange={(e) => setFilters((prev) => ({ ...prev, academic_year: e.target.value }))}
              >
                <option value="">All Academic Years</option>
                {filterOptions.academic_years.map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </label>

            <label className="finance-filter-field">
              Semester (Fee Analysis)
              <select
                value={filters.semester}
                onChange={(e) => setFilters((prev) => ({ ...prev, semester: e.target.value }))}
              >
                <option value="">All Semesters</option>
                {filterOptions.semesters.map((sem) => (
                  <option key={sem} value={sem}>
                    Semester {sem}
                  </option>
                ))}
              </select>
            </label>

            <div className="finance-filter-actions">
              <button type="button" className="btn-secondary" onClick={resetFilters}>
                <RotateCcw size={15} /> Reset Filters
              </button>
            </div>
          </div>
        )}
      </section>

      {loading ? (
        <LoadingSpinner message="Loading financial intelligence analytics..." />
      ) : error ? (
        <ErrorAlert message={error} onRetry={fetchDashboardData} />
      ) : !overview ? (
        <div className="card finance-empty">No financial data available for the selected filters.</div>
      ) : (
        <>
          {/* KPI Cards */}
          <section className="finance-kpis" aria-label="Financial Key Performance Indicators">
            <KpiCard
              label="TOTAL REVENUE"
              value={formatINR(overview.total_revenue)}
              subtext="Aggregated revenue"
              icon={ArrowUpRight}
              valueColor="#059669"
            />
            <KpiCard
              label="TOTAL EXPENSES"
              value={formatINR(overview.total_expenses)}
              subtext="Operational expenditure"
              icon={ArrowDownRight}
              valueColor="#dc2626"
            />
            <KpiCard
              label="NET SURPLUS / DEFICIT"
              value={formatINR(overview.net_surplus_deficit)}
              subtext={overview.net_surplus_deficit >= 0 ? "Operating Surplus" : "Operating Deficit"}
              icon={Wallet}
              valueColor={overview.net_surplus_deficit >= 0 ? "#059669" : "#dc2626"}
            />
            <KpiCard
              label="TOTAL BUDGET"
              value={formatINR(overview.total_budget)}
              subtext={`Actual: ${formatINR(overview.actual_expenditure)}`}
              icon={Building2}
            />
            <KpiCard
              label="BUDGET UTILIZATION"
              value={`${overview.budget_utilization}%`}
              subtext={`Variance: ${formatINR(overview.budget_variance)}`}
              icon={PieChartIcon}
              valueColor={overview.budget_utilization > 100 ? "#b45309" : "#2563eb"}
            />
            <KpiCard
              label="FEES COLLECTED"
              value={formatINR(overview.total_fees_collected)}
              subtext={`Collection Rate: ${overview.fee_collection_rate}%`}
              icon={BookOpen}
              valueColor="#059669"
            />
            <KpiCard
              label="OUTSTANDING FEES"
              value={formatINR(overview.outstanding_fees)}
              subtext="Pending student fee dues"
              icon={AlertTriangle}
              valueColor="#dc2626"
            />
            <KpiCard
              label="SCHOLARSHIPS DISBURSED"
              value={formatINR(overview.scholarships_disbursed)}
              subtext={`Awarded: ${formatINR(overview.total_scholarship_amount)}`}
              icon={Award}
              valueColor="#8b5cf6"
            />
          </section>

          {/* Rule-Based Financial Risk Section */}
          {risk && (
            <section className={`card finance-risk-card ${risk.risk_level}`} aria-label="Financial Risk Assessment">
              <div className="finance-risk-header">
                <div className="finance-risk-title">
                  <ShieldAlert size={26} color={risk.risk_level === "HIGH" ? "#be123c" : risk.risk_level === "MEDIUM" ? "#d97706" : "#059669"} />
                  <div>
                    <h2>Rule-Based Financial Risk Assessment</h2>
                    <span style={{ fontSize: "0.85rem", color: "#475569" }}>
                      Department Scope: {isHod ? userDept : (risk.department_id || "Institution-Wide")} {risk.academic_year ? `(${risk.academic_year})` : ""}
                    </span>
                  </div>
                </div>

                <div className="finance-risk-badge-box">
                  <RiskBadge level={risk.risk_level} />
                  <div className="finance-risk-score">
                    Score: {risk.risk_score} <span style={{ fontSize: "0.9rem", color: "#64748b", fontWeight: 500 }}>/ 100</span>
                  </div>
                </div>
              </div>

              <div className="finance-risk-explanation">
                ℹ️ Risk is calculated using a transparent <strong>rule-based financial scoring system</strong> based on institutional financial indicators. <strong>This is NOT a machine-learning prediction.</strong>
              </div>

              <div className="finance-risk-factors">
                <h4>Contributing Risk Factors:</h4>
                <ul>
                  {risk.contributing_factors.map((factor, idx) => (
                    <li key={idx}>{factor}</li>
                  ))}
                </ul>
              </div>

              <div className="finance-risk-metrics-grid">
                <div className="finance-risk-metric-box">
                  <div className="finance-risk-metric-label">Budget Utilization</div>
                  <div className="finance-risk-metric-val">{risk.metrics?.budget_utilization}%</div>
                </div>
                <div className="finance-risk-metric-box">
                  <div className="finance-risk-metric-label">Revenue-Expense Ratio</div>
                  <div className="finance-risk-metric-val">{risk.metrics?.revenue_expense_ratio}</div>
                </div>
                <div className="finance-risk-metric-box">
                  <div className="finance-risk-metric-label">Fee Collection Rate</div>
                  <div className="finance-risk-metric-val">{risk.metrics?.fee_collection_rate}%</div>
                </div>
                <div className="finance-risk-metric-box">
                  <div className="finance-risk-metric-label">Outstanding Fee %</div>
                  <div className="finance-risk-metric-val">{risk.metrics?.outstanding_fee_percentage}%</div>
                </div>
              </div>
            </section>
          )}

          {/* Department comparisons are on the dedicated performance page. */}
          <section className="finance-chart-grid" aria-label="Institutional scholarship analytics">
            <article className="card finance-chart-card">
              <h3 className="card-title" style={{ marginBottom: "0.75rem" }}>
                Scholarship Disbursement by Type
              </h3>
              <p style={{ color: "#64748b", fontSize: "0.85rem", margin: "0 0 0.75rem" }}>Actual scholarship amounts disbursed for the selected department and academic filters, grouped by scholarship type.</p>
              {scholarshipTypeData.length ? (
                <div className="finance-chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={scholarshipTypeData} margin={{ top: 10, right: 10, left: -10, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="type" stroke="#64748b" tick={{ fontSize: 11 }} label={{ value: "Scholarship type", position: "insideBottom", offset: -3 }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 11 }} tickFormatter={(val) => formatINR(val, true)} label={{ value: "Amount disbursed (₹)", angle: -90, position: "insideLeft" }} />
                      <Tooltip formatter={(value) => [formatINRPrecise(value), "Amount disbursed"]} contentStyle={{ borderRadius: "0.5rem", border: "1px solid #cbd5e1" }} />
                      <Legend />
                      <Bar dataKey="amount_disbursed" name="Disbursed Amount" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="finance-empty">No scholarship data available.</div>
              )}
            </article>
          </section>
        </>
      )}
    </div>
  );
}

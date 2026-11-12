import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Cpu,
  GraduationCap,
  ShieldAlert,
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

import ErrorAlert from "../components/common/ErrorAlert";
import FilterBar from "../components/common/FilterBar";
import LoadingSpinner from "../components/common/LoadingSpinner";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";

const RISK_COLORS = {
  HIGH: "#be123c",
  MEDIUM: "#d97706",
  LOW: "#059669",
};

export default function Students() {
  const { role, department } = useAuth();
  const isHod = role === "HOD";
  const userDept = isHod ? (department || "CSE") : "";

  const [filters, setFilters] = useState({
    department: userDept,
    academicYear: "",
    semester: "",
    riskLevel: "",
    search: "",
  });

  const [overview, setOverview] = useState(null);
  const [modelInsights, setModelInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Sync department filter if role changes
  useEffect(() => {
    if (isHod) {
      setFilters((prev) => ({ ...prev, department: userDept }));
    }
  }, [isHod, userDept]);

  const fetchDashboardData = useCallback(() => {
    setLoading(true);
    setError(null);

    const activeDept = isHod ? userDept : filters.department;

    const apiParams = {
      department: activeDept,
      academic_year: filters.academicYear,
      semester: filters.semester,
      risk_level: filters.riskLevel,
      search: filters.search,
    };

    Promise.all([api.getOverview(apiParams), api.getStudentModelInsights()])
      .then(([overviewRes, insightsRes]) => {
        setOverview(overviewRes);
        setModelInsights(insightsRes);
      })
      .catch((err) => {
        setError(err.message || "Failed to load student success analytics.");
      })
      .finally(() => setLoading(false));
  }, [filters, isHod, userDept]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Chart Dataset 1: Overall Risk Pie Chart
  const pieDistributionData = overview?.risk_distribution
    ? [
        { name: "Low Risk (<0.40)", value: overview.risk_distribution.low_count || 0, color: RISK_COLORS.LOW },
        { name: "Medium Risk (0.40-0.59)", value: overview.risk_distribution.medium_count || 0, color: RISK_COLORS.MEDIUM },
        { name: "High Risk (>=0.60)", value: overview.risk_distribution.high_count || 0, color: RISK_COLORS.HIGH },
      ]
    : [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#0f172a", marginBottom: "0.25rem" }}>
            Student Success & Dropout Risk Analytics
          </h1>
          <p style={{ color: "#475569", fontSize: "0.95rem" }}>
            {isHod
              ? `Department Student Success Analytics for ${userDept}`
              : "ML-powered dropout risk intelligence, Logistic Regression feature insights, and student performance tracking."}
          </p>
        </div>
        {(role === "ADMINISTRATOR" || isHod) && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem" }}>
            <Link to="/students/directory" className="btn-primary">
              View Enrolled Students Directory <ArrowRight size={17} />
            </Link>
            <Link to="/students/department-performance" className="btn-secondary">
              View Department Performance <ArrowRight size={17} />
            </Link>
          </div>
        )}
      </div>

      {/* Dynamic Dependent Filter Bar */}
      <FilterBar
        filters={filters}
        onFilterChange={(newFilters) => {
          setFilters(newFilters);
        }}
        showRiskFilter={true}
        showSearch={true}
      />

      {loading ? (
        <LoadingSpinner message="Loading student analytics & risk predictions..." />
      ) : error ? (
        <ErrorAlert message={error} onRetry={fetchDashboardData} />
      ) : (
        <>
          {/* 1. Student Risk Overview KPI Cards */}
          <section
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: "1rem",
            }}
            aria-label="Student Risk KPIs"
          >
            <div className="card" style={{ padding: "1.1rem" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>
                    TOTAL STUDENTS
                  </span>
                  <h3 style={{ fontSize: "1.6rem", fontWeight: 700, color: "#0f172a", marginTop: "0.2rem" }}>
                    {overview?.total_students?.toLocaleString() || 0}
                  </h3>
                </div>
                <div style={{ padding: "0.6rem", backgroundColor: "#eff6ff", borderRadius: "0.5rem", color: "#2563eb" }}>
                  <GraduationCap size={24} />
                </div>
              </div>
            </div>

            <div className="card" style={{ padding: "1.1rem" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>
                    HIGH RISK (≥0.60)
                  </span>
                  <h3 style={{ fontSize: "1.6rem", fontWeight: 700, color: "#be123c", marginTop: "0.2rem" }}>
                    {overview?.high_risk_count?.toLocaleString() || 0}
                    <span style={{ fontSize: "0.85rem", color: "#9f1239", fontWeight: 600, marginLeft: "0.5rem" }}>
                      ({overview?.risk_distribution?.high_pct || 0}%)
                    </span>
                  </h3>
                </div>
                <div style={{ padding: "0.6rem", backgroundColor: "#fff1f2", borderRadius: "0.5rem", color: "#be123c" }}>
                  <AlertTriangle size={24} />
                </div>
              </div>
            </div>

            <div className="card" style={{ padding: "1.1rem" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>
                    MEDIUM RISK (0.40-0.59)
                  </span>
                  <h3 style={{ fontSize: "1.6rem", fontWeight: 700, color: "#d97706", marginTop: "0.2rem" }}>
                    {overview?.medium_risk_count?.toLocaleString() || 0}
                    <span style={{ fontSize: "0.85rem", color: "#b45309", fontWeight: 600, marginLeft: "0.5rem" }}>
                      ({overview?.risk_distribution?.medium_pct || 0}%)
                    </span>
                  </h3>
                </div>
                <div style={{ padding: "0.6rem", backgroundColor: "#fffbeb", borderRadius: "0.5rem", color: "#d97706" }}>
                  <ShieldAlert size={24} />
                </div>
              </div>
            </div>

            <div className="card" style={{ padding: "1.1rem" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>
                    LOW RISK (&lt;0.40)
                  </span>
                  <h3 style={{ fontSize: "1.6rem", fontWeight: 700, color: "#059669", marginTop: "0.2rem" }}>
                    {overview?.low_risk_count?.toLocaleString() || 0}
                    <span style={{ fontSize: "0.85rem", color: "#047857", fontWeight: 600, marginLeft: "0.5rem" }}>
                      ({overview?.risk_distribution?.low_pct || 0}%)
                    </span>
                  </h3>
                </div>
                <div style={{ padding: "0.6rem", backgroundColor: "#ecfdf5", borderRadius: "0.5rem", color: "#059669" }}>
                  <CheckCircle2 size={24} />
                </div>
              </div>
            </div>

            <div className="card" style={{ padding: "1.1rem" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>
                    AVG RISK PROBABILITY
                  </span>
                  <h3 style={{ fontSize: "1.6rem", fontWeight: 700, color: "#0f172a", marginTop: "0.2rem" }}>
                    {((overview?.average_dropout_probability || 0) * 100).toFixed(1)}%
                  </h3>
                </div>
                <div style={{ padding: "0.6rem", backgroundColor: "#f1f5f9", borderRadius: "0.5rem", color: "#475569" }}>
                  <Activity size={24} />
                </div>
              </div>
            </div>
          </section>

          <section className="card" style={{ padding: "1.25rem" }} aria-label="Institutional student risk distribution">
            <h3 className="card-title" style={{ marginBottom: "0.5rem" }}>Student Risk Distribution</h3>
            <p style={{ color: "#64748b", marginBottom: "0.75rem" }}>
              Counts of students by the configured model probability bands: low (&lt;40%), medium (40%-59%), and high (60%+).
            </p>
            {pieDistributionData.some((d) => d.value > 0) ? (
              <div style={{ width: "100%", height: "260px" }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={pieDistributionData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={4}>
                      {pieDistributionData.map((entry, index) => <Cell key={`pie-cell-${index}`} fill={entry.color} />)}
                    </Pie>
                    <Tooltip formatter={(value) => [value.toLocaleString(), "Students"]} contentStyle={{ borderRadius: "0.5rem", border: "1px solid #cbd5e1" }} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : <div style={{ padding: "2rem", textAlign: "center", color: "#64748b" }}>No distribution data.</div>}
          </section>

          {/* 3. Logistic Regression Model Feature Insights */}
          {modelInsights && (
            <section className="card" style={{ padding: "1.5rem" }} aria-label="Logistic Regression Feature Insights">
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }}>
                <div style={{ padding: "0.5rem", borderRadius: "0.5rem", backgroundColor: "#eff6ff", color: "#2563eb" }}>
                  <Cpu size={24} />
                </div>
                <div>
                  <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a" }}>
                    Logistic Regression Feature Coefficient Insights
                  </h2>
                  <p style={{ fontSize: "0.85rem", color: "#475569" }}>
                    Model-wide associations, not causal effects or a student's individual explanation. Positive coefficients increase predicted log-odds of dropout risk.
                  </p>
                </div>
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))",
                  gap: "1.5rem",
                  marginTop: "1.25rem",
                }}
              >
                {/* Risk Factors Bar Chart */}
                <div style={{ backgroundColor: "#fff1f2", padding: "1.25rem", borderRadius: "0.5rem", border: "1px solid #fecdd3" }}>
                  <h4 style={{ fontSize: "0.95rem", fontWeight: 700, color: "#be123c", marginBottom: "0.75rem" }}>
                    ⚠️ Factors Associated with HIGHER Predicted Risk
                  </h4>
                  <div style={{ width: "100%", height: "240px" }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={modelInsights.risk_factors} layout="vertical" margin={{ top: 5, right: 20, left: 30, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#fecdd3" />
                        <XAxis type="number" stroke="#9f1239" tick={{ fontSize: 11 }} label={{ value: "Log-odds coefficient", position: "insideBottom", offset: -3 }} />
                        <YAxis dataKey="feature_name" type="category" stroke="#9f1239" tick={{ fontSize: 11 }} width={140} />
                        <Tooltip formatter={(val) => [`+${val}`, "Log-Odds Coefficient"]} contentStyle={{ borderRadius: "0.5rem", border: "1px solid #fecdd3" }} />
                        <Bar dataKey="coefficient" fill="#be123c" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Protective Factors Bar Chart */}
                <div style={{ backgroundColor: "#ecfdf5", padding: "1.25rem", borderRadius: "0.5rem", border: "1px solid #a7f3d0" }}>
                  <h4 style={{ fontSize: "0.95rem", fontWeight: 700, color: "#047857", marginBottom: "0.75rem" }}>
                    🛡️ Factors Associated with LOWER Predicted Risk (Retention Drivers)
                  </h4>
                  <div style={{ width: "100%", height: "240px" }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={modelInsights.protective_factors} layout="vertical" margin={{ top: 5, right: 20, left: 30, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#a7f3d0" />
                        <XAxis type="number" stroke="#047857" tick={{ fontSize: 11 }} label={{ value: "Log-odds coefficient", position: "insideBottom", offset: -3 }} />
                        <YAxis dataKey="feature_name" type="category" stroke="#047857" tick={{ fontSize: 11 }} width={140} />
                        <Tooltip formatter={(val) => [val, "Log-Odds Coefficient"]} contentStyle={{ borderRadius: "0.5rem", border: "1px solid #a7f3d0" }} />
                        <Bar dataKey="coefficient" fill="#059669" radius={[4, 0, 0, 4]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </section>
          )}

        </>
      )}
    </div>
  );
}

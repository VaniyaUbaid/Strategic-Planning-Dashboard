import React, { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  ChevronRight,
} from "lucide-react";
import { api } from "../services/api";
import { useRole } from "../context/RoleContext";
import LoadingSpinner from "../components/common/LoadingSpinner";
import ErrorAlert from "../components/common/ErrorAlert";
import FilterBar from "../components/common/FilterBar";
import AdminCharts from "../components/admin/AdminCharts";
import HodDepartmentView from "../components/hod/HodDepartmentView";

export default function Overview() {
  const { activeRole, userDepartment, getRoleLabel } = useRole();

  const [filters, setFilters] = useState({
    department: activeRole === "ADMINISTRATOR" ? "" : userDepartment,
    academicYear: "",
    semester: "",
    riskLevel: "",
    search: "",
  });

  const [adminOverview, setAdminOverview] = useState(null);
  const [hodOverview, setHodOverview] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Sync department filter if role changes
  useEffect(() => {
    setFilters((prev) => ({
      ...prev,
      department: activeRole === "ADMINISTRATOR" ? "" : userDepartment,
    }));
  }, [activeRole, userDepartment]);

  const loadDashboardData = useCallback(() => {
    setLoading(true);
    setError(null);

    const apiParams = {
      department: activeRole === "ADMINISTRATOR" ? filters.department : userDepartment,
      academic_year: filters.academicYear,
      semester: filters.semester,
      risk_level: filters.riskLevel,
      search: filters.search,
    };

    if (activeRole === "ADMINISTRATOR") {
      api
        .getOverview(apiParams)
        .then((data) => {
          setAdminOverview(data);
          setLoading(false);
        })
        .catch((err) => {
          setError(err.message || "Failed to load institutional overview.");
          setLoading(false);
        });
    } else if (activeRole === "HOD") {
      api
        .getHodOverview(apiParams)
        .then((data) => {
          setHodOverview(data);
          setLoading(false);
        })
        .catch((err) => {
          setError(err.message || "Failed to load HOD department overview.");
          setLoading(false);
        });
    }
  }, [activeRole, userDepartment, filters]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const avgGpa = adminOverview?.average_gpa !== undefined ? adminOverview.average_gpa : adminOverview?.avg_gpa || 0.0;
  const avgAtt = adminOverview?.average_attendance !== undefined ? adminOverview.average_attendance : adminOverview?.avg_attendance || 0.0;
  const avgDropProb = adminOverview?.average_dropout_probability !== undefined ? adminOverview.average_dropout_probability : 0.0;
  const lowRisk = adminOverview?.risk_distribution?.low !== undefined ? adminOverview.risk_distribution.low : adminOverview?.low_risk_count || 0;
  const medRisk = adminOverview?.risk_distribution?.medium !== undefined ? adminOverview.risk_distribution.medium : adminOverview?.medium_risk_count || 0;
  const highRisk = adminOverview?.risk_distribution?.high !== undefined ? adminOverview.risk_distribution.high : adminOverview?.high_risk_count || 0;
  const modelStatus = adminOverview?.model_status || "active";

  return (
    <div>
      {/* Top Welcome & Active Role Banner */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", marginBottom: "1.5rem", gap: "1rem" }}>
        <div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#0f172a", marginBottom: "0.25rem" }}>
            Institutional Intelligence Platform
          </h1>
          <p style={{ color: "#475569", fontSize: "0.95rem" }}>
            Role-Based Hierarchical Data Access: <strong style={{ color: "#2563eb" }}>{getRoleLabel()}</strong>
          </p>
        </div>
      </div>

      {(activeRole === "ADMINISTRATOR" || activeRole === "HOD") && (
        <Link
          to="/department-performance"
          className="btn-primary"
          style={{ marginBottom: "1.5rem", padding: "0.85rem 1.1rem", fontSize: "0.95rem" }}
        >
          View Department Performance <ChevronRight size={18} />
        </Link>
      )}

      {/* Dynamic Dependent Filter Bar */}
      <FilterBar
        filters={filters}
        onFilterChange={setFilters}
        showRiskFilter={true}
        showSearch={false}
      />

      {loading ? (
        <LoadingSpinner message={`Loading ${activeRole} institutional analytics...`} />
      ) : error ? (
        <ErrorAlert message={error} onRetry={loadDashboardData} />
      ) : activeRole === "ADMINISTRATOR" ? (
        /* ==================================================== */
        /* ADMINISTRATOR DASHBOARD VIEW                         */
        /* ==================================================== */
        <div>
          {/* Admin Metric Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1.25rem", marginBottom: "1.5rem" }}>
            <div className="card" style={{ padding: "1.25rem" }}>
              <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700 }}>TOTAL MATCHING STUDENTS</span>
              <h3 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#0f172a", marginTop: "0.2rem" }}>
                {adminOverview?.total_students?.toLocaleString() || "0"}
              </h3>
              <span style={{ fontSize: "0.75rem", color: "#059669", fontWeight: 600 }}>Active Enrolled</span>
            </div>

            <div className="card" style={{ padding: "1.25rem" }}>
              <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700 }}>HIGH RISK COUNT</span>
              <h3 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#be123c", marginTop: "0.2rem" }}>
                {highRisk.toLocaleString()}
              </h3>
              <span style={{ fontSize: "0.75rem", color: "#be123c", fontWeight: 600 }}>≥60% Risk Threshold</span>
            </div>

            <div className="card" style={{ padding: "1.25rem" }}>
              <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700 }}>MEDIUM RISK COUNT</span>
              <h3 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#b45309", marginTop: "0.2rem" }}>
                {medRisk.toLocaleString()}
              </h3>
              <span style={{ fontSize: "0.75rem", color: "#b45309", fontWeight: 600 }}>40-59% Risk Threshold</span>
            </div>

            <div className="card" style={{ padding: "1.25rem" }}>
              <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700 }}>LOW RISK COUNT</span>
              <h3 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#047857", marginTop: "0.2rem" }}>
                {lowRisk.toLocaleString()}
              </h3>
              <span style={{ fontSize: "0.75rem", color: "#047857", fontWeight: 600 }}>&lt;40% Risk Threshold</span>
            </div>

            <div className="card" style={{ padding: "1.25rem" }}>
              <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700 }}>AVERAGE GPA</span>
              <h3 style={{ fontSize: "1.75rem", fontWeight: 700, color: avgGpa >= 7.0 ? "#047857" : "#b45309", marginTop: "0.2rem" }}>
                {avgGpa.toFixed(2)}
              </h3>
              <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Cumulative GPA</span>
            </div>

            <div className="card" style={{ padding: "1.25rem" }}>
              <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700 }}>AVG ATTENDANCE</span>
              <h3 style={{ fontSize: "1.75rem", fontWeight: 700, color: avgAtt >= 75 ? "#047857" : "#be123c", marginTop: "0.2rem" }}>
                {avgAtt.toFixed(1)}%
              </h3>
              <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Target ≥75%</span>
            </div>

            <div className="card" style={{ padding: "1.25rem" }}>
              <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700 }}>AVG DROPOUT PROBABILITY</span>
              <h3 style={{ fontSize: "1.75rem", fontWeight: 700, color: avgDropProb >= 0.40 ? "#be123c" : "#047857", marginTop: "0.2rem" }}>
                {(avgDropProb * 100).toFixed(1)}%
              </h3>
              <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Logistic Regression Model</span>
            </div>

            <div className="card" style={{ padding: "1.25rem" }}>
              <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700 }}>MODEL STATUS</span>
              <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#047857", marginTop: "0.4rem", textTransform: "uppercase" }}>
                ● {modelStatus}
              </h3>
              <span style={{ fontSize: "0.75rem", color: "#059669", fontWeight: 600 }}>Active Trained Model</span>
            </div>
          </div>

          {/* Recharts Visualizations */}
          <AdminCharts overviewData={adminOverview} />
        </div>
      ) : (
        <HodDepartmentView hodData={hodOverview} />
      )}
    </div>
  );
}

import React, { useState, useEffect } from "react";
import {
  BrainCircuit,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  GraduationCap,
  DollarSign,
  BookOpen,
  Search,
  Sparkles,
  Filter,
  Layers,
} from "lucide-react";
import { api } from "../services/api";
import LoadingSpinner from "../components/common/LoadingSpinner";
import ErrorAlert from "../components/common/ErrorAlert";
import { formatINR } from "../utils/currency";

export default function Decisions() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // User context from localStorage
  const userRole = localStorage.getItem("platform_user_role") || "ADMINISTRATOR";
  const userDept = localStorage.getItem("platform_user_department") || "";
  const isHod = userRole === "HOD";

  // Filter states
  const [selectedDept, setSelectedDept] = useState(isHod ? userDept : "");
  const [selectedYear, setSelectedYear] = useState("");
  const [departments, setDepartments] = useState([]);
  const [years, setYears] = useState([]);

  // Query assistant state
  const [queryInput, setQueryInput] = useState("");
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryResult, setQueryResult] = useState(null);

  useEffect(() => {
    // Load available departments & years for filters
    api.getAccessibleDepartments().then((res) => {
      setDepartments(res || []);
    }).catch(() => {});

    api.getAccessibleYears().then((res) => {
      setYears(res || []);
    }).catch(() => {});
  }, []);

  const fetchOverview = () => {
    setLoading(true);
    setError(null);
    const params = {};
    if (selectedDept && !isHod) params.department = selectedDept;
    if (selectedYear) params.academic_year = selectedYear;

    api
      .getDecisionOverview(params)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load Decision Assistant intelligence.");
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchOverview();
  }, [selectedDept, selectedYear]);

  const handleQuerySubmit = (e, customQuery) => {
    if (e) e.preventDefault();
    const q = customQuery || queryInput;
    if (!q.trim()) return;

    setQueryLoading(true);
    setQueryInput(q);
    api
      .queryDecisionAssistant(q, {
        department: selectedDept && !isHod ? selectedDept : undefined,
        academic_year: selectedYear || undefined,
      })
      .then((res) => {
        setQueryResult(res);
        setQueryLoading(false);
      })
      .catch((err) => {
        setQueryLoading(false);
      });
  };

  if (loading && !data) return <LoadingSpinner message="Synthesizing cross-module institutional intelligence..." />;
  if (error && !data) return <ErrorAlert message={error} onRetry={fetchOverview} />;

  const evidence = data?.evidence || {};
  const studentEv = evidence.student || {};
  const financeEv = evidence.finance || {};
  const researchEv = evidence.research || {};
  return (
    <div style={{ paddingBottom: "3rem" }}>
      {/* HEADER BAR */}
      <div style={{ marginBottom: "1.5rem" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.85rem" }}>
            <div style={{ padding: "0.75rem", borderRadius: "0.75rem", backgroundColor: "#faf5ff", color: "#9333ea", border: "1px solid #e9d5ff" }}>
              <BrainCircuit size={32} />
            </div>
            <div>
              <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#0f172a", margin: 0 }}>
                Executive Decision Assistant
              </h1>
              <p style={{ color: "#475569", fontSize: "0.95rem", margin: "0.25rem 0 0 0" }}>
                Cross-module intelligence synthesis combining Student, Finance, and Research analytics.
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <span style={{ fontSize: "0.85rem", fontWeight: 600, padding: "0.4rem 0.85rem", borderRadius: "2rem", backgroundColor: "#eff6ff", color: "#1d4ed8", border: "1px solid #bfdbfe", display: "flex", alignItems: "center", gap: "0.35rem" }}>
              <Layers size={14} /> Scope: {data?.scope?.role || userRole} {data?.scope?.department ? `(${data.scope.department})` : ""}
            </span>
          </div>
        </div>
      </div>

      {/* FILTERS BAR */}
      <div className="card" style={{ marginBottom: "1.5rem", padding: "1rem 1.25rem" }}>
        <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: "1.25rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontWeight: 600, color: "#334155", fontSize: "0.9rem" }}>
            <Filter size={16} /> Filters:
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <label style={{ fontSize: "0.85rem", color: "#64748b", fontWeight: 500 }}>Department:</label>
            {isHod ? (
              <span style={{ fontSize: "0.85rem", fontWeight: 600, padding: "0.3rem 0.75rem", borderRadius: "0.375rem", backgroundColor: "#f1f5f9", color: "#334155", border: "1px solid #cbd5e1" }}>
                {userDept || "Assigned Department"} (Locked)
              </span>
            ) : (
              <select
                value={selectedDept}
                onChange={(e) => setSelectedDept(e.target.value)}
                style={{ padding: "0.4rem 0.75rem", borderRadius: "0.375rem", border: "1px solid #cbd5e1", fontSize: "0.85rem", backgroundColor: "#fff", color: "#1e293b" }}
              >
                <option value="">All Departments</option>
                {departments.map((d) => (
                  <option key={d.code} value={d.code}>
                    {d.name} ({d.code})
                  </option>
                ))}
              </select>
            )}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <label style={{ fontSize: "0.85rem", color: "#64748b", fontWeight: 500 }}>Academic Year:</label>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(e.target.value)}
              style={{ padding: "0.4rem 0.75rem", borderRadius: "0.375rem", border: "1px solid #cbd5e1", fontSize: "0.85rem", backgroundColor: "#fff", color: "#1e293b" }}
            >
              <option value="">All Years</option>
              {years.map((y) => (
                <option key={y} value={y}>
                  Year {y}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* NATURAL QUERY ASSISTANT INTERFACE */}
      <div className="card" style={{ marginBottom: "1.5rem", background: "linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%)", border: "1px solid #e9d5ff" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
          <Sparkles size={20} style={{ color: "#9333ea" }} />
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#581c87", margin: 0 }}>
            Ask Institutional Data Assistant
          </h3>
        </div>
        <p style={{ fontSize: "0.875rem", color: "#6b21a8", marginBottom: "1rem" }}>
          Query real cross-module metrics across Student, Finance, and Research datasets for evidence-backed answers.
        </p>

        <form onSubmit={handleQuerySubmit} style={{ display: "flex", gap: "0.5rem", marginBottom: "0.75rem" }}>
          <div style={{ position: "relative", flex: 1 }}>
            <Search size={18} style={{ position: "absolute", left: "0.85rem", top: "50%", transform: "translateY(-50%)", color: "#a855f7" }} />
            <input
              type="text"
              placeholder="e.g. Which departments require attention? / Where is financial stress visible?"
              value={queryInput}
              onChange={(e) => setQueryInput(e.target.value)}
              style={{ width: "100%", padding: "0.6rem 1rem 0.6rem 2.5rem", borderRadius: "0.5rem", border: "1px solid #c084fc", fontSize: "0.9rem", backgroundColor: "#ffffff" }}
            />
          </div>
          <button
            type="submit"
            disabled={queryLoading}
            style={{ padding: "0.6rem 1.25rem", borderRadius: "0.5rem", backgroundColor: "#9333ea", color: "#ffffff", border: "none", fontWeight: 600, cursor: "pointer", fontSize: "0.9rem" }}
          >
            {queryLoading ? "Analyzing..." : "Query Assistant"}
          </button>
        </form>

        {/* Quick query pills */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
          <span style={{ fontSize: "0.78rem", color: "#7e22ce", fontWeight: 600, display: "flex", alignItems: "center" }}>Suggested:</span>
          {[
            "Which departments require attention?",
            "What are the primary student risks?",
            "Where is financial pressure visible?",
            "Give me an overall institutional summary.",
          ].map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleQuerySubmit(null, q)}
              style={{ fontSize: "0.78rem", padding: "0.25rem 0.6rem", borderRadius: "1rem", backgroundColor: "#ffffff", color: "#6b21a8", border: "1px solid #d8b4fe", cursor: "pointer" }}
            >
              {q}
            </button>
          ))}
        </div>

        {/* Query Result Box */}
        {queryResult && (
          <div style={{ marginTop: "1rem", padding: "1rem", backgroundColor: "#ffffff", borderRadius: "0.5rem", border: "1px solid #d8b4fe", boxShadow: "0 2px 4px rgba(0,0,0,0.05)" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
              <span style={{ fontSize: "0.8rem", fontWeight: 700, padding: "0.2rem 0.5rem", borderRadius: "0.25rem", backgroundColor: "#f3e8ff", color: "#7e22ce" }}>
                Intent: {queryResult.matched_intent}
              </span>
              <button onClick={() => setQueryResult(null)} style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", fontSize: "0.8rem" }}>Close</button>
            </div>
            <p style={{ fontSize: "0.9rem", color: "#1e293b", fontWeight: 500, margin: "0 0 0.5rem 0" }}>
              {queryResult.summary}
            </p>
            {queryResult.findings && queryResult.findings.length > 0 && (
              <div style={{ marginTop: "0.5rem", fontSize: "0.85rem", color: "#475569" }}>
                <strong>Evidence Finding:</strong> {queryResult.findings[0].description}
              </div>
            )}
          </div>
        )}
      </div>

      {/* DECISION SUMMARY BANNER */}
      <div className="card" style={{ marginBottom: "1.5rem", borderLeft: "4px solid #9333ea" }}>
        <h3 className="card-title" style={{ marginBottom: "0.5rem", color: "#581c87" }}>
          Executive Decision Summary
        </h3>
        <p style={{ color: "#334155", fontSize: "0.95rem", lineHeight: "1.5", margin: 0 }}>
          {data?.summary}
        </p>
      </div>

      {/* KEY FINDINGS BY DOMAIN */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a", marginBottom: "1rem" }}>
          Cross-Module Key Findings
        </h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1.25rem" }}>
          {/* Student Domain Finding Card */}
          <div className="card" style={{ borderTop: "4px solid #10b981" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "0.75rem" }}>
              <div style={{ padding: "0.5rem", borderRadius: "0.375rem", backgroundColor: "#ecfdf5", color: "#059669" }}>
                <GraduationCap size={22} />
              </div>
              <div>
                <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#065f46", margin: 0 }}>Student Success</h3>
                <span style={{ fontSize: "0.75rem", color: "#64748b" }}>ML Dropout Risk Intelligence</span>
              </div>
            </div>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#047857", marginBottom: "0.25rem" }}>
              {studentEv.high_risk_pct}% High Risk
            </div>
            <p style={{ fontSize: "0.875rem", color: "#475569", lineHeight: "1.4", margin: "0 0 0.75rem 0" }}>
              Out of {studentEv.total_students?.toLocaleString()} students, {studentEv.high_risk_students?.toLocaleString()} are at high risk. Top predictor: <strong>{studentEv.top_risk_factor}</strong>.
            </p>
            <div style={{ fontSize: "0.8rem", padding: "0.4rem 0.6rem", borderRadius: "0.25rem", backgroundColor: "#f0fdf4", color: "#15803d", fontWeight: 600 }}>
              Highest Risk Dept: {studentEv.top_risk_department}
            </div>
          </div>

          {/* Finance Domain Finding Card */}
          <div className="card" style={{ borderTop: "4px solid #f59e0b" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "0.75rem" }}>
              <div style={{ padding: "0.5rem", borderRadius: "0.375rem", backgroundColor: "#fffbeb", color: "#d97706" }}>
                <DollarSign size={22} />
              </div>
              <div>
                <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#92400e", margin: 0 }}>Financial Intelligence</h3>
                <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Rule-Based Fiscal Metrics</span>
              </div>
            </div>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#b45309", marginBottom: "0.25rem" }}>
              {financeEv.budget_utilization_pct}% Budget Utilized
            </div>
            <p style={{ fontSize: "0.875rem", color: "#475569", lineHeight: "1.4", margin: "0 0 0.75rem 0" }}>
              Total budget allocation {formatINR(financeEv.total_budget)}. {financeEv.overrun_departments_count} department(s) report budget overrun.
            </p>
            <div style={{ fontSize: "0.8rem", padding: "0.4rem 0.6rem", borderRadius: "0.25rem", backgroundColor: "#fffbeb", color: "#b45309", fontWeight: 600 }}>
              Outstanding Fees: {financeEv.outstanding_fee_pct}% of total
            </div>
          </div>

          {/* Research Domain Finding Card */}
          <div className="card" style={{ borderTop: "4px solid #3b82f6" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "0.75rem" }}>
              <div style={{ padding: "0.5rem", borderRadius: "0.375rem", backgroundColor: "#eff6ff", color: "#2563eb" }}>
                <BookOpen size={22} />
              </div>
              <div>
                <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#1e40af", margin: 0 }}>Research Intelligence</h3>
                <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Productivity & Publications</span>
              </div>
            </div>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#1d4ed8", marginBottom: "0.25rem" }}>
              {researchEv.participation_rate_pct}% Participation
            </div>
            <p style={{ fontSize: "0.875rem", color: "#475569", lineHeight: "1.4", margin: "0 0 0.75rem 0" }}>
              Total student research publications: {researchEv.total_publications?.toLocaleString()} ({researchEv.avg_publications_per_student} per student avg).
            </p>
            <div style={{ fontSize: "0.8rem", padding: "0.4rem 0.6rem", borderRadius: "0.25rem", backgroundColor: "#eff6ff", color: "#1d4ed8", fontWeight: 600 }}>
              Avg Faculty Rating: {researchEv.avg_faculty_rating} / 5.0
            </div>
          </div>
        </div>
      </div>

      {/* AREAS REQUIRING ATTENTION (RISK ALERTS) */}
      <div style={{ marginBottom: "1.5rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
          <AlertTriangle size={20} style={{ color: "#dc2626" }} />
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a", margin: 0 }}>
            Areas Requiring Proactive Attention ({data?.areas_of_attention?.length || 0})
          </h2>
        </div>

        {data?.areas_of_attention && data.areas_of_attention.length > 0 ? (
          <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "1rem" }}>
            {data.areas_of_attention.map((item) => {
              const isHigh = item.severity === "HIGH";
              const isMed = item.severity === "MEDIUM";
              const borderCol = isHigh ? "#ef4444" : isMed ? "#f59e0b" : "#3b82f6";
              const bgCol = isHigh ? "#fef2f2" : isMed ? "#fffbeb" : "#eff6ff";

              return (
                <div
                  key={item.id}
                  className="card"
                  style={{ borderLeft: `5px solid ${borderCol}`, padding: "1.1rem 1.25rem" }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.5rem" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                      <span style={{ fontSize: "0.75rem", fontWeight: 700, padding: "0.2rem 0.5rem", borderRadius: "0.25rem", backgroundColor: bgCol, color: borderCol, border: `1px solid ${borderCol}` }}>
                        {item.severity} SEVERITY
                      </span>
                      <h4 style={{ fontSize: "1rem", fontWeight: 700, color: "#0f172a", margin: 0 }}>
                        {item.title}
                      </h4>
                    </div>

                    <div style={{ display: "flex", gap: "0.35rem" }}>
                      {item.affected_modules.map((m) => (
                        <span key={m} style={{ fontSize: "0.72rem", padding: "0.15rem 0.45rem", borderRadius: "0.25rem", backgroundColor: "#f1f5f9", color: "#475569", border: "1px solid #cbd5e1" }}>
                          {m}
                        </span>
                      ))}
                    </div>
                  </div>

                  <p style={{ fontSize: "0.875rem", color: "#334155", margin: "0 0 0.5rem 0" }}>
                    {item.observation}
                  </p>

                  <div style={{ fontSize: "0.8rem", color: "#64748b", fontWeight: 600 }}>
                    Supporting Metric: <span style={{ color: "#0f172a" }}>{item.supporting_metric}</span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="card" style={{ padding: "1.5rem", textAlign: "center", color: "#64748b" }}>
            <CheckCircle2 size={32} style={{ color: "#10b981", marginBottom: "0.5rem" }} />
            <p style={{ margin: 0, fontWeight: 600 }}>No critical cross-module risk alerts identified for current scope.</p>
          </div>
        )}
      </div>

      {/* RECOMMENDED ACTIONS */}
      <div style={{ marginBottom: "1.5rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
          <TrendingUp size={20} style={{ color: "#9333ea" }} />
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a", margin: 0 }}>
            Evidence-Backed Policy Recommendations ({data?.recommendations?.length || 0})
          </h2>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: "1rem" }}>
          {data?.recommendations?.map((rec) => (
            <div key={rec.id} className="card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, padding: "0.2rem 0.5rem", borderRadius: "0.25rem", backgroundColor: "#faf5ff", color: "#7e22ce", border: "1px solid #e9d5ff" }}>
                    PRIORITY: {rec.priority}
                  </span>
                  <span style={{ fontSize: "0.78rem", color: "#64748b" }}>Target: {rec.target_department}</span>
                </div>
                <h4 style={{ fontSize: "1rem", fontWeight: 700, color: "#0f172a", marginBottom: "0.5rem" }}>
                  {rec.title}
                </h4>
                <p style={{ fontSize: "0.875rem", color: "#334155", lineHeight: "1.4", marginBottom: "0.75rem" }}>
                  <strong>Action:</strong> {rec.action}
                </p>
                <p style={{ fontSize: "0.825rem", color: "#64748b", lineHeight: "1.4", margin: 0 }}>
                  <strong>Rationale:</strong> {rec.rationale}
                </p>
              </div>

              <div style={{ marginTop: "1rem", paddingTop: "0.75rem", borderTop: "1px solid #e2e8f0", fontSize: "0.78rem", color: "#475569" }}>
                <strong>Evidence:</strong> {rec.supporting_evidence}
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}

import { useEffect, useMemo, useState } from "react";
import { ArrowUpRight, BrainCircuit, Search } from "lucide-react";
import { api } from "../services/api";
import LoadingSpinner from "../components/common/LoadingSpinner";
import ErrorAlert from "../components/common/ErrorAlert";
import { useAuth } from "../context/AuthContext";
import { formatDecisionMetric } from "../utils/decisionFormatting";
import "./Decisions.css";

const MODULE_NAMES = {
  student: "Student",
  finance: "Finance",
  research: "Faculty Research",
};

function formatLabel(value) {
  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function MetricValue({ metricKey, value }) {
  return formatDecisionMetric(metricKey, value);
}

function QueryEvidence({ metrics }) {
  const safeMetrics = metrics && typeof metrics === "object" && !Array.isArray(metrics)
    ? metrics
    : {};
  const entries = Object.entries(safeMetrics).filter(([key, value]) => (
    key !== "scope" && value !== null && value !== undefined
  ));
  const scalarEntries = entries.filter(([, value]) => (
    typeof value === "string" || typeof value === "number" || typeof value === "boolean"
  ));
  const primitiveListEntries = entries.filter(([, value]) => (
    Array.isArray(value)
    && value.length > 0
    && value.every((item) => typeof item === "string" || typeof item === "number")
  ));
  const detailEntries = entries
    .filter(([, value]) => Array.isArray(value))
    .map(([key, values]) => [
      key,
      values.filter((item) => item && typeof item === "object" && !Array.isArray(item)),
    ])
    .filter(([, values]) => values.length > 0);
  const attentionCriteria = safeMetrics.attention_criteria;

  if (
    !scalarEntries.length
    && !primitiveListEntries.length
    && !detailEntries.length
    && !attentionCriteria
  ) return null;

  return (
    <div className="decision-query-evidence">
      {scalarEntries.map(([key, value]) => (
        <div className="decision-evidence-metric" key={key}>
          <span>{formatLabel(key)}</span>
          <strong><MetricValue metricKey={key} value={value} /></strong>
        </div>
      ))}
      {primitiveListEntries.map(([key, values]) => (
        <div className="decision-evidence-list" key={key}>
          <span className="decision-evidence-list-title">{formatLabel(key)}</span>
          <span>{values.map((value) => (
            typeof value === "number" ? formatDecisionMetric(key, value) : value
          )).join(" · ")}</span>
        </div>
      ))}
      {detailEntries.map(([key, values]) => values.length > 0 && (
        <div className="decision-evidence-list" key={key}>
          <span className="decision-evidence-list-title">{formatLabel(key)}</span>
          <span className="decision-evidence-count">{values.length} result{values.length === 1 ? "" : "s"}</span>
          {values.map((item, index) => (
            <div className="decision-evidence-row" key={`${key}-${item.department || item.faculty_id || item.student_id || index}`}>
              <strong>{item.department || item.faculty_name || item.student_id || item.academic_year || "Result"}</strong>
              <span>
                {Object.entries(item)
                  .filter(([name, value]) => (
                    !["department", "faculty_name", "faculty_id", "student_id", "academic_year"].includes(name)
                    && (
                      typeof value === "number"
                      || typeof value === "string"
                      || (Array.isArray(value) && value.every((item) => typeof item === "string" || typeof item === "number"))
                    )
                  ))
                  .map(([name, value]) => `${formatLabel(name)}: ${Array.isArray(value) ? value.join(", ") : formatDecisionMetric(name, value)}`)
                  .join(" · ")}
              </span>
            </div>
          ))}
        </div>
      ))}
      {attentionCriteria && typeof attentionCriteria === "object" && !Array.isArray(attentionCriteria) && (
        <div className="decision-evidence-list decision-criteria">
          <span className="decision-evidence-list-title">Selection criteria</span>
          {Object.entries(attentionCriteria).map(([key, value]) => (
            <div className="decision-evidence-row" key={key}>
              <strong>{formatLabel(key)}</strong>
              <span>{typeof value === "string" || typeof value === "number" ? value : ""}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Decisions() {
  const { role, department: userDepartment } = useAuth();
  const isHod = role === "HOD";
  const [selectedDepartment, setSelectedDepartment] = useState("");
  const [selectedYear, setSelectedYear] = useState("");
  const [departments, setDepartments] = useState([]);
  const [years, setYears] = useState([]);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [queryResult, setQueryResult] = useState(null);
  const [queryError, setQueryError] = useState("");
  const [queryLoading, setQueryLoading] = useState(false);

  const params = useMemo(() => ({
    ...(isHod ? {} : selectedDepartment ? { department: selectedDepartment } : {}),
    ...(selectedYear ? { academic_year: selectedYear } : {}),
  }), [isHod, selectedDepartment, selectedYear]);

  useEffect(() => {
    let active = true;
    Promise.all([
      api.getAccessibleDepartments(),
      api.getAccessibleYears(isHod ? userDepartment : selectedDepartment || undefined),
    ]).then(([departmentOptions, yearOptions]) => {
      if (!active) return;
      setDepartments(departmentOptions || []);
      setYears(yearOptions || []);
    }).catch((loadError) => {
      if (active) setError(loadError.message || "Unable to load Decision Assistant filters.");
    });
    return () => { active = false; };
  }, [isHod, selectedDepartment, userDepartment]);

  useEffect(() => {
    let active = true;
    api.getDecisionOverview(params).then((response) => {
      if (active) setData(response);
    }).catch((loadError) => {
      if (active) setError(loadError.message || "Unable to load decision data.");
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [params]);

  const submitQuery = async (event) => {
    event.preventDefault();
    const question = query.trim();
    if (!question || queryLoading) return;

    setQueryLoading(true);
    setQueryError("");
    setQueryResult(null);
    try {
      const response = await api.queryDecisionAssistant(question, params);
      setQueryResult(response);
    } catch (requestError) {
      setQueryError(requestError.message || "The query could not be answered.");
    } finally {
      setQueryLoading(false);
    }
  };

  const updateDepartment = (value) => {
    setLoading(true);
    setError("");
    setQueryResult(null);
    setSelectedDepartment(value);
  };

  const updateYear = (value) => {
    setLoading(true);
    setError("");
    setQueryResult(null);
    setSelectedYear(value);
  };

  const evidence = data?.evidence;
  const moduleStatuses = [
    ["student", evidence?.student?.status],
    ["finance", evidence?.finance?.status],
    ["research", evidence?.research?.status],
  ];

  return (
    <main className="decision-page">
      <header className="decision-header">
        <div className="decision-heading">
          <div className="decision-heading-icon"><BrainCircuit size={25} /></div>
          <div>
            <h1>Executive Decision Assistant</h1>
            <p>Ask a question and get a concise answer grounded in current institutional data.</p>
          </div>
        </div>
        <div className="decision-scope" aria-label="Role-based data scope">
          <span>{data?.scope?.role || role || "Authenticated"} scope</span>
          <strong>{isHod ? (userDepartment || "Assigned department") : (data?.scope?.department || "Institution-wide")}</strong>
        </div>
      </header>

      <section className="decision-filters card" aria-label="Decision data filters">
        <label>
          <span>Department</span>
          {isHod ? (
            <span className="decision-locked-filter">{userDepartment || "Assigned department"} · locked</span>
          ) : (
            <select value={selectedDepartment} onChange={(event) => updateDepartment(event.target.value)}>
              <option value="">All departments</option>
              {departments.map((item) => (
                <option key={item.id || item.code} value={item.id || item.code}>
                  {item.name || item.id || item.code}
                </option>
              ))}
            </select>
          )}
        </label>
        <label>
          <span>Academic year</span>
          <select value={selectedYear} onChange={(event) => updateYear(event.target.value)}>
            <option value="">All available years</option>
            {years.map((year) => (
              <option key={year} value={year}>
                {year}–{String((Number(year) + 1) % 100).padStart(2, "0")}
              </option>
            ))}
          </select>
        </label>
        <div className="decision-data-status" aria-label="Module data availability">
          {moduleStatuses.map(([module, status]) => {
            const resolvedStatus = status || (loading ? "loading" : "unavailable");
            return (
            <span className={resolvedStatus === "available" ? "is-available" : resolvedStatus === "unavailable" ? "is-unavailable" : ""} key={module}>
              <i aria-hidden="true" />
              {MODULE_NAMES[module]} {resolvedStatus}
            </span>
            );
          })}
        </div>
      </section>

      {error && !data && <ErrorAlert message={error} />}
      {loading && !data && <LoadingSpinner message="Loading current institutional data..." />}

      <section className="decision-query card">
        <div className="decision-section-heading">
          <div>
            <h2>Query Assistant</h2>
            <p>Ask about student risk, budgets, faculty research, or cross-module comparisons.</p>
          </div>
          <span className="decision-live-label">Current data</span>
        </div>
        <form className="decision-query-form" onSubmit={submitQuery}>
          <label className="decision-query-input">
            <Search size={19} aria-hidden="true" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="e.g. Which department has the highest dropout risk?"
              maxLength={500}
              aria-label="Ask the Decision Assistant"
            />
          </label>
          <button type="submit" disabled={!query.trim() || queryLoading}>
            {queryLoading ? "Analyzing…" : "Ask"}
            {!queryLoading && <ArrowUpRight size={17} />}
          </button>
        </form>
        {queryError && <p className="decision-error" role="alert">{queryError}</p>}
        {queryResult && (
          <div className="decision-answer" aria-live="polite">
            <div className="decision-answer-meta">
              {queryResult.matched_intent !== "unsupported" && (
                <span>{formatLabel(queryResult.matched_intent)}</span>
              )}
              <button type="button" onClick={() => setQueryResult(null)}>Clear answer</button>
            </div>
            <p>{queryResult.summary}</p>
            <QueryEvidence metrics={queryResult.supporting_metrics} />
          </div>
        )}
      </section>

      <section className="decision-findings">
        <div className="decision-section-heading">
          <div>
            <h2>Cross-Module Key Findings</h2>
            <p>One current evidence summary per available module.</p>
          </div>
        </div>
        {loading && data && <p className="decision-inline-status">Refreshing findings…</p>}
        {error && data && <p className="decision-error" role="alert">{error}</p>}
        <div className="decision-finding-grid">
          {(data?.key_findings || []).map((finding) => (
            <article className={`decision-finding decision-finding-${finding.domain}`} key={finding.domain}>
              <span>{MODULE_NAMES[finding.domain] || formatLabel(finding.domain)}</span>
              <h3>{finding.title}</h3>
              <strong>{finding.metric}</strong>
              <p>{finding.description}</p>
              {finding.domain === "research" && evidence?.research?.is_synthetic && (
                <small className="decision-provenance">Source records are marked synthetic in the database.</small>
              )}
            </article>
          ))}
          {data && !data.key_findings?.length && (
            <p className="decision-empty">No module data is currently available for this scope.</p>
          )}
        </div>
      </section>

      {!!data?.actionable_issues?.length && (
        <section className="decision-issues">
          <div className="decision-section-heading">
            <div>
              <h2>Actionable Issues</h2>
              <p>Only signals supported by current data are shown.</p>
            </div>
          </div>
          <div className="decision-issue-list">
            {data.actionable_issues.slice(0, 4).map((issue, index) => (
              <article className="decision-issue" key={`${issue.domain}-${issue.department || "scope"}-${index}`}>
                <span>{MODULE_NAMES[issue.domain] || formatLabel(issue.domain)}</span>
                <div>
                  <h3>{issue.title}</h3>
                  <p>{issue.evidence}</p>
                </div>
                {issue.department && <strong>{issue.department}</strong>}
              </article>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}

import React from "react";
import {
  Activity,
  Banknote,
  BookOpen,
  CircleHelp,
  Users,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Cell,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const numberFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const decimalFormat = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const currencyFormat = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});
const tooltipStyle = { borderRadius: "0.5rem", border: "1px solid #cbd5e1" };
const CITATION_COLORS = ["#2563eb", "#0d9488", "#f59e0b", "#8b5cf6", "#ef4444", "#64748b"];

const definitions = {
  faculty: "Distinct active faculty members in the selected department. Faculty without an annual research record are still included.",
  researchers: "Distinct active faculty with at least one publication in the selected academic year or reporting period. Numerator: publishing faculty; denominator: active faculty.",
  publications: "Sum of publications in annual faculty research records for the selected department and reporting period.",
  average: "Total publications in the selected period divided by all distinct active faculty in scope, including faculty with zero publications or no annual record.",
  participation: "Publishing active faculty divided by all distinct active faculty in scope, multiplied by 100. Faculty with no annual record remain in the denominator.",
  grants: "Sum of grant amounts recorded in faculty research records for the selected reporting period.",
  citations: "Sum of citations recorded in faculty research records for the selected period.",
  averageCitations: "Average citations per faculty = total citations divided by all distinct active faculty. Average citations per publishing faculty = total citations divided by distinct active faculty with at least one publication. Both use the selected period; faculty counts are distinct across years.",
  rating: "Mean of non-missing faculty ratings in selected faculty-year records. Missing scores are excluded; count of included records is shown.",
  mentorship: "Mean of non-missing mentorship scores in selected faculty-year records. Missing scores are excluded; count of included records is shown.",
};

function KpiCard({ label, value, icon: Icon, definition }) {
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
      <h3 className="card-title">{title}</h3>
      <p className="department-performance-note">{description}</p>
      {children}
    </article>
  );
}

function EmptyChart() {
  return <div className="research-empty" role="status">No faculty research records are available for this reporting period.</div>;
}

export default function FacultyResearchAnalytics({ data }) {
  if (!data) return null;
  const { overview, departments, publication_trends: trends, top_researchers: researchers } = data;
  const chartDepartments = departments.map((item) => ({
    ...item,
    average_faculty_rating: item.average_faculty_rating ?? null,
    average_mentorship_score: item.average_mentorship_score ?? null,
  }));
  const formatMoney = (value) => currencyFormat.format(value || 0);

  return (
    <section className="faculty-research-section" aria-label="Faculty research analytics">
      <header className="faculty-research-heading">
        <div>
          <h2>Faculty Research Overview</h2>
          <p>
            {overview.selected_academic_year
              ? `Faculty output for academic year ${overview.selected_academic_year}.`
              : "Faculty output across all available academic years."}
            {overview.selected_department ? ` Department: ${overview.selected_department}.` : ""}
          </p>
        </div>
        <span className="synthetic-data-badge">
          {data.is_synthetic ? "Synthetic sample data — not actual university records" : "Institutional faculty research records"}
        </span>
      </header>

      <div className="research-kpis" aria-label="Faculty research key performance indicators">
        <KpiCard label="TOTAL ACTIVE FACULTY" value={numberFormat.format(overview.total_faculty)} icon={Users} definition={definitions.faculty} />
        <KpiCard label="FACULTY RESEARCHERS" value={numberFormat.format(overview.faculty_researchers)} icon={Activity} definition={definitions.researchers} />
        <KpiCard label="FACULTY PUBLICATIONS" value={numberFormat.format(overview.total_publications)} icon={BookOpen} definition={definitions.publications} />
        <KpiCard label="AVG PUBLICATIONS / FACULTY" value={decimalFormat.format(overview.average_publications_per_faculty)} icon={BookOpen} definition={definitions.average} />
        <KpiCard label="FACULTY PARTICIPATION" value={`${decimalFormat.format(overview.faculty_participation_rate)}%`} icon={Activity} definition={definitions.participation} />
        <KpiCard label="RESEARCH GRANTS" value={formatMoney(overview.total_research_grants)} icon={Banknote} definition={definitions.grants} />
        <KpiCard label="TOTAL CITATIONS" value={numberFormat.format(overview.total_citations)} icon={BookOpen} definition={definitions.citations} />
        <KpiCard label="AVG CITATIONS / FACULTY" value={decimalFormat.format(overview.average_citations_per_faculty)} icon={BookOpen} definition={`${definitions.averageCitations} In this period, ${numberFormat.format(overview.total_citations)} citations / ${numberFormat.format(overview.total_faculty)} active faculty = ${decimalFormat.format(overview.average_citations_per_faculty)}. Per publishing faculty: ${numberFormat.format(overview.total_citations)} citations / ${numberFormat.format(overview.publishing_faculty_count)} publishing faculty = ${overview.average_citations_per_publishing_faculty == null ? "not available" : decimalFormat.format(overview.average_citations_per_publishing_faculty)}.`} />
        <KpiCard label="AVG FACULTY RATING" value={overview.average_faculty_rating == null ? "—" : decimalFormat.format(overview.average_faculty_rating)} icon={Users} definition={`${definitions.rating} Valid records: ${overview.faculty_rating_count}.`} />
        <KpiCard label="AVG MENTORSHIP SCORE" value={overview.average_mentorship_score == null ? "—" : decimalFormat.format(overview.average_mentorship_score)} icon={Users} definition={`${definitions.mentorship} Valid records: ${overview.mentorship_score_count}.`} />
      </div>

      <section className="research-chart-grid" aria-label="Faculty research comparison charts">
        <ChartCard
          title="Faculty Publications by Department"
          description="Sum of annual faculty publication records in the selected reporting period. Counts are synthetic and are not student publications."
        >
          {chartDepartments.length ? (
            <div className="research-chart">
              <ResponsiveContainer>
                <BarChart data={chartDepartments} margin={{ top: 10, right: 12, left: 0, bottom: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="department" label={{ value: "Department", position: "insideBottom", offset: -14 }} />
                  <YAxis allowDecimals={false} label={{ value: "Publications", angle: -90, position: "insideLeft" }} />
                  <Tooltip formatter={(value) => [numberFormat.format(value), "Faculty publications"]} contentStyle={tooltipStyle} />
                  <Legend />
                  <Bar dataKey="publications" name="Faculty publications" fill="#2563eb" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : <EmptyChart />}
        </ChartCard>

        <ChartCard
          title="Faculty Research Participation by Department"
          description="Publishing faculty as a percentage of all active faculty in each department. Tooltip values include the publishing count and denominator."
        >
          {chartDepartments.length ? (
            <div className="research-chart">
              <ResponsiveContainer>
                <BarChart data={chartDepartments} margin={{ top: 10, right: 12, left: 0, bottom: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="department" label={{ value: "Department", position: "insideBottom", offset: -14 }} />
                  <YAxis domain={[0, 100]} tickFormatter={(value) => `${value}%`} label={{ value: "Participating faculty (%)", angle: -90, position: "insideLeft" }} />
                  <Tooltip
                    formatter={(value, _name, item) => [
                      `${decimalFormat.format(value)}% (${item.payload.faculty_researchers}/${item.payload.total_faculty} faculty)`,
                      "Participation",
                    ]}
                    contentStyle={tooltipStyle}
                  />
                  <Legend />
                  <Bar dataKey="participation_rate" name="Faculty participation" fill="#0d9488" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : <EmptyChart />}
        </ChartCard>

        <ChartCard
          title="Faculty Citation Distribution by Department"
          description="Total citations recorded in annual faculty research records for the selected reporting period."
        >
          {chartDepartments.length ? (
            <div className="research-chart">
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={chartDepartments} dataKey="total_citations" nameKey="department" cx="50%" cy="50%" innerRadius={52} outerRadius={92} paddingAngle={2}>
                    {chartDepartments.map((item, index) => (
                      <Cell key={item.department} fill={CITATION_COLORS[index % CITATION_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [numberFormat.format(value), "Citations"]} contentStyle={tooltipStyle} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : <EmptyChart />}
        </ChartCard>

        <ChartCard
          title="Faculty Publication Trends"
          description="Faculty publication totals grouped by academic year. Selecting a year narrows the chart to that reporting period."
        >
          {trends.length ? (
            <div className="research-chart">
              <ResponsiveContainer>
                <LineChart data={trends} margin={{ top: 10, right: 16, left: 0, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="academic_year" label={{ value: "Academic year", position: "insideBottom", offset: -3 }} />
                  <YAxis allowDecimals={false} label={{ value: "Count", angle: -90, position: "insideLeft" }} />
                  <Tooltip formatter={(value, name) => [numberFormat.format(value), name]} contentStyle={tooltipStyle} />
                  <Legend />
                  <Line type="monotone" dataKey="publications" name="Publications" stroke="#2563eb" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : <EmptyChart />}
        </ChartCard>

        <ChartCard
          title="Top Faculty Researchers by Publications"
          description="Faculty publication totals for the selected reporting period, ranked from highest to lowest."
        >
          {researchers.length ? (
            <div className="research-chart">
              <ResponsiveContainer>
                <BarChart data={researchers} layout="vertical" margin={{ top: 8, right: 16, left: 12, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" allowDecimals={false} label={{ value: "Publications", position: "insideBottom", offset: -3 }} />
                  <YAxis type="category" dataKey="faculty_name" width={108} tick={{ fontSize: 11 }} />
                  <Tooltip
                    formatter={(value, _name, item) => [
                      `${numberFormat.format(value)} publications; ${numberFormat.format(item.payload.citations)} citations`,
                      item.payload.department,
                    ]}
                    contentStyle={tooltipStyle}
                  />
                  <Legend />
                  <Bar dataKey="publications" name="Faculty publications" fill="#2563eb" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : <EmptyChart />}
        </ChartCard>

        <ChartCard
          title="Research Grant Distribution"
          description="Grant amounts attributed to faculty by department for the selected reporting period."
        >
          {chartDepartments.length ? (
            <div className="research-chart">
              <ResponsiveContainer>
                <BarChart data={chartDepartments} margin={{ top: 10, right: 12, left: 8, bottom: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="department" label={{ value: "Department", position: "insideBottom", offset: -14 }} />
                  <YAxis tickFormatter={(value) => `₹${numberFormat.format(value)}`} label={{ value: "Synthetic grant amount (₹)", angle: -90, position: "insideLeft" }} />
                  <Tooltip formatter={(value) => [formatMoney(value), "Synthetic grants"]} contentStyle={tooltipStyle} />
                  <Legend />
                  <Bar dataKey="research_grants" name="Synthetic grants" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : <EmptyChart />}
        </ChartCard>

        <ChartCard
          title="Faculty Rating and Mentorship by Department"
          description="Mean scores from valid faculty-year ratings and mentorship records only; missing scores are excluded. Both scales range from 1 to 5."
        >
          {chartDepartments.length ? (
            <div className="research-chart">
              <ResponsiveContainer>
                <BarChart data={chartDepartments} margin={{ top: 10, right: 12, left: 0, bottom: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="department" label={{ value: "Department", position: "insideBottom", offset: -14 }} />
                  <YAxis domain={[0, 5]} label={{ value: "Mean score (1–5)", angle: -90, position: "insideLeft" }} />
                  <Tooltip
                    formatter={(value, name, item) => [
                      value == null ? "Not available" : `${decimalFormat.format(value)} (${name === "Faculty rating" ? item.payload.faculty_rating_count : item.payload.mentorship_score_count} valid records)`,
                      name,
                    ]}
                    contentStyle={tooltipStyle}
                  />
                  <Legend />
                  <Bar dataKey="average_faculty_rating" name="Faculty rating" fill="#2563eb" />
                  <Bar dataKey="average_mentorship_score" name="Mentorship score" fill="#14b8a6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : <EmptyChart />}
        </ChartCard>
      </section>

      <section className="card research-table-card" aria-label="Top faculty researchers">
        <div className="card-header">
          <h3 className="card-title">Top Faculty Researchers</h3>
          <span className="synthetic-data-badge">{data.is_synthetic ? "Synthetic sample data" : "Institutional records"}</span>
        </div>
        {researchers.length ? (
          <div className="table-container">
            <table className="data-table faculty-research-table">
              <thead>
                <tr><th>Faculty</th><th>Department</th><th>Publications</th><th>Citations</th></tr>
              </thead>
              <tbody>
                {researchers.map((item) => (
                  <tr key={item.faculty_id}>
                    <td>{item.faculty_name}</td>
                    <td>{item.department}</td>
                    <td>{numberFormat.format(item.publications)}</td>
                    <td>{numberFormat.format(item.citations)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <EmptyChart />}
        <p className="department-performance-note">Ranked by publication count in the selected reporting period; ties are ordered by faculty name.</p>
      </section>
    </section>
  );
}

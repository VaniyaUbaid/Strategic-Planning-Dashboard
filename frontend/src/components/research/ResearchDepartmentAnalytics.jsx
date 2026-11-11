import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const numberFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const decimalFormat = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const chartTooltip = { borderRadius: "0.5rem", border: "1px solid #cbd5e1" };

export default function ResearchDepartmentAnalytics({ departments = [] }) {
  return (
    <>
      <section className="department-performance-chart-grid" aria-label="Department research comparisons">
        <article className="card department-performance-chart-card">
          <h2 className="card-title">Research participation rate by department</h2>
          <p className="department-performance-note">
            Share of department student records marked as participating; unknown participation statuses remain in the denominator.
          </p>
          <div className="department-performance-chart">
            <ResponsiveContainer>
              <BarChart data={departments} margin={{ top: 16, right: 12, left: 4, bottom: 24 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="department" stroke="#64748b" tick={{ fontSize: 12 }} label={{ value: "Department", position: "insideBottom", offset: -14 }} />
                <YAxis domain={[0, 100]} tickFormatter={(value) => `${value}%`} stroke="#64748b" label={{ value: "Participating students (%)", angle: -90, position: "insideLeft" }} />
                <Tooltip formatter={(value) => [`${decimalFormat.format(value)}%`, "Participation rate"]} contentStyle={chartTooltip} />
                <Bar dataKey="participation_rate" name="Participation rate" fill="#0d9488" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="card department-performance-chart-card">
          <h2 className="card-title">Average publications per student by department</h2>
          <p className="department-performance-note">
            Mean publication count among records with a reported publication value; this is descriptive, not a causal measure of research quality.
          </p>
          <div className="department-performance-chart">
            <ResponsiveContainer>
              <BarChart data={departments} margin={{ top: 16, right: 12, left: 4, bottom: 24 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="department" stroke="#64748b" tick={{ fontSize: 12 }} label={{ value: "Department", position: "insideBottom", offset: -14 }} />
                <YAxis allowDecimals stroke="#64748b" label={{ value: "Publications per reported student", angle: -90, position: "insideLeft" }} />
                <Tooltip formatter={(value) => [decimalFormat.format(value), "Average publications"]} contentStyle={chartTooltip} />
                <Bar dataKey="average_publications" name="Average publications" fill="#2563eb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>
      </section>

      <section className="card" aria-label="Department research performance table">
        <div className="card-header">
          <h2 className="card-title">Department Research Performance</h2>
          <span style={{ color: "#64748b", fontSize: "0.85rem" }}>{numberFormat.format(departments.length)} departments</span>
        </div>
        {departments.length ? (
          <div className="table-container">
            <table className="data-table department-performance-table">
              <thead>
                <tr>
                  <th>Department</th>
                  <th>Total Students</th>
                  <th>Research Participants</th>
                  <th>Participation Rate</th>
                  <th>Total Publications</th>
                  <th>Avg Publications*</th>
                  <th>Avg Faculty Rating</th>
                  <th>Avg Mentorship Score</th>
                  <th>Avg Infrastructure Rating</th>
                </tr>
              </thead>
              <tbody>
                {departments.map((item) => (
                  <tr key={item.department}>
                    <td style={{ fontWeight: 700 }}>{item.department}</td>
                    <td>{numberFormat.format(item.total_students)}</td>
                    <td>{numberFormat.format(item.research_participants)}</td>
                    <td>{decimalFormat.format(item.participation_rate)}%</td>
                    <td>{numberFormat.format(item.total_publications)}</td>
                    <td>{decimalFormat.format(item.average_publications)}</td>
                    <td>{item.average_faculty_rating == null ? "—" : decimalFormat.format(item.average_faculty_rating)}</td>
                    <td>{item.average_mentorship_score == null ? "—" : decimalFormat.format(item.average_mentorship_score)}</td>
                    <td>{item.average_infrastructure_rating == null ? "—" : decimalFormat.format(item.average_infrastructure_rating)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="research-empty" role="status">No department research records available for the selected filters.</div>
        )}
        <p className="department-performance-note" style={{ marginTop: "0.75rem" }}>
          *Average publications is calculated from non-missing publication values in each department. No research funding field is available in this dataset.
        </p>
      </section>
    </>
  );
}

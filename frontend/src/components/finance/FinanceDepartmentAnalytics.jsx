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
import RiskBadge from "../common/RiskBadge";
import { formatINR, formatINRPrecise } from "../../utils/currency";

const axis = { fontSize: 12 };
const tooltipStyle = { borderRadius: "0.5rem", border: "1px solid #cbd5e1" };

export default function FinanceDepartmentAnalytics({ departments = [] }) {
  return (
    <>
      <section className="department-performance-chart-grid" aria-label="Department financial comparisons">
        <article className="card department-performance-chart-card">
          <h2 className="card-title">Budget utilization by department</h2>
          <p className="department-performance-note">
            Actual expenditure divided by allocated budget. Values above 100% indicate spending beyond the reported allocation.
          </p>
          <div className="department-performance-chart">
            <ResponsiveContainer>
              <BarChart data={departments} margin={{ top: 16, right: 12, left: 18, bottom: 24 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="department_id" stroke="#64748b" tick={axis} label={{ value: "Department", position: "insideBottom", offset: -14 }} />
                <YAxis tickFormatter={(value) => `${value}%`} stroke="#64748b" tick={axis} label={{ value: "Budget utilized (%)", angle: -90, position: "insideLeft" }} />
                <Tooltip formatter={(value) => [`${Number(value).toFixed(1)}%`, "Budget utilization"]} contentStyle={tooltipStyle} />
                <Bar dataKey="budget_utilization" name="Budget utilization" fill="#2563eb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="card department-performance-chart-card">
          <h2 className="card-title">Revenue and expenditure by department</h2>
          <p className="department-performance-note">
            Aggregated financial totals for the selected academic-year scope. Both series use the same rupee scale.
          </p>
          <div className="department-performance-chart">
            <ResponsiveContainer>
              <BarChart data={departments} margin={{ top: 16, right: 12, left: 24, bottom: 24 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="department_id" stroke="#64748b" tick={axis} label={{ value: "Department", position: "insideBottom", offset: -14 }} />
                <YAxis tickFormatter={(value) => formatINR(value, true)} stroke="#64748b" tick={axis} label={{ value: "Amount (₹)", angle: -90, position: "insideLeft" }} />
                <Tooltip formatter={(value, name) => [formatINRPrecise(value), name]} contentStyle={tooltipStyle} />
                <Bar dataKey="total_revenue" name="Revenue" fill="#059669" radius={[4, 4, 0, 0]} />
                <Bar dataKey="total_expenses" name="Expenses" fill="#dc2626" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>
      </section>

      <section className="card" aria-label="Department financial performance table">
        <div className="card-header">
          <h2 className="card-title">Department Financial Performance</h2>
          <span style={{ color: "#64748b", fontSize: "0.85rem" }}>{departments.length} departments</span>
        </div>
        {departments.length ? (
          <div className="table-container">
            <table className="data-table department-performance-table">
              <thead>
                <tr>
                  <th>Department</th>
                  <th>Allocated Budget (₹)</th>
                  <th>Actual Expenditure (₹)</th>
                  <th>Budget Utilization</th>
                  <th>Revenue (₹)</th>
                  <th>Expenses (₹)</th>
                  <th>Revenue / Expense</th>
                  <th>Outstanding Fees (₹)</th>
                  <th>Scholarship Expenditure (₹)</th>
                  <th>Financial Risk</th>
                </tr>
              </thead>
              <tbody>
                {departments.map((item) => (
                  <tr key={item.department_id}>
                    <td style={{ fontWeight: 700 }}>{item.department_id}</td>
                    <td>{formatINR(item.allocated_budget)}</td>
                    <td>{formatINR(item.actual_expenditure)}</td>
                    <td>{Number(item.budget_utilization).toFixed(1)}%</td>
                    <td>{formatINR(item.total_revenue)}</td>
                    <td>{formatINR(item.total_expenses)}</td>
                    <td>{item.total_expenses > 0 ? (item.total_revenue / item.total_expenses).toFixed(2) : "—"}</td>
                    <td>{formatINR(item.outstanding_fees)}</td>
                    <td>{formatINR(item.scholarship_disbursed)}</td>
                    <td style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <RiskBadge level={item.risk_level} />
                      <span>{Number(item.risk_score).toFixed(0)}/100</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="finance-empty">No department financial records available for the selected filters.</div>
        )}
        <p className="department-performance-note" style={{ marginTop: "0.75rem" }}>
          Financial risk is the existing rule-based score. Revenue-to-expense is total revenue ÷ total expenses and is not shown when reported expenses are zero.
        </p>
      </section>
    </>
  );
}

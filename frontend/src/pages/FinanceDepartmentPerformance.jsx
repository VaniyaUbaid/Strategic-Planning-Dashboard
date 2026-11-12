import React, { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowDownRight, ArrowUpRight, Building2, PieChart, Wallet } from "lucide-react";
import { Navigate } from "react-router-dom";
import ErrorAlert from "../components/common/ErrorAlert";
import DepartmentPerformanceHeader from "../components/common/DepartmentPerformanceHeader";
import DepartmentPerformanceKpiCard from "../components/common/DepartmentPerformanceKpiCard";
import LoadingSpinner from "../components/common/LoadingSpinner";
import FinanceDepartmentAnalytics from "../components/finance/FinanceDepartmentAnalytics";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import { formatINR } from "../utils/currency";
import "../components/common/DepartmentPerformance.css";

export default function FinanceDepartmentPerformance() {
  const { role, department } = useAuth();
  const isHod = role === "HOD";
  const assignedDepartment = isHod ? (department || "CSE") : "";
  const [filterOptions, setFilterOptions] = useState({ departments: [], academic_years: [] });
  const [filters, setFilters] = useState({ department_id: assignedDepartment, academic_year: "" });
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterError, setFilterError] = useState(null);

  useEffect(() => {
    if (isHod) {
      setFilters((current) => (current.department_id === assignedDepartment ? current : { ...current, department_id: assignedDepartment }));
    }
  }, [assignedDepartment, isHod]);

  const fetchFilterOptions = useCallback(() => {
    const controller = new AbortController();
    api.getFinanceFilters({ signal: controller.signal })
      .then((options) => {
        setFilterOptions(options);
        setFilterError(null);
      })
      .catch((err) => {
        if (controller.signal.aborted || err.name === "AbortError") return;
        setFilterError(err.message || "Unable to load financial filters.");
      });
    return controller;
  }, []);

  useEffect(() => {
    const controller = fetchFilterOptions();
    return () => {
      controller.abort();
    };
  }, [fetchFilterOptions]);

  const fetchDepartmentData = useCallback(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    api.getFinanceDepartments({
      department_id: isHod ? assignedDepartment : filters.department_id,
      academic_year: filters.academic_year,
    }, { signal: controller.signal })
      .then((result) => {
        if (controller.signal.aborted) return;
        setDepartments(result.departments || []);
        setError(null);
      })
      .catch((err) => {
        if (controller.signal.aborted || err.name === "AbortError") return;
        setError(err.message || "Failed to load finance department performance.");
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return controller;
  }, [assignedDepartment, filters, isHod]);

  useEffect(() => {
    const controller = fetchDepartmentData();
    return () => {
      controller.abort();
    };
  }, [fetchDepartmentData]);

  const totals = useMemo(() => departments.reduce((summary, item) => ({
    allocated: summary.allocated + Number(item.allocated_budget || 0),
    expenditure: summary.expenditure + Number(item.actual_expenditure || 0),
    revenue: summary.revenue + Number(item.total_revenue || 0),
    expenses: summary.expenses + Number(item.total_expenses || 0),
    outstanding: summary.outstanding + Number(item.outstanding_fees || 0),
    scholarships: summary.scholarships + Number(item.scholarship_disbursed || 0),
  }), {
    allocated: 0,
    expenditure: 0,
    revenue: 0,
    expenses: 0,
    outstanding: 0,
    scholarships: 0,
  }), [departments]);

  if (role !== "ADMINISTRATOR" && !isHod) return <Navigate to="/finance" replace />;

  const budgetUtilization = totals.allocated > 0
    ? `${((totals.expenditure / totals.allocated) * 100).toFixed(1)}%`
    : "—";
  const revenueExpenseRatio = totals.expenses > 0
    ? (totals.revenue / totals.expenses).toFixed(2)
    : "—";

  const handleFilterChange = (key, value) => {
    setFilters((current) => ({ ...current, [key]: value }));
    setLoading(true);
    setError(null);
  };

  const retry = () => {
    setLoading(true);
    setError(null);
    fetchDepartmentData()
      .then((result) => {
        setDepartments(result.departments || []);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load finance department performance.");
        setLoading(false);
      });
  };

  return (
    <div className="department-performance-page">
      <DepartmentPerformanceHeader
        title="Finance Department Performance"
        description="Review department budgets, expenditure, revenue, fee balances, scholarship disbursement, and rule-based financial risk."
        backTo="/finance"
        backLabel="Back to Finance Dashboard"
      />

      <section className="card finance-filter-card" aria-label="Finance department performance filters">
        <div className="finance-filter-title"><Building2 size={18} color="#2563eb" /> Financial data filters</div>
        {filterError ? (
          <ErrorAlert message={filterError} onRetry={fetchFilterOptions} />
        ) : (
          <div className="finance-filter-grid">
            <label className="finance-filter-field">
              Department
              {isHod ? (
                <div className="department-scope-lock">{assignedDepartment} (Assigned Department)</div>
              ) : (
                <select
                  value={filters.department_id}
                  onChange={(event) => handleFilterChange("department_id", event.target.value)}
                >
                  <option value="">All Departments</option>
                  {filterOptions.departments.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              )}
            </label>
            <label className="finance-filter-field">
              Academic Year
              <select
                value={filters.academic_year}
                onChange={(event) => handleFilterChange("academic_year", event.target.value)}
              >
                <option value="">All Academic Years</option>
                {filterOptions.academic_years.map((year) => <option key={year} value={year}>{year}</option>)}
              </select>
            </label>
          </div>
        )}
      </section>

      {loading ? (
        <LoadingSpinner message="Loading finance department performance..." />
      ) : error ? (
        <ErrorAlert message={error} onRetry={retry} />
      ) : departments.length === 0 ? (
        <div className="card finance-empty" role="status">
          No financial department records are available for the selected filters.
        </div>
      ) : (
        <>
          <section className="department-performance-kpis" aria-label="Department financial indicators">
            <DepartmentPerformanceKpiCard label="DEPARTMENTS" value={departments.length.toLocaleString()} icon={Building2} />
            <DepartmentPerformanceKpiCard label="ALLOCATED BUDGET" value={formatINR(totals.allocated)} icon={Wallet} />
            <DepartmentPerformanceKpiCard label="ACTUAL EXPENDITURE" value={formatINR(totals.expenditure)} icon={ArrowDownRight} tone="amber" />
            <DepartmentPerformanceKpiCard label="BUDGET UTILIZATION" value={budgetUtilization} icon={PieChart} />
            <DepartmentPerformanceKpiCard label="REVENUE GENERATED" value={formatINR(totals.revenue)} icon={ArrowUpRight} tone="teal" />
            <DepartmentPerformanceKpiCard label="OUTSTANDING FEES" value={formatINR(totals.outstanding)} icon={Wallet} tone="red" />
            <DepartmentPerformanceKpiCard label="SCHOLARSHIP EXPENDITURE" value={formatINR(totals.scholarships)} icon={ArrowDownRight} tone="teal" />
            <DepartmentPerformanceKpiCard label="REVENUE / EXPENSE" value={revenueExpenseRatio} icon={PieChart} />
          </section>
          <p className="department-performance-note">
            Financial totals aggregate the returned department rows. Overall utilization is total expenditure ÷ total allocation, not an unweighted mean of department percentages.
          </p>
          <FinanceDepartmentAnalytics departments={departments} />
        </>
      )}
    </div>
  );
}

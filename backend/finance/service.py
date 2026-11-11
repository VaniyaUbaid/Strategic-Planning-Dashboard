import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from backend.common.supabase_client import (
    SupabaseConfigurationError,
    get_supabase_client,
)
from backend.finance.schemas import (
    CategoryAmount,
    DepartmentBudgetItem,
    DepartmentFinanceItem,
    FinanceBudgetResponse,
    FinanceDepartmentListResponse,
    FinanceFeeResponse,
    FinanceFilterOptionsResponse,
    FinanceOverviewResponse,
    FinanceRevenueExpenseResponse,
    FinanceRiskResponse,
    FinanceScholarshipResponse,
    FinanceStatusResponse,
    FinanceTransactionsResponse,
    PaymentStatusCount,
    RevenueExpenseItem,
    ScholarshipStatusCount,
    ScholarshipTypeCount,
    SemesterFeeItem,
    UtilizationCategoryCount,
)

logger = logging.getLogger(__name__)

_SAFE_ERROR_CODE = re.compile(r"^[A-Za-z0-9_.-]{1,32}$")


class FinanceService:
    # Rule-Based Risk Constants & Thresholds
    UTILIZATION_HIGH_THRESHOLD = 106.0  # %
    UTILIZATION_MODERATE_THRESHOLD = 100.0  # %
    UTILIZATION_UNDER_THRESHOLD = 85.0  # %

    RATIO_DEFICIT_THRESHOLD = 0.95
    RATIO_TIGHT_THRESHOLD = 1.05
    RATIO_MODERATE_THRESHOLD = 1.15

    OUTSTANDING_FEE_HIGH_THRESHOLD = 14.5  # %
    OUTSTANDING_FEE_ELEVATED_THRESHOLD = 13.0  # %

    RISK_HIGH_SCORE = 55.0
    RISK_MEDIUM_SCORE = 25.0

    def _query_table(
        self,
        table_name: str,
        department_id: Optional[str] = None,
        academic_year: Optional[str] = None,
        semester: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query Supabase table with filters and pagination."""
        try:
            client = get_supabase_client()

            all_rows: List[Dict[str, Any]] = []
            page_size = 1000
            start = 0

            while True:
                query = client.table(table_name).select("*")

                if department_id and str(department_id).strip():
                    clean_dept = str(department_id).strip()
                    if clean_dept.upper() not in ["ALL", "NONE", "", "NULL"]:
                        query = query.ilike("department_id", clean_dept)

                if academic_year and str(academic_year).strip():
                    clean_ay = str(academic_year).strip()
                    if clean_ay.upper() not in ["ALL", "NONE", "", "NULL"]:
                        query = query.ilike("academic_year", clean_ay)

                if semester is not None:
                    try:
                        query = query.eq("semester", int(semester))
                    except (ValueError, TypeError):
                        pass

                res = (
                    query
                    .range(start, start + page_size - 1)
                    .execute()
                )

                rows = res.data if res and res.data else []

                all_rows.extend(rows)

                if len(rows) < page_size:
                    break

                start += page_size

            return all_rows

        except Exception as exc:
            self._raise_database_unavailable(table_name, exc)

    @staticmethod
    def _raise_database_unavailable(table_name: str, exc: Exception) -> None:
        """Log safe error metadata and surface failed reads separately from empty tables."""
        error_type = type(exc).__name__
        error_code = getattr(exc, "code", None)
        if not isinstance(error_code, str) or not _SAFE_ERROR_CODE.fullmatch(error_code):
            error_code = "unavailable"

        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)
        if not isinstance(status_code, int):
            candidate_status = getattr(exc, "status_code", None)
            status_code = candidate_status if isinstance(candidate_status, int) else None

        if isinstance(exc, SupabaseConfigurationError):
            failure_kind = "configuration failure"
            diagnostic = "Finance database configuration is incomplete"
        elif error_type in {
            "ConnectError",
            "ConnectTimeout",
            "ReadTimeout",
            "TimeoutException",
            "NetworkError",
        } or isinstance(exc, (ConnectionError, TimeoutError, OSError)):
            failure_kind = "connection failure"
            diagnostic = "Supabase connection is unavailable"
        elif status_code in (401, 403) or error_code in {
            "42501",
            "PGRST301",
            "PGRST302",
        }:
            failure_kind = "read access denied"
            diagnostic = "Supabase denied read access"
        elif error_code in {"42P01", "42703", "PGRST204", "PGRST205"}:
            failure_kind = "schema/query failure"
            diagnostic = "Supabase rejected the table or column query"
        else:
            failure_kind = "database read failure"
            diagnostic = "Supabase read failed"

        logger.error(
            "[FinanceService] %s (table=%s, error_type=%s, code=%s, status=%s)",
            failure_kind,
            table_name,
            error_type,
            error_code,
            status_code if status_code is not None else "unknown",
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{diagnostic} for Finance table '{table_name}'.",
        ) from None

    def get_status(self) -> FinanceStatusResponse:
        """Check Finance readiness with a lightweight read from a required table."""
        try:
            get_supabase_client().table("finance_budgets").select("department_id").limit(1).execute()
        except Exception as exc:
            self._raise_database_unavailable("finance_budgets", exc)
        return FinanceStatusResponse(module="finance", status="ready")

    def get_filter_options(self) -> FinanceFilterOptionsResponse:
        budget_rows = self._query_table("finance_budgets")
        fee_rows = self._query_table("finance_fees")

        depts = sorted(list({str(r["department_id"]) for r in budget_rows if r.get("department_id")}))
        years = sorted(list({str(r["academic_year"]) for r in budget_rows if r.get("academic_year")}))
        semesters = sorted(list({int(r["semester"]) for r in fee_rows if r.get("semester") is not None}))

        return FinanceFilterOptionsResponse(
            departments=depts,
            academic_years=years,
            semesters=semesters,
        )

    def calculate_risk(
        self,
        utilization: float,
        rev_exp_ratio: float,
        outstanding_fee_pct: float,
    ) -> tuple[str, float, list[str]]:
        """Transparent rule-based financial risk calculation."""
        score = 0.0
        factors = []

        # 1. Budget Utilization factor
        if utilization > self.UTILIZATION_HIGH_THRESHOLD:
            score += 35.0
            factors.append(f"High budget overrun ({utilization:.1f}% utilization)")
        elif utilization > self.UTILIZATION_MODERATE_THRESHOLD:
            score += 20.0
            factors.append(f"Moderate budget overrun ({utilization:.1f}% utilization)")
        elif utilization < self.UTILIZATION_UNDER_THRESHOLD:
            score += 10.0
            factors.append(f"Budget underutilization ({utilization:.1f}% utilization)")

        # 2. Revenue-to-Expense Ratio factor
        if rev_exp_ratio < self.RATIO_DEFICIT_THRESHOLD:
            score += 40.0
            factors.append(f"Severe deficit ratio ({rev_exp_ratio:.2f})")
        elif rev_exp_ratio < self.RATIO_TIGHT_THRESHOLD:
            score += 25.0
            factors.append(f"Tight operating margin ({rev_exp_ratio:.2f})")
        elif rev_exp_ratio < self.RATIO_MODERATE_THRESHOLD:
            score += 10.0
            factors.append(f"Moderate operating margin ({rev_exp_ratio:.2f})")

        # 3. Outstanding Fee Percentage factor
        if outstanding_fee_pct > self.OUTSTANDING_FEE_HIGH_THRESHOLD:
            score += 25.0
            factors.append(f"High outstanding fees ({outstanding_fee_pct:.1f}% pending)")
        elif outstanding_fee_pct > self.OUTSTANDING_FEE_ELEVATED_THRESHOLD:
            score += 15.0
            factors.append(f"Elevated outstanding fees ({outstanding_fee_pct:.1f}% pending)")

        score = min(100.0, max(0.0, score))

        if score >= self.RISK_HIGH_SCORE:
            level = "HIGH"
        elif score >= self.RISK_MEDIUM_SCORE:
            level = "MEDIUM"
        else:
            level = "LOW"

        if not factors:
            factors.append("Healthy financial indicators across all metrics")

        return level, round(score, 1), factors

    def get_overview(
        self,
        department_id: Optional[str] = None,
        academic_year: Optional[str] = None,
        semester: Optional[int] = None,
    ) -> FinanceOverviewResponse:
        dept_sum_rows = self._query_table("finance_department_summaries", department_id, academic_year)
        budget_rows = self._query_table("finance_budgets", department_id, academic_year)
        fee_rows = self._query_table("finance_fees", department_id, academic_year, semester)
        schol_rows = self._query_table("finance_scholarships", department_id, academic_year)

        total_revenue = sum(float(r.get("revenue") or 0.0) for r in dept_sum_rows)
        total_expenses = sum(float(r.get("expense") or 0.0) for r in dept_sum_rows)
        net_surplus_deficit = round(total_revenue - total_expenses, 2)

        total_budget = sum(float(r.get("allocated_budget") or 0.0) for r in budget_rows)
        actual_expenditure = sum(float(r.get("actual_expenditure") or 0.0) for r in budget_rows)
        budget_utilization = (
            round((actual_expenditure / total_budget) * 100, 2)
            if total_budget > 0
            else 0.0
        )
        budget_variance = round(actual_expenditure - total_budget, 2)

        total_fees_collected = sum(float(r.get("fee_paid") or 0.0) for r in fee_rows)
        outstanding_fees = sum(float(r.get("fee_pending") or 0.0) for r in fee_rows)
        total_fee_due = sum(float(r.get("fee_due") or 0.0) for r in fee_rows)
        fee_collection_rate = (
            round((total_fees_collected / total_fee_due) * 100, 2)
            if total_fee_due > 0
            else 0.0
        )

        total_scholarship_amount = sum(float(r.get("amount_awarded") or 0.0) for r in schol_rows)
        scholarships_disbursed = sum(float(r.get("amount_disbursed") or 0.0) for r in schol_rows)

        return FinanceOverviewResponse(
            total_revenue=round(total_revenue, 2),
            total_expenses=round(total_expenses, 2),
            net_surplus_deficit=net_surplus_deficit,
            total_budget=round(total_budget, 2),
            actual_expenditure=round(actual_expenditure, 2),
            budget_utilization=budget_utilization,
            budget_variance=budget_variance,
            total_fees_collected=round(total_fees_collected, 2),
            outstanding_fees=round(outstanding_fees, 2),
            fee_collection_rate=fee_collection_rate,
            total_scholarship_amount=round(total_scholarship_amount, 2),
            scholarships_disbursed=round(scholarships_disbursed, 2),
        )

    def get_departments(
        self,
        department_id: Optional[str] = None,
        academic_year: Optional[str] = None,
    ) -> FinanceDepartmentListResponse:
        dept_sum_rows = self._query_table(
            "finance_department_summaries", department_id, academic_year
        )
        budget_rows = self._query_table("finance_budgets", department_id, academic_year)
        fee_rows = self._query_table("finance_fees", department_id, academic_year)
        schol_rows = self._query_table("finance_scholarships", department_id, academic_year)
        rer_rows = self._query_table(
            "finance_revenue_expense_ratios", department_id, academic_year
        )

        departments = sorted(list({str(r["department_id"]).upper() for r in budget_rows if r.get("department_id")}))
        if not departments:
            # Fallback to checking department summaries if budget table has no entries
            departments = sorted(list({str(r["department_id"]).upper() for r in dept_sum_rows if r.get("department_id")}))

        items: List[DepartmentFinanceItem] = []

        for d_id in departments:
            d_sum = [r for r in dept_sum_rows if str(r.get("department_id")).upper() == d_id]
            d_bud = [r for r in budget_rows if str(r.get("department_id")).upper() == d_id]
            d_fee = [r for r in fee_rows if str(r.get("department_id")).upper() == d_id]
            d_sch = [r for r in schol_rows if str(r.get("department_id")).upper() == d_id]
            d_rer = [r for r in rer_rows if str(r.get("department_id")).upper() == d_id]

            rev = sum(float(r.get("revenue") or 0.0) for r in d_sum)
            exp = sum(float(r.get("expense") or 0.0) for r in d_sum)
            surplus = round(rev - exp, 2)
            scores = [float(r["financial_health_score"]) for r in d_sum if r.get("financial_health_score") is not None]
            health_score = round(sum(scores) / len(scores), 2) if scores else 1.0

            alloc = sum(float(r.get("allocated_budget") or 0.0) for r in d_bud)
            act_exp = sum(float(r.get("actual_expenditure") or 0.0) for r in d_bud)
            util = round((act_exp / alloc) * 100, 2) if alloc > 0 else 0.0
            variance = round(act_exp - alloc, 2)

            f_paid = sum(float(r.get("fee_paid") or 0.0) for r in d_fee)
            f_pend = sum(float(r.get("fee_pending") or 0.0) for r in d_fee)
            f_due = sum(float(r.get("fee_due") or 0.0) for r in d_fee)
            f_rate = round((f_paid / f_due) * 100, 2) if f_due > 0 else 0.0
            out_pct = round((f_pend / f_due) * 100, 2) if f_due > 0 else 0.0

            sch_disb = sum(float(r.get("amount_disbursed") or 0.0) for r in d_sch)

            ratios = [float(r["revenue_expense_ratio"]) for r in d_rer if r.get("revenue_expense_ratio") is not None]
            rev_exp_ratio = (
                round(sum(ratios) / len(ratios), 2)
                if ratios
                else (round(rev / exp, 2) if exp > 0 else 1.0)
            )

            risk_level, risk_score, _ = self.calculate_risk(util, rev_exp_ratio, out_pct)

            items.append(
                DepartmentFinanceItem(
                    department_id=d_id,
                    academic_year=academic_year,
                    total_revenue=round(rev, 2),
                    total_expenses=round(exp, 2),
                    net_surplus_deficit=surplus,
                    allocated_budget=round(alloc, 2),
                    actual_expenditure=round(act_exp, 2),
                    budget_utilization=util,
                    budget_variance=variance,
                    fee_collection=round(f_paid, 2),
                    outstanding_fees=round(f_pend, 2),
                    fee_collection_rate=f_rate,
                    scholarship_disbursed=round(sch_disb, 2),
                    financial_health_score=health_score,
                    revenue_expense_ratio=rev_exp_ratio,
                    risk_level=risk_level,
                    risk_score=risk_score,
                )
            )

        return FinanceDepartmentListResponse(departments=items)

    def get_transactions(
        self,
        department_id: Optional[str] = None,
        academic_year: Optional[str] = None,
    ) -> FinanceTransactionsResponse:
        tx_rows = self._query_table("finance_transactions", department_id, academic_year)
        if not tx_rows:
            return FinanceTransactionsResponse(
                total_transactions=0,
                total_revenue=0.0,
                total_expense=0.0,
                revenue_by_category=[],
                expense_by_category=[],
            )

        total_tx = len(tx_rows)
        rev_rows = [r for r in tx_rows if r.get("is_revenue") == 1 or r.get("transaction_type") == "revenue"]
        exp_rows = [r for r in tx_rows if r.get("is_expense") == 1 or r.get("transaction_type") == "expense"]

        tot_rev = sum(float(r.get("amount") or 0.0) for r in rev_rows)
        tot_exp = sum(float(r.get("amount") or 0.0) for r in exp_rows)

        rev_cat_map: Dict[str, float] = {}
        for r in rev_rows:
            cat = r.get("revenue_category")
            if cat is not None and str(cat).strip():
                cat_str = str(cat).strip()
                rev_cat_map[cat_str] = rev_cat_map.get(cat_str, 0.0) + float(r.get("amount") or 0.0)

        rev_cats = [CategoryAmount(category=k, amount=round(v, 2)) for k, v in rev_cat_map.items()]

        exp_cat_map: Dict[str, float] = {}
        for r in exp_rows:
            cat = r.get("expense_category")
            if cat is not None and str(cat).strip():
                cat_str = str(cat).strip()
                exp_cat_map[cat_str] = exp_cat_map.get(cat_str, 0.0) + float(r.get("amount") or 0.0)

        exp_cats = [CategoryAmount(category=k, amount=round(v, 2)) for k, v in exp_cat_map.items()]

        return FinanceTransactionsResponse(
            total_transactions=total_tx,
            total_revenue=round(tot_rev, 2),
            total_expense=round(tot_exp, 2),
            revenue_by_category=sorted(rev_cats, key=lambda x: x.amount, reverse=True),
            expense_by_category=sorted(exp_cats, key=lambda x: x.amount, reverse=True),
        )

    def get_budget(
        self,
        department_id: Optional[str] = None,
        academic_year: Optional[str] = None,
    ) -> FinanceBudgetResponse:
        budget_rows = self._query_table("finance_budgets", department_id, academic_year)
        if not budget_rows:
            return FinanceBudgetResponse(
                total_allocated_budget=0.0,
                total_actual_expenditure=0.0,
                overall_budget_utilization=0.0,
                total_budget_variance=0.0,
                overrun_count=0,
                utilization_categories=[],
                department_budgets=[],
            )

        tot_alloc = sum(float(r.get("allocated_budget") or 0.0) for r in budget_rows)
        tot_actual = sum(float(r.get("actual_expenditure") or 0.0) for r in budget_rows)
        overall_util = round((tot_actual / tot_alloc) * 100, 2) if tot_alloc > 0 else 0.0
        tot_var = round(tot_actual - tot_alloc, 2)

        overrun_count = sum(1 for r in budget_rows if (r.get("budget_overrun") or 0) > 0 or (r.get("calculated_overrun") or 0) > 0)

        cat_counts_map: Dict[str, int] = {}
        for r in budget_rows:
            cat = r.get("utilization_category")
            if cat is not None and str(cat).strip():
                cat_str = str(cat).strip()
                cat_counts_map[cat_str] = cat_counts_map.get(cat_str, 0) + 1

        cat_counts = [UtilizationCategoryCount(category=k, count=v) for k, v in cat_counts_map.items()]

        dept_items = []
        for r in budget_rows:
            dept_items.append(
                DepartmentBudgetItem(
                    department_id=str(r.get("department_id")),
                    academic_year=str(r.get("academic_year")),
                    allocated_budget=round(float(r.get("allocated_budget") or 0.0), 2),
                    actual_expenditure=round(float(r.get("actual_expenditure") or 0.0), 2),
                    budget_utilization=round(float(r.get("budget_utilization") or 0.0), 2),
                    budget_variance=round(float(r.get("budget_variance") or 0.0), 2),
                    budget_overrun=round(float(r.get("budget_overrun") or 0.0), 2),
                    utilization_category=str(r.get("utilization_category") or "Normal"),
                )
            )

        return FinanceBudgetResponse(
            total_allocated_budget=round(tot_alloc, 2),
            total_actual_expenditure=round(tot_actual, 2),
            overall_budget_utilization=overall_util,
            total_budget_variance=tot_var,
            overrun_count=overrun_count,
            utilization_categories=cat_counts,
            department_budgets=dept_items,
        )

    def get_fees(
        self,
        department_id: Optional[str] = None,
        academic_year: Optional[str] = None,
        semester: Optional[int] = None,
    ) -> FinanceFeeResponse:
        fee_rows = self._query_table("finance_fees", department_id, academic_year, semester)
        if not fee_rows:
            return FinanceFeeResponse(
                total_fee_due=0.0,
                total_fee_paid=0.0,
                total_fee_pending=0.0,
                collection_rate=0.0,
                outstanding_rate=0.0,
                payment_status_distribution=[],
                semester_breakdown=[],
            )

        tot_due = sum(float(r.get("fee_due") or 0.0) for r in fee_rows)
        tot_paid = sum(float(r.get("fee_paid") or 0.0) for r in fee_rows)
        tot_pend = sum(float(r.get("fee_pending") or 0.0) for r in fee_rows)

        coll_rate = round((tot_paid / tot_due) * 100, 2) if tot_due > 0 else 0.0
        out_rate = round((tot_pend / tot_due) * 100, 2) if tot_due > 0 else 0.0

        status_map: Dict[str, dict] = {}
        for r in fee_rows:
            st = str(r.get("payment_status") or "Unknown")
            if st not in status_map:
                status_map[st] = {"count": 0, "amount": 0.0}
            status_map[st]["count"] += 1
            status_map[st]["amount"] += float(r.get("fee_paid") or 0.0)

        status_dist = [
            PaymentStatusCount(
                status=st,
                count=info["count"],
                amount=round(info["amount"], 2),
            )
            for st, info in status_map.items()
        ]

        sem_map: Dict[int, dict] = {}
        for r in fee_rows:
            try:
                sem = int(r.get("semester"))
            except (ValueError, TypeError):
                continue
            if sem not in sem_map:
                sem_map[sem] = {"due": 0.0, "paid": 0.0, "pending": 0.0}
            sem_map[sem]["due"] += float(r.get("fee_due") or 0.0)
            sem_map[sem]["paid"] += float(r.get("fee_paid") or 0.0)
            sem_map[sem]["pending"] += float(r.get("fee_pending") or 0.0)

        sem_breakdown = []
        for sem in sorted(sem_map.keys()):
            info = sem_map[sem]
            due = info["due"]
            paid = info["paid"]
            rate = round((paid / due) * 100, 2) if due > 0 else 0.0
            sem_breakdown.append(
                SemesterFeeItem(
                    semester=sem,
                    fee_due=round(due, 2),
                    fee_paid=round(paid, 2),
                    fee_pending=round(info["pending"], 2),
                    collection_rate=rate,
                )
            )

        return FinanceFeeResponse(
            total_fee_due=round(tot_due, 2),
            total_fee_paid=round(tot_paid, 2),
            total_fee_pending=round(tot_pend, 2),
            collection_rate=coll_rate,
            outstanding_rate=out_rate,
            payment_status_distribution=status_dist,
            semester_breakdown=sem_breakdown,
        )

    def get_scholarships(
        self,
        department_id: Optional[str] = None,
        academic_year: Optional[str] = None,
    ) -> FinanceScholarshipResponse:
        schol_rows = self._query_table("finance_scholarships", department_id, academic_year)
        if not schol_rows:
            return FinanceScholarshipResponse(
                total_awarded=0.0,
                total_disbursed=0.0,
                disbursement_rate=0.0,
                total_recipients=0,
                by_type=[],
                by_status=[],
            )

        tot_awarded = sum(float(r.get("amount_awarded") or 0.0) for r in schol_rows)
        tot_disbursed = sum(float(r.get("amount_disbursed") or 0.0) for r in schol_rows)
        disb_rate = round((tot_disbursed / tot_awarded) * 100, 2) if tot_awarded > 0 else 0.0

        recipients = len({str(r["student_id"]) for r in schol_rows if r.get("student_id")}) or len(schol_rows)

        type_map: Dict[str, dict] = {}
        for r in schol_rows:
            stype = str(r.get("scholarship_type") or "General")
            if stype not in type_map:
                type_map[stype] = {"count": 0, "awarded": 0.0, "disbursed": 0.0}
            type_map[stype]["count"] += 1
            type_map[stype]["awarded"] += float(r.get("amount_awarded") or 0.0)
            type_map[stype]["disbursed"] += float(r.get("amount_disbursed") or 0.0)

        by_type = [
            ScholarshipTypeCount(
                type=stype,
                count=info["count"],
                amount_awarded=round(info["awarded"], 2),
                amount_disbursed=round(info["disbursed"], 2),
            )
            for stype, info in type_map.items()
        ]

        status_map: Dict[str, dict] = {}
        for r in schol_rows:
            stat = str(r.get("scholarship_status") or "Disbursed")
            if stat not in status_map:
                status_map[stat] = {"count": 0, "disbursed": 0.0}
            status_map[stat]["count"] += 1
            status_map[stat]["disbursed"] += float(r.get("amount_disbursed") or 0.0)

        by_status = [
            ScholarshipStatusCount(
                status=stat,
                count=info["count"],
                amount=round(info["disbursed"], 2),
            )
            for stat, info in status_map.items()
        ]

        return FinanceScholarshipResponse(
            total_awarded=round(tot_awarded, 2),
            total_disbursed=round(tot_disbursed, 2),
            disbursement_rate=disb_rate,
            total_recipients=recipients,
            by_type=by_type,
            by_status=by_status,
        )

    def get_revenue_expense(
        self,
        department_id: Optional[str] = None,
        academic_year: Optional[str] = None,
    ) -> FinanceRevenueExpenseResponse:
        dept_sum_rows = self._query_table("finance_department_summaries", department_id, academic_year)
        if not dept_sum_rows:
            return FinanceRevenueExpenseResponse(overall_ratio=0.0, by_department=[], by_year=[])

        tot_rev = sum(float(r.get("revenue") or 0.0) for r in dept_sum_rows)
        tot_exp = sum(float(r.get("expense") or 0.0) for r in dept_sum_rows)
        overall_ratio = round(tot_rev / tot_exp, 2) if tot_exp > 0 else 0.0

        dept_map: Dict[str, dict] = {}
        for r in dept_sum_rows:
            d_id = str(r.get("department_id")).upper()
            if d_id not in dept_map:
                dept_map[d_id] = {"rev": 0.0, "exp": 0.0}
            dept_map[d_id]["rev"] += float(r.get("revenue") or 0.0)
            dept_map[d_id]["exp"] += float(r.get("expense") or 0.0)

        by_dept = []
        for d_id, info in dept_map.items():
            r = info["rev"]
            e = info["exp"]
            ratio = round(r / e, 2) if e > 0 else 0.0
            by_dept.append(
                RevenueExpenseItem(
                    academic_year=academic_year or "All Years",
                    department_id=d_id,
                    revenue=round(r, 2),
                    expense=round(e, 2),
                    ratio=ratio,
                )
            )

        yr_map: Dict[str, dict] = {}
        for r in dept_sum_rows:
            ay = str(r.get("academic_year"))
            if ay not in yr_map:
                yr_map[ay] = {"rev": 0.0, "exp": 0.0}
            yr_map[ay]["rev"] += float(r.get("revenue") or 0.0)
            yr_map[ay]["exp"] += float(r.get("expense") or 0.0)

        by_yr = []
        for ay in sorted(yr_map.keys()):
            info = yr_map[ay]
            r = info["rev"]
            e = info["exp"]
            ratio = round(r / e, 2) if e > 0 else 0.0
            by_yr.append(
                RevenueExpenseItem(
                    academic_year=ay,
                    department_id=department_id,
                    revenue=round(r, 2),
                    expense=round(e, 2),
                    ratio=ratio,
                )
            )

        return FinanceRevenueExpenseResponse(
            overall_ratio=overall_ratio,
            by_department=sorted(by_dept, key=lambda x: x.revenue, reverse=True),
            by_year=sorted(by_yr, key=lambda x: x.academic_year),
        )

    def get_risk(
        self,
        department_id: Optional[str] = None,
        academic_year: Optional[str] = None,
    ) -> FinanceRiskResponse:
        budget_rows = self._query_table("finance_budgets", department_id, academic_year)
        fee_rows = self._query_table("finance_fees", department_id, academic_year)
        dept_sum_rows = self._query_table("finance_department_summaries", department_id, academic_year)

        alloc = sum(float(r.get("allocated_budget") or 0.0) for r in budget_rows)
        act_exp = sum(float(r.get("actual_expenditure") or 0.0) for r in budget_rows)
        utilization = round((act_exp / alloc) * 100, 2) if alloc > 0 else 0.0
        budget_var_pct = round(((act_exp - alloc) / alloc) * 100, 2) if alloc > 0 else 0.0

        rev = sum(float(r.get("revenue") or 0.0) for r in dept_sum_rows)
        exp = sum(float(r.get("expense") or 0.0) for r in dept_sum_rows)
        rev_exp_ratio = round(rev / exp, 2) if exp > 0 else 1.0

        f_due = sum(float(r.get("fee_due") or 0.0) for r in fee_rows)
        f_paid = sum(float(r.get("fee_paid") or 0.0) for r in fee_rows)
        f_pend = sum(float(r.get("fee_pending") or 0.0) for r in fee_rows)
        coll_rate = round((f_paid / f_due) * 100, 2) if f_due > 0 else 0.0
        out_pct = round((f_pend / f_due) * 100, 2) if f_due > 0 else 0.0

        risk_level, risk_score, factors = self.calculate_risk(utilization, rev_exp_ratio, out_pct)

        metrics = {
            "budget_utilization": utilization,
            "budget_variance_percentage": budget_var_pct,
            "revenue_expense_ratio": rev_exp_ratio,
            "fee_collection_rate": coll_rate,
            "outstanding_fee_percentage": out_pct,
            "allocated_budget": alloc,
            "actual_expenditure": act_exp,
            "total_revenue": rev,
            "total_expenses": exp,
            "outstanding_fees": f_pend,
        }

        return FinanceRiskResponse(
            department_id=department_id,
            academic_year=academic_year,
            risk_level=risk_level,
            risk_score=risk_score,
            contributing_factors=factors,
            metrics=metrics,
        )


finance_service = FinanceService()

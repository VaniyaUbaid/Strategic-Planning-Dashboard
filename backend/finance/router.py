from typing import Optional
from fastapi import APIRouter, Header, Query

from backend.common.auth import get_user_context
from backend.finance.schemas import (
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
)
from backend.finance.service import finance_service

router = APIRouter(prefix="/api/finance", tags=["Finance"])


@router.get("/status", response_model=FinanceStatusResponse)
def get_finance_status():
    """Return status of the Finance module."""
    return finance_service.get_status()


@router.get("/filters", response_model=FinanceFilterOptionsResponse)
def get_finance_filters(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return available filter options (departments, academic years, semesters)."""
    user_ctx = get_user_context(x_user_role, x_user_department, role, user_department)
    filters = finance_service.get_filter_options()

    if user_ctx.is_hod and user_ctx.department_id:
        return FinanceFilterOptionsResponse(
            departments=[user_ctx.department_id],
            academic_years=filters.academic_years,
            semesters=filters.semesters,
        )

    return filters


@router.get("/overview", response_model=FinanceOverviewResponse)
def get_finance_overview(
    department_id: Optional[str] = Query(None, alias="department_id"),
    academic_year: Optional[str] = Query(None, alias="academic_year"),
    semester: Optional[int] = Query(None, alias="semester"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return financial overview metrics with RBAC enforcement."""
    user_ctx = get_user_context(x_user_role, x_user_department, role, user_department)
    eff_dept = user_ctx.enforce_department(department_id)

    return finance_service.get_overview(
        department_id=eff_dept,
        academic_year=academic_year,
        semester=semester,
    )


@router.get("/departments", response_model=FinanceDepartmentListResponse)
def get_finance_departments(
    department_id: Optional[str] = Query(None, alias="department_id"),
    academic_year: Optional[str] = Query(None, alias="academic_year"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return department-wise financial summary and risk metrics with RBAC scope."""
    user_ctx = get_user_context(x_user_role, x_user_department, role, user_department)
    eff_dept = user_ctx.enforce_department(department_id)
    res = finance_service.get_departments(
        department_id=eff_dept,
        academic_year=academic_year,
    )

    return res


@router.get("/transactions", response_model=FinanceTransactionsResponse)
def get_finance_transactions(
    department_id: Optional[str] = Query(None, alias="department_id"),
    academic_year: Optional[str] = Query(None, alias="academic_year"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return financial transaction breakdown with RBAC enforcement."""
    user_ctx = get_user_context(x_user_role, x_user_department, role, user_department)
    eff_dept = user_ctx.enforce_department(department_id)

    return finance_service.get_transactions(
        department_id=eff_dept,
        academic_year=academic_year,
    )


@router.get("/budget", response_model=FinanceBudgetResponse)
def get_finance_budget(
    department_id: Optional[str] = Query(None, alias="department_id"),
    academic_year: Optional[str] = Query(None, alias="academic_year"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return budget allocation, expenditure, and utilization analysis with RBAC enforcement."""
    user_ctx = get_user_context(x_user_role, x_user_department, role, user_department)
    eff_dept = user_ctx.enforce_department(department_id)

    return finance_service.get_budget(
        department_id=eff_dept,
        academic_year=academic_year,
    )


@router.get("/fees", response_model=FinanceFeeResponse)
def get_finance_fees(
    department_id: Optional[str] = Query(None, alias="department_id"),
    academic_year: Optional[str] = Query(None, alias="academic_year"),
    semester: Optional[int] = Query(None, alias="semester"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return fee collection and pending fee metrics with RBAC enforcement."""
    user_ctx = get_user_context(x_user_role, x_user_department, role, user_department)
    eff_dept = user_ctx.enforce_department(department_id)

    return finance_service.get_fees(
        department_id=eff_dept,
        academic_year=academic_year,
        semester=semester,
    )


@router.get("/scholarships", response_model=FinanceScholarshipResponse)
def get_finance_scholarships(
    department_id: Optional[str] = Query(None, alias="department_id"),
    academic_year: Optional[str] = Query(None, alias="academic_year"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return scholarship distribution and disbursement analysis with RBAC enforcement."""
    user_ctx = get_user_context(x_user_role, x_user_department, role, user_department)
    eff_dept = user_ctx.enforce_department(department_id)

    return finance_service.get_scholarships(
        department_id=eff_dept,
        academic_year=academic_year,
    )


@router.get("/revenue-expense", response_model=FinanceRevenueExpenseResponse)
def get_finance_revenue_expense(
    department_id: Optional[str] = Query(None, alias="department_id"),
    academic_year: Optional[str] = Query(None, alias="academic_year"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return revenue vs expense comparison with RBAC enforcement."""
    user_ctx = get_user_context(x_user_role, x_user_department, role, user_department)
    eff_dept = user_ctx.enforce_department(department_id)

    return finance_service.get_revenue_expense(
        department_id=eff_dept,
        academic_year=academic_year,
    )


@router.get("/risk", response_model=FinanceRiskResponse)
def get_finance_risk(
    department_id: Optional[str] = Query(None, alias="department_id"),
    academic_year: Optional[str] = Query(None, alias="academic_year"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return transparent rule-based financial risk assessment with RBAC enforcement."""
    user_ctx = get_user_context(x_user_role, x_user_department, role, user_department)
    eff_dept = user_ctx.enforce_department(department_id)

    return finance_service.get_risk(
        department_id=eff_dept,
        academic_year=academic_year,
    )

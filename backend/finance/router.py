from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.common.auth import UserContext, get_user_context
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

router = APIRouter(
    prefix="/api/finance",
    tags=["Finance"],
    dependencies=[Depends(get_user_context)],
)


@router.get("/status", response_model=FinanceStatusResponse)
def get_finance_status():
    return finance_service.get_status()


@router.get("/filters", response_model=FinanceFilterOptionsResponse)
def get_finance_filters(
    user_ctx: UserContext = Depends(get_user_context),
):
    filters = finance_service.get_filter_options()
    if user_ctx.is_hod:
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
    user_ctx: UserContext = Depends(get_user_context),
):
    return finance_service.get_overview(
        department_id=user_ctx.enforce_department(department_id),
        academic_year=academic_year,
        semester=semester,
    )


@router.get("/departments", response_model=FinanceDepartmentListResponse)
def get_finance_departments(
    department_id: Optional[str] = Query(None, alias="department_id"),
    academic_year: Optional[str] = Query(None, alias="academic_year"),
    user_ctx: UserContext = Depends(get_user_context),
):
    return finance_service.get_departments(
        department_id=user_ctx.enforce_department(department_id),
        academic_year=academic_year,
    )


@router.get("/transactions", response_model=FinanceTransactionsResponse)
def get_finance_transactions(
    department_id: Optional[str] = Query(None, alias="department_id"),
    academic_year: Optional[str] = Query(None, alias="academic_year"),
    user_ctx: UserContext = Depends(get_user_context),
):
    return finance_service.get_transactions(
        department_id=user_ctx.enforce_department(department_id),
        academic_year=academic_year,
    )


@router.get("/budget", response_model=FinanceBudgetResponse)
def get_finance_budget(
    department_id: Optional[str] = Query(None, alias="department_id"),
    academic_year: Optional[str] = Query(None, alias="academic_year"),
    user_ctx: UserContext = Depends(get_user_context),
):
    return finance_service.get_budget(
        department_id=user_ctx.enforce_department(department_id),
        academic_year=academic_year,
    )


@router.get("/fees", response_model=FinanceFeeResponse)
def get_finance_fees(
    department_id: Optional[str] = Query(None, alias="department_id"),
    academic_year: Optional[str] = Query(None, alias="academic_year"),
    semester: Optional[int] = Query(None, alias="semester"),
    user_ctx: UserContext = Depends(get_user_context),
):
    return finance_service.get_fees(
        department_id=user_ctx.enforce_department(department_id),
        academic_year=academic_year,
        semester=semester,
    )


@router.get("/scholarships", response_model=FinanceScholarshipResponse)
def get_finance_scholarships(
    department_id: Optional[str] = Query(None, alias="department_id"),
    academic_year: Optional[str] = Query(None, alias="academic_year"),
    user_ctx: UserContext = Depends(get_user_context),
):
    return finance_service.get_scholarships(
        department_id=user_ctx.enforce_department(department_id),
        academic_year=academic_year,
    )


@router.get("/revenue-expense", response_model=FinanceRevenueExpenseResponse)
def get_finance_revenue_expense(
    department_id: Optional[str] = Query(None, alias="department_id"),
    academic_year: Optional[str] = Query(None, alias="academic_year"),
    user_ctx: UserContext = Depends(get_user_context),
):
    return finance_service.get_revenue_expense(
        department_id=user_ctx.enforce_department(department_id),
        academic_year=academic_year,
    )


@router.get("/risk", response_model=FinanceRiskResponse)
def get_finance_risk(
    department_id: Optional[str] = Query(None, alias="department_id"),
    academic_year: Optional[str] = Query(None, alias="academic_year"),
    user_ctx: UserContext = Depends(get_user_context),
):
    return finance_service.get_risk(
        department_id=user_ctx.enforce_department(department_id),
        academic_year=academic_year,
    )

from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, Query

from backend.common.auth import UserContext, get_user_context
from backend.decision.schemas import (
    DecisionOverviewResponse,
    DecisionQueryRequest,
    DecisionQueryResponse,
    DecisionStatusResponse,
    FindingItem,
)
from backend.decision.service import decision_service

router = APIRouter(
    prefix="/api/decision",
    tags=["Decision Assistant"],
    dependencies=[Depends(get_user_context)],
)


def parse_user_context(ctx: UserContext) -> Tuple[str, Optional[str]]:
    department = ctx.enforce_department(None) if ctx.is_hod else None
    return ctx.role, department


@router.get("/status", response_model=DecisionStatusResponse)
def get_decision_status():
    return decision_service.get_status()


@router.get("/overview", response_model=DecisionOverviewResponse)
def get_decision_overview(
    department: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    user_ctx: UserContext = Depends(get_user_context),
):
    role, user_department = parse_user_context(user_ctx)
    target_department = user_department if user_ctx.is_hod else department
    return decision_service.get_decision_overview(
        role=role,
        user_dept=user_department,
        department=target_department,
        academic_year=academic_year,
        semester=semester,
        access_token=user_ctx.access_token,
    )


@router.get("/insights", response_model=List[FindingItem])
def get_decision_insights(
    department: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    user_ctx: UserContext = Depends(get_user_context),
):
    role, user_department = parse_user_context(user_ctx)
    overview = decision_service.get_decision_overview(
        role=role,
        user_dept=user_department,
        department=user_department if user_ctx.is_hod else department,
        academic_year=academic_year,
        access_token=user_ctx.access_token,
    )
    return overview.key_findings


@router.get("/recommendations", response_model=List[Dict[str, object]])
def get_decision_recommendations(
    department: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    user_ctx: UserContext = Depends(get_user_context),
):
    del department, academic_year, user_ctx
    return []


@router.get("/query", response_model=DecisionQueryResponse)
def query_decision_assistant_get(
    q: str = Query(..., description="Institutional decision query text"),
    department: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    user_ctx: UserContext = Depends(get_user_context),
):
    role, user_department = parse_user_context(user_ctx)
    return decision_service.execute_natural_query(
        query=q,
        role=role,
        user_dept=user_department,
        department=user_department if user_ctx.is_hod else department,
        academic_year=academic_year,
        access_token=user_ctx.access_token,
    )


@router.post("/query", response_model=DecisionQueryResponse)
def query_decision_assistant_post(
    req: DecisionQueryRequest,
    user_ctx: UserContext = Depends(get_user_context),
):
    role, user_department = parse_user_context(user_ctx)
    return decision_service.execute_natural_query(
        query=req.query,
        role=role,
        user_dept=user_department,
        department=user_department if user_ctx.is_hod else req.department,
        academic_year=req.academic_year,
        access_token=user_ctx.access_token,
    )

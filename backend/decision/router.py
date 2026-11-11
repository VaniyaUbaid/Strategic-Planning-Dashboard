from typing import List, Optional, Tuple
from fastapi import APIRouter, Header, HTTPException, Query, status

from backend.common.auth import get_user_context
from backend.decision.schemas import (
    DecisionOverviewResponse,
    DecisionQueryRequest,
    DecisionQueryResponse,
    DecisionStatusResponse,
    FindingItem,
    RecommendedAction,
)
from backend.decision.service import decision_service

router = APIRouter(prefix="/api/decision", tags=["Decision Assistant"])


def parse_user_context(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
) -> Tuple[str, Optional[str]]:
    ctx = get_user_context(x_user_role, x_user_department, role, user_department)
    eff_role = ctx.role
    eff_dept = ctx.enforce_department(None) if ctx.is_hod else ctx.department_id
    return eff_role, eff_dept


@router.get("/status", response_model=DecisionStatusResponse)
def get_decision_status():
    """Return status of the Decision Assistant module."""
    return decision_service.get_status()


@router.get("/overview", response_model=DecisionOverviewResponse)
def get_decision_overview(
    department: Optional[str] = Query(None),
    academic_year: Optional[int] = Query(None),
    semester: Optional[int] = Query(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return synthesized decision overview across Student, Finance, and Research modules with RBAC enforcement."""
    eff_role, eff_dept = parse_user_context(x_user_role, x_user_department, role, user_department)
    target_dept = eff_dept if eff_role == "HOD" else department

    return decision_service.get_decision_overview(
        role=eff_role,
        user_dept=eff_dept,
        department=target_dept,
        academic_year=academic_year,
        semester=semester,
    )


@router.get("/insights", response_model=List[FindingItem])
def get_decision_insights(
    department: Optional[str] = Query(None),
    academic_year: Optional[int] = Query(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return cross-module findings for permitted department scope."""
    eff_role, eff_dept = parse_user_context(x_user_role, x_user_department, role, user_department)
    target_dept = eff_dept if eff_role == "HOD" else department
    res = decision_service.get_decision_overview(
        role=eff_role,
        user_dept=eff_dept,
        department=target_dept,
        academic_year=academic_year,
    )
    return res.key_findings


@router.get("/recommendations", response_model=List[RecommendedAction])
def get_decision_recommendations(
    department: Optional[str] = Query(None),
    academic_year: Optional[int] = Query(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return evidence-backed policy recommendations."""
    eff_role, eff_dept = parse_user_context(x_user_role, x_user_department, role, user_department)
    target_dept = eff_dept if eff_role == "HOD" else department
    res = decision_service.get_decision_overview(
        role=eff_role,
        user_dept=eff_dept,
        department=target_dept,
        academic_year=academic_year,
    )
    return res.recommendations


@router.get("/query", response_model=DecisionQueryResponse)
def query_decision_assistant_get(
    q: str = Query(..., description="Institutional decision query text"),
    department: Optional[str] = Query(None),
    academic_year: Optional[int] = Query(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Execute natural query intent matching against cross-module data (GET)."""
    eff_role, eff_dept = parse_user_context(x_user_role, x_user_department, role, user_department)
    target_dept = eff_dept if eff_role == "HOD" else department
    return decision_service.execute_natural_query(
        query=q,
        role=eff_role,
        user_dept=eff_dept,
        department=target_dept,
        academic_year=academic_year,
    )


@router.post("/query", response_model=DecisionQueryResponse)
def query_decision_assistant_post(
    req: DecisionQueryRequest,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Execute natural query intent matching against cross-module data (POST)."""
    eff_role, eff_dept = parse_user_context(x_user_role, x_user_department, role, user_department)
    target_dept = eff_dept if eff_role == "HOD" else req.department
    return decision_service.execute_natural_query(
        query=req.query,
        role=eff_role,
        user_dept=eff_dept,
        department=target_dept,
        academic_year=req.academic_year,
    )

from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Query

from backend.common.auth import get_user_context
from backend.research.schemas import (
    ResearchDepartmentResponse,
    ResearchFilterOptionsResponse,
    ResearchOverviewResponse,
    ResearchParticipationResponse,
    ResearchProgramResponse,
    ResearchPublicationResponse,
    ResearchStatusResponse,
)
from backend.research.service import ResearchDataError, research_service

router = APIRouter(prefix="/api/research", tags=["Research"])


@router.get("/status", response_model=ResearchStatusResponse)
def get_research_status():
    """Return status of the Research module."""
    return research_service.get_status()


def _run_research_query(method, department, program, admission_year):
    try:
        return method(department=department, program=program, admission_year=admission_year)
    except ResearchDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None


@router.get("/overview", response_model=ResearchOverviewResponse)
def get_research_overview(
    department: Optional[str] = Query(None),
    program: Optional[str] = Query(None),
    admission_year: Optional[int] = Query(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    user_ctx = get_user_context(x_user_role, x_user_department, role, user_department)
    eff_dept = user_ctx.enforce_department(department)
    return _run_research_query(research_service.get_overview, eff_dept, program, admission_year)


@router.get("/departments", response_model=ResearchDepartmentResponse)
def get_research_departments(
    department: Optional[str] = Query(None),
    program: Optional[str] = Query(None),
    admission_year: Optional[int] = Query(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    user_ctx = get_user_context(x_user_role, x_user_department, role, user_department)
    eff_dept = user_ctx.enforce_department(department)
    res = _run_research_query(research_service.get_departments, eff_dept, program, admission_year)

    if user_ctx.is_hod and user_ctx.department_id:
        filtered = [
            d for d in res.departments
            if d.department.strip().upper() == user_ctx.department_id.strip().upper()
        ]
        return ResearchDepartmentResponse(departments=filtered)

    return res


@router.get("/programs", response_model=ResearchProgramResponse)
def get_research_programs(
    department: Optional[str] = Query(None),
    program: Optional[str] = Query(None),
    admission_year: Optional[int] = Query(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    user_ctx = get_user_context(x_user_role, x_user_department, role, user_department)
    eff_dept = user_ctx.enforce_department(department)
    return _run_research_query(research_service.get_programs, eff_dept, program, admission_year)


@router.get("/publications", response_model=ResearchPublicationResponse)
def get_research_publications(
    department: Optional[str] = Query(None),
    program: Optional[str] = Query(None),
    admission_year: Optional[int] = Query(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    user_ctx = get_user_context(x_user_role, x_user_department, role, user_department)
    eff_dept = user_ctx.enforce_department(department)
    return _run_research_query(research_service.get_publications, eff_dept, program, admission_year)


@router.get("/participation", response_model=ResearchParticipationResponse)
def get_research_participation(
    department: Optional[str] = Query(None),
    program: Optional[str] = Query(None),
    admission_year: Optional[int] = Query(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    user_ctx = get_user_context(x_user_role, x_user_department, role, user_department)
    eff_dept = user_ctx.enforce_department(department)
    return _run_research_query(research_service.get_participation, eff_dept, program, admission_year)


@router.get("/filters", response_model=ResearchFilterOptionsResponse)
def get_research_filters(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    user_ctx = get_user_context(x_user_role, x_user_department, role, user_department)
    try:
        filters = research_service.get_filter_options()
        if user_ctx.is_hod and user_ctx.department_id:
            return ResearchFilterOptionsResponse(
                departments=[user_ctx.department_id],
                programs=filters.programs,
                admission_years=filters.admission_years,
            )
        return filters
    except ResearchDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None

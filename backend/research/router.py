from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.common.auth import UserContext, get_user_context
from backend.research.schemas import (
    FacultyResearchAnalyticsResponse,
    ResearchDepartmentResponse,
    ResearchFilterOptionsResponse,
    ResearchOverviewResponse,
    ResearchParticipationResponse,
    ResearchProgramResponse,
    ResearchPublicationResponse,
    ResearchStatusResponse,
)
from backend.research.service import (
    ResearchAccessError,
    ResearchDataError,
    research_service,
)

router = APIRouter(
    prefix="/api/research",
    tags=["Research"],
    dependencies=[Depends(get_user_context)],
)


@router.get("/status", response_model=ResearchStatusResponse)
def get_research_status():
    return research_service.get_status()


def _run_research_query(method, department, program, admission_year):
    try:
        return method(department=department, program=program, admission_year=admission_year)
    except ResearchAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    except ResearchDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None


def _effective_research_department(user_ctx: UserContext, requested_department: Optional[str]):
    department = user_ctx.enforce_department(requested_department)
    if isinstance(department, str) and department.strip().upper() == "BT":
        return "Biotech"
    return department


@router.get("/overview", response_model=ResearchOverviewResponse)
def get_research_overview(
    department: Optional[str] = Query(None),
    program: Optional[str] = Query(None),
    admission_year: Optional[int] = Query(None),
    user_ctx: UserContext = Depends(get_user_context),
):
    effective_department = _effective_research_department(user_ctx, department)
    return _run_research_query(
        research_service.get_overview, effective_department, program, admission_year
    )


@router.get("/departments", response_model=ResearchDepartmentResponse)
def get_research_departments(
    department: Optional[str] = Query(None),
    program: Optional[str] = Query(None),
    admission_year: Optional[int] = Query(None),
    user_ctx: UserContext = Depends(get_user_context),
):
    effective_department = _effective_research_department(user_ctx, department)
    response = _run_research_query(
        research_service.get_departments, effective_department, program, admission_year
    )
    if user_ctx.is_hod:
        department_name = _effective_research_department(user_ctx, None)
        return ResearchDepartmentResponse(departments=[
            item for item in response.departments
            if item.department.strip().casefold() == department_name.casefold()
        ])
    return response


@router.get("/programs", response_model=ResearchProgramResponse)
def get_research_programs(
    department: Optional[str] = Query(None),
    program: Optional[str] = Query(None),
    admission_year: Optional[int] = Query(None),
    user_ctx: UserContext = Depends(get_user_context),
):
    return _run_research_query(
        research_service.get_programs,
        _effective_research_department(user_ctx, department),
        program,
        admission_year,
    )


@router.get("/publications", response_model=ResearchPublicationResponse)
def get_research_publications(
    department: Optional[str] = Query(None),
    program: Optional[str] = Query(None),
    admission_year: Optional[int] = Query(None),
    user_ctx: UserContext = Depends(get_user_context),
):
    return _run_research_query(
        research_service.get_publications,
        _effective_research_department(user_ctx, department),
        program,
        admission_year,
    )


@router.get("/participation", response_model=ResearchParticipationResponse)
def get_research_participation(
    department: Optional[str] = Query(None),
    program: Optional[str] = Query(None),
    admission_year: Optional[int] = Query(None),
    user_ctx: UserContext = Depends(get_user_context),
):
    return _run_research_query(
        research_service.get_participation,
        _effective_research_department(user_ctx, department),
        program,
        admission_year,
    )


@router.get("/filters", response_model=ResearchFilterOptionsResponse)
def get_research_filters(
    user_ctx: UserContext = Depends(get_user_context),
):
    try:
        filters = research_service.get_filter_options()
        if user_ctx.is_hod:
            return ResearchFilterOptionsResponse(
                departments=[_effective_research_department(user_ctx, None)],
                programs=filters.programs,
                admission_years=filters.admission_years,
            )
        return filters
    except ResearchAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    except ResearchDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None


@router.get("/faculty/analytics", response_model=FacultyResearchAnalyticsResponse)
def get_faculty_research_analytics(
    department: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    user_ctx: UserContext = Depends(get_user_context),
):
    try:
        return research_service.get_faculty_analytics(
            department=_effective_research_department(user_ctx, department),
            academic_year=academic_year,
            access_token=user_ctx.access_token,
        )
    except ResearchAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    except ResearchDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None

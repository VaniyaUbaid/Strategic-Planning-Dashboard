from typing import List, Optional, Tuple
from fastapi import APIRouter, Header, HTTPException, Query, status

from backend.common.auth import get_user_context
from backend.student.schemas import (
    DepartmentOption,
    DetailedOverviewResponse,
    FilterOptionsResponse,
    HodOverviewResponse,
    PaginatedDetailedStudentListResponse,
    PaginatedStudentListResponse,
    SimpleFilterOptionsResponse,
    StudentHistoryResponse,
    StudentModelInsightsResponse,
    StudentProfileResponse,
    StudentRiskResponse,
)
from backend.student.service import student_service

router = APIRouter(tags=["Students"])


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


def check_student_department_access(
    student_id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    ctx = get_user_context(x_user_role, x_user_department, role, user_department)
    if ctx.is_hod:
        if not ctx.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: HOD user has no assigned department.",
            )
        profile = student_service.get_student_profile(student_id=student_id)
        if profile.department_id and profile.department_id.strip().upper() != ctx.department_id.strip().upper():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Student '{student_id}' belongs to department '{profile.department_id}', which is outside your assigned department ('{ctx.department_id}').",
            )


# ====================================================
# ACCESS CONTROL & DYNAMIC FILTER OPTIONS API
# ====================================================

@router.get("/api/students/filters", response_model=SimpleFilterOptionsResponse, tags=["Access & Filtering"])
@router.get("/api/filters", response_model=SimpleFilterOptionsResponse, tags=["Access & Filtering"])
def get_students_filters(
    department: Optional[str] = Query(None),
    academic_year: Optional[int] = Query(None),
):
    """Return available filter options metadata derived dynamically from the dataset."""
    return student_service.get_simple_filters(department=department, academic_year=academic_year)


@router.get("/api/students/analytics/model-insights", response_model=StudentModelInsightsResponse, tags=["Model Analytics"])
def get_students_model_insights():
    """Return Logistic Regression model coefficients, performance metrics, and threshold reasoning."""
    return student_service.get_model_insights()

@router.get("/api/students/model-insights",response_model=StudentModelInsightsResponse)
def get_students_model_insights_alias():
    """Return Logistic Regression model insights."""
    return student_service.get_model_insights()


@router.get("/api/access/departments", response_model=List[DepartmentOption], tags=["Access & Filtering"])
def get_accessible_departments(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return departments permitted for current user role."""
    eff_role, eff_dept = parse_user_context(x_user_role, x_user_department, role, user_department)
    return student_service.get_available_departments(role=eff_role, user_dept=eff_dept)


@router.get("/api/access/years", response_model=List[int], tags=["Access & Filtering"])
def get_accessible_years(
    department: Optional[str] = Query(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Dynamically derive available academic years based on department & role context."""
    eff_role, eff_dept = parse_user_context(x_user_role, x_user_department, role, user_department)
    return student_service.get_available_years(role=eff_role, user_dept=eff_dept, department=department)


@router.get("/api/access/semesters", response_model=List[int], tags=["Access & Filtering"])
def get_accessible_semesters(
    department: Optional[str] = Query(None),
    academic_year: Optional[int] = Query(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Dynamically derive available semesters based on department, academic year & role context."""
    eff_role, eff_dept = parse_user_context(x_user_role, x_user_department, role, user_department)
    return student_service.get_available_semesters(
        role=eff_role, user_dept=eff_dept, department=department, academic_year=academic_year
    )


# ====================================================
# ADMINISTRATOR & OVERVIEW API ENDPOINTS
# ====================================================

@router.get("/api/overview", response_model=DetailedOverviewResponse, tags=["Admin & Overview"])
@router.get("/api/admin/overview", response_model=DetailedOverviewResponse, tags=["Admin & Overview"])
def get_overview(
    department: Optional[str] = Query(None),
    academic_year: Optional[int] = Query(None),
    semester: Optional[int] = Query(None),
    risk_level: Optional[str] = Query(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return institutional-level overview metrics & visualization datasets."""
    eff_role, eff_dept = parse_user_context(x_user_role, x_user_department, role, user_department)
    target_dept = eff_dept if eff_role == "HOD" else department

    return student_service.get_admin_overview(
        role=eff_role,
        user_dept=eff_dept,
        department=target_dept,
        academic_year=academic_year,
        semester=semester,
        risk_level=risk_level,
    )


@router.get("/api/admin/departments", response_model=List[DepartmentOption], tags=["Admin"])
def get_admin_departments():
    """Return all institutional departments."""
    return student_service.get_available_departments(role="ADMINISTRATOR")


@router.get("/api/admin/years", response_model=List[int], tags=["Admin"])
def get_admin_years(department: Optional[str] = Query(None)):
    """Return academic years containing data for selected department (or all)."""
    return student_service.get_available_years(role="ADMINISTRATOR", department=department)


@router.get("/api/admin/semesters", response_model=List[int], tags=["Admin"])
def get_admin_semesters(
    department: Optional[str] = Query(None),
    academic_year: Optional[int] = Query(None),
):
    """Return semesters available for selected department and academic year."""
    return student_service.get_available_semesters(
        role="ADMINISTRATOR", department=department, academic_year=academic_year
    )


@router.get("/api/admin/analytics", response_model=DetailedOverviewResponse, tags=["Admin"])
def get_admin_analytics(
    department: Optional[str] = Query(None),
    academic_year: Optional[int] = Query(None),
    semester: Optional[int] = Query(None),
    risk_level: Optional[str] = Query(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return institutional department, semester, and academic year analytics breakdowns."""
    eff_role, eff_dept = parse_user_context(x_user_role, x_user_department, role, user_department)
    target_dept = eff_dept if eff_role == "HOD" else department
    return student_service.get_admin_overview(
        role=eff_role,
        user_dept=eff_dept,
        department=target_dept,
        academic_year=academic_year,
        semester=semester,
        risk_level=risk_level,
    )


@router.get("/api/admin/students", response_model=PaginatedDetailedStudentListResponse, tags=["Admin"])
def get_admin_students(
    department: Optional[str] = Query(None),
    academic_year: Optional[int] = Query(None),
    semester: Optional[int] = Query(None),
    risk_level: Optional[str] = Query(None),
    student_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return filtered student records with full performance & risk attributes."""
    eff_role, eff_dept = parse_user_context(x_user_role, x_user_department, role, user_department)
    target_dept = eff_dept if eff_role == "HOD" else department
    search_term = search or student_id
    return student_service.get_filtered_students(
        role=eff_role,
        user_dept=eff_dept,
        department=target_dept,
        academic_year=academic_year,
        semester=semester,
        risk_level=risk_level,
        search=search_term,
        page=page,
        page_size=page_size,
    )


# ====================================================
# HOD (HEAD OF DEPARTMENT) API ENDPOINTS
# ====================================================

@router.get("/api/hod/overview", response_model=HodOverviewResponse, tags=["HOD"])
def get_hod_overview(
    academic_year: Optional[int] = Query(None),
    semester: Optional[int] = Query(None),
    risk_level: Optional[str] = Query(None),
    x_user_role: Optional[str] = Header("HOD", alias="X-User-Role"),
    x_user_department: Optional[str] = Header("CSE", alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return department-level overview for assigned HOD department."""
    eff_role, eff_dept = parse_user_context(x_user_role, x_user_department, role, user_department)
    return student_service.get_hod_overview(
        role=eff_role,
        user_dept=eff_dept,
        academic_year=academic_year,
        semester=semester,
        risk_level=risk_level,
    )


@router.get("/api/hod/students", response_model=PaginatedDetailedStudentListResponse, tags=["HOD"])
def get_hod_students(
    department: Optional[str] = Query(None),
    academic_year: Optional[int] = Query(None),
    semester: Optional[int] = Query(None),
    risk_level: Optional[str] = Query(None),
    student_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    x_user_role: Optional[str] = Header("HOD", alias="X-User-Role"),
    x_user_department: Optional[str] = Header("CSE", alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return HOD student directory strictly enforced to assigned department."""
    eff_role, eff_dept = parse_user_context(x_user_role, x_user_department, role, user_department)
    search_term = search or student_id
    return student_service.get_filtered_students(
        role="HOD",
        user_dept=eff_dept,
        department=department,
        academic_year=academic_year,
        semester=semester,
        risk_level=risk_level,
        search=search_term,
        page=page,
        page_size=page_size,
    )


# ====================================================
# PROFESSOR / TEACHER API ENDPOINTS
# ====================================================

@router.get("/api/teacher/students", response_model=PaginatedDetailedStudentListResponse, tags=["Teacher"])
def get_teacher_students(
    department: Optional[str] = Query(None),
    academic_year: Optional[int] = Query(None),
    semester: Optional[int] = Query(None),
    risk_level: Optional[str] = Query(None),
    student_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    x_user_role: Optional[str] = Header("PROFESSOR", alias="X-User-Role"),
    x_user_department: Optional[str] = Header("CSE", alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return teacher student view restricted to assigned teaching department scope."""
    eff_role, eff_dept = parse_user_context(x_user_role, x_user_department, role, user_department)
    search_term = search or student_id
    return student_service.get_filtered_students(
        role="PROFESSOR",
        user_dept=eff_dept,
        department=eff_dept,
        academic_year=academic_year,
        semester=semester,
        risk_level=risk_level,
        search=search_term,
        page=page,
        page_size=page_size,
    )


# ====================================================
# PRESERVED CORE STUDENT API ENDPOINTS WITH RBAC
# ====================================================

@router.get("/api/students", tags=["Students"])
def get_students(
    department: Optional[str] = Query(None),
    academic_year: Optional[int] = Query(None),
    semester: Optional[int] = Query(None),
    risk_level: Optional[str] = Query(None),
    student_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return filtered student list strictly enforcing role & department authorization."""
    eff_role, eff_dept = parse_user_context(x_user_role, x_user_department, role, user_department)
    search_term = search or student_id
    target_dept = eff_dept if eff_role == "HOD" else department

    if not any([department, academic_year, semester, risk_level, search_term]) and eff_role == "ADMINISTRATOR":
        return student_service.get_paginated_students(page=page, page_size=page_size)

    return student_service.get_filtered_students(
        role=eff_role,
        user_dept=eff_dept,
        department=target_dept,
        academic_year=academic_year,
        semester=semester,
        risk_level=risk_level,
        search=search_term,
        page=page,
        page_size=page_size,
    )


@router.get("/api/students/{student_id}", response_model=StudentProfileResponse, tags=["Students"])
def get_student_profile(
    student_id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return basic profile demographic & program information for a given student with RBAC checks."""
    check_student_department_access(student_id, x_user_role, x_user_department, role, user_department)
    return student_service.get_student_profile(student_id=student_id)


@router.get("/api/students/{student_id}/risk", response_model=StudentRiskResponse, tags=["Students"])
def get_student_risk(
    student_id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return ML dropout probability and risk factors with RBAC checks."""
    check_student_department_access(student_id, x_user_role, x_user_department, role, user_department)
    return student_service.get_student_risk(student_id=student_id)


@router.get("/api/students/{student_id}/history", response_model=StudentHistoryResponse, tags=["Students"])
def get_student_history(
    student_id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department"),
    role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
):
    """Return historical semester-by-semester performance with RBAC checks."""
    check_student_department_access(student_id, x_user_role, x_user_department, role, user_department)
    return student_service.get_student_history(student_id=student_id)

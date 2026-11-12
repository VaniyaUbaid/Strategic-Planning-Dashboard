from typing import Any, List, Optional
from pydantic import BaseModel, Field


# User Role Context
class UserContext(BaseModel):
    role: str = Field(..., description="Role: ADMINISTRATOR, HOD, PROFESSOR")
    department: Optional[str] = Field(None, description="Assigned department for HOD/PROFESSOR")


class DepartmentOption(BaseModel):
    id: str = Field(..., description="Department short code (e.g., CSE)")
    name: str = Field(..., description="Full department name (e.g., Computer Science & Engineering)")


class FilterOptionsResponse(BaseModel):
    departments: List[DepartmentOption]
    academic_years: List[int]
    semesters: List[int]


class SimpleFilterOptionsResponse(BaseModel):
    departments: List[str]
    academic_years: List[int]
    semesters: List[int]
    programs: List[str] = Field(default_factory=list)
    risk_levels: List[str] = ["LOW", "MEDIUM", "HIGH"]


class FeatureFactor(BaseModel):
    feature: str = Field(..., description="Name of the feature")
    value: Any = Field(..., description="Student's raw feature value")
    contribution: float = Field(..., description="Logistic Regression log-odds contribution")
    direction: str = Field(..., description="'increases_risk' or 'reduces_risk'")


class StudentRiskResponse(BaseModel):
    student_id: str
    semester: int
    dropout_probability: float
    retention_probability: float
    risk_level: str = Field(..., description="'LOW' (<0.40), 'MEDIUM' (0.40-0.59), 'HIGH' (>=0.60)")
    risk_factors: List[FeatureFactor]
    protective_factors: List[FeatureFactor]


class StudentProfileResponse(BaseModel):
    student_id: str
    program: Optional[str] = None
    specialization: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    semester: int
    academic_year: int
    gender: Optional[str] = None
    admission_year: int
    hostel_status: int
    scholarship_status: int


class SemesterHistoryItem(BaseModel):
    semester: int
    academic_year: int
    attendance_percentage: float
    semester_gpa: float
    cumulative_gpa: float
    backlog_count: int
    courses_failed: int
    courses_passed: int
    internal_marks_percentage: float
    assignments_completed_pct: float
    fee_pending_amount: float
    historical_dropout_label: int = Field(
        ...,
        description="Historical outcome label at transition (0=retained, 1=dropped out). Distinguish from live prediction."
    )


class StudentHistoryResponse(BaseModel):
    student_id: str
    history: List[SemesterHistoryItem]


class StudentSummaryItem(BaseModel):
    student_id: str
    program: Optional[str] = None
    department_id: Optional[str] = None
    latest_semester: int
    latest_academic_year: int


class PaginatedStudentListResponse(BaseModel):
    total_students: int
    page: int
    page_size: int
    total_pages: int
    students: List[StudentSummaryItem]


# New Detailed Student Item & List Response
class StudentDetailedListItem(BaseModel):
    student_id: str
    program: Optional[str] = None
    department_id: str
    department_name: str
    semester: int
    academic_year: int
    gpa: float
    attendance_percentage: float
    backlog_count: int
    fee_pending_amount: float
    fee_payment_status: str
    risk_level: str
    dropout_probability: float


class PaginatedDetailedStudentListResponse(BaseModel):
    total_students: int
    page: int
    page_size: int
    total_pages: int
    students: List[StudentDetailedListItem]


# Analytics Item Models
class RiskDistribution(BaseModel):
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    high_pct: float = 0.0
    medium_pct: float = 0.0
    low_pct: float = 0.0


class OverviewRiskDistribution(BaseModel):
    low: int = 0
    medium: int = 0
    high: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    high_pct: float = 0.0
    medium_pct: float = 0.0
    low_pct: float = 0.0


class DepartmentAnalyticsItem(BaseModel):
    department_id: str
    department_name: str
    total_students: int
    avg_gpa: float
    avg_attendance: float
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    students_with_backlogs: int
    students_fee_pending: int
    total_fee_pending: float


class SemesterAnalyticsItem(BaseModel):
    semester: int
    total_students: int
    avg_gpa: float
    avg_attendance: float
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int


class AcademicYearAnalyticsItem(BaseModel):
    academic_year: int
    total_students: int
    avg_gpa: float
    avg_attendance: float
    high_risk_count: int


class DetailedOverviewResponse(BaseModel):
    total_students: int
    risk_distribution: OverviewRiskDistribution
    average_gpa: float
    average_attendance: float
    average_dropout_probability: float
    model_status: str = "active"

    # Extended chart attributes for dashboard visualizations
    user_role: Optional[str] = "ADMINISTRATOR"
    department_filter: Optional[str] = None
    academic_year_filter: Optional[int] = None
    semester_filter: Optional[int] = None
    high_risk_count: Optional[int] = 0
    medium_risk_count: Optional[int] = 0
    low_risk_count: Optional[int] = 0
    students_with_backlogs: Optional[int] = 0
    students_fee_pending: Optional[int] = 0
    total_fee_pending_amount: Optional[float] = 0.0
    department_chart: Optional[List[DepartmentAnalyticsItem]] = []
    semester_chart: Optional[List[SemesterAnalyticsItem]] = []
    academic_year_chart: Optional[List[AcademicYearAnalyticsItem]] = []


InstitutionalOverviewResponse = DetailedOverviewResponse



class HodOverviewResponse(BaseModel):
    user_role: str
    department_id: str
    department_name: str
    academic_year_filter: Optional[int] = None
    semester_filter: Optional[int] = None
    risk_level_filter: Optional[str] = None
    total_students: int
    avg_gpa: float
    avg_attendance: float
    risk_distribution: RiskDistribution
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    students_at_risk: int
    students_with_backlogs: int
    students_fee_pending: int
    total_fee_pending_amount: float
    available_years: List[int]
    available_semesters: List[int]
    semester_breakdown: List[SemesterAnalyticsItem]
    academic_year_breakdown: List[AcademicYearAnalyticsItem]


class ModelFeatureInsight(BaseModel):
    raw_feature: str
    feature_name: str
    coefficient: float
    direction: str  # "increases_risk" or "reduces_risk"


class StudentModelInsightsResponse(BaseModel):
    model_name: str = "Logistic Regression"
    accuracy: float = 0.7509
    roc_auc: float = 0.8204
    pr_auc: float = 0.3273
    precision: float = 0.2467
    recall: float = 0.6344
    f1_score: float = 0.3552
    high_risk_threshold: float = 0.60
    medium_risk_threshold: float = 0.40
    explanation: str = "Student Success risk is estimated using a Logistic Regression model based on student academic, financial, and institutional features."
    threshold_reasoning: str = "LOW (< 0.40) filters out safe students. MEDIUM (0.40 to 0.59) triggers light advising. HIGH (>= 0.60) captures urgent high-probability dropouts."
    risk_factors: List[ModelFeatureInsight] = Field(default_factory=list)
    protective_factors: List[ModelFeatureInsight] = Field(default_factory=list)

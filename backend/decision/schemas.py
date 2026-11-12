from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class DecisionStatusResponse(BaseModel):
    module: str = "decision_assistant"
    status: str = "ready"


class ScopeInfo(BaseModel):
    role: str
    department: str
    academic_year: Optional[Union[int, str]] = None
    semester: Optional[int] = None


class FindingItem(BaseModel):
    domain: str
    title: str
    description: str
    metric: str
    impact: str = "neutral"


class ActionableIssue(BaseModel):
    domain: str
    department: Optional[str] = None
    title: str
    evidence: str


class StudentEvidence(BaseModel):
    status: str
    total_students: Optional[int] = None
    high_risk_students: Optional[int] = None
    high_risk_pct: Optional[float] = None
    medium_risk_students: Optional[int] = None
    low_risk_students: Optional[int] = None
    avg_dropout_prob: Optional[float] = None
    average_gpa: Optional[float] = None
    average_attendance: Optional[float] = None
    top_risk_department: Optional[str] = None
    top_risk_factor: Optional[str] = None
    risk_factors: List[str] = Field(default_factory=list)
    department_chart: List[Dict[str, Any]] = Field(default_factory=list)


class FinanceEvidence(BaseModel):
    status: str
    total_budget: Optional[float] = None
    total_spent: Optional[float] = None
    budget_utilization_pct: Optional[float] = None
    overrun_departments_count: Optional[int] = None
    total_outstanding_fees: Optional[float] = None
    outstanding_fee_pct: Optional[float] = None
    fee_collection_rate: Optional[float] = None
    departments: List[Dict[str, Any]] = Field(default_factory=list)


class ResearchEvidence(BaseModel):
    status: str
    total_faculty: Optional[int] = None
    faculty_researchers: Optional[int] = None
    total_publications: Optional[int] = None
    average_publications_per_faculty: Optional[float] = None
    participation_rate_pct: Optional[float] = None
    total_citations: Optional[int] = None
    total_research_grants: Optional[float] = None
    is_synthetic: Optional[bool] = None
    departments: List[Dict[str, Any]] = Field(default_factory=list)
    publication_trends: List[Dict[str, Any]] = Field(default_factory=list)
    top_researchers: List[Dict[str, Any]] = Field(default_factory=list)


class DepartmentComparisonItem(BaseModel):
    department: str
    student_total: Optional[int] = None
    student_high_risk: Optional[int] = None
    student_high_risk_pct: Optional[float] = None
    finance_budget_utilization_pct: Optional[float] = None
    finance_outstanding_fees: Optional[float] = None
    finance_fee_collection_rate: Optional[float] = None
    research_total_faculty: Optional[int] = None
    research_publications: Optional[int] = None
    research_publications_per_faculty: Optional[float] = None
    research_participation_pct: Optional[float] = None


class EvidenceSummary(BaseModel):
    student: StudentEvidence
    finance: FinanceEvidence
    research: ResearchEvidence
    department_comparison: List[DepartmentComparisonItem] = Field(default_factory=list)


class DecisionOverviewResponse(BaseModel):
    scope: ScopeInfo
    summary: str
    key_findings: List[FindingItem] = Field(default_factory=list)
    actionable_issues: List[ActionableIssue] = Field(default_factory=list)
    evidence: EvidenceSummary
    # Keep the legacy properties for API clients while no longer generating static content.
    areas_of_attention: List[ActionableIssue] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)


class DecisionQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    department: Optional[str] = None
    academic_year: Optional[Union[int, str]] = None


class DecisionQueryResponse(BaseModel):
    query: str
    matched_intent: str
    summary: str
    findings: List[FindingItem] = Field(default_factory=list)
    supporting_metrics: Dict[str, Any] = Field(default_factory=dict)

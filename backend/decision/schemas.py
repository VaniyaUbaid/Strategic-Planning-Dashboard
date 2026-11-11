from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class DecisionStatusResponse(BaseModel):
    module: str = Field("decision_assistant", example="decision_assistant")
    status: str = Field("ready", example="ready")


class ScopeInfo(BaseModel):
    role: str
    department: str
    academic_year: Optional[int] = None
    semester: Optional[int] = None


class FindingItem(BaseModel):
    domain: str  # "student", "finance", "research"
    title: str
    description: str
    metric: str
    impact: str  # "positive", "negative", "neutral"


class AttentionArea(BaseModel):
    id: str
    title: str
    department: str
    severity: str  # "HIGH", "MEDIUM", "LOW"
    observation: str
    supporting_metric: str
    affected_modules: List[str]


class RecommendedAction(BaseModel):
    id: str
    title: str
    target_department: str
    priority: str  # "HIGH", "MEDIUM", "LOW"
    action: str
    rationale: str
    supporting_evidence: str


class StudentEvidence(BaseModel):
    status: str = "available"  # "available" or "unavailable"
    total_students: int = 0
    high_risk_students: int = 0
    high_risk_pct: float = 0.0
    medium_risk_students: int = 0
    low_risk_students: int = 0
    avg_dropout_prob: float = 0.0
    top_risk_department: str = "N/A"
    top_risk_factor: str = "N/A"


class FinanceEvidence(BaseModel):
    status: str = "available"
    total_budget: float = 0.0
    total_spent: float = 0.0
    budget_utilization_pct: float = 0.0
    overrun_departments_count: int = 0
    total_outstanding_fees: float = 0.0
    outstanding_fee_pct: float = 0.0


class ResearchEvidence(BaseModel):
    status: str = "available"
    total_students: int = 0
    participating_students: int = 0
    participation_rate_pct: float = 0.0
    total_publications: int = 0
    avg_publications_per_student: float = 0.0
    avg_faculty_rating: float = 0.0


class DepartmentComparisonItem(BaseModel):
    department: str
    department_name: str
    student_high_risk_pct: float = 0.0
    student_avg_risk: float = 0.0
    finance_budget_utilization: float = 0.0
    finance_outstanding_fee_pct: float = 0.0
    research_participation_pct: float = 0.0
    research_avg_publications: float = 0.0
    overall_health_score: float = 0.0
    status_label: str = "Stable"


class EvidenceSummary(BaseModel):
    student: StudentEvidence
    finance: FinanceEvidence
    research: ResearchEvidence
    department_comparison: List[DepartmentComparisonItem] = []


class DecisionOverviewResponse(BaseModel):
    scope: ScopeInfo
    summary: str
    key_findings: List[FindingItem]
    areas_of_attention: List[AttentionArea]
    recommendations: List[RecommendedAction]
    evidence: EvidenceSummary


class DecisionQueryRequest(BaseModel):
    query: str
    department: Optional[str] = None
    academic_year: Optional[int] = None


class DecisionQueryResponse(BaseModel):
    query: str
    matched_intent: str
    summary: str
    findings: List[FindingItem]
    areas_of_attention: List[AttentionArea]
    recommendations: List[RecommendedAction]
    supporting_metrics: Dict[str, Any]

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FinanceStatusResponse(BaseModel):
    module: str = Field("finance", example="finance")
    status: str = Field("ready", example="ready")


class FinanceFilterOptionsResponse(BaseModel):
    departments: List[str] = Field(default_factory=list)
    academic_years: List[str] = Field(default_factory=list)
    semesters: List[int] = Field(default_factory=list)


class FinanceOverviewResponse(BaseModel):
    total_revenue: float
    total_expenses: float
    net_surplus_deficit: float
    total_budget: float
    actual_expenditure: float
    budget_utilization: float
    budget_variance: float
    total_fees_collected: float
    outstanding_fees: float
    fee_collection_rate: float
    total_scholarship_amount: float
    scholarships_disbursed: float


class DepartmentFinanceItem(BaseModel):
    department_id: str
    academic_year: Optional[str] = None
    total_revenue: float
    total_expenses: float
    net_surplus_deficit: float
    allocated_budget: float
    actual_expenditure: float
    budget_utilization: float
    budget_variance: float
    fee_collection: float
    outstanding_fees: float
    fee_collection_rate: float
    scholarship_disbursed: float
    financial_health_score: float
    revenue_expense_ratio: float
    risk_level: str  # LOW, MEDIUM, HIGH
    risk_score: float  # 0 to 100


class FinanceDepartmentListResponse(BaseModel):
    departments: List[DepartmentFinanceItem] = Field(default_factory=list)


class CategoryAmount(BaseModel):
    category: str
    amount: float


class FinanceTransactionsResponse(BaseModel):
    total_transactions: int
    total_revenue: float
    total_expense: float
    revenue_by_category: List[CategoryAmount] = Field(default_factory=list)
    expense_by_category: List[CategoryAmount] = Field(default_factory=list)


class DepartmentBudgetItem(BaseModel):
    department_id: str
    academic_year: str
    allocated_budget: float
    actual_expenditure: float
    budget_utilization: float
    budget_variance: float
    budget_overrun: float
    utilization_category: str


class UtilizationCategoryCount(BaseModel):
    category: str
    count: int


class FinanceBudgetResponse(BaseModel):
    total_allocated_budget: float
    total_actual_expenditure: float
    overall_budget_utilization: float
    total_budget_variance: float
    overrun_count: int
    utilization_categories: List[UtilizationCategoryCount] = Field(default_factory=list)
    department_budgets: List[DepartmentBudgetItem] = Field(default_factory=list)


class PaymentStatusCount(BaseModel):
    status: str
    count: int
    amount: float


class SemesterFeeItem(BaseModel):
    semester: int
    fee_due: float
    fee_paid: float
    fee_pending: float
    collection_rate: float


class FinanceFeeResponse(BaseModel):
    total_fee_due: float
    total_fee_paid: float
    total_fee_pending: float
    collection_rate: float
    outstanding_rate: float
    payment_status_distribution: List[PaymentStatusCount] = Field(default_factory=list)
    semester_breakdown: List[SemesterFeeItem] = Field(default_factory=list)


class ScholarshipTypeCount(BaseModel):
    type: str
    count: int
    amount_awarded: float
    amount_disbursed: float


class ScholarshipStatusCount(BaseModel):
    status: str
    count: int
    amount: float


class FinanceScholarshipResponse(BaseModel):
    total_awarded: float
    total_disbursed: float
    disbursement_rate: float
    total_recipients: int
    by_type: List[ScholarshipTypeCount] = Field(default_factory=list)
    by_status: List[ScholarshipStatusCount] = Field(default_factory=list)


class RevenueExpenseItem(BaseModel):
    academic_year: str
    department_id: Optional[str] = None
    revenue: float
    expense: float
    ratio: float


class FinanceRevenueExpenseResponse(BaseModel):
    overall_ratio: float
    by_department: List[RevenueExpenseItem] = Field(default_factory=list)
    by_year: List[RevenueExpenseItem] = Field(default_factory=list)


class FinanceRiskResponse(BaseModel):
    department_id: Optional[str] = None
    academic_year: Optional[str] = None
    risk_level: str  # LOW / MEDIUM / HIGH
    risk_score: float  # 0 to 100
    contributing_factors: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


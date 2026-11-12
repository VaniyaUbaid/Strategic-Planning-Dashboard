import logging
import re
from statistics import median
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException

from backend.decision.rules import classify_query
from backend.decision.schemas import (
    ActionableIssue,
    DecisionOverviewResponse,
    DecisionQueryResponse,
    DecisionStatusResponse,
    DepartmentComparisonItem,
    EvidenceSummary,
    FinanceEvidence,
    FindingItem,
    ResearchEvidence,
    ScopeInfo,
    StudentEvidence,
)
from backend.finance.service import finance_service
from backend.research.service import research_service
from backend.student.service import student_service

logger = logging.getLogger(__name__)
_ACADEMIC_YEAR_PATTERN = re.compile(r"^(\d{4})(?:-(\d{2}|\d{4}))?$")


def _academic_year_parts(value: Optional[Union[int, str]]) -> Optional[tuple[int, int]]:
    if value is None or not str(value).strip():
        return None
    match = _ACADEMIC_YEAR_PATTERN.fullmatch(str(value).strip())
    if not match:
        raise HTTPException(status_code=422, detail="Invalid academic year filter.")

    start = int(match.group(1))
    expected_end = start + 1
    if match.group(2):
        end = int(match.group(2))
        if len(match.group(2)) == 2:
            end += (start // 100) * 100
            if end <= start:
                end += 100
        if end != expected_end:
            raise HTTPException(status_code=422, detail="Invalid academic year filter.")
    return start, expected_end


def _year_start(value: Optional[Union[int, str]]) -> Optional[int]:
    parts = _academic_year_parts(value)
    return parts[0] if parts else None


def _finance_year(value: Optional[Union[int, str]]) -> Optional[str]:
    parts = _academic_year_parts(value)
    return f"{parts[0]}-{parts[1]}" if parts else None


def _faculty_year(value: Optional[Union[int, str]]) -> Optional[str]:
    parts = _academic_year_parts(value)
    return f"{parts[0]}-{parts[1] % 100:02d}" if parts else None


def _department_code(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    code = student_service.normalize_department(value)
    return str(code or value).strip().upper()


def _dump(model: Any) -> Dict[str, Any]:
    if isinstance(model, dict):
        return model
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


def _unavailable(defaults: Dict[str, Any], error: Exception, module: str) -> Dict[str, Any]:
    logger.error(
        "Decision Assistant could not load module evidence (module=%s, error_type=%s)",
        module,
        type(error).__name__,
    )
    return {"status": "unavailable", **defaults}


class DecisionService:
    def get_status(self) -> DecisionStatusResponse:
        return DecisionStatusResponse(module="decision_assistant", status="ready")

    def _get_student_evidence(
        self,
        role: str,
        user_dept: Optional[str],
        department: Optional[str],
        academic_year: Optional[Union[int, str]],
        semester: Optional[int],
    ) -> Dict[str, Any]:
        try:
            response = student_service.get_admin_overview(
                role=role,
                user_dept=user_dept,
                department=department,
                academic_year=_year_start(academic_year),
                semester=semester,
            )
            total = int(response.total_students or 0)
            high = int(response.high_risk_count or 0)
            medium = int(response.medium_risk_count or 0)
            low = int(response.low_risk_count or 0)
            departments = [_dump(row) for row in (response.department_chart or [])]
            ranked = sorted(
                (row for row in departments if row.get("total_students", 0) > 0),
                key=lambda row: row["high_risk_count"] / row["total_students"],
                reverse=True,
            )

            risk_factors = []
            try:
                insights = student_service.get_model_insights()
                if insights and insights.risk_factors:
                    risk_factors = [
                        factor.feature_name for factor in insights.risk_factors
                    ]
            except Exception as error:
                logger.warning(
                    "Decision Assistant model insight unavailable (error_type=%s)",
                    type(error).__name__,
                )

            return {
                "status": "available",
                "total_students": total,
                "high_risk_students": high,
                "high_risk_pct": round(high / total * 100, 2) if total else 0.0,
                "medium_risk_students": medium,
                "low_risk_students": low,
                "avg_dropout_prob": response.average_dropout_probability,
                "average_gpa": response.average_gpa,
                "average_attendance": response.average_attendance,
                "top_risk_department": ranked[0]["department_id"] if ranked else None,
                "top_risk_department_pct": (
                    round(ranked[0]["high_risk_count"] / ranked[0]["total_students"] * 100, 2)
                    if ranked else None
                ),
                "top_risk_factor": risk_factors[0] if risk_factors else None,
                "risk_factors": risk_factors,
                "department_chart": departments,
            }
        except Exception as error:
            return _unavailable({
                "total_students": None,
                "high_risk_students": None,
                "high_risk_pct": None,
                "medium_risk_students": None,
                "low_risk_students": None,
                "avg_dropout_prob": None,
                "average_gpa": None,
                "average_attendance": None,
                "top_risk_department": None,
                "top_risk_department_pct": None,
                "top_risk_factor": None,
                "risk_factors": [],
                "department_chart": [],
            }, error, "student")

    def _get_finance_evidence(
        self,
        department: Optional[str],
        academic_year: Optional[Union[int, str]],
        semester: Optional[int],
    ) -> Dict[str, Any]:
        try:
            year = _finance_year(academic_year)
            overview = finance_service.get_overview(
                department_id=department,
                academic_year=year,
                semester=semester,
            )
            department_response = finance_service.get_departments(
                department_id=department,
                academic_year=year,
            )
            departments = []
            for item in department_response.departments:
                row = _dump(item)
                allocated = row.get("allocated_budget")
                expenditure = row.get("actual_expenditure")
                try:
                    allocated = float(allocated) if allocated is not None else None
                    expenditure = float(expenditure) if expenditure is not None else None
                except (TypeError, ValueError):
                    allocated = expenditure = None
                row["budget_utilization"] = (
                    round(expenditure / allocated * 100, 2)
                    if allocated is not None and allocated > 0 and expenditure is not None
                    else None
                )
                departments.append(row)

            total_budget = overview.total_budget
            total_spent = overview.actual_expenditure
            budget_utilization = (
                round(total_spent / total_budget * 100, 2)
                if total_budget is not None and total_budget > 0 and total_spent is not None
                else None
            )
            has_finance_data = bool(departments) or bool(
                (total_budget or 0)
                or (total_spent or 0)
                or (overview.outstanding_fees or 0)
            )
            if not has_finance_data:
                return _unavailable({
                    "total_budget": None,
                    "total_spent": None,
                    "budget_utilization_pct": None,
                    "overrun_departments_count": None,
                    "total_outstanding_fees": None,
                    "outstanding_fee_pct": None,
                    "fee_collection_rate": None,
                    "departments": [],
                }, ValueError("No Finance records matched the current scope"), "finance")
            return {
                "status": "available",
                "total_budget": total_budget,
                "total_spent": total_spent,
                "budget_utilization_pct": budget_utilization,
                "overrun_departments_count": sum(
                    row.get("budget_utilization") is not None
                    and row["budget_utilization"] > 100
                    for row in departments
                ),
                "total_outstanding_fees": overview.outstanding_fees,
                "outstanding_fee_pct": (
                    round(100 - overview.fee_collection_rate, 2)
                    if overview.fee_collection_rate is not None else None
                ),
                "fee_collection_rate": overview.fee_collection_rate,
                "departments": departments,
            }
        except Exception as error:
            return _unavailable({
                "total_budget": None,
                "total_spent": None,
                "budget_utilization_pct": None,
                "overrun_departments_count": None,
                "total_outstanding_fees": None,
                "outstanding_fee_pct": None,
                "fee_collection_rate": None,
                "departments": [],
            }, error, "finance")

    def _get_research_evidence(
        self,
        department: Optional[str],
        academic_year: Optional[Union[int, str]],
        access_token: Optional[str],
    ) -> Dict[str, Any]:
        try:
            response = research_service.get_faculty_analytics(
                department=department,
                academic_year=_faculty_year(academic_year),
                access_token=access_token,
            )
            overview = response.overview
            return {
                "status": "available",
                "total_faculty": overview.total_faculty,
                "faculty_researchers": overview.faculty_researchers,
                "total_publications": overview.total_publications,
                "average_publications_per_faculty": overview.average_publications_per_faculty,
                "participation_rate_pct": overview.faculty_participation_rate,
                "total_citations": overview.total_citations,
                "total_research_grants": overview.total_research_grants,
                "is_synthetic": overview.is_synthetic,
                "departments": [_dump(row) for row in response.departments],
                "publication_trends": [_dump(row) for row in response.publication_trends],
                "top_researchers": [_dump(row) for row in response.top_researchers],
            }
        except Exception as error:
            return _unavailable({
                "total_faculty": None,
                "faculty_researchers": None,
                "total_publications": None,
                "average_publications_per_faculty": None,
                "participation_rate_pct": None,
                "total_citations": None,
                "total_research_grants": None,
                "is_synthetic": None,
                "departments": [],
                "publication_trends": [],
                "top_researchers": [],
            }, error, "research")

    @staticmethod
    def _build_department_comparison(
        student: Dict[str, Any],
        finance: Dict[str, Any],
        research: Dict[str, Any],
        role: str,
        user_dept: Optional[str],
        department: Optional[str],
    ) -> List[DepartmentComparisonItem]:
        research_rows = {
            _department_code(str(row.get("department", ""))): row
            for row in research.get("departments", [])
        }
        student_rows = {
            _department_code(str(row.get("department_id", ""))): row
            for row in student.get("department_chart", [])
        }
        finance_rows = {
            _department_code(str(row.get("department_id", ""))): row
            for row in finance.get("departments", [])
        }
        if role == "HOD" and user_dept:
            codes = {_department_code(user_dept)}
        elif department:
            codes = {_department_code(department)}
        else:
            codes = set(student_rows) | set(finance_rows) | set(research_rows)

        result = []
        for code in sorted(value for value in codes if value):
            s_row = student_rows.get(code)
            f_row = finance_rows.get(code)
            r_row = research_rows.get(code)
            total = s_row.get("total_students") if s_row else None
            high = s_row.get("high_risk_count") if s_row else None
            result.append(DepartmentComparisonItem(
                department=code,
                student_total=total,
                student_high_risk=high,
                student_high_risk_pct=(
                    round(high / total * 100, 2) if total and high is not None else None
                ),
                finance_budget_utilization_pct=(
                    f_row.get("budget_utilization") if f_row else None
                ),
                finance_outstanding_fees=f_row.get("outstanding_fees") if f_row else None,
                finance_fee_collection_rate=(
                    f_row.get("fee_collection_rate") if f_row else None
                ),
                research_total_faculty=r_row.get("total_faculty") if r_row else None,
                research_publications=r_row.get("publications") if r_row else None,
                research_publications_per_faculty=(
                    r_row.get("average_publications_per_faculty") if r_row else None
                ),
                research_participation_pct=(
                    r_row.get("participation_rate") if r_row else None
                ),
            ))
        return result

    @staticmethod
    def _findings(student: Dict[str, Any], finance: Dict[str, Any], research: Dict[str, Any]) -> List[FindingItem]:
        findings = []
        if student["status"] == "available":
            findings.append(FindingItem(
                domain="student",
                title="Student risk",
                description=(
                    f'{student["high_risk_students"]:,} of {student["total_students"]:,} students '
                    f'are classified high risk ({student["high_risk_pct"]:.1f}%).'
                ),
                metric=f'{student["high_risk_pct"]:.1f}% high risk',
                impact="negative" if student["high_risk_students"] else "neutral",
            ))
        if finance["status"] == "available":
            utilization = finance["budget_utilization_pct"]
            findings.append(FindingItem(
                domain="finance",
                title="Financial position",
                description=(
                    (
                        f'Budget utilization is {utilization:.1f}%; '
                        if utilization is not None else "Budget utilization is unavailable; "
                    )
                    + f'{finance["overrun_departments_count"]} department(s) exceed allocation. '
                    + f'Outstanding fees total ₹{finance["total_outstanding_fees"]:,.2f}.'
                ),
                metric=(
                    f'{utilization:.1f}% budget utilization'
                    if utilization is not None else "Budget utilization unavailable"
                ),
                impact=(
                    "negative"
                    if finance["overrun_departments_count"]
                    else "neutral"
                ),
            ))
        if research["status"] == "available":
            findings.append(FindingItem(
                domain="research",
                title="Faculty research",
                description=(
                    f'{research["total_publications"]:,} publications across '
                    f'{research["total_faculty"]:,} active faculty; average '
                    f'{research["average_publications_per_faculty"]:.2f} per faculty member.'
                ),
                metric=f'{research["participation_rate_pct"]:.1f}% faculty participation',
                impact="neutral",
            ))
        return findings

    @staticmethod
    def _actionable_issues(
        student: Dict[str, Any],
        finance: Dict[str, Any],
    ) -> List[ActionableIssue]:
        issues = []
        if (
            student["status"] == "available"
            and student["high_risk_students"]
            and student.get("top_risk_department")
        ):
            code = student.get("top_risk_department")
            department_row = next(
                (row for row in student["department_chart"] if row.get("department_id") == code),
                None,
            )
            evidence = (
                f'{department_row["high_risk_count"]:,} of '
                f'{department_row["total_students"]:,} students in {code} are high risk '
                f'({student["top_risk_department_pct"]:.1f}%).'
                if department_row else (
                    f"{code} has the highest observed high-risk share "
                    f'({student["top_risk_department_pct"]:.1f}%).'
                )
            )
            issues.append(ActionableIssue(
                domain="student",
                department=code,
                title="Review the department with the highest student risk share",
                evidence=evidence,
            ))
        if finance["status"] == "available":
            overruns = [
                row for row in finance["departments"]
                if row.get("budget_utilization") is not None
                and row["budget_utilization"] > 100
            ]
            overruns.sort(key=lambda row: row["budget_utilization"], reverse=True)
            for row in overruns[:3]:
                issues.append(ActionableIssue(
                    domain="finance",
                    department=row.get("department_id"),
                    title="Department spending exceeds its budget allocation",
                    evidence=(
                        f'{row.get("department_id")}: '
                        f'{row["budget_utilization"]:.1f}% utilization.'
                    ),
                ))
        return issues[:4]

    def get_decision_overview(
        self,
        role: str = "ADMINISTRATOR",
        user_dept: Optional[str] = None,
        department: Optional[str] = None,
        academic_year: Optional[Union[int, str]] = None,
        semester: Optional[int] = None,
        access_token: Optional[str] = None,
        evidence_modules: Optional[set[str]] = None,
    ) -> DecisionOverviewResponse:
        _academic_year_parts(academic_year)
        effective_role = role.upper()
        scoped_department = user_dept if effective_role == "HOD" else department
        requested_modules = evidence_modules or {"student", "finance", "research"}
        student = (
            self._get_student_evidence(
                effective_role, user_dept, scoped_department, academic_year, semester
            )
            if "student" in requested_modules else {
                "status": "not_requested",
                "total_students": None,
                "high_risk_students": None,
                "high_risk_pct": None,
                "medium_risk_students": None,
                "low_risk_students": None,
                "avg_dropout_prob": None,
                "top_risk_department": None,
                "top_risk_department_pct": None,
                "top_risk_factor": None,
                "department_chart": [],
            }
        )
        finance = (
            self._get_finance_evidence(scoped_department, academic_year, semester)
            if "finance" in requested_modules else {
                "status": "not_requested",
                "total_budget": None,
                "total_spent": None,
                "budget_utilization_pct": None,
                "overrun_departments_count": None,
                "total_outstanding_fees": None,
                "outstanding_fee_pct": None,
                "fee_collection_rate": None,
                "departments": [],
            }
        )
        research = (
            self._get_research_evidence(
                scoped_department, academic_year, access_token
            )
            if "research" in requested_modules else {
                "status": "not_requested",
                "total_faculty": None,
                "faculty_researchers": None,
                "total_publications": None,
                "average_publications_per_faculty": None,
                "participation_rate_pct": None,
                "total_citations": None,
                "total_research_grants": None,
                "is_synthetic": None,
                "departments": [],
                "publication_trends": [],
                "top_researchers": [],
            }
        )
        comparison = self._build_department_comparison(
            student, finance, research, effective_role, user_dept, scoped_department
        )
        findings = self._findings(student, finance, research)
        issues = self._actionable_issues(student, finance)
        available = [
            name for name, result in (
                ("Student", student), ("Finance", finance), ("Faculty Research", research)
            ) if result["status"] == "available"
        ]
        unavailable = [
            name for name, result in (
                ("Student", student), ("Finance", finance), ("Faculty Research", research)
            ) if result["status"] != "available"
        ]
        summary_parts = []
        if available:
            summary_parts.append("Data available: " + ", ".join(available))
        if unavailable:
            summary_parts.append("Unavailable: " + ", ".join(unavailable))
        summary = ". ".join(summary_parts) + "." if summary_parts else "No module data is available."

        return DecisionOverviewResponse(
            scope=ScopeInfo(
                role=effective_role,
                department=scoped_department or "All accessible departments",
                academic_year=academic_year,
                semester=semester,
            ),
            summary=summary,
            key_findings=findings,
            actionable_issues=issues,
            areas_of_attention=issues,
            evidence=EvidenceSummary(
                student=StudentEvidence(**{
                    key: value for key, value in student.items()
                    if key != "department_chart"
                }, department_chart=student.get("department_chart", [])),
                finance=FinanceEvidence(**finance),
                research=ResearchEvidence(**research),
                department_comparison=comparison,
            ),
        )

    @staticmethod
    def _module_unavailable(name: str) -> str:
        return f"{name} data is unavailable for the current access scope; no figure is reported."

    def _query_answer(
        self,
        intent: str,
        data: DecisionOverviewResponse,
    ) -> tuple[str, List[FindingItem], Dict[str, Any]]:
        student = data.evidence.student
        finance = data.evidence.finance
        research = data.evidence.research
        departments = data.evidence.department_comparison
        scope_department = (
            data.scope.department
            if data.scope.department != "All accessible departments"
            else None
        )

        if intent.startswith("student_"):
            if student.status != "available":
                return self._module_unavailable("Student"), [], {"student_status": student.status}
            if intent == "student_predictors":
                factors = student.risk_factors
                answer = (
                    "Current model-level dropout predictors in ranked order: "
                    + ", ".join(factors[:5])
                    + ". These are model-wide predictors, not department-specific causal findings."
                    if factors else "The Student model did not return predictor data."
                )
                return answer, [], {"risk_factors": factors[:5]}
            if intent == "student_average_gpa":
                return (
                    f"Average GPA in the current student scope is {student.average_gpa:.2f}.",
                    [], {"average_gpa": student.average_gpa},
                )
            if intent == "student_average_probability":
                return (
                    f"Average predicted dropout probability is "
                    f"{student.avg_dropout_prob * 100:.1f}%.",
                    [], {"average_dropout_probability": student.avg_dropout_prob},
                )
            if intent == "student_distribution":
                if not student.total_students:
                    return "No students were found for the current access scope and filters.", [], {}
                answer = (
                    f'Risk distribution: {student.high_risk_students:,} high, '
                    f'{student.medium_risk_students:,} medium, and '
                    f'{student.low_risk_students:,} low-risk students '
                    f'out of {student.total_students:,}.'
                )
                return answer, [], {
                    "high": student.high_risk_students,
                    "medium": student.medium_risk_students,
                    "low": student.low_risk_students,
                    "total": student.total_students,
                }
            if intent == "student_department_risk":
                ranked = sorted(
                    (row for row in departments if row.student_total),
                    key=lambda row: row.student_high_risk_pct or 0,
                    reverse=True,
                )
                if not ranked:
                    return "No department-level student risk data is available for this scope.", [], {}
                top = ranked[0]
                if len(ranked) == 1:
                    answer = (
                        f"{top.department} has a high-risk share of "
                        f"{top.student_high_risk_pct:.1f}% "
                        f"({top.student_high_risk:,} of {top.student_total:,} students) "
                        "in the current scope; other departments are not in scope for comparison."
                    )
                else:
                    answer = (
                        f"{top.department} has the highest observed high-risk share: "
                        f"{top.student_high_risk_pct:.1f}% "
                        f"({top.student_high_risk:,} of {top.student_total:,} students)."
                    )
                return answer, [], {
                    "department": top.department,
                    "high_risk_percentage": top.student_high_risk_pct,
                    "high_risk_students": top.student_high_risk,
                    "total_students": top.student_total,
                }
            if intent == "student_high_risk":
                if not student.total_students:
                    return "No students were found for the current access scope and filters.", [], {}
                department_label = (
                    f" in {data.scope.department}"
                    if data.scope.department != "All accessible departments"
                    else ""
                )
                return (
                    f'{student.high_risk_students:,} of {student.total_students:,} students{department_label} '
                    f'({student.high_risk_pct:.1f}%) are classified high risk.',
                    [], {"high_risk_students": student.high_risk_students,
                         "total_students": student.total_students,
                         "high_risk_percentage": student.high_risk_pct},
                )
            if intent == "student":
                return (
                    f'{student.total_students:,} students are in scope; '
                    f'{student.high_risk_students:,} ({student.high_risk_pct:.1f}%) '
                    f'are classified high risk. Average GPA is {student.average_gpa:.2f}.',
                    [], {"total_students": student.total_students,
                         "high_risk_students": student.high_risk_students,
                         "high_risk_percentage": student.high_risk_pct,
                         "average_gpa": student.average_gpa},
                )

        if intent.startswith("finance_"):
            if finance.status != "available":
                return self._module_unavailable("Finance"), [], {"finance_status": finance.status}
            rows = finance.departments
            if intent == "finance_outstanding":
                if finance.total_outstanding_fees is None:
                    return self._module_unavailable("Finance"), [], {"finance_status": finance.status}
                scope_label = f" in {scope_department}" if scope_department else ""
                return (
                    f"Total outstanding fees{scope_label} are ₹{finance.total_outstanding_fees:,.2f}.",
                    [], {"outstanding_fees": finance.total_outstanding_fees},
                )
            if intent == "finance_expenditure":
                if finance.total_spent is None:
                    return "Finance expenditure data is unavailable for the current scope and filters.", [], {}
                scope_label = f" in {scope_department}" if scope_department else ""
                return (
                    f"Recorded actual expenditure{scope_label} is ₹{finance.total_spent:,.2f}.",
                    [], {"actual_expenditure": finance.total_spent},
                )
            if intent == "finance_overrun":
                valid_budget_rows = [
                    row for row in rows if row.get("budget_utilization") is not None
                ]
                if not valid_budget_rows:
                    return (
                        "Budget utilization is unavailable because allocated budget or actual "
                        "expenditure data is missing or the allocation is zero.",
                        [], {},
                    )
                overruns = [row for row in valid_budget_rows if row["budget_utilization"] > 100]
                overruns.sort(key=lambda row: row["budget_utilization"], reverse=True)
                if len(valid_budget_rows) == 1:
                    row = valid_budget_rows[0]
                    answer = (
                        f'{row["department_id"]} has exceeded its allocated budget '
                        f'({row["budget_utilization"]:.1f}% utilization).'
                        if overruns else
                        f'{row["department_id"]} has not exceeded its allocated budget '
                        f'({row["budget_utilization"]:.1f}% utilization).'
                    )
                else:
                    answer = (
                        f"{len(overruns)} department(s) exceed allocation: " + "; ".join(
                            f'{row["department_id"]} ({row["budget_utilization"]:.1f}%)'
                            for row in overruns
                        ) + "."
                        if overruns else "No department exceeds its recorded budget allocation."
                    )
                return answer, [], {
                    "overrun_departments": [
                        {
                            "department": row["department_id"],
                            "budget_utilization_pct": row["budget_utilization"],
                            "allocated_budget": row["allocated_budget"],
                            "actual_expenditure": row["actual_expenditure"],
                        }
                        for row in overruns
                    ]
                }
            if intent == "finance_collection":
                ranked = sorted(
                    (row for row in rows if row.get("fee_collection_rate") is not None),
                    key=lambda row: row["fee_collection_rate"],
                    reverse=True,
                )
                return (
                    (
                        f'{ranked[0]["department_id"]} has the highest fee collection rate '
                        f'({ranked[0]["fee_collection_rate"]:.1f}%).'
                    ) if ranked else "Department fee collection data is unavailable.",
                    [], {"departments": [
                        {"department": row["department_id"],
                         "fee_collection_rate": row["fee_collection_rate"]}
                        for row in ranked
                    ]},
                )
            if intent == "finance_utilization":
                ranked = sorted(
                    (row for row in rows if row.get("budget_utilization") is not None),
                    key=lambda row: row["budget_utilization"],
                    reverse=True,
                )
                answer = "; ".join(
                    f'{row["department_id"]}: {row["budget_utilization"]:.1f}%'
                    for row in ranked
                )
                return (
                    f"Budget utilization by department: {answer}."
                    if answer else "Department budget utilization data is unavailable.",
                    [], {"departments": [
                        {"department": row["department_id"],
                         "budget_utilization_pct": row["budget_utilization"]}
                        for row in ranked
                    ]},
                )
            if intent == "finance_pressure":
                ranked = sorted(
                    (row for row in rows if row.get("risk_score") is not None),
                    key=lambda row: row["risk_score"],
                    reverse=True,
                )
                if not ranked:
                    return "Department financial pressure scores are unavailable.", [], {}
                top = ranked[0]
                return (
                    f'{top["department_id"]} has the highest finance-service risk score '
                    f'({top["risk_score"]:.1f}; {top.get("risk_level", "unclassified")}).',
                    [], {"department": top["department_id"],
                         "risk_score": top["risk_score"],
                         "risk_level": top.get("risk_level")},
                )
            if intent == "finance":
                outstanding = (
                    f"₹{finance.total_outstanding_fees:,.2f}"
                    if finance.total_outstanding_fees is not None
                    else "unavailable"
                )
                fee_rate = (
                    f"{finance.fee_collection_rate:.1f}%"
                    if finance.fee_collection_rate is not None
                    else "unavailable"
                )
                return (
                    (
                        f'Budget utilization is {finance.budget_utilization_pct:.1f}%; '
                        if finance.budget_utilization_pct is not None
                        else "Budget utilization is unavailable; "
                    )
                    + f'outstanding fees are {outstanding}; fee collection rate is {fee_rate}.',
                    [], {"budget_utilization_pct": finance.budget_utilization_pct,
                         "outstanding_fees": finance.total_outstanding_fees,
                         "fee_collection_rate": finance.fee_collection_rate},
                )

        if intent.startswith("research_"):
            if research.status != "available":
                return self._module_unavailable("Faculty Research"), [], {"research_status": research.status}
            rows = research.departments
            if intent == "research_average":
                if not research.total_faculty:
                    return "No active faculty were found for the current access scope and filters.", [], {}
                scope_label = f" in {scope_department}" if scope_department else ""
                return (
                    f"Average faculty publication output is "
                    f"{research.average_publications_per_faculty:.2f} per active faculty member{scope_label}.",
                    [], {"publications": research.total_publications,
                         "active_faculty": research.total_faculty,
                         "average_publications_per_faculty": research.average_publications_per_faculty},
                )
            if intent == "research_department_average":
                ranked = sorted(
                    (
                        row for row in rows
                        if row.get("total_faculty", 0) > 0
                        and row.get("average_publications_per_faculty") is not None
                    ),
                    key=lambda row: row["average_publications_per_faculty"],
                    reverse=True,
                )
                if not ranked:
                    return "Department average faculty publication data is unavailable.", [], {}
                top = ranked[0]
                comparison = (
                    "the highest average faculty publication output"
                    if len(ranked) > 1
                    else "an average faculty publication output"
                )
                return (
                    f'{top["department"]} has {comparison} '
                    f'({top["average_publications_per_faculty"]:.2f} publications per active faculty '
                    f'from {top["publications"]:,} publications across {top["total_faculty"]:,} active faculty'
                    + (")." if len(ranked) > 1 else " in the current scope; other departments are not available for comparison."),
                    [],
                    {
                        "departments": [
                            {
                                "department": row["department"],
                                "total_publications": row["publications"],
                                "active_faculty": row["total_faculty"],
                                "average_publications_per_faculty": row["average_publications_per_faculty"],
                            }
                            for row in ranked
                        ]
                    },
                )
            if intent == "research_faculty_count":
                if research.total_faculty is None:
                    return "Active faculty data is unavailable for the current scope and filters.", [], {}
                scope_label = f" in {scope_department}" if scope_department else ""
                return (
                    f"{research.total_faculty:,} active faculty members are in the current scope{scope_label}.",
                    [], {"active_faculty": research.total_faculty},
                )
            if intent == "research_total_publications":
                if research.total_publications is None:
                    return "Faculty publication data is unavailable for the current scope and filters.", [], {}
                scope_label = f" in {scope_department}" if scope_department else ""
                return (
                    f"{research.total_publications:,} faculty publications are recorded in the current scope{scope_label}.",
                    [], {"total_publications": research.total_publications},
                )
            if intent == "research_top_faculty":
                leaders = research.top_researchers[:5]
                answer = (
                    "Top faculty researchers by publication count: " + "; ".join(
                        f'{row["faculty_name"]} ({row["department"]}, {row["publications"]})'
                        for row in leaders
                    ) + "."
                    if leaders else "Faculty researcher publication data is unavailable."
                )
                return answer, [], {
                    "top_researchers": [
                        {
                            "faculty_name": row["faculty_name"],
                            "department": row["department"],
                            "publications": row["publications"],
                        }
                        for row in leaders
                    ]
                }
            if intent == "research_trends":
                trends = research.publication_trends
                answer = (
                    "Publication totals by academic year: " + "; ".join(
                        f'{row["academic_year"]}: {row["publications"]:,}'
                        for row in trends
                    ) + "."
                    if trends else "Publication trend data is unavailable."
                )
                return answer, [], {
                    "publication_trends": [
                        {"academic_year": row["academic_year"], "publications": row["publications"]}
                        for row in trends
                    ]
                }
            if intent in {"research_department_publications", "research_participation"}:
                field = "publications" if intent == "research_department_publications" else "participation_rate"
                ranked = sorted(
                    (row for row in rows if row.get(field) is not None),
                    key=lambda row: row[field],
                    reverse=intent == "research_department_publications",
                )
                if not ranked:
                    return "Department faculty research data is unavailable.", [], {}
                if intent == "research_department_publications":
                    top = ranked[0]
                    answer = (
                        f'{top["department"]} has the highest faculty publication output '
                        f'({top["publications"]:,} publications).'
                    )
                    details = [
                        {
                            "department": row["department"],
                            "total_publications": row["publications"],
                            "active_faculty": row["total_faculty"],
                        }
                        for row in ranked
                    ]
                else:
                    answer = "Faculty research participation by department: " + "; ".join(
                        f'{row["department"]}: {row["participation_rate"]:.1f}%'
                        for row in ranked
                    ) + "."
                    details = [
                        {
                            "department": row["department"],
                            "participating_faculty": row["faculty_researchers"],
                            "total_active_faculty": row["total_faculty"],
                            "participation_pct": row["participation_rate"],
                        }
                        for row in ranked
                    ]
                return answer, [], {"departments": details}
            if intent == "research":
                top_department = max(
                    rows,
                    key=lambda row: row.get("publications", 0),
                    default=None,
                )
                answer = (
                    f'{research.total_publications:,} publications across '
                    f'{research.total_faculty:,} active faculty; average '
                    f'{research.average_publications_per_faculty:.2f} per faculty member.'
                )
                if top_department:
                    answer += (
                        f' Highest department output is {top_department["department"]} '
                        f'({top_department["publications"]:,}).'
                    )
                return answer, [], {
                    "total_publications": research.total_publications,
                    "total_faculty": research.total_faculty,
                    "average_publications_per_faculty": research.average_publications_per_faculty,
                    "top_department": (
                        {
                            "department": top_department["department"],
                            "total_publications": top_department["publications"],
                            "active_faculty": top_department["total_faculty"],
                        }
                        if top_department else None
                    ),
                }

        if intent in {"cross_attention", "cross_weak_departments", "cross_priorities"}:
            if not departments:
                return "Department comparison data is unavailable for the current scope.", [], {}
            risk_values = [
                row.student_high_risk_pct for row in departments
                if row.student_high_risk_pct is not None
            ]
            risk_median = median(risk_values) if risk_values else None
            ranked = []
            for row in departments:
                flags = []
                if row.student_high_risk_pct is not None:
                    if risk_median is not None and row.student_high_risk_pct > risk_median:
                        flags.append("student high-risk share above scoped median")
                if row.finance_budget_utilization_pct is not None and row.finance_budget_utilization_pct > 100:
                    flags.append("budget utilization above 100% (overrun)")
                # Faculty participation is contextual evidence, not a weakness signal.
                if flags:
                    ranked.append({
                        "department": row.department,
                        "signals": flags,
                        "student_high_risk_pct": row.student_high_risk_pct,
                        "budget_utilization_pct": row.finance_budget_utilization_pct,
                        "research_participation_pct": row.research_participation_pct,
                    })
            ranked.sort(key=lambda row: (-len(row["signals"]), row["department"]))
            if intent == "cross_weak_departments":
                ranked = [row for row in ranked if len(row["signals"]) >= 2]
            qualifying_departments = len(ranked)
            if intent == "cross_priorities":
                ranked = ranked[:3]
            if not ranked:
                answer = (
                    "No department has both an above-median student high-risk share and budget utilization "
                    "above 100% in the available data."
                    if intent == "cross_weak_departments"
                    else "No attention signals were found in the available department data."
                )
            else:
                answer = (
                    f"Top supported priorities ({len(ranked)} of {qualifying_departments} "
                    "qualifying departments): "
                    if intent == "cross_priorities" else ""
                ) + "; ".join(
                    f'{row["department"]}: {", ".join(row["signals"])}'
                    + (
                        f' (faculty research participation {row["research_participation_pct"]:.1f}% as context)'
                        if row["research_participation_pct"] is not None else ""
                    )
                    for row in ranked
                ) + "."
            return answer, [], {
                "departments": ranked,
                "qualifying_departments": qualifying_departments,
                "results_shown": len(ranked),
                "scope_student_risk_context": (
                    {
                        "high_risk_students": student.high_risk_students,
                        "total_students": student.total_students,
                        "high_risk_percentage": student.high_risk_pct,
                        "note": (
                            "No cross-department median comparison is available in this scope."
                            if len(departments) == 1 else None
                        ),
                    }
                    if student.status == "available" and len(departments) == 1
                    else None
                ),
                "attention_criteria": {
                    "student_risk": "High-risk percentage strictly above the median across scoped departments.",
                    "financial_overrun": "Budget utilization strictly greater than 100%.",
                    "research_participation": "Context only; it is not used to flag or rank weakness.",
                    "department_qualifies": (
                        "At least one student-risk or financial-overrun signal."
                        if intent == "cross_attention"
                        else "Both student-risk and financial-overrun signals."
                        if intent == "cross_weak_departments"
                        else "Rank the supported student-risk and financial-overrun signals; research participation is context only."
                    ),
                },
            }

        if intent in {"cross_compare", "cross_summary"}:
            if intent == "cross_compare":
                rows = [
                    row for row in departments
                    if row.student_high_risk_pct is not None
                    or row.finance_budget_utilization_pct is not None
                ]
                return (
                    "Department comparison uses observed student high-risk share and finance budget utilization.",
                    [], {"departments": [
                        {"department": row.department,
                         "student_high_risk_pct": row.student_high_risk_pct,
                         "budget_utilization_pct": row.finance_budget_utilization_pct}
                        for row in rows
                    ]},
                )
            summary = []
            if student.status == "available":
                summary.append(
                    f'{student.high_risk_students:,}/{student.total_students:,} students high risk '
                    f'({student.high_risk_pct:.1f}%)'
                )
            if finance.status == "available":
                finance_summary = []
                if finance.budget_utilization_pct is not None:
                    finance_summary.append(
                        f'{finance.budget_utilization_pct:.1f}% budget utilization'
                    )
                else:
                    finance_summary.append("budget utilization unavailable")
                if finance.total_outstanding_fees is not None:
                    finance_summary.append(
                        f'₹{finance.total_outstanding_fees:,.2f} outstanding fees'
                    )
                else:
                    finance_summary.append("outstanding fee data unavailable")
                summary.append(
                    ", ".join(finance_summary)
                )
            if research.status == "available":
                summary.append(
                    f'{research.total_publications:,} faculty publications across '
                    f'{research.total_faculty:,} active faculty '
                    f'({research.average_publications_per_faculty:.2f} per faculty)'
                )
            if not summary:
                return "Student, Finance, and Faculty Research data are unavailable for this scope.", [], {}
            title = (
                f"{data.scope.department} performance summary"
                if data.scope.department != "All accessible departments"
                else "Institutional summary"
            )
            return title + ": " + "; ".join(summary) + ".", [], {
                "student_status": student.status,
                "finance_status": finance.status,
                "research_status": research.status,
                "student_high_risk_students": student.high_risk_students,
                "student_total_students": student.total_students,
                "student_high_risk_pct": student.high_risk_pct,
                "finance_budget_utilization_pct": finance.budget_utilization_pct,
                "finance_outstanding_fees": finance.total_outstanding_fees,
                "research_total_publications": research.total_publications,
                "research_total_faculty": research.total_faculty,
                "research_average_publications_per_faculty": research.average_publications_per_faculty,
            }

        return (
            "I could not match that question to a supported Student, Finance, Faculty Research, "
            "or cross-module data query. Please ask about a metric, department comparison, or trend.",
            [], {"supported_modules": ["student", "finance", "faculty research", "cross-module"]},
        )

    def execute_natural_query(
        self,
        query: str,
        role: str = "ADMINISTRATOR",
        user_dept: Optional[str] = None,
        department: Optional[str] = None,
        academic_year: Optional[Union[int, str]] = None,
        access_token: Optional[str] = None,
    ) -> DecisionQueryResponse:
        intent = classify_query(query)
        if intent is None:
            answer, metrics = (
                "I could not match that question to a supported Student, Finance, Faculty Research, "
                "or cross-module data query. Please ask about a metric, department comparison, or trend.",
                {},
            )
            return DecisionQueryResponse(
                query=query,
                matched_intent="unsupported",
                summary=answer,
                supporting_metrics=metrics,
            )

        if intent == "student" or intent.startswith("student_"):
            modules = {"student"}
        elif intent == "finance" or intent.startswith("finance_"):
            modules = {"finance"}
        elif intent == "research" or intent.startswith("research_"):
            modules = {"research"}
        else:
            modules = {"student", "finance", "research"}
        overview = self.get_decision_overview(
            role=role,
            user_dept=user_dept,
            department=department,
            academic_year=academic_year,
            access_token=access_token,
            evidence_modules=modules,
        )
        if intent == "student_high_risk_students":
            scoped_department = user_dept if role.upper() == "HOD" else department
            try:
                records = student_service.get_filtered_students(
                    role=role,
                    user_dept=user_dept,
                    department=scoped_department,
                    academic_year=_year_start(academic_year),
                    semester=None,
                    risk_level="HIGH",
                    page=1,
                    page_size=20,
                )
            except Exception as error:
                logger.error(
                    "Decision Assistant could not load high-risk student records "
                    "(error_type=%s)",
                    type(error).__name__,
                )
                return DecisionQueryResponse(
                    query=query,
                    matched_intent=intent,
                    summary="High-risk student records are unavailable for the current access scope and filters.",
                    supporting_metrics={"student_status": "unavailable"},
                )
            students = [
                {
                    "student_id": row.student_id,
                    "risk_level": row.risk_level,
                    "dropout_probability": row.dropout_probability,
                }
                for row in records.students
            ]
            total = records.total_students
            scope_label = (
                f" in {scoped_department}"
                if scoped_department else " in the current access scope"
            )
            answer = (
                f"No high-risk students were found{scope_label}."
                if total == 0
                else (
                    f"Showing {len(students)} of {total:,} high-risk students{scope_label}; "
                    "the list is capped at 20 records."
                )
            )
            metrics = {
                "students": students,
                "total_matching_students": total,
                "results_shown": len(students),
            }
            if overview.scope.academic_year is not None:
                metrics["academic_year"] = overview.scope.academic_year
            if overview.scope.semester is not None:
                metrics["semester"] = overview.scope.semester
            metrics["scope"] = overview.scope.model_dump()
            return DecisionQueryResponse(
                query=query,
                matched_intent=intent,
                summary=answer,
                supporting_metrics=metrics,
            )
        answer, _, metrics = self._query_answer(intent, overview)
        metrics["scope"] = overview.scope.model_dump()
        return DecisionQueryResponse(
            query=query,
            matched_intent=intent or "unsupported",
            summary=answer,
            findings=overview.key_findings,
            supporting_metrics=metrics,
        )


decision_service = DecisionService()

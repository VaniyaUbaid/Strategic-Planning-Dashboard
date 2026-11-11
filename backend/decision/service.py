import logging
import traceback
from typing import Dict, List, Optional, Any
from backend.decision.rules import DecisionRulesEngine
from backend.decision.schemas import (
    AttentionArea,
    DecisionOverviewResponse,
    DecisionQueryResponse,
    DecisionStatusResponse,
    DepartmentComparisonItem,
    EvidenceSummary,
    FinanceEvidence,
    FindingItem,
    RecommendedAction,
    ResearchEvidence,
    ScopeInfo,
    StudentEvidence,
)
from backend.finance.service import finance_service
from backend.research.service import research_service
from backend.student.service import student_service

logger = logging.getLogger(__name__)


class DecisionService:
    DEPT_NAMES = {
        "CSE": "Computer Science & Engineering",
        "AIML": "AI & Machine Learning",
        "BBA": "Business Administration",
        "ECE": "Electronics & Communication",
        "EEE": "Electrical & Electronics",
        "ME": "Mechanical Engineering",
        "BT": "Biotechnology",
        "MATH": "Mathematics",
        "CHEM": "Chemistry",
        "PHY": "Physics",
    }

    def get_status(self) -> DecisionStatusResponse:
        """Return operational readiness status of the Decision Assistant module."""
        return DecisionStatusResponse(module="decision_assistant", status="ready")

    def _get_student_evidence(
        self,
        role: str,
        user_dept: Optional[str],
        department: Optional[str],
        academic_year: Optional[int],
        semester: Optional[int],
    ) -> Dict[str, Any]:
        try:
            res = student_service.get_admin_overview(
                role=role,
                user_dept=user_dept,
                department=department,
                academic_year=academic_year,
                semester=semester,
            )
            top_dept = "N/A"
            dept_chart = res.department_chart or []
            if dept_chart:
                sorted_depts = sorted(
                    dept_chart,
                    key=lambda d: (d.high_risk_count / d.total_students * 100.0) if d.total_students > 0 else 0.0,
                    reverse=True,
                )
                if sorted_depts:
                    top_dept = sorted_depts[0].department_id

            top_factor = "Academic Backlog"
            try:
                model_insights = student_service.get_model_insights()
                if model_insights and model_insights.risk_factors:
                    top_factor = model_insights.risk_factors[0].feature_name
            except Exception:
                pass

            total = res.total_students or 0
            high_risk = res.high_risk_count or res.risk_distribution.high_count or 0
            high_pct = (high_risk / total * 100.0) if total > 0 else 0.0

            return {
                "status": "available",
                "total_students": total,
                "high_risk_students": high_risk,
                "high_risk_pct": round(high_pct, 1),
                "medium_risk_students": res.medium_risk_count or res.risk_distribution.medium_count or 0,
                "low_risk_students": res.low_risk_count or res.risk_distribution.low_count or 0,
                "avg_dropout_prob": round(res.average_dropout_probability or 0.0, 4),
                "top_risk_department": top_dept,
                "top_risk_factor": top_factor,
                "department_chart": dept_chart,
            }
        except Exception as err:
            logger.error(f"[DecisionService] Error fetching Student evidence: {err}")
            traceback.print_exc()
            return {
                "status": "unavailable",
                "error": str(err),
                "total_students": 0,
                "high_risk_students": 0,
                "high_risk_pct": 0.0,
                "medium_risk_students": 0,
                "low_risk_students": 0,
                "avg_dropout_prob": 0.0,
                "top_risk_department": "N/A",
                "top_risk_factor": "N/A",
                "department_chart": [],
            }

    def _get_finance_evidence(
        self,
        department: Optional[str],
        academic_year: Optional[int],
        semester: Optional[int],
    ) -> Dict[str, Any]:
        try:
            year_str = str(academic_year) if academic_year else None
            res = finance_service.get_overview(
                department_id=department,
                academic_year=year_str,
                semester=semester,
            )
            dept_res = finance_service.get_departments(
                academic_year=year_str,
            )

            dept_list = dept_res.departments or []
            if department and str(department).strip().upper() not in ["ALL", "NONE", "", "NULL"]:
                target_code = str(department).strip().upper()
                dept_list = [d for d in dept_list if d.department_id.upper() == target_code]

            overrun_count = sum(1 for d in dept_list if d.budget_utilization > 100.0)
            out_pct = (100.0 - res.fee_collection_rate) if res.fee_collection_rate > 0 else 0.0

            return {
                "status": "available",
                "total_budget": round(res.total_budget, 2),
                "total_spent": round(res.actual_expenditure, 2),
                "budget_utilization_pct": round(res.budget_utilization, 1),
                "overrun_departments_count": overrun_count,
                "total_outstanding_fees": round(res.outstanding_fees, 2),
                "outstanding_fee_pct": round(out_pct, 1),
                "department_list": dept_list,
            }
        except Exception as err:
            logger.error(f"[DecisionService] Error fetching Finance evidence: {err}")
            traceback.print_exc()
            return {
                "status": "unavailable",
                "error": str(err),
                "total_budget": 0.0,
                "total_spent": 0.0,
                "budget_utilization_pct": 0.0,
                "overrun_departments_count": 0,
                "total_outstanding_fees": 0.0,
                "outstanding_fee_pct": 0.0,
                "department_list": [],
            }

    def _get_research_evidence(
        self,
        department: Optional[str],
        academic_year: Optional[int],
    ) -> Dict[str, Any]:
        try:
            res = research_service.get_overview(
                department=department,
                admission_year=academic_year,
            )
            dept_res = research_service.get_departments(
                department=department,
                admission_year=academic_year,
            )

            dept_list = dept_res.departments or []

            return {
                "status": "available",
                "total_students": res.total_students,
                "participating_students": res.research_participants,
                "participation_rate_pct": round(res.research_participation_rate, 1),
                "total_publications": res.total_publications,
                "avg_publications_per_student": round(res.average_publications, 2),
                "avg_faculty_rating": round(res.average_faculty_rating or 0.0, 2),
                "department_list": dept_list,
            }
        except Exception as err:
            logger.error(f"[DecisionService] Error fetching Research evidence: {err}")
            traceback.print_exc()
            return {
                "status": "unavailable",
                "error": str(err),
                "total_students": 0,
                "participating_students": 0,
                "participation_rate_pct": 0.0,
                "total_publications": 0,
                "avg_publications_per_student": 0.0,
                "avg_faculty_rating": 0.0,
                "department_list": [],
            }

    def _build_department_comparison(
        self,
        student_data: Dict[str, Any],
        finance_data: Dict[str, Any],
        research_data: Dict[str, Any],
        role: str,
        user_dept: Optional[str],
        target_dept: Optional[str],
    ) -> List[DepartmentComparisonItem]:
        # Determine allowed departments for RBAC
        if role.upper() == "HOD" and user_dept:
            depts_to_process = [user_dept.upper()]
        elif target_dept and target_dept.upper() != "ALL":
            depts_to_process = [target_dept.upper()]
        else:
            depts_to_process = list(self.DEPT_NAMES.keys())

        student_depts = {
            d.department_id.upper(): d for d in student_data.get("department_chart", [])
        }
        finance_depts = {
            d.department_id.upper(): d for d in finance_data.get("department_list", [])
        }
        research_depts = {
            d.department.upper(): d for d in research_data.get("department_list", [])
        }

        items = []
        for code in depts_to_process:
            dept_name = self.DEPT_NAMES.get(code, code)

            s_item = student_depts.get(code)
            if s_item and s_item.total_students > 0:
                s_high_pct = (s_item.high_risk_count / s_item.total_students) * 100.0
            else:
                s_high_pct = 0.0
            s_avg_risk = (s_high_pct / 100.0) * 0.8  # proportional risk metric

            f_item = finance_depts.get(code)
            f_util = f_item.budget_utilization if f_item else 0.0
            if f_item and f_item.fee_collection_rate > 0:
                f_fee_pct = 100.0 - f_item.fee_collection_rate
            else:
                f_fee_pct = 0.0

            r_item = research_depts.get(code)
            r_part_pct = r_item.participation_rate if r_item else 0.0
            r_pubs = r_item.average_publications if r_item else 0.0

            # Compute normalized health score (0 to 100, where higher is better)
            risk_penalty = min(s_high_pct * 1.5, 40.0)
            fin_penalty = max(0.0, (f_util - 100.0) * 1.5)
            res_bonus = min(r_part_pct * 0.3, 30.0)

            raw_health = 80.0 - risk_penalty - fin_penalty + res_bonus
            health_score = max(10.0, min(99.0, round(raw_health, 1)))

            if health_score >= 75.0:
                status_lbl = "Optimal"
            elif health_score >= 55.0:
                status_lbl = "Stable"
            else:
                status_lbl = "Requires Attention"

            items.append(
                DepartmentComparisonItem(
                    department=code,
                    department_name=dept_name,
                    student_high_risk_pct=round(s_high_pct, 1),
                    student_avg_risk=round(s_avg_risk, 4),
                    finance_budget_utilization=round(f_util, 1),
                    finance_outstanding_fee_pct=round(f_fee_pct, 1),
                    research_participation_pct=round(r_part_pct, 1),
                    research_avg_publications=round(r_pubs, 2),
                    overall_health_score=health_score,
                    status_label=status_lbl,
                )
            )

        # Sort by overall health score ascending so departments requiring attention appear first
        items.sort(key=lambda i: i.overall_health_score)
        return items

    def get_decision_overview(
        self,
        role: str = "ADMINISTRATOR",
        user_dept: Optional[str] = None,
        department: Optional[str] = None,
        academic_year: Optional[int] = None,
        semester: Optional[int] = None,
    ) -> DecisionOverviewResponse:
        """
        Synthesize cross-module intelligence from Student, Finance, and Research modules with strict RBAC.
        """
        eff_role = role.upper()
        eff_dept = user_dept if eff_role == "HOD" else department

        target_dept = eff_dept
        if target_dept and target_dept.upper() in ["ALL", "NONE", "", "NULL"]:
            target_dept = None

        student_data = self._get_student_evidence(eff_role, user_dept, target_dept, academic_year, semester)
        finance_data = self._get_finance_evidence(target_dept, academic_year, semester)
        research_data = self._get_research_evidence(target_dept, academic_year)

        dept_comparison = self._build_department_comparison(
            student_data, finance_data, research_data, eff_role, user_dept, target_dept
        )

        findings = DecisionRulesEngine.evaluate_cross_module_findings(
            student_data, finance_data, research_data, dept_comparison
        )

        areas_of_attention = DecisionRulesEngine.evaluate_areas_of_attention(
            dept_comparison, student_data, finance_data, research_data
        )

        recommendations = DecisionRulesEngine.generate_recommendations(
            areas_of_attention, dept_comparison
        )

        dept_lbl = self.DEPT_NAMES.get(target_dept.upper(), target_dept) if target_dept else "All Institutional Departments"
        high_risk_pct = student_data.get("high_risk_pct", 0.0)
        budget_util = finance_data.get("budget_utilization_pct", 0.0)
        res_part = research_data.get("participation_rate_pct", 0.0)

        summary = (
            f"Decision intelligence synthesis for {dept_lbl} ({eff_role} scope). "
            f"Cross-module analysis reveals a {high_risk_pct:.1f}% High Dropout Risk rate in Student Success, "
            f"{budget_util:.1f}% budget utilization in Financial Intelligence, and a {res_part:.1f}% student research participation rate. "
            f"{len(areas_of_attention)} department area(s) require proactive policy attention."
        )

        scope_info = ScopeInfo(
            role=eff_role,
            department=dept_lbl,
            academic_year=academic_year,
            semester=semester,
        )

        evidence = EvidenceSummary(
            student=StudentEvidence(**{k: v for k, v in student_data.items() if k != "department_chart"}),
            finance=FinanceEvidence(**{k: v for k, v in finance_data.items() if k != "department_list"}),
            research=ResearchEvidence(**{k: v for k, v in research_data.items() if k != "department_list"}),
            department_comparison=dept_comparison,
        )

        return DecisionOverviewResponse(
            scope=scope_info,
            summary=summary,
            key_findings=findings,
            areas_of_attention=areas_of_attention,
            recommendations=recommendations,
            evidence=evidence,
        )

    def execute_natural_query(
        self,
        query: str,
        role: str = "ADMINISTRATOR",
        user_dept: Optional[str] = None,
        department: Optional[str] = None,
        academic_year: Optional[int] = None,
    ) -> DecisionQueryResponse:
        """
        Execute deterministic intent query against real cross-module data.
        """
        eff_role = role.upper()
        eff_dept = user_dept if eff_role == "HOD" else department
        target_dept = eff_dept if eff_dept and eff_dept.upper() != "ALL" else None

        student_data = self._get_student_evidence(eff_role, user_dept, target_dept, academic_year, None)
        finance_data = self._get_finance_evidence(target_dept, academic_year, None)
        research_data = self._get_research_evidence(target_dept, academic_year)

        dept_comparison = self._build_department_comparison(
            student_data, finance_data, research_data, eff_role, user_dept, target_dept
        )
        areas = DecisionRulesEngine.evaluate_areas_of_attention(
            dept_comparison, student_data, finance_data, research_data
        )
        recs = DecisionRulesEngine.generate_recommendations(areas, dept_comparison)

        query_res = DecisionRulesEngine.match_natural_query(
            query, student_data, finance_data, research_data, dept_comparison, areas, recs
        )

        return DecisionQueryResponse(
            query=query,
            matched_intent=query_res["matched_intent"],
            summary=query_res["summary"],
            findings=query_res["findings"],
            areas_of_attention=query_res["areas_of_attention"],
            recommendations=query_res["recommendations"],
            supporting_metrics=query_res["supporting_metrics"],
        )


decision_service = DecisionService()

from typing import Dict, List, Any, Optional
from backend.decision.schemas import (
    AttentionArea,
    FindingItem,
    RecommendedAction,
    DepartmentComparisonItem,
)


class DecisionRulesEngine:
    """
    Deterministic rule-based cross-module decision intelligence engine.
    Analyzes Student, Finance, and Research indicators without fabricating metrics.
    """

    @staticmethod
    def evaluate_cross_module_findings(
        student_data: Dict[str, Any],
        finance_data: Dict[str, Any],
        research_data: Dict[str, Any],
        dept_comparison: List[DepartmentComparisonItem],
    ) -> List[FindingItem]:
        findings = []

        # 1. Student Findings
        if student_data.get("status") == "available":
            total_students = student_data.get("total_students", 0)
            high_risk = student_data.get("high_risk_students", 0)
            high_risk_pct = student_data.get("high_risk_pct", 0.0)
            avg_risk = student_data.get("avg_dropout_prob", 0.0)
            top_risk_factor = student_data.get("top_risk_factor", "Academic backlog")
            top_risk_dept = student_data.get("top_risk_department", "N/A")

            findings.append(
                FindingItem(
                    domain="student",
                    title="Student Dropout Risk Assessment",
                    description=(
                        f"Out of {total_students:,} total students, {high_risk:,} ({high_risk_pct:.1f}%) "
                        f"are identified as High Risk (probability >= 0.60) by the Logistic Regression model. "
                        f"The average predicted risk probability is {avg_risk * 100:.1f}%. "
                        f"Highest risk department is {top_risk_dept}."
                    ),
                    metric=f"{high_risk_pct:.1f}% High Risk ({high_risk:,} students)",
                    impact="negative" if high_risk_pct > 15.0 else "neutral",
                )
            )

            if top_risk_factor and top_risk_factor != "N/A":
                findings.append(
                    FindingItem(
                        domain="student",
                        title="Primary Learned Dropout Predictors",
                        description=(
                            f"The Logistic Regression model identified '{top_risk_factor}' "
                            f"as one of the strongest features associated with higher predicted dropout risk."
                        ),
                        metric=f"Top Factor: {top_risk_factor}",
                        impact="negative",
                    )
                )

        # 2. Finance Findings
        if finance_data.get("status") == "available":
            budget_util = finance_data.get("budget_utilization_pct", 0.0)
            overrun_count = finance_data.get("overrun_departments_count", 0)
            outstanding_pct = finance_data.get("outstanding_fee_pct", 0.0)

            findings.append(
                FindingItem(
                    domain="finance",
                    title="Institutional Financial & Budget Performance",
                    description=(
                        f"Overall budget utilization stands at {budget_util:.1f}%. "
                        f"{overrun_count} department(s) exceed 100% budget utilization. "
                        f"Outstanding student fees represent {outstanding_pct:.1f}% of total fee obligations."
                    ),
                    metric=f"{budget_util:.1f}% Utilization ({overrun_count} Overruns)",
                    impact="negative" if budget_util > 100.0 or outstanding_pct > 12.0 else "positive",
                )
            )

        # 3. Research Findings
        if research_data.get("status") == "available":
            participation_rate = research_data.get("participation_rate_pct", 0.0)
            total_pubs = research_data.get("total_publications", 0)
            avg_pubs = research_data.get("avg_publications_per_student", 0.0)

            findings.append(
                FindingItem(
                    domain="research",
                    title="Research Productivity & Participation",
                    description=(
                        f"Research participation rate across students is {participation_rate:.1f}%, "
                        f"yielding {total_pubs:,} total academic publications "
                        f"(average {avg_pubs:.2f} publications per student)."
                    ),
                    metric=f"{participation_rate:.1f}% Participation ({total_pubs:,} Publications)",
                    impact="positive" if participation_rate > 50.0 else "neutral",
                )
            )

        return findings

    @staticmethod
    def evaluate_areas_of_attention(
        dept_comparison: List[DepartmentComparisonItem],
        student_data: Dict[str, Any],
        finance_data: Dict[str, Any],
        research_data: Dict[str, Any],
    ) -> List[AttentionArea]:
        areas = []
        area_id = 1

        for dept in dept_comparison:
            # Alert 1: High Student Risk + Financial Stress
            if dept.student_high_risk_pct >= 18.0 and (dept.finance_budget_utilization >= 100.0 or dept.finance_outstanding_fee_pct >= 12.0):
                areas.append(
                    AttentionArea(
                        id=f"ATTN-{area_id:03d}",
                        title=f"Elevated Student Risk & Financial Stress in {dept.department_name}",
                        department=dept.department_name,
                        severity="HIGH" if dept.student_high_risk_pct >= 25.0 else "MEDIUM",
                        observation=(
                            f"{dept.department_name} exhibits both elevated student dropout risk "
                            f"({dept.student_high_risk_pct:.1f}% high risk) and financial pressure "
                            f"(budget utilization {dept.finance_budget_utilization:.1f}%, outstanding fee ratio {dept.finance_outstanding_fee_pct:.1f}%)."
                        ),
                        supporting_metric=f"High Risk: {dept.student_high_risk_pct:.1f}%, Budget Util: {dept.finance_budget_utilization:.1f}%",
                        affected_modules=["Student", "Finance"],
                    )
                )
                area_id += 1

            # Alert 2: High Student Risk + Low Research Activity
            elif dept.student_high_risk_pct >= 18.0 and dept.research_participation_pct < 45.0:
                areas.append(
                    AttentionArea(
                        id=f"ATTN-{area_id:03d}",
                        title=f"High Academic Risk & Low Research Engagement in {dept.department_name}",
                        department=dept.department_name,
                        severity="MEDIUM",
                        observation=(
                            f"Student dropout risk is elevated ({dept.student_high_risk_pct:.1f}%) "
                            f"while student research participation remains low ({dept.research_participation_pct:.1f}%)."
                        ),
                        supporting_metric=f"High Risk: {dept.student_high_risk_pct:.1f}%, Research Part: {dept.research_participation_pct:.1f}%",
                        affected_modules=["Student", "Research"],
                    )
                )
                area_id += 1

            # Alert 3: Critical Budget Overrun
            elif dept.finance_budget_utilization >= 105.0:
                areas.append(
                    AttentionArea(
                        id=f"ATTN-{area_id:03d}",
                        title=f"Budget Overrun Warning in {dept.department_name}",
                        department=dept.department_name,
                        severity="HIGH",
                        observation=(
                            f"Budget utilization in {dept.department_name} has reached {dept.finance_budget_utilization:.1f}%, "
                            f"exceeding approved annual financial allocations."
                        ),
                        supporting_metric=f"Budget Utilization: {dept.finance_budget_utilization:.1f}%",
                        affected_modules=["Finance"],
                    )
                )
                area_id += 1

            # Alert 4: Low Research Participation
            elif dept.research_participation_pct < 40.0 and dept.research_participation_pct > 0.0:
                areas.append(
                    AttentionArea(
                        id=f"ATTN-{area_id:03d}",
                        title=f"Sub-optimal Research Engagement in {dept.department_name}",
                        department=dept.department_name,
                        severity="LOW",
                        observation=(
                            f"Research participation in {dept.department_name} is currently {dept.research_participation_pct:.1f}%, "
                            f"which is below institutional targets."
                        ),
                        supporting_metric=f"Research Participation: {dept.research_participation_pct:.1f}%",
                        affected_modules=["Research"],
                    )
                )
                area_id += 1

        # Sort areas of attention by severity (HIGH > MEDIUM > LOW)
        sev_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        areas.sort(key=lambda a: sev_order.get(a.severity, 3))
        return areas

    @staticmethod
    def generate_recommendations(
        areas_of_attention: List[AttentionArea],
        dept_comparison: List[DepartmentComparisonItem],
    ) -> List[RecommendedAction]:
        recommendations = []
        rec_id = 1

        for area in areas_of_attention:
            if "Student" in area.affected_modules and "Finance" in area.affected_modules:
                recommendations.append(
                    RecommendedAction(
                        id=f"REC-{rec_id:03d}",
                        title=f"Targeted Academic & Fee Payment Relief in {area.department}",
                        target_department=area.department,
                        priority="HIGH",
                        action=(
                            f"Establish specialized academic counseling paired with flexible fee installment plans "
                            f"for high-risk students in {area.department}."
                        ),
                        rationale=(
                            "Financial pending status is a top predictor of student dropout. Combining academic "
                            "support with fee payment relief directly addresses both risk factors."
                        ),
                        supporting_evidence=area.supporting_metric,
                    )
                )
                rec_id += 1
            elif "Finance" in area.affected_modules and area.severity == "HIGH":
                recommendations.append(
                    RecommendedAction(
                        id=f"REC-{rec_id:03d}",
                        title=f"Operational Expenditure Audit for {area.department}",
                        target_department=area.department,
                        priority="HIGH",
                        action=(
                            f"Conduct an immediate line-item budget review for {area.department} to realign spending "
                            f"with allocated fiscal caps."
                        ),
                        rationale="Prevent further fiscal deficits and reallocate unspent contingency funds.",
                        supporting_evidence=area.supporting_metric,
                    )
                )
                rec_id += 1
            elif "Research" in area.affected_modules:
                recommendations.append(
                    RecommendedAction(
                        id=f"REC-{rec_id:03d}",
                        title=f"Faculty-Guided Mentorship & Research Grants in {area.department}",
                        target_department=area.department,
                        priority="MEDIUM",
                        action=(
                            f"Introduce student-faculty research micro-grants and structured mentorship sessions "
                            f"in {area.department} to increase participation."
                        ),
                        rationale=(
                            "Increased research involvement improves student retention and enhances overall "
                            "departmental publication output."
                        ),
                        supporting_evidence=area.supporting_metric,
                    )
                )
                rec_id += 1

        # Generic baseline recommendation if few area-specific recommendations were generated
        if len(recommendations) < 2:
            recommendations.append(
                RecommendedAction(
                    id=f"REC-{rec_id:03d}",
                    title="Institutional Cross-Module Strategy Alignment",
                    target_department="All Departments",
                    priority="MEDIUM",
                    action="Schedule quarterly joint reviews between Academic Deans, Financial Officers, and Research Directors.",
                    rationale="Synchronizing academic intervention and resource allocation ensures holistic institutional growth.",
                    supporting_evidence="Cross-module intelligence synthesis",
                )
            )

        return recommendations

    @staticmethod
    def match_natural_query(
        query: str,
        student_data: Dict[str, Any],
        finance_data: Dict[str, Any],
        research_data: Dict[str, Any],
        dept_comparison: List[DepartmentComparisonItem],
        areas: List[AttentionArea],
        recs: List[RecommendedAction],
    ) -> Dict[str, Any]:
        q_clean = query.strip().lower()

        if any(w in q_clean for w in ["risk", "attention", "urgent", "critical", "problem", "warning"]):
            intent = "Cross-Module High Attention Areas"
            high_sev_areas = [a for a in areas if a.severity in ["HIGH", "MEDIUM"]]
            summary = (
                f"Identified {len(areas)} total department(s) requiring attention across Student, Finance, "
                f"or Research metrics. {len(high_sev_areas)} area(s) are rated High/Medium severity."
            )
            return {
                "matched_intent": intent,
                "summary": summary,
                "findings": [f for f in DecisionRulesEngine.evaluate_cross_module_findings(student_data, finance_data, research_data, dept_comparison)],
                "areas_of_attention": areas,
                "recommendations": recs,
                "supporting_metrics": {
                    "total_attention_areas": len(areas),
                    "high_severity_count": len([a for a in areas if a.severity == "HIGH"]),
                },
            }

        elif any(w in q_clean for w in ["student", "dropout", "gpa", "academic", "backlog"]):
            intent = "Student Success & Dropout Risk Analysis"
            high_risk_pct = student_data.get("high_risk_pct", 0.0)
            high_risk_count = student_data.get("high_risk_students", 0)
            top_dept = student_data.get("top_risk_department", "N/A")

            summary = (
                f"Student dropout analysis reveals {high_risk_count:,} high-risk students ({high_risk_pct:.1f}% of total). "
                f"The department with the highest predicted risk is {top_dept}."
            )
            student_findings = [f for f in DecisionRulesEngine.evaluate_cross_module_findings(student_data, finance_data, research_data, dept_comparison) if f.domain == "student"]
            student_recs = [r for r in recs if "Student" in r.title or "Academic" in r.title]

            return {
                "matched_intent": intent,
                "summary": summary,
                "findings": student_findings,
                "areas_of_attention": [a for a in areas if "Student" in a.affected_modules],
                "recommendations": student_recs if student_recs else recs[:2],
                "supporting_metrics": student_data,
            }

        elif any(w in q_clean for w in ["finance", "budget", "fee", "expense", "revenue"]):
            intent = "Financial Health & Budget Utilization Analysis"
            budget_util = finance_data.get("budget_utilization_pct", 0.0)
            overruns = finance_data.get("overrun_departments_count", 0)
            out_pct = finance_data.get("outstanding_fee_pct", 0.0)

            summary = (
                f"Financial health check indicates overall budget utilization of {budget_util:.1f}%. "
                f"{overruns} department(s) report budget overruns, and outstanding fees represent {out_pct:.1f}%."
            )
            fin_findings = [f for f in DecisionRulesEngine.evaluate_cross_module_findings(student_data, finance_data, research_data, dept_comparison) if f.domain == "finance"]

            return {
                "matched_intent": intent,
                "summary": summary,
                "findings": fin_findings,
                "areas_of_attention": [a for a in areas if "Finance" in a.affected_modules],
                "recommendations": [r for r in recs if "Audit" in r.title or "Fee" in r.title or "Finance" in r.title],
                "supporting_metrics": finance_data,
            }

        elif any(w in q_clean for w in ["research", "publication", "grant", "faculty", "paper"]):
            intent = "Research Activity & Publication Productivity"
            part_pct = research_data.get("participation_rate_pct", 0.0)
            pubs = research_data.get("total_publications", 0)

            summary = (
                f"Research productivity assessment: {part_pct:.1f}% student research participation "
                f"yielding {pubs:,} total academic publications."
            )
            res_findings = [f for f in DecisionRulesEngine.evaluate_cross_module_findings(student_data, finance_data, research_data, dept_comparison) if f.domain == "research"]

            return {
                "matched_intent": intent,
                "summary": summary,
                "findings": res_findings,
                "areas_of_attention": [a for a in areas if "Research" in a.affected_modules],
                "recommendations": [r for r in recs if "Research" in r.title or "Grant" in r.title],
                "supporting_metrics": research_data,
            }

        else:
            intent = "General Institutional Executive Overview"
            summary = (
                f"Synthesized cross-module institutional intelligence across Student, Finance, and Research domains. "
                f"Student High Risk: {student_data.get('high_risk_pct', 0.0):.1f}%, Budget Utilization: {finance_data.get('budget_utilization_pct', 0.0):.1f}%, "
                f"Research Participation: {research_data.get('participation_rate_pct', 0.0):.1f}%."
            )
            return {
                "matched_intent": intent,
                "summary": summary,
                "findings": DecisionRulesEngine.evaluate_cross_module_findings(student_data, finance_data, research_data, dept_comparison),
                "areas_of_attention": areas,
                "recommendations": recs,
                "supporting_metrics": {
                    "student_high_risk_pct": student_data.get("high_risk_pct", 0.0),
                    "budget_utilization_pct": finance_data.get("budget_utilization_pct", 0.0),
                    "research_participation_pct": research_data.get("participation_rate_pct", 0.0),
                },
            }

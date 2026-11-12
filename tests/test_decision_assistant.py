from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.decision import router as decision_router
from backend.decision.rules import classify_query
from backend.decision.schemas import (
    DecisionOverviewResponse,
    DecisionQueryResponse,
    DepartmentComparisonItem,
    EvidenceSummary,
    FinanceEvidence,
    ResearchEvidence,
    ScopeInfo,
    StudentEvidence,
)
from backend.decision.service import DecisionService
from backend.student.service import student_service


def test_query_intents_cover_supported_examples():
    examples = {
        "Which department has the highest dropout risk?": "student_department_risk",
        "How many students are classified as high risk?": "student_high_risk",
        "What are the most important student dropout predictors?": "student_predictors",
        "Which departments have the highest student risk percentage?": "student_department_risk",
        "What is the student dropout risk distribution?": "student_distribution",
        "Which departments have exceeded their budgets?": "finance_overrun",
        "Where is financial pressure highest?": "finance_pressure",
        "What is the total outstanding fee amount?": "finance_outstanding",
        "Which departments have the highest fee collection rate?": "finance_collection",
        "Compare budget utilization across departments.": "finance_utilization",
        "Which department has the highest faculty publication output?": "research_department_publications",
        "Which department has the highest average faculty publications?": "research_department_average",
        "Which department is most productive by average publications?": "research_department_average",
        "Which department has the highest publications?": "research_department_publications",
        "What is the average number of publications per faculty?": "research_average",
        "Which faculty members have the highest publication counts?": "research_top_faculty",
        "How does research participation vary by department?": "research_participation",
        "What are the publication trends across academic years?": "research_trends",
        "Which departments require the most attention?": "cross_attention",
        "Give me an institutional performance summary.": "cross_summary",
        "Compare student risk and financial performance.": "cross_compare",
        "Which departments have weak performance across multiple modules?": "cross_weak_departments",
        "Which students in CSE are at high risk of dropping out?": "student_high_risk_students",
        "What percentage of CSE students are classified as high risk?": "student_high_risk",
        "How many CSE students are at high risk?": "student_high_risk",
        "What are the major factors contributing to student dropout risk in CSE?": "student_predictors",
        "Has CSE exceeded its allocated budget?": "finance_overrun",
        "What is CSE's current budget utilization?": "finance_utilization",
        "How much outstanding fee revenue does CSE have?": "finance_outstanding",
        "What is CSE's total expenditure?": "finance_expenditure",
        "How many active faculty members are in CSE?": "research_faculty_count",
        "What is the total faculty publication count in CSE?": "research_total_publications",
        "What is the average number of publications per active faculty member in CSE?": "research_average",
        "What is CSE's faculty research participation rate?": "research_participation",
        "Which areas of CSE require immediate attention?": "cross_attention",
        "Give me an overall performance summary of CSE.": "cross_summary",
        "What are the top three priorities for CSE?": "cross_priorities",
    }

    for query, expected_intent in examples.items():
        assert classify_query(query) == expected_intent, query


def test_student_department_risk_answer_uses_current_evidence():
    data = DecisionOverviewResponse(
        scope=ScopeInfo(role="ADMINISTRATOR", department="All accessible departments"),
        summary="Current data.",
        evidence=EvidenceSummary(
            student=StudentEvidence(
                status="available",
                total_students=100,
                high_risk_students=20,
                high_risk_pct=20,
            ),
            finance=FinanceEvidence(status="unavailable"),
            research=ResearchEvidence(status="unavailable"),
            department_comparison=[
                DepartmentComparisonItem(
                    department="BIO",
                    student_total=10,
                    student_high_risk=4,
                    student_high_risk_pct=40,
                ),
                DepartmentComparisonItem(
                    department="CSE",
                    student_total=90,
                    student_high_risk=16,
                    student_high_risk_pct=17.78,
                ),
            ],
        ),
    )

    answer, _, metrics = DecisionService()._query_answer("student_department_risk", data)

    assert "BIO" in answer
    assert "40.0%" in answer
    assert metrics["high_risk_students"] == 4
    assert metrics["total_students"] == 10


def test_unavailable_module_is_not_reported_as_zero():
    data = DecisionOverviewResponse(
        scope=ScopeInfo(role="ADMINISTRATOR", department="All accessible departments"),
        summary="Finance unavailable.",
        evidence=EvidenceSummary(
            student=StudentEvidence(status="unavailable"),
            finance=FinanceEvidence(status="unavailable"),
            research=ResearchEvidence(status="unavailable"),
        ),
    )

    answer, _, metrics = DecisionService()._query_answer("finance_outstanding", data)

    assert "unavailable" in answer
    assert "outstanding_fees" not in metrics


def test_total_and_average_faculty_publications_can_have_different_winners():
    data = DecisionOverviewResponse(
        scope=ScopeInfo(role="ADMINISTRATOR", department="All accessible departments"),
        summary="Current data.",
        evidence=EvidenceSummary(
            student=StudentEvidence(status="not_requested"),
            finance=FinanceEvidence(status="not_requested"),
            research=ResearchEvidence(
                status="available",
                total_faculty=42,
                total_publications=373,
                average_publications_per_faculty=8.88,
                departments=[
                    {
                        "department": "CE",
                        "publications": 82,
                        "total_faculty": 11,
                        "average_publications_per_faculty": 7.45,
                    },
                    {
                        "department": "Biotech",
                        "publications": 76,
                        "total_faculty": 11,
                        "average_publications_per_faculty": 6.91,
                    },
                    {
                        "department": "MBA",
                        "publications": 76,
                        "total_faculty": 10,
                        "average_publications_per_faculty": 7.60,
                    },
                    {
                        "department": "ME",
                        "publications": 73,
                        "total_faculty": 10,
                        "average_publications_per_faculty": 7.30,
                    },
                    {
                        "department": "ECE",
                        "publications": 66,
                        "total_faculty": 11,
                        "average_publications_per_faculty": 6.00,
                    },
                ],
            ),
        ),
    )

    total_answer, _, total_metrics = DecisionService()._query_answer(
        "research_department_publications", data
    )
    average_answer, _, average_metrics = DecisionService()._query_answer(
        "research_department_average", data
    )

    assert "CE has the highest faculty publication output" in total_answer
    assert "MBA has the highest average faculty publication output" in average_answer
    assert average_metrics["departments"][0] == {
        "department": "MBA",
        "total_publications": 76,
        "active_faculty": 10,
        "average_publications_per_faculty": 7.6,
    }
    assert total_metrics["departments"][0]["department"] == "CE"
    assert "faculty_rating" not in average_metrics["departments"][0]
    assert "research_grants" not in average_metrics["departments"][0]


def test_faculty_participation_returns_only_relevant_department_metrics():
    data = DecisionOverviewResponse(
        scope=ScopeInfo(role="ADMINISTRATOR", department="All accessible departments"),
        summary="Current data.",
        evidence=EvidenceSummary(
            student=StudentEvidence(status="not_requested"),
            finance=FinanceEvidence(status="not_requested"),
            research=ResearchEvidence(
                status="available",
                departments=[
                    {
                        "department": "CSE",
                        "total_faculty": 10,
                        "faculty_researchers": 7,
                        "participation_rate": 70,
                        "publications": 50,
                        "total_citations": 100,
                        "research_grants": 50000,
                        "average_faculty_rating": 4.5,
                    }
                ],
            ),
        ),
    )

    _, _, metrics = DecisionService()._query_answer("research_participation", data)

    assert metrics["departments"] == [{
        "department": "CSE",
        "participating_faculty": 7,
        "total_active_faculty": 10,
        "participation_pct": 70,
    }]


def test_zero_publication_active_faculty_remains_in_average_denominator(monkeypatch):
    seen = {}
    faculty_overview = SimpleNamespace(
        total_faculty=10,
        faculty_researchers=8,
        total_publications=76,
        average_publications_per_faculty=7.6,
        faculty_participation_rate=80,
        total_citations=0,
        total_research_grants=0,
        is_synthetic=False,
    )
    service_response = SimpleNamespace(
        overview=faculty_overview,
        departments=[{
            "department": "MBA",
            "total_faculty": 10,
            "faculty_researchers": 8,
            "publications": 76,
            "average_publications_per_faculty": 7.6,
            "participation_rate": 80,
            "total_citations": 0,
            "research_grants": 0,
            "faculty_rating_count": 0,
            "mentorship_score_count": 0,
        }],
        publication_trends=[],
        top_researchers=[],
    )
    monkeypatch.setattr(
        "backend.decision.service.research_service.get_faculty_analytics",
        lambda **kwargs: seen.update(kwargs) or service_response,
    )

    evidence = DecisionService()._get_research_evidence("MBA", None, "jwt")

    assert evidence["status"] == "available"
    assert evidence["departments"][0]["total_faculty"] == 10
    assert evidence["departments"][0]["faculty_researchers"] == 8
    assert evidence["departments"][0]["publications"] == 76
    assert evidence["departments"][0]["average_publications_per_faculty"] == 7.6


def test_hod_research_scope_uses_dashboard_period_and_active_faculty_denominator(monkeypatch):
    seen = {}
    overview = SimpleNamespace(
        total_faculty=11,
        faculty_researchers=9,
        total_publications=58,
        average_publications_per_faculty=round(58 / 11, 2),
        faculty_participation_rate=round(9 / 11 * 100, 2),
        total_citations=0,
        total_research_grants=0,
        is_synthetic=False,
    )
    response = SimpleNamespace(
        overview=overview,
        departments=[{
            "department": "CSE",
            "total_faculty": 11,
            "faculty_researchers": 9,
            "publications": 58,
            "average_publications_per_faculty": round(58 / 11, 2),
            "participation_rate": round(9 / 11 * 100, 2),
        }],
        publication_trends=[],
        top_researchers=[],
    )
    monkeypatch.setattr(
        "backend.decision.service.research_service.get_faculty_analytics",
        lambda **kwargs: seen.update(kwargs) or response,
    )

    evidence = DecisionService()._get_research_evidence("CSE", "2024", "verified-token")

    assert seen == {
        "department": "CSE",
        "academic_year": "2024-25",
        "access_token": "verified-token",
    }
    assert evidence["total_publications"] == 58
    assert evidence["total_faculty"] == 11
    assert evidence["average_publications_per_faculty"] == 5.27


def test_finance_evidence_normalizes_year_and_calculates_utilization_from_amounts(monkeypatch):
    seen = {}
    overview = SimpleNamespace(
        total_budget=290,
        actual_expenditure=300,
        outstanding_fees=100,
        fee_collection_rate=80,
    )
    department_response = SimpleNamespace(departments=[{
        "department_id": "CSE",
        "allocated_budget": 290,
        "actual_expenditure": 300,
        "budget_utilization": 0,
    }])

    def get_overview(**kwargs):
        seen["overview"] = kwargs
        return overview

    def get_departments(**kwargs):
        seen["departments"] = kwargs
        return department_response

    monkeypatch.setattr("backend.decision.service.finance_service.get_overview", get_overview)
    monkeypatch.setattr("backend.decision.service.finance_service.get_departments", get_departments)

    evidence = DecisionService()._get_finance_evidence("CSE", "2024", None)

    assert seen["overview"]["academic_year"] == "2024-2025"
    assert seen["departments"]["academic_year"] == "2024-2025"
    assert evidence["budget_utilization_pct"] == round(300 / 290 * 100, 2)
    assert evidence["departments"][0]["budget_utilization"] == round(300 / 290 * 100, 2)
    assert evidence["overrun_departments_count"] == 1


def test_zero_budget_is_not_reported_as_zero_utilization(monkeypatch):
    monkeypatch.setattr(
        "backend.decision.service.finance_service.get_overview",
        lambda **kwargs: SimpleNamespace(
            total_budget=0, actual_expenditure=0, outstanding_fees=0, fee_collection_rate=0
        ),
    )
    monkeypatch.setattr(
        "backend.decision.service.finance_service.get_departments",
        lambda **kwargs: SimpleNamespace(departments=[{
            "department_id": "CSE",
            "allocated_budget": 0,
            "actual_expenditure": 0,
            "budget_utilization": 0,
        }]),
    )

    evidence = DecisionService()._get_finance_evidence("CSE", None, None)

    assert evidence["status"] == "available"
    assert evidence["budget_utilization_pct"] is None
    assert evidence["departments"][0]["budget_utilization"] is None

    data = DecisionOverviewResponse(
        scope=ScopeInfo(role="HOD", department="CSE"),
        summary="Current data.",
        evidence=EvidenceSummary(
            student=StudentEvidence(status="not_requested"),
            finance=FinanceEvidence(**evidence),
            research=ResearchEvidence(status="not_requested"),
        ),
    )
    answer, _, _ = DecisionService()._query_answer("finance_overrun", data)
    assert "unavailable" in answer


def test_empty_finance_response_is_unavailable_not_a_zero_budget(monkeypatch):
    monkeypatch.setattr(
        "backend.decision.service.finance_service.get_overview",
        lambda **kwargs: SimpleNamespace(
            total_budget=0, actual_expenditure=0, outstanding_fees=0, fee_collection_rate=0
        ),
    )
    monkeypatch.setattr(
        "backend.decision.service.finance_service.get_departments",
        lambda **kwargs: SimpleNamespace(departments=[]),
    )

    evidence = DecisionService()._get_finance_evidence("CSE", None, None)

    assert evidence["status"] == "unavailable"
    assert evidence["total_budget"] is None
    assert evidence["budget_utilization_pct"] is None


def test_hod_scoped_query_answers_only_relevant_student_finance_and_research_metrics():
    data = DecisionOverviewResponse(
        scope=ScopeInfo(role="HOD", department="CSE", academic_year="2024"),
        summary="Current data.",
        evidence=EvidenceSummary(
            student=StudentEvidence(
                status="available",
                total_students=3232,
                high_risk_students=1146,
                high_risk_pct=35.46,
            ),
            finance=FinanceEvidence(
                status="available",
                total_spent=300,
                total_budget=290,
                budget_utilization_pct=round(300 / 290 * 100, 2),
                departments=[{
                    "department_id": "CSE",
                    "budget_utilization": round(300 / 290 * 100, 2),
                    "allocated_budget": 290,
                    "actual_expenditure": 300,
                }],
            ),
            research=ResearchEvidence(
                status="available",
                total_faculty=11,
                faculty_researchers=9,
                total_publications=58,
                average_publications_per_faculty=5.27,
                participation_rate_pct=round(9 / 11 * 100, 2),
            ),
        ),
    )
    service = DecisionService()

    student_answer, _, student_metrics = service._query_answer("student_high_risk", data)
    finance_answer, _, finance_metrics = service._query_answer("finance_overrun", data)
    faculty_answer, _, faculty_metrics = service._query_answer("research_average", data)
    count_answer, _, count_metrics = service._query_answer("research_faculty_count", data)

    assert "1,146 of 3,232 students in CSE (35.5%)" in student_answer
    assert set(student_metrics) == {
        "high_risk_students", "total_students", "high_risk_percentage"
    }
    assert "CSE has exceeded its allocated budget" in finance_answer
    assert set(finance_metrics["overrun_departments"][0]) == {
        "department", "budget_utilization_pct", "allocated_budget", "actual_expenditure"
    }
    assert "5.27 per active faculty member" in faculty_answer
    assert set(faculty_metrics) == {
        "publications", "active_faculty", "average_publications_per_faculty"
    }
    assert "11 active faculty" in count_answer
    assert count_metrics == {"active_faculty": 11}


def test_hod_high_risk_student_list_uses_authenticated_department_scope(monkeypatch):
    seen = {}
    data = DecisionOverviewResponse(
        scope=ScopeInfo(role="HOD", department="CSE", academic_year="2024"),
        summary="Current data.",
        evidence=EvidenceSummary(
            student=StudentEvidence(status="available"),
            finance=FinanceEvidence(status="not_requested"),
            research=ResearchEvidence(status="not_requested"),
        ),
    )
    service = DecisionService()
    monkeypatch.setattr(service, "get_decision_overview", lambda **kwargs: data)

    def get_filtered_students(**kwargs):
        seen.update(kwargs)
        return SimpleNamespace(
            total_students=1146,
            students=[SimpleNamespace(
                student_id="CSE-001",
                risk_level="HIGH",
                dropout_probability=0.82,
            )],
        )

    monkeypatch.setattr(
        "backend.decision.service.student_service.get_filtered_students",
        get_filtered_students,
    )

    result = service.execute_natural_query(
        "Which students in CSE are at high risk of dropping out?",
        role="HOD",
        user_dept="CSE",
        department="ECE",
        academic_year="2024",
    )

    assert seen["department"] == "CSE"
    assert seen["user_dept"] == "CSE"
    assert seen["risk_level"] == "HIGH"
    assert seen["academic_year"] == 2024
    assert result.supporting_metrics["total_matching_students"] == 1146
    assert result.supporting_metrics["students"] == [{
        "student_id": "CSE-001",
        "risk_level": "HIGH",
        "dropout_probability": 0.82,
    }]
    assert "Showing 1 of 1,146" in result.summary


def test_unsupported_query_has_no_parser_internals():
    result = DecisionService().execute_natural_query("Tell me a joke")

    assert result.matched_intent == "unsupported"
    assert "could not match" in result.summary
    assert result.supporting_metrics == {}


def test_department_comparison_normalizes_department_names_across_modules():
    comparison = DecisionService._build_department_comparison(
        student={
            "department_chart": [{
                "department_id": "BT",
                "total_students": 100,
                "high_risk_count": 20,
            }]
        },
        finance={"departments": [{"department_id": "BT", "budget_utilization": 105}]},
        research={"departments": [{
            "department": "Biotech",
            "total_faculty": 10,
            "publications": 30,
            "average_publications_per_faculty": 3,
            "participation_rate": 60,
        }]},
        role="ADMINISTRATOR",
        user_dept=None,
        department=None,
    )

    assert len(comparison) == 1
    assert comparison[0].department == "BT"
    assert comparison[0].research_publications == 30


def test_invalid_academic_year_is_rejected_instead_of_removing_filter():
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as error:
        DecisionService().get_decision_overview(academic_year="not-a-year")

    assert error.value.status_code == 422


def test_finance_overrun_summary_and_result_list_are_complete():
    rows = [
        {
            "department_id": f"D{index}",
            "budget_utilization": 100 + index,
            "allocated_budget": 1000 * index,
            "actual_expenditure": 1000 * index + 10,
        }
        for index in range(1, 8)
    ]
    data = DecisionOverviewResponse(
        scope=ScopeInfo(role="ADMINISTRATOR", department="All accessible departments"),
        summary="Current data.",
        evidence=EvidenceSummary(
            student=StudentEvidence(status="not_requested"),
            finance=FinanceEvidence(status="available", departments=rows),
            research=ResearchEvidence(status="not_requested"),
        ),
    )

    summary, _, metrics = DecisionService()._query_answer("finance_overrun", data)
    results = metrics["overrun_departments"]

    assert "7 department(s)" in summary
    assert len(results) == 7
    assert [row["department"] for row in results] == [f"D{index}" for index in range(7, 0, -1)]
    assert set(results[0]) == {
        "department",
        "budget_utilization_pct",
        "allocated_budget",
        "actual_expenditure",
    }


def test_cross_module_attention_uses_student_and_finance_signals_only():
    data = DecisionOverviewResponse(
        scope=ScopeInfo(role="ADMINISTRATOR", department="All accessible departments"),
        summary="Current data.",
        evidence=EvidenceSummary(
            student=StudentEvidence(status="available"),
            finance=FinanceEvidence(status="available"),
            research=ResearchEvidence(status="available"),
            department_comparison=[
                DepartmentComparisonItem(
                    department="A",
                    student_high_risk_pct=40,
                    finance_budget_utilization_pct=105,
                    research_participation_pct=95,
                ),
                DepartmentComparisonItem(
                    department="B",
                    student_high_risk_pct=20,
                    finance_budget_utilization_pct=90,
                    research_participation_pct=10,
                ),
                DepartmentComparisonItem(
                    department="C",
                    student_high_risk_pct=10,
                    finance_budget_utilization_pct=101,
                    research_participation_pct=50,
                ),
            ],
        ),
    )

    answer, _, metrics = DecisionService()._query_answer("cross_weak_departments", data)

    assert [row["department"] for row in metrics["departments"]] == ["A"]
    assert metrics["departments"][0]["signals"] == [
        "student high-risk share above scoped median",
        "budget utilization above 100% (overrun)",
    ]
    assert "95.0% as context" in answer
    assert "research_participation" in metrics["attention_criteria"]
    assert "Context only" in metrics["attention_criteria"]["research_participation"]
    assert "Both student-risk and financial-overrun signals" in metrics["attention_criteria"]["department_qualifies"]


def test_hod_and_admin_student_results_match_for_same_department_and_filters():
    filters = {"department": "CSE", "academic_year": None, "semester": None}
    admin = student_service.get_admin_overview(
        role="ADMINISTRATOR", user_dept=None, **filters
    )
    hod = student_service.get_admin_overview(
        role="HOD", user_dept="CSE", **filters
    )

    assert hod.total_students == admin.total_students
    assert hod.high_risk_count == admin.high_risk_count
    assert hod.medium_risk_count == admin.medium_risk_count
    assert hod.low_risk_count == admin.low_risk_count
    assert hod.average_gpa == admin.average_gpa
    assert hod.average_attendance == admin.average_attendance


def test_budget_overrun_is_strictly_greater_than_one_hundred_percent():
    data = DecisionOverviewResponse(
        scope=ScopeInfo(role="ADMINISTRATOR", department="All accessible departments"),
        summary="Current data.",
        evidence=EvidenceSummary(
            student=StudentEvidence(status="not_requested"),
            finance=FinanceEvidence(status="available", departments=[{
                "department_id": "CSE",
                "budget_utilization": 100,
                "allocated_budget": 100,
                "actual_expenditure": 100,
            }]),
            research=ResearchEvidence(status="not_requested"),
        ),
    )

    answer, _, metrics = DecisionService()._query_answer("finance_overrun", data)

    assert "has not exceeded" in answer
    assert metrics["overrun_departments"] == []


def test_hod_attention_does_not_flag_single_department_risk_as_above_median():
    data = DecisionOverviewResponse(
        scope=ScopeInfo(role="HOD", department="CSE"),
        summary="Current data.",
        evidence=EvidenceSummary(
            student=StudentEvidence(
                status="available",
                total_students=100,
                high_risk_students=35,
                high_risk_pct=35,
            ),
            finance=FinanceEvidence(status="available"),
            research=ResearchEvidence(status="available"),
            department_comparison=[DepartmentComparisonItem(
                department="CSE",
                student_total=100,
                student_high_risk=35,
                student_high_risk_pct=35,
                finance_budget_utilization_pct=100,
                research_participation_pct=90,
            )],
        ),
    )

    answer, _, metrics = DecisionService()._query_answer("cross_attention", data)

    assert "No attention signals" in answer
    assert metrics["departments"] == []
    assert metrics["scope_student_risk_context"]["high_risk_percentage"] == 35
    assert "No cross-department median comparison" in metrics["scope_student_risk_context"]["note"]
    assert "Context only" in metrics["attention_criteria"]["research_participation"]


def test_query_only_fetches_the_classified_module(monkeypatch):
    calls = []
    service = DecisionService()
    monkeypatch.setattr(
        service,
        "_get_student_evidence",
        lambda *args: calls.append("student") or {
            "status": "available",
            "total_students": 30,
            "high_risk_students": 5,
            "high_risk_pct": 16.67,
            "medium_risk_students": 10,
            "low_risk_students": 15,
            "avg_dropout_prob": 0.2,
            "top_risk_department": "CSE",
            "top_risk_department_pct": 16.67,
            "top_risk_factor": None,
            "department_chart": [],
        },
    )
    monkeypatch.setattr(
        service,
        "_get_finance_evidence",
        lambda *args: calls.append("finance") or {"status": "unavailable"},
    )
    monkeypatch.setattr(
        service,
        "_get_research_evidence",
        lambda *args: calls.append("research") or {"status": "unavailable"},
    )

    result = service.execute_natural_query(
        "How many students are classified as high risk?"
    )

    assert calls == ["student"]
    assert "5 of 30 students" in result.summary


def test_hod_scope_and_verified_token_are_forwarded_to_module_services(monkeypatch):
    seen = {}
    overview = SimpleNamespace(
        total_students=0,
        high_risk_count=0,
        medium_risk_count=0,
        low_risk_count=0,
        average_dropout_probability=0,
        department_chart=[],
    )

    def get_student_overview(**kwargs):
        seen["student"] = kwargs
        return overview

    def get_faculty_analytics(**kwargs):
        seen["research"] = kwargs
        raise RuntimeError("research unavailable")

    monkeypatch.setattr(
        "backend.decision.service.student_service.get_admin_overview",
        get_student_overview,
    )
    monkeypatch.setattr(
        "backend.decision.service.student_service.get_model_insights",
        lambda: None,
    )
    monkeypatch.setattr(
        "backend.decision.service.finance_service.get_overview",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("finance unavailable")),
    )
    monkeypatch.setattr(
        "backend.decision.service.research_service.get_faculty_analytics",
        get_faculty_analytics,
    )

    DecisionService().get_decision_overview(
        role="HOD",
        user_dept="CSE",
        department="ECE",
        academic_year="2024",
        access_token="verified-token",
    )

    assert seen["student"]["department"] == "CSE"
    assert seen["research"]["department"] == "CSE"
    assert seen["research"]["access_token"] == "verified-token"


def test_query_route_enforces_hod_department_and_forwards_auth_token(monkeypatch):
    seen = {}

    def execute_query(**kwargs):
        seen.update(kwargs)
        return DecisionQueryResponse(
            query=kwargs["query"],
            matched_intent="student_high_risk",
            summary="Current evidence answer.",
        )

    monkeypatch.setattr(decision_router.decision_service, "execute_natural_query", execute_query)
    app = FastAPI()
    app.include_router(decision_router.router)

    with TestClient(app, headers={"Authorization": "Bearer valid.token.value"}) as client:
        response = client.get(
            "/api/decision/query",
            params={
                "q": "How many ECE students are classified as high risk?",
                "department": "ECE",
                "academic_year": "2024",
            },
        )

    assert response.status_code == 200
    assert seen["role"] == "HOD"
    assert seen["user_dept"] == "CSE"
    assert seen["department"] == "CSE"
    assert seen["academic_year"] == "2024"
    assert seen["access_token"] == "valid.token.value"

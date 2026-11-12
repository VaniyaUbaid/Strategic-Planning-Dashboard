from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from backend.main import app
from backend.common import supabase_client
from backend.research import router as research_router_module
from backend.research.schemas import (
    FacultyResearchAnalyticsResponse,
    FacultyResearchDepartment,
    FacultyResearchOverview,
)
from backend.research.service import (
    ResearchAccessError,
    ResearchDataError,
    ResearchService,
)


class FixtureQuery:
    def __init__(self, rows):
        self.rows = rows
        self.start = 0
        self.end = 999

    def select(self, *_args, **_kwargs):
        return self

    def ilike(self, *_args, **_kwargs):
        return self

    def in_(self, *_args, **_kwargs):
        return self

    def range(self, start, end):
        self.start = start
        self.end = end
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows[self.start : self.end + 1])


class FixtureSupabaseClient:
    def __init__(self):
        self.tables = {
            "research_faculty": [
                {"faculty_id": "a", "faculty_name": "A Faculty", "department": "CSE", "is_active": True, "is_synthetic": True},
                {"faculty_id": "b", "faculty_name": "B Faculty", "department": "CSE", "is_active": True, "is_synthetic": True},
                {"faculty_id": "c", "faculty_name": "C Faculty", "department": "CSE", "is_active": True, "is_synthetic": True},
                {"faculty_id": "d", "faculty_name": "D Faculty", "department": "ECE", "is_active": True, "is_synthetic": True},
                {"faculty_id": "inactive", "faculty_name": "Inactive Faculty", "department": "CSE", "is_active": False, "is_synthetic": True},
            ],
            "faculty_research_records": [
                {"id": "a1", "faculty_id": "a", "academic_year": "2023-24", "publications": 2, "citations": 4, "research_grants": 100, "faculty_rating": 4, "mentorship_score": 5, "is_synthetic": True},
                {"id": "a2", "faculty_id": "a", "academic_year": "2024-25", "publications": 1, "citations": 3, "research_grants": 0, "faculty_rating": 3, "mentorship_score": 4, "is_synthetic": True},
                {"id": "b1", "faculty_id": "b", "academic_year": "2023-24", "publications": 0, "citations": 0, "research_grants": 0, "faculty_rating": None, "mentorship_score": 2, "is_synthetic": True},
                {"id": "d1", "faculty_id": "d", "academic_year": "2023-24", "publications": 10, "citations": 20, "research_grants": 500, "faculty_rating": 5, "mentorship_score": 5, "is_synthetic": True},
                {"id": "i1", "faculty_id": "inactive", "academic_year": "2023-24", "publications": 10, "citations": 20, "research_grants": 500, "faculty_rating": 5, "mentorship_score": 5, "is_synthetic": True},
            ],
        }

    def table(self, name):
        return FixtureQuery(self.tables[name])


class SupabasePermissionError(Exception):
    code = "42501"


class DeniedQuery:
    def select(self, *_args, **_kwargs):
        return self

    def range(self, *_args, **_kwargs):
        return self

    def execute(self):
        raise SupabasePermissionError()


class DeniedSupabaseClient:
    def table(self, _name):
        return DeniedQuery()


def test_faculty_kpis_use_all_active_faculty_and_distinct_denominators(monkeypatch):
    client = FixtureSupabaseClient()
    monkeypatch.setattr(
        "backend.research.service.get_supabase_client_for_access_token",
        lambda _token: client,
    )

    result = ResearchService().get_faculty_analytics(department="CSE")

    assert result.overview.total_faculty == 3
    assert result.overview.faculty_researchers == 1
    assert result.overview.publishing_faculty_count == 1
    assert result.overview.total_publications == 3
    assert result.overview.average_publications_per_faculty == 1.0
    assert result.overview.faculty_participation_rate == 33.33
    assert result.overview.total_citations == 7
    assert result.overview.average_citations_per_faculty == 2.33
    assert result.overview.average_citations_per_publishing_faculty == 7.0
    assert result.overview.total_research_grants == 100
    assert result.overview.average_faculty_rating == 3.5
    assert result.overview.faculty_rating_count == 2
    assert result.overview.average_mentorship_score == 3.67
    assert result.overview.mentorship_score_count == 3
    assert [item.department for item in result.departments] == ["CSE"]
    assert result.departments[0].total_faculty == 3
    assert result.departments[0].average_publications_per_faculty == 1.0
    assert result.publication_trends[0].academic_year == "2023-24"
    assert [
        (trend.department, trend.academic_year, trend.publications)
        for trend in result.department_publication_trends
    ] == [
        ("CSE", "2023-24", 2),
        ("CSE", "2024-25", 1),
    ]
    assert result.top_researchers[0].faculty_id == "a"
    assert result.is_synthetic is True


def test_faculty_year_filter_keeps_active_zero_output_faculty_in_denominator(monkeypatch):
    monkeypatch.setattr(
        "backend.research.service.get_supabase_client_for_access_token",
        lambda _token: FixtureSupabaseClient(),
    )

    result = ResearchService().get_faculty_analytics(
        department="CSE",
        academic_year="2023-24",
    )

    assert result.overview.total_faculty == 3
    assert result.overview.total_publications == 2
    assert result.overview.average_publications_per_faculty == 0.67
    assert result.overview.faculty_researchers == 1
    assert result.overview.faculty_participation_rate == 33.33
    assert len(result.publication_trends) == 1
    assert result.publication_trends[0].academic_year == "2023-24"
    assert [
        (trend.department, trend.academic_year, trend.publications)
        for trend in result.department_publication_trends
    ] == [
        ("CSE", "2023-24", 2),
    ]


def test_faculty_analytics_rejects_invalid_academic_year(monkeypatch):
    called = False

    def fail_if_called(_token):
        nonlocal called
        called = True
        raise AssertionError("Database must not be queried for an invalid year")

    monkeypatch.setattr(
        "backend.research.service.get_supabase_client_for_access_token",
        fail_if_called,
    )
    with pytest.raises(ResearchDataError, match="Academic year must use the YYYY-YY format."):
        ResearchService().get_faculty_analytics(academic_year="2024")
    assert not called


def test_faculty_analytics_does_not_treat_missing_counts_as_zero(monkeypatch):
    client = FixtureSupabaseClient()
    client.tables["faculty_research_records"][0]["publications"] = None
    monkeypatch.setattr(
        "backend.research.service.get_supabase_client_for_access_token",
        lambda _token: client,
    )

    with pytest.raises(ResearchDataError, match="invalid publications value"):
        ResearchService().get_faculty_analytics(department="CSE")


def test_faculty_analytics_preserves_access_denied_as_distinct_error(monkeypatch):
    monkeypatch.setattr(
        "backend.research.service.get_supabase_client_for_access_token",
        lambda _token: DeniedSupabaseClient(),
    )

    with pytest.raises(ResearchAccessError):
        ResearchService().get_faculty_analytics(access_token="valid.token.value")


def test_request_scoped_client_uses_synchronous_sdk_options(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        supabase_client,
        "get_supabase_config",
        lambda: ("https://project.supabase.co", "server-key"),
    )

    def create_client(url, key, options):
        captured.update(url=url, key=key, options=options)
        return object()

    monkeypatch.setattr(supabase_client, "create_client", create_client)
    supabase_client.get_supabase_client_for_access_token("test-access-token")

    assert captured["url"] == "https://project.supabase.co"
    assert captured["key"] == "server-key"
    assert captured["options"].storage is not None
    assert captured["options"].headers["Authorization"] == "Bearer test-access-token"


def test_supabase_error_details_are_sanitized():
    from backend.research.service import _safe_database_error

    error = SimpleNamespace(
        status=403,
        code="42501",
        message=(
            "Bearer abc.def.ghi sb_secret_sensitive user@example.com access denied"
        ),
    )
    status_code, code, message = _safe_database_error(error)

    assert status_code == 403
    assert code == "42501"
    assert "abc.def.ghi" not in message
    assert "sb_secret_sensitive" not in message
    assert "user@example.com" not in message
    assert "[REDACTED" in message


def test_hod_cannot_override_faculty_department_scope(monkeypatch):
    captured = {}

    def faculty_analytics(department, academic_year, access_token):
        captured.update({
            "department": department,
            "academic_year": academic_year,
            "access_token": access_token,
        })
        return FacultyResearchAnalyticsResponse(
            overview=FacultyResearchOverview(
                selected_department=department,
                total_faculty=0,
                faculty_researchers=0,
                publishing_faculty_count=0,
                total_publications=0,
                average_publications_per_faculty=0,
                faculty_participation_rate=0,
                total_citations=0,
                average_citations_per_faculty=0,
                total_research_grants=0,
                faculty_rating_count=0,
                mentorship_score_count=0,
            ),
            departments=[
                FacultyResearchDepartment(
                    department=department,
                    total_faculty=0,
                    faculty_researchers=0,
                    publications=0,
                    participation_rate=0,
                    total_citations=0,
                    research_grants=0,
                    faculty_rating_count=0,
                    mentorship_score_count=0,
                )
            ] if department else [],
            publication_trends=[],
            top_researchers=[],
            available_departments=[department] if department else [],
            academic_years=[],
        )

    monkeypatch.setattr(
        research_router_module.research_service,
        "get_faculty_analytics",
        faculty_analytics,
    )
    with TestClient(app, headers={"Authorization": "Bearer test-hod-cse"}) as client:
        response = client.get(
            "/api/research/faculty/analytics?department=ECE",
            headers={
                "X-User-Role": "HOD",
                "X-User-Department": "CSE",
                "Authorization": "Bearer a.b.c",
            },
        )

    assert response.status_code == 200
    assert captured["department"] == "CSE"


def test_faculty_api_requires_supabase_session():
    with TestClient(app) as client:
        response = client.get(
            "/api/research/faculty/analytics",
            headers={"X-User-Role": "ADMINISTRATOR"},
        )

    assert response.status_code == 401

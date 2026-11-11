from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_research_status_and_module_registration():
    status = client.get("/api/research/status")
    assert status.status_code == 200
    assert status.json() == {"module": "research", "status": "ready"}

    modules = client.get("/api/modules/status")
    assert modules.status_code == 200
    assert modules.json()["research"] == "ready"


def test_research_analytics_endpoints_return_dataset_data():
    overview = client.get("/api/research/overview")
    departments = client.get("/api/research/departments")
    programs = client.get("/api/research/programs")
    publications = client.get("/api/research/publications")
    participation = client.get("/api/research/participation")
    filters = client.get("/api/research/filters")

    assert all(response.status_code == 200 for response in (
        overview, departments, programs, publications, participation, filters
    ))
    assert overview.json()["total_students"] == 5000
    assert overview.json()["research_participants"] == 2359
    assert len(departments.json()["departments"]) == 9
    assert len(programs.json()["programs"]) == 2
    assert sum(item["count"] for item in publications.json()["distribution"]) == 5000
    assert {item["category"] for item in participation.json()["distribution"]} == {
        "Participating", "Not participating"
    }
    assert filters.json()["admission_years"] == list(range(2019, 2027))


def test_research_filters_are_applied_consistently():
    params = {"department": "CSE", "program": "UG", "admission_year": 2023}
    overview = client.get("/api/research/overview", params=params)
    departments = client.get("/api/research/departments", params=params)
    programs = client.get("/api/research/programs", params=params)

    assert overview.status_code == 200
    assert departments.status_code == 200
    assert programs.status_code == 200
    assert overview.json()["total_students"] > 0
    assert [item["department"] for item in departments.json()["departments"]] == ["CSE"]
    assert [item["program"] for item in programs.json()["programs"]] == ["UG"]
    assert departments.json()["departments"][0]["total_students"] == overview.json()["total_students"]


def test_research_empty_filter_returns_empty_analytics():
    response = client.get("/api/research/overview", params={"department": "not-a-department"})
    assert response.status_code == 200
    assert response.json()["total_students"] == 0
    assert response.json()["research_participation_rate"] == 0

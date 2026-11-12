import os
import sys
from pathlib import Path

# Ensure project root is in python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app, headers={"Authorization": "Bearer test-admin"})


def test_1_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_2_modules_status_endpoint():
    response = client.get("/api/modules/status")
    assert response.status_code == 200
    data = response.json()
    assert data["student"] == "ready"


def test_3_get_students():
    response = client.get("/api/students")
    assert response.status_code == 200
    data = response.json()
    assert "total_students" in data
    assert data["total_students"] == 15985
    assert len(data["students"]) > 0


def test_4_get_students_by_department():
    response = client.get("/api/students?department=CSE")
    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] > 0
    for s in data["students"]:
        assert s["department_id"] == "CSE"


def test_5_get_students_by_academic_year():
    response = client.get("/api/students?academic_year=2025")
    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] > 0
    for s in data["students"]:
        assert s["academic_year"] == 2025


def test_6_get_students_by_semester():
    response = client.get("/api/students?semester=3")
    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] > 0
    for s in data["students"]:
        assert s["semester"] == 3


def test_7_get_students_combined_filter():
    response = client.get("/api/students?department=CSE&academic_year=2025&semester=3")
    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] > 0
    for s in data["students"]:
        assert s["department_id"] == "CSE"
        assert s["academic_year"] == 2025
        assert s["semester"] == 3


def test_8_get_students_by_risk_level():
    response = client.get("/api/students?risk_level=HIGH")
    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] > 0
    for s in data["students"]:
        assert s["risk_level"] == "HIGH"


def test_9_get_students_filters():
    response = client.get("/api/students/filters")
    assert response.status_code == 200
    data = response.json()
    assert "departments" in data
    assert "academic_years" in data
    assert "semesters" in data
    assert "risk_levels" in data
    assert "CSE" in data["departments"]


def test_10_get_overview():
    response = client.get("/api/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] == 15985
    assert "risk_distribution" in data
    assert "low" in data["risk_distribution"]
    assert "average_gpa" in data
    assert "average_attendance" in data
    assert "average_dropout_probability" in data
    assert data["model_status"] == "active"


def test_11_get_overview_by_department():
    response = client.get("/api/overview?department=CSE")
    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] > 0
    assert data["total_students"] < 15985


def test_12_get_overview_by_dept_and_year():
    response = client.get("/api/overview?department=CSE&academic_year=2025")
    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] > 0


def test_13_get_overview_by_dept_year_and_sem():
    response = client.get("/api/overview?department=CSE&academic_year=2025&semester=3")
    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] > 0


def test_14_unknown_student_404():
    response = client.get("/api/students/STU_UNKNOWN/risk")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "STU_UNKNOWN" in data["detail"]


if __name__ == "__main__":
    print("Running PART 15 Specified API Test Suite...")
    test_1_health_endpoint()
    print("  [OK] 1. GET /api/health")
    test_2_modules_status_endpoint()
    print("  [OK] 2. GET /api/modules/status")
    test_3_get_students()
    print("  [OK] 3. GET /api/students")
    test_4_get_students_by_department()
    print("  [OK] 4. GET /api/students?department=CSE")
    test_5_get_students_by_academic_year()
    print("  [OK] 5. GET /api/students?academic_year=2025")
    test_6_get_students_by_semester()
    print("  [OK] 6. GET /api/students?semester=3")
    test_7_get_students_combined_filter()
    print("  [OK] 7. GET /api/students?department=CSE&academic_year=2025&semester=3")
    test_8_get_students_by_risk_level()
    print("  [OK] 8. GET /api/students?risk_level=HIGH")
    test_9_get_students_filters()
    print("  [OK] 9. GET /api/students/filters")
    test_10_get_overview()
    print("  [OK] 10. GET /api/overview")
    test_11_get_overview_by_department()
    print("  [OK] 11. GET /api/overview?department=CSE")
    test_12_get_overview_by_dept_and_year()
    print("  [OK] 12. GET /api/overview?department=CSE&academic_year=2025")
    test_13_get_overview_by_dept_year_and_sem()
    print("  [OK] 13. GET /api/overview?department=CSE&academic_year=2025&semester=3")
    test_14_unknown_student_404()
    print("  [OK] 14. GET /api/students/STU_UNKNOWN/risk -> HTTP 404")
    print("\nALL 14 PART 15 API TESTS PASSED SUCCESSFULLY!")

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app, headers={"Authorization": "Bearer test-admin"})


def test_get_accessible_departments_admin():
    response = client.get("/api/access/departments", headers={"X-User-Role": "ADMINISTRATOR"})
    assert response.status_code == 200
    depts = response.json()
    assert len(depts) >= 10
    dept_ids = [d["id"] for d in depts]
    assert "CSE" in dept_ids
    assert "ME" in dept_ids
    assert "BBA" in dept_ids


def test_get_accessible_departments_hod():
    response = client.get(
        "/api/access/departments",
        headers={
            "Authorization": "Bearer test-hod-cse",
            "X-User-Role": "ADMINISTRATOR",
            "X-User-Department": "ECE",
        }
    )
    assert response.status_code == 200
    depts = response.json()
    assert len(depts) == 1
    assert depts[0]["id"] == "CSE"
    assert depts[0]["name"] == "Computer Science & Engineering"


def test_dependent_years_and_semesters_filtering():
    # Fetch years for CSE
    years_res = client.get("/api/access/years?department=CSE", headers={"X-User-Role": "ADMINISTRATOR"})
    assert years_res.status_code == 200
    years = years_res.json()
    assert len(years) > 0
    assert 2025 in years

    # Fetch semesters for CSE in 2025
    sems_res = client.get("/api/access/semesters?department=CSE&academic_year=2025", headers={"X-User-Role": "ADMINISTRATOR"})
    assert sems_res.status_code == 200
    semesters = sems_res.json()
    assert len(semesters) > 0
    assert isinstance(semesters[0], int)


def test_admin_overview():
    response = client.get("/api/admin/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] > 0
    assert "risk_distribution" in data
    assert "department_chart" in data
    assert len(data["department_chart"]) >= 10


def test_admin_filtered_students():
    response = client.get("/api/admin/students?department=CSE&academic_year=2025&semester=3&risk_level=HIGH")
    assert response.status_code == 200
    data = response.json()
    assert "students" in data
    for s in data["students"]:
        assert s["department_id"] == "CSE"
        assert s["academic_year"] == 2025
        assert s["semester"] == 3
        assert s["risk_level"] == "HIGH"


def test_hod_overview_assigned_dept():
    response = client.get(
        "/api/hod/overview",
        headers={
            "Authorization": "Bearer test-hod-cse",
            "X-User-Role": "ADMINISTRATOR",
            "X-User-Department": "ME",
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["department_id"] == "CSE"
    assert data["total_students"] > 0
    assert "available_years" in data
    assert "available_semesters" in data


def test_hod_unauthorized_department_rejection():
    # HOD assigned to CSE attempting to query Mechanical department
    response = client.get(
        "/api/hod/students?department=ME",
        headers={
            "Authorization": "Bearer test-hod-cse",
            "X-User-Role": "ADMINISTRATOR",
            "X-User-Department": "ME",
        }
    )
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Access denied" in data["detail"]


def test_teacher_students_view():
    response = client.get(
        "/api/teacher/students",
        headers={"Authorization": "Bearer test-hod-cse"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["students"]) > 0
    sample = data["students"][0]
    assert "gpa" in sample
    assert "attendance_percentage" in sample
    assert "backlog_count" in sample
    assert "risk_level" in sample
    assert "dropout_probability" in sample


def test_empty_filter_combination_graceful_handling():
    # Query non-existent academic year
    response = client.get("/api/admin/students?department=CSE&academic_year=1990")
    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] == 0
    assert data["total_pages"] == 0
    assert data["students"] == []


def test_student_directory_pagination_program_filter_and_export():
    page_response = client.get("/api/students/directory?page=2&page_size=5")
    assert page_response.status_code == 200
    page_data = page_response.json()
    assert page_data["page"] == 2
    assert page_data["page_size"] == 5
    assert len(page_data["students"]) == 5
    assert page_data["total_pages"] == (page_data["total_students"] + 4) // 5
    assert {
        "student_id",
        "program",
        "department_id",
        "semester",
        "academic_year",
        "gpa",
        "attendance_percentage",
        "backlog_count",
        "dropout_probability",
        "risk_level",
    }.issubset(page_data["students"][0])

    student_id = page_data["students"][0]["student_id"]
    search_response = client.get(
        "/api/students/directory",
        params={"search": student_id, "page_size": 5},
    )
    assert search_response.status_code == 200
    assert search_response.json()["total_students"] == 1
    assert search_response.json()["students"][0]["student_id"] == student_id

    filter_options = client.get("/api/students/filters?department=CSE").json()
    assert filter_options["programs"]
    program = filter_options["programs"][0]
    filtered = client.get(
        "/api/students/directory",
        params={"department": "CSE", "program": program, "page_size": 5},
    )
    assert filtered.status_code == 200
    assert filtered.json()["students"]
    assert all(
        row["department_id"] == "CSE" and row["program"] == program
        for row in filtered.json()["students"]
    )

    export = client.get("/api/students/export", params={"department": "CSE", "program": program})
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("text/csv")
    assert export.text.splitlines()[0] == (
        "Student ID,Program,Department,Semester,Academic Year,GPA,Attendance,"
        "Backlogs,Dropout Probability,Risk Level"
    )


def test_hod_directory_and_csv_ignore_department_override():
    hod_headers = {"Authorization": "Bearer test-hod-cse"}
    response = client.get(
        "/api/students/directory",
        params={"department": "ME", "page_size": 10},
        headers=hod_headers,
    )
    assert response.status_code == 200
    assert response.json()["students"]
    assert all(row["department_id"] == "CSE" for row in response.json()["students"])

    export = client.get(
        "/api/students/export",
        params={"department": "ME", "search": "STU"},
        headers=hod_headers,
    )
    assert export.status_code == 200
    rows = export.text.splitlines()[1:]
    assert rows
    assert all(",CSE," in row for row in rows)


if __name__ == "__main__":
    print("Running Role-Based Access & Hierarchical Filtering Tests...")
    test_get_accessible_departments_admin()
    print("  [OK] Admin accessible departments")
    test_get_accessible_departments_hod()
    print("  [OK] HOD restricted departments")
    test_dependent_years_and_semesters_filtering()
    print("  [OK] Dynamic dependent years & semesters")
    test_admin_overview()
    print("  [OK] Admin institutional overview")
    test_admin_filtered_students()
    print("  [OK] Admin filtered student list")
    test_hod_overview_assigned_dept()
    print("  [OK] HOD overview assigned department")
    test_hod_unauthorized_department_rejection()
    print("  [OK] Security: HOD unauthorized department query rejected with HTTP 403")
    test_teacher_students_view()
    print("  [OK] Teacher students view scope")
    test_empty_filter_combination_graceful_handling()
    print("  [OK] Empty filter combination handles zero results cleanly")
    test_student_directory_pagination_program_filter_and_export()
    print("  [OK] Student directory pagination, program filter, and CSV export")
    test_hod_directory_and_csv_ignore_department_override()
    print("  [OK] HOD directory and CSV department scope")
    print("\nALL ROLE & FILTERING TESTS PASSED SUCCESSFULLY!")

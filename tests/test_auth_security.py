import base64
import json
import time

from fastapi.testclient import TestClient

from backend.common.auth import _verified_jwt_claims
from backend.common.supabase_client import get_supabase_config
from backend.main import app


def _token(claims):
    payload = base64.urlsafe_b64encode(
        json.dumps(claims).encode("utf-8")
    ).decode("ascii").rstrip("=")
    return f"header.{payload}.signature"


def test_verified_claim_validation_checks_issuer_expiry_audience_and_subject():
    url, _ = get_supabase_config()
    claims = {
        "iss": f"{url.rstrip('/')}/auth/v1",
        "sub": "verified-user",
        "aud": "authenticated",
        "exp": time.time() + 60,
        "app_metadata": {"role": "ADMINISTRATOR"},
    }

    assert _verified_jwt_claims(_token(claims), "verified-user")["app_metadata"]["role"] == "ADMINISTRATOR"
    for changed in (
        {**claims, "iss": "https://wrong-project.example/auth/v1"},
        {**claims, "exp": time.time() - 1},
        {**claims, "aud": "anon"},
        {**claims, "sub": "another-user"},
    ):
        try:
            _verified_jwt_claims(_token(changed), "verified-user")
        except Exception as error:
            assert getattr(error, "status_code", None) == 401
        else:
            raise AssertionError("Invalid Supabase claims must be rejected.")


def test_missing_and_invalid_tokens_are_rejected():
    with TestClient(app) as client:
        missing = client.get("/api/auth/me")
        invalid = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.jwt.token"},
        )
        expired = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer expired.jwt.token"},
        )

    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert expired.status_code == 401


def test_administrator_role_comes_from_verified_app_metadata_not_headers_or_query():
    with TestClient(app) as client:
        response = client.get(
            "/api/access/departments?role=HOD&user_department=CSE",
            headers={
                "Authorization": "Bearer test-admin",
                "X-User-Role": "HOD",
                "X-User-Department": "CSE",
            },
        )

    assert response.status_code == 200
    assert len(response.json()) >= 10


def test_hod_cannot_expand_department_scope_with_caller_headers_or_query():
    with TestClient(app) as client:
        departments = client.get(
            "/api/access/departments?role=ADMINISTRATOR&user_department=ME",
            headers={
                "Authorization": "Bearer test-hod-cse",
                "X-User-Role": "ADMINISTRATOR",
                "X-User-Department": "ME",
            },
        )
        another_department = client.get(
            "/api/hod/students?department=ME",
            headers={
                "Authorization": "Bearer test-hod-cse",
                "X-User-Role": "ADMINISTRATOR",
                "X-User-Department": "ME",
            },
        )

    assert departments.status_code == 200
    assert [item["id"] for item in departments.json()] == ["CSE"]
    assert another_department.status_code == 403


def test_unknown_or_user_metadata_only_role_is_denied():
    with TestClient(app) as client:
        unknown = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer test-unknown-role"},
        )
        user_metadata_only = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer test-user-metadata-only"},
        )
        unassigned_hod = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer test-hod-without-department"},
        )

    assert unknown.status_code == 403
    assert user_metadata_only.status_code == 403
    assert unassigned_hod.status_code == 403

from types import SimpleNamespace

import pytest
from supabase_auth.errors import AuthApiError

from backend.common import auth as auth_module

TEST_PRINCIPALS = {
    "test-admin": {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "admin@test.invalid",
        "app_metadata": {"role": "ADMINISTRATOR"},
        "user_metadata": {},
    },
    "test-hod-cse": {
        "id": "00000000-0000-0000-0000-000000000002",
        "email": "hod-cse@test.invalid",
        "app_metadata": {"role": "HOD", "department_id": "CSE"},
        "user_metadata": {},
    },
    "test-hod-bt": {
        "id": "00000000-0000-0000-0000-000000000003",
        "email": "hod-bt@test.invalid",
        "app_metadata": {"role": "HOD", "department_id": "BT"},
        "user_metadata": {},
    },
    "test-unknown-role": {
        "id": "00000000-0000-0000-0000-000000000004",
        "email": "user@test.invalid",
        "app_metadata": {"role": "PROFESSOR"},
        "user_metadata": {"role": "ADMINISTRATOR"},
    },
    "test-user-metadata-only": {
        "id": "00000000-0000-0000-0000-000000000005",
        "email": "user-metadata@test.invalid",
        "app_metadata": {},
        "user_metadata": {"role": "ADMINISTRATOR"},
    },
    "test-hod-without-department": {
        "id": "00000000-0000-0000-0000-000000000006",
        "email": "hod@test.invalid",
        "app_metadata": {"role": "HOD"},
        "user_metadata": {"department_id": "CSE"},
    },
    "valid.token.value": {
        "id": "00000000-0000-0000-0000-000000000002",
        "email": "hod-cse@test.invalid",
        "app_metadata": {"role": "HOD", "department_id": "CSE"},
        "user_metadata": {},
    },
}


class TestAuthClient:
    def get_user(self, token):
        if token in {"invalid.jwt.token", "expired.jwt.token", "expired-or-invalid"}:
            raise AuthApiError("invalid test access token", 401, None)
        principal = TEST_PRINCIPALS.get(token)
        if principal is None and isinstance(token, str) and token.count(".") == 2:
            principal = TEST_PRINCIPALS["test-hod-cse"]
        if principal is None:
            raise AuthApiError("invalid test access token", 401, None)
        return SimpleNamespace(user=SimpleNamespace(**principal))


class TestSupabaseClient:
    auth = TestAuthClient()


@pytest.fixture(autouse=True)
def use_test_supabase_auth(monkeypatch):
    """Provide deterministic test identities; production always uses Supabase Auth."""
    monkeypatch.setattr(auth_module, "get_supabase_client", lambda: TestSupabaseClient())

    def verified_test_claims(token, user_id):
        principal = TEST_PRINCIPALS.get(token, TEST_PRINCIPALS["test-hod-cse"])
        return {
            "sub": user_id,
            "app_metadata": principal["app_metadata"],
        }

    monkeypatch.setattr(auth_module, "_verified_jwt_claims", verified_test_claims)

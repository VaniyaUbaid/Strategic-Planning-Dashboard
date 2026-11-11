import logging
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException

from backend.common import supabase_client as supabase_client_module
from backend.finance import service as finance_service_module
from backend.finance.schemas import FinanceStatusResponse
from backend.finance.service import FinanceService


class EmptySupabaseQuery:
    def select(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def range(self, *_args, **_kwargs):
        return self

    def ilike(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=[])


class EmptySupabaseClient:
    def table(self, _table_name):
        return EmptySupabaseQuery()


class PaginatedQuery:
    def __init__(self, rows, calls):
        self.rows = rows
        self.calls = calls
        self.page_range = (0, 0)

    def select(self, *_args, **_kwargs):
        return self

    def ilike(self, column, value):
        self.calls.append(("ilike", column, value))
        return self

    def eq(self, column, value):
        self.calls.append(("eq", column, value))
        return self

    def range(self, start, end):
        self.page_range = (start, end)
        self.calls.append(("range", start, end))
        return self

    def execute(self):
        start, end = self.page_range
        return SimpleNamespace(data=self.rows[start : end + 1])


class PaginatedSupabaseClient:
    def __init__(self, rows, calls):
        self.rows = rows
        self.calls = calls

    def table(self, _table_name):
        return PaginatedQuery(self.rows, self.calls)


def test_supabase_config_prefers_backend_credentials(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://backend-project.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "backend-key")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-key")
    monkeypatch.setenv("VITE_SUPABASE_URL", "https://frontend-project.supabase.co")
    monkeypatch.setenv("VITE_SUPABASE_PUBLISHABLE_KEY", "publishable-key")

    assert supabase_client_module.get_supabase_config() == (
        "https://backend-project.supabase.co",
        "backend-key",
    )


def test_supabase_config_uses_publishable_key_as_public_fallback(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    monkeypatch.setenv("VITE_SUPABASE_PUBLISHABLE_KEY", "publishable-key")

    assert supabase_client_module.get_supabase_config() == (
        "https://project.supabase.co",
        "publishable-key",
    )


def test_empty_finance_table_is_a_successful_empty_read(monkeypatch):
    monkeypatch.setattr(
        finance_service_module,
        "get_supabase_client",
        lambda: EmptySupabaseClient(),
    )
    service = FinanceService()

    assert service._query_table("finance_budgets") == []
    assert service.get_status() == FinanceStatusResponse(module="finance", status="ready")


def test_finance_table_pagination_and_filters(monkeypatch):
    rows = [{"row": index} for index in range(2001)]
    calls = []
    monkeypatch.setattr(
        finance_service_module,
        "get_supabase_client",
        lambda: PaginatedSupabaseClient(rows, calls),
    )

    result = FinanceService()._query_table(
        "finance_fees",
        department_id="CSE",
        academic_year="2025-2026",
        semester=2,
    )

    assert len(result) == len(rows)
    assert calls.count(("range", 0, 999)) == 1
    assert calls.count(("range", 1000, 1999)) == 1
    assert calls.count(("range", 2000, 2999)) == 1
    assert ("ilike", "department_id", "CSE") in calls
    assert ("ilike", "academic_year", "2025-2026") in calls
    assert ("eq", "semester", 2) in calls


def test_finance_database_connection_failure_is_503_and_does_not_log_error_text(
    monkeypatch, caplog
):
    def fail_connection():
        raise httpx.ConnectError("sensitive-token-must-not-be-logged")

    monkeypatch.setattr(finance_service_module, "get_supabase_client", fail_connection)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(HTTPException) as error:
            FinanceService()._query_table("finance_budgets")

    assert error.value.status_code == 503
    assert "connection is unavailable" in error.value.detail
    assert "finance_budgets" in caplog.text
    assert "ConnectError" in caplog.text
    assert "sensitive-token-must-not-be-logged" not in caplog.text

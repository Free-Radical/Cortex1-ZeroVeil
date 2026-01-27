from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def disable_tenant_auth_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable tenant auth by default so existing tests run without auth.

    Tests that need tenant auth (like test_tenant_auth.py) override this
    by setting ZEROVEIL_TENANTS_PATH to a valid config file.
    """
    monkeypatch.setenv("ZEROVEIL_TENANTS_PATH", "/nonexistent/tenants.json")


@pytest.fixture(autouse=True)
def enable_stub_mode_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enable stub mode by default so tests don't call real LLM providers.

    Tests that need real provider calls can set ZEROVEIL_STUB_MODE=0.
    """
    monkeypatch.setenv("ZEROVEIL_STUB_MODE", "1")

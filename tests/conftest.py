from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def disable_tenant_auth_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable tenant auth by default so existing tests run without auth.

    Tests that need tenant auth (like test_tenant_auth.py) override this
    by setting ZEROVEIL_TENANTS_PATH to a valid config file.
    """
    monkeypatch.setenv("ZEROVEIL_TENANTS_PATH", "/nonexistent/tenants.json")

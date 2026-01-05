from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from zeroveil_gateway.tenants import sha256_hex


@pytest.fixture
def tenants_config(tmp_path: Path) -> Path:
    """Create a test tenants config file."""
    config = {
        "tenants": [
            {
                "tenant_id": "test-tenant",
                "api_key_hashes": [sha256_hex("valid-api-key")],
                "rate_limit_rpm": 5,
                "rate_limit_tpd": 1000,
                "enabled": True,
            },
            {
                "tenant_id": "disabled-tenant",
                "api_key_hashes": [sha256_hex("disabled-key")],
                "rate_limit_rpm": 0,
                "rate_limit_tpd": 0,
                "enabled": False,
            },
            {
                "tenant_id": "low-limit-tenant",
                "api_key_hashes": [sha256_hex("low-limit-key")],
                "rate_limit_rpm": 1,
                "rate_limit_tpd": 0,
                "enabled": True,
            },
        ]
    }
    config_path = tmp_path / "tenants.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path


@pytest.fixture
def policy_config(tmp_path: Path) -> Path:
    """Create a test policy config file."""
    config = {
        "version": "test",
        "enforce_zdr_only": False,
        "require_scrubbed_attestation": False,
        "allowed_providers": ["test-provider"],
        "allowed_models": ["*"],
        "limits": {"max_messages": 50, "max_chars_per_message": 16000},
        "logging": {"mode": "metadata_only", "sink": "stdout"},
    }
    config_path = tmp_path / "policy.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path


@pytest.fixture
def client(
    tenants_config: Path, policy_config: Path, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """Create a test client with tenant auth enabled."""
    monkeypatch.setenv("ZEROVEIL_TENANTS_PATH", str(tenants_config))
    monkeypatch.setenv("ZEROVEIL_POLICY_PATH", str(policy_config))

    from zeroveil_gateway.app import create_app

    app = create_app()
    return TestClient(app)


def _valid_request() -> dict:
    return {
        "messages": [{"role": "user", "content": "hello"}],
        "model": "test",
        "zdr_only": True,
        "metadata": {"scrubbed": True},
    }


class TestTenantAuth:
    def test_valid_tenant_key_returns_200(self, client: TestClient) -> None:
        response = client.post(
            "/v1/chat/completions",
            json=_valid_request(),
            headers={"Authorization": "Bearer valid-api-key"},
        )
        assert response.status_code == 200
        assert response.json()["choices"][0]["message"]["content"] == "stubbed_response"

    def test_invalid_key_returns_401(self, client: TestClient) -> None:
        response = client.post(
            "/v1/chat/completions",
            json=_valid_request(),
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthorized"

    def test_missing_authorization_header_returns_401(self, client: TestClient) -> None:
        response = client.post(
            "/v1/chat/completions",
            json=_valid_request(),
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthorized"
        assert response.json()["error"]["details"]["header"] == "Authorization"

    def test_disabled_tenant_returns_401(self, client: TestClient) -> None:
        response = client.post(
            "/v1/chat/completions",
            json=_valid_request(),
            headers={"Authorization": "Bearer disabled-key"},
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthorized"

    def test_rate_limited_tenant_returns_429(self, client: TestClient) -> None:
        # First request should succeed
        response = client.post(
            "/v1/chat/completions",
            json=_valid_request(),
            headers={"Authorization": "Bearer low-limit-key"},
        )
        assert response.status_code == 200

        # Second request should be rate limited (rpm=1)
        response = client.post(
            "/v1/chat/completions",
            json=_valid_request(),
            headers={"Authorization": "Bearer low-limit-key"},
        )
        assert response.status_code == 429
        assert response.json()["error"]["code"] == "rate_limited"

    def test_rate_limit_headers_present(self, client: TestClient) -> None:
        response = client.post(
            "/v1/chat/completions",
            json=_valid_request(),
            headers={"Authorization": "Bearer valid-api-key"},
        )
        assert response.status_code == 200
        # Tenant has rpm=5, after 1 request should have 4 remaining
        assert "X-RateLimit-Remaining-RPM" in response.headers
        assert response.headers["X-RateLimit-Remaining-RPM"] == "4"
        # Tenant has tpd=1000
        assert "X-RateLimit-Remaining-TPD" in response.headers

    def test_malformed_bearer_token_returns_401(self, client: TestClient) -> None:
        response = client.post(
            "/v1/chat/completions",
            json=_valid_request(),
            headers={"Authorization": "NotBearer valid-api-key"},
        )
        assert response.status_code == 401

    def test_empty_bearer_token_returns_401(self, client: TestClient) -> None:
        response = client.post(
            "/v1/chat/completions",
            json=_valid_request(),
            headers={"Authorization": "Bearer "},
        )
        assert response.status_code == 401

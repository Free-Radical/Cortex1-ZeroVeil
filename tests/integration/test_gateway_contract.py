from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from zeroveil_gateway.app import create_app


def _load_fixture(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_policy(tmp_path: Path, **overrides: object) -> Path:
    policy = {
        "version": "0",
        "enforce_zdr_only": True,
        "require_scrubbed_attestation": True,
        "allowed_providers": ["openrouter"],
        "allowed_models": ["*"],
        "limits": {"max_messages": 50, "max_chars_per_message": 16000},
        "logging": {"mode": "metadata_only", "sink": "jsonl", "path": str(tmp_path / "audit.jsonl")},
    }
    policy.update(overrides)
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy), encoding="utf-8")
    return path


@pytest.fixture()
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures"


def test_validation_errors_return_400_error_model(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    policy_path = _write_policy(tmp_path)
    monkeypatch.setenv("ZEROVEIL_POLICY_PATH", str(policy_path))

    client = TestClient(create_app())
    resp = client.post("/v1/chat/completions", json={})
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "invalid_request"


def test_requires_api_key_when_configured(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fixtures_dir: Path) -> None:
    policy_path = _write_policy(tmp_path)
    monkeypatch.setenv("ZEROVEIL_POLICY_PATH", str(policy_path))
    monkeypatch.setenv("ZEROVEIL_API_KEY", "secret")

    client = TestClient(create_app())
    payload = _load_fixture(fixtures_dir / "requests" / "valid_minimal.json")

    missing = client.post("/v1/chat/completions", json=payload)
    assert missing.status_code == 401
    assert missing.json()["error"]["code"] == "unauthorized"

    wrong = client.post("/v1/chat/completions", json=payload, headers={"Authorization": "Bearer wrong"})
    assert wrong.status_code == 401
    assert wrong.json()["error"]["code"] == "unauthorized"

    ok = client.post("/v1/chat/completions", json=payload, headers={"Authorization": "Bearer secret"})
    assert ok.status_code == 200


def test_enforces_zdr_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fixtures_dir: Path) -> None:
    policy_path = _write_policy(tmp_path, enforce_zdr_only=True)
    monkeypatch.setenv("ZEROVEIL_POLICY_PATH", str(policy_path))

    client = TestClient(create_app())
    payload = _load_fixture(fixtures_dir / "requests" / "invalid_missing_zdr_only.json")
    resp = client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "policy_denied"


def test_enforces_scrub_attestation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fixtures_dir: Path) -> None:
    policy_path = _write_policy(tmp_path, require_scrubbed_attestation=True)
    monkeypatch.setenv("ZEROVEIL_POLICY_PATH", str(policy_path))

    client = TestClient(create_app())
    payload = _load_fixture(fixtures_dir / "requests" / "invalid_missing_scrub_attestation.json")
    resp = client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 403
    body = resp.json()
    assert body["error"]["code"] == "policy_denied"
    assert body["error"]["details"]["field"] == "metadata.scrubbed"


def test_enforces_message_limits(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    policy_path = _write_policy(tmp_path, limits={"max_messages": 1, "max_chars_per_message": 1})
    monkeypatch.setenv("ZEROVEIL_POLICY_PATH", str(policy_path))

    client = TestClient(create_app())

    too_many = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "a"}, {"role": "user", "content": "b"}], "metadata": {"scrubbed": True}},
    )
    assert too_many.status_code == 403
    assert too_many.json()["error"]["code"] == "policy_denied"

    too_large = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "ab"}], "metadata": {"scrubbed": True}},
    )
    assert too_large.status_code == 403
    assert too_large.json()["error"]["code"] == "policy_denied"

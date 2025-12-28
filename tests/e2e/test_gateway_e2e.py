from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from zeroveil_gateway.app import create_app


def test_e2e_happy_path_writes_audit_line(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    audit_path = tmp_path / "audit.jsonl"
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "version": "0",
                "enforce_zdr_only": True,
                "require_scrubbed_attestation": True,
                "allowed_providers": ["openrouter"],
                "allowed_models": ["*"],
                "limits": {"max_messages": 50, "max_chars_per_message": 16000},
                "logging": {"mode": "metadata_only", "sink": "jsonl", "path": str(audit_path)},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("ZEROVEIL_POLICY_PATH", str(policy_path))

    client = TestClient(create_app())
    resp = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "hello"}], "metadata": {"scrubbed": True}},
    )
    assert resp.status_code == 200
    assert resp.json()["choices"][0]["message"]["content"] == "stubbed_response"

    lines = audit_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1


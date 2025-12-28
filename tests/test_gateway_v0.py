from __future__ import annotations

from fastapi.testclient import TestClient

from zeroveil_gateway.app import create_app


def test_healthz_ok() -> None:
    client = TestClient(create_app())
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_requires_scrub_attestation() -> None:
    client = TestClient(create_app())
    resp = client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "hi"}]})
    assert resp.status_code == 403
    body = resp.json()
    assert body["error"]["code"] == "policy_denied"


def test_accepts_scrub_attestation() -> None:
    client = TestClient(create_app())
    resp = client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "hi"}],
            "zdr_only": True,
            "metadata": {"scrubbed": True},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["object"] == "chat.completion"
    assert body["choices"][0]["message"]["content"] == "stubbed_response"

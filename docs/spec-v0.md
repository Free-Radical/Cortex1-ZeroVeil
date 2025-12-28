# ZeroVeil Gateway -- Spec v0 (Week 1)

This document is the v0 **source of truth** for the ZeroVeil community gateway:

- API contract (request/response + errors)
- Policy schema v0 (what the gateway enforces)
- Logging/retention contract v0 (what we do/do not record)

ZeroVeil is **risk reduction**, not "guaranteed anonymity".

## 1) API Contract (v0)

### Base URL

- Local dev: `http://localhost:8000`

### Auth

- If `ZEROVEIL_API_KEY` is configured on the gateway, requests MUST include `Authorization: Bearer <ZEROVEIL_API_KEY>`.
- If `ZEROVEIL_API_KEY` is not configured, auth is disabled (intended for local dev only).
- API keys are tenant-scoped (v0 uses a single `ZEROVEIL_API_KEY`; multi-tenant comes later).

### Endpoint: `POST /v1/chat/completions`

#### Request JSON (v0)

Compatible with `zeroveil-sdk` basic shape.

```json
{
  "messages": [
    {"role": "system", "content": "optional system prompt"},
    {"role": "user", "content": "hello"}
  ],
  "model": "optional-model-id",
  "zdr_only": true,
  "metadata": {
    "scrubbed": true,
    "scrubber": "zeroveil-sdk",
    "scrubber_version": "0.1.0"
  }
}
```

#### Required fields

- `messages`: non-empty list of `{role, content}`.
- **Scrub attestation**: `metadata.scrubbed == true` (see Section 2).

#### Response JSON (v0)

OpenAI-style response shape (minimal).

```json
{
  "id": "zv_...",
  "object": "chat.completion",
  "created": 1730000000,
  "model": "stub",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "stubbed_response"},
      "finish_reason": "stop"
    }
  ],
  "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
}
```

#### Error model (v0)

All errors return JSON:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "human readable",
    "details": {"field": "metadata.scrubbed"}
  }
}
```

Common `code` values:
- `unauthorized`
- `invalid_request`
- `policy_denied`
- `server_error`

### Endpoint: `GET /healthz`

Returns:

```json
{"ok": true}
```

## 2) Policy Schema (v0)

Policy is loaded from a JSON file pointed to by `ZEROVEIL_POLICY_PATH` (default: `policies/default.json`).

### Schema (v0)

```json
{
  "version": "0",
  "enforce_zdr_only": true,
  "require_scrubbed_attestation": true,
  "allowed_providers": ["openrouter"],
  "allowed_models": ["*"],
  "limits": {
    "max_messages": 50,
    "max_chars_per_message": 16000
  },
  "logging": {
    "mode": "metadata_only",
    "sink": "jsonl",
    "path": "logs/audit.jsonl"
  }
}
```

### Notes

- v0 does **not** cryptographically verify scrubbing. It enforces an attestation gate to prevent accidental raw data submission and to support compliance posture.
- Later versions may add optional server-side **PII-likely reject** heuristics (reject only, never “scrub-as-a-service”).

## 3) Logging & Retention Contract (v0)

Default intent: **no prompt/response content logging**.

### What the gateway may log (metadata-only)

- timestamp
- request id
- auth result (success/failure)
- tenant id (v0: `default`)
- policy decision (allowed/denied + reason code)
- selected provider/model (v0 stubbed)
- request sizes (message count, character counts)
- latency
- token counts if provided by upstream (v0: zeros)

### What the gateway MUST NOT log by default

- raw prompt content
- raw response content
- full headers beyond minimal debugging context

### Retention

v0: whatever the operator configures for the metadata log file. Hosted offering will define defaults and explicit retention controls.

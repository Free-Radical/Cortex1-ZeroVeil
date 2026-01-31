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
  "model": "meta-llama/llama-3.1-8b-instruct",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "Hello! How can I help you?"},
      "finish_reason": "stop"
    }
  ],
  "usage": {"prompt_tokens": 15, "completion_tokens": 8, "total_tokens": 23}
}
```

**Phase 0 (current):** Gateway calls actual LLM providers (OpenRouter by default). Token usage reflects real API consumption. Set `ZEROVEIL_STUB_MODE=1` for stubbed responses in tests.

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

**FAILSAFE DESIGN (NON-NEGOTIABLE):**
- **PII scanning is ALWAYS ON.** The gateway scans every request for PII patterns. No bypass, no exceptions.
- `require_scrubbed_attestation` controls whether the client must send `metadata.scrubbed=true` header — but **attestation never bypasses scanning**. If a client attests "I scrubbed" and we still detect PII, we block and log `attestation_mismatch`.
- Attestation is logged for audit evidence, not trusted as security control.
- See `docs/threat-model.md` for full failsafe design philosophy.

### Corporate Gateway Mode (v1)

For enterprise DLP deployments, use `mode: corporate_gateway`:

```json
{
  "version": "1",
  "mode": "corporate_gateway",
  "require_scrubbed_attestation": false,
  "pii_rejection": {
    "enabled": true,
    "sensitivity": "high"
  },
  "allowed_models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "claude-3-*"],
  "blocked_models": ["*-32k"],
  "limits": {
    "max_requests_per_minute": 60,
    "max_tokens_per_day": 1000000
  },
  "content_policy": {
    "require_system_preamble": true,
    "system_preamble": "You are a helpful assistant for Acme Corp.",
    "blocked_keywords": ["confidential", "internal only"]
  }
}
```

**Key differences from default mode:**
- `require_scrubbed_attestation: false` — clients don't need to send attestation header (simpler integration)
- **PII scanning still happens** — gateway always scans, regardless of attestation setting
- Model allowlist/blocklist with glob pattern support
- Optional content policy (system preamble injection, keyword blocking)
- Per-tenant rate and cost limits

This enables drop-in deployment where applications only change `OPENAI_API_BASE`.

## 3) Logging & Retention Contract (v0)

Default intent: **no prompt/response content logging**.

### What the gateway may log (metadata-only)

- timestamp
- request id
- auth result (success/failure)
- tenant id (v0: `default`)
- policy decision (allowed/denied + reason code)
- selected provider/model (Phase 0: actual provider calls)
- request sizes (message count, character counts)
- latency
- token counts from provider (Phase 0: actual usage from OpenRouter)

### What the gateway MUST NOT log by default

- raw prompt content
- raw response content
- full headers beyond minimal debugging context

### Retention

v0: whatever the operator configures for the metadata log file. Hosted offering will define defaults and explicit retention controls.

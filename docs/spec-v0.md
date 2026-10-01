# ZeroVeil Gateway -- Spec v0

This document is the v0 **source of truth** for the ZeroVeil community gateway:

- API contract (request/response + errors)
- Policy schema v0 (what the gateway enforces)
- Logging/retention contract v0 (what we do/do not record)

ZeroVeil is **risk reduction**, not "guaranteed anonymity".

## 1) API Contract (v0)

### Base URL

- Local dev: `http://localhost:8000`

### Auth

Checked in this order:

1. **Tenant registry.** If the file at `ZEROVEIL_TENANTS_PATH` (default `tenants/default.json`) loads, every request MUST carry `Authorization: Bearer <key>`. The key's SHA-256 hex digest is matched against each enabled tenant's `api_key_hashes`; the matching tenant id is used for audit events and rate limits.
2. **Legacy single key.** If the tenants file is missing or invalid and `ZEROVEIL_API_KEY` is set, requests MUST send `Authorization: Bearer <ZEROVEIL_API_KEY>`.
3. **No auth.** If neither applies, auth is disabled (local dev only).

Per-tenant limits in the tenants file: `rate_limit_rpm` (requests per rolling 60 s) and `rate_limit_tpd` (tokens per rolling 24 h); `0` means unlimited. Exceeding either returns `429 rate_limited`. Successful responses carry `X-RateLimit-Remaining-RPM` and `X-RateLimit-Remaining-TPD` when a limit is set.

### Endpoint: `POST /v1/chat/completions`

#### Request JSON (v0)

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
    "scrubber": "local-scrubber",
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

The gateway forwards to OpenRouter, the only supported provider, and token usage reflects the real API response. Set `ZEROVEIL_STUB_MODE=1` for stubbed responses in tests.

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

`code` values and HTTP status:
- `unauthorized` (401)
- `invalid_request` (400)
- `pii_detected` (403)
- `policy_denied` (403)
- `rate_limited` (429)
- `provider_error` (upstream status, or 502; 500 for an unsupported provider name)

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
    "path": "logs/audit.jsonl",
    "retention": {"max_size_mb": 100, "max_age_days": 30, "rotate_count": 5}
  },
  "pii_gate": {
    "enabled": true,
    "patterns": ["ssn", "credit_card", "email", "phone", "ip_address"]
  }
}
```

Keys not listed here are ignored. Behavior:

- `enforce_zdr_only` (default true): requests must send `zdr_only: true`, otherwise `403 policy_denied`.
- `require_scrubbed_attestation` (default true): requests must send `metadata.scrubbed: true`, otherwise `403 policy_denied`. It is a declared flag, not proof.
- `allowed_providers`: must be non-empty; the first entry is used. Only `openrouter` is supported.
- `allowed_models`: `["*"]` allows any model; otherwise the request's `model` must appear in the list (exact match, no globs).
- `limits.max_messages` / `limits.max_chars_per_message`: exceeded limits return `403 policy_denied`.
- `logging.mode` must be `metadata_only`; `logging.sink` is `jsonl` (requires `path`) or `stdout`. `retention` rotates the JSONL file by size and prunes rotated files by age.
- `pii_gate`: regex check for the listed pattern types, on by default. Setting `enabled` to `false` turns it off (not recommended). A match returns `403 pii_detected` and names the types found, never the content.

### Check order

auth, rate limit, message shape, PII gate, `max_messages`, model allow-list, message size, `zdr_only`, scrub attestation, content sanity (null bytes), then the provider call.

The gateway does not scrub content. With the PII gate on, a request that attests `scrubbed: true` but still matches a pattern is rejected.

## 3) Logging & Retention Contract (v0)

Default intent: **no prompt/response content logging**.

### What the gateway may log (metadata-only)

- timestamp
- request id
- tenant id (the authenticated tenant, or `default` in legacy/no-auth mode)
- policy decision (allowed/denied + reason code)
- selected provider/model
- request sizes (message count, character counts)
- latency
- token counts from provider

### What the gateway MUST NOT log by default

- raw prompt content
- raw response content
- full headers beyond minimal debugging context

### Retention

The metadata log file rotates by size and age per `logging.retention` (defaults: 100 MB, 30 days, 5 rotated files). The operator owns everything else about retention.

# ZeroVeil Threat Model (v1)

## Design Philosophy: FAIL-SAFE

**Security is OPT-OUT, not opt-in.**

ZeroVeil defaults to the most restrictive, privacy-preserving configuration:
- **PII gate**: ENABLED by default - rejects requests containing obvious PII patterns
- **ZDR-only**: ENABLED by default - requires zero data retention intent
- **Scrub attestation**: REQUIRED by default - client must confirm data is scrubbed
- **Metadata-only logging**: ENFORCED - content is never logged

False positives are acceptable; false negatives are not. Operators must explicitly
disable protections if they want to relax security posture.

## Overview

ZeroVeil is a privacy-focused LLM gateway that enforces policy gates (ZDR-only intent, scrub attestation, PII detection, and input limits) and writes **metadata-only** audit events. It reduces logging/policy foot-guns, but it is **not guaranteed anonymity** and it does not scrub content server-side (see `docs/spec-v0.md`).

## What ZeroVeil protects against

- **Accidental prompt/response logging at the gateway** via a metadata-only audit event schema (`src/zeroveil_gateway/audit.py`) and `logging.mode=metadata_only` in `policies/default.json`.
- **Obvious PII leakage** via regex-based PII gate (`src/zeroveil_gateway/pii.py`) that rejects requests containing SSN, credit card, email, phone, or IP patterns. ENABLED BY DEFAULT.
- **Policy-violating requests** (e.g., missing scrub attestation or `zdr_only=false`) via enforcement in `src/zeroveil_gateway/app.py` and policy loading in `src/zeroveil_gateway/policy.py`.
- **Basic abuse and key guessing noise** via per-tenant authentication + rate limiting (`src/zeroveil_gateway/tenants.py`, enforced in `src/zeroveil_gateway/app.py`).

## What it does NOT protect against

- **Upstream visibility of submitted content**: upstream providers still receive whatever the client sends; client-side scrubbing is required.
- **A malicious/compromised gateway operator or host**: host access can bypass checks, capture traffic, or change logging behavior.
- **Traffic analysis and timing correlation**: network metadata can still correlate requests; mixing/batching is not part of the v0/v1 implementation.
- **Client compromise and app-layer attacks**: malware/key theft, prompt injection, and content moderation are out of scope for the gateway.

## Trust Model

ZeroVeil sits between clients and upstream providers and enforces “safe-to-relay” signals plus minimal persistence. Security depends on client scrubbing, safe operator deployment, and upstream retention/security claims.

### What the gateway operator is trusted to do / not do

- **Trusted to do**: terminate TLS, protect secrets/config/log files, patch dependencies, and keep audit logging metadata-only (see `policies/default.json` and `src/zeroveil_gateway/audit.py`).
- **Trusted not to do**: log prompts/responses or instrument request bodies for debugging in production.

### What the upstream provider is trusted to do / not do

- **Trusted to do**: apply access controls and honor any Zero Data Retention commitment for data it receives.
- **Trusted not to do**: retain, re-identify, or misuse content/metadata beyond its stated policy.

### What the client is trusted to do / not do

- **Trusted to do**: scrub PII/PHI locally and set scrub attestation (`metadata.scrubbed=true`) before sending requests.
- **Trusted not to do**: treat attestation as proof; the gateway does not cryptographically verify scrubbing (see `docs/spec-v0.md`).

## Attack Surface

### API endpoints exposed

- `GET /healthz` (health probe) in `src/zeroveil_gateway/app.py`.
- `POST /v1/chat/completions` (gateway API) in `src/zeroveil_gateway/app.py` accepting request JSON plus `Authorization: Bearer ...` and optional `X-Zeroveil-Tenant`.

### Configuration files (policy.json, tenants.json)

- Policy file at `ZEROVEIL_POLICY_PATH` (default `policies/default.json`) controls allowlists, limits, and logging sink/path.
- Tenant file at `ZEROVEIL_TENANTS_PATH` (default `tenants/default.json`) controls tenant ids, `api_key_hashes` (SHA-256 digests), and rate limits.
- Legacy single-key mode via `ZEROVEIL_API_KEY` is supported but intended for local/dev fallback.

### Audit logs

- Default sink is JSONL to `logs/audit.jsonl` (path and retention configured in `policies/default.json`), written by `src/zeroveil_gateway/audit.py`.
- Logs include decisions and request metadata (counts/sizes/latency), not prompt/response content, unless modified by the operator.

### Environment variables (API keys)

- `ZEROVEIL_POLICY_PATH`, `ZEROVEIL_TENANTS_PATH`, `ZEROVEIL_API_KEY` (legacy).
- Upstream provider credentials should be managed as secrets; compromise impacts billing and privacy posture.

## Threats Mitigated

| Threat | Mitigation | Residual Risk |
|---|---|---|
| Upstream sees raw PII | Require client-side scrub + `metadata.scrubbed=true` gate | Client can lie; no cryptographic proof |
| Obvious PII patterns leak | PII gate rejects SSN/CC/email/phone/IP (ENABLED BY DEFAULT) | Regex-only; won't catch names, addresses, context |
| Upstream correlates by API key | ZDR-only intent gate now; shared-identity/mixing is future work | Timing/volume correlation remains possible |
| Gateway logs leak content | `metadata_only` mode + audit schema lacks content fields | Misconfiguration or code changes can add logging |
| Brute-force API keys | Rate limiting + compare hashed keys (`sha256`) | Weak keys still guessable over time |
| Oversized payload DoS | Policy limits on message count/size | Distributed DoS still possible |
| Tenant "noisy neighbor" | Per-tenant RPM/TPD limits | Shared infra saturation remains an ops risk |

## Threats NOT Addressed (Non-Goals)

- Traffic analysis / timing attacks (requires mixer, Week 5)
- Malicious gateway operator (self-host or trust)
- Client-side malware (out of scope)
- Upstream provider collusion (trust boundary)
- Content moderation / prompt injection (application layer)

## Abuse Cases

- **High-volume abuse and key guessing**: rate limiting reduces impact, but operators should monitor 401/429 spikes in `logs/audit.jsonl`.
- **Using the relay for prohibited content**: the gateway does not moderate; acceptable use and downstream controls remain operator responsibility.
- **Tenant attribution games**: avoid legacy mode in production; rely on authenticated tenant id.

## Security Recommendations

- Rotate tenant API keys periodically; revoke on suspected compromise.
- Use strong keys (32+ random bytes) and store only SHA-256 digests in `tenants/*.json`.
- Prefer `ZEROVEIL_TENANTS_PATH` multi-tenant mode; avoid `ZEROVEIL_API_KEY` in production.
- Protect `policies/*.json`, `tenants/*.json`, and `logs/*.jsonl` with strict permissions and sensible retention.
- Keep the gateway updated and deploy behind TLS (reverse proxy/WAF) with monitoring.

# Cortex1-ZeroVeil - Core TODO

This file tracks engineering execution priorities for the Community Gateway (this repo).

## Week 1 (Done)

- v0 contract: `docs/spec-v0.md`
- Policy + enforcement stub: `policies/default.json`, `src/zeroveil_gateway/app.py`
- CI + tests: `.github/workflows/ci.yml`, `tests/test_gateway_v0.py`
- Community vs Pro boundary + contribution/legal docs: `docs/editions.md`, `CLA.md`, `CONTRIBUTING.md`

## Week 2 (MVP Hardening)

- Multi-tenant auth model (tenant IDs + per-tenant keys + rate limits)
- Request validation hardening (size limits, role validation, better errors)
- Metadata-only audit event schema v1 + retention defaults
- Optional PII/PHI reject-only gate (detect and reject unsafely-scrubbed requests; never "scrub-as-a-service") - Pro/Hosted first
- Threat model doc v1 (conservative claims, abuse cases, non-goals)

## Week 3 (First Real Provider)

- Implement provider adapter (start with OpenRouter) behind policy gates
- Enforce ZDR allowlist as a first-class policy rule
- Consistent upstream error mapping + timeouts + retries

## Week 4 (Policy + Normalization)

- Prompt normalization rules (system preamble injection, tool constraints)
- Policy packs/examples (regulated vs general)
- Conformance tests proving invariants (no content logging by default, scrub attestation required, ZDR enforced)

## Week 5 (Relay Identity / Mixing v0)

- Shared upstream identity implementation (single upstream key)
- Per-tenant isolation controls (rate limiting, quotas, failure isolation)
- Optional small batching window (latency-controlled), behind config

## Week 6 (Compliance Telemetry)

- Audit exports (metadata-only) + signed log option (Pro later)
- Operational metrics without content (latency, token counts, errors)

## Week 7 (Showcase Integration)

- One reference client integration proving infrastructure value
- Reproducible demo script + short walkthrough

## Week 8 (Security + Release)

- Abuse resistance pass + key-handling review
- Public MVP release notes + grant applications kickoff

## ZeroVeil SDK Visibility (Action Required)

- Current intent: keep `zeroveil-sdk` repo private (invite-only) during early development.
- TODO: When ready for broad adoption, make `zeroveil-sdk` public and update docs/links in this repo accordingly.


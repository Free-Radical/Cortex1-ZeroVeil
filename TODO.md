# Cortex1-ZeroVeil - Community Gateway Plan (Weekly)

This file tracks the **weekly execution plan** for the **Community Gateway** (this repo).

## Core Innovation & MVP

**Foundation:** Unique LLM mixer/privacy relay architecture (the moat)
- Breaks user<->prompt correlation at the provider level
- Multi-tenant aggregation through shared relay identity
- No other solution offers provider-side correlation resistance

**MVP Deliverable:** DLP Gateway for developers and enterprises
- OpenAI-compatible proxy with DLP controls for any LLM endpoint
- Two audiences: developers building regulated apps + enterprise IT controlling access
- Routes directly to providers OR forwards to ZeroVeil mixer
- PII rejection, model allowlists, rate limits, audit logging

Both the mixer and gateway share the same core: policy enforcement, provider routing, audit logging. See `docs/architecture.md` for deployment topologies.

## Best practices (edition boundary)

- Community is for **proving core value with minimal trust + minimal ops**:
  - an auditable policy gateway + relay primitives, safe defaults, and a working reference integration
  - OpenAI-compatible drop-in proxy for corporate AI gateway deployments
- Pro/Hosted is for **advanced features** that expand trust/compliance/ops surface:
  - tier escalation, automated cost/pricing policy, enterprise auth/RBAC, compliance exports, signed logs, hosted relay identity at scale
  - Admin dashboard, SIEM integration, per-tenant policy overrides

## Week 1 (Done)

- v0 contract: `docs/spec-v0.md`
- Policy + enforcement stub: `policies/default.json`, `src/zeroveil_gateway/app.py`
- CI + tests: `.github/workflows/ci.yml`, `tests/test_gateway_v0.py`
- Community vs Pro boundary + contribution/legal docs: `docs/editions.md`, `CLA.md`, `CONTRIBUTING.md`

## Week 2 (Done)

- Multi-tenant auth model (tenant IDs + per-tenant keys + rate limits)
- Request validation hardening (size limits, role validation, better errors)
- Metadata-only audit event schema v1 + retention defaults
- PII/PHI reject-only gate (detect and reject; never "scrub-as-a-service") - **enabled by default**
- Threat model doc v1 (conservative claims, abuse cases, non-goals)

## Week 3 (First Real Provider + OpenAI Compatibility)

**Provider Routing:**
- Implement provider adapter (start with OpenRouter) behind policy gates
- Enforce ZDR allowlist as a first-class policy rule
- Consistent upstream error mapping + timeouts + retries

**OpenAI-Compatible Endpoint (Corporate Gateway foundation):**
- Full `/v1/chat/completions` compatibility (drop-in for `OPENAI_API_BASE`)
- `/v1/models` endpoint returning allowed models
- OpenAI error format mapping
- Streaming support (SSE chunked transfer)

## Week 4 (Policy + Normalization)

**Core Policy:**
- Prompt normalization rules (system preamble injection, tool constraints)
- Policy packs/examples (regulated vs general vs corporate-gateway)
- Conformance tests proving invariants (no content logging by default, ZDR enforced)

**Corporate Gateway Mode:**
- `mode: corporate_gateway` policy option (disables scrub attestation requirement)
- Model allowlist/blocklist with glob patterns (`gpt-4-*`, `claude-3-*`)
- Keyword blocking for content policy
- Enhanced PII rejection with entity type breakdown in error responses

## Week 5 (Mixer Primitives + Cost Controls)

Full mixer implementation for both Community and Pro editions. See `docs/mixer-design.md` for technical details.

**Mixer Primitives (both editions):**
- Request batching with configurable windows (min_batch, max_wait)
- Shuffle dispatch (randomized order within batches)
- Timing jitter (50-200ms random delays)
- Header stripping (remove tenant-identifying metadata)
- Request normalization (strip fingerprinting vectors)
- One-time response tokens (unlinkable return routing)

**Cloud-Hosted (both editions):**
- Shared relay identity (ZeroVeil-operated API keys)
- Network effect: larger mixing pool = stronger correlation resistance

**Corporate Gateway - Cost & Rate Controls:**
- Per-tenant rate limiting (requests/minute)
- Token usage tracking (prompt + completion)
- Daily token/cost budgets per tenant
- Cost estimation from model pricing tables

**Pro additions:**
- Advanced abuse resistance controls
- Multi-region routing options
- Stronger tenant isolation guarantees

## Week 6 (Telemetry + Multi-Provider)

**Operational Telemetry (metadata-only):**
- Community: operational metrics without content (latency, token counts, error rates, cost)
- Pro/Hosted: compliance exports and signed/immutable logs (see `docs/editions.md`)

**Multi-Provider Support:**
- Anthropic `/v1/messages` compatibility endpoint
- Request format translation (OpenAI ↔ Anthropic)
- Provider-specific model ID mapping
- Automatic failover between providers

## Week 7 (Showcase Integration)

**Privacy Relay Demo:**
- Reference client integration proving mixer value
- Reproducible demo script + short walkthrough

**Corporate Gateway Demo:**
- Sample corporate policy pack (model allowlist, PII rejection, cost limits)
- Docker Compose deployment example
- Demo: Python app using `OPENAI_API_BASE` → ZeroVeil → OpenAI
- Demo: PII rejection in action (blocked request with entity details)

## Week 8 (Security + Release)

**Security Hardening:**
- Abuse resistance pass + key-handling review
- TLS configuration hardening
- Secrets management documentation (HSM/Vault integration)

**Pro Features (Enterprise):**
- Admin dashboard UI (read-only metrics: requests, blocks, costs by tenant)
- SIEM webhook integration for audit events
- Per-tenant policy overrides
- SSO/OIDC authentication (stubbed, full impl post-MVP)
- Scrubbing webhook integration (forward blocked requests to customer's cleaning service for retry)

**Release:**
- Public MVP release notes
- Corporate AI Gateway deployment guide
- Grant applications kickoff

## ZeroVeil SDK Visibility

- SDK is source-available under BSL (same as gateway)
- Early access is invite-only during initial development
- TODO: Open public access when ready for broad adoption

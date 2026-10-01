# Cortex1-ZeroVeil Architecture

## Executive Summary

Cortex1-ZeroVeil is a **DLP-first LLM gateway**: it enforces policy (PII rejection, ZDR-only intent, redaction attestation) before a request ever reaches a provider, and keeps a metadata-only audit trail. A separate request-aggregation design exists purely as research (see `docs/mixer-design.md`); it is not implemented, not scheduled, and not a feature of any release.

Current releases focus on **enterprise DLP controls**: an OpenAI-compatible gateway with PII rejection, model allowlists, rate limits, and audit logging.

**What is implemented today:**
1. **Content privacy / DLP Gateway (`IMPLEMENTED_NOW`):** policy enforcement, PII rejection, ZDR-only intent, redaction attestation, metadata-only audit logging.

Everything else described as "research" is design work: not built, not scheduled, and not a claim about what ZeroVeil does today.

**Two audiences, same product:**
- **Developers** — Add DLP to regulated apps with one endpoint change
- **Enterprise IT** — Control employee AI access through a corporate proxy

**Important:** We **reject** PII, we don't scrub it. If you send us data to clean, you've already exposed it. ZeroVeil detects PII patterns and blocks the request—your sensitive data never leaves your network.

---

## Implementation Status

**Status:** `IMPLEMENTED_NOW` DLP gateway controls are live and enforced. The request-aggregation design remains research only (`docs/mixer-design.md`), with no committed schedule.

| Component | Status |
|-----------|--------|
| Policy enforcement | Done |
| PII rejection gate | Done (enabled by default) |
| Multi-tenant auth | Done |
| Audit logging | Done |
| Provider routing | Done (OpenRouter) |

See `docs/spec-v0.md` for API contract and `docs/editions.md` for editions.

---

## Problem Statement

Current LLM API usage has a fundamental privacy flaw:

```
User -> API Key -> Cloud Provider
```

Even with "zero data retention" promises, the provider knows:
- Which API key sent each prompt
- Timing and frequency patterns
- Content of each request (even if not stored long-term)

**Result:** The provider sees which API key sent each prompt. ZeroVeil does not change that; it limits what is sent (PII rejection) and what is requested of the provider (zero data retention).

---

## Research Design: Request Aggregation (not implemented, not a feature)

A design for aggregating requests from several tenants behind a shared relay credential is described in `docs/mixer-design.md`. It is a research document only. ZeroVeil v0.2.0 does not implement it, it is not scheduled, and ZeroVeil makes no claim about what such a design would achieve.

---

## Why We Don't Offer PII Scrubbing

### The Privacy Paradox

Many "privacy" services offer to scrub your PII before forwarding to LLMs. This is backwards.

**If you send raw PII to a third party for scrubbing, you've already exposed it.**

It doesn't matter if they promise ZDR, encryption, or compliance certifications. The moment your unredacted data leaves your environment, you've trusted someone else with it.

### Separation of Concerns

| Responsibility | Owner | Rationale |
|----------------|-------|-----------|
| Content privacy (PII/PHI removal) | User | Your data, your environment, your control |

This separation is intentional:
- Minimizes what you trust us with
- Keeps sensitive data in your environment
- Makes our security posture simpler (we never see raw PII)

### Scrubbing Tooling

Scrub locally with your own tooling (for example Presidio) before sending. ZeroVeil ships no scrubbing tool in v0.2.0:
- **Local-only**: Runs entirely in your environment—your data never leaves
- **Optional**: Not part of the gateway

ZeroVeil never asks you to send raw PII to a service for scrubbing.

---

## Architecture Components

### 1. Research: Aggregation Layer (not implemented)

The central aggregation component (research design, not implemented):

- Receives requests from multiple tenants
- Strips/replaces identifying metadata
- Batches requests within configurable windows
- Routes through shared provider credentials
- Demultiplexes responses back to originators

**Design Considerations:**
- Latency impact of batching windows
- Tenant isolation within aggregation
- Request ordering and priority handling
- Failure isolation (one tenant's error doesn't affect others)

---

## Editions Boundary (Community vs Pro)

This repository is the **Community Gateway**: the auditable enforcement core.

ZeroVeil v0.2.0 is **self-hosted only**; there is no ZeroVeil-operated hosted service:

- **Community** — Source-available under PolyForm Noncommercial 1.0.0. Free for personal, educational, nonprofit and government use; companies get a 32-day evaluation under PolyForm Free Trial 1.0.0 (LICENSE-FREE-TRIAL); any other commercial use needs a written license: see COMMERCIAL-LICENSE.md or write to Saqib.Khan@Me.com.
  - `IMPLEMENTED_NOW`: Policy enforcement, PII rejection gate, metadata-only audit events, conformance tests
  - Request aggregation is research only (`docs/mixer-design.md`); not implemented, not scheduled.
- **Pro:** a commercial license is available (contact Saqib.Khan@Me.com). Pro features are not part of v0.2.0.

See `docs/editions.md` for the canonical split and `docs/mixer-design.md` for the research design.

### 2. ZDR Enforcement

- The policy requires clients to send `zdr_only: true` (`enforce_zdr_only`).
- Every OpenRouter request carries `zdr: true`, `data_collection: "deny"` and `allow_fallbacks: false`; a caller cannot weaken these.
- OpenRouter is the only supported provider (`allowed_providers: ["openrouter"]`). ZeroVeil does not verify what OpenRouter or the upstream model providers actually retain.
- Audit events record the provider and model, never content.

### 3. Client SDKs

Client SDKs are not part of v0.2.0.

---

## Security Model

**Guiding Principle:** ZeroVeil is a DLP/redaction-attestation gateway. It does not provide anonymity, unlinkability, or correlation resistance.

### Threat Mitigation

| Threat | Mitigation |
|--------|------------|
| PII exposure to providers | Gateway PII rejection gate + user redacts locally before sending |
| Gateway operator logging | Policy + audit (trust required) |
| Provider-side user correlation | Not mitigated |
| Metadata fingerprinting | Not mitigated |

### What This Does NOT Protect Against

- Malicious gateway operator (requires trust)
- Content-based fingerprinting (if content is unique enough)
- Legal compulsion of the gateway operator
- Side-channel attacks on the gateway host
- PII in content (user responsibility to scrub)

### Logging Policy

**Principle:** Minimize logging to operational necessity. Content is never persisted.

| Category | Policy | Retention | Rationale |
|----------|--------|-----------|-----------|
| Prompt/response content | Never persisted | N/A | Core privacy guarantee |
| Operational metrics | TBD | TBD | Error rates, latency (aggregate only) |
| Security events | TBD | TBD | Auth failures, anomalies |
| Provider routing | TBD | TBD | Which provider handled request (no content) |

*Specific retention periods and operational logging scope to be defined during implementation.*

### Trust Boundaries

```
┌─────────────────────────────────────────────────────────┐
│ USER ENVIRONMENT (full trust)                           │
│   - Raw content with PII                                │
│   - PII scrubbing happens HERE                          │
│   - User identity                                       │
└─────────────────────┬───────────────────────────────────┘
                      │ (scrubbed content only)
┌─────────────────────▼───────────────────────────────────┐
│ CORTEX1-ZEROVEIL (trust required)                       │
│   - Sees scrubbed requests only                         │
│   - Enforces policy                                     │
│   - Enforces ZDR                                        │
│   - Never sees raw PII                                  │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│ CLOUD PROVIDER (zero trust)                             │
│   - Sees the operator's API key and the redacted prompt │
│   - ZDR policy enforced                                 │
└─────────────────────────────────────────────────────────┘
```

### Abuse Prevention

**Challenge:** Preventing abuse while minimizing what the gateway logs about users.

**Approach:**
- **Rate limiting:** Token-based limits per tenant
- **Content policy:** Provider-side content policies apply; the gateway's PII gate (on by default) inspects every request before it is forwarded, and the gateway does not otherwise moderate content
- **Operator policy:** The operator of a deployment decides acceptable use and can revoke tenant keys

**What we will NOT do:**
- Content inspection or logging for abuse detection
- User identification based on content patterns
- Proactive monitoring of request content

*Specific abuse prevention mechanisms to be finalized during implementation, balancing privacy preservation with operational necessity.*

---

## Deployment Models

ZeroVeil is self-hosted.

### Self-Hosted

Organization runs its own gateway:
- Full control over infrastructure
- No external trust required
- Data sovereignty / air-gap compliance

**Best for:** Air-gapped environments, strict data sovereignty requirements, large enterprises with internal multi-tenancy.

### Corporate AI Gateway Mode

ZeroVeil can operate as an enterprise DLP proxy that intercepts and controls all LLM API traffic, routing to providers directly:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Corporate Network                                                       │
│                                                                         │
│  ┌─────────────┐     ┌─────────────────────────────────────────────┐   │
│  │ Developer   │     │           ZeroVeil Gateway                  │   │
│  │ Workstation │     │  ┌─────────────────────────────────────┐    │   │
│  │             │     │  │ Ingress Layer                       │    │   │
│  │ OPENAI_API_ │────►│  │ - OpenAI-compatible endpoint        │    │   │
│  │ BASE=proxy  │     │  │                                     │    │   │
│  └─────────────┘     │  └──────────────┬──────────────────────┘    │   │
│                      │                 │                           │   │
│  ┌─────────────┐     │  ┌──────────────▼──────────────────────┐    │   │
│  │ CI/CD       │     │  │ Policy & Inspection Layer           │    │   │
│  │ Pipeline    │────►│  │ - PII/PHI rejection gate            │    │   │
│  └─────────────┘     │  │ - Model allowlist enforcement       │    │   │
│                      │  │ - Rate limiting                     │    │   │
│                      │  └──────────────┬──────────────────────┘    │   │
│                      │                 │                           │   │
│                      │  ┌──────────────▼──────────────────────┐    │   │
│                      │  │ Audit Layer (metadata-only)         │    │   │
│                      │  └──────────────┬──────────────────────┘    │   │
│                      │                 │                           │   │
│                      │  ┌──────────────▼──────────────────────┐    │   │
│                      │  │ Egress → LLM provider (OpenRouter)  │    │   │
│                      │  └──────────────┬──────────────────────┘    │   │
│                      └─────────────────┼───────────────────────────┘   │
│                                        │                               │
│  Firewall: BLOCK direct access to      │                               │
│  direct provider APIs                  │                               │
└────────────────────────────────────────┼───────────────────────────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │ OpenRouter          │
                              │                     │
                              └─────────────────────┘
```

**Egress routing:** requests go to OpenRouter, the only supported provider, after the DLP controls pass.

**Attestation option:** a corporate deployment can set `require_scrubbed_attestation` to `false` so clients don't need to send `metadata.scrubbed`. The PII gate is on by default either way and never relies on the attestation. This enables drop-in deployment where applications only need to change `OPENAI_API_BASE`.

**Integration options:**

| Mode | How It Works | Pros | Cons |
|------|--------------|------|------|
| **Direct endpoint** | Apps set `OPENAI_API_BASE` to gateway | Simple, works with any OpenAI-compatible client | Requires app configuration |
| **DNS override** | Internal DNS resolves `api.openai.com` → gateway | Zero app changes | Requires corporate CA on devices |
| **Upstream proxy** | Gateway sits behind existing proxy (Squid, Zscaler) | Integrates with existing infra | More complex |

**Network enforcement:** For gateway mode to be effective, direct access to AI providers must be blocked at the firewall. Native desktop apps (ChatGPT macOS/Windows) use certificate pinning and cannot be proxied—block them entirely and force users to web/API channels.

**Best for:** Enterprises requiring DLP controls, compliance logging, and centralized AI governance.

---

## Compliance

ZeroVeil holds no certifications. See [docs/compliance.md](compliance.md) for what the gateway does and what the operator must provide (TLS, encryption at rest, incident response, log integrity).

---

## Future Directions

- Differential privacy for statistical queries
- Formal verification of privacy properties (long-term goal, as resources permit)
- Independent security audits
- PII/PHI leak detection to identify insufficient or failed data scrubbing before it reaches the gateway

---

*Document Version: 1.4*
*Date: 2026-10-01*
*Author: Saqib Ali Khan*
*Part of the Cortex1 family*

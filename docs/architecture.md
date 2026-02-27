# Cortex1-ZeroVeil Architecture

## Executive Summary

Cortex1-ZeroVeil is a **privacy-first LLM gateway**. The long-term architecture includes an LLM mixer/privacy relay intended to reduce user-to-prompt correlation risk at the provider level through multi-tenant aggregation.

Current releases focus on **enterprise DLP controls**: an OpenAI-compatible gateway with PII rejection, model allowlists, rate limits, and audit logging.

**The two value propositions:**
1. **Identity privacy (`PLANNED_COMMUNITY`):** Mixer architecture intended to reduce linkability
2. **Content privacy (`IMPLEMENTED_NOW`):** DLP Gateway for developers and enterprises

**Two audiences, same product:**
- **Developers** — Add DLP to regulated apps with one endpoint change
- **Enterprise IT** — Control employee AI access through a corporate proxy

**Important:** We **reject** PII, we don't scrub it. If you send us data to clean, you've already exposed it. ZeroVeil detects PII patterns and blocks the request—your sensitive data never leaves your network.

---

## Implementation Status

**Week 2 complete.** `IMPLEMENTED_NOW` DLP gateway controls are live; `PLANNED_COMMUNITY` mixer primitives are targeted for Week 5.

| Component | Status |
|-----------|--------|
| Policy enforcement | Done |
| PII rejection gate | Done (enabled by default) |
| Multi-tenant auth | Done |
| Audit logging | Done |
| Provider routing | Stubbed (Week 3) |
| Mixer primitives | Week 5 (batching, shuffle, jitter, header stripping) |

See `docs/spec-v0.md` for API contract and `docs/editions.md` for Community vs Pro boundary.

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

**Result:** User<->prompt correlation is fully visible to the provider.

Existing solutions address content privacy (PII scrubbing) but not **identity privacy** at the provider level.

---

## Solution Blueprint: Mixer Architecture (`PLANNED_COMMUNITY`)

### Core Concept

```
User A --->                                ---> Response A
User B --+--> [Aggregation Layer] ---> [Shared Identity] ---> Cloud --+--> Response B
User C --->                                ---> Response C
```

**Analogy:** Mix networks (a concept from anonymous communication research, similar in principle to cryptocurrency tumblers) break the sender<->receiver link by pooling messages through intermediate nodes. Cortex1-ZeroVeil applies this principle to LLM interactions, reducing the user<->prompt linkability by pooling requests through a shared relay identity.

### Privacy Properties

| Property | Mechanism |
|----------|-----------|
| Provider-side correlation resistance | Planned shared relay identity |
| User<->prompt unlinkability | Planned aggregation to reduce correlation |
| Timing obfuscation | Planned batching windows to reduce fingerprinting |
| Reduced metadata exposure | Planned shared patterns across tenants |

### Trust Model

The relay operator (Cortex1-ZeroVeil) sees individual requests. Users must trust:
1. Relay does not log prompt content
2. Relay does not correlate users to prompts
3. Relay enforces stated ZDR policies

This is a **trust tradeoff**, not trustless privacy. Users who cannot accept this should self-host or use direct API access.

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
| Identity privacy (user<->prompt unlinking) | ZeroVeil | Requires aggregation infrastructure |

This separation is intentional:
- Minimizes what you trust us with
- Keeps sensitive data in your environment
- Makes our security posture simpler (we never see raw PII)

### Scrubbing Tooling

ZeroVeil SDK provides source-available local scrubbing tooling:
- **Local-only**: Runs entirely in your environment—your data never leaves
- **Source-available (BSL)**: Auditable, reviewable, and testable
- **Optional**: Not part of the relay service—use your own scrubbing if preferred

*Note: The `zeroveil-sdk` repository is source-available under BSL. Early access is invite-only during initial development.*

We will never ask you to send raw PII to our servers.

For advanced requirements (reversible tokens, multiple backends, audit logging), see ZeroVeil Pro.

---

## Architecture Components

### 1. Aggregation Layer (Core)

The central mixer component:

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

Both editions are available **self-hosted** or **cloud-hosted** (operated by ZeroVeil):

- **Community (free, BSL):**
  - `IMPLEMENTED_NOW`: Policy enforcement, PII rejection gate, metadata-only audit events, conformance tests
  - `PLANNED_COMMUNITY`: Mixer primitives (batching, shuffle, jitter, header stripping), shared relay identity (cloud-hosted deployment)
- **Pro (paid):**
  - `PRO_ONLY`: Enterprise auth (SSO/SAML), compliance evidence bundles, signed audit logs, advanced routing/governance

**Recommendation:** For small-to-medium organizations, cloud-hosted is preferable because larger mixing pools provide stronger correlation resistance.

See `docs/editions.md` for the canonical split and `docs/mixer-design.md` for mixer technical details.

### 2. ZDR Enforcement

Strict Zero Data Retention policy enforcement:

- Provider allow-list based on contractual ZDR commitments
- Runtime verification where provider APIs support it (currently limited; most verification is policy-based)
- Audit logging of provider selection (without content)
- Fallback behavior when ZDR cannot be verified

**Supported Providers (must verify ZDR):**
- Providers with contractual ZDR guarantees
- Self-hosted endpoints
- Custom deployments with verified retention policies

**Provider Optimization:**
We are implementing periodic reviews of supported LLM providers to optimize routing decisions based on:
- Cost efficiency (price per token/request)
- Response latency and throughput
- Task-specific performance (coding, analysis, creative, etc.)
- ZDR policy compliance status
- Reliability and uptime history

Tier escalation and automated pricing/cost policy are **Pro/Hosted** responsibilities. The Community gateway stays conservative and auditable; it provides policy enforcement and provider adapter primitives.

**Aggregation Benefits:**
The multi-tenant architecture provides compounding advantages:

*Correlation Resistance (Risk Reduction):*
- Larger user base = larger "mixing set" -> lower correlation risk (not a guarantee)
- More traffic = better timing obfuscation through natural batching
- Diverse usage patterns make individual fingerprinting harder

*Economic:*
- Aggregated volume qualifies for better provider pricing tiers
- Collective buying power enables enterprise rate negotiations
- Shared infrastructure and compliance costs

This is the intended network effect once mixer primitives are enabled: more users -> stronger mixing set and lower costs for everyone.

### 3. Client SDK

ZeroVeil provides a source-available client SDK (BSL) for local PII scrubbing and relay access.

**Installation:**
```bash
pip install zeroveil
```

- SDK repo: private for now (invite-only)

#### SDK Tiers

| Tier | Distribution | Features |
|------|--------------|----------|
| **ZeroVeil SDK** (Free) | `pip install zeroveil` | Presidio-based PII scrubbing, relay client |
| **ZeroVeil Pro** (Paid) | Private PyPI | Deterministic/non-deterministic modes, reversible token mapping, multiple backends (Presidio, regex, scrubadub), audit logging |

Contact Saqib.Khan@Me.com for Pro tier access.

#### Client-Side Responsibilities

**Device-Aware Routing:**
| Mode | Hardware | Strategy |
|------|----------|----------|
| LOCAL_PREFERRED | GPU (8GB+ VRAM) | Local models preferred, relay fallback |
| HYBRID | CPU (16GB+ RAM) | Local preprocessing, relay for complex tasks |
| CLOUD_ONLY | Minimal | Relay with mandatory local PII scrubbing |

**Pro/Hosted routing policy:**
- Tier escalation and cost-optimized routing (if used) are Pro/Hosted features and should not be required to adopt the Community gateway.

*Note: Device detection and local-first routing occur client-side. The relay service handles aggregation and provider routing for cloud-bound requests only.*

---

## Security Model

**Guiding Principle:** We aim to maximize user privacy and reduce correlation risk. This is risk reduction, not a guarantee of anonymity.

### Threat Mitigation

| Threat | Mitigation |
|--------|------------|
| Provider-side user correlation | Aggregation through shared identity |
| PII exposure to providers | User scrubs locally before sending |
| Metadata fingerprinting | Batching, timing normalization |
| Relay operator logging | Policy + audit (trust required) |

### What This Does NOT Protect Against

- Malicious relay operator (requires trust)
- Content-based fingerprinting (if content is unique enough)
- Legal compulsion of relay operator
- Side-channel attacks on relay infrastructure
- PII in content (user responsibility to scrub)

### Logging Policy

**Principle:** Minimize logging to operational necessity. Content is never persisted.

| Category | Policy | Retention | Rationale |
|----------|--------|-----------|-----------|
| Prompt/response content | Never persisted | N/A | Core privacy guarantee |
| User<->request correlation | Not retained beyond session | N/A | Defeats mixer purpose |
| Operational metrics | TBD | TBD | Error rates, latency (aggregate only) |
| Security events | TBD | TBD | Auth failures, anomalies |
| Provider routing | TBD | TBD | Which provider handled request (no content) |

*Specific retention periods and operational logging scope to be defined during implementation. Session-scoped correlation (required for response routing) is ephemeral and not persisted.*

**Jurisdictional Intent:** We plan to operate infrastructure in privacy-respecting jurisdictions with strong data protection laws and limited compelled disclosure regimes, to the extent commercially feasible. Specific jurisdictions to be determined.

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
│   - Performs aggregation                                │
│   - Enforces ZDR                                        │
│   - Never sees raw PII                                  │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│ CLOUD PROVIDER (zero trust)                             │
│   - Sees only relay identity                            │
│   - Cannot correlate to individual users                │
│   - ZDR policy enforced                                 │
└─────────────────────────────────────────────────────────┘
```

### Abuse Prevention

**Challenge:** Preventing abuse while preserving correlation-resistance goals requires privacy-preserving techniques.

**Approach:**
- **Rate limiting:** Token-based limits without persistent identity correlation
- **Content policy:** Provider-side content policies apply; relay does not inspect content
- **Terms of Service:** Users agree to acceptable use; violations may result in token revocation
- **Cryptographic accountability:** Privacy-preserving mechanisms (e.g., blind signatures) may enable revocation without identification

**What we will NOT do:**
- Content inspection or logging for abuse detection
- User identification based on content patterns
- Proactive monitoring of request content

**Legal compliance:** We will respond to valid legal process in operating jurisdictions. See Transparency & Trust Commitments for warrant canary and disclosure policies.

*Specific abuse prevention mechanisms to be finalized during implementation, balancing privacy preservation with operational necessity.*

---

## Deployment Models

Both Community and Pro editions support either deployment model.

### Cloud-Hosted (Recommended for Most Users)

Cortex1-ZeroVeil operates the relay:
- **Network effect:** Larger mixing pool = stronger correlation resistance
- Simplest setup, no infrastructure to maintain
- Shared relay identity for all tenants
- Economies of scale

**Best for:** Small-to-medium organizations, teams without dedicated ops.

### Self-Hosted

Organization runs own relay:
- Full control over infrastructure
- No external trust required
- Data sovereignty / air-gap compliance
- **No mixing benefit** unless you have multiple internal tenants

**Best for:** Air-gapped environments, strict data sovereignty requirements, large enterprises with internal multi-tenancy.

### Corporate AI Gateway Mode

ZeroVeil can operate as an enterprise DLP proxy that intercepts and controls all LLM API traffic. The gateway can route to providers directly OR forward to a ZeroVeil mixer (self-hosted or cloud) for correlation resistance:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Corporate Network                                                       │
│                                                                         │
│  ┌─────────────┐     ┌─────────────────────────────────────────────┐   │
│  │ Developer   │     │           ZeroVeil Gateway                  │   │
│  │ Workstation │     │  ┌─────────────────────────────────────┐    │   │
│  │             │     │  │ Ingress Layer                       │    │   │
│  │ OPENAI_API_ │────►│  │ - OpenAI-compatible endpoint        │    │   │
│  │ BASE=proxy  │     │  │ - Anthropic-compatible endpoint     │    │   │
│  └─────────────┘     │  └──────────────┬──────────────────────┘    │   │
│                      │                 │                           │   │
│  ┌─────────────┐     │  ┌──────────────▼──────────────────────┐    │   │
│  │ CI/CD       │     │  │ Policy & Inspection Layer           │    │   │
│  │ Pipeline    │────►│  │ - PII/PHI rejection gate            │    │   │
│  └─────────────┘     │  │ - Model allowlist enforcement       │    │   │
│                      │  │ - Cost/rate limiting                │    │   │
│                      │  └──────────────┬──────────────────────┘    │   │
│                      │                 │                           │   │
│                      │  ┌──────────────▼──────────────────────┐    │   │
│                      │  │ Audit Layer (metadata-only)         │    │   │
│                      │  └──────────────┬──────────────────────┘    │   │
│                      │                 │                           │   │
│                      │  ┌──────────────▼──────────────────────┐    │   │
│                      │  │ Egress → Route to:                  │    │   │
│                      │  │   A) LLM providers directly, OR     │    │   │
│                      │  │   B) ZeroVeil Mixer (for mixing)    │    │   │
│                      │  └──────────────┬──────────────────────┘    │   │
│                      └─────────────────┼───────────────────────────┘   │
│                                        │                               │
│  Firewall: BLOCK direct access to      │                               │
│  api.openai.com, api.anthropic.com     │                               │
└────────────────────────────────────────┼───────────────────────────────┘
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
         ┌─────────────────────┐               ┌─────────────────────────┐
         │ LLM Providers       │               │ ZeroVeil Mixer          │
         │ (direct)            │               │ (self-hosted or cloud)  │
         └─────────────────────┘               │         │               │
                                               │         ▼               │
                                               │  ┌─────────────────┐    │
                                               │  │ LLM Providers   │    │
                                               │  │ (via mixer)     │    │
                                               │  └─────────────────┘    │
                                               └─────────────────────────┘
```

**Egress routing options:**
- **Direct to providers:** DLP controls only, no mixing (simpler, lower latency)
- **Via ZeroVeil Mixer (self-hosted):** DLP + mixing with full control, no external trust
- **Via ZeroVeil Mixer (cloud):** DLP + mixing with network effect benefits (larger mixing pool)

**Key difference from Privacy Relay mode:** In Corporate Gateway mode, clients don't need to send attestation headers (`require_scrubbed_attestation` is disabled for simpler integration). **PII scanning is ALWAYS ON in both modes** — the gateway never relies on client attestation for security. This enables drop-in deployment where applications only need to change `OPENAI_API_BASE`.

**Integration options:**

| Mode | How It Works | Pros | Cons |
|------|--------------|------|------|
| **Direct endpoint** | Apps set `OPENAI_API_BASE` to gateway | Simple, works with any OpenAI-compatible client | Requires app configuration |
| **DNS override** | Internal DNS resolves `api.openai.com` → gateway | Zero app changes | Requires corporate CA on devices |
| **Upstream proxy** | Gateway sits behind existing proxy (Squid, Zscaler) | Integrates with existing infra | More complex |

**Network enforcement:** For gateway mode to be effective, direct access to AI providers must be blocked at the firewall. Native desktop apps (ChatGPT macOS/Windows) use certificate pinning and cannot be proxied—block them entirely and force users to web/API channels.

**Best for:** Enterprises requiring DLP controls, compliance logging, and centralized AI governance—with optional correlation resistance via mixer routing.

---

## Compliance & Security Standards

ZeroVeil Pro is architected to support major security frameworks:

| Framework | ZeroVeil Alignment |
|-----------|-------------------|
| HITRUST CSF | PHI scrubbed client-side, audit logging |
| SOC 2 Type II | Access controls, audit trails, availability |
| ISO 27001/27701 | Information security + privacy management |
| NIST CSF | US enterprise security baseline |
| NIST AI RMF | AI-specific privacy and risk controls |
| HIPAA | BAA support, PHI never reaches relay |
| GDPR | Data minimization, DPA templates |

See [docs/compliance.md](compliance.md) for detailed control mappings across all frameworks.

**Regulatory notes:**
- **HIPAA**: PHI must be scrubbed before reaching relay; consult qualified legal counsel for BAA requirements
- **GDPR**: Data minimization by design; processor agreements available
- **CCPA**: User rights and disclosure procedures documented

Note: By requiring local PII scrubbing, compliance burden is simplified — we are not a processor of personal data.

---

## Transparency & Trust Commitments

Policy commitments we intend to uphold from day one of operation:

### Warrant Canary

Where legally permitted in our operating jurisdictions, we will maintain a regularly updated warrant canary to signal whether we have received legal demands that we cannot disclose. Absence of update or removal of the canary should be treated as a potential compromise indicator.

*Note: Warrant canary legality and effectiveness varies by jurisdiction. Users should understand the limitations of this mechanism in their specific legal context.*

### Incident Response

In the event of a security incident affecting user privacy or correlation-risk posture:
- Users will be notified promptly through published channels
- Scope and nature of the incident will be disclosed to the extent legally permitted
- Post-incident analysis will be published

### Service Termination

If ZeroVeil ceases operation:
- Users will receive advance notice (minimum period TBD)
- Any ephemeral data will be securely destroyed
- Clear documentation of shutdown procedures will be provided

*Specific procedures and timelines to be formalized before production launch.*

---

## Future Directions

- Differential privacy for statistical queries
- Cryptographic mixing protocols (reduce trust requirements)
- Multi-relay chaining for increased correlation resistance
- Formal verification of privacy properties (long-term goal, as resources permit)
- Independent security audits
- PII/PHI leak detection to identify insufficient or failed data scrubbing before relay
- Transparency reports (periodic publication of aggregate statistics, legal request counts)
- Source-available roadmap (timeline for code auditability)
- Federated relay architecture (multiple trusted operators for distributed trust)
- SDK enhancements: additional scrubbing backends, language support expansion

---

*Document Version: 1.3*
*Date: December 2025*
*Author: Saqib Ali Khan*
*Part of the Cortex1 family*

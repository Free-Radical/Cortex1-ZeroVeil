# Cortex1-ZeroVeil Architecture

## Executive Summary

Cortex1-ZeroVeil is a privacy-preserving relay layer for LLM interactions. Its core innovation is a **multi-tenant aggregation architecture** (mixer) that breaks user-to-prompt correlation at the cloud provider level, combined with strict Zero Data Retention enforcement.

**Important:** PII/PHI scrubbing is explicitly NOT part of the relay service. Users must scrub content locally before sending to ZeroVeil. Sending raw PII to any third party — including us — defeats the purpose of privacy protection.

---

## Problem Statement

Current LLM API usage has a fundamental privacy flaw:

```
User → API Key → Cloud Provider
```

Even with "zero data retention" promises, the provider knows:
- Which API key sent each prompt
- Timing and frequency patterns
- Content of each request (even if not stored long-term)

**Result:** User↔prompt correlation is fully visible to the provider.

Existing solutions address content privacy (PII scrubbing) but not **identity privacy** at the provider level.

---

## Solution: Mixer Architecture

### Core Concept

```
User A ─┐                                    ┌─→ Response A
User B ─┼─→ [Aggregation Layer] ─→ [Shared Identity] ─→ Cloud ─┼─→ Response B
User C ─┘                                    └─→ Response C
```

**Analogy:** Bitcoin mixers break the sender↔receiver link by pooling transactions through intermediate wallets. Cortex1-ZeroVeil breaks the user↔prompt link by pooling requests through a shared relay identity.

### Privacy Properties

| Property | Mechanism |
|----------|-----------|
| Provider-side anonymity | Single relay identity for all requests |
| User↔prompt unlinkability | Aggregation breaks correlation |
| Timing obfuscation | Batching windows reduce fingerprinting |
| Reduced metadata exposure | Shared patterns across tenants |

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
| Identity privacy (user↔prompt unlinking) | ZeroVeil | Requires aggregation infrastructure |

This separation is intentional:
- Minimizes what you trust us with
- Keeps sensitive data in your environment
- Makes our security posture simpler (we never see raw PII)

### Future Tooling

If market demand exists, we may provide scrubbing tools — but they would be:
- **Local-only**: Runs in your environment
- **Open source**: Auditable by you
- **Optional**: Not part of the relay service

We will never ask you to send raw PII to our servers.

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

### 2. ZDR Enforcement

Strict Zero Data Retention policy enforcement:

- Provider allow-list with verified ZDR policies
- Runtime verification where APIs support it
- Audit logging of provider selection (without content)
- Fallback behavior when ZDR cannot be verified

**Supported Providers (must verify ZDR):**
- Providers with contractual ZDR guarantees
- Self-hosted endpoints
- Custom deployments with verified retention policies

### 3. Routing Layer

Intelligent request routing:

**Device-Aware Modes:**
| Mode | Hardware | Strategy |
|------|----------|----------|
| Mode A | GPU (e.g., RTX 4070+) | Local 8B+ models preferred |
| Mode B | CPU only | Local small models; cloud for complex |
| Mode C | Minimal | Cloud-dominant with local preprocessing |

**Cost-Optimized Escalation:**
| Tier | Purpose | Trigger |
|------|---------|---------|
| Tier 1 | Default | Initial attempt (~80% of requests) |
| Tier 2 | Fallback | Tier 1 failure |
| Tier 3 | Critical | VIP items or Tier 2 failure |

Tier 3 failure → flag for human review.

---

## Security Model

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

---

## Deployment Models

### Hosted Relay (Default)

Cortex1-ZeroVeil operates the relay:
- Simplest setup
- Requires trust in operator
- Shared infrastructure, economies of scale

### Self-Hosted Relay

Organization runs own relay:
- Full control
- No external trust required
- Higher operational burden

### Federated Relay

Multiple trusted operators:
- Distributed trust
- Resilience
- Complex coordination

---

## Compliance Considerations

- **GDPR**: Data minimization, purpose limitation, processor agreements
- **HIPAA**: PHI must be scrubbed before reaching relay; no BAA needed if we never see PHI
- **SOC 2**: Audit logging, access controls on relay
- **CCPA**: User rights, disclosure requirements

Note: By requiring local PII scrubbing, compliance burden is simplified — we are not a processor of personal data.

---

## Future Directions

- Differential privacy for statistical queries
- Cryptographic mixing protocols (reduce trust requirements)
- Multi-relay chaining (onion routing for LLMs)
- Formal verification of privacy properties
- Independent security audits
- Local-only, open-source scrubbing toolkit (if demand exists)

---

*Document Version: 1.1*
*Date: December 2025*
*Author: Saqib Ali Khan*
*Part of the Cortex1 family*

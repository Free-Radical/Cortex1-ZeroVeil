# Editions (Community vs Pro)

This repository is the **Community Gateway** with enterprise DLP controls.

**Core innovation (`PLANNED_COMMUNITY`):** Mixer architecture designed to reduce user<->prompt correlation at the provider level.

**MVP focus (`IMPLEMENTED_NOW`):** DLP Gateway for developers and enterprises (PII rejection, model allowlists, audit logging).

**Status labels used in this document**
- `IMPLEMENTED_NOW`: Available in current Community releases
- `PLANNED_COMMUNITY`: On Community roadmap, not implemented yet
- `PRO_ONLY`: Available only in Pro

**Two audiences, same product:**
1. **Developers** — Add DLP to your regulated app with one endpoint change
2. **Enterprise IT** — Control employee AI access through a corporate proxy

Both editions are available **self-hosted** or **cloud-hosted** (operated by ZeroVeil).

## Deployment Options

| Option | Who Operates | Relay Identity | Best For |
|--------|--------------|----------------|----------|
| **Self-Hosted** | You | Your own API keys | Full control, air-gapped environments |
| **Cloud-Hosted** | ZeroVeil | Shared (ZeroVeil-operated) | Network effect benefits, lower ops burden |

**Recommendation:** For small-to-medium organizations, **cloud-hosted is preferable** because larger mixing pools provide stronger correlation resistance once mixer primitives are enabled. Self-hosting makes sense for air-gapped environments or organizations with strict data sovereignty requirements.

---

## Community (Free, BSL)

Community provides the enforceable DLP gateway today, with mixer primitives planned.

**`PLANNED_COMMUNITY` Mixer Architecture (Core Innovation):**
- Request batching with configurable windows
- Shuffle dispatch (randomized order within batches)
- Timing jitter (50-200ms random delays)
- Header stripping (remove tenant-identifying metadata)
- One-time response tokens (unlinkable return routing)
- Shared relay identity (cloud-hosted only)

**`IMPLEMENTED_NOW` Corporate AI Gateway (MVP Use Case):**
- OpenAI-compatible `/v1/chat/completions` endpoint (drop-in `OPENAI_API_BASE` replacement)
- PII rejection gate with configurable sensitivity levels (enabled by default)
- Model allowlist/blocklist with glob patterns (`gpt-4-*`, `claude-3-*`)
- Per-tenant rate limiting (requests/minute)
- Basic cost tracking (token counts)
- Metadata-only audit events (no prompt/response logging)
- Route directly to providers
- `PLANNED_COMMUNITY`: Optional forwarding to ZeroVeil mixer

**Core Gateway Features:**
- Policy schema + enforcement (ZDR-only, allowlists, limits, tool constraints)
- PII scanning ALWAYS ON (failsafe design — no bypass, no exceptions)
- Client attestation logging (evidence for audit, never bypasses scanning)
- Prompt normalization and policy preambles
- Provider adapters (community-maintained)
- Conformance tests proving policy + logging invariants
- Threat model and conservative claim framing ("risk reduction")

**Available as:** Self-hosted or ZeroVeil Cloud

---

## Pro (Paid)

Enterprise features on top of Community (`PRO_ONLY` unless stated otherwise).

**Enterprise Auth & Governance:**
- SSO/SAML/OIDC and SCIM provisioning
- Fine-grained RBAC, per-app policies, change control workflows
- Advanced governance packs and admin UI

**Compliance & Audit:**
- Architecture aligned with:
  - HITRUST CSF, SOC 2 Type II, ISO 27001/27002
  - ISO 27701 (privacy management)
  - NIST Cybersecurity Framework (CSF)
  - NIST AI Risk Management Framework (AI RMF)
- Compliance evidence bundles for customer audits (access logs, data flow diagrams, control matrices)
- Signed/immutable audit log integrations and exports
- Security integrations (SIEM, KMS/HSM, key rotation tooling)
- Pre-built documentation for HIPAA BAA, GDPR DPA requirements

*See [docs/compliance.md](compliance.md) for detailed control mappings across all frameworks.*

*Note: ZeroVeil Pro is designed to support customers' compliance programs. Formal certifications (SOC 2, HITRUST, ISO 27001, FedRAMP) for ZeroVeil Hosted are on the roadmap pending scale.*

**Advanced Privacy:**
- Custom PII/PHI detection policies (additional patterns beyond preset Community rules)
- Signed scrub reports from SDK (cryptographic attestation verification)
- Attestation failure tracking and dashboards (detect misbehaving clients)
- Advanced abuse resistance / multi-region routing controls
- Tier escalation and automated cost/pricing policy

**Corporate AI Gateway (Pro):**
- Admin dashboard UI (requests, blocks, costs by tenant)
- SIEM webhook integration for audit events
- Per-tenant policy overrides (different models/limits per department)
- Daily token/cost budgets with alerts
- Blocked content logging to secure store (for incident investigation)
- SSO/OIDC authentication for tenant management
- Scrubbing webhook integration (forward blocked requests to customer's cleaning service for retry)

**SDK Pro Features:**
- Deterministic and non-deterministic scrubbing modes
- Reversible token mapping (recover original values post-processing)
- Multiple scrubbing backends (Presidio, regex, scrubadub)
- Audit logging for compliance

**Available as:** Self-hosted or ZeroVeil Cloud (with SLAs, monitoring, incident response)

---

## Network Effect: Why Cloud Beats Self-Hosted for Privacy

The mixer's effectiveness depends on the size of the mixing pool:

| Pool Size | Correlation Resistance | Timing Obfuscation |
|-----------|------------------------|-------------------|
| 1 tenant (self-hosted, solo) | None | None |
| 5-10 tenants | Weak | Basic |
| 100+ tenants | Strong | Good |
| 1000+ tenants | Very strong | Excellent |

**Cloud-hosted Community** benefits from the aggregate traffic of all ZeroVeil users once mixer primitives are enabled. Self-hosting only makes sense when:
- You have strict air-gap requirements
- Data sovereignty prevents any external relay
- You operate multiple internal tenants yourself

For everyone else: the shared mixing pool provides better privacy than isolated self-hosting.

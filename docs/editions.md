# Editions (Community vs Pro vs Hosted)

This repository is the **Community Gateway**: the auditable core that enforces policy and defines the trust posture.

## Community (Public, BSL)

- FastAPI gateway implementing `/v1/chat/completions`
- Policy schema + enforcement (ZDR-only, allowlists, limits, tool constraints)
- Scrub attestation enforcement (reject unsafely-marked requests)
- Prompt normalization and policy preambles
- Provider adapters (community-maintained)
- Metadata-only audit events by default (no prompt/response logging)
- Conformance tests proving policy + logging invariants
- Threat model and conservative claim framing (“risk reduction”)

## Pro (Paid, Private)

- Enterprise auth (SSO/SAML/OIDC) and SCIM provisioning
- Fine-grained RBAC, per-app policies, change control workflows
- Compliance reporting and evidence bundles (SOC2/HIPAA/ISO workflows)
- Signed/immutable audit log integrations and exports
- Optional PII/PHI **reject-only** ingress checks (detect and reject unsafely-scrubbed requests; never “scrub-as-a-service”)
- Advanced governance packs and admin UI
- Security integrations (SIEM, KMS/HSM, key rotation tooling)
- Advanced abuse resistance / multi-region routing controls
- Optional deterministic reversible token mapping + audit-grade scrubbing features (ZeroVeil Pro)

## Hosted (ZeroVeil Cloud)

- Managed deployment of Pro features with SLAs, monitoring, and incident response
- Shared upstream credentials (the “relay identity”) operated by ZeroVeil

# Compliance & Security Controls

ZeroVeil is a self-hosted gateway. It holds no certifications (SOC 2, ISO 27001, HITRUST, FedRAMP or otherwise) and is not itself a compliance program. It supplies a few technical controls that can feed an operator's own program; everything else is the operator's responsibility.

---

## What the gateway does

| Area | Behavior in v0.2.0 |
|------|--------------------|
| API authentication | Per-tenant API keys stored as SHA-256 hashes in `tenants/*.json`, compared in constant time; legacy single-key mode via `ZEROVEIL_API_KEY` |
| Rate limits | Per-tenant requests per minute and tokens per day (in memory, reset on restart) |
| PII gate | Regex rejection of SSN, credit card, email, phone and IPv4 patterns; on by default; not a comprehensive detector |
| Zero data retention | Requests must set `zdr_only: true`; the OpenRouter call asks for `zdr: true`, `data_collection: "deny"`, `allow_fallbacks: false`. This is a request to the provider, not proof of its behavior |
| Redaction attestation | Client must declare `metadata.scrubbed: true`; a declared flag, not a cryptographic proof |
| Audit log | JSONL (or stdout) with metadata only: no prompt or response text. Rotated by size, pruned by age (`logging.retention`) |
| Transport | Plain HTTP. The gateway does not terminate TLS |
| Storage | Writes only the audit log file. No database |

## What the operator is responsible for

- **TLS** in transit (terminate it at a reverse proxy or load balancer in front of the gateway).
- **Encryption at rest** for the host disk and the audit log.
- **Audit log integrity, retention and shipping** (the log is an ordinary file; it is not signed or immutable), and any SIEM integration.
- **Incident detection and response**, breach notification and post-incident review.
- **Access reviews**, key rotation and secret management for tenant keys and the OpenRouter key.
- **Deployment, change management and rollback** of the gateway itself.
- **Reviewing OpenRouter and the upstream model providers** for data handling; ZeroVeil does not verify provider retention.
- **Client-side redaction** before data reaches the gateway.

## How this can help a customer's own program

| Customer need | What the gateway contributes |
|---------------|------------------------------|
| Keep obvious PII out of provider requests | Regex PII rejection; clients redact locally |
| An audit trail of AI usage | Metadata-only decision log without content |
| Ask providers not to retain data | ZDR requested on every OpenRouter call; fallbacks disabled |
| Limit which models are used | `allowed_models` allow-list |

See `docs/threat-model.md` for limits and non-goals.

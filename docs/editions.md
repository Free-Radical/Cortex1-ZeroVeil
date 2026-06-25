# ZeroVeil Product Editions

> Canonical edition definitions live in `zeroveil-gateway-pro/docs/editions.md`.
> This file is the community repo summary. Keep in sync.

This repository is the **Community Gateway**: the source-available, noncommercial enforcement core.

## Overview

ZeroVeil ships two product lines:
- **SDKs** (client-side libraries) — scrub PII locally before requests leave the client
- **Gateways** (server-side proxies) — enforce policy, audit, and optionally mix traffic

Community source is licensed under the PolyForm Noncommercial License 1.0.0.
Commercial, hosted, managed-service, customer-facing, internal business,
revenue-generating, paid, or other monetized use requires a separate written
commercial license.

---

## Product Matrix

| | SDK | SDK Pro | Gateway Community | Gateway Pro | Gateway Relay |
|---|---|---|---|---|---|
| **License** | PolyForm NC | PolyForm NC + paid license | PolyForm NC | PolyForm NC + paid license | Paid service |
| **Runs where** | Client machine | Client machine | Self-hosted | Self-hosted or hosted | Hosted only |
| **Cost** | Source-available, no fee | Paid license | Source-available, no fee | Paid license | Paid usage-based |
| | | | | | |
| **PII scrubbing (local)** | Presidio backend only | Presidio + regex + scrubadub | — | — | — |
| **Scrubbing modes** | Non-deterministic only (redacts) | Deterministic + non-deterministic (can reverse tokens after response) | — | — | — |
| **Reversible token mapping** | no | yes | — | — | — |
| **Scrub audit logging** | no | yes | — | — | — |
| **Relay client** | Basic client to talk to gateway | Full client with auth, retry, streaming | — | — | — |
| | | | | | |
| **PII rejection gate** | — | — | yes (safety net) | yes | yes |
| **Policy / allowlists / budgets** | — | — | yes | yes | yes |
| **Audit logging** | — | — | basic | signed + immutable | signed + immutable |
| **Multi-tenant auth** | — | — | yes | yes | yes |
| **Tier escalation** | — | — | no | yes | yes |
| **SSO / SIEM / dashboard** | — | — | no | yes | yes |
| **Mixer** | — | — | no | no | **yes** |
| **Shared relay identity** | — | — | no | no | **yes** |
| **Provider can't ID you** | — | — | no | no | **yes** |
| **Bring your own keys** | — | — | yes | yes | no (ZeroVeil's keys) |

---

## Who Uses What

| User | SDK | SDK Pro | GW Community | GW Pro | GW Relay |
|---|---|---|---|---|---|
| Solo dev, wants basic PII safety | yes | — | — | — | — |
| Startup proving PII handling to investors | yes | — | yes | — | — |
| Dev team wanting shared LLM proxy with rate limits | — | — | yes | — | — |
| Consultancy needing reversible scrubbing | — | yes | yes | — | — |
| Healthcare company, PHI audit trail required | — | yes | — | yes | — |
| Enterprise IT, 500 engineers, SSO + SIEM | — | — | — | yes | — |
| Law firm, provider must not know which clients | — | yes | — | — | yes |
| Defense contractor, provider must not correlate queries | — | yes | — | — | yes |
| Journalist, can't risk provider subpoena | yes | — | — | — | yes |
| Hospital, full stack: scrubbing + audit + provider blindness | — | yes | — | — | yes |
| Fintech, regulatory pressure, limited budget | yes | — | yes | — | — |
| Large bank, full compliance + provider privacy | — | yes | — | yes | yes |

---

## Key Constraint: Relay Requires Shared Keys

For the mixer to provide correlation resistance, all tenant traffic must flow through ZeroVeil-owned shared provider API keys. If each tenant uses their own key, the provider can group requests by key — the mixer becomes ineffective.

| Mode | Whose keys | Mixer works? |
|---|---|---|
| Community / Pro (self-hosted) | Tenant's own | No |
| Pro (hosted) | Tenant's own | No |
| Relay (hosted) | ZeroVeil's shared | Yes |

---

## Trust Funnel

1. **SDK** — Run locally, read the source, verify it works. Zero trust required.
2. **Gateway Community** — Self-hosted, read the source, verify no content logging. Minimal trust.
3. **Gateway Pro** — Hosted option, signed audit logs prove behavior. Moderate trust.
4. **Gateway Relay** — Trust ZeroVeil with shared keys and mixing. Maximum value, maximum trust.

Nobody starts at Relay. They start with their own keys and upgrade when they understand the privacy gain.

---

## Network Effect: Why Cloud Beats Self-Hosted for Privacy

The mixer's effectiveness depends on the size of the mixing pool:

| Pool Size | Correlation Resistance | Timing Obfuscation |
|-----------|------------------------|-------------------|
| 1 tenant (self-hosted, solo) | None | None |
| 5-10 tenants | Weak | Basic |
| 100+ tenants | Strong | Good |
| 1000+ tenants | Very strong | Excellent |

Cloud-hosted Relay benefits from the aggregate traffic of all ZeroVeil users. Self-hosting only makes sense when you have strict air-gap requirements, data sovereignty prevents external relay, or you operate multiple internal tenants yourself.

---

## Chat UI: Open WebUI

For interactive chat (replacing ChatGPT/Claude web), the recommended frontend is **Open WebUI** (MIT license, 126k+ GitHub stars).

Open WebUI speaks OpenAI-compatible API natively. Point its `OPENAI_API_BASE` at the gateway and it works — no custom integration code. All gateway features (PII rejection, model allowlists, rate limits, audit) apply transparently.

### Deployment Stacks

| Stack | What you get | Use case |
|---|---|---|
| Gateway + Open WebUI | Chat UI + DLP gateway, cloud models via OpenRouter | Power user or corporate ChatGPT replacement |
| Gateway + Open WebUI + Ollama | Chat UI + DLP gateway + local models, no cloud keys needed | Air-gapped or fully local deployment |
| Gateway only (no UI) | OpenAI-compatible API proxy | Developers integrating via SDK or `OPENAI_API_BASE` |

### Corporate Chatbot Replacement

Instead of intercepting ChatGPT/Claude traffic (requires TLS interception, breaks with certificate pinning):
1. Block `chat.openai.com`, `claude.ai`, `gemini.google.com` at the firewall
2. Deploy Open WebUI + ZeroVeil Gateway
3. Employees use the replacement — works in any browser, including iPhone (PWA)

---

*Keep in sync with `zeroveil-gateway-pro/docs/editions.md`.*

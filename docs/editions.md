# ZeroVeil Product Editions

> This file is the canonical edition summary. Pro features are available under a separate commercial license; contact Saqib.Khan@Me.com.

This repository is the **Community Gateway**: the source-available, noncommercial enforcement core.

## Overview

> **The SDKs are not part of this repository or of v0.2.0 and are not publicly available.** Only the Community Gateway is available. The SDK columns below describe a product split, not available software.

ZeroVeil's product lines:
- **SDKs** (client-side libraries, not available) — would scrub PII locally before requests leave the client
- **Gateways** (server-side proxies) — enforce policy and audit

Source-available under PolyForm Noncommercial 1.0.0. Free for personal, educational, nonprofit and government use; companies get a 32-day evaluation under PolyForm Free Trial 1.0.0 (LICENSE-FREE-TRIAL); any other commercial use needs a written license: see COMMERCIAL-LICENSE.md or write to Saqib.Khan@Me.com.

Commercial, hosted, managed-service, customer-facing, internal business,
revenue-generating, paid, or other monetized use requires a separate written
commercial license.

---

## Product Matrix

| | SDK | SDK Pro | Gateway Community | Gateway Pro |
|---|---|---|---|---|
| **License** | PolyForm NC + Free Trial (32 days) | PolyForm NC + Free Trial (32 days) + paid license | PolyForm NC + Free Trial (32 days) | PolyForm NC + Free Trial (32 days) + paid license |
| **Runs where** | Client machine | Client machine | Self-hosted | Self-hosted |
| **Cost** | Source-available, no fee | Paid license | Source-available, no fee | Paid license |
| | | | | |
| **PII scrubbing (local)** | Presidio backend only | Presidio + regex + scrubadub | — | — |
| **Scrubbing modes** | Non-deterministic only (redacts) | Deterministic + non-deterministic (can reverse tokens after response) | — | — |
| **Reversible token mapping** | no | yes | — | — |
| **Scrub audit logging** | no | yes | — | — |
| **Relay client** | Basic client to talk to gateway | Full client with auth, retry, streaming | — | — |
| | | | | |
| **PII rejection gate** | — | — | yes (safety net) | yes |
| **Policy / allowlists / budgets** | — | — | yes | yes |
| **Audit logging** | — | — | basic | signed + immutable |
| **Multi-tenant auth** | — | — | yes | yes |
| **Tier escalation** | — | — | no | yes |
| **SSO / SIEM / dashboard** | — | — | no | yes |
| **Bring your own keys** | — | — | yes | yes |

---

## Who Uses What

| User | SDK | SDK Pro | GW Community | GW Pro |
|---|---|---|---|---|
| Solo dev, wants basic PII safety | yes | — | — | — |
| Startup proving PII handling to investors | yes | — | yes | — |
| Dev team wanting shared LLM proxy with rate limits | — | — | yes | — |
| Consultancy needing reversible scrubbing | — | yes | yes | — |
| Healthcare company, PHI audit trail required | — | yes | — | yes |
| Enterprise IT, 500 engineers, SSO + SIEM | — | — | — | yes |
| Fintech, regulatory pressure, limited budget | yes | — | yes | — |
| Large bank, full compliance | — | yes | — | yes |

---

## Trust Funnel

1. **SDK** (not available) — Would run locally. Zero trust required.
2. **Gateway Community** — Self-hosted, read the source, verify no content logging. Minimal trust.
3. **Gateway Pro** — Self-hosted, signed audit logs prove behavior. Moderate trust.

---

## Chat UI: Open WebUI

For interactive chat (replacing ChatGPT/Claude web), the recommended frontend is **Open WebUI** (MIT license, 126k+ GitHub stars).

Open WebUI speaks OpenAI-compatible API natively. Point its `OPENAI_API_BASE` at the gateway and it works — no custom integration code. All gateway features (PII rejection, model allowlists, rate limits, audit) apply transparently.

### Deployment Stacks

| Stack | What you get | Use case |
|---|---|---|
| Gateway + Open WebUI | Chat UI + DLP gateway, cloud models via OpenRouter | Power user or corporate ChatGPT replacement |
| Gateway + Open WebUI + Ollama | Chat UI + DLP gateway + local models, no cloud keys needed | Air-gapped or fully local deployment |
| Gateway only (no UI) | OpenAI-compatible API proxy | Developers integrating via `OPENAI_API_BASE` |

### Corporate Chatbot Replacement

Instead of intercepting ChatGPT/Claude traffic (requires TLS interception, breaks with certificate pinning):
1. Block `chat.openai.com`, `claude.ai`, `gemini.google.com` at the firewall
2. Deploy Open WebUI + ZeroVeil Gateway
3. Employees use the replacement — works in any browser, including iPhone (PWA)


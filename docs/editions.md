# ZeroVeil Editions

This repository is the **Community Gateway**: the source-available enforcement core, self-hosted. It is the only thing available in v0.2.0.

Client SDKs are not part of v0.2.0.

Source-available under PolyForm Noncommercial 1.0.0. Free for personal, educational, nonprofit and government use; companies get a 32-day evaluation under PolyForm Free Trial 1.0.0 (LICENSE-FREE-TRIAL); any other commercial use needs a written license: see COMMERCIAL-LICENSE.md or write to Saqib.Khan@Me.com.

Beyond the 32-day PolyForm Free Trial 1.0.0 evaluation (LICENSE-FREE-TRIAL),
commercial, hosted, managed-service, customer-facing, internal business,
revenue-generating, paid, or other monetized use requires a separate written
commercial license.

---

## What v0.2.0 includes

| | Community Gateway |
|---|---|
| **License** | PolyForm NC + Free Trial (32 days); commercial use needs a written license |
| **Runs where** | Self-hosted |
| **PII rejection gate** | yes (regex tripwire, on by default) |
| **Model allow-list, message limits** | yes |
| **Per-tenant API keys and rate limits** | yes |
| **Audit logging** | metadata-only JSONL |
| **Provider** | OpenRouter only (ZDR requested) |
| **Bring your own keys** | yes (your OpenRouter key) |

## Pro

A commercial license is available; contact Saqib.Khan@Me.com. Pro features are not part of v0.2.0 and are not described here as available.

---

## Chat UI: Open WebUI

For interactive chat, a common frontend is **Open WebUI** (MIT license). It speaks the OpenAI-compatible API, so point its `OPENAI_API_BASE` at the gateway. Gateway features (PII rejection, model allow-list, rate limits, audit) apply to its requests.

### Deployment Stacks

| Stack | What you get | Use case |
|---|---|---|
| Gateway + Open WebUI | Chat UI + DLP gateway, models via OpenRouter | Power user or team chat frontend |
| Gateway only (no UI) | OpenAI-compatible API proxy | Developers integrating via `OPENAI_API_BASE` |

### Corporate Chatbot Replacement

Instead of intercepting ChatGPT/Claude traffic (requires TLS interception, breaks with certificate pinning):
1. Block `chat.openai.com`, `claude.ai`, `gemini.google.com` at the firewall
2. Deploy Open WebUI + ZeroVeil Gateway
3. Employees use the replacement in any browser

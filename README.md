# ZeroVeil (community gateway)

**An LLM gateway you run yourself. It won't forward a prompt unless the rules are met, and it keeps a record of every decision without keeping the words.**

You put ZeroVeil between your app and a model API (it speaks the OpenAI chat format). Every request has to clear three checks, and if any one fails, the request goes nowhere:

- **Zero data retention, requested.** ZeroVeil asks the provider for zero data retention and refuses to fall back to a provider that won't honor it.
- **Redaction, attested.** The client has to state that the prompt was redacted (`metadata.scrubbed: true`). ZeroVeil also runs its own sensitive-data check and blocks what it catches. The attestation is a declared flag, not a cryptographic proof.
- **Audit, without the content.** Each allow/deny decision is written to an audit log that holds metadata only: no prompt text, no response text.

That's the whole pitch. It lowers your risk; it doesn't guarantee it. ZeroVeil doesn't make you anonymous to the provider, and it isn't a compliance certification.

> License: source-available under PolyForm Noncommercial 1.0.0. Free for personal, educational, nonprofit and government use; companies get a 32-day evaluation under PolyForm Free Trial 1.0.0 (LICENSE-FREE-TRIAL); any other commercial use needs a written license: see COMMERCIAL-LICENSE.md or write to Saqib.Khan@Me.com.

## Try it (about 5 minutes)

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -U pip && python -m pip install -e .[dev]

# Inbound auth (the gateway's own key). tenants/default.json ships with a
# placeholder that will not match any real token, so point ZEROVEIL_TENANTS_PATH
# at a path that does not exist to use single-key auth for this demo:
export ZEROVEIL_TENANTS_PATH=/tmp/no-such-tenants.json
export ZEROVEIL_API_KEY="demo-key-change-me"

# Outbound provider key (OpenRouter), used once a request passes policy:
export OPENROUTER_API_KEY="your-openrouter-api-key"

python -m zeroveil_gateway          # OpenAI-compatible endpoint on :8000
curl http://127.0.0.1:8000/healthz  # {"ok":true}
```

Send a request without the redaction attestation and watch it get refused:

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer demo-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"hi"}],"zdr_only":true}'
# 403 policy_denied: "Scrub attestation required (metadata.scrubbed=true)."
```

That refusal is the product.

## What's not here

The request-aggregation design in `docs/mixer-design.md` is research. It isn't built and it isn't a feature. Paid features are available under a separate commercial license.

---

## Development and Test

```bash
# Unit tests
pytest -q

# Lint (if installed)
ruff check src tests

# Demo request flow
python scripts/demo_gateway.py
```

## Core Configuration

- `ZEROVEIL_API_KEY`: the gateway's own inbound auth key (legacy single-tenant mode, used only when `ZEROVEIL_TENANTS_PATH` does not resolve to a valid tenants file).
- `OPENROUTER_API_KEY`: the outbound OpenRouter provider key (no `ZEROVEIL_` prefix).
- `ZEROVEIL_POLICY_PATH`: policy JSON path (default `policies/default.json`).
- `ZEROVEIL_TENANTS_PATH`: tenant config JSON path (default `tenants/default.json`); when it loads, per-tenant API keys (sha256 hashes) are required instead of `ZEROVEIL_API_KEY`.
- `ZEROVEIL_STUB_MODE`: set `1`/`true` for local stub mode (skips the outbound provider call).

## What Is This?

Cortex1-ZeroVeil is an **OpenAI-compatible proxy** that adds DLP controls to LLM calls routed through OpenRouter—with one line of code.

```python
# Add DLP to your app
client = OpenAI(base_url="https://your-zeroveil/v1")
```

**What makes ZeroVeil unique:**

1. **We reject PII, we don't scrub it.** If you send us data to "clean," you've already exposed it. ZeroVeil detects PII patterns and blocks the request—your sensitive data never leaves your environment.

2. **DLP gateway controls, enforced today.** Policy enforcement, PII rejection, and metadata-only audit logging are implemented now.

3. **Routes through OpenRouter today.** OpenRouter is the only upstream provider the gateway supports in v0.2.0.

---

## Who Is This For?

### Developers Building Regulated Apps

You're building an app that calls LLM APIs and handles PHI, PII, or PCI data. How do you add DLP today?

| Option | Problem |
|--------|---------|
| Build your own | Time, expertise, ongoing maintenance |
| Enterprise gateways (Kong, Securiti) | Enterprise pricing, enterprise sales cycle |
| DIY toolkits (LiteLLM + Presidio) | No compliance artifacts, DIY audit logging |
| Cloud scrubbing (Strac, Private AI) | You send them your PII first—defeats the purpose |
| Provider guardrails (Bedrock, Model Armor) | Single-provider lock-in |

**ZeroVeil fills this gap:** Developer-friendly and self-hosted, with a metadata-only audit trail.

```python
from openai import OpenAI

# Before: Direct to provider
client = OpenAI()

# After: Through ZeroVeil with DLP
client = OpenAI(base_url="https://your-zeroveil/v1")

# Your code stays the same
response = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": user_input}]
)
```

**What you get:**
- PII/PHI/PCI rejection before data leaves your environment
- Audit logging for compliance (metadata-only, no content)
- Model allowlists (restrict to approved models)
- Per-tenant rate and daily-token limits
- Routes through OpenRouter (the only provider supported today)

### Enterprise IT / Security Teams

Employees are pasting everything into AI chatbots—the same things they used to paste into search engines, plus far worse:

- Corporate emails, business plans, proposals, RFP responses
- Confidential legal agreements, M&A documents, board presentations
- Proprietary source code, API keys, database credentials
- Financial spreadsheets: quarterly numbers, salary data with names, revenue forecasts
- Customer PII, patient records, internal org charts

Companies are responding with blanket bans:

| Company | Action | Reason |
|---------|--------|--------|
| Samsung | Banned ChatGPT | Source code leaked |
| Apple | Restricted use | Confidential information concerns |
| Verizon | Blocked | Customer data / source code risk |
| Deutsche Bank | Blocked | Data leakage protection |

**The solution:** Don't ban AI—control it through ZeroVeil.

```
+-------------------------------------------------------------+
| Corporate Network                                           |
|                                                             |
|  Employee  --> ZeroVeil Gateway --> OpenRouter             |
|  ChatGPT   -->  - PII rejection (blocks sensitive data)    |
|  Apps      -->  - Model allowlists                         |
|  CI/CD     -->  - Rate limits                               |
|                 - Audit logging                             |
|                                                             |
|  Firewall: BLOCK direct api.openai.com                     |
+-------------------------------------------------------------+
```

**What happens when ZeroVeil detects sensitive data:**

1. Request is **blocked immediately**—never reaches the LLM provider
2. Employee sees actionable error: "Request blocked: PII detected (email, SSN). Remove sensitive data before retrying."
3. IT/Security receives audit event (metadata only, no content logged)
4. Employee rephrases without sensitive data, or escalates to approved channel

**We reject, we don't scrub.** If you send data to a service to "clean" it, you've already exposed it. ZeroVeil detects and blocks—your sensitive data never leaves your network.

**What you get:**
- Drop-in proxy (apps just change `OPENAI_API_BASE`)
- Block direct provider access at firewall
- Model restrictions and per-tenant limits
- Metadata-only audit trail

---

## Research: Request Aggregation Design

A design for aggregating requests through a shared relay credential is documented in `docs/mixer-design.md`. It is research only: not implemented, not scheduled, and not a feature of any release.

## Why We Reject, Not Scrub

**If you send us PII to scrub, you've already compromised your privacy.**

| Approach | What Happens | Problem |
|----------|--------------|---------|
| Cloud scrubbing | You send raw PII to us, we remove it | You've already exposed it to us |
| **ZeroVeil** | We detect PII, reject the request | Your PII never leaves your network |

**The rejection response tells you what was detected**, so you can fix it locally before retrying.

For proactive redaction, scrub locally with your own tooling (for example Presidio) before sending.

---

## How We Compare

| Competitor | Their Approach | ZeroVeil Difference |
|------------|---------------|---------------------|
| Bastio, Portkey | Cloud scrubbing | We reject, not scrub—your PII never reaches us |
| LiteLLM + Presidio | DIY toolkit | We provide compliance-ready audit + gateway out of box |
| Kong Enterprise | Enterprise pricing | Developer-friendly, source-available core (PolyForm Noncommercial 1.0.0) |
| Bedrock/Model Armor | Single provider | Routes through OpenRouter today |
| **All of them** | — | ZeroVeil does not provide anonymity or correlation resistance |

---

## Trust Model

**Be clear about what you're trusting:**

| Component | You Trust |
|-----------|-----------|
| Gateway | ZeroVeil to enforce policies and not log content |
| ZDR Providers | Provider's retention policy claims |
| Your Environment | That you're blocking direct AI access |

We designed this so you trust us with **less**, not more.

---

## Getting Started

### Install and run

```bash
# Install
python -m pip install -e .[dev]

# Configure
export ZEROVEIL_POLICY_PATH=policies/default.json

# Run gateway
python -m zeroveil_gateway

# Test
python scripts/demo_gateway.py
```

See [docs/architecture.md](docs/architecture.md) for Corporate AI Gateway deployment topology.

### Deployment

ZeroVeil v0.2.0 is self-hosted only. There is no ZeroVeil-operated hosted service.

---

## ZeroVeil Pro

A commercial license is available; contact Saqib.Khan@Me.com. Pro features are not part of v0.2.0.

---

## Status

**Status:** DLP gateway is implemented and enforced. Request aggregation is research only (see `docs/mixer-design.md`); it is not built and not a feature.

| Component | Status |
|-----------|--------|
| Policy enforcement | Done |
| PII rejection gate | Done (enabled by default) |
| Multi-tenant auth | Done |
| Audit logging (metadata-only) | Done |
| Provider routing | Done (OpenRouter) |

OpenRouter is the only supported provider in v0.2.0.

---

## Key Files

- Spec: `docs/spec-v0.md`
- Policy schema: `policies/default.json`
- Gateway: `src/zeroveil_gateway/app.py`

---

## Contributing

Looking for contributors interested in privacy-first AI infrastructure. If you care about:
- LLM data-loss-prevention (DLP) gateway controls
- Zero-trust architecture
- Building the missing privacy layer for AI

See `CONTRIBUTING.md`. Contributions are accepted under the terms in `CLA.md`; signing off your commits (`git commit -s`, the DCO) is the only acceptance step, and there is no separate CLA signature.

Open an issue or reach out: Saqib.Khan@Me.com

---

## License

Source-available under PolyForm Noncommercial 1.0.0. Free for personal, educational, nonprofit and government use; companies get a 32-day evaluation under PolyForm Free Trial 1.0.0 (LICENSE-FREE-TRIAL); any other commercial use needs a written license: see COMMERCIAL-LICENSE.md or write to Saqib.Khan@Me.com.

## Prior Art

This repository constitutes a public disclosure of the described techniques. See [NOTICE](NOTICE) for details.

---

## Author

Saqib Ali Khan
Contact: Saqib.Khan@Me.com

---

*The privacy layer for AI that should have existed from day one.*

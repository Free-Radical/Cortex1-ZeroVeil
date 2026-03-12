# Cortex1-ZeroVeil

> **License:** Source-available under PolyForm Noncommercial 1.0.0. Personal, hobby, educational, research, evaluation, and other noncommercial use are allowed. Commercial, hosted, customer-facing, internal business, paid, or other monetized use requires a separate written license. See `LICENSE`, `NOTICE.md`, and `COMMERCIAL-LICENSE.md`.

**DLP Controls for Any LLM API**

*For Developers Building Regulated Apps and Enterprise IT Teams*

Part of the Cortex1 family of privacy-first AI infrastructure.

---

## Repo Tier and Access

- **Tier:** Community / Public / Noncommercial
- Audience: personal users, researchers, and developers evaluating or using the community gateway for noncommercial purposes.
- Commercial note: paid, hosted, customer-facing, internal business, or other monetized use requires a separate written commercial license.
- Pro note: commercially licensed paid features live in `zeroveil-gateway-pro` and `zeroveil-pro`.

## Quick Start (Community Gateway)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .[dev]

# Required for provider calls
export ZEROVEIL_API_KEY="your-provider-api-key"

# Start gateway (OpenAI-compatible endpoint on :8000)
python -m zeroveil_gateway

# Smoke check
curl http://127.0.0.1:8000/healthz
```

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

- `ZEROVEIL_API_KEY`: upstream provider key used by the gateway.
- `ZEROVEIL_POLICY_PATH`: policy JSON path (default `policies/default.json`).
- `ZEROVEIL_TENANTS_PATH`: tenant config JSON path (default `tenants/default.json`).
- `ZEROVEIL_STUB_MODE`: set `1`/`true` for local stub mode.
- `ZEROVEIL_OPENROUTER_API_KEY`: OpenRouter key when routing via OpenRouter.

## Related ZeroVeil Repos

- `zeroveil-sdk`: public/community client SDK.
- `zeroveil-gateway-pro`: commercially licensed gateway repo.
- `zeroveil-pro`: commercially licensed SDK/features repo.

---

## What Is This?

Cortex1-ZeroVeil is an **OpenAI-compatible proxy** that adds DLP controls to any LLM endpoint—with one line of code.

```python
# Add DLP to your app
client = OpenAI(base_url="https://your-zeroveil/v1")
```

**What makes ZeroVeil unique:**

1. **We reject PII, we don't scrub it.** If you send us data to "clean," you've already exposed it. ZeroVeil detects PII patterns and blocks the request—your sensitive data never leaves your environment.

2. **Provider-side correlation resistance (`PLANNED_COMMUNITY`).** Mixer primitives are planned for Week 5. Current releases provide DLP gateway controls; correlation-resistance claims apply after mixer rollout.

3. **Works with any OpenAI-compatible endpoint.** Direct providers (OpenAI, Anthropic), aggregators (OpenRouter, Together AI), or self-hosted models (vLLM, Ollama).

---

## Who Is This For?

### Developers Building Regulated Apps

You're building an app that calls LLM APIs and handles PHI, PII, or PCI data. How do you add DLP today?

| Option | Problem |
|--------|---------|
| Build your own | Time, expertise, ongoing maintenance |
| Enterprise gateways (Kong, Securiti) | Enterprise pricing, enterprise sales cycle |
| Open-source toolkits (LiteLLM + Presidio) | No compliance artifacts, DIY audit logging |
| Cloud scrubbing (Strac, Private AI) | You send them your PII first—defeats the purpose |
| Provider guardrails (Bedrock, Model Armor) | Single-provider lock-in |

**ZeroVeil fills this gap:** Developer-friendly, provider-agnostic, compliance-ready.

```python
from openai import OpenAI

# Before: Direct to provider
client = OpenAI()

# After: Through ZeroVeil with DLP
client = OpenAI(base_url="https://your-zeroveil/v1")

# Your code stays the same
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": user_input}]
)
```

**What you get:**
- PII/PHI/PCI rejection before data leaves your environment
- Audit logging for compliance (metadata-only, no content)
- Model allowlists (restrict to approved models)
- Rate/cost limits per tenant
- Works with OpenRouter, OpenAI, Anthropic, or any OpenAI-compatible endpoint

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
|  Employee  --> ZeroVeil Gateway --> OpenAI/Anthropic/etc   |
|  ChatGPT   -->  - PII rejection (blocks sensitive data)    |
|  Apps      -->  - Model allowlists                         |
|  CI/CD     -->  - Rate/cost limits                          |
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
- Per-department budgets and model restrictions
- Compliance-ready audit trails
- `PLANNED_COMMUNITY`: Optional mixer routing for correlation resistance (Week 5 target)

**Pro roadmap: Scrubbing webhook integration.** For enterprises with existing data cleaning pipelines, ZeroVeil can optionally forward blocked requests to your scrubbing service. Your service cleans the data using your approved methods, then retries through ZeroVeil. ZeroVeil never touches your data—but integrates with your existing compliance infrastructure.

---

## Planned Innovation: Mixer Architecture (`PLANNED_COMMUNITY`)

This is a design target for the Community roadmap (not active in Week 2 builds).

```
User A --->
User B --+--> [ZeroVeil Mixer] ---> Shared Identity ---> Cloud LLM
User C --->
```

**How it is planned to work:**
- Aggregates requests from multiple tenants through a shared relay identity
- Provider sees one source, not individual users
- Timing jitter and batching reduce fingerprinting
- Response routing via one-time tokens (unlinkable)

**Why this matters:**
- Even with "zero data retention," providers see who sent each prompt in real-time
- API key breaches expose user-to-prompt history
- Metadata accumulation enables competitive intelligence and legal exposure
- **Design goal:** reduce provider-side correlation risk through mixing once primitives ship

---

## Why We Reject, Not Scrub

**If you send us PII to scrub, you've already compromised your privacy.**

| Approach | What Happens | Problem |
|----------|--------------|---------|
| Cloud scrubbing | You send raw PII to us, we remove it | You've already exposed it to us |
| **ZeroVeil** | We detect PII, reject the request | Your PII never leaves your network |

**The rejection response tells you what was detected**, so you can fix it locally before retrying.

For proactive scrubbing, use the ZeroVeil SDK (local-only, source-available under BSL) or your own tooling.

---

## How We Compare

| Competitor | Their Approach | ZeroVeil Difference |
|------------|---------------|---------------------|
| Bastio, Portkey | Cloud scrubbing | We reject, not scrub—your PII never reaches us |
| LiteLLM + Presidio | DIY toolkit | We provide compliance-ready audit + gateway out of box |
| Kong Enterprise | Enterprise pricing | Developer-friendly, source-available core (BSL) |
| Bedrock/Model Armor | Single provider | Provider-agnostic, works with any endpoint |
| **All of them** | No correlation resistance | `PLANNED_COMMUNITY`: design reduces user-to-prompt linkability through mixing |

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

### For Developers

```bash
# Install
pip install cortex1-zeroveil-community

# Configure
export ZEROVEIL_UPSTREAM_URL="https://api.openai.com/v1"
export ZEROVEIL_API_KEY="your-openai-key"

# Run
python -m zeroveil_gateway

# Use in your app
client = OpenAI(base_url="http://localhost:8000/v1")
```

### For Enterprise IT

```bash
# Install
python -m pip install -e .[dev]

# Configure
set ZEROVEIL_POLICY_PATH=policies/default.json

# Run gateway
python -m zeroveil_gateway

# Test
python scripts/demo_gateway.py
```

See [docs/architecture.md](docs/architecture.md) for Corporate AI Gateway deployment topology.

### Deployment Options

Both Community and Pro are available **self-hosted** or **cloud-hosted**:

| Option | Relay Identity | Mixing Benefit | Best For |
|--------|----------------|----------------|----------|
| **Cloud-Hosted** | Shared (ZeroVeil-operated) | High (network effect) | Most users |
| **Self-Hosted** | Your own API keys | None (unless multi-tenant) | Air-gap, data sovereignty |

**Recommendation:** For small-to-medium organizations, **cloud-hosted is preferable** because larger mixing pools provide stronger correlation resistance.

---

## ZeroVeil Pro

Enterprise features on top of Community:

- Enterprise auth (SSO/SAML/OIDC) and RBAC
- Architecture aligned with HITRUST CSF, ISO 27001/27701, SOC 2, NIST CSF, NIST AI RMF
- Compliance evidence bundles for customer audits
- Signed/immutable audit logs
- Admin dashboard UI (requests, blocks, costs by tenant)
- SIEM webhook integration

*Formal certifications for ZeroVeil Hosted on roadmap pending scale.*

See [docs/compliance.md](docs/compliance.md) for detailed control mappings.

Contact: Saqib.Khan@Me.com for access.

---

## Status

**Week 2 complete.** DLP gateway is implemented; mixer primitives are planned for Week 5.

| Component | Status |
|-----------|--------|
| Policy enforcement | Done |
| PII rejection gate | Done (enabled by default) |
| Multi-tenant auth | Done |
| Audit logging (metadata-only) | Done |
| Provider routing | Stubbed (Week 3) |
| Mixer primitives | Week 5 (batching, shuffle, jitter, header stripping) |

**Roadmap:** `IMPLEMENTED_NOW` DLP Gateway → `PLANNED_COMMUNITY` Mixer primitives → `PLANNED_COMMUNITY` Multi-provider support → Public release

---

## Key Files

- Spec: `docs/spec-v0.md`
- Policy schema: `policies/default.json`
- Gateway: `src/zeroveil_gateway/app.py`
- Whitepaper: `docs/whitepaper.md`

---

## Contributing

Looking for contributors interested in privacy-first AI infrastructure. If you care about:
- LLM privacy and correlation risk reduction
- Zero-trust architecture
- Building the missing privacy layer for AI

See `CONTRIBUTING.md` and `CLA.md`.

Open an issue or reach out: Saqib.Khan@Me.com

---

## License

PolyForm Noncommercial License 1.0.0.

- Personal, hobby, educational, research, evaluation, and other noncommercial use are allowed.
- Commercial, hosted, customer-facing, internal business, paid, or other monetized use requires a separate written commercial license.
- Contact: Saqib.Khan@Me.com

## Prior Art

This repository constitutes a public disclosure of the described techniques. See [NOTICE](NOTICE) for details.

---

## Author

Saqib Ali Khan
Contact: Saqib.Khan@Me.com

---

*The privacy layer for AI that should have existed from day one.*

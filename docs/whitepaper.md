# Cortex1-ZeroVeil

**DLP Controls for Any LLM API**

*For Developers Building Regulated Apps and Enterprise IT Teams*

---

**Author:** Saqib Ali Khan
**Date:** December 2025
**Status:** Week 2 complete. `IMPLEMENTED_NOW` DLP gateway controls; `PLANNED_COMMUNITY` mixer primitives targeted for Week 5.
**Family:** Part of the Cortex1 privacy-first AI infrastructure

---

## Abstract

LLM API calls leak sensitive data. Whether you're a developer building a healthcare app or an IT team controlling employee AI access, adding DLP controls today means:

- Building your own PII detection logic
- Paying enterprise prices for enterprise gateways
- Cobbling together open-source toolkits without compliance artifacts
- Trusting cloud scrubbing services with your raw data

**ZeroVeil is different.** An OpenAI-compatible proxy that adds DLP controls to any LLM endpoint—with one line of code.

```python
# Add DLP to your app
client = OpenAI(base_url="https://your-zeroveil/v1")
```

**What makes ZeroVeil unique:**

1. **We reject PII, we don't scrub it.** If you send us data to "clean," you've already exposed it. ZeroVeil detects PII patterns and blocks the request—your sensitive data never leaves your environment.

2. **Provider-side correlation resistance (`PLANNED_COMMUNITY`).** Mixer architecture is the planned path for reducing provider-side correlation risk; current builds focus on DLP enforcement.

3. **Works with any OpenAI-compatible endpoint.** Direct providers (OpenAI, Anthropic), aggregators (OpenRouter, Together AI), or self-hosted models (vLLM, Ollama).

---

**Status labels used in this document**
- `IMPLEMENTED_NOW`: Available in current Community releases
- `PLANNED_COMMUNITY`: On Community roadmap, not implemented yet
- `PRO_ONLY`: Available only in Pro

---

## The Problem Nobody Is Solving

### For Developers Building Regulated Apps

You're building an app that calls LLM APIs and handles PHI, PII, or PCI data. How do you add DLP today?

| Option | Problem |
|--------|---------|
| Build your own | Time, expertise, ongoing maintenance |
| Enterprise gateways (Kong, Securiti) | Enterprise pricing, enterprise sales cycle |
| Open-source toolkits (LiteLLM + Presidio) | No compliance artifacts, DIY audit logging |
| Cloud scrubbing (Strac, Private AI) | You send them your PII first—defeats the purpose |
| Provider guardrails (Bedrock, Model Armor) | Single-provider lock-in |

**The gap:** A developer-friendly, provider-agnostic proxy with compliance-ready features.

### For Enterprise IT / Security Teams

Employees are pasting everything into AI chatbots—the same things they used to paste into search engines, plus far worse:

- Corporate emails, business plans, proposals, RFP responses
- Confidential legal agreements, M&A documents, board presentations
- Proprietary source code, API keys, database credentials
- Financial spreadsheets: quarterly numbers, salary data with names, revenue forecasts
- Customer PII, patient records, internal org charts

Companies are responding with blanket bans:

| Company | Action | Reason |
|---------|--------|--------|
| Samsung | Banned ChatGPT | Source code leaked to ChatGPT |
| Apple | Restricted use | Confidential information concerns |
| Verizon | Blocked from corporate systems | Customer data / source code risk |
| Deutsche Bank | Blocked website | Data leakage protection |
| Microsoft | Temporarily blocked | Security and data concerns |

**The gap:** A middle path—controlled access with DLP enforcement, not blanket bans.

### The Correlation Problem (Both Audiences)

Even with "zero data retention" promises, every LLM API call exposes identity:

```
User A -> API Key A -> OpenAI
User B -> API Key B -> OpenAI
User C -> API Key C -> OpenAI
```

Provider sees exactly who sent each prompt. This creates:
- **Legal exposure**: Subpoenas target identifiable records
- **Breach risk**: API key leaks expose user-to-prompt history
- **Competitive intelligence**: Providers see what you're building

**No existing solution addresses this in current mainstream gateways.** Competitors focus on content privacy (scrubbing). ZeroVeil's planned mixer adds an identity-privacy layer.

---

## The Solution: ZeroVeil

### For Developers

Add DLP controls to your regulated app with one endpoint change:

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

### For Enterprise IT / Security

Deploy as a corporate AI gateway that intercepts all employee AI interactions:

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

**Pro roadmap: Scrubbing webhook integration.** For enterprises with existing data cleaning pipelines, ZeroVeil can optionally forward blocked requests to your scrubbing service. Your service cleans the data, then retries through ZeroVeil. ZeroVeil never touches your data—but integrates with your existing compliance infrastructure.

### The Mixer (`PLANNED_COMMUNITY`)

Planned Community capability: forward requests through ZeroVeil's mixer for correlation resistance.

```
User A --->
User B --+--> [ZeroVeil Mixer] ---> Shared Identity ---> Cloud Provider
User C --->
```

Target behavior after rollout: provider sees one source, not individual users.

---

## Why We Reject, Not Scrub

**If you send us PII to scrub, you've already compromised your privacy.**

| Approach | What Happens | Problem |
|----------|--------------|---------|
| Cloud scrubbing | You send raw PII to them, they remove it | You've already exposed it |
| **ZeroVeil** | We detect PII, reject the request | Your PII never leaves your network |

The rejection response tells you what was detected, so you can fix it locally before retrying.

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

## Use Cases

### Developers Building Regulated Apps

**Healthcare:** App processes patient data with LLM. ZeroVeil blocks PHI before it reaches the model.

**Fintech:** App handles financial data. ZeroVeil rejects PCI patterns, provides audit trail for compliance.

**Legal:** App processes privileged documents. ZeroVeil prevents confidential content from leaking.

**Any regulated industry:** Add DLP controls without building from scratch or paying enterprise prices.

### Enterprise IT / Corporate AI Gateway

**The problem:** Employees pasting sensitive data into AI chatbots—emails, source code, financials, customer PII.

**The solution:** Don't ban AI—control it through ZeroVeil.

- Deploy as the only approved path to AI providers
- Block direct access at firewall
- PII rejection catches accidental leaks (employee sees actionable error)
- Model allowlists restrict to approved models
- Audit logging for compliance (metadata only)

### SaaS / Multi-Tenant

- Offer privacy guarantees to customers
- Reduce liability from customer data exposure
- Clear trust boundaries

### Regulated Industries

- **Healthcare:** PHI never reaches relay (client scrubs), audit logging for HIPAA
- **Legal:** Privilege protection with clear boundaries
- **Finance:** PCI rejection, compliance-friendly architecture

---

## Trust Model

**Be clear about what you're trusting:**

| Component | You Trust |
|-----------|-----------|
| Gateway | ZeroVeil to enforce policies and not log content |
| ZDR Providers | Provider's retention policy claims |
| Your Environment | That you're blocking direct AI access |

We designed this so you trust us with **less**, not more:
- We never see your raw PII (if you reject properly)
- We don't log prompt content by default
- You can self-host for full control

---

## Deployment Options

| Option | Who Operates | Best For |
|--------|--------------|----------|
| **Self-Hosted** | You | Full control, air-gapped environments |
| **Cloud-Hosted** | ZeroVeil | Network effect (larger mixing pool), lower ops |

**For developers:** Self-host in your environment, or use ZeroVeil Cloud.

**For enterprises:** Deploy on-prem behind your firewall, or use ZeroVeil Cloud with BAA.

---

## Compliance & Security

ZeroVeil Pro supports enterprise compliance:

| Framework | How ZeroVeil Helps |
|-----------|-------------------|
| **HIPAA** | PHI rejection, BAA support, audit logging |
| **SOC 2** | Access controls, metadata-only audit trails |
| **HITRUST CSF** | PHI never reaches relay, audit logging |
| **ISO 27001/27701** | Information security + privacy controls |
| **PCI DSS** | Card data rejection at boundary |

---

## Getting Started

### For Developers

```bash
# Install
pip install zeroveil

# Configure
export ZEROVEIL_UPSTREAM_URL="https://api.openai.com/v1"
export ZEROVEIL_API_KEY="your-openai-key"

# Run
python -m zeroveil_community

# Use in your app
client = OpenAI(base_url="http://localhost:8000/v1")
```

### For Enterprise IT

See [docs/architecture.md](architecture.md) for Corporate AI Gateway deployment topology.

---

## Conclusion

ZeroVeil fills the gap between:
- **DIY toolkits** that lack compliance artifacts
- **Enterprise gateways** with enterprise pricing
- **Cloud scrubbing** that defeats the purpose of privacy

Whether you're a developer adding DLP to a regulated app or an IT team controlling corporate AI access, ZeroVeil gives you:

1. **One-line integration** — OpenAI-compatible, works with any endpoint
2. **Reject, not scrub** — Your PII never leaves your environment
3. **Correlation resistance (`PLANNED_COMMUNITY`)** — Planned mixer design to reduce user-to-prompt linkability

This is privacy done right.

---

**Author:** Saqib Ali Khan
**Contact:** Saqib.Khan@Me.com
**Repository:** https://github.com/Free-Radical/Cortex1-ZeroVeil

*The privacy layer for AI that should have existed from day one.*

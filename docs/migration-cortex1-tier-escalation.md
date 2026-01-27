# Migration: Tier Escalation from cortex1-core to ZeroVeil Pro

This document lays out the migration of LLM tier escalation and cost/pricing policy from `cortex1-core` to `ZeroVeil Pro` gateway, as specified in the `cortex1-core/TODO.md` release blockers.

> **Note:** All tier escalation and cost/pricing features are **Pro-only**. Community edition continues to use single-model routing with basic rate limiting. See `editions.md` line 89: "Tier escalation and automated cost/pricing policy" is listed under Pro.

## Goal

After migration, `cortex1-core` calls a **single ZeroVeil gateway endpoint** instead of managing tier escalation, model selection, and cost tracking internally. ZeroVeil **Pro** handles:

- Model selection + tier escalation *(Pro only)*
- Price/cost policy + tracking *(Pro only)*
- API key management
- Rate limiting (Community has basic; Pro has per-tenant budgets)
- A/B testing *(Pro only)*
- Fallback chains *(Pro only)*

**Community behavior:** Single model from policy, no escalation, basic token counting.

## Source Files (cortex1-core)

| File | What to Extract |
|------|-----------------|
| `src/cortex1/infra/model_gateway.py` | Tier routing, escalation logic, validation |
| `src/cortex1/infra/llm_prompts.py` | Prompt templates (may stay in cortex1) |
| `src/cortex1/config.py` | Model config (tiers, retry settings) |
| `src/cortex1/infra/llm_metrics.py` | Cost tracking / `log_llm_call()` |

---

## What Moves to ZeroVeil Pro

> All features in this section are **Pro-only**. Community edition uses single-model routing.

### 1. Tier Model Configuration (Pro)

**From `config.py` (lines 129-142):**

```python
# Tier 1: Fast, cheap, handles 80% of emails ($0.05/M)
openrouter_model: str = "meta-llama/llama-3.1-8b-instruct"
openrouter_email_model: str = "meta-llama/llama-3.1-8b-instruct"

# Tier 2: Better logic/JSON, for validation failures ($0.14/M)
openrouter_tier2_model: str = "qwen/qwen-2.5-coder-32b-instruct"

# Tier 3: Heavy reasoning, VIP/Critical only ($0.33/M)
openrouter_tier3_model: str = "qwen/qwen-2.5-72b-instruct"

# Escalation settings
escalate_urgent_vip: bool = True
max_tier1_retries: int = 1
```

**ZeroVeil Pro location:** New `pricing_policy.py` or extend existing `policy.py`

**New schema:**

```python
@dataclass
class TierConfig:
    name: str                    # "tier1", "tier2", "tier3"
    model: str                   # "meta-llama/llama-3.1-8b-instruct"
    cost_per_million: float      # 0.05
    timeout_seconds: int         # 20, 30, 45
    max_retries: int             # 1 for tier1, 0 for tier2/3
    priority_bypass: bool        # True = VIP/Critical skip to this tier

@dataclass
class EscalationPolicy:
    tiers: list[TierConfig]
    escalate_on_validation_failure: bool = True
    escalate_urgent_vip_to_tier: int = 3      # VIP emails go directly here
    flag_human_review_after_tier: int = 3     # If tier3 fails validation
```

---

### 2. Tier Escalation Logic (Pro)

**From `model_gateway.py` (`_call_openrouter_email_with_escalation`, lines 1029-1136):**

```
Flow:
1. VIP/Critical emails → Tier 3 directly
2. Normal emails → Tier 1, retry once, then Tier 2
3. If Tier 2 fails → Tier 3
4. If Tier 3 fails → Flag for human review
```

**ZeroVeil Pro implementation:**

1. Add `POST /v1/chat/completions` processing that:
   - Reads escalation policy from config
   - Detects priority from request metadata (`metadata.priority`, `metadata.vip`)
   - Routes to appropriate tier
   - Retries on failure/validation issues
   - Escalates through tiers as needed
   - Returns `X-ZeroVeil-Tier` header indicating which tier was used

2. Response includes:
   ```json
   {
     "id": "zv_...",
     "choices": [...],
     "usage": {...},
     "_zeroveil": {
       "tier_used": 2,
       "escalation_reason": "tier1_quality_failure",
       "low_confidence": true,
       "needs_human_review": false
     }
   }
   ```

---

### 3. Output Validation (Pro)

**From `model_gateway.py` (`_validate_llm_output`, lines 515-544, and `TEMPLATE_LEAKAGE_PATTERNS`, lines 22-41):**

```python
TEMPLATE_LEAKAGE_PATTERNS = [
    (r"Start with sender's name", "Instruction leaked"),
    (r"max \d+ words", "Instruction leaked"),
    (r"Here is the (?:output|response|result) in", "LLM preamble"),
    # ... more patterns
]

class ValidationResult:
    is_valid: bool
    issues: List[str]
    needs_escalation: bool = False
    needs_human_review: bool = False
```

**ZeroVeil Pro location:** New `validation.py` module

**Implementation:**
- Generic validation patterns (can be customized per tenant/policy)
- Returns validation result that triggers escalation
- Patterns are configurable in policy file

---

### 4. Priority Detection (Pro)

**From `model_gateway.py` (`_is_priority_email`, lines 546-572):**

```python
def _is_priority_email(self, scrubbed: Dict[str, Any]) -> bool:
    # Check for urgent/critical tags
    if tags.get("@urgent") or tags.get("@critical"):
        return True
    # Check for VIP sender
    if tags.get("@vip"):
        return True
    # Check urgency field
    if urgency in ("critical", "urgent", "high"):
        return True
```

**ZeroVeil Pro approach:**

cortex1-core sends priority hint in request:

```json
{
  "messages": [...],
  "metadata": {
    "scrubbed": true,
    "priority": "vip",       // or "urgent", "critical", "normal"
    "task_type": "email"     // for task-specific routing
  }
}
```

ZeroVeil uses `metadata.priority` to determine tier routing.

---

### 5. Cost Tracking (Pro)

**From `llm_metrics.py` (`log_llm_call`):**

```python
def log_llm_call(
    task_type: str,           # "email_processing", "draft_generation"
    backend: str,             # "openrouter", "ollama"
    tier: str,                # "tier1", "tier2", "tier3", "local"
    email_data: dict,
    escalation_reason: str | None = None,
    token_estimate: dict | None = None,
    actual_usage: dict | None = None,
    success: bool = True,
    error: str | None = None,
    metadata: dict | None = None,
)
```

**ZeroVeil Pro location:** Extend existing `audit.py`

**Implementation:**
- Track token usage per tier per tenant
- Calculate cost based on tier pricing
- Daily/monthly budget tracking
- Alert on budget thresholds (Pro feature per `editions.md`)

---

## What Stays in cortex1-core

### 1. Prompt Templates (`llm_prompts.py`)

Prompts are application-specific and should stay in cortex1-core. ZeroVeil is provider-agnostic and shouldn't know about email processing semantics.

### 2. Email Preprocessing (`email_preprocessor.py`)

Content cleaning, reply detection, signature removal - all application logic.

### 3. LLMProvider Abstraction

The unified OpenAI-compatible interface can stay in cortex1-core for:
- Local Ollama routing (bypasses ZeroVeil)
- Fallback when ZeroVeil is unavailable

### 4. Spam Bypass Logic (`_bypass_spam_emails`)

Application-level decision to skip LLM entirely for spam.

---

## Migration Steps

### Phase 0: Provider Adapters (Community) (Week 1)

**Prerequisite:** Replace stub response with actual provider calls in Community edition.

1. **Create provider abstraction (shared):**
   ```
   src/zeroveil_gateway/providers/
   ├── base.py              # ProviderAdapter interface
   ├── openrouter.py        # OpenRouter implementation
   └── ollama.py            # Ollama implementation
   ```

2. **Update `app.py`:**
   - Remove `content="stubbed_response"`
   - Route to provider based on `policy.allowed_providers[0]`
   - Return actual LLM response

### Phase 1: ZeroVeil Pro Infrastructure (Week 2-3)

1. **Create Pro-only tier routing module:**
   ```
   src/zeroveil_gateway/pro/
   ├── __init__.py          # Edition check, feature flags
   ├── tier_routing.py      # TierConfig, EscalationPolicy, route_request()
   ├── validation.py        # Output validation patterns
   └── pricing.py           # Cost calculation, budget tracking
   ```

2. **Create Pro policy schema:**
   ```json
   {
     "version": "1.1.0",
     "edition": "pro",
     "tier_escalation": {
       "enabled": true,
       "tiers": [
         {"name": "tier1", "model": "meta-llama/llama-3.1-8b-instruct", "cost_per_million": 0.05},
         {"name": "tier2", "model": "qwen/qwen-2.5-coder-32b-instruct", "cost_per_million": 0.14},
         {"name": "tier3", "model": "qwen/qwen-2.5-72b-instruct", "cost_per_million": 0.33}
       ],
       "escalate_vip_to": "tier3",
       "max_tier1_retries": 1
     },
     "budgets": {
       "daily_usd": 10.0,
       "monthly_usd": 200.0,
       "alert_threshold_pct": 80
     }
   }
   ```

3. **Add edition detection:**
   ```python
   def is_pro_edition() -> bool:
       return os.getenv("ZEROVEIL_EDITION") == "pro" or validate_license_key()
   ```

### Phase 2: Pro Tier Escalation (Week 3-4)

1. **Update `app.py` to conditionally use Pro features:**
   ```python
   if is_pro_edition() and policy.tier_escalation.enabled:
       result = pro.tier_routing.route_with_escalation(req, policy)
   else:
       # Community: single provider call, no escalation
       result = providers.call(selected_provider, req)
   ```

2. **Add Pro response metadata (headers):**
   ```python
   if is_pro_edition():
       response.headers["X-ZeroVeil-Tier"] = str(tier_used)
       response.headers["X-ZeroVeil-Escalation-Reason"] = reason or "none"
       response.headers["X-ZeroVeil-Cost-USD"] = f"{cost:.6f}"
   ```

### Phase 3: cortex1-core Integration (Week 4-5)

1. **Add ZeroVeil client to cortex1-core:**
   ```python
   class ZeroVeilClient:
       def __init__(self, gateway_url: str, api_key: str):
           ...

       def chat_completions(self, messages, metadata) -> dict:
           # Single endpoint call
           # - Community: single model, no escalation
           # - Pro: ZeroVeil handles tier selection + escalation
           ...
   ```

2. **Update `model_gateway.py`:**
   - Add `use_zeroveil: bool` config option
   - If enabled, route through ZeroVeil instead of direct OpenRouter
   - Keep Ollama routing local (privacy: local LLM never goes through gateway)

3. **Remove redundant code from cortex1-core (when using ZeroVeil Pro):**
   - `_call_openrouter_email_with_escalation()` → ZeroVeil Pro handles this
   - `_call_tier2_email()`, `_call_tier3_email()` → ZeroVeil Pro handles this
   - Tier model config → Moved to ZeroVeil Pro policy

   **Note:** Keep this code for direct OpenRouter mode (when ZeroVeil disabled).

### Phase 4: Testing & Rollout (Week 5-6)

1. **Test Community edition:**
   ```bash
   # Run ZeroVeil Community locally
   cd cortex1-zeroveil && uvicorn zeroveil_gateway.app:create_app --port 8080

   # Configure cortex1-core
   ZEROVEIL_GATEWAY_URL=http://localhost:8080
   ZEROVEIL_API_KEY=test-key
   ```

   **Verify Community:**
   - Single model routing works
   - Basic token counting in audit logs
   - No tier escalation (single tier only)

2. **Test Pro edition:**
   ```bash
   # Run ZeroVeil Pro locally
   ZEROVEIL_EDITION=pro uvicorn zeroveil_gateway.app:create_app --port 8080
   ```

   **Verify Pro:**
   - Tier escalation works (trigger validation failure, verify tier2 used)
   - VIP emails go to tier3 directly
   - Cost tracking with budget alerts
   - Response headers include tier/cost metadata
   - Fallback to direct OpenRouter if ZeroVeil unavailable

---

## API Contract

### Request (cortex1-core → ZeroVeil)

```json
POST /v1/chat/completions
Authorization: Bearer <zeroveil-api-key>
X-ZeroVeil-Tenant: cortex1

{
  "model": "auto",                    // Pro: Let ZeroVeil choose based on tier
                                      // Community: Uses policy.allowed_models[0]
  "messages": [...],
  "metadata": {
    "scrubbed": true,
    "priority": "normal",             // Pro only: "vip", "urgent", "critical"
    "task_type": "email_processing",  // Pro only: for task-specific routing/pricing
    "client_version": "cortex1-core/1.0"
  }
}
```

### Response - Community Edition

```json
{
  "id": "zv_abc123",
  "object": "chat.completion",
  "created": 1706000000,
  "model": "meta-llama/llama-3.1-8b-instruct",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "..."},
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 50,
    "total_tokens": 200
  }
}

// No tier/cost headers in Community
```

### Response - Pro Edition

```json
{
  "id": "zv_abc123",
  "object": "chat.completion",
  "created": 1706000000,
  "model": "meta-llama/llama-3.1-8b-instruct",   // Actual model used
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "..."},
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 50,
    "total_tokens": 200
  }
}

// Pro-only response headers:
X-ZeroVeil-Tier: tier1
X-ZeroVeil-Escalation-Reason: none
X-ZeroVeil-Cost-USD: 0.00001
X-ZeroVeil-Low-Confidence: false
X-ZeroVeil-Needs-Human-Review: false
```

---

## Backward Compatibility

1. **cortex1-core can still call OpenRouter directly** if ZeroVeil is disabled
2. **Ollama/local LLM routing stays in cortex1-core** (privacy: local processing never goes through gateway)
3. **ZeroVeil Community edition** works without tier escalation (uses single model from policy, no retries, no cost tracking beyond basic token counts)
4. **All tier escalation features are Pro-only:**
   - Multi-tier model routing
   - Automatic escalation on validation failure
   - VIP/priority direct-to-tier3 routing
   - Cost/budget tracking with alerts
   - A/B testing between models

---

## Files to Create in ZeroVeil

```
src/zeroveil_gateway/
├── providers/               # SHARED (Community + Pro)
│   ├── __init__.py
│   ├── base.py              # NEW: Provider interface
│   ├── openrouter.py        # NEW: OpenRouter adapter
│   └── ollama.py            # NEW: Ollama adapter (for self-hosted)
├── app.py                   # MODIFY: Replace stub with actual routing
│
├── pro/                     # PRO-ONLY MODULE
│   ├── __init__.py
│   ├── tier_routing.py      # NEW: Tier config, escalation logic
│   ├── validation.py        # NEW: Output validation patterns
│   ├── pricing.py           # NEW: Cost calculation, budgets
│   └── ab_testing.py        # NEW: A/B test between models

policies/
├── default.json             # Community: single model, basic limits
└── pro-example.json         # Pro: tier_escalation, budgets, A/B config
```

**Pro detection:** Check for `ZEROVEIL_EDITION=pro` env var or license key validation.

---

## Open Questions

1. **Should validation patterns be per-tenant configurable? (Pro)**
   - Pro: Different apps have different quality requirements
   - Con: Complexity, maintenance burden
   - **Decision:** Yes, Pro feature - store in tenant config

2. **Should ZeroVeil cache responses? (Pro)**
   - Pro: Cost savings for repeated queries
   - Con: Privacy implications, cache invalidation complexity
   - **Decision:** Defer - not in initial Pro release

3. **How to handle Ollama/local LLM?**
   - Option A: Always bypass ZeroVeil for local (current plan) ✓
   - Option B: Route through ZeroVeil for audit logging only
   - Option C: ZeroVeil can route to customer's Ollama endpoint
   - **Decision:** Option A for privacy; Option C as future Pro feature

4. **Budget enforcement (Pro):**
   - Hard cutoff when budget exceeded?
   - Soft warning + allow overflow?
   - Per-tenant vs per-task budgets?
   - **Decision:** Soft warning by default, configurable hard cutoff, per-tenant budgets

5. **Edition detection:**
   - Environment variable (`ZEROVEIL_EDITION=pro`)?
   - License key file?
   - Remote license validation?
   - **Decision:** Start with env var, add license key for production

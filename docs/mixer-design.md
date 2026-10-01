# Mixer Design (Research)

> **Research design, not built, not scheduled.** This document describes a research direction only. It is not implemented in any release, ZeroVeil v0.2.0 contains none of it, and it is not a product feature. ZeroVeil makes no anonymity, unlinkability, or correlation-resistance claim. Every statement below is hypothetical: it describes what such a design would do, not what ZeroVeil does.

This note sketches how a request-aggregation ("mixer") layer could be structured if one were ever built.

**Hypothetical goal:** Reduce how directly a provider could associate a request with the tenant that sent it. Whether any design achieves this would have to be demonstrated; none is claimed.

---

## Overview

```
Tenant A ──┐
Tenant B ──┼──→ [Auth + Validate] ──→ [Aggregation Queue] ──→ [Shared API Key] ──→ Provider
Tenant C ──┘         │                      │
                     │                      │
              Verify attestation     Batch + Shuffle
              Rate limit check       Random delays
              Strip tenant headers   Normalize requests
```

In such a design, the provider would see requests arriving under the shared credential, without tenant headers.

---

## Hypothetical Primitives

### 1. Request Batching

A mixer would collect several requests before dispatching them.

```python
@dataclass
class MixerConfig:
    min_batch_size: int = 3         # Wait for N requests before dispatch
    max_wait_ms: int = 500          # Or timeout, whichever comes first
    jitter_range_ms: tuple = (50, 200)  # Random delay per request
```

**Trade-off:** Larger batches would add latency.

| Setting | Latency Impact |
|---------|----------------|
| min_batch=1, max_wait=0 | None (pass-through) |
| min_batch=3, max_wait=500ms | Up to 500ms |
| min_batch=10, max_wait=2000ms | Up to 2s |

### 2. Request Normalization

A mixer would strip tenant-identifying metadata before forwarding.

```python
def normalize_request(req: dict, tenant: TenantConfig) -> dict:
    """Remove tenant-identifying fields from the request."""
    return {
        "messages": req["messages"],
        "model": req.get("model", "default"),
        "metadata": {
            "scrubbed": req.get("metadata", {}).get("scrubbed", False),
        },
    }
```

Fields it would drop: the tenant header, client IP address, request timestamps (replaced with a batch timestamp), and custom metadata beyond the scrub attestation.

### 3. Shuffle Dispatch

A mixer would randomize the order within each batch.

```python
import random
import asyncio

async def dispatch_batch(batch: list[NormalizedRequest]) -> list[Response]:
    """Dispatch batch in random order with jitter."""
    random.shuffle(batch)

    responses = []
    for req in batch:
        await asyncio.sleep(random.uniform(0.05, 0.2))
        responses.append(await send_to_provider(req))

    return responses
```

### 4. One-Time Response Tokens

A mixer would need to route responses back without keeping a persistent tenant-to-request mapping.

```python
import secrets

token = secrets.token_hex(16)  # One-time, random
pending_responses[token] = tenant_connection

async def handle_response(response, token):
    tenant_conn = pending_responses.pop(token)  # Remove immediately
    await tenant_conn.send(response)
```

### 5. Shared Relay Credential

In such a design, all requests would use one provider credential held by the aggregating operator. A self-hosted gateway with a single tenant would gain nothing from this and would only keep policy enforcement and ZDR routing.

---

## Limits (even in a hypothetical build)

| Concern | Why a mixer would not address it |
|---------|----------------------------------|
| Stylometry (writing style) | Content-based |
| Semantic fingerprinting | Unique topics can identify the sender |
| Few tenants | A small pool would give little aggregation |
| Compromised or colluding operator | The operator would see individual requests |
| Legal compulsion | The operator could be compelled to disclose |

---

## Hypothetical Configuration

Nothing below exists in the gateway. These names are illustrative only.

```bash
ZEROVEIL_MIXER_MIN_BATCH=3
ZEROVEIL_MIXER_MAX_WAIT_MS=500
ZEROVEIL_MIXER_JITTER_MIN_MS=50
ZEROVEIL_MIXER_JITTER_MAX_MS=200
ZEROVEIL_MIXER_ENABLED=false
```

```json
{
  "version": "1",
  "mixer": {
    "enabled": true,
    "min_batch_size": 3,
    "max_wait_ms": 500,
    "jitter_ms": [50, 200]
  }
}
```

---

## Implementation Status

None of the components above is implemented or scheduled.

---

## Hypothetical Security Considerations

A mixer would have to avoid logging request content, one-time tokens after response delivery, and tenant-to-request mappings. It could log metadata only (batch sizes, aggregate latency, error rates), clear tokens immediately after delivery, keep the batch queue bounded, dispatch a partial batch on timeout, return provider errors to the originating tenant only, and reject new requests (429) under memory pressure.

---

*Research note. Last revised: October 2026.*

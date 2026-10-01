# Contributing to Cortex1-ZeroVeil (Community Gateway)

This repository is source-available under PolyForm Noncommercial 1.0.0 (`LICENSE`), with a 32-day commercial evaluation under PolyForm Free Trial 1.0.0 (`LICENSE-FREE-TRIAL`); nonprofits use it free. We welcome contributions that improve safety, correctness, and adoption.

## Ground Rules (Safety + Claims)

- Do not add marketing language that implies “guaranteed anonymity”. This project provides **risk reduction**, not magic.
- Do not add server-side “scrub-as-a-service”. Scrubbing is designed to be client-side; the gateway enforces scrub attestation.
- Do not introduce prompt/response content logging by default.

## Contribution Requirements

### 1) Contribution terms (accepted by your DCO sign-off)

Signing off your commits accepts the terms in `CLA.md` (a license grant; you keep ownership). There is no separate CLA signature. Pseudonymous handles are fine; we only need a consistent identity and a working email.

### 2) Sign your commits (Required, the only acceptance step)

Every commit needs a DCO sign-off:

```bash
git commit -s -m "Your message"
```

This adds `Signed-off-by: ...` to the commit message.

## What to Work On

- Policy enforcement tests and conformance harness
- Provider adapter hardening (timeouts, retries, safe error mapping)
- Documentation (threat model, retention, deployment examples)
- Security posture improvements (rate limits, abuse resistance, config validation)

## How to Submit a PR

1. Fork the repo and create a branch.
2. Install dev deps: `python -m pip install -e ".[dev]"`
3. Run tests: `python -m pytest -q`
4. Open a PR with a short description of the behavior change and why it’s safe.

## Security Issues

Please do not open public issues for security vulnerabilities. See `SECURITY.md`.

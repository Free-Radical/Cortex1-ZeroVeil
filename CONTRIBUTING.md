# Contributing to Cortex1-ZeroVeil (Community Gateway)

This repository is source-available under Business Source License 1.1 (`LICENSE`). We welcome contributions that improve safety, correctness, and adoption.

## Ground Rules (Safety + Claims)

- Do not add marketing language that implies “guaranteed anonymity”. This project provides **risk reduction**, not magic.
- Do not add server-side “scrub-as-a-service”. Scrubbing is designed to be client-side; the gateway enforces scrub attestation.
- Do not introduce prompt/response content logging by default.

## Contribution Requirements

### 1) CLA (Required)

By submitting a pull request, you agree to the **license-grant CLA** in `CLA.md`. You keep ownership of your contributions; you grant the Project the rights needed to distribute and (later) transition to Apache 2.0 per the Change Date in `LICENSE`.

If CLA checks are enabled, the bot will prompt you to comment:

`I have read the CLA Document and I hereby sign the CLA`

You only need to do this once.

### 2) Sign your commits (Recommended)

We recommend using DCO-style sign-offs on commits:

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

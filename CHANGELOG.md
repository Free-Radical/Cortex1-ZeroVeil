# Changelog

## 0.2.0 - 2026-10-01
- OpenRouter provider requests now always carry ZDR provider settings
  (`zdr: true`, `data_collection: "deny"`, `allow_fallbacks: false`); a
  caller-supplied provider block can add routing preferences but can no
  longer weaken these three values.
- Added `LICENSE-FREE-TRIAL` (PolyForm Free Trial 1.0.0) for a 32-day
  commercial evaluation window; `COMMERCIAL-LICENSE.md` and `NOTICE.md`
  updated to reference it.
- `CLA.md` bumped to v0.2: dropped stale BSL/Apache/Change-Date language,
  clarified that acceptance is a DCO `Signed-off-by` line (pseudonymous
  handles welcome).
- Replaced the CLA-signature-bot workflow (`.github/workflows/cla.yml`)
  with the existing DCO check (`.github/workflows/dco.yml`).
- Removed mixer/anonymity/unlinkability/correlation-resistance language
  presented as a current or near-term feature from README, NOTICE,
  TODO.md, docs/architecture.md and pyproject's description; the mixer
  design remains research-only documentation in `docs/mixer-design.md`
  with a new top-of-file disclaimer.
- Replaced remaining stale BSL/Apache/Change-Date license references with
  PolyForm Noncommercial 1.0.0 across CONTRIBUTING.md, TODO.md,
  docs/architecture.md and README.md.
- Repository links now point to `https://github.com/ZeroVeilAI/zeroveil`;
  added `site/index.html` as the project's static landing page.
- `pyproject.toml`: version 0.2.0, updated project description, added
  `[project.urls]` (Homepage, Repository).

## Unreleased
- License updated to PolyForm Noncommercial License 1.0.0.
- Commercial, hosted, managed-service, customer-facing, internal business,
  revenue-generating, paid, or other monetized use requires a separate written
  commercial license.

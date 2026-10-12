# Changelog

## 0.2.0 - 2026-10-01
- OpenRouter provider requests now always carry ZDR provider settings
  (`zdr: true`, `data_collection: "deny"`, `allow_fallbacks: false`); a
  caller-supplied provider block can add routing preferences but can no
  longer weaken these three values. The OpenRouter `Referer` is
  `https://zeroveil.io`.
- License: PolyForm Noncommercial 1.0.0 plus PolyForm Free Trial 1.0.0
  (`LICENSE-FREE-TRIAL`, a 32-day commercial evaluation); nonprofits are free.
  One canonical license sentence is now used in README, NOTICE.md, COPYRIGHT,
  COMMERCIAL-LICENSE.md, docs/editions.md, docs/architecture.md and
  `site/index.html`; `pyproject.toml` carries a matching `license` field.
  Earlier license wording and the old transition note in `NOTICE.md` were
  removed.
- Contributions: acceptance is by DCO sign-off only. `CLA.md` is v0.2 (license
  grant text unchanged, acceptance by sign-off), `CONTRIBUTING.md` and the PR
  template no longer ask for a separate CLA signature, and the CLA-signature
  workflow was replaced by the DCO check (`.github/workflows/dco.yml`).
- `NOTICE` prior-art item 1 is reworded as "Request aggregation (research
  design, not implemented, not a product feature)"; the identity-privacy
  responsibility claim was removed.
- Removed privacy-benefit claims for the unbuilt aggregation design from
  README, docs/architecture.md, docs/mixer-design.md (now conditional research
  only, no schedule or status table), docs/threat-model.md and pyproject's
  description.
- Removed language describing any ZeroVeil-operated hosted/cloud service
  (README, docs/architecture.md, docs/compliance.md): v0.2.0 is self-hosted
  only.
- Removed `docs/whitepaper.md`, `TODO.md` and
  `docs/migration-cortex1-tier-escalation.md`, and all references to them.
- Removed pointers to private repositories from README and docs/editions.md;
  this repository is canonical.
- Repository links point to `https://github.com/Free-Radical/Cortex1-ZeroVeil`; added
  `site/index.html` as the project's static landing page.
- `pyproject.toml`: version 0.2.0, updated project description, added
  `[project.urls]` (Homepage, Repository).

# Roadmap — 12-week MVP (distilled from proposal)

Status as of OpenPulse 100: schema 0.4.0, 129 tests, catalog at
100 entries, September report regenerated over the full catalog with
sourced references, iText license case validated end to end.

## Done

- [x] **Phase 0 (W1) — Schema freeze.** `core/schema/` v0.4.0 (was v0.1.0;
  additive provenance/independence/relation fields). Event taxonomy,
  confidence, impact levels frozen.
- [x] **Phase 1 (W2–4) — Collectors.** All 7: github (+repo metadata),
  osv, nvd (+CPE criteria), cve, kev (+match strength), endoflife.date,
  registries (+digests). Structured `CollectorError`s, graceful degrade.
- [x] **Phase 2 (W3–5) — Analysts.** Change, Security, Evidence, Report
  as pure functions + evidence gate with veto power. No giant agent.
- [x] **Phase 3 (W5) — Bitnami validation.** Reference event
  (`CONFIRMED`/`ACTION`, 3 official evidences), `demo-bitnami`
  rehearsal, permanent acceptance test (`tests/test_acceptance.py`).
  Gate passed — SaaS track unblocked in principle, not started.
- [x] **Phase 4 (W5–7) — OSS Pulse facets.** `core/pulse.py` maps
  findings+events to 7 facets (worst-wins + reason); `pulse` CLI
  renders computed status live or from offline bundles.
- [x] **Trust hardening (arch review).** Provenance fields, independent
  corroboration, NVD relationships + caps, KEV strength, observation
  history + diffs, `CollectorError` redaction, CLI input bounds,
  `PROJECT_ARCHIVED`, CI (least privilege, CodeQL, pip-audit),
  Dependabot.
- [x] **Security re-implementation.** Conservative CPE identity,
  explicit version applicability (`core/versions.py`), claim objects +
  support/conflict gate rules, generalized observations, typed identity
  refs, `AFFECTS_ARTIFACT` matching, explainable security rendering,
  SHA-pinned actions, `requirements.lock`, 10-test boundary contract.
  See `IMPLEMENTATION_PLAN.md` / `IMPLEMENTATION_SUMMARY.md`.
- [x] **Early Warning integrity hardening.** Explicit `DependencyVerdict`,
  scope-driven matching, `NOT_AFFECTED`, tri-state versions end to end,
  `version_scheme`, watchlist metadata, four-state `check` output.

## In progress

- [x] **Phase 5 — OpenPulse 100 seed.** Catalog at 100 entries
  (was 10), incl. endoflife overrides verified live (kafka, airflow,
  spark, argocd, cassandra, couchdb) and the iText license-change
  reference case (`data/fixtures/itext-license/`).
- [x] **Phase 6 (W7–8) — Monthly report pipeline.** `reports/generate.py`
  ranks seed projects into action-worthy / watch / informational with
  evidence per item; `openpulse report --month YYYY-MM` runs offline
  bundles or live collectors and writes `reports/<month>-openpulse.md`.
- [x] **Phase 10 preview — watchlist check.** `openpulse check
  --watchlist file --event file` evaluates image refs (artifact/project
  matching) and versioned packages (OSV/CPE ranges → `AFFECTS_VERSION`
  for exact pins); `--strict` exits 1 when anything is affected.

## Not started

- **Phase 7–10 (W8–12)** — website, follows/newsletter, customer
  watchlist, impact engine (only `core/risk/match.py` preview exists).

## Non-goals W1–12 (unchanged)

Full SAST/SCA duplication, auto-remediation, CI/CD apps, SSO/RBAC,
mobile, opaque risk scores. They don't prove the core hypothesis.

## Next — scheduled watching at scale + report cadence

1. **Report cadence**: monthly regeneration ritual (first Monday run,
   curator pass, commit). October edition grows with the catalog.
2. **Digest consumers**: post `--digest` output where teams already look
   (release notes, Slack webhook recipe in `docs/SCHEDULED_CHECKS.md`).
3. **Seed growth** (#9): 50 → 70, prioritizing report coverage gaps.

Deliberately later: accounts, dashboards, SaaS monitoring.

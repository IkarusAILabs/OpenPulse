# Roadmap — 12-week MVP (distilled from proposal)

Status as of v0.4 check: schema 0.3.0, 99 tests, catalog at
45 entries, watchlist checking with version-aware verdicts.

## Done

- [x] **Phase 0 (W1) — Schema freeze.** `core/schema/` v0.3.0 (was v0.1.0;
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

## In progress

- [ ] **Phase 5 remainder — OpenPulse 100 seed.** Catalog at 45 entries
  (was 10). Growth toward 100 continues in #9.
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

## Next — website readability + alerts (recommended)

The engine answers everything locally now. Next makes it consumable:

1. **Publish the report**: render `reports/` markdown for the web
   (static site or README-linked archive) — the Free level made real.
2. **Scheduled watching**: `check` on a timer (cron doc + `--strict`
   for CI gates) with a weekly digest shape reusing `render_digest`.
3. **Seed growth** (#9): 45 → 70, prioritizing report coverage gaps.

Deliberately later: accounts, dashboards, SaaS monitoring.

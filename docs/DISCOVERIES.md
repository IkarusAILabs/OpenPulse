# M2 Discovery Ledger — acceptance evidence, not aspirations

Milestone M2 (`docs/ROADMAP.md`) is met only by reproducible,
automatically-detected non-lifecycle discoveries. This file is the
ledger: every case carries the full acceptance shape (what changed,
why it matters, affected artifact/package, evidence, confidence,
first detection, effective date, applicable scope) plus a
verification status and reproduction. Curated-only entries are
marked and never counted. A case that cannot replay is removed,
not argued for.

Acceptance status: **NOT MET — 2 of 5 verified.** The gap and the
path to close it are recorded below, not hidden.

## Case 1 — minio/minio archived ✅ VERIFIED

- What changed: the minio/minio GitHub repository was archived (read-only).
- Why it matters: no fixes will land upstream; dependents need a migration plan.
- Affected: project `minio` (repository `minio/minio`).
- Evidence: live `repo_meta` 2026-10-02 — `archived: True`,
  `pushed_at: 2026-04-24T17:54:39Z`, `full_name: minio/minio`.
- Confidence: EMERGING (single primary source: the repository itself).
- First detection: 2026-10-02 (analyst run; observation-history tracking
  for lifecycle-class findings is follow-up work).
- Effective date: 2026-04-24 (last push; archival date unrecorded by the source).
- Scope: project-wide. Finding: `PROJECT_ARCHIVED` / REVIEW-eligible.
- Reproduction: `openpulse analyze --project minio` (or
  `analyze_github_meta` on the recorded meta — see
  `tests/test_discoveries.py::test_minio_archived_replays`).
- Ownership check: owner unchanged (`minio/minio`) — the drift
  detector correctly stays silent
  (`test_minio_shows_no_ownership_drift`).

## Case 2 — Bitnami version-distribution split ✅ VERIFIED (structural)

- What changed: versioned Redis tags do not live in `docker.io/bitnami/redis`;
  versioned distribution lives in `docker.io/bitnamilegacy/redis`.
- Why it matters: pinned `bitnami/redis:<version>` references resolve
  against a namespace with no versioned tags — migration planning.
- Affected: artifact namespace `docker.io/bitnami/redis` (all versioned refs).
- Evidence: full-set registry observations 2026-10-02 —
  bitnami/redis: 534 tags, **0 version-like** (latest + `sha256-*`
  digest tags); bitnamilegacy/redis: 919+ version-like tags
  (`5.0.4`, `5.0.3-r75`, …). Reproduce from local history:
  `load_all('docker.io', <ns>, 'redis')` under `.openpulse/observations`.
- Confidence: EMERGING (direct observation, single source family).
- First detection: 2026-10-02 (structural confirmation; per-tag
  first-detection tracking applies to diffs, not to this split).
- Effective date: unrecorded (the move predates observation history).
- Scope: artifact namespace.
- Known detector gap (locked by
  `test_bitnami_digest_mainline_gap_locked`): the `latest_only`
  namespace heuristic does not fire on digest-tagged mainlines, so no
  producer derives this split yet. A version-aware rule is follow-up
  work — it must flip that test, not sneak past it.

## Cases 3–5 — registry pruning (nginx / python / mongo) ⏳ PENDING RE-VERIFICATION

- Observed 2026-10-01: tag disappearances (nginx `1.30-alpine*`,
  python `3.12-slim*`/`3.10-slim*`, mongo `8.3-noble*`, postgres
  `19beta4-bookworm`) with chain-verified observation identity
  (prior report revision `dd4bd59`, superseded).
- Status: NOT counted. Those probes used a 5-tag recency window
  (`page_size=5`, first page only) — a tag bumped out of the window
  is indistinguishable from a removal. Formalizing window-era diffs
  as removals would fabricate confidence.
- Path to verification: full-set probes (shipped: `page_size=100` +
  pagination, parser `0.4.1`→`0.4.2`) against current Hub state.
  Blocked 2026-10-02 by Hub `403` rate limiting. Confirm-or-kill per
  tag on quota reset: absent from the full set confirms removal
  (case accepted); present kills the case (record the kill here).

## Anti-case — the 5-tag window flaw (caught, fixed)

Same-session catch: symmetric appear/disappear pairs (`latest`
vanishing from golang while appearing on mongo) exposed first-page-
only acquisition. Fixed without weakening: full pagination
(`collectors/registries/docker.py`), page-cap + `truncated` flag
with diffs withheld on partial sets
(`core/observations/registry.py`), parser-version re-baseline guard
(`core/observations/sweep.py`, `0.4.0`→`0.4.1`→`0.4.2`), golden
hashes advanced. Recorded here so the bar stays visible: the
pipeline must not be able to claim more than its acquisition supports.

## Armed, awaiting live firing

- Ownership drift (`OWNERSHIP_CHANGE`, `analyze_github_meta`):
  owner-change detection with same-owner renames silent. Offline
  proofs in `tests/test_analysts.py`; no live firing yet (needs a
  real transfer; GitHub quota reserved).
- Namespace moves (`split_moves`, `core/observations/sweep.py`):
  cross-namespace appear/disappear pairs become one migration story.
  Offline proofs in `tests/test_correlation.py`; no live pair
  observed yet.

## What closes acceptance

1. Hub quota reset → confirm-or-kill the three pruning cases (accept
   confirmations, record kills).
2. One live firing from the armed detectors (move or ownership).
3. Version-aware latest-only rule flipping the Bitnami gap test.

Then: 5 verified cases, M2 acceptance met, M4 benchmark fed.

# M2 Discovery Ledger — acceptance evidence, not aspirations

Milestone M2 (`docs/ROADMAP.md`) is met only by reproducible,
automatically-detected non-lifecycle discoveries. This file is the
ledger: every case carries the full acceptance shape (what changed,
why it matters, affected artifact/package, evidence, confidence,
first detection, effective date, applicable scope) plus a
verification status and reproduction. Curated-only entries are
marked and never counted. A case that cannot replay is removed,
not argued for.

Acceptance status: **NOT MET — 4 of 5 verified.** The pruning
candidates were probed 2026-10-03 and killed (see Cases 3–5); the
two live ownership-move firings below (Cases 6–7, capa and etcd)
replaced them. One more verified case closes the set; the gap and
the path to close it are recorded below, not hidden.

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
- Detector gap closed (was locked by
  `test_bitnami_digest_mainline_gap_locked`, now flipped to
  `test_bitnami_digest_mainline_gap_closed`): the `latest_only`
  probe flag is version-aware — a mainline serving only `latest`
  plus digest/attestation tags (`sha256-*`, `*.sig`, `*.att`,
  `-metadata`) counts as latest-only, any version-like tag
  disqualifies it (`collectors/registries/docker.py:parse_tags`).
  The model-change finding now fires for the recorded probe shapes,
  so this split is producer-derived, not just analyst-confirmed.

## Cases 3–5 — registry pruning (nginx / python / mongo) ❌ KILLED (wrong-window artifacts)

- Observed 2026-10-01: tag disappearances (nginx `1.30-alpine*`,
  python `3.12-slim*`/`3.10-slim*`, mongo `8.3-noble*`, postgres
  `19beta4-bookworm`) with chain-verified observation identity
  (prior report revision `dd4bd59`, superseded).
- Status: NOT counted. Those probes used a 5-tag recency window
  (`page_size=5`, first page only) — a tag bumped out of the window
  is indistinguishable from a removal. Formalizing window-era diffs
  as removals would fabricate confidence.
- Kill verification 2026-10-03: every candidate tag is present in the
  current sets. All ten of ten per-tag lookups on the Hub API
  (`/v2/repositories/library/<repo>/tags/<tag>`) returned `200` with
  `tag_status: active`; the v2 registry protocol full lists
  (`auth.docker.io` pull token → `registry-1.docker.io/v2/library/
  <repo>/tags/list`, one response, no pagination) show
  nginx 1,339 tags (Hub `count` 1,339), python 3,974 (3,974),
  mongo 3,670 (3,670), postgres 1,427 (1,427) — and every candidate
  (nginx `1.30-alpine3.24`, `1.30.5-alpine3.24`, `1.30.5-alpine`;
  python `3.11.16-slim-trixie`, `3.12-slim-trixie`, `3.12-slim`,
  `3.12.14-slim-trixie`; mongo `8.3-noble`, `8.3.11-noble`; postgres
  `19beta4-bookworm`) is in its list.
- Verdict: wrong-window artifacts, not removals. Killed per the
  confirm-or-kill rule — recorded, not silently dropped.
- Corroboration: python `3.12-slim-trixie`/`3.12-slim` and mongo
  `8.3-noble`/`8.3.11-noble` were re-pushed 2026-10-02
  (`tag_last_pushed` 2026-10-02T02:08Z / 06:08Z), i.e. active
  recency churn — exactly what a 5-tag window mistakes for removal.
- Acquisition note: the prescribed `check_image` full-set probe could
  not complete for any of these repos — Hub now rejects anonymous
  pagination past ~offset 500 with
  `403 "pagination offset too large for anonymous requests"` while
  `x-ratelimit-remaining` sits untouched at 160/180, so the
  collector's 30-page walk is structurally `truncated` for repos this
  large. Presence verdicts do not need the full window, so the kills
  stand on the per-tag + v2-list evidence above. The acquisition gap
  itself is filed as #36.

## Case 6 — fireeye/capa moved to mandiant/capa ✅ VERIFIED (live replay)

- What changed: the capa repository moved from `fireeye/capa` to
  `mandiant/capa` (Mandiant acquired FireEye's products business,
  2021). A recorded `github.com/fireeye/capa` require, remote or
  checkout URL now names a redirect, not a first-party source.
- Why it matters: recorded source paths silently change meaning on
  an ownership move; pulls work via redirect today and break when
  the redirect or the archived shape changes.
- Affected: source reference `github.com/fireeye/capa` (the
  moved-from path). The moved-to path is a different identity.
- Evidence: live `repo_meta` 2026-10-06 — queried `fireeye/capa`,
  `full_name: mandiant/capa`, `archived: false`,
  `pushed_at: 2026-10-05T14:43:20Z`, `stargazers: 6213`,
  fixture `data/fixtures/capa-move/raw_bundle.json`.
- Confidence: EMERGING (single primary source: the repository itself).
- First detection: 2026-10-06 (live probe; replayed offline by
  `test_golden_capa_ownership_move`).
- Effective date: the transfer predates observation history;
  unrecorded — the stale reference is in force now.
- Scope: project-wide, artifact-named. Finding:
  `OWNERSHIP_CHANGE` / REVIEW-eligible; the finding names the
  moved-from path as its affected artifact (gate requirement).
- Reproduction: `openpulse analyze --project capa` (or
  `analyze_github_meta` on the recorded meta — see the golden test).

## Case 7 — coreos/etcd moved to etcd-io/etcd ✅ VERIFIED (live replay)

- What changed: the etcd repository moved from `coreos/etcd` to
  `etcd-io/etcd` (CoreOS wind-down, 2018). A recorded
  `github.com/coreos/etcd` require or remote now names a redirect.
- Why it matters: same class as Case 6 on a second real move —
  proves the rule is not shaped around one repository's history.
- Affected: source reference `github.com/coreos/etcd`.
- Evidence: live `repo_meta` 2026-10-06 — queried `coreos/etcd`,
  `full_name: etcd-io/etcd`, `archived: false`,
  `pushed_at: 2026-10-05T23:11:12Z`, `stargazers: 52329`,
  fixture `data/fixtures/etcd-move/raw_bundle.json`.
- Confidence: EMERGING (single primary source).
- First detection: 2026-10-06 (live probe; replayed offline by
  `test_golden_etcd_namespace_move`).
- Effective date: predates observation history; in force now.
- Scope: project-wide, artifact-named. Finding:
  `OWNERSHIP_CHANGE` / REVIEW-eligible.

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
  **fired live twice** (Cases 6–7, capa and etcd, 2026-10-06) and
  formalized with golden replays; same-owner renames stay silent
  (offline proofs in `tests/test_analysts.py`).
- Namespace moves (`split_moves`, `core/observations/sweep.py`):
  cross-namespace appear/disappear pairs become one migration story.
  Offline proofs in `tests/test_correlation.py`; no live pair
  observed yet.

## What closes acceptance

1. ~~Confirm-or-kill the three pruning cases~~ — done 2026-10-03,
   all three killed (Cases 3–5). Replacements delivered 2026-10-06:
   Cases 6–7 (capa, etcd ownership moves) from live repo_meta
   probes. One more verified case closes the set; #36 (Hub
   anonymous pagination cap) still blocks full-set probes for
   large repos.
2. ~~One live firing from the armed detectors (move or
   ownership)~~ — ownership fired live twice (Cases 6–7). The
   cross-namespace `split_moves` detector stays armed, awaiting a
   live pair.
3. Version-aware latest-only rule flipping the Bitnami gap test —
   CLOSED: `parse_tags` is version-aware and the flipped test
   (`test_bitnami_digest_mainline_gap_closed`) plus a no-false-positive
   test on versioned mainlines lock it. Case 2 is now producer-derived.

Then: 5 verified cases, M2 acceptance met, M4 benchmark fed.

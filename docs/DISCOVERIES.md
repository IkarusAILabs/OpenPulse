# M2 Discovery Ledger — acceptance evidence, not aspirations

Milestone M2 (`docs/ROADMAP.md`) is met only by reproducible,
automatically-detected non-lifecycle discoveries. This file is the
ledger: every case carries the full acceptance shape (what changed,
why it matters, affected artifact/package, evidence, confidence,
first detection, effective date, applicable scope) plus a
verification status and reproduction. Curated-only entries are
marked and never counted. A case that cannot replay is removed,
not argued for.

Acceptance status: **MET 2026-10-07 — 5 of 5 verified, all
live-replayed.** The pruning candidates were probed 2026-10-03 and
killed (see Cases 3–5); capa and etcd (2026-10-06) then traefik,
fbsdk and bitnami/spark (2026-10-07) replaced them. Every counted
case replays offline from recorded evidence; the residual gaps are
recorded below, not hidden.

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

## Case 8 — containous/traefik renamed to traefik/traefik ✅ VERIFIED (live replay)

- What changed: the repository moved from `containous/traefik` to
  `traefik/traefik` when Traefik Labs replaced the Containous
  company identity (2020). A recorded `github.com/containous/traefik`
  require or remote now names a redirect, while the moved-to repo
  ships actively (v3.7.14 released 2026-10-06).
- Why it matters: third real move through the same rule — proves it
  is not shaped around capa (acquisition), etcd (wind-down) or dead
  projects; live-destination moves are the common shape.
- Affected: source reference `github.com/containous/traefik` (the
  moved-from path). The moved-to path is a different identity.
- Evidence: live `repo_meta` 2026-10-07 — queried `containous/traefik`,
  `full_name: traefik/traefik`, `archived: false`,
  `pushed_at: 2026-10-06T07:48:29Z`, `stargazers: 65098`; latest
  release `v3.7.14` published `2026-10-06T07:49:56Z`; fixture
  `data/fixtures/traefik-move/raw_bundle.json`.
- Confidence: EMERGING (single primary source: the repository itself).
- First detection: 2026-10-07 (live probe; replayed offline by
  `test_golden_traefik_ownership_move`).
- Effective date: the rename predates observation history;
  unrecorded — the stale reference is in force now.
- Scope: project-wide, artifact-named. Finding:
  `OWNERSHIP_CHANGE` / REVIEW-eligible.
- Reproduction: `openpulse analyze --project traefik` (or
  `analyze_github_meta` on the recorded meta — see the golden test).

## Case 9 — facebook/react-native-fbsdk moved AND archived ✅ VERIFIED (live replay)

- What changed: the repository moved from `facebook/react-native-fbsdk`
  to `facebookarchive/react-native-fbsdk` and was archived (2021):
  one recorded repository carrying both signals at once. The final
  release `v3.0.0` (2020-11-23) predates the archive — every pin is
  a pin of a dead project.
- Why it matters: first combined case — archive and ownership are
  independent findings, not one folded event; the dead-and-moved
  combination is only visible by observation.
- Affected: source reference `github.com/facebook/react-native-fbsdk`
  (the moved-from path); the npm package pin is contextual
  (the project itself is read-only).
- Evidence: live `repo_meta` 2026-10-07 — queried
  `facebook/react-native-fbsdk`,
  `full_name: facebookarchive/react-native-fbsdk`, `archived: true`,
  `pushed_at: 2021-03-26T23:24:22Z`, `stargazers: 2973`; final
  release `v3.0.0` published `2020-11-23`, release URL served from
  the archive org; fixture
  `data/fixtures/fbsdk-archive-move/raw_bundle.json`.
- Confidence: EMERGING (single primary source each finding).
- First detection: 2026-10-07 (live probe; replayed offline by
  `test_golden_fbsdk_archive_and_move`).
- Effective date: archived 2021; in force now, nothing upcoming.
- Scope: project-wide, artifact-named. Findings: `PROJECT_ARCHIVED`
  (ACTION proposal, REVIEW-capped) + `OWNERSHIP_CHANGE` (REVIEW).
- Reproduction: `openpulse analyze --project react-native-fbsdk` (see
  the golden test for both findings firing together).

## Case 10 — docker.io/bitnami/spark mainline answers empty ✅ VERIFIED (live replay)

- What changed: `docker.io/bitnami/spark` now answers with an empty
  tag set — not `latest`-only, zero names on both the Hub API
  (`count: 0`) and the registry v2 protocol (`tags: []`) — while
  `docker.io/bitnamilegacy/spark` holds all 936 historical tags
  (859 version-like, digests recorded for all 936, no pushes since
  2025-08-08). The Bitnami catalog deletion (announced 2025-07-16,
  effective 2025-08-28, postponed to 2025-09-29) produced a
  distribution removal one step past latest-only for repos outside
  the kept subset.
- Why it matters: the split rule previously required `latest_only`
  on the mainline side and stayed silent on exactly this shape; the
  empty probe is the observed end-state of the deletion the curated
  Bitnami case announced. An empty answer is a distribution-model
  fact, not a missing-repo error (that is the `missing` 404 flag).
- Affected: pinned `docker.io/bitnami/spark:<version>` (no longer
  resolves) and `docker.io/bitnamilegacy/spark:<version>` (frozen,
  unsupported snapshot); upstream `docker.io/apache/spark` explicitly
  NOT affected.
- Evidence: live registry probes 2026-10-07 — Hub
  `bitnami/spark` `count: 0`; v2 protocol `tags: []`; Hub
  `bitnamilegacy/spark` `count: 936` with the full name set;
  official announcement `github.com/bitnami/containers#83267`;
  fixtures `data/fixtures/spark-mainline-empty/` (both probes +
  curated event).
- Confidence: CONFIRMED (official announcement + primary probes) in
  the curated event; producer-side finding bridges EMERGING with a
  date violation — weak evidence holds itself back.
- First detection: 2026-10-07 (live probe; replayed offline by
  `test_golden_bitnami_spark_empty_mainline`).
- Effective date: 2025-08-28 (catalog deletion postponed to
  2025-09-29); in force now.
- Scope: artifact-scoped, both namespace refs named. Finding:
  `DISTRIBUTION_CHANGE` / REVIEW-eligible at the producer layer;
  ACTION in the curated event.
- Reproduction: `openpulse analyze` on the two recorded probes (see
  the golden test) or `openpulse check --images` against the
  curated event.

## Phase 14 cases (v0.20.0) — change evidence beyond lifecycle

Each class Phase 14 added needs at least one case here before it is
claimed (decision 19, item C6); `analyzers.change_analyst.VERIFIED_CASES`
names them, every finding carries `support: verified` with its case
numbers, and a class with none is `experimental` and says so. The
registry responses below were recorded 2026-11-09 under
`data/fixtures/<case>/`, trimmed to the fields the checks read (values
verbatim, each file names its source URL), and replay offline in
`tests/test_discoveries.py`. Each case is also confirmed by a source
the detection did not use.

| Class | Cases | Status |
|---|---|---|
| Release licenses, npm (C3) | 11 | verified |
| Release licenses, PyPI (C3) | 12 | verified |
| npm `deprecated` (C4) | 13, 14 | verified |
| PyPI yanked (C4) | 15 | verified |
| PyPI Inactive classifier (C4) | 16 | verified |
| Repository history: license, archive, move (C2) | — | **experimental** |

## Case 11 — react relicensed BSD-3-Clause to MIT ✅ VERIFIED (recorded replay)

- What changed: release 15.6.2 is the first, by version, to declare MIT;
  15.6.1 declared BSD-3-Clause.
- Why it matters: a license change between the release you run and the
  one you upgrade to changes what you may do with it.
- Affected: `pkg:npm/react`, releases from 15.6.2.
- Evidence: the npm packument (`react-relicense/packument.json`; every
  main-line release's `license` and publish time; prereleases, which the
  check ignores, dropped).
- Independent confirmation: React's own CHANGELOG, "15.6.2 (September
  25, 2017) — Switch from BSD + Patents to MIT license".
- Confidence: EMERGING (a difference OpenPulse observed between two
  declarations). First detection: none recorded (no history of
  OpenPulse's own). Effective date: 2017-09-26 (publish time of 15.6.2).
- Scope: package. Finding: `LICENSE_CHANGE` / REVIEW.
- Reproduction: `openpulse release-license --ecosystem npm --package
  react --version 15.6.1`; offline `test_case_11_react_relicensed_bsd_to_mit_replays`.

## Case 12 — psycopg2 dropped ZPL ✅ VERIFIED (recorded replay)

- What changed: 2.7 declared "LGPL with exceptions or ZPL"; the latest,
  2.9.13, declares "LGPL with exceptions".
- Why it matters: the Zope Public License option is gone; anyone relying
  on it now holds an LGPL licence only.
- Affected: `pkg:pypi/psycopg2`.
- Evidence: the PyPI project document and release 2.7's
  (`psycopg2-license/`). PyPI is read for two releases, so the finding
  says the change is somewhere after 2.7, at the latest in 2.9.13.
- Independent confirmation: psycopg2 commit `8b2450287e` "Removed ZPL
  license (closes: #1087)", 2020-04-28, between 2.8.5 and 2.8.6; PyPI's
  2.8 still declares ZPL and 2.8.6 does not.
- Confidence: EMERGING. First detection: none recorded. Effective date:
  the publish time of 2.9.13 (the latest moment the change can be placed
  from the two releases read).
- Scope: package. Finding: `LICENSE_CHANGE` / REVIEW.
- Reproduction: `openpulse release-license --ecosystem PyPI --package
  psycopg2 --version 2.7`; offline `test_case_12_psycopg2_dropped_zpl_replays`.

## Case 13 — request deprecated ✅ VERIFIED (recorded replay)

- What changed: the release npm installs by default (2.88.2) carries the
  publisher's deprecation: "request has been deprecated, see
  https://github.com/request/request/issues/3142".
- Why it matters: no further fixes; npm warns on every install.
- Affected: `pkg:npm/request`, every version.
- Evidence: `request-deprecated/latest.json` (npm `/request/latest`).
- Independent confirmation: request/request issue #3142, "Request's
  Past, Present and Future" (opened 2019-03-30), the announcement the
  message points to.
- Confidence: CONFIRMED (the publisher's own statement on its package).
  First detection: none recorded. Effective date: unrecorded (the
  registry keeps no date for a deprecation).
- Scope: package. Finding: `DEPRECATION` / REVIEW.
- Reproduction: `openpulse deprecation --ecosystem npm --package request`;
  offline `test_case_13_request_deprecated_replays`.

## Case 14 — uuid 3.4.0 deprecated while the latest is not ✅ VERIFIED (recorded replay)

- What changed: release 3.4.0 carries the publisher's deprecation
  ("uuid@10 and below is no longer supported …"); the latest, 14.0.3,
  does not.
- Why it matters: the flag covers the release you run, not the package;
  the finding is scoped to 3.4.0.
- Affected: `pkg:npm/uuid@3.4.0`.
- Evidence: `uuid-version-deprecated/latest.json` and `3.4.0.json`.
- Independent confirmation: the publisher's message names the supported
  line (uuid@11 and later), and the latest release carries no flag.
- Confidence: CONFIRMED. First detection: none recorded. Effective date:
  unrecorded.
- Scope: one release. Finding: `DEPRECATION` / REVIEW.
- Reproduction: `openpulse deprecation --ecosystem npm --package uuid
  --version 3.4.0`; offline
  `test_case_14_uuid_old_line_deprecated_while_latest_is_not_replays`.

## Case 15 — urllib3 2.0.0 yanked ✅ VERIFIED (recorded replay)

- What changed: every file of 2.0.0 is yanked (PEP 592), with the reason
  "Truncated response bodies when streaming a large compressed body.
  Upgrade to at least 2.0.2 …".
- Why it matters: installers skip it unless pinned exactly; a lockfile
  pinning it keeps the bug.
- Affected: `pkg:pypi/urllib3@2.0.0`.
- Evidence: `urllib3-yanked/project.json` (each release's files with
  their yank flags and reasons).
- Independent confirmation: urllib3's CHANGES, 2.0.2 (2023-05-03), fixes
  `HTTPResponse.stream()` truncating decompressed data.
- Confidence: CONFIRMED. First detection: none recorded. Effective date:
  unrecorded.
- Scope: one release. Finding: `DEPRECATION` / REVIEW.
- Reproduction: `openpulse deprecation --ecosystem PyPI --package urllib3
  --version 2.0.0`; offline `test_case_15_urllib3_2_0_0_yanked_replays`.

## Case 16 — attrdict declares itself inactive ✅ VERIFIED (recorded replay)

- What changed: the latest release (2.0.1) carries "Development Status
  :: 7 - Inactive".
- Why it matters: the publisher says the project is no longer developed.
- Affected: `pkg:pypi/attrdict`.
- Evidence: `attrdict-inactive/project.json`.
- Independent confirmation: the source repository, bcj/AttrDict, is
  archived (last push 2019-02-01).
- Confidence: EMERGING (a classifier describes the release it shipped
  with). First detection: none recorded. Effective date: unrecorded.
- Scope: package. Finding: `DEPRECATION` / REVIEW.
- Reproduction: `openpulse deprecation --ecosystem PyPI --package
  attrdict`; offline `test_case_16_attrdict_declares_itself_inactive_replays`.

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
  **fired live four times** (Cases 6–7 capa and etcd 2026-10-06;
  Cases 8–9 traefik and fbsdk 2026-10-07 — the fbsdk one together
  with `PROJECT_ARCHIVED`, the first combined firing) and
  formalized with golden replays; same-owner renames stay silent
  (offline proofs in `tests/test_analysts.py`).
- Repository history (`diff_repository_observations`, v0.20.0 C2):
  license changes, archives and moves seen between two of
  OpenPulse's own observations. Offline proofs in
  `tests/test_repository_changes.py`; no real change has been
  observed twice yet, so the class ships **experimental** and its
  findings say so. It is verified by the first live firing,
  recorded here with both observations.
- Namespace moves (`split_moves`, `core/observations/sweep.py`):
  cross-namespace appear/disappear pairs become one migration story.
  Offline proofs in `tests/test_correlation.py`; no live pair
  observed yet.

## What closes acceptance

1. ~~Confirm-or-kill the three pruning cases~~ — done 2026-10-03,
   all three killed (Cases 3–5). Replacements delivered 2026-10-06:
   Cases 6–7 (capa, etcd ownership moves) from live repo_meta
   probes, and 2026-10-07: Cases 8–10 (traefik org rename; fbsdk
   archive+move combined; bitnami/spark empty-mainline split) —
   five live-replayed verified cases beyond the structural set,
   acceptance closed. #36 (Hub anonymous pagination cap) still
   blocks full-set probes for large repos.
2. ~~One live firing from the armed detectors (move or
   ownership)~~ — ownership fired live twice (Cases 6–7). The
   cross-namespace `split_moves` detector stays armed, awaiting a
   live pair.
3. Version-aware latest-only rule flipping the Bitnami gap test —
   CLOSED: `parse_tags` is version-aware and the flipped test
   (`test_bitnami_digest_mainline_gap_closed`) plus a no-false-positive
   test on versioned mainlines lock it. Case 2 is now producer-derived.

M2 acceptance met 2026-10-07: five verified live-replayed
non-lifecycle cases (6–10) + the structural Case 2, each with an
offline golden replay. Then: M4 benchmark fed.

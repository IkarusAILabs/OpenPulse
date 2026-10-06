# Lead time case studies — verified, never averaged

Lead time is `effective_date − first_trustworthy_detection`, in whole
days ([core/leadtime.py](../core/leadtime.py)). Every case below
states which dates make its number, where each date came from, and
how to reproduce it. A case that cannot replay is removed, not
argued for — same rule as the M2 discovery ledger.

Two temporal roles are never conflated: an **announcement lead**
(announcement → effective, what the source offered) and a
**detection lead** (OpenPulse first detection → effective, what this
system actually delivered to a customer). Cases carry one or both,
each labelled. No averages: a mean over heterogeneous changes would
be a marketing number, not a measurement.

## Case 1 — Bitnami versioned-catalog split (DISTRIBUTION_CHANGE)

- Project: `bitnami` (namespace `docker.io/bitnami`, all versioned refs).
- Change: versioned images moved to `docker.io/bitnamilegacy`;
  mainline limited to a latest-only community tier.
- Evidence: official Bitnami/Broadcom announcements,
  `github/bitnami-containers#83267`, `github/bitnami-charts#35164`
  (fixture: `data/fixtures/bitnami/event.json`).
- Announcement lead: **43 days** — announced 2025-07-16, effective
  2025-08-28 (both evidence-declared dates).
- Detection lead: **not a forward case** — OpenPulse's structural
  registry confirmation (0 version-like tags in `docker.io/bitnami`,
  919+ in `docker.io/bitnamilegacy`) dates 2026-10-02, after the
  change was already in force. Recorded as such; no forward lead is
  claimed for it.
- Customer impact: any deployment pinning `docker.io/bitnami/<image>:<version>`
  stopped receiving updates the day the split took effect; pipelines
  and Helm values referencing `X.Y.Z-debian-12-rX` tags must move to a
  maintained source. This is the canonical "public intelligence was
  there, but nobody connected it to MY dependencies" case — the class
  of failure OpenPulse exists to close.
- Reproduction: `openpulse check --watchlist <wl with docker.io/bitnami/redis:7.2>
  --event data/fixtures/bitnami/event.json` (AFFECTS_ARTIFACT verdict);
  structural split: `tests/test_golden.py` bitnami scenarios and
  `docs/DISCOVERIES.md` Case 2.

## Case 2 — PostgreSQL 14 EOL, detected 37 days ahead (EOL, UPCOMING)

- Project: `postgresql`, cycle 14.
- Change: cycle 14 reaches end of life; the final minor release ships
  and the version is unsupported after that date.
- Evidence: official versioning policy — a major version is supported
  5 years after release (postgresql.org/support/versioning);
  cycle data live-verified 2026-10-06 from endoflife.date
  (`eol: 2026-11-12`, `latest: 14.24`).
- First trustworthy detection: **2026-10-06** — the change-analyst
  UPCOMING finding fires from the live cycle data
  (`EOL_WARN_DAYS = 180`; 37 days remain).
- Detection lead: **37 days** (2026-10-06 → 2026-11-12).
- Customer impact: a deployment pinned to `postgres:14` /
  `postgresql 14.x` receives its last fixes on 2026-11-12, then
  nothing — a database, not a library: plan the major upgrade (15–18)
  now, within the window the warning leaves.
- Reproduction (pinned in the suite):
  `tests/test_warnings.py::test_case_postgresql_14_lead_time` —
  the live-verified cycle entry runs through the producer pipeline
  (analyze → finding_to_event → check → build_warnings) and must
  yield `days_until_effective == 37`, `severity == MEDIUM` (31-90
  days: one planning cycle), lead time 37 days from a first
  detection recorded the same day. Live probe:
  `curl -s https://endoflife.date/api/postgresql.json | jq '.[] | select(.cycle=="14")'`.

## Case 3 — Redis 8.0 EOL, detected 56 days ahead (EOL, UPCOMING)

- Project: `redis`, cycle 8.0 (standard release).
- Change: cycle 8.0 reaches end of life; security updates and
  critical fixes stop. Redis 8.0 is tri-licensed (RSALv2/SSPLv1/AGPLv3);
  the supported migration targets are 8.2+ (extended releases carry
  5 years of fixes).
- Evidence: official version-management page — "Redis 8.0, Standard,
  EOL December 1, 2026" (redis.io/docs/latest/operate/oss_and_stack/install/version-mgmt);
  cycle data live-verified 2026-10-06 from endoflife.date
  (`eol: 2026-12-01`, `latest: 8.0.6`).
- First trustworthy detection: **2026-10-06** — same producer path
  as Case 2; 56 days remain at detection.
- Detection lead: **56 days** (2026-10-06 → 2026-12-01).
- Customer impact: deployments on `redis:8.0` / Redis 8.0.x stop
  receiving security fixes on 2026-12-01. Standard releases get 6
  months of fixes after the next minor; 8.0's window closes with the
  EOL date, and the 8.0.6 patch stream (last release 2026-02-22)
  has already gone quiet — the EOL warning is the planning signal.
- Reproduction (pinned in the suite):
  `tests/test_warnings.py::test_case_redis_80_lead_time` — the
  live-verified cycle entry runs through the same producer pipeline
  and must yield `days_until_effective == 56`, `severity == MEDIUM`,
  lead time 56 days. Live probe:
  `curl -s https://endoflife.date/api/redis.json | jq '.[] | select(.cycle=="8.0")'`.

## Why these three

The Bitnami case is the canonical distribution change with real
customer impact and an official announcement trail. PostgreSQL 14
and Redis 8.0 are the two other shapes a lead-time claim must
survive: upcoming EOLs that the producer pipeline detects TODAY,
from live official cycle data, with the first-detection date
recorded by the ledger before the deadline arrives. Every date in
all three cases comes from a cited source; every number replays in
the test suite; nothing is estimated, averaged, or marketed.

Verification status: Bitnami — VERIFIED (structural + official
evidence, DISCOVERIES.md Case 2). PostgreSQL 14 and Redis 8.0 —
VERIFIED as detections (producer-derived findings, live official
cycle data); they become *completed* lead-time cases when their
effective dates pass and the recorded first detections hold, which
the ledger will attest without rewriting history.

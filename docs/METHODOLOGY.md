# Methodology — how OpenPulse knows what it claims (schema v0.7.0)

## Sources

Upstream: GitHub releases + repo metadata, official blogs/changelogs.
Security: OSV.dev, NVD, MITRE CVE, CISA KEV, GitHub Advisories,
Exploit-DB (link only). Lifecycle: endoflife.date. Ecosystems: Maven,
npm, PyPI, Docker/OCI (initial).

## Source authority tiers

Sources are not equal. Tiers, strongest first:

- **official** — the vendor/project itself (announcement, changelog,
  advisory, repo). Alone sufficient for CONFIRMED. Derived, never taken
  on trust: a source counts as official only when its URL is https and
  names a location on the project's allowlist in
  `data/official_domains.yaml` (a host and its subdomains, or a host
  with a path, such as `github.com/django`). Any other source claiming
  official is read as secondary, and the gate names the reason.
- **primary** — lifecycle databases (endoflife.date), registries
  serving protocol truth (tag lists, digests). Strong but narrow:
  endoflife.date proves dates, never distribution intent.
- **secondary** — reputable press, mirrors, aggregators. Corroborates;
  never confirms alone.
- **tertiary** — rumors, single discussions. Context at most.

endoflife.date is a primary lifecycle source — one input among many,
not the definition of OpenPulse. A lifecycle database answers "when
does software reach EOL"; OpenPulse answers "what is changing upstream,
and does it affect what I depend on".

## Identity hierarchy

`docker.io/redis` ≠ `docker.io/bitnami/redis`, always. Resolution
order: curated overrides → catalog aliases → Bitnami-namespace rule →
normalized fallback (`core/entities/resolve.py`). Typed identity refs
(`core/entities/identity.py`: project, package, artifact, repository,
registry_artifact, purl, cpe) record *why* two names were treated as
the same thing. Same identity evidence = same thing; same name is
never enough.

Every resolution carries an identity status: VERIFIED (curated
mappings and self-identity), REVIEW_REQUIRED (heuristic rules or
flagged catalog entries, e.g. broad aliases), UNVERIFIED
(explicitly distrusted). Catalog entries that need it declare an
`identity:` block (status, source, reviewed_at, maintainer,
confidence, note) — never mechanically, only where ambiguity lives
(aliases, forks, renames, distributions, namespace collisions).
Affected verdicts that rely on REVIEW_REQUIRED/UNVERIFIED mappings
are capped at EMERGING confidence: unverified identity can never
silently elevate impact. Exact artifact equality needs no mapping
and is never capped.

## Vulnerability correlation methodology

NVD `keywordSearch` is **discovery**, never applicability. Findings
carry `relationship` + `match_method` + `identity_evidence`:

- `osv_package` — OSV query scope (package/ecosystem identity).
- `osv_package+version_range` / `cpe_version_range` — plus an evaluated
  version range → `AFFECTS_VERSION`.
- `cpe_vendor_product` — normalized exact product equality only.
  Token overlap (`spring` vs `spring-shell`) is NOT identity.
- `keyword_only` — capped at `REVIEW`, never `AFFECTS_VERSION/_ARTIFACT`.
- KEV `exact`/`strong` sets `in_kev`; `weak` never does. KEV +
  uncertain applicability → `REVIEW`, never `CRITICAL`.

## Version applicability

`core/versions.py` evaluates OSV events
(introduced/fixed/last_affected) and NVD CPE range attributes
(versionStart/EndIncluding/Excluding) plus exact versions. Result is
`True`/`False`/`None` — `None` (unknown version, exotic scheme) keeps
the ceiling at `AFFECTS_PACKAGE` or `RELATED`. Uncertainty never
strengthens a conclusion.

An OSV range is a **union of intervals**: events are walked in
version order, `introduced` opens an interval and `fixed` (exclusive)
or `last_affected` (inclusive) closes it, so `introduced 1.0, fixed
1.2, introduced 2.0, fixed 2.3` covers `[1.0, 1.2)` and `[2.0, 2.3)`.
Only `SEMVER` and `ECOSYSTEM` ranges are evaluated: `GIT` ranges need
commit-graph reasoning and are `None`, as is any unknown range type
and any version at or past a `limit`. An advisory is cleared for a
version only when **every** affected entry decides `False`; one
undetermined entry withholds the clearance. Withdrawn advisories
assert nothing. Versions carrying an epoch (`1:2.3`, `1!2.3`) are not
comparable: an epoch outranks every release number, so it is never
read as one more dotted segment. The only comparable form is a dotted
numeric core with at most one known prerelease marker (`dev`, `a`,
`b`, `rc`, `pre` and their long forms) and an optional number:
`2.0.0-rc.1`, `1.0b2`. The number orders within a marker (`rc1 <
rc2`). A bare numeric or build suffix (`1.0.0-1`, `2.4.1-1`,
`1.0.0+5`) is not comparable, because ecosystems disagree on it: SemVer
reads `1.0.0-1` as a prerelease below `1.0.0`, Debian as a revision
above it. Accepting a form is not enough: it must be ordered as the
range's scheme orders it. So each OSV range is compared under its own
scheme. `SEMVER` ranges use SemVer 2.0 precedence, where prerelease
identifiers order lexically (`1.0.0-dev` above `1.0.0-beta`).
`ECOSYSTEM` ranges use the advisory's ecosystem: PyPI the generic
grammar above, npm/Go/crates.io SemVer, and anything else plain dotted
numbers only, with padding-only equality (`1.0` vs `1.0.0`)
undetermined.

Event version scopes name **release lines** (endoflife.date cycles such
as `4.2`, `13`, `18`), while dependencies pin releases. A line covers
every version whose leading segments equal it (`versions.in_release_line`):
`django==4.2.11` and `postgres:13.5-alpine` are inside cycles `4.2` and
`13`; `4.20.1` is not inside `4.2`. A version that cannot be compared is
`RELATED` (not established), never `NOT_AFFECTED`.

## Evidence, claims, independence

Every claim names supporting evidence (`Claim.evidence_refs`); an
official-but-unrelated source never satisfies a claim. Corroboration
counts independent families, folding `derived_from` chains. A family is
also derived from each source's URL: its registrable domain, or the
host plus owner on shared hosts such as `github.com/bitnami`. Two
pages on one site are one source, whatever families their producer
declares; a declared family can merge sources but never split them.
The monthly report counts families, not labels: NVD + OSV share the
vuln-data family, and OpenPulse's own correlation never counts as an
independent source (`source_family_count`,
`corroborating_family_count`). Contradicting evidence stays visible
(`⚠️ CONTRADICTS`); unresolved conflict blocks `ACTION`/`CRITICAL`.
High-impact conclusions require official/primary authority or hashed
provenance.

## Confidence

- CONFIRMED: official announcement (vendor blog, repo release, EOL page).
- CORROBORATED: 2+ independent sources.
- EMERGING: single credible secondary.
- UNVERIFIED: weak/rumor — never triggers ACTION alone.

Match strength and evidence strength are separate axes
(`core/risk/check.py`): an exact artifact match answers *what
matches*; the event's evidence answers *how trustworthy the claim
is*. Final verdict confidence is the conservative minimum of the
two — a precise match on a weak claim stays weak. Official evidence
proves the statement *from that source*; it does not automatically
prove the user's dependency is affected. Impact coupling is enforced
by the gate.

Finding confidence follows the same ladder at analyst level
(`AFFECTS_*` from ≥2 sources → CORROBORATED, else EMERGING;
`RELATED` → UNVERIFIED unless KEV-confirmed-exploited → EMERGING).
Weakly established findings (EMERGING/UNVERIFIED) cap at REVIEW:
weak evidence never enters an ACTION-level channel (`check --strict`
fires only on ACTION/CRITICAL causes).

## Popularity

GitHub stars inform reach, never risk: ≥50k very high, ≥10k high,
≥1k medium, else low, unknown → unranked. The facet stays
informational (always 🟢) — popularity never promotes an impact.

## Impact

INFORMATIONAL < WATCH < REVIEW < ACTION < CRITICAL. Findings also
carry severity (CVSS band), urgency, and recommended_action. No opaque
single score — facets stay separate.

## Intelligence semantics

An analyst `impact` is a proposal, not a conclusion. Reports place
findings through impact eligibility (`core/risk/impact.py`):

- `PROJECT_SIGNAL` — something exists (unscoped, unconfirmed).
- `PROJECT_CHANGE` — scoped ecosystem change (what changed, with
  versions/artifacts/dates). Never impact on a user's environment.
- `AFFECTS_DEPENDENCY` — a linked inventory entry matches.
- `ACTION_REQUIRED` — affected + effective + strong confidence. Only
  here does EOL (or any change) become action for *your* software.

Eligibility ladder for public reports: scoped effective EOL and
distribution model changes may be ACTION-framed (with disclaimer);
archived upstreams, vanished repositories/tags, and support ends are
REVIEW at most; upcoming EOL and routine registry churn are WATCH.
EOL detected never equals ACTION_REQUIRED — that needs inventory.

## Lead time

Upcoming changes carry their warning in days: effective −
first_detected_at, per finding (`core/leadtime.py`). First detection
is the first trustworthy OpenPulse detection of the change —
re-observations never stand in, and an unknown first detection means
no lead-time claim (never estimated). Unknown or already-past
effective dates print nothing — silence, not a number. Temporal
roles are never conflated: published/announcement (source claims),
first detection (our discovery), last observation (confirmation),
effective (applies). Lead times are never averaged, ranked, or
marketed: the metric stays instrumented but unclaimed until
independently measured incidents exist.

### Durable detection ledger

Sweep findings derive first detection from observation history, but
lifecycle and security findings had no persisted history — warning
windows died with the process. Watchlist runs (`openpulse check`)
now record durable first detections under `.openpulse/detections/`
(`core/detections/ledger.py`): one JSON entry per fact, keyed by
stable identity — (project, class, subject, scope) where lifecycle
facts use (project, `EOL`/`EOS`/`DEPRECATION`, sorted cycle versions)
and security facts use (project, CVE id). The store reuses the
observation-history trust model: atomic writes (temp + rename),
per-project OS advisory locks, and (unkeyed) content hashes over
identity and the sighting dates, verified on every read so an
edited entry degrades to unknown instead of being trusted. No hash
chain: an entry is a standalone earliest-witness record, so its own
content hash meets the integrity need, and absence — deleted or
never written — is
indistinguishable from never-detected, which is exactly the
"unknown means unknown" rule. An entry's first sighting is fixed
when it is created: a later stamp never overwrites it, and an earlier
stamp is not taken, because the ledger never witnessed it. Every
stamp must also lie within five minutes of UTC wall-clock time when
it is recorded, so a caller cannot backdate a detection to inflate a
lead time; a stamp outside that bound is refused and nothing is
written (clock trust, finding L7).
Deleting the ledger degrades to per-run behavior — no claims, never
invented dates.

## Research window and freshness

OpenPulse researches the last 12 months (`core/freshness.py`).
Freshness derives from the effective date, never the observation
date: a 2024 EOL re-observed today is background knowledge
(`BACKGROUND`), not news. Findings effective over a year ago sink in
rankings and carry the background label, but stay narrated with full
evidence — freshness demotes and labels, never deletes. Unknown
effective dates are `UNKNOWN` freshness, never assumed old.
Reports segment background explicitly so monthly briefings cannot
present last year's changes as this month's.

## Date semantics

Five temporal roles, never substituted for one another
(`core/freshness.py:_finding_dates`, `core/leadtime.py`):

- Announced — when the upstream project publicly communicated the
  change. Used only with provenance: `official` (NVD/CVE
  publication, OSV publication, KEV catalog addition, GitHub release
  publication) or `unknown`. Inferred dates are marked inferred with
  their provenance retained; without a trustworthy date the report
  shows "Announcement: Unknown" — dates are never fabricated from
  file times, commit dates, scan dates, or report generation dates.
- Effective — when the change takes (or took) effect.
- First detected — when OpenPulse first observed sufficient
  evidence. Re-observations never stand in.
- Last verified — when OpenPulse most recently confirmed the
  evidence (`last_observed_at`, else `observed_at`).
- Reported — the reporting period that included the finding.

## Freshness policy (`core/freshness.py`)

Event-temporal classification is deterministic date arithmetic —
no LLM, no heuristics beyond the documented rules:

- `UPCOMING` — effective date in the future. Announcement age never
  hides a future consequence.
- `NEW` — announced within the recency window and not yet past effect.
- `RECENTLY_UPDATED` — old announcement with a recent first
  detection or verification: the update is treated as new intelligence.
- `ACTIVE` — ongoing dateless conditions, recently verified.
- `EXPIRED` — effective date past with no recent update; moves to
  the Historical appendix, never deleted.
- `UNKNOWN_DATE` — no dates at all; narrates only when
  REVIEW/ACTION-eligible.

The recency window defaults to 90 days (`OPENPULSE_REPORT_FRESHNESS_DAYS`
overrides): three monthly reporting cycles, matching typical OSS
disclosure-to-impact spans. Effective-date rules always take
precedence over the window; a 365-day research window backstops
unknown-announcement cases.

## Public/internal/debug information boundary

Monthly Markdown reports are website-facing. Every report field is
classified:

| Class | Content | Examples |
|---|---|---|
| PUBLIC | Evidence, sources, dates with provenance, scope, assessment vocabulary, confidence | finding titles, summaries, references, observation/content/chain hashes, `Announced/Effective/First detected/Last verified/Status` lines |
| INTERNAL | Trust machinery legible only with codebase context | analyst names, impact proposals, parser versions, match methods, `_refs`, evidence-link internals, lifecycle states, store paths |
| DEBUG | Diagnostics, never rendered | tracebacks, raw payloads, lock files, credentials (never collected) |

`tests/test_public_report.py` enforces the boundary by token scan.
Assessment and eligibility labels (`PROJECT_CHANGE`, `ACTION`,
`REVIEW`, `WATCH`) are PUBLIC domain vocabulary, defined in the
report Methodology section — not cryptic codes.

## Registry observations

What the registry exposed at time T: repository state, tag→digest
map, content hash (`core/observations/`). Tags are mutable pointers,
never identities. First sighting is a baseline; changes derive only
from observation diffs. History lives in git-ignored local JSON —
portable, no server.

Observations are corruption-detecting: every persisted record carries a
chain hash `H[n] = SHA256(canonical_fields(n) + H[n-1])` over
observation id, source, entity, timestamps, content hash, parser
version, and predecessor link; the first record links to an explicit
`genesis` marker. Histories verify VALID / BROKEN / UNKNOWN —
a broken chain is never diffed against (no findings, no append;
the corrupt predecessor stays on disk as evidence). Sealed records
are frozen; concurrent writers serialize on a per-repository OS advisory lock
(`core/filelock.py`, released by the OS if the holder dies)
with atomic writes, and history is ordered by chain links, never
filenames. Threat model: the chain defeats silent corruption,
partial edits, and fork anomalies. Rollback and downgrade are refused,
never adopted silently: a tip pointer that disagrees with the data
(ROLLBACK), a chained history whose tip is missing
(ROLLBACK_SUSPECTED), and an unchained record after chained ones or an
unkeyed record after keyed ones (DOWNGRADE) all stop diffing and
appending. Only `openpulse observe --rebaseline --reason "..."` accepts
such a history: a rollback is accepted at its current tip, anything
else is moved to a `quarantine-*` folder and restarted, the reason is
logged in `rebaselines.json` (MACed under the history key), and no
change claims cross the re-baseline. A full wipe of the repository's
folder, tip included, still looks like a first run; detecting that
needs an anchor outside the store (B5). It does not resist an adversary who
recomputes the whole suffix, unless a history key is set.

With a history key (`OPENPULSE_HISTORY_KEY` or `--history-key-file`,
made by `openpulse history-key generate`), every new observation
record and detection-ledger entry also carries an HMAC-SHA256 under
that key. The observation MAC covers the chain hash and
`first_detected_at`; the ledger MAC covers the entry's content hash.
Histories then verify VALID_KEYED (every MAC verifies), VALID_UNKEYED
(hashes verify, but some record has no MAC), BROKEN or UNKNOWN (a MAC
whose key was not supplied). An edit whose hashes were recomputed
without the key is BROKEN under the key. A keyed history is never
appended to without its key, and records written before the key stay
unkeyed rather than being MACed after the fact. The key never lives in
`.openpulse/`. Rotation keeps retired keys verify-only
(`OPENPULSE_HISTORY_KEYS_PREVIOUS`, `--history-previous-keys-file`): the
first observation written under a new key is a handover record, MACed
by the retired key too, and a ledger rotation log (`rotations.json`,
MACed by both keys) records when each key was retired. After a
handover, a record under the retired key, a key change without a
handover, or a ledger sighting under the retired key dated after its
rotation is BROKEN, so a leaked retired key cannot extend history.

History written before the key is adopted, never re-MACed as if it had
always been keyed. In an observation chain, unkeyed records followed
only by keyed ones verify VALID_KEYED: the first keyed record's chain
hash pins them, and its `observed_at` is the adoption time. A ledger
entry first written without a key gets `adopted_at`, under the MAC, the
next time a keyed run writes it. Nothing before adoption is proved, so
a lead time counts from the later of the first detection and the
adoption: a lower bound, never an overstatement. Lead times in
`digest`, `warnings`, `report` and `check` come only from VALID_KEYED
ledger entries; without a history key they are not published, and the
output says so. External anchoring is still planned for v0.9.0
(`docs/NEXT_PHASES.md`, `docs/KEYED_INTEGRITY.md`); until all of them
ship, the history is not claimed to be tamper-evident.

Every registry-derived finding retains first-class observation
evidence (`observation_evidence`: observation ids, hashes, chain
links, timestamps, the exact diff fact). The public Hub URL is
reader context; the observation identity is the machine evidence.
Diffs are candidate changes with explicit evidence strength
(observed fact: moderate; namespace heuristic: weak) — weak
evidence caps report placement at REVIEW and can never become
ACTION_REQUIRED, however precise the dependency match.

## Image inventories and the tag-vs-digest pinning policy

Container image inventories (`openpulse check --images`, one ref per
line or a simple YAML list) are a deployment-side input: the refs a
team actually runs. Entries map through the same identity semantics
as watchlist refs (`split_image_ref`/`tag_of` in `core/risk/match.py`)
and produce identical verdicts to the same refs via `--watchlist`
— there is no second matching engine.

Identity is digest-aware while inventories name tags, so pinning
forms carry an explicit policy (`tag_vs_digest_policy`):

- **Pinned digests match exactly.** Two refs that pin the same
  digest are the same immutable bytes — AFFECTS_ARTIFACT, the only
  form of exact artifact identity besides tag equality.
- **Different digests of one repository are RELATED, not a
  clearance.** Different bytes, but OCI object levels are not
  recorded: one digest may be an image index and the other one of
  its platform manifests -- the same image. Until levels are
  resolved, digest inequality never clears. Every artifact the event
  names is compared; any equal digest is AFFECTS_ARTIFACT. (A digest
  of a *different repository* is still decisively outside.)
- **A digest on one side and a tag on the other is RELATED, never
  AFFECTS_ARTIFACT and never NOT_AFFECTED.** The refs agree on the
  repository, but a tag can move onto (or away from) the pinned
  digest at any time; the uncertainty is reported, not resolved.
- **Tags match by current registry-scope semantics** (`match.py`),
  unchanged; comparing tags says nothing about bytes.

A moving tag never reports digest-level certainty — enforced by
tests (`tests/test_image_inventory.py`), not just documented.

## Repository inspection coverage (schema 0.5.0, contract v1.1)

A GitHub repository input (`--github-repo`) is read at one pinned
commit; every dependency file is fetched by the blob SHA its tree
declares, and the returned bytes must hash back to that SHA. Each
inspection states `inspection_coverage`: COMPLETE, PARTIAL (with
reasons - a skipped, oversized or unreadable file) or FAILED. Absence
of dependency files under PARTIAL or FAILED coverage is never "no
dependencies": it is an inspection limit, carried on the verdict, in
`check`/`attest` output and in the evidence contract. The same rule
holds inside a file: a manifest that declares dependencies but yields
none must refuse or record skips, never return a silent empty set
(the namespaced pom.xml regression, #112).

## Uncertainty handling

Unknown version → no version claim. Unknown identity → RELATED, not
AFFECTS. Unknown applicability + KEV → REVIEW, not CRITICAL.
Conflicting evidence → visible + blocking for strong actions.

## Limitations — what OpenPulse does not know

- No auto-remediation; not a SAST/SCA replacement.
- English sources first; no private-registry visibility.
- Version comparison is best-effort numeric (exotic schemes → unknown).
- CPE data depends on NVD configuration quality.
- Popularity informs reach, never risk (stars bands, always 🟢).
- `latest` moves constantly — pin digests in production.
- License/support-model changes are curated events for now (Bitnami,
  iText fixtures): no automated license collector exists yet, so the
  pipeline cannot *discover* them — only validate, gate, and match
  them once recorded with evidence.

## Core distinctions (design principles)

- RELATED ≠ AFFECTED — association is not impact.
- AFFECTS_PROJECT ≠ AFFECTS_VERSION — project ties are contextual.
- UNKNOWN ≠ NOT_AFFECTED — unevaluated is not cleared.
- OBSERVATION ≠ CLAIM ≠ EVENT — facts, assertions, and gated
  intelligence are separate layers.
- Detection (what was observed) ≠ assessment (what evidence
  establishes) ≠ recommendation (what to investigate). Recommendations
  never feed back into impact calculations.
- SOURCE SIGNAL ≠ CHANGE ≠ AFFECTED DEPENDENCY ≠ ACTIONABLE
  INTELLIGENCE. A lifecycle date is a signal; a scoped, dated change
  is intelligence; impact requires a dependency.
- Public intelligence (what changed in OSS) ≠ dependency-specific intelligence
  (does it affect my software). Public reports never assert the second.
- MATCH STRENGTH ≠ EVIDENCE STRENGTH — precise identity answers
  "what matches", never "how trustworthy is the claim".
- HEURISTIC DETECTION ≠ AUTHORITATIVE EVIDENCE — discovery leads
  stay capped until confirmed.
- OBSERVED DATE ≠ FIRST DETECTED DATE — re-observation is
  confirmation, not discovery.

## Webhook security boundary (`core/notify.py`)

Digest webhooks POST to operator-supplied URLs, but OpenPulse runs
automated — so delivery enforces an SSRF policy: https by default
(http needs `--webhook-allow-http` opt-in), no credentials in URLs,
every resolved IP checked (loopback, link-local incl. the cloud
metadata range, RFC1918/ULA, CGNAT, multicast, reserved, and named
metadata endpoints all rejected — one blocked address refuses the
whole delivery), redirects never followed, short timeout, bounded
response body, failures never log secrets: delivery errors report the
HTTP status and the scheme + host only, because for Slack/Teams/Discord
incoming webhooks the URL path is the credential, and shared redaction
strips webhook paths, `Bearer` credentials and GitHub/Slack token
shapes. Prefer `OPENPULSE_WEBHOOK_URL` over `--webhook` so the URL
stays out of the process list. Known limitation: DNS is
resolved before connecting, so a hostile resolver could race the
check; short timeouts and no-redirects bound the blast radius.

## Alert digest — the first M6 early-warning surface (`core/digest.py`)

`openpulse digest` joins three things that already exist — the
dependency inputs the user just checked, the events the check
ran against, and the durable first-detection ledger `openpulse
check` records into — and renders one ranked briefing: what is
changing in MY software, and by when. It computes nothing new and
stores nothing: it is a read-only projection over the same stores,
so there is no second source of truth to drift.

Rules the digest inherits rather than reinvents:

- **Dependency evidence is required.** An entry exists only for a
  dependency the caller declared with an impact-asserting verdict.
  Public intelligence never implies user impact.
- **Deadlines come from event evidence only.** `days_until_effective`
  is the evidence-declared effective date minus today; an affected
  dependency whose event declares no effective date has no deadline
  to count down to and stays in `check` output, out of the digest.
  The derivation is `core.leadtime.event_effective_day` — the same
  one the evidence contract's dates block pins — not a re-derivation.
- **Lead time is never estimated.** It comes from the ledger's
  `first_seen` for the exact fact (project, class, subject, scope),
  read through the same `durable_fact_from_cause` identity the
  writer uses, so a fact can never be recorded under one identity
  and surfaced under another. No record → no lead-time claim. A
  missing or unreadable entry renders as that statement, never as
  an exception: the digest is a briefing a cron schedule depends on
  rendering.
- **The window is symmetric around today.** Default 90 days each
  way: upcoming deadlines count down, and changes that just became
  effective (days_until_effective negative, rendered with an
  OVERDUE marker) lead the briefing — a weekly digest must not
  drop a change the day it crosses zero. History older than the
  lookback is the monthly report's to narrate.
- **Security findings are excluded on purpose.** They carry CVE
  ids, not event deadlines: a CVE fix is available the moment it
  is published, so there is nothing to count down to. They keep
  their severity and their home in `check` output.
- **Ranking is deterministic and explained.** Soonest effective
  date first, then dependency, then event id — no mystery score,
  no unexplained ordering.

The rendered briefing is two urgency bands (Act this cycle /
Watch), one headline plus an evidence line per entry, and a clean
“nothing upcoming or newly-effective” message for an empty window — which makes
no claim about dependencies outside the window. `--output json`
emits the same entries as structured documents for machine
consumption.

## Verdict decision matrix (`core/risk/check.py`)

AFFECTS_ARTIFACT > AFFECTS_VERSION > AFFECTS_PACKAGE >
NOT_AFFECTED > RELATED > AFFECTS_PROJECT > UNKNOWN.
`affected` is True only for ARTIFACT/VERSION/PACKAGE. Within one
event, an evaluated negative beats RELATED/UNKNOWN. Across events, a
clearance never outranks an unresolved association: while any cause
is RELATED or AFFECTS_PROJECT, the headline is that cause, not
NOT_AFFECTED (`winning_cause`). UNKNOWN causes ("matches nothing in
this event") do not block a clearance. Every cause stays in
`verdicts`.

**When a negative is admissible.** NOT_AFFECTED requires (1) a
scope the producer *declares* complete (`Scope.exhaustive: true`).
Completeness is opt-in: unspecified means partial, and outside a
partial scope is RELATED. Analysts declare it only where the scope
is the event itself (one release line reaching EOL/EOS, one
repository's distribution or registry change); curated events
declare it explicitly, and a catalogue-wide change is stated with
namespace elements (`docker.io/bitnami/*`), not example images. Each
artifact element has a role. A plain namespace is an *envelope*: it
bounds the affected set, so membership is only RELATED ("possibly in
scope") while exclusion from it is decisive. Every other element is
*exact*, and membership is a positive. Tag predicates make exact
namespace elements expressible: `:<version>` covers version-like tags
(not `latest`) and `:*` every tag, so the Bitnami move is
`docker.io/bitnami/*:<version>` (exact) plus `docker.io/bitnami/*`
(envelope). A named artifact's literal tag establishes that tag only.
Nothing verifies a declaration, but every declaration must record
its basis (`Scope.basis`: definitional, announced, corroborated,
verified); `exhaustive` without a basis never clears. Withdrawn and
superseded events are not evaluated, and an event whose own evidence
contradicts it can associate but never clear. An optional freshness
bound (`as_of`, `max_evidence_age`) turns negatives from events with
older evidence into RELATED. (2) Every scope element evaluated
and decisively excluded, with no early return on the first element.
(3) An identity exclusion ("this ref is another project") resting on
a VERIFIED resolution. A heuristic mapping such as the generic
Bitnami namespace rule is RELATED, never an exclusion, and so is any
unmapped ref that resolves only to itself, whatever its name
(`github.com/etcd-io/etcd` against etcd, or a mirror called
`zzz/kvstore`): its identity is unresolved, not another project. Only
a curated mapping to a different project gives "no association" or an
identity exclusion; the OpenTofu fork, for example, is curated as its
own project so terraform events exclude it. Registry hosts are
canonical before any comparison: `index.docker.io` and
`registry-1.docker.io` are `docker.io`. The match implies a confidence *ceiling*
(ARTIFACT → CONFIRMED, VERSION/NOT_AFFECTED → CORROBORATED, PACKAGE →
EMERGING, project/related → EMERGING/UNVERIFIED, unknown →
UNVERIFIED); the verdict takes the minimum of that ceiling and the
evidence behind the event. NOT_AFFECTED carries the explicit
NOT_AFFECTED assessment (informational/cleared) — a negative is never
combinable with an AFFECTS_* assessment.

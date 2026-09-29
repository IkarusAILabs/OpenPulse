# Analysts — Phase 2 (pure functions, deterministic, no network)

Four analysts, kept separate on purpose. Each consumes raw collector
dicts or findings and returns plain data. Only the gate
(`core/evidence/policy.py`) can promote a proposal to an OSSEvent.

## Change Analyst (`analyzers/change_analyst.py`)

Rules today:

- endoflife.date cycle with EOL date in the past (or `eol: true`) →
  `EOL` / `ACTION`. Within 180 days → `EOL` / `REVIEW`.
- endoflife.date active-support date in the past → `EOS` / `REVIEW`.
- Registry probes showing Bitnami mainline latest-only + legacy holding
  versioned tags → `DISTRIBUTION_CHANGE` / `ACTION`.
- Any repo serving latest-only tags → `DISTRIBUTION_CHANGE` / `WATCH`.
- Missing repo → `REGISTRY_CHANGE` / `REVIEW`.
- Archived GitHub repo (via `fetch_repo_meta`) → `PROJECT_ARCHIVED` / `ACTION`.
- Observation diffs (`analyze_diffs`): `tag_disappeared` → `REVIEW`,
  `tag_appeared`/`tag_digest_changed`/`latest_moved` → `WATCH`,
  `repo_missing` → `ACTION`, `repo_restored` → `INFORMATIONAL`.

Registry findings label `detection_method`: `registry_observation`
for direct probe/diff facts, `namespace_heuristic` for the
legacy-namespace pattern rule (discovery aid, never authoritative
evidence). `official_distribution_announcement` is reserved for
curated official findings.

## Security Analyst (`analyzers/security_analyst.py`)

Merges OSV + NVD + CVE + KEV entries by CVE ID: source list, max CVSS,
KEV flag, reference union — plus `relationship`, `match_method`,
`identity_evidence`, severity, urgency, and recommended_action:

- `AFFECTS_VERSION` — version evaluated inside a range (OSV events or
  NVD CPE range attributes) via `core/versions.py`.
- `AFFECTS_PACKAGE` — identity evidence exists (OSV query scope,
  normalized-exact CPE/CNA product match) but version unproven.
- `RELATED` — the CVE exists but nothing ties it to this project
  (keyword-only NVD hits land here and cap at `REVIEW`).
- `UNKNOWN` — no score and no identity signal.

CPE matching is normalized-exact only: token overlap (`spring` vs
`spring-shell`) is never identity. Impact: KEV + AFFECTS →
`CRITICAL`; KEV alone → `REVIEW`; AFFECTS_VERSION ≥ 7 / AFFECTS_PACKAGE
≥ 9 → `ACTION`. Weak KEV matches never set `in_kev`. Findings name
their match method (`osv_package[+version_range]`, `cpe_version_range`,
`cpe_vendor_product`, `keyword_only`); `keyword_only` never yields
`AFFECTS_VERSION`/`AFFECTS_ARTIFACT`.

Findings also carry `confidence` (CORROBORATED for ≥2 sources, else
EMERGING for AFFECTS_*, UNVERIFIED for RELATED/UNKNOWN) and cap at
REVIEW on weak evidence. `check --strict` fires only on affected
verdicts carried by ACTION/CRITICAL causes.

## Evidence Analyst (`analyzers/evidence_analyst.py`)

`assess_confidence`: official source → `CONFIRMED`; ≥2 independent
sources → `CORROBORATED`; single secondary → `EMERGING`; else
`UNVERIFIED`. `assemble_event` builds the OSSEvent (claims included)
and returns `(event, gate_violations)` — callers must handle
violations. Claims (`core/claims.py`) name supporting source names;
contradictions surface as `⚠️ CONTRADICTS` and unresolved conflict
blocks strong actions.

## OSS Pulse (`core/pulse.py`)

`compute_pulse` maps findings + events to 7 facets (activity, security,
lifecycle, support, licence, distribution, popularity). Worst impact
wins per facet; the strongest title is kept as the reason, so every
dot traces to a finding. Activity derives from repo metadata + release
recency (archived → action, >365d stale → review); popularity uses
documented stars bands (reach only, never risk). Rendered by
`openpulse pulse --project <slug> [--raw-bundle file]`.

## Report Analyst (`analyzers/report_analyst.py`)

`render_event_md`, `render_finding_md`, `render_digest`. Every claim
traces to an evidence URL or named collector output.

## Monthly report (`reports/generate.py`)

`collect_project` turns one raw bundle into pulse + findings;
`build_report` ranks items into action-worthy / watch / informational
with named evidence per item. Supporting source URLs (endoflife links,
release/advisory URLs) print beneath each item, deduplicated; recency
(`--since`) and relationship (`--include-related`) filters keep the
monthly narrative honest. `openpulse report --month YYYY-MM`
runs the catalog live or from `--raw-bundle-dir` offline bundles.

## Distribution discovery (`core/observations/sweep.py`)

`sweep_targets` lists every probeable catalog image (registry/namespace/
repo triples only — bare namespaces are skipped, never guessed).
`sweep_catalog` probes (injected function, offline-testable), persists
sealed observations, diffs against history, and emits distribution
findings. First sightings are baselines. `openpulse sweep` wires the
live Docker Hub probe with `--projects` filter and `--out` findings.

## Golden scenarios (`tests/test_golden.py`)

Bitnami, iText, minio-archived, Django EOL versions — each asserting
the five product questions. New golden cases go here, not scattered
across suites.

## Try it

```bash
openpulse analyze --project redis
openpulse analyze --project bitnami
openpulse demo-bitnami
openpulse check --watchlist data/fixtures/watchlist_sample.yaml --event data/fixtures/bitnami/event.json
openpulse sweep --projects bitnami,redis
```

## Verdicts (`core/risk/check.py`)

`check_dependency` keeps event-based and correlation causes separate
(`upstream_change` vs `security_vulnerability`) and combines them with
the matrix in METHODOLOGY. AFFECTS_PROJECT never means affected;
NOT_AFFECTED beats RELATED/UNKNOWN; findings and recommendations stay
in their lanes (detection ≠ assessment ≠ recommendation).

# Roadmap — strategic sequence (reset 2026-09-27, see `docs/STRATEGIC_RESET.md`)

Status: schema 0.4.0, 143 tests, catalog at 100 (15 probeable
images), `openpulse sweep` live, golden suite green (Bitnami, iText,
minio, Django EOL). Positioning: Upstream Change Intelligence +
Dependency Impact Intelligence — explicitly not an EOL tracker,
vulnerability scanner, or SCA.

## Built to date (condensed history)

Schema 0.4.0 (taxonomy, confidence, evidence, claims, scope);
7 collectors (github, osv, nvd, cve, kev, endoflife.date, registries);
4 analysts + veto gate; entity resolution + catalog 100; version
applicability; KEV strength; observations + diffs; verdicts with
NOT_AFFECTED; Pulse facets; monthly reports; watchlist `check`;
trust hardening (provenance, independence, redacted errors, CLI
bounds, SHA-pinned CI, lockfile). Detail: git history +
`docs/ARCHITECTURE_REVIEW.md`.

## Phase 0 — Strategic reset [DONE]

Product thesis, positioning, competitive boundary, canonical schema,
event taxonomy, evidence model, source authority model, this roadmap.
Deliverable: `docs/STRATEGIC_RESET.md`.

## Phase 1 — Intelligence foundation [IN PROGRESS]

Raw Signal model, Evidence model, entity resolution ✅, event
correlation (lifecycle story aggregation — this slice), provenance ✅,
confidence ✅ (match strength vs evidence strength split),
lead time ✅ (`core/leadtime.py` — effective minus first detection,
never averaged or marketed), identity trust ✅ (VERIFIED /
REVIEW_REQUIRED / UNVERIFIED), observation integrity ✅
(hash-chained, tamper-evident, concurrency-safe), deduplication
(per-project stories ✅; cross-project next). Acceptance: September
re-render shows coherent stories, fewer rows, same versions;
ruff/pytest green.

## Phase 2 — Upstream Change Intelligence [STARTED]

Prioritise: GitHub releases, repo changes, archival ✅ (exists),
announcements, docs, package registries, Docker/OCI ✅ (exists +
`sweep`), advisories, distribution changes. `openpulse sweep`
(`core/observations/sweep.py`, injectable probes, offline tests)
is the first standing non-lifecycle discovery beyond curated
fixtures; `tests/test_golden.py` locks the golden scenarios.
`report --with-sweep` carries live distribution findings into the
monthly edition with evidence links. Acceptance: a non-lifecycle
story the pipeline discovers (not curates).

## Phase 3 — Golden scenarios [MOSTLY DONE]

Bitnami ✅, iText ✅, minio ✅, Django EOL ✅ end to end, locked in
`tests/test_golden.py` against the five product questions. Still to
formalise: cert-manager, Redis, PostgreSQL, Kafka, Grafana,
Terraform, Kubernetes, one AI/ML project.
Criterion: each proves something a lifecycle database cannot.

## Phase 4 — Public intelligence [PARTIAL]

Pulse ✅, OpenPulse 100 ✅, monthly intelligence ✅, scheduled
watching ✅. Missing: event history store, project pages, trends.

## Phase 5 — Customer Impact [NOT STARTED]

Inventory, SBOM, GitHub integration, matching ✅ (engine ready),
dashboard, alerts. Watchlist `check` is the local-first preview.

## Phase 6 — Early Warning Network [NOT STARTED]

Emerging signals, community contributions, confidence progression,
warning lead time (instrumented, never published until measurable),
historical intelligence.

## Non-goals (unchanged, plus strategy §18)

Full SAST/SCA, auto-remediation, generic vuln scanner, SBOM platform,
asset inventory, AI-agent/MCP security, GRC, mobile. SafeAI stays a
separate repo (conceptual KYA/KYD integration only).

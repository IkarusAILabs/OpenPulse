# OpenPulse Strategic Reset — audit, strategy, and plan

> Status as of 2026-10-02: this document is a preserved point-in-time
> audit (2026-09-27). Its diagnosis drove the work since, and most of
> its gaps are now closed: distribution discovery is live (65 registry
> diffs in the October 2026 sweep), story aggregation covers lifecycle
> AND distribution, lead-time uses first detection, OSV is wired into
> live analysis, CI runs Linux + Windows with an archived SBOM, and the
> monthly report is a decision-support briefing. The Prioritised
> backlog (§-below items 1–4) is done; item 5 (Pulse dimensions) was
> superseded. Current direction: `docs/ROADMAP.md` (M1–M8, reset
> 2026-10-02). What follows is the original audit, unedited.

Date: 2026-09-27. Status: analysis + first code slice (lifecycle story
aggregation). This document is the §20/§29 audit output. It does not
replace `docs/ARCHITECTURE_REVIEW.md` (trust architecture, still
valid); it reframes product direction.

## A. Current architecture (what exists)

Sources → collectors (7, structured errors) → pure-function analysts
(Change, Security, Evidence, Report) → evidence gate (veto) →
OSSEvent 0.4.0 → Pulse facets → reports/`check`/`observe` CLI.
Plus: catalog + namespace-aware resolution, CPE/version
applicability, KEV strength, digest-aware observations + local
history, claims/conflicts, verdicts with NOT_AFFECTED, SHA-pinned CI,
lockfile. 129 tests, all offline.

## B. Current product capabilities (what it actually does)

Validates and gates curated events (Bitnami, iText, Django EOL);
evaluates watchlists with version-aware verdicts; renders pulses and
monthly reports; observes registries with diffs. Live discovery beyond
lifecycle is thin: no license/support/ownership collectors exist.

## C. endoflife.date dependency (measured, not asserted)

September edition (`reports/2026-09-openpulse.md`, 716 lines):
85 findings = **80 endoflife-derived EOL/EOS (94%)** + 1 archived-repo
(GitHub) + 4 keyword-associated security records. **0 distribution
findings.** Report sections depending on it: every lifecycle line.
Genuinely independent capabilities: Bitnami/iText/Django fixtures,
gate, verdicts, observations, `check`, `observe` — all real, none in
the monthly product. Incremental value today: evidence discipline
around lifecycle data (recency, caps, references), not new discovery.

## D. Differentiation gaps

1. No Raw Signal → Event consolidation: N endoflife rows → N findings
   (ClickHouse-style inflation).
2. Monthly report reads as an EOL catalogue; count is the headline.
3. No discovery collectors for distribution/support/license/ownership;
   non-lifecycle intelligence exists only as curated fixtures.
4. Pulse has 7 facets; strategy wants 6 with Change+Ecosystem+Impact
   central (support/licence/distribution fold into Change stories).

## E. Documents requiring revision — done in this reset

- `docs/ROADMAP.md`: rewritten to the strategic sequence (§17).
- `README.md`: competitive boundary + five questions + not-an-EOL-tracker.
- `docs/METHODOLOGY.md`: source authority tiers; endoflife.date as one source.
- `docs/ANALYSTS.md`: agent-role mapping (§12), story aggregation rule.
- `docs/ARCHITECTURE_REVIEW.md`: addendum pointer (trust work stands).

## F. Code requiring revision — this slice only

- NEW `analyzers/event_correlation.py`: `aggregate_lifecycle()`.
- `reports/generate.py`: story rendering + non-lifecycle-first ordering.
- `analyzers/change_analyst.py`: attach `product` to lifecycle findings.
- Tests for the above. Nothing else touched.

## G. Target architecture (reframe, not rebuild)

OSS Sources → Raw Signals → Evidence Collection → Entity Resolution →
Signal Correlation → OSS Event → Impact Analysis → OpenPulse
Intelligence → Public/Customer Outputs. Current modules already sit
on these layers; the missing layer is **Signal Correlation**
(aggregation/dedup), added now for lifecycle stories first.

## H. Revised roadmap — see `docs/ROADMAP.md` (§17 sequence)

Phase 0 strategic reset (this document) → Phase 1 story aggregation
+ source tiers (this slice) → Phase 2 non-lifecycle discovery
(distribution first) → Phase 3 golden scenarios (Bitnami + iText +
minio + 7 more) → Phase 4 public intelligence → Phase 5 customer
impact → Phase 6 early-warning network. Non-goals unchanged; SafeAI
stays separate (conceptual KYA/KYD integration only).

## I. Acceptance criteria (measurable)

- September report re-rendered from identical bundles shows fewer,
  coherent lifecycle stories (count drops, versions preserved) and
  leads with non-lifecycle intelligence where present.
- At least one non-endoflife event demonstrable end to end (Bitnami:
  already; iText: already) — criterion: no new code needed, both
  re-verified in this slice.
- `ruff check`, `pytest -q`, `pip-audit` green; no new dependencies.

## Prioritised backlog (after this slice)

1. Distribution discovery collector (registry-set diffing across the
   catalog, not one-off probes) → feeds the Change facet with
   non-lifecycle stories.
2. License/support signal collectors (release-note + doc polling
   patterns; curated fixtures graduate to detected candidates).
3. Golden-scenario suite formalised (`tests/test_golden.py`).
4. Warning-lead-time instrumentation (detect date vs effective date,
   recorded never published until measurable).
5. Pulse 6-dimension migration (Change/Ecosystem/Impact central).

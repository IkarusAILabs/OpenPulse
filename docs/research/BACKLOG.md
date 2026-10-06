# Implementation Backlog — P0–P3, P5 (with item dispositions)

Scope: work that moves roadmap acceptance, in priority order. Every item states its research or product purpose. Speculative functionality is out; anything here must be buildable against the current pipeline (`collectors/` → `analyzers/` → `core/evidence` → `reports/`, 445 tests green).

Item states: DONE, ACTIVE, NEXT, DEFERRED, REMOVED. Dispositions at the bottom record what was removed, merged, deferred, downgraded, or left for validation.

## P0 — Evidence Foundation (maintain and harden)

Purpose: the trust model is the product; regressions here invalidate everything above.

- [ACTIVE] M2 acceptance set: ownership moves formalized from live firings (capa, etcd — `docs/DISCOVERIES.md` Cases 6-7); one more verified case and a live namespace-move pair remain. Purpose: prove repeatable discovery.
- [ACTIVE] Parser-version discipline: every acquisition-semantics change bumps `core/evidence/provenance.py:PARSER_VERSION` and re-baselines history (`core/observations/sweep.py` guard). Purpose: histories must never silently compare incomparable semantics.
- [NEXT] OSV/CVE/NVD published-date coverage audit: which findings still lack `announced_at`, and whether any authoritative source is untapped. Purpose: temporal accuracy (roadmap metric).
- [NEXT] `first_seen` backfill policy for lifecycle findings predating the ledger: document whether (and how) historical first detection may ever be reconstructed — default stays "unknown means unknown". Purpose: protect the no-estimation rule.
- [DEFERRED] Confidence calibration study (do CORROBORATED findings verify at the claimed rate?). Purpose: methodology stability before any metric is marketed. Deferred until M4 measurements exist.

## P1 — Real Upstream Change Discovery

Purpose: the differentiation — changes lifecycle DBs never record and SCA notices only after breakage.

- [ACTIVE] Version-aware latest-only rule follow-through: the Bitnami split must keep firing as registries evolve (digest-tagged mainlines). Purpose: keep a verified discovery derived, not just recorded.
- [NEXT] Repository/archive-change detection beyond the archived flag (deletion, rename vs transfer disambiguation in `analyze_github_meta`). Purpose: M2 priority 3 with the ownership detector as template.
- [NEXT] Support-model and license-change signal candidates (release-note/doc polling patterns; curated fixtures graduate to detected candidates only). Purpose: M2 priorities 5–6 without collector-count vanity.
- [DEFERRED] Breaking-change signals from release metadata. Purpose: real, but needs a version-diff semantics design first; no heuristic placeholders.

## P2 — Dependency Impact Intelligence

Purpose: turn public intelligence into customer answers without building generic SCA.

- [DONE] YAML watchlist path (`openpulse check`) and CycloneDX SBOM input (`core/sbom_reader.py`) converging on `check_dependency` verdicts.
- [NEXT] SPDX input alongside CycloneDX, same convergence rule (reuse identity/applicability semantics or do not ship). Purpose: M5 input breadth without a second engine.
- [DONE] Lockfile readers (package-lock, poetry.lock, Cargo.lock — pinned-version truth only; `core/lockfile_reader.py`, skip-and-record discipline, `--lockfile` composable with watchlist/SBOM). Purpose: exact-version applicability, the highest-precision M5 input.
- [DONE] Package manifest readers (requirements.txt, pyproject.toml, pom.xml, go.mod, Cargo.toml - pinned-version truth only; `core/manifest_reader.py`, skip-and-record discipline, `--manifest` composable with watchlist/SBOM/lockfile). Purpose: the most direct customer dependency input - what developers actually commit; exact-version applicability through the existing identity engine.
- [NEXT] Container image inventory input (image:tag lists → artifact matching). Purpose: closes the loop with distribution intelligence (M2→M5).
- [DEFERRED] GitHub-repository ingestion (dependency files at a ref). Purpose: real, but auth/permissions/rate-limit design belongs with customer monitoring, not local CLI.

## P3 — Intelligence Benchmark

Purpose: turn scenarios into measurements (precision/recall, false-impact/clear rates).

- [ACTIVE] Formalize cert-manager, Kafka (M4 list order). Purpose: benchmark coverage toward 10.
- [NEXT] Grafana, Terraform, one AI/ML project (the AI/ML case doubles as the M8 entry point). Purpose: close M4 coverage including agent-selected software.
- [NEXT] Benchmark harness reporting per-scenario applicability outcomes (affected/not/unknown vs expected) as a reproducibility package. Purpose: first step from scenarios to the research metrics the roadmap promises.
- [VALIDATION] Keep the Bitnami/iText/MinIO/Django/Redis/PostgreSQL six green and historically pinned; any semantic change must flip-or-justify their assertions, never silently adjust them.

## P5 — Evidence Contract (attestation precursor)

Purpose: machine-readable dependency intelligence another system can consume without understanding OpenPulse internals — the prerequisite for any SafeAI interchange (M9).

- [DONE] Evidence contract minimal schema (`core/attestation.py`): event context, identity (with trust status), scope, affected dependency, applicability basis (match strength + method), assessment, confidence, evidence references with source authority, the four temporal roles, recommendation, unknowns, limitations, provenance (OpenPulse version, schema version, generation timestamp, content hash). Every field documents its current source; convergence, not invention. Builder is a pure function over (event, verdict[, finding]); round-trip dump→validate→byte-identical is test-pinned; the content hash covers the evidence body only (clock-independent), so the same logical document always hashes identically.
- [PLANNED, marked in schema, never populated] `signature`, `signing_key_id`, `trust_root` — keys, signatures, and trust roots are a separate, later issue. The contract is NOT a signature format and NOT a policy decision: consumers decide what to do with the assessment.
- [NEXT] First external consumer validation (M9 experiment design only — no coupled runtime before the contract has a consumer).

## Dispositions

- REMOVED: v0.x phase plan; "292 tests" header; completed Next-90 items (SBOM reader, detection ledger, OSV live wiring) as roadmap aspirations — all shipped.
- MERGED: distribution story aggregation + namespace-move detection into the M2 mechanism story; SBOM archiving (CI) vs SBOM input (product) clarified as separate lines.
- DEFERRED (with reason stated above): confidence calibration, breaking-change signals, GitHub-repo ingestion.
- DOWNGRADED: AI/ML golden scenario from M4-must to M4-closeout/M8-entry (keeps benchmark shippable without the research direction).
- LEFT FOR VALIDATION: M2 acceptance set; applicability metric measurement; combined SafeAI+OpenPulse experiment design (M9, hypothesised only).

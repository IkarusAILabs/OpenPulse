# Implementation Backlog — P0–P3 (with item dispositions)

Scope: work that moves roadmap acceptance, in priority order. Every item states its research or product purpose. Speculative functionality is out; anything here must be buildable against the current pipeline (`collectors/` → `analyzers/` → `core/evidence` → `reports/`, 409 tests green).

Item states: DONE, ACTIVE, NEXT, DEFERRED, REMOVED. Dispositions at the bottom record what was removed, merged, deferred, downgraded, or left for validation.

## P0 — Evidence Foundation (maintain and harden)

Purpose: the trust model is the product; regressions here invalidate everything above.

- [ACTIVE] M2 acceptance set: confirm-or-kill pending pruning cases; formalize ownership/namespace-move firings (`docs/DISCOVERIES.md`). Purpose: prove repeatable discovery.
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
- [NEXT] Lockfile readers (package-lock, poetry.lock, Cargo.lock — one format at a time, pinned-version truth only). Purpose: exact-version applicability, the highest-precision M5 input.
- [NEXT] Container image inventory input (image:tag lists → artifact matching). Purpose: closes the loop with distribution intelligence (M2→M5).
- [DEFERRED] GitHub-repository ingestion (dependency files at a ref). Purpose: real, but auth/permissions/rate-limit design belongs with customer monitoring, not local CLI.

## P3 — Intelligence Benchmark

Purpose: turn scenarios into measurements (precision/recall, false-impact/clear rates).

- [ACTIVE] Formalize Kubernetes, cert-manager, Kafka (M4 list order). Purpose: benchmark coverage toward 10.
- [NEXT] Grafana, Terraform, one AI/ML project (the AI/ML case doubles as the M8 entry point). Purpose: close M4 coverage including agent-selected software.
- [NEXT] Benchmark harness reporting per-scenario applicability outcomes (affected/not/unknown vs expected) as a reproducibility package. Purpose: first step from scenarios to the research metrics the roadmap promises.
- [VALIDATION] Keep the Bitnami/iText/MinIO/Django/Redis/PostgreSQL six green and historically pinned; any semantic change must flip-or-justify their assertions, never silently adjust them.

## Dispositions

- REMOVED: v0.x phase plan; "292 tests" header; completed Next-90 items (SBOM reader, detection ledger, OSV live wiring) as roadmap aspirations — all shipped.
- MERGED: distribution story aggregation + namespace-move detection into the M2 mechanism story; SBOM archiving (CI) vs SBOM input (product) clarified as separate lines.
- DEFERRED (with reason stated above): confidence calibration, breaking-change signals, GitHub-repo ingestion.
- DOWNGRADED: AI/ML golden scenario from M4-must to M4-closeout/M8-entry (keeps benchmark shippable without the research direction).
- LEFT FOR VALIDATION: M2 acceptance set; applicability metric measurement; combined SafeAI+OpenPulse experiment design (M9, hypothesised only).

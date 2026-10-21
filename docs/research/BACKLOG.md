# Implementation Backlog — P0–P3, P5 (with item dispositions)

Scope: work that moves roadmap acceptance, in priority order. Every item states its research or product purpose. Speculative functionality is out; anything here must be buildable against the current pipeline (`collectors/` → `analyzers/` → `core/evidence` → `reports/`; test count reported by CI). Security-review items (2026-10-21) are sequenced in `docs/NEXT_PHASES.md`; finding IDs (H1, M1–M7, L1–L11) refer to that review.

Item states: DONE, ACTIVE, NEXT, DEFERRED, REMOVED. Dispositions at the bottom record what was removed, merged, deferred, downgraded, or left for validation.

## P0 — Evidence Foundation (maintain and harden)

Purpose: the trust model is the product; regressions here invalidate everything above.

- [DONE 2026-10-07] M2 acceptance set: five live-replayed cases (capa, etcd, traefik, fbsdk archive+move, bitnami/spark empty mainline — `docs/DISCOVERIES.md` Cases 6-10); a live namespace-move pair for `split_moves` remains. Purpose: repeatable discovery proven.
- [ACTIVE] Parser-version discipline: every acquisition-semantics change bumps `core/evidence/provenance.py:PARSER_VERSION` and re-baselines history (`core/observations/sweep.py` guard). Purpose: histories must never silently compare incomparable semantics.
- [NEXT] OSV/CVE/NVD published-date coverage audit: which findings still lack `announced_at`, and whether any authoritative source is untapped. Purpose: temporal accuracy (roadmap metric).
- [NEXT] `first_seen` backfill policy for lifecycle findings predating the ledger: document whether (and how) historical first detection may ever be reconstructed — default stays "unknown means unknown". Purpose: protect the no-estimation rule.
- [DEFERRED] Confidence calibration study (do CORROBORATED findings verify at the claimed rate?). Purpose: methodology stability before any metric is marketed. Deferred until M4 measurements exist.
- [NEXT, v0.7.0] Derived source authority (M1): `official` only when an https URL's host is on the project's `official_domains` allowlist; `Source.authority` becomes a fail-closed Literal. Purpose: a caller-supplied string must never reach CONFIRMED.
- [NEXT, v0.7.0] Derived independence (M2): source family from the URL's registrable domain when `family` is absent. Purpose: two names for one origin never make CORROBORATED.
- [NEXT, v0.7.0] Keyed history integrity (H2): HMAC over chain fields and ledger entries with a key outside `.openpulse/`, `first_detected_at` chained, missing tip = ROLLBACK_SUSPECTED, external anchor checkpoints. Purpose: lead time - the headline metric - must rest on a history an attacker cannot silently rewrite.

## P1 — Real Upstream Change Discovery

Purpose: the differentiation — changes lifecycle DBs never record and SCA notices only after breakage.

- [DONE] Warning deadline surface (`core/warnings.py`, `openpulse warnings`): severity bands over the ONE digest join, ranked countdown with lead times inherited from the ledger (`docs/LEAD_TIME_CASES.md` pins three replayable cases). Purpose: turn first detections into deadlines without a second matching engine.
- [ACTIVE] Version-aware latest-only rule follow-through: the Bitnami split must keep firing as registries evolve (digest-tagged mainlines). Purpose: keep a verified discovery derived, not just recorded.
- [NEXT] Repository/archive-change detection beyond the archived flag (deletion, rename vs transfer disambiguation in `analyze_github_meta`). Purpose: M2 priority 3 with the ownership detector as template.
- [NEXT] Support-model and license-change signal candidates (release-note/doc polling patterns; curated fixtures graduate to detected candidates only). Purpose: M2 priorities 5–6 without collector-count vanity.
- [DEFERRED] Breaking-change signals from release metadata. Purpose: real, but needs a version-diff semantics design first; no heuristic placeholders.

## P2 — Dependency Impact Intelligence

Purpose: turn public intelligence into customer answers without building generic SCA.

- [DONE] YAML watchlist path (`openpulse check`) and CycloneDX SBOM input (`core/sbom_reader.py`) converging on `check_dependency` verdicts.
- [DONE] SPDX input alongside CycloneDX, same convergence rule (`read_spdx`, `check --spdx`). Purpose: M5 input breadth without a second engine.
- [DONE] Lockfile readers (package-lock, poetry.lock, Cargo.lock — pinned-version truth only; `core/lockfile_reader.py`, skip-and-record discipline, `--lockfile` composable with watchlist/SBOM). Purpose: exact-version applicability, the highest-precision M5 input.
- [DONE] Package manifest readers (requirements.txt, pyproject.toml, pom.xml, go.mod, Cargo.toml - pinned-version truth only; `core/manifest_reader.py`, skip-and-record discipline, `--manifest` composable with watchlist/SBOM/lockfile). Purpose: the most direct customer dependency input - what developers actually commit; exact-version applicability through the existing identity engine.
- [DONE] Container image inventory input (`core/image_inventory.py`, `check --images`); registry-port refs keep distinct identities since #113. Purpose: closes the loop with distribution intelligence (M2→M5).
- [DONE 2026-10-19] GitHub-repository ingestion (`core/github_reader.py`, `--github-repo`): commit- and blob-SHA-pinned, bounded, COMPLETE/PARTIAL/FAILED coverage in verdicts and contract v1.1. Purpose: dependency files at a ref without treating absence as proof.
- [DONE 2026-10-21] Namespaced pom.xml (#112): real-world POMs no longer parse to zero deps; DOCTYPE refused, depth/element caps.
- [NEXT, v0.6.1] SBOMs discovered in GitHub repos are never ingested (M7: dict passed to path readers); bounded reads (`read(MAX+1)`), RecursionError handling, iterative package-lock v1 walk. Purpose: no silent input-layer gaps.

## P3 — Intelligence Benchmark

Purpose: turn scenarios into measurements (precision/recall, false-impact/clear rates).

- [DONE] Kafka and cert-manager goldens formalized (M4): two EOL cycles each verified against live endoflife.date rows and packaged-image identity.
- [DONE] Grafana and Terraform goldens (M4 now at 11 scenarios). [NEXT] one AI/ML project only where it tests a distinct hypothesis (doubles as the M8 entry point).
- [NEXT] Benchmark harness reporting per-scenario applicability outcomes (affected/not/unknown vs expected) as a reproducibility package. Purpose: first step from scenarios to the research metrics the roadmap promises.
- [VALIDATION] Keep the Bitnami/iText/MinIO/Django/Redis/PostgreSQL/Kubernetes/Kafka/cert-manager nine green and historically pinned; any semantic change must flip-or-justify their assertions, never silently adjust them.

## P5 — Evidence Contract (attestation precursor)

Purpose: machine-readable dependency intelligence another system can consume without understanding OpenPulse internals — the prerequisite for any SafeAI interchange (M9).

- [DONE] Evidence contract minimal schema (`core/attestation.py`): event context, identity (with trust status), scope, affected dependency, applicability basis (match strength + method), assessment, confidence, evidence references with source authority, the four temporal roles, recommendation, unknowns, limitations, provenance (OpenPulse version, schema version, generation timestamp, content hash). Every field documents its current source; convergence, not invention. Builder is a pure function over (event, verdict[, finding]); round-trip dump→validate→byte-identical is test-pinned; the content hash covers the evidence body only (clock-independent), so the same logical document always hashes identically.
- [PLANNED, marked in schema, never populated] `signature`, `signing_key_id`, `trust_root` — keys, signatures, and trust roots are a separate, later issue. The contract is NOT a signature format and NOT a policy decision: consumers decide what to do with the assessment.
- [DONE] Evidence contract v1 standalone schema (issue #67): `schemas/evidence-contract/v1/schema.json` (draft 2020-12, per-field provenance pointers, planned signature fields null), `core/evidence_contract.py` (builder over the #60 convergence, dependency-free fail-closed validator, content hash over the v1 shape), `openpulse attest` CLI (JSONL emit, composable sources), docs/EVIDENCE_CONTRACT.md. No new dependencies.
- [DONE 2026-10-19] Evidence contract v1.1 (`schemas/evidence-contract/v1.1/`): additive required `inspection_coverage` block; v1.0 schema untouched.
- [NEXT, v0.7.0] Contract v1.2: content hash over RFC 8785 (JCS) canonical JSON so non-Python consumers can verify it (today's hash uses Python-mode `model_dump()`). Signature fields stay null.
- [NEXT] First external consumer validation (M9 experiment design only — no coupled runtime before the contract has a consumer).

## Dispositions

- REMOVED: v0.x phase plan; "292 tests" header; completed Next-90 items (SBOM reader, detection ledger, OSV live wiring) as roadmap aspirations — all shipped.
- MERGED: distribution story aggregation + namespace-move detection into the M2 mechanism story; SBOM archiving (CI) vs SBOM input (product) clarified as separate lines.
- DEFERRED (with reason stated above): confidence calibration, breaking-change signals.
- UN-DEFERRED → DONE: GitHub-repo ingestion (v0.6.0, #100), with auth limited to a read-only token and bounded, pinned inspection.
- ADDED 2026-10-21: security-review items (derived authority/independence, keyed history, contract JCS hash, input-layer gaps), sequenced in `docs/NEXT_PHASES.md`.
- DOWNGRADED: AI/ML golden scenario from M4-must to M4-closeout/M8-entry (keeps benchmark shippable without the research direction).
- LEFT FOR VALIDATION: M2 acceptance set; applicability metric measurement; combined SafeAI+OpenPulse experiment design (M9, hypothesised only).

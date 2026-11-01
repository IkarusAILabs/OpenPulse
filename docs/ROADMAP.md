# OpenPulse Roadmap — re-baselined 2026-10-04 for the Ikarus AI Labs research programme

> OpenPulse is the Software Ecosystem Evidence Plane within the [Ikarus AI Labs research programme](https://ikaruslabs.net/research) on Evidence-Based Assurance for AI-Mediated Software Change.
>
> OpenPulse investigates how software organisations can establish trustworthy evidence about changes occurring in the open-source ecosystem, determine whether those changes apply to their dependencies, and provide timely, explainable warnings.
>
> SafeAI independently investigates the Agent Authority Evidence Plane: what authority an AI agent can potentially exercise and how that authority changes.
>
> A future research direction is to connect these evidence planes and investigate whether combined evidence can improve decisions about AI-mediated software changes.

Use this framing without claiming that the combined model is already proven. The combined assurance experiment is hypothesised, not established.

Status (2026-11-01): **product development continues alongside track R** (owner decision; see "Amendment 2026-11-01" below). v0.9.0 "Anchored Trust" and v0.10.0 "Verified Releases & Safe Gates" are released; M6 is no longer paused. Status (2026-10-31): track T, AI Dependency Trust Assurance, is added as a planned, separate future study (see below). It changes neither track R nor R's precedence. Status (2026-10-30): research track R (below) takes precedence until the TR-2026-01 journal submission. Earlier status (2026-10-28): v0.7.0 "Channels" released (MCP server for AI coding agents, DefectDojo export, Dependency-Track upload, release-line verdict fix #133, install name `ikarus-openpulse`); v0.7.1 adds collector response caps (#155) and hash-locked installs (#156); Phase A correctness and leak fixes merged (#112, #113, #115–#120); intelligence schema 0.5.0, evidence contract v1.1, CI on Linux + Windows, deterministic SBOM archived. Test count is reported by CI. Next phases: `docs/NEXT_PHASES.md`. This reset supersedes the 2026-10-02 M1–M8 sequence: the milestones below re-baseline it against implementation reality and the research programme, they do not discard it.

Status words used in this document: DONE, ACTIVE, VALIDATION, NEXT, FUTURE, RESEARCH, PAUSED. Research claims are additionally qualified as observed, implemented, validated, hypothesised, or planned — hypotheses are never described as established capabilities.

## Re-baseline 2026-10-30: research track R takes precedence

An external recommendation on TR-2026-01 (assessment: `papers/tr-2026-01/RECOMMENDATION_ASSESSMENT.md`) concludes that the report is a sound specification and implementation audit, but not yet a competitive journal submission. Its missing piece is evidence that completeness-aware decisions are *better* than simpler alternatives. We accept that conclusion. Until the journal submission, **track R below is the priority**. Everything else is either a prerequisite for R or waits.

- Target: "Level 2", an empirically strengthened manuscript. It needs a precise contribution, independent validation, labelled historical cases and a comparative evaluation. Level 3 (multiple ecosystems, longitudinal and practitioner studies) is not a prerequisite.
- TR-2026-01 itself may be published now as a technical report, with its claims as they stand. The journal version waits for R-C.
- Rule for R: build only what an experiment needs. Every R item names the research question it serves.

**Amendment 2026-11-01 (owner decision): product development is not frozen for the paper.** Track R stays the research priority, but product features no longer wait for the journal submission; they are planned on their own merits, release by release. One guardrail stays: product work never changes the frozen evaluation (`evaluation/`, `build_v1_contract`, the freeze tags) or the verdict semantics the registered study depends on without an explicit owner decision. The table below records what this un-pauses.

### R-A — Research design (contribution and protocol)
STATUS: ACTIVE

- [ACTIVE] **R-A1:** State the contribution as a testable model: when a negative applicability verdict is justified (scope typing, completeness with a basis, exact vs envelope, identity, freshness). Claim the model and its evaluation. Do not claim completeness reasoning or three-valued logic as new.
- [DONE 2026-10-31 as an open protocol] **R-A2:** The registration is complete in `evaluation/REGISTRATION.md`, and the registered analysis is implemented in `evaluation/registration.py`, with frozen constants and tests. It also implements S3, G4, W1–W3 and D1–D2, and sets the stopping rule and the inclusion criteria. The single author will not archive or run it alone, because it needs independent annotators. It is offered to independent teams, who register it in their own name (REGISTRATION, "Who runs it").
  - **Primary:** C vs B. H1 is safety: event-level false-clear share, δ 0.05, ≥ 60 events. H2 is a resolution gain of ≥ 0.10.
  - **Secondary**, Holm-corrected: C vs V equivalence within ±0.05; A vs C false clears; C vs R resolution (S3).
  - **Guardrails:** silent misses ≤ 0.02; unresolved ≤ B + 0.05; per-class flag above 0.60; C's median W1 ≤ B's (G4).
  - **The change from the draft:** making V secondary is disclosed.
  - **Remaining, for the author:** complete the fields marked "to fill at archiving" (registry, date, freeze tag, window start, annotators, stopping number, per-class inclusion criteria), then archive on OSF Registries or Zenodo before any held-out label exists.
- [NEXT] **R-A3:** Widen related work on vulnerability applicability and VEX/CSAF consumption, SBOM accuracy, package identity (purl, cross-ecosystem naming), dependency management and AI package recommendation. Each comparison must answer one question: what can a consumer do with the model that it could not do reliably before?

### R-B — Minimal OpenPulse enhancements the experiments need
STATUS: ACTIVE

- [DONE 2026-10-30] **R-B1:** Evaluation harness (`evaluation/`). It provides:
  - decision policies A-naive, B-conservative and C-openpulse;
  - input-transform ablations of completeness and freshness;
  - the recommendation's metrics: false clears, FCR_affected and FCR_clear, silent misses, false impact, resolution, abstention, unsupported decisiveness and evidence completeness;
  - replay of recorded evidence as known at a date (`replay.py`).
- [DONE 2026-10-30] **R-B2:** Labelled development set, `evaluation/cases/dev-2026-10.json`: 60 pairs over 13 events, each label with a rationale and a source. It tests the harness and is not evaluation evidence.
- [DONE 2026-10-30] **R-B3:** Fixed evaluation finding **F1**. Package identity resolved by name across ecosystems, so redis-py (PyPI `redis`) was AFFECTS_VERSION under Redis server end of life. Package identity is now per ecosystem (catalog `packages` lists plus `osv` blocks), and redis-py and node-redis are curated as their own projects. No golden flipped. Follow-up done 2026-10-30: every catalog entry now curates its `packages`, and a hygiene test requires it.
  - Libraries list the packages that are the project (Maven coordinates included).
  - Servers and tools declare none, so a same-named client package (PyPI `kubernetes`, npm `mongodb`, npm `angular`) is unresolved.
- [DONE 2026-10-30] **F2:** A package-scope rule that was outside the specification is now specified as the *project package element*: a package-scope value naming the event's own project denotes every package curated as that project.
  - It is exact. It gives **M** for curated identity, **0** for other projects, and **?** for unresolved identity.
  - It is in SPEC §4.4, the team oracle and baseline V. The conformance vocabulary now includes `redis-server`, a package whose name is not its project's slug, and a new F2 mutant is caught by the matrix and the random cases.
  - Package names also compare in canonical form: Maven `group:artifact` = `group/artifact`, and PEP 503 for PyPI.
  - TR §5.3 needs the matching sentence (proposed in the PR).
- [DONE 2026-10-30] **F3:** Package-scope values may now be ecosystem-qualified purls (`pkg:pypi/redis`), with no schema change, since `Scope.packages` is a list of strings.
  - A qualified value names exactly one package and decides on (ecosystem, canonical name) before identity: **M** when equal, **N** for another ecosystem, **?** otherwise.
  - Bare values decide on identity first, and SPEC §4.4 is now aligned with the engine.
  - It is in the engine, the team oracle, baseline V and the kit (dependencies may state an ecosystem). The matrix and generators gained packages with stated ecosystems and qualified values. A new F3 mutant (qualified values matched by name alone) is caught.
  - Producers should qualify package values; the curated fixtures still use bare names.
- [DONE 2026-10-30] **F4:** A package that resolves only to itself is now unresolved (RELATED) even when its name equals the event's project. It is never excluded by version and never counted as the project. This is the package-side twin of D10.
  - Real relocation events were affected, not just test fixtures: capa and react-native-fbsdk were not in the catalog, so bare package names matched their projects by coincidence. Both are now curated: capa with PyPI `flare-capa`, react-native-fbsdk with npm `react-native-fbsdk`. Their goldens are unchanged.
  - `tests/test_false_clear.py` curates its `acme` stand-in in a fixture instead of relying on the name. One security-chain test is flipped, with its justification.
  - The randomised generator has an uncatalogued event project (`zzzpkg`). A new F4 mutant is caught by the random cases and a regression test.
- [DONE 2026-10-30] **R-B4:** Strong conservative baseline V (`evaluation/strong_baseline.py`): the same typed scopes, admissibility and curated identities as C, exact identity only, `packaging` for PyPI, and plain numbers elsewhere. On the development set it differs from C on 1 of 60 pairs, so the contribution to claim is the model, not the engine.
  - Comparators pinned 2026-10-30, through bridges to the real tools: node-semver 7.8.5, x/mod v0.42.0, maven-artifact 3.9.16 (`evaluation/comparators/`).
  - The registered run refuses without them (`--require-comparators`), and CI's `comparators` job runs them against documented semantics.
  - `crosscheck.py` compares OpenPulse's own comparator with them.
  - dpkg is out of scope: no `pkg:deb` reader exists.
- [DONE 2026-10-30] **R-B5:** Identity ablation as an explicit, call-scoped engine parameter: `check_dependency(unresolved_identity="unrelated")`. On the development set it cuts abstention from 0.47 to 0.18 at the cost of silent misses on 3 of 27 in-scope pairs, which is the measured coverage cost of D10.
- [DONE 2026-10-30] **R-B6:** Decisions expose their limitations. Evidence contract 1.2.0 adds `verdict_meaning` (direct scope, plus embedded components, availability, maintenance and security consequence, all `not_evaluated`, and a fixed statement with no upstream text), `scope.completeness` (state, basis, admits_negative) and `evaluation_context` (freshness bound and identity policy). The MCP response carries the same `verdict.meaning`, and its fixed note now qualifies NOT_AFFECTED too. The evaluation's evidence-completeness metric reads these contract fields. The JCS hash moves to contract 2.0.0, because hash changes are breaking under the versioning policy.
- [ACTIVE 2026-10-30, waiting on an outside author] **R-B7:** Independent specification check. The kit is ready in `conformance/independent/`:
  - `SPEC.md`: the decision rules, self-contained;
  - `README.md`: the process, deliverables, case format, attestation and adjudication;
  - `vocabulary.json`: the references a case may use;
  - `kit.py`: `export` (seeded random cases), `validate` (fails closed), and `compare` (expected, independent oracle, team oracle and implementation side by side, with severities, and judgement-vs-rules conflicts listed as candidate specification defects).

  A throwaway oracle written from SPEC.md alone agreed with both team sources on 20,000 exported cases, so the text has no transcription errors that random cases expose. That is not independent evidence. Next: recruit the author, agree the export seed, and publish the submission and its adjudication.
- [LATER, only if R-C needs it] Ecosystem expansion beyond the current three change classes on two platforms.

### R-C — Empirical evaluation
STATUS: NEXT for the held-out study, which waits on an independent team to register and run the R-A2 open protocol. R-C0, the exploratory retrospective study, is done.

- [ACTIVE 2026-10-30, design awaiting approval] **R-C0:** Retrospective study on real historical changes. It answers the recommendation's Priority 2. It is exploratory, reported separately, and never pooled with the registered result.
  - Rules: `evaluation/retrospective/DESIGN.md`. Screened candidates: `evaluation/retrospective/SHORTLIST.md`, with 27 of 33 included or provisional across 6 classes.
  - The implementation is frozen at `retro-freeze-2026-10-30`.
  - Next, after approval: fill the gaps (relocation, end of life), build the fixtures, sample dependents, label (with a 25% outside sample), freeze the case file, run, and report.
- **R-C1:** Held-out event set. Sample from sources that do not feed OpenPulse, with per-class inclusion criteria fixed first, over a window after the implementation freeze. A prospective window is preferred: OpenPulse cannot replay registry state it never recorded, and reconstructing past state from today's state invites hindsight bias. Retrospective events are admitted only with archived contemporaneous evidence.
- **R-C2:** Independent labels. Two annotators outside the detector's development, adjudication by a third, and Cohen's κ. Undeterminable is a first-class label. This needs external collaborators (see Availability and Collaboration in the report) and is the schedule's critical path.
- **R-C3:** Comparison. Run A, B, the strong baseline v and C, plus the ablations (completeness, freshness, identity, the gate), with event-clustered intervals and stratification by event class, identity status and completeness basis. Include error analysis of every wrong or unresolved decision.
- **R-C4:** Discovery on historical changes. Report precision, and recall against an independent reference set only where a defensible ground truth exists. Report scope-construction and identity-resolution accuracy separately from decision accuracy. Name the classes with no reliable ground truth.
- Pre-commitment: the result decides the claim. "Fewer false clears at the cost of more abstentions" and "no better than the strong baseline" are both reportable outcomes. Neither is repaired by adding features.

### R-D — Paper revision and submission
STATUS: FUTURE (after R-C)

- **R-D1:** Rewrite the introduction and contributions around the demonstrated gap. Every major claim cites an R-C result or is removed.
- **R-D2:** Reproducibility package: a tagged, archived release (DOI) containing the dataset with its SHA-256, the protocol version, the harness, raw results, ground-truth construction notes, and examples of wrong and unresolved decisions.
- **R-D3:** Choose the venue from the finished contribution, not before.

### What track R pauses or defers

| Work | Disposition | Reason |
|---|---|---|
| M6 hosted surfaces, dashboards, notifications, delivery state | UN-PAUSED 2026-11-01 (was PAUSED) | Product maturity is not evidence, so M6 never feeds the paper's claims; it now proceeds alongside R (amendment above). |
| M7 Intelligence Network | FUTURE (unchanged) | |
| M9, and SafeAI integration in this paper | DEFERRED | It widens scope and complicates attribution. It stays a separate future study. |
| v0.9.0 Anchored Trust (keyed history, external anchoring) | DONE 2026-11-01 (released ahead of R-C) | Needed for lead-time claims. The applicability evaluation does not rest on them, and the frozen evaluation is unchanged. The paper keeps lead times as caveated observations. |
| E1–E5 external developments | E5 (comparator runs) folded into R-C3; E1–E4 LATER | |
| Security-review items (Phase B in `docs/NEXT_PHASES.md`) | Continue (since 2026-11-01, no longer limited to false clears and false impacts) | |
| Track T, AI Dependency Trust Assurance (added 2026-10-31) | Phase 0 (design) first; code may follow without waiting for the submission (2026-11-01) | It is a separate study, outside the TR-2026-01 registration (§13: discovery and the agent interface are outside the study). It must not change verdicts or the frozen evaluation. |

## Product thesis (kept)

OpenPulse is:

“OSS Dependency Intelligence that detects upstream changes and warns you before they become problems for your software.”

Core product loop:

```text
UPSTREAM CHANGE
      ↓
EVIDENCE
      ↓
IDENTITY
      ↓
APPLICABILITY
      ↓
DEPENDENCY IMPACT
      ↓
WARNING WINDOW
      ↓
ACTION
```

Positioning: “Watch what can change underneath your software.”

The roadmap continues to reject: becoming an EOL database, becoming a generic SCA, collector-count vanity, opaque risk scores, and AI reasoning in the trusted decision path.

## Where OpenPulse sits in the research programme

Ikarus AI Labs investigates how organisations can make AI-mediated software changes observable, explainable and accountable, across four planes: Agent Authority Evidence (SafeAI), Software Ecosystem / Dependency Evidence (OpenPulse), Assurance Policy / Decision, and Human Accountability. OpenPulse is the primary implementation of the **Software Ecosystem Evidence Plane**. Its question is:

> **What is changing in the software ecosystem, what evidence establishes the change, and does that evidence apply to a dependency?**

Do NOT merge SafeAI and OpenPulse into one product. Do NOT turn OpenPulse into a generic AI-security scanner. OpenPulse stays a rigorous, evidence-based dependency intelligence system that can eventually participate in an assurance decision when software changes are AI-mediated.

The core evidence model:

```text
SOURCE SIGNAL
      ↓
OBSERVED CHANGE
      ↓
IDENTITY
      ↓
APPLICABILITY
      ↓
DEPENDENCY IMPACT
      ↓
ASSESSMENT
      ↓
RECOMMENDATION
```

Kept as research assets, not slogans:

```text
RELATED ≠ AFFECTED
AFFECTS_PROJECT ≠ AFFECTS_VERSION
UNKNOWN ≠ NOT_AFFECTED
MATCH STRENGTH ≠ EVIDENCE STRENGTH
OBSERVATION ≠ CLAIM ≠ EVENT
```

## Conceptual layers (durable research architecture)

Beyond the chronological milestones, the pipeline is ten layers. New work should name the layer it extends; work that fits no layer is suspect.

1. **Observe** — upstream signals and registry observations.
2. **Establish Evidence** — source authority, provenance, independence, confidence.
3. **Resolve Identity** — project, package, artifact, distribution, registry identity.
4. **Establish Applicability** — version and artifact matching.
5. **Assess Impact** — affected / not affected / unknown.
6. **Establish Time** — announced / detected / verified / effective.
7. **Warn** — warning windows and early detection.
8. **Integrate Dependency Context** — SBOMs, manifests, lockfiles, image inventories.
9. **AI-Mediated Change** — dependency intelligence for agent-selected software changes.
10. **Assurance Research** — combined OpenPulse + SafeAI evidence experiments.

## M1 — Trusted Software Ecosystem Evidence
STATUS: DONE / MAINTENANCE

The evidence foundation. Existing architecture is strong; do not expand it without a concrete requirement:

- evidence schema, provenance, source authority, source-family independence
- identity trust (VERIFIED / REVIEW_REQUIRED / UNVERIFIED)
- version applicability, explicit NOT_AFFECTED
- confidence model with match strength vs evidence strength separated
- registry observations, tamper-evident (keyed) observation history since v0.9.0 "Anchored Trust" (corruption-detecting without a history key) - the one M1 expansion with a concrete requirement (lead-time claims rest on this history)
- first-detection semantics, deterministic reports
- security hardening (SSRF policy, redaction, lock-drift check, secret tripwire)

## M2 — Real Upstream Change Discovery
STATUS: ACTIVE / HIGHEST PRIORITY

Objective: repeatedly discover meaningful non-lifecycle changes with enough evidence to survive independent validation — distribution, registry, repository/archive, maintainer/ownership, support-model, license, breaking changes, package/distribution removal, migration signals. Not more signals: the October 2026 sweep proved mechanisms fire (65 diffs, since killed as window artifacts per `docs/DISCOVERIES.md`), but M2 acceptance (5 verified reproducible cases; met 2026-10-07 — capa, etcd, traefik, fbsdk and bitnami/spark live-replayed, joining minio and Bitnami) is met. Formalization and verification, not mechanism, is the work.

## M3 — Intelligence Report Product
STATUS: ACTIVE

The monthly briefing is a product surface (Executive Summary through Historical appendix, plus the `.meta.json` machine companion and the Lifecycle Posture view). Keep it ahead of the intelligence it carries; no new sections without a reader need. Lifecycle stays one category, never the product.

## M4 — Software Ecosystem Intelligence Benchmark
STATUS: VALIDATION (11 scenarios formalized: Bitnami, iText, MinIO, Django, Redis, PostgreSQL, Kubernetes, Kafka, cert-manager, Grafana, Terraform)

A major research milestone: the suite must test identity (upstream vs distribution vs fork vs rename vs namespace vs package vs artifact), applicability (affected / not affected / unknown), evidence (official / corroborated / emerging / unverified), time (announced / first detected / last verified / effective / reported), and discovery across change classes. Every scenario answers the eight questions (change, evidence, identity, dependency, versions/artifacts, timing, investigation, why-not-a-database-record) with a “why OpenPulse?” assertion. The current suite is intentionally biased toward identity/applicability ambiguity and non-lifecycle change classes; an AI/ML scenario remains a useful future expansion, not a release blocker.

## M5 — Dependency Context & Impact Intelligence
STATUS: DONE / MAINTENANCE

```text
USER DEPENDENCY
        ↓
CANONICAL IDENTITY
        ↓
OPENPULSE INTELLIGENCE
        ↓
APPLICABILITY
        ↓
IMPACT
        ↓
EVIDENCE
        ↓
ACTION
```

Shipped: YAML watchlists, CycloneDX + SPDX SBOM input (`core/sbom_reader.py`), container image inventories (`core/image_inventory.py`), lockfile input - package-lock.json/poetry.lock/Cargo.lock (`core/lockfile_reader.py`), package manifests - requirements.txt/pyproject.toml/pom.xml/go.mod/Cargo.toml (`core/manifest_reader.py`), and GitHub repository input (`core/github_reader.py`). All inputs converge on the same canonical identity and applicability semantics — never a second matching engine, never generic SCA coverage-chasing. GitHub inspection is bounded, commit-pinned, and reports partial/unsupported coverage rather than treating absence as proof of no dependencies.

## M6 — Early Warning
STATUS: NEXT (un-paused 2026-11-01; paused 2026-10-30 for track R; was ACTIVE / OPERATIONALIZATION)

Continuous monitoring, alerts, digests, dashboards, warning deadlines, first-detection history, event timeline, CI/PR checks. Implemented foundation: durable per-entity first-detection ledger (`core/detections/ledger.py`), lead time defined as `effective_date − first_trustworthy_detection`, never estimated, never averaged for marketing; alert digest (`core/digest.py`) and ranked warning deadlines with severity bands (`core/warnings.py`), plus replayable lead-time case studies (`docs/LEAD_TIME_CASES.md`). Research question stays: “What is changing in MY software?”

## M7 — Intelligence Network
STATUS: FUTURE

Emerging signals, community observations, confidence progression, cross-source triangulation, long-term history, anonymized cross-user intelligence. Only start when dependency monitoring is working.

## M8 — AI-Mediated Dependency Intelligence
STATUS: RESEARCH + EARLY PREVIEW (agent channel shipped: `openpulse mcp`, see `docs/MCP.md`)

Implemented (2026-10-24): an MCP server lets coding agents query dependency evidence before they change a dependency. This keeps the principle below intact: the agent *consumes* OpenPulse evidence, while OpenPulse's verdicts stay deterministic and evidence-gated. No AI is in OpenPulse's decision path.

Research question: how should dependency intelligence change when AI agents increasingly select, introduce, upgrade and remove software dependencies? OpenPulse contributes dependency intelligence + applicability + evidence + temporal context; SafeAI contributes agent authority + change + authority evidence. Do NOT put an AI agent in the trusted decision path; study the evidence question first.

## M9 — Evidence-Based Assurance for AI-Mediated Software Change
STATUS: RESEARCH / FUTURE (flagship experiment, hypothesised); DEFERRED out of the TR-2026-01 journal version

Can agent-authority evidence and dependency evidence be combined into safer, more explainable decisions? Compare dependency-only (OpenPulse) vs authority-only (SafeAI) vs combined evidence (+ deterministic policy) on: unsafe changes detected, false positives/negatives, unnecessary reviews, decision explainability, evidence completeness, unknown conditions, reproducibility, human decision effort. None of this is proven; the experiment is the point.

## SafeAI / OpenPulse boundary (not blurred)

- SafeAI answers: what authority does this AI agent have, what changed, and what evidence supports that conclusion?
- OpenPulse answers: what is changing in the software ecosystem, what evidence establishes the change, and does it affect this dependency?
- A future assurance layer answers: should the AI-mediated software change be allowed?

The future system combines evidence rather than duplicating either product. Interchange stays a boundary, not a runtime: OpenPulse exports dependency identity, context, upstream event, applicability, confidence, evidence, temporal information, recommendation; SafeAI exports agent identity, authority, changed authority, dependency references, policy context, evidence. A future policy layer combines the two. No coupled runtime before the contract exists.

## Public/internal evidence boundary (research principle)

Retain and formalise: observation ≠ claim ≠ event; public intelligence ≠ dependency-specific intelligence. Public intelligence must never imply user impact without dependency evidence; an upstream event is not evidence that a specific dependency is affected. Enforced in code by the eligibility gate and in tests by the public-boundary suite.

## Roadmap principles

1. Do not become an EOL database.
2. Do not become another generic SCA.
3. Do not add collectors just to increase source count.
4. Prefer discovered non-lifecycle intelligence over curated examples.
5. Evidence must explain every material conclusion.
6. Identity must precede impact.
7. Applicability must precede action.
8. Unknown must remain unknown.
9. Public intelligence must not imply user impact.
10. Lead time must be measured from first trustworthy detection.
11. Reports are a product experience, not an implementation dump.
12. Do not add AI reasoning to the trusted decision path.
13. Avoid architecture expansion when the existing pipeline is sufficient.
14. Hypotheses are labelled as such; validated claims cite their evidence.

## Roadmap metrics

Banned as primary success metrics: projects monitored, collectors, findings, lifecycle records. Research metrics instead: identity precision/recall, applicability precision/recall, false-impact and false-clear rates, unknown rate, weak-evidence holdback rate, evidence completeness, temporal accuracy, first-detection accuracy, automatically discovered and verified events, user-confirmed affected events. Do not market these until the methodology is stable.

## Research artefacts per milestone

Every major milestone produces at least one of: benchmark, dataset, schema, evidence contract, case study, reproducibility package, technical report, academic paper, reference implementation. This is what makes OpenPulse a research instrument, not a prototype.

## External developments review (2026-10-28)

Checked against recent research and open-source tools. Items are adopted only where they strengthen an existing layer; nothing here reopens the rejected list (EOL database, generic SCA, collector count, opaque scores, AI in the trusted path).

- [NEXT, after v0.7.0] **E1 — External applicability evidence (VEX) input** (layer 4). Consume OpenVEX and CycloneDX VEX statements, and the output of ecosystem reachability tools such as `govulncheck`, as a separately labelled evidence class. Such evidence may support NOT_AFFECTED only with its provenance attached; its absence leaves the verdict as it was. OpenPulse runs no call-graph or reachability analysis of its own. Why: [Ourari, ICSME 2026](https://arxiv.org/abs/2609.08810) names "is the vulnerability actually exploitable?" as a key measurement gap. Accepting other tools' evidence closes part of it without building an SCA engine.
- [NEXT] **E2 — Dependency-path context from SBOM graphs** (layer 8). When an SBOM declares its dependency graph (CycloneDX `dependencies`, SPDX relationships), record whether the affected component is direct or transitive, and the path to it. Never infer a graph the input does not state. Why: the same agenda identifies transitive modelling as a weakness; the path is context for the warning, not a new verdict.
- [NEXT, M8; folded into track T as T-A1 on 2026-10-31] **E3 — "Not found in registry" ≠ "not catalogued"** (layer 3, MCP channel). `dependency_status` distinguishes a package or version that does not exist in its registry from one OpenPulse has no intelligence on. Coding agents propose non-existent versions often enough to matter (secondary reporting of an Endor Labs study), and a non-existent package is an identity fact, not an UNKNOWN. No malicious-package scoring: that belongs to tools such as OpenSSF Package Analysis and GuardDog.
- [RESEARCH, M9] **E4 — Dependency-decision experiment design** (layer 9/10). Arms: agent alone; agent plus conventional vulnerability scanning (OSV-Scanner); agent plus OpenPulse; agent plus SafeAI authority evidence, only where the candidate is itself an AI component (MCP server, agent framework); combined. Score against what happened after the decision date (later advisories, deprecation, archival, end of life), using retrospective evidence snapshots, with model training cut-offs recorded to control leakage. Also measure unnecessary additions, reuse of existing dependencies, policy compliance and functional success, so that blocking useful changes counts against a condition. Align the task format with [DepDec-Bench](https://arxiv.org/abs/2601.00205) once it is released (no public code or dataset as of 2026-10-28; paper under review at JAWS 2026).
- [VALIDATION, M4] **E5 — Comparator runs on the benchmark.** Run xeol, OSV-Scanner and plain endoflife.date lookups on the 11 formalized scenarios. Report where their verdicts differ from OpenPulse's on identity and applicability (false-impact, false-clear, unknown), not on feed coverage.

Considered and not adopted: dependency-discovery benchmarking (inventory generation is Syft's and the SBOM producer's job; OpenPulse consumes inventories); vulnerability-feed accuracy and freshness as a product metric (a property of OSV and NVD, not a differentiator — temporal coverage stays the P0 audit item); a reachability or call-graph engine (generic SCA); malicious-package detection. Track T below keeps that decision: it cites confirmed-malicious records published by others and reports transparent indicators, but it does not detect malware.

## Track T — AI Dependency Trust Assurance: Know Why You Trust Your Dependencies
STATUS: FUTURE (planned 2026-10-31; a separate future study; nothing in this section is implemented)

**The question.** When a person or a coding agent is about to add a dependency, what evidence shows that:

- the package is the one intended;
- the artifact is the one its source built;
- its reputation signals have not been manufactured?

And which of these did nobody check at all?

Track T extends layers 2 (evidence), 3 (identity) and 9 (AI-mediated change). It is planned as its own study, with its own design, registration and evaluation.

**Relationship to track R.** Track T does not touch track R. It is not part of the TR-2026-01 registration: the registration's §13 already lists discovery and the agent interface as outside that study. It does not change R's hypotheses, thresholds, population, scope or precedence. Since 2026-11-01, product work no longer waits for the journal submission: track T starts with Phase 0 below, which is design and desk research only.

Three rules apply to later T code:

- It must not change any `check_dependency` verdict. T's outputs are new, separately labelled fields.
- It must not modify the frozen implementation or `evaluation/`.
- It competes with R for reviewer time, so R wins.

**Positioning.** OpenPulse stays evidence-based dependency intelligence. Track T makes it complement OSV, the registries, Sigstore, SLSA, SBOM tools and malware scanners. It does not replace any of them.

Track T does **not** make OpenPulse any of the following:

- a malware scanner;
- an SCA replacement;
- a reputation service;
- a safety guarantee;
- an AI governance platform;
- a black-box trust score.

There is no composite score and no SAFE status. Every statement names the check that produced it, its source and when it ran. Principle 12 holds: no model sits in the trusted decision path, and no model sits in the enforcement path either.

### Available today vs planned (verified against `main` @ `f16c8aa`)

| Capability | Today | Planned in track T |
|---|---|---|
| Package identity | Curated catalog with per-ecosystem `packages` and VERIFIED / REVIEW_REQUIRED / UNVERIFIED status (`core/entities/identity.py`, `core/entities/catalog.py`). An uncatalogued package is unresolved, not cleared (F1–F4). | Registry existence (T-A1), lookalike indicators (T-A2), dependency confusion (T-A3), repository linkage (T-A4) |
| Registry facts | Docker Hub only (`collectors/registries/docker.py`). Attestation and signature tags are excluded from observations, not verified. No PyPI or npm registry collector exists. | PyPI and npm registry metadata, for T-A and T-B only |
| Artifact provenance | None. Signature fields in the evidence contract are always `null`. OpenPulse's own release signing (`docs/NEXT_PHASES.md` D2) is a separate item about OpenPulse's own supply chain. | Verification of PyPI (PEP 740) and npm attestations, and lockfile digests (T-B) |
| Malicious-package records | Not distinguished. OSV is queried only for catalogued packages, and an OSV `MAL-` record would be counted as an ordinary advisory. | A CONFIRMED_MALICIOUS status that cites the record (T-F1). Detection stays out of scope. |
| Reputation | GitHub repository metadata (archived flag, last push, license), shown as context and never used in the verdict | Transparent indicators (T-C) |
| Agent interface | `dependency_status`, `check_dependency_file` and `project_lifecycle`: read-only, confined to the server root, with a freshness bound (PR #200), `verdict.meaning` and `not_established` (`core/agent_tools.py`, `docs/MCP.md`) | An additive trust-evidence block in the same tools (T-D) |
| Enforcement | `openpulse check --fail-on` / `--fail-on-partial` and the GitHub Action. They gate on lifecycle and applicability verdicts only, after resolution, not before installation. | Policy conditions on trust statuses, then pre-installation controls (T-E) |
| Evidence contract | 1.2.0, with closed vocabularies (`verdict_meaning`) and an additive versioning policy (`docs/EVIDENCE_CONTRACT.md`) | A trust-assurance block in a new minor version (T-F2) |
| Untrusted text | `verdict_meaning.statement` and the MCP `note` are fixed templates. Advisory text is not passed to agents (ids and URLs only). Engine `reason` strings do interpolate caller- and event-supplied strings (package names, scope values). | A rule for untrusted text, tested with injection fixtures (T-F3) |

### Initial threat model

The table separates two things: whether a technique has been **demonstrated** (incidents or published research), and whether its **prevalence** has been measured. Prevalence among agent-selected dependencies is unmeasured for every row. That is a research question here, not an assumption. The references were re-verified on 2026-11-01 in the Phase 0 review (`docs/research/TRACK_T_PHASE0.md`, section 1), which also lists newer sources.

| # | Threat | Demonstrated? | Prevalence | What OpenPulse could establish | Workstream |
|---|---|---|---|---|---|
| T1 | Typosquatting and lookalike names (edit distance, homoglyphs, separators, npm scopes) | Yes: repeated registry takedowns | Measured for some registries by others; unmeasured for agent selection | The candidate resembles a named reference package, and by which rule. It cannot establish intent. | T-A2 |
| T2 | Hallucinated package names that an attacker can register ("slopsquatting") | Hallucination rates measured in a lab study (Spracklen et al., USENIX Security 2025). Registration by attackers: isolated vendor reports (e.g. Koi PhantomRaven, Oct 2025), intent inferred; `huggingface-cli` (Lasso, 2024) was a researcher's benign test. | In-the-wild exploitation unmeasured | The name or version did not exist in the registry at time *t* | T-A1 |
| T3 | Dependency confusion (a public package shadows an internal name) | Yes (Birsan, 2021) | Unmeasured here | A name on the user's private list also exists publicly | T-A3 |
| T4 | Starjacking: registry metadata claims a popular repository | Yes (reported by Checkmarx, 2022) | Unmeasured | The claimed repository does or does not name the package back, or provenance binds the artifact elsewhere | T-A4, T-B |
| T5 | Manufactured reputation (fake stars, download inflation) | Fake stars measured on GitHub (He et al., ICSE 2026, "Six Million (Suspected) Fake Stars in GitHub"; the 2024 preprint said 4.5 million) | Effect on agent or human selection unmeasured | Indicator facts (bursts, inconsistent signals) with their inputs. Never a verdict of manipulation. | T-C |
| T6 | Maintainer account or token takeover, then a malicious release | Yes (for example ua-parser-js, 2021; the npm "Shai-Hulud" worm, 2025) | Incident counts only | A maintainer-set change since the last observation; a release built outside the attested workflow | T-C, T-B |
| T7 | A compromised build or publish pipeline produces malicious artifacts with valid provenance | Yes (for example Ultralytics, Dec 2024: the first malicious releases went out through the project's own Trusted Publishing workflow) | Incident counts only | Little. Provenance shows where and how an artifact was built, not that it is benign. This limit is stated in every provenance answer. | T-B (limit) |
| T8 | An artifact is substituted between build and install (digest mismatch, mirror tampering) | The technique is known. Major registries serve over TLS with hashes. | Unmeasured | The lockfile digest does or does not equal the registry digest; a signature does or does not verify | T-B4 |
| T9 | A long-term malicious maintainer (xz-utils, 2024) | Yes | Rare and unmeasured | **Out of reach.** Identity, provenance and reputation would all look legitimate. This is stated, not hidden. | none |
| T10 | Instructions injected through package metadata, READMEs or advisory text, read by an agent | Indirect prompt injection is demonstrated in research (issues, READMEs, docs). For package metadata specifically: proofs of concept; no documented in-the-wild agent compromise. | Unmeasured | That upstream text never reaches fixed-template fields | T-F3 |
| T11 | An agent ignores, skips or is talked out of an advisory warning | Expected: advisory output has no enforcement | Unmeasured (RQ4, RQ5) | Nothing by itself. This is why T-E works without the model. | T-D, T-E |
| T12 | Attacks on OpenPulse's own evidence: poisoned reference lists, stale caches, forged records | In scope under `SECURITY.md` | n/a | Pinned and hashed reference snapshots; freshness bounds; existing history integrity (Anchored Trust) | T-F |

Two rules apply to every row:

- **Missing evidence is never proof of malice, and never proof of safety.** Most packages publish no attestation today, so a missing attestation is MISSING_EVIDENCE, not a failure.
- **"No known vulnerabilities", UNKNOWN and NOT_PERFORMED are never "safe".**

### Workstreams

IDs use a `T-` prefix so they don't collide with the `docs/NEXT_PHASES.md` items (A6b, B1–B7, C1–C5, D1–D6).

**T-A — Package Identity and Impersonation Intelligence (P0; layer 3).** Builds on the curated catalog, PEP 503 and Maven canonical names (F2), purl qualification (F3), and the unresolved-identity rule (F4, D10).

- **T-A1 Registry existence** (absorbs E3). The states are:
  - the package exists;
  - the version exists;
  - verified absent from registry R at time *t*;
  - registry unreachable, which is NOT_PERFORMED.

  PyPI and npm come first, through their JSON APIs. crates.io, the Go module proxy and Maven Central follow after Phase 0 checks their APIs. An absent package is an identity fact, not an UNKNOWN and not evidence of malice.
- **T-A2 Lookalike indicators** against two references: the curated catalog and a pinned, hashed snapshot of popular package names per ecosystem. Where the snapshot comes from, and its licence, are decided in Phase 0. The rules are:
  - normalised-name collision;
  - bounded edit distance;
  - Unicode confusable skeletons (UTS #39);
  - separator and scope confusion;
  - the same name in another ecosystem.

  Each result names the reference matched and the rule that matched it. A lookalike is an indicator, never a "typosquat" verdict.
- **T-A3 Dependency confusion.** The user lists private names, and OpenPulse reports which of them exist publicly. Nothing is inferred about names the user did not list.
- **T-A4 Repository linkage.** Does the repository named in the registry metadata name the package back, or does verified provenance (T-B) bind the artifact to that repository? This addresses starjacking.

**T-B — Artifact Provenance and Integrity (P0; layers 2–3).** Verification uses existing libraries and never a cryptographic implementation of our own. The candidates are `sigstore` (sigstore-python) and `pypi-attestations`. They would be an optional extra (for example `[provenance]`), hash-locked, and need explicit sign-off as new runtime dependencies (`docs/NEXT_PHASES.md` rules).

- **T-B1 PyPI, first.** Fetch PEP 740 attestations from the PyPI Integrity API. Verify them against the Trusted Publisher identity (repository, workflow, ref) and the distribution's digest.
- **T-B2 npm, first.** Fetch the registry's provenance attestations (Sigstore bundles carrying SLSA provenance) and verify them with the same library. Phase 0 confirms that sigstore-python verifies npm's bundles without a Node toolchain; if it can't, T-B2 waits.
- **T-B3 Containers, second.** cosign signatures and OCI referrers, plus GitHub artifact attestations, for the images that image inventories already list.
- **T-B4 Digest integrity**, independent of attestations. Lockfile hashes (`poetry.lock`, `package-lock.json` `integrity`, pip `--hash`) are compared with registry-published digests. A mismatch is a VERIFIED_FAILURE.
- **Later, after Phase 0 assesses them:**
  - Maven Central: Sigstore signatures are optional and PGP is common;
  - Go: the checksum database establishes integrity, not build provenance;
  - crates.io and RubyGems: attestation support is to be confirmed.
- **Stated limit (T7):** a verified relationship says where and how an artifact was built. It never says the artifact is benign.

**T-C — Reputation Integrity and Manipulation Detection (P1; layer 2).** Transparent, explainable indicators come first. Each one has a written rule, its inputs and its source, for example:

- star-history bursts;
- stars inconsistent with downloads or dependents;
- a young repository with claimed popularity;
- a maintainer-set change since the last observation (reusing the observation history);
- a repository transferred or renamed (reusing discovery).

Indicators are reported one by one. They are never summed into a score. Popularity is never evidence of trustworthiness, and the absence of indicators is never evidence of authenticity. **No statistical or ML detection** until an evaluation plan with labelled data exists (see the evaluation plan below). An indicator without a measured false-positive rate on organic projects is labelled experimental. GitHub's API budget limits how much star history can be read, so T-C runs on demand, not in a sweep.

**T-D — AI Dependency Selection Evidence (P1; layer 9).**

- **The same tools, extended.** `dependency_status` and `check_dependency_file` gain an additive trust-evidence block: T-A, T-B and T-C results, each with a T-F1 status. A new tool is justified only if M8's opt-in usage records show agents comparing candidates in a way the existing tools can't serve, for example a `compare_candidates` call.
- **The agent's reasoning is never inferred.** An optional, caller-supplied `selection_context` (stated intent, where the package name came from) is recorded verbatim and labelled agent-supplied. It is never used in any status or verdict.
- **The freshness bound applies** to trust evidence as it does to verdicts (`evaluation_context`).
- **Data source.** The M8 opt-in, local recording of questions and answers is the data source for RQ1 and RQ4.

**T-E — Policy Enforcement and Pre-Installation Controls (P1 for T-E1, P2 for T-E2; layers 9–10).** Advisory MCP warnings are **not a security boundary**: an agent can skip the call, ignore the answer, or be steered away from it by injected text (T11). Enforcement therefore runs without the model.

- **T-E1 (P1): declarative policy conditions.** The conditions are evaluated deterministically by `openpulse check` and the GitHub Action, extending `--fail-on`. Examples:
  - `confirmed_malicious`;
  - `verified_failure`;
  - `not_found_in_registry`;
  - a user blocklist;
  - provenance required for a named set of packages.
- **T-E2 (P2): pre-installation controls** at existing integration points:
  - a CI step on the lockfile diff before `npm ci` or `pip install`;
  - a pre-commit hook on lockfiles.

  A registry proxy or firewall is out of scope, because it is a product category of its own.
- **Failing closed.** Policy fails closed **only for explicitly prohibited conditions**. SUSPICIOUS_INCONCLUSIVE, MISSING_EVIDENCE and NOT_PERFORMED warn by default. They block only where the user's policy explicitly prohibits them for a named scope, which makes that rule the explicit prohibition. No default ever blocks on missing evidence.
- **Boundary.** OpenPulse enforces conditions on its own evidence only. Whether an agent may make a change at all belongs to SafeAI and the future assurance-policy layer (see the SafeAI / OpenPulse boundary above).

**T-F — Evidence Contracts and Auditability (P0 for T-F1 and T-F3, P1 for T-F2 and T-F4).**

- **T-F1 (P0): a closed status vocabulary** for every trust check, with no SAFE value:

  | Status | Meaning |
  |---|---|
  | CONFIRMED_MALICIOUS | A cited authoritative record says so, such as an OSV `MAL-` entry or a registry security takedown. OpenPulse never assigns it on its own indicators. |
  | VERIFIED_FAILURE | A check ran and failed: a signature that doesn't verify, a digest mismatch, a provenance identity that differs from the expected repository or workflow. |
  | SUSPICIOUS_INCONCLUSIVE | One or more indicators fired, without confirmation. |
  | MISSING_EVIDENCE | The check ran, but there was nothing to verify (for example, no attestation published). |
  | VERIFIED_RELATIONSHIP | The check ran and the binding holds: the package exists, or the artifact is bound to its source and workflow. |
  | NOT_PERFORMED | The check did not run: an unsupported ecosystem, offline mode, an unreachable source, or an exhausted budget. |

  The design aligns this vocabulary with the existing `not_evaluated` value of `verdict_meaning`.
- **T-F2 (P1): contract block.** A `trust_assurance` block goes in a new minor contract version, in a sibling schema directory, under the existing versioning policy. It is additive, the hash computation is unchanged, and earlier schemas stay untouched. JCS hashing remains the separate 2.0.0 change. If the validator's keyword subset must grow, it grows in the same PR.
- **T-F3 (P0): untrusted text.** Registry descriptions, READMEs, advisory summaries, maintainer names and caller-supplied names are data.
  - Statements and notes stay fixed templates.
  - Upstream text appears only in explicitly labelled, length-capped fields with control characters stripped, or not at all.
  - The existing engine `reason` strings are audited for interpolated caller and event strings.
  - Tests use injection fixtures.
- **T-F4 (P1): audit record.** Every check records what was checked, against which source, when, and by which OpenPulse version. This reuses the contract's `provenance` block and the observation history. It is not a new store.

### Phases

```text
Phase 0  threat model + feasibility (docs only; can run alongside track R)
   │
   ▼
Phase 1  identity + provenance foundation: T-F1, T-F3 ─► T-A1 ─► T-B4 ─► T-B1, T-B2 ─► T-A2
   │                                    │
   ▼                                    ▼
Phase 2  reputation integrity:        Phase 3  AI decision integration:
         T-C, T-A4, T-A3                       T-D, T-F2 (uses Phase 1; Phase 2 optional)
   └──────────────┬─────────────────────┘
                  ▼
Phase 4  independent enforcement: T-E1 ─► T-E2 (needs T-F1 and measured false positives)
```

| Phase | Content | Depends on | Exit |
|---|---|---|---|
| 0 — Threat model and feasibility (draft for approval, 2026-11-01: `docs/research/TRACK_T_PHASE0.md`) | <ul><li>Re-verify the threat model's references.</li><li>Check, with dates, which registries expose attestations and which libraries verify them.</li><li>Check rate limits.</li><li>Choose the reference-list sources and their licences.</li><li>Design notes for T-F1 and T-F3.</li><li>A separate study design and registration plan.</li></ul> | none (docs only) | The owner approves the design note and the ecosystem table |
| 1 — Identity and provenance foundation | T-F1, T-F3, T-A1, T-B4, T-B1, T-B2, T-A2, with offline tests on synthetic fixtures | Phase 0; the R implementation freeze tag exists | PyPI and npm answers carry existence, digest and provenance statuses; no verdict changes |
| 2 — Reputation integrity | T-C indicators, T-A4, T-A3 | T-F1, and T-A1's registry metadata | Each indicator is documented, with a measured false-positive rate on the organic fixture set |
| 3 — AI decision integration | T-D in the MCP tools; T-F2 contract block; M8 recording | Phase 1 (Phase 2 optional) | Agent answers carry the trust block. The contract minor is published beside 1.2. |
| 4 — Independent enforcement | T-E1, then T-E2 | T-F1, Phase 1, and the false-positive results of the evaluation | Prohibited conditions block in CI without any model involved. Bypass tests pass. |

**First milestone, kept deliberately small: T-M1, "Does this package exist?"** After Phase 0, `dependency_status` answers whether a PyPI or npm package and version exist in their registry, with the T-F1 status, the registry and the time checked. It also applies the T-F3 rule to every new field.

T-M1 is limited in three ways:

- it is additive to the response, with no contract change and no verdict change;
- it has offline tests against a stub registry;
- it adds no new runtime dependency.

It is the highest-priority item in the track because hallucinated names are its demonstrated failure (T2), it needs no cryptography, and E3 already asked for it.

### Evaluation plan (proposed, for the separate study)

**Fixtures are safe and synthetic.**

- No real malware is used.
- Nothing is published to a public registry, and no live attack is run.
- Package names come from a reserved fixture namespace, served by a local stub registry.
- Attestations are generated locally or against Sigstore's staging instance.
- Star histories and maintainer changes are synthetic.

**Eight test categories:**

1. Existence: non-existent packages and versions, including hallucination-shaped names.
2. Lookalike names: edit distance, confusables, separators, npm scopes, cross-ecosystem reuse.
3. Dependency confusion: private names that also exist in the stub public registry.
4. Provenance verification: valid; invalid signature; wrong repository or workflow identity; no attestation; unsupported ecosystem.
5. Digest integrity: a lockfile digest that differs from the registry digest.
6. Reputation manipulation: star bursts, starjacked repository links, maintainer changes, plus an organic control set for false positives.
7. Untrusted text and injection: metadata carrying instructions, control characters and markup.
8. Enforcement and bypass: policy on lockfile diffs; installs outside the gate; edited lockfiles; an agent ignoring a warning.

Every category also runs degraded (offline, rate-limited, registry unreachable), where the expected result is NOT_PERFORMED.

**Six baselines,** each compared with OpenPulse advisory (MCP) and with OpenPulse plus enforcement:

1. The agent alone.
2. A registry-resolution check only, such as `pip download --no-deps` or `npm view`.
3. Vulnerability scanning: OSV-Scanner, pip-audit, npm audit.
4. Native ecosystem verification: `npm audit signatures`, `pypi-attestations verify`, `gh attestation verify`, cosign.
5. Dedicated malicious-package tools as comparators: the OpenSSF malicious-packages data through OSV, and GuardDog.
6. A simple popularity or allowlist heuristic.

**Metrics:**

- **Selection rate:** the share of tasks in which the agent chooses a prohibited, non-existent or lookalike candidate.
- **Detection rate,** per category.
- **False-positive rate:** legitimate packages flagged.
- **Acceptance rate:** legitimate changes allowed. Blocking useful work counts against a condition, as in E4.
- **Provenance accuracy:** the status matches ground truth across valid, invalid and missing.
- **Anomaly precision and recall** for T-C indicators.
- **Agent compliance:** warnings acted on.
- **Enforcement rate** and **bypass rate.**
- **Latency:** p50 and p95 per dependency and per file.
- **Unresolved rate:** the share of assessments that end NOT_PERFORMED, MISSING_EVIDENCE or SUSPICIOUS_INCONCLUSIVE.

**Research questions.** These are proposed questions, not findings:

- **RQ1.** How often do coding agents select non-existent, lookalike or confusable packages in realistic tasks? Does registry-existence and identity evidence reduce that rate?
- **RQ2.** For which ecosystems, and for what share of a realistic dependency set, can provenance be verified today? How often does verification resolve, and how often does it end in missing evidence?
- **RQ3.** Do transparent reputation indicators separate manipulated from organic projects with useful precision and recall on labelled data?
- **RQ4.** Do agents act on structured trust evidence delivered through MCP? Do closed vocabularies and fixed templates improve compliance, and resistance to injected metadata, compared with free text?
- **RQ5.** Compared with advisory output alone, does model-independent enforcement reduce prohibited installs? At what cost in false blocks and latency, and by which routes is it bypassed?

This study can share infrastructure with E4, the dependency-decision experiment design, but it is designed and registered separately. M9 stays deferred.

### Open questions for Phase 0

- Whether sigstore-python can verify npm provenance bundles directly, and what the current state of attestations is on crates.io, RubyGems and Maven Central.
- Where an openly licensed, reproducible list of popular package names per ecosystem comes from, and how often it must be refreshed.
- What GitHub API budget star-history indicators need, and whether a token is required.
- Whether trust checks should run on every dependency of a file check, or only on additions (lockfile diffs). The latter fits the existing 40-project live budget.
- Who labels the reputation set (RQ3), and on what basis.
- How the T-F1 statuses map onto SARIF, DefectDojo and Dependency-Track severities without implying a risk score.

## Item dispositions (reconciled 2026-10-04)

- DONE → M1 maintenance: schema, gate, identity trust, match/evidence split, hash-chained observations, lead-time semantics, Windows CI, SBOM archiving, metadata sidecar.
- DONE 2026-10-07: M2 acceptance set closed (5 live-replayed cases: capa, etcd, traefik, fbsdk archive+move, bitnami/spark empty mainline). The namespace-move detector (`split_moves`) still awaits a live firing.
- VALIDATION: M4 at 11 formalized scenarios; benchmark expansion remains research work.
- DONE: M5 dependency inputs converge on one verdict engine, including GitHub repositories.
- ACTIVE: M6 warning engine, durable detection, digest and webhook delivery; remaining work is persistent delivery state, deduplication/retry policy, scheduling and CI/PR integration.
- NEXT: external-consumer validation of evidence contract v1, then cryptographic contract v2 only after semantic stability.
- FUTURE/RESEARCH: M6 hosted surfaces, M7 network, M8 direction, M9 experiment.
- REMOVED: v0.x phase plan (superseded 2026-10-02), hard-coded test-count headers (CI reports the count), Next-90 items completed since (SBOM reader, detection ledger, OSV live wiring).
- OBSOLETE as product scope: generic SCA matching, auto-remediation, dashboard complexity, AI-generated conclusions.
- DONE 2026-10-19: repository coverage assurance (v0.6.0, #100) - blob-SHA-pinned GitHub inspection with COMPLETE/PARTIAL/FAILED coverage, evidence contract v1.1.
- DONE 2026-10-21: v0.6.1 correctness slice - namespaced pom.xml (#112), registry-port identity (#113), webhook secret redaction (#115), OS advisory locks (#116), GitHub-repo SBOM ingestion (#117), bounded reads (#118), identifier validation (#119), `SECURITY.md` (#120), certifi PYSEC-2026-4320.
- DONE 2026-10-28: collector response caps (A6b, #155) and hash-locked installs (#110, #156). NEXT: v0.9.0 Anchored Trust before M6 runs unattended - see `docs/NEXT_PHASES.md`.
- DONE 2026-11-01: v0.9.0 "Anchored Trust" - derived authority (#224) and independence (#227), clock trust (#223), keyed history with rotation and adoption (#229-#232, #235), rollback and downgrade detection (#233), anchors (#234), evidence contract 2.0.0 (#236).
- NEXT 2026-11-01: v0.11.0 "Early Warning Operations" (M6 un-paused): persistent alert delivery with dedup, retry and dead-letter (#78), a `warnings` severity gate, signed webhooks, MCP hardening, and track T Phase 0 - see `docs/NEXT_PHASES.md` Phase 5.
- DONE 2026-11-01: v0.10.0 "Verified Releases & Safe Gates" (#240-#249): attested tag-triggered releases (#111), gates that fail on FAILED coverage (#101), `NOT_APPLICABLE` coverage (#109, #102), DNS-pinned webhooks (M5) and hardening issues - see `docs/NEXT_PHASES.md` Phase 3. Product work continues alongside track R (amendment 2026-11-01).

## Next 8–16 weeks (re-baselined 2026-10-30; supersedes the 2026-10-21 list)

This is a planning estimate, not a commitment: independent labelling and ground-truth construction may take longer.

1. **Weeks 1–2:** publish TR-2026-01 as a technical report with its current claims. Register the protocol (R-A2). Fix F1 (R-B3). Build the strong baseline (R-B4) and the identity ablation (R-B5). Recruit annotators and an independent oracle author (R-B7, R-C2).
2. **Weeks 2–6:** contract negative-meaning fields (R-B6). Independent oracle and edge-case set (R-B7). Freeze the implementation and tag it. Start the prospective event window (R-C1).
3. **Weeks 6–12:** independent labelling (R-C2), the comparison and ablations (R-C3), discovery precision and recall (R-C4).
4. **Weeks 12–16:** paper revision and reproducibility package (R-D).

Superseded items from the 2026-10-21 list: v0.9.0 Anchored Trust moves after R-C. M6 operationalisation is PAUSED. The M4 benchmark harness is superseded by R-B1, the evaluation harness. Real non-lifecycle discovery (M2) continues only where it feeds R-C1.

Do not add unrelated features. This roadmap exists to stop OpenPulse from becoming a feature-rich data aggregator and instead drive it toward a defensible dependency-intelligence product and a credible research instrument.

# OpenPulse Roadmap — re-baselined 2026-10-04 for the Ikarus AI Labs research programme

> OpenPulse is the Software Ecosystem Evidence Plane within the [Ikarus AI Labs research programme](https://ikaruslabs.net/research) on Evidence-Based Assurance for AI-Mediated Software Change.
>
> OpenPulse investigates how software organisations can establish trustworthy evidence about changes occurring in the open-source ecosystem, determine whether those changes apply to their dependencies, and provide timely, explainable warnings.
>
> SafeAI independently investigates the Agent Authority Evidence Plane: what authority an AI agent can potentially exercise and how that authority changes.
>
> A future research direction is to connect these evidence planes and investigate whether combined evidence can improve decisions about AI-mediated software changes.

Use this framing without claiming that the combined model is already proven. The combined assurance experiment is hypothesised, not established.

Status (2026-10-30): research track R (below) takes precedence until the TR-2026-01 journal submission. Earlier status (2026-10-28): v0.7.0 "Channels" released (MCP server for AI coding agents, DefectDojo export, Dependency-Track upload, release-line verdict fix #133, install name `ikarus-openpulse`); v0.7.1 adds collector response caps (#155) and hash-locked installs (#156); Phase A correctness and leak fixes merged (#112, #113, #115–#120); intelligence schema 0.5.0, evidence contract v1.1, CI on Linux + Windows, deterministic SBOM archived. Test count is reported by CI. Next phases: `docs/NEXT_PHASES.md`. This reset supersedes the 2026-10-02 M1–M8 sequence: the milestones below re-baseline it against implementation reality and the research programme, they do not discard it.

Status words used in this document: DONE, ACTIVE, VALIDATION, NEXT, FUTURE, RESEARCH, PAUSED. Research claims are additionally qualified as observed, implemented, validated, hypothesised, or planned — hypotheses are never described as established capabilities.

## Re-baseline 2026-10-30: research track R takes precedence

An external recommendation on TR-2026-01 (assessment: `papers/tr-2026-01/RECOMMENDATION_ASSESSMENT.md`) concludes that the report is a sound specification and implementation audit, but not yet a competitive journal submission. Its missing piece is evidence that completeness-aware decisions are *better* than simpler alternatives. We accept that conclusion. Until the journal submission, **track R below is the priority**. Everything else is either a prerequisite for R or waits.

- Target: "Level 2", an empirically strengthened manuscript. It needs a precise contribution, independent validation, labelled historical cases and a comparative evaluation. Level 3 (multiple ecosystems, longitudinal and practitioner studies) is not a prerequisite.
- TR-2026-01 itself may be published now as a technical report, with its claims as they stand. The journal version waits for R-C.
- Rule for R: build only what an experiment needs. Every R item names the research question it serves. Product features that serve no R question wait.

### R-A — Research design (contribution and protocol)
STATUS: ACTIVE

- [ACTIVE] **R-A1:** State the contribution as a testable model: when a negative applicability verdict is justified (scope typing, completeness with a basis, exact vs envelope, identity, freshness). Claim the model and its evaluation. Do not claim completeness reasoning or three-valued logic as new.
- [NEXT] **R-A2:** Register the evaluation protocol (`evaluation/PROTOCOL.md`) as an archived, dated version before any held-out label exists. It must record the primary endpoint (FCR_affected non-inferiority against the strong baseline, plus superiority on resolution rate), numeric margins, the power justification for the number of events, and the freeze date.
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
- [NEXT] **F2:** a package-scope membership rule outside the specification. The engine counts a package as a member of a package scope when the scope's list contains the package's project slug. SPEC §4.4 and TR §5.3 give membership only on name equality, and **?** otherwise.
  - Package curation made it visible: every curated iText module is AFFECTS_PACKAGE under the iText licence event (it-02, it-03), so V and C now differ on them.
  - The conformance gate missed it, because every package name in its vocabulary equals its project slug.
  - It is not a false clear, but it turns a list entry into a project-wide positive, which TR §5.4 (P3) allows only from exact elements.
  - Decision needed, as one trust-core PR: either specify it (a package-scope value naming the project denotes every curated package of the project) or remove it, together with canonical Maven name comparison (`group:artifact` = `group/artifact`).
  - In both cases, add vocabulary cases where a package's name differs from its project's slug.
- [DONE 2026-10-30] **R-B4:** Strong conservative baseline V (`evaluation/strong_baseline.py`): the same typed scopes, admissibility and curated identities as C, exact identity only, `packaging` for PyPI, and plain numbers elsewhere. On the development set it differs from C on 1 of 60 pairs, so the contribution to claim is the model, not the engine. Remaining: pin node-semver, Go `x/mod/semver`, Maven `ComparableVersion` and `dpkg` comparators before the freeze.
- [DONE 2026-10-30] **R-B5:** Identity ablation as an explicit, call-scoped engine parameter: `check_dependency(unresolved_identity="unrelated")`. On the development set it cuts abstention from 0.47 to 0.18 at the cost of silent misses on 3 of 27 in-scope pairs, which is the measured coverage cost of D10.
- [DONE 2026-10-30] **R-B6:** Decisions expose their limitations. Evidence contract 1.2.0 adds `verdict_meaning` (direct scope, plus embedded components, availability, maintenance and security consequence, all `not_evaluated`, and a fixed statement with no upstream text), `scope.completeness` (state, basis, admits_negative) and `evaluation_context` (freshness bound and identity policy). The MCP response carries the same `verdict.meaning`, and its fixed note now qualifies NOT_AFFECTED too. The evaluation's evidence-completeness metric reads these contract fields. The JCS hash moves to contract 2.0.0, because hash changes are breaking under the versioning policy.
- [NEXT] **R-B7:** Independent specification check. Hand a second engineer the specification text, Algorithm 1 and the membership tests, but not the code. They write their own oracle and an edge-case set with expected outcomes and rationale, and we publish both, including disagreements. This addresses the circularity of an oracle written by the team that wrote the engine.
- [LATER, only if R-C needs it] Ecosystem expansion beyond the current three change classes on two platforms.

### R-C — Empirical evaluation
STATUS: NEXT (blocked on R-A2: protocol registration)

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
| M6 SaaS surfaces, dashboards, notifications, delivery state | PAUSED | Product maturity is not evidence. Resume after R-D. |
| M7 Intelligence Network | FUTURE (unchanged) | |
| M9, and SafeAI integration in this paper | DEFERRED | It widens scope and complicates attribution. It stays a separate future study. |
| v0.8.0 Anchored Trust (keyed history, external anchoring) | NEXT after R-C | Needed for lead-time claims. The applicability evaluation does not rest on them. The paper keeps lead times as caveated observations. |
| E1–E5 external developments | E5 (comparator runs) folded into R-C3; E1–E4 LATER | |
| Security-review items (Phase B in `docs/NEXT_PHASES.md`) | Continue only where they fix a false clear or false impact | |

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
- registry observations, corruption-detecting (unkeyed hash-chained) observation history - keyed integrity and rollback detection are the v0.8.0 "Anchored Trust" work, the one M1 expansion with a concrete requirement (lead-time claims rest on this history)
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
CUSTOMER DEPENDENCY
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

## M6 — Early Warning SaaS
STATUS: PAUSED 2026-10-30 for track R (was ACTIVE / OPERATIONALIZATION)

Continuous monitoring, alerts, digests, dashboards, warning deadlines, first-detection history, event timeline, CI/PR checks. Implemented foundation: durable per-entity first-detection ledger (`core/detections/ledger.py`), lead time defined as `effective_date − first_trustworthy_detection`, never estimated, never averaged for marketing; alert digest (`core/digest.py`) and ranked warning deadlines with severity bands (`core/warnings.py`), plus replayable lead-time case studies (`docs/LEAD_TIME_CASES.md`). Commercial question stays: “What is changing in MY software?”

## M7 — Intelligence Network
STATUS: FUTURE

Emerging signals, community observations, confidence progression, cross-source triangulation, long-term history, anonymized cross-customer intelligence. Only start when customer monitoring is working.

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

Retain and formalise: observation ≠ claim ≠ event; public intelligence ≠ customer intelligence. Public intelligence must never imply customer impact without dependency evidence; an upstream event is not evidence that a specific dependency is affected. Enforced in code by the eligibility gate and in tests by the public-boundary suite.

## Roadmap principles

1. Do not become an EOL database.
2. Do not become another generic SCA.
3. Do not add collectors just to increase source count.
4. Prefer discovered non-lifecycle intelligence over curated examples.
5. Evidence must explain every material conclusion.
6. Identity must precede impact.
7. Applicability must precede action.
8. Unknown must remain unknown.
9. Public intelligence must not imply customer impact.
10. Lead time must be measured from first trustworthy detection.
11. Reports are a product experience, not an implementation dump.
12. Do not add AI reasoning to the trusted decision path.
13. Avoid architecture expansion when the existing pipeline is sufficient.
14. Hypotheses are labelled as such; validated claims cite their evidence.

## Roadmap metrics

Banned as primary success metrics: projects monitored, collectors, findings, lifecycle records. Research metrics instead: identity precision/recall, applicability precision/recall, false-impact and false-clear rates, unknown rate, weak-evidence holdback rate, evidence completeness, temporal accuracy, first-detection accuracy, automatically discovered and verified events, customer-confirmed affected events. Do not market these until the methodology is stable.

## Research artefacts per milestone

Every major milestone produces at least one of: benchmark, dataset, schema, evidence contract, case study, reproducibility package, technical report, academic paper, reference implementation. This is what makes OpenPulse a research instrument, not a prototype.

## External developments review (2026-10-28)

Checked against recent research and open-source tools. Items are adopted only where they strengthen an existing layer; nothing here reopens the rejected list (EOL database, generic SCA, collector count, opaque scores, AI in the trusted path).

- [NEXT, after v0.7.0] **E1 — External applicability evidence (VEX) input** (layer 4). Consume OpenVEX and CycloneDX VEX statements, and the output of ecosystem reachability tools such as `govulncheck`, as a separately labelled evidence class. Such evidence may support NOT_AFFECTED only with its provenance attached; its absence leaves the verdict as it was. OpenPulse runs no call-graph or reachability analysis of its own. Why: [Ourari, ICSME 2026](https://arxiv.org/abs/2609.08810) names "is the vulnerability actually exploitable?" as a key measurement gap. Accepting other tools' evidence closes part of it without building an SCA engine.
- [NEXT] **E2 — Dependency-path context from SBOM graphs** (layer 8). When an SBOM declares its dependency graph (CycloneDX `dependencies`, SPDX relationships), record whether the affected component is direct or transitive, and the path to it. Never infer a graph the input does not state. Why: the same agenda identifies transitive modelling as a weakness; the path is context for the warning, not a new verdict.
- [NEXT, M8] **E3 — "Not found in registry" ≠ "not catalogued"** (layer 3, MCP channel). `dependency_status` distinguishes a package or version that does not exist in its registry from one OpenPulse has no intelligence on. Coding agents propose non-existent versions often enough to matter (secondary reporting of an Endor Labs study), and a non-existent package is an identity fact, not an UNKNOWN. No malicious-package scoring: that belongs to tools such as OpenSSF Package Analysis and GuardDog.
- [RESEARCH, M9] **E4 — Dependency-decision experiment design** (layer 9/10). Arms: agent alone; agent plus conventional vulnerability scanning (OSV-Scanner); agent plus OpenPulse; agent plus SafeAI authority evidence, only where the candidate is itself an AI component (MCP server, agent framework); combined. Score against what happened after the decision date (later advisories, deprecation, archival, end of life), using retrospective evidence snapshots, with model training cut-offs recorded to control leakage. Also measure unnecessary additions, reuse of existing dependencies, policy compliance and functional success, so that blocking useful changes counts against a condition. Align the task format with [DepDec-Bench](https://arxiv.org/abs/2601.00205) once it is released (no public code or dataset as of 2026-10-28; paper under review at JAWS 2026).
- [VALIDATION, M4] **E5 — Comparator runs on the benchmark.** Run xeol, OSV-Scanner and plain endoflife.date lookups on the 11 formalized scenarios. Report where their verdicts differ from OpenPulse's on identity and applicability (false-impact, false-clear, unknown), not on feed coverage.

Considered and not adopted: dependency-discovery benchmarking (inventory generation is Syft's and the SBOM producer's job; OpenPulse consumes inventories); vulnerability-feed accuracy and freshness as a product metric (a property of OSV and NVD, not a differentiator — temporal coverage stays the P0 audit item); a reachability or call-graph engine (generic SCA); malicious-package detection.

## Item dispositions (reconciled 2026-10-04)

- DONE → M1 maintenance: schema, gate, identity trust, match/evidence split, hash-chained observations, lead-time semantics, Windows CI, SBOM archiving, metadata sidecar.
- DONE 2026-10-07: M2 acceptance set closed (5 live-replayed cases: capa, etcd, traefik, fbsdk archive+move, bitnami/spark empty mainline). The namespace-move detector (`split_moves`) still awaits a live firing.
- VALIDATION: M4 at 11 formalized scenarios; benchmark expansion remains research work.
- DONE: M5 dependency inputs converge on one verdict engine, including GitHub repositories.
- ACTIVE: M6 warning engine, durable detection, digest and webhook delivery; remaining work is persistent delivery state, deduplication/retry policy, scheduling and CI/PR integration.
- NEXT: external-consumer validation of evidence contract v1, then cryptographic contract v2 only after semantic stability.
- FUTURE/RESEARCH: M6 SaaS surfaces, M7 network, M8 direction, M9 experiment.
- REMOVED: v0.x phase plan (superseded 2026-10-02), hard-coded test-count headers (CI reports the count), Next-90 items completed since (SBOM reader, detection ledger, OSV live wiring).
- OBSOLETE as product scope: generic SCA matching, auto-remediation, dashboard complexity, AI-generated conclusions.
- DONE 2026-10-19: repository coverage assurance (v0.6.0, #100) - blob-SHA-pinned GitHub inspection with COMPLETE/PARTIAL/FAILED coverage, evidence contract v1.1.
- DONE 2026-10-21: v0.6.1 correctness slice - namespaced pom.xml (#112), registry-port identity (#113), webhook secret redaction (#115), OS advisory locks (#116), GitHub-repo SBOM ingestion (#117), bounded reads (#118), identifier validation (#119), `SECURITY.md` (#120), certifi PYSEC-2026-4320.
- DONE 2026-10-28: collector response caps (A6b, #155) and hash-locked installs (#110, #156). NEXT: v0.8.0 Anchored Trust before M6 runs unattended - see `docs/NEXT_PHASES.md`.

## Next 8–16 weeks (re-baselined 2026-10-30; supersedes the 2026-10-21 list)

This is a planning estimate, not a commitment: independent labelling and ground-truth construction may take longer.

1. **Weeks 1–2:** publish TR-2026-01 as a technical report with its current claims. Register the protocol (R-A2). Fix F1 (R-B3). Build the strong baseline (R-B4) and the identity ablation (R-B5). Recruit annotators and an independent oracle author (R-B7, R-C2).
2. **Weeks 2–6:** contract negative-meaning fields (R-B6). Independent oracle and edge-case set (R-B7). Freeze the implementation and tag it. Start the prospective event window (R-C1).
3. **Weeks 6–12:** independent labelling (R-C2), the comparison and ablations (R-C3), discovery precision and recall (R-C4).
4. **Weeks 12–16:** paper revision and reproducibility package (R-D).

Superseded items from the 2026-10-21 list: v0.8.0 Anchored Trust moves after R-C. M6 operationalisation is PAUSED. The M4 benchmark harness is superseded by R-B1, the evaluation harness. Real non-lifecycle discovery (M2) continues only where it feeds R-C1.

Do not add unrelated features. This roadmap exists to stop OpenPulse from becoming a feature-rich data aggregator and instead drive it toward a defensible dependency-intelligence product and a credible research instrument.

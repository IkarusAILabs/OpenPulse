# OpenPulse Roadmap — re-baselined 2026-10-04 for the Ikarus AI Labs research programme

> OpenPulse is the Software Ecosystem Evidence Plane within the [Ikarus AI Labs research programme](https://ikaruslabs.net/research) on Evidence-Based Assurance for AI-Mediated Software Change.
>
> OpenPulse investigates how software organisations can establish trustworthy evidence about changes occurring in the open-source ecosystem, determine whether those changes apply to their dependencies, and provide timely, explainable warnings.
>
> SafeAI independently investigates the Agent Authority Evidence Plane: what authority an AI agent can potentially exercise and how that authority changes.
>
> A future research direction is to connect these evidence planes and investigate whether combined evidence can improve decisions about AI-mediated software changes.

Use this framing without claiming that the combined model is already proven. The combined assurance experiment is hypothesised, not established.

Status (2026-10-25): v0.6.3 released; on `main` since then: wheel data packaging (#132), release-line scope fix (#133), MCP server for AI coding agents, DefectDojo export and Dependency-Track upload (#134–#136, landed via the recovery PR); Phase A correctness and leak fixes merged (#112, #113, #115–#120); intelligence schema 0.5.0, evidence contract v1.1, CI on Linux + Windows, deterministic SBOM archived. Test count is reported by CI. Next phases: `docs/NEXT_PHASES.md`. This reset supersedes the 2026-10-02 M1–M8 sequence: the milestones below re-baseline it against implementation reality and the research programme, they do not discard it.

Status words used in this document: DONE, ACTIVE, VALIDATION, NEXT, FUTURE, RESEARCH. Research claims are additionally qualified as observed, implemented, validated, hypothesised, or planned — hypotheses are never described as established capabilities.

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
STATUS: ACTIVE / OPERATIONALIZATION

Continuous monitoring, alerts, digests, dashboards, warning deadlines, first-detection history, event timeline, CI/PR checks. Implemented foundation: durable per-entity first-detection ledger (`core/detections/ledger.py`), lead time defined as `effective_date − first_trustworthy_detection`, never estimated, never averaged for marketing; alert digest (`core/digest.py`) and ranked warning deadlines with severity bands (`core/warnings.py`), plus replayable lead-time case studies (`docs/LEAD_TIME_CASES.md`). Commercial question stays: “What is changing in MY software?”

## M7 — Intelligence Network
STATUS: FUTURE

Emerging signals, community observations, confidence progression, cross-source triangulation, long-term history, anonymized cross-customer intelligence. Only start when customer monitoring is working.

## M8 — AI-Mediated Dependency Intelligence
STATUS: RESEARCH + EARLY PREVIEW (agent channel shipped: `openpulse mcp`, see `docs/MCP.md`)

Implemented (2026-10-24): an MCP server lets coding agents query dependency evidence before they change a dependency. This keeps the principle below intact: the agent *consumes* OpenPulse evidence, while OpenPulse's verdicts stay deterministic and evidence-gated. No AI is in OpenPulse's decision path.

Research question: how should dependency intelligence change when AI agents increasingly select, introduce, upgrade and remove software dependencies? OpenPulse contributes dependency intelligence + applicability + evidence + temporal context; SafeAI contributes agent authority + change + authority evidence. Do NOT put an AI agent in the trusted decision path; study the evidence question first.

## M9 — Evidence-Based Assurance for AI-Mediated Software Change
STATUS: RESEARCH / FUTURE (flagship experiment, hypothesised)

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
- NEXT (reconciled 2026-10-21 security architecture review): collector response caps (A6b), then v0.7.0 Anchored Trust before M6 runs unattended - see `docs/NEXT_PHASES.md`.

## Next 90 Days (reconciled 2026-10-21)

1. ~~v0.6.1 correctness/leak fixes~~ DONE 2026-10-21 — remaining: collector response caps (A6b) and tagging the v0.6.1 release.
2. v0.8.0 Anchored Trust (M1 requirement, not expansion) — derived source authority, derived independence, keyed history integrity with rollback detection and external anchoring, portable (JCS) contract hashing. Lead-time claims cite keyed-valid detections only.
3. Early-warning operationalization (M6) — persistent delivery state, deterministic deduplication/retry policy, DNS-pinned webhook transport, CI/PR integration. Builds on item 2.
4. Real non-lifecycle discovery (M2) — a live namespace-move pair for `split_moves`; repository/archive and support/license candidates per the backlog.
5. Benchmark harness (M4) and release supply chain — per-scenario reproducibility package; hash-pinned lock, signed releases with provenance.

Do not add unrelated features. This roadmap exists to stop OpenPulse from becoming a feature-rich data aggregator and instead drive it toward a defensible dependency-intelligence product and a credible research instrument.

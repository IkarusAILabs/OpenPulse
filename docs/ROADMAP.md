# OpenPulse Roadmap — re-baselined 2026-10-04 for the Ikarus AI Labs research programme

> OpenPulse is the Software Ecosystem Evidence Plane within the [Ikarus AI Labs research programme](https://ikaruslabs.net/research) on Evidence-Based Assurance for AI-Mediated Software Change.
>
> OpenPulse investigates how software organisations can establish trustworthy evidence about changes occurring in the open-source ecosystem, determine whether those changes apply to their dependencies, and provide timely, explainable warnings.
>
> SafeAI independently investigates the Agent Authority Evidence Plane: what authority an AI agent can potentially exercise and how that authority changes.
>
> A future research direction is to connect these evidence planes and investigate whether combined evidence can improve decisions about AI-mediated software changes.

Use this framing without claiming that the combined model is already proven. The combined assurance experiment is hypothesised, not established.

Status: schema 0.4.0, 409 tests, catalog at 100, CI on Linux + Windows, deterministic SBOM archived, v0.5.0 released. This reset supersedes the 2026-10-02 M1–M8 sequence: the milestones below re-baseline it against implementation reality and the research programme, they do not discard it.

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
- registry observations, tamper-evident observation history
- first-detection semantics, deterministic reports
- security hardening (SSRF policy, redaction, lock-drift check, secret tripwire)

## M2 — Real Upstream Change Discovery
STATUS: ACTIVE / HIGHEST PRIORITY

Objective: repeatedly discover meaningful non-lifecycle changes with enough evidence to survive independent validation — distribution, registry, repository/archive, maintainer/ownership, support-model, license, breaking changes, package/distribution removal, migration signals. Not more signals: the October 2026 sweep proved mechanisms fire (65 diffs, since killed as window artifacts per `docs/DISCOVERIES.md`), but M2 acceptance (5 verified reproducible cases; currently 4 of 5 — the capa and etcd ownership moves joined minio and Bitnami) is nearly met. Formalization and verification, not mechanism, is the work.

## M3 — Intelligence Report Product
STATUS: ACTIVE

The monthly briefing is a product surface (Executive Summary through Historical appendix, plus the `.meta.json` machine companion and the Lifecycle Posture view). Keep it ahead of the intelligence it carries; no new sections without a reader need. Lifecycle stays one category, never the product.

## M4 — Software Ecosystem Intelligence Benchmark
STATUS: VALIDATION (9 of 10–15 scenarios formalized: Bitnami, iText, MinIO, Django, Redis, PostgreSQL, Kubernetes, Kafka, cert-manager)

A major research milestone: the suite must test identity (upstream vs distribution vs fork vs rename vs namespace vs package vs artifact), applicability (affected / not affected / unknown), evidence (official / corroborated / emerging / unverified), time (announced / first detected / last verified / effective / reported), and discovery across change classes. Every scenario answers the eight questions (change, evidence, identity, dependency, versions/artifacts, timing, investigation, why-not-a-database-record) with a “why OpenPulse?” assertion. Still to formalise: Grafana, Terraform, one AI/ML project.

## M5 — Dependency Context & Impact Intelligence
STATUS: NEXT MAJOR PRODUCT MILESTONE

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

Shipped: YAML watchlists, CycloneDX + SPDX SBOM input (`core/sbom_reader.py`), container image inventories (`core/image_inventory.py`), lockfile input - package-lock.json/poetry.lock/Cargo.lock (`core/lockfile_reader.py`), package manifests - requirements.txt/pyproject.toml/pom.xml/go.mod/Cargo.toml (`core/manifest_reader.py`), verdicts (AFFECTED / NOT_AFFECTED / UNKNOWN with identity, evidence, applicability, confidence, timing, recommendation). Missing: GitHub repositories as inputs (package manifests shipped in `core/manifest_reader.py`). All inputs must converge on the same canonical identity and applicability semantics — never a second matching engine, never generic SCA coverage-chasing.

## M6 — Early Warning SaaS
STATUS: FUTURE

Continuous monitoring, alerts, digests, dashboards, warning deadlines, first-detection history, event timeline, CI/PR checks. Currently implemented toward it (not as it): durable per-entity first-detection ledger (`core/detections/ledger.py`), lead time defined as `effective_date − first_trustworthy_detection`, never estimated, never averaged for marketing; alert digest (`core/digest.py`) and ranked warning deadlines with severity bands (`core/warnings.py`), plus replayable lead-time case studies (`docs/LEAD_TIME_CASES.md`). Commercial question stays: “What is changing in MY software?”

## M7 — Intelligence Network
STATUS: FUTURE

Emerging signals, community observations, confidence progression, cross-source triangulation, long-term history, anonymized cross-customer intelligence. Only start when customer monitoring is working.

## M8 — AI-Mediated Dependency Intelligence
STATUS: RESEARCH (integration direction, not a product feature)

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

## Item dispositions (reconciled 2026-10-04)

- DONE → M1 maintenance: schema, gate, identity trust, match/evidence split, hash-chained observations, lead-time semantics, Windows CI, SBOM archiving, metadata sidecar.
- ACTIVE: M2 acceptance set (4/5; capa and etcd ownership moves formalized with live fixtures), the namespace-move detector still awaiting a live firing.
- VALIDATION: M4 at 9 scenarios; SPDX/lockfile/manifest inputs; per-entity ledger already shipped, SaaS surfaces absent.
- NEXT: watchlist→SBOM→manifest ingestion sequence; evidence contract v1 shipped (schemas/evidence-contract/v1, see backlog P5).
- FUTURE/RESEARCH: M6 SaaS surfaces, M7 network, M8 direction, M9 experiment.
- REMOVED: v0.x phase plan (superseded 2026-10-02), "292 tests" header (now 409), Next-90 items completed since (SBOM reader, detection ledger, OSV live wiring).
- OBSOLETE as product scope: generic SCA matching, auto-remediation, dashboard complexity, AI-generated conclusions.

## Next 90 Days

1. Real non-lifecycle discovery — close the M2 acceptance set (ownership moves formalized: capa, etcd; one more verified case needed; a live namespace-move pair still pending).
2. Report/productization — briefing stays ahead of the intelligence; evidence-contract minimal schema for machine consumers.
3. Golden benchmark — cert-manager, Kafka; start Grafana/Terraform/AI-ML.
4. Customer dependency ingestion — SPDX, lockfiles, manifests into the existing verdict engine.
5. Early-warning prototype — watchlist-scoped first-detection history already durable; add verified lead-time cases.

Do not add unrelated features. This roadmap exists to stop OpenPulse from becoming a feature-rich data aggregator and instead drive it toward a defensible dependency-intelligence product and a credible research instrument.

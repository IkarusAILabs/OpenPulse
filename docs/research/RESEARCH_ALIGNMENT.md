# Research Alignment — OpenPulse in the Ikarus AI Labs programme

Ikarus AI Labs investigates how organisations can make AI-mediated software change observable, explainable and accountable: **Evidence-Based Assurance for AI-Mediated Software Change** ([programme](https://ikaruslabs.net/research)). Its central question:

> What evidence should exist before an AI-mediated software change is allowed to proceed?

Its conceptual model has four planes: Agent Authority Evidence (SafeAI), Software Ecosystem / Dependency Evidence (OpenPulse), Assurance Policy / Decision, Human Accountability. This document states OpenPulse's place in that model. Status labels follow the roadmap rules: observed, implemented, validated, hypothesised, planned.

## Thesis

AI is becoming part of the software change process — agents independently discover, select, modify, configure and execute. Traditional assurance assumed developers make changes, humans understand them, dependencies are passive and permissions stable. None of that holds reliably anymore, so assurance must connect: who, can do what, changed what, depends on what, what evidence exists, what should happen.

## OpenPulse's role: the Software Ecosystem Evidence Plane

OpenPulse answers:

> What is changing in the software ecosystem, what evidence establishes the change, and does that evidence apply to a dependency?

Its Core product loop (implemented): upstream change → evidence → identity → applicability → dependency impact → warning window → action. Its evidence model (implemented): source signal → observed change → identity → applicability → dependency impact → assessment → recommendation — with RELATED ≠ AFFECTED, UNKNOWN ≠ NOT_AFFECTED, MATCH STRENGTH ≠ EVIDENCE STRENGTH, OBSERVATION ≠ CLAIM ≠ EVENT enforced in code and tests.

## SafeAI relationship (boundary, not merger)

SafeAI ([repo](https://github.com/IkarusAILabs/SafeAI)) is the Agent Authority Evidence Plane: what authority an AI agent can potentially exercise and how that authority changes (static analysis over capabilities, tools, MCP servers, workflows). The two instruments are intentionally separate. The research question — hypothesised, not established — is whether combining them produces better decisions about AI-mediated software change.

- SafeAI exports (their plane): agent identity, agent authority, changed authority, dependency references, policy context, evidence.
- OpenPulse exports (this plane): dependency identity, dependency context, upstream event, applicability, confidence, evidence, temporal information, recommendation.
- A future policy layer combines the two; no coupled runtime exists or is planned before the interchange contract does.

## Research questions (OpenPulse scope)

1. Can meaningful non-lifecycle upstream changes be discovered repeatedly with evidence that survives independent validation? (M2; observed: mechanisms fire; planned: 5-case acceptance set.)
2. Can applicability be determined precisely — affected vs not affected vs unknown — with measured precision/recall and bounded false-impact and false-clear rates? (M4/M5; implemented: verdict engine; planned: benchmark measurement.)
3. Can first trustworthy detection be persisted so warning windows survive across runs, and can lead time be measured without estimation? (Implemented: detection ledger, `effective_date − first_trustworthy_detection`; planned: verified case studies.)
4. Can OpenPulse evidence be consumed by a separate assurance system without understanding OpenPulse internals? (Planned: evidence contract, attestation schema.)
5. How should dependency intelligence change when AI agents select, introduce, upgrade and remove dependencies? (Research direction; the trusted decision path stays deterministic.)

## Evidence model (implemented)

Collectors (GitHub, OSV, NVD, CVE, KEV, endoflife.date, registries; all degrade gracefully) feed pure-function analysts; the evidence gate vetoes weak claims; findings carry sources, content hashes, parser versions, confidence, scope, and temporal roles (announced / first detected / last verified / effective / reported). Registry observations are hash-chained and tamper-evident; dependency verdicts separate match strength from evidence strength; identity trust states (VERIFIED / REVIEW_REQUIRED / UNVERIFIED) cap conclusions from untrusted mappings. Reports render a PUBLIC/INTERNAL/DEBUG boundary enforced by tests.

## Benchmark strategy (M4, validation in progress)

9 of 10–15 golden scenarios formalized (Bitnami, iText, MinIO, Django, Redis, PostgreSQL, Kubernetes, Kafka, cert-manager). Each answers eight questions (change, evidence, identity, dependency, versions/artifacts, timing, investigation, why-not-a-database-record) plus a “why OpenPulse?” assertion. Planned: Grafana, Terraform, one AI/ML project — each also answering the applicability metrics (precision/recall, false-impact/clear rates) as the benchmark matures from scenarios into measurements.

## AI-mediated dependency research (M8 direction, M9 experiment)

Study, don't build: how agent-selected dependencies change the selection patterns OpenPulse must watch (a first AI/ML golden scenario is the concrete entry point). The flagship experiment — dependency-only vs authority-only vs combined evidence, scored on unsafe changes detected, false positives/negatives, unnecessary reviews, explainability, completeness, unknowns, reproducibility, human effort — is hypothesised. Combined-model claims stay out of roadmaps, READMEs and reports until it runs.

## Programme principles, OpenPulse reading

Evidence over assertion (gate + provenance); provenance matters (hashes, parser versions); unknown is first-class (never silently safe); applicability matters (a finding is not an impact); deterministic where possible (no LLM in the trusted path); human accountability (recommendations, never auto-remediation); open research (schema, benchmarks, ledger formats inspectable).

# OpenPulse Roadmap — reset 2026-10-02 (supersedes the 2026-09-27 sequence)

Status: schema 0.4.0, 292 tests, catalog at 100, CI on Linux + Windows,
deterministic SBOM archived. The 2026-09 phases are retired below, not
because they failed, but because the implementation outgrew them.

## Product thesis

OpenPulse is:

“OSS Dependency Intelligence that detects upstream changes and warns
you before they become problems for your software.”

Core product loop:

UPSTREAM CHANGE → EVIDENCE → IDENTITY → CORRELATION →
DEPENDENCY IMPACT → WARNING WINDOW → ACTION

Positioning: “Watch what can change underneath your software.”

The strategic question for the next phase is:

“Can OpenPulse repeatedly discover meaningful upstream changes that a
conventional lifecycle database, vulnerability database or SCA
workflow may not surface, prove them with evidence, correctly identify
affected dependencies, and provide useful warning?”

## M1 — Trusted Intelligence Engine
STATUS: DONE

Shipped and tested:

- intelligence schema (0.4.0: taxonomy, confidence, evidence, claims, scope)
- evidence and provenance (content hashes, parser versions, veto gate)
- source authority tiers and source-family independence
- confidence semantics, with match strength vs evidence strength separated
- identity resolution and identity trust states (VERIFIED / REVIEW_REQUIRED / UNVERIFIED)
- version applicability (OSV ranges, NVD CPE ranges, KEV strength)
- registry observations: hash-chained, tamper-evident, concurrency-safe
- event correlation (lifecycle and distribution story aggregation)
- lead-time semantics (effective minus first trustworthy detection, never estimated)
- dependency matching with explicit NOT_AFFECTED (never UNKNOWN by default)
- CI/security controls (ruff, pytest, pip-audit, CodeQL, SHA-pinned actions,
  lock-drift check, deterministic SBOM archived, secret tripwire, Linux + Windows)

This milestone is now maintenance/hardening, not active feature
development. Do not add architectural complexity without a concrete
requirement.

## M2 — Real Upstream Change Discovery
STATUS: ACTIVE / HIGHEST PRIORITY

Objective: automatically discover meaningful non-lifecycle changes.
These are the changes lifecycle databases never record and SCA
workflows only notice after breakage — distribution moves, removals,
ownership and support-model shifts. They are the differentiation; a
roadmap that lets lifecycle volume dominate them has failed.

Priorities, in order:

1. Distribution intelligence (who ships what, where, under which namespace)
2. Registry changes (tag appearance/disappearance, digest moves, removals)
3. Repository/archive changes
4. Ownership/maintainer changes
5. Support-model changes
6. License changes
7. Breaking-change signals
8. Package/distribution removal
9. Major release/migration signals

Do not define success as number of collectors. One standing discovery
mechanism that fires repeatedly beats five collectors that never do.

Acceptance criterion: at least 5 reproducible real-world
non-lifecycle discoveries automatically detected and converted into
OpenPulse evidence-backed intelligence. For every accepted case
demonstrate: what changed, why it matters, affected
artifact/package, evidence, confidence, first detection, effective
date, applicable scope. No curated-only example counts as a
successful discovery. Fixtures may be used for regression tests, but
the milestone requires automatically discovered cases.

Current position (honest): the distribution sweep fires live — the
October 2026 run surfaced 65 registry diffs in one pass (nginx,
python, mongo tag pruning) with chain-verified observation identity —
but none are yet formalized into the acceptance set. Formalization,
not mechanism, is the work.

## M3 — Intelligence Report Product
STATUS: ACTIVE

The monthly report is a product surface. It must communicate:

- What changed?
- Why does it matter?
- What did OpenPulse discover?
- Who may be affected?
- What evidence supports it?
- When does it matter?
- What should be investigated?

Required sections:

1. Executive Summary
2. Top Changes
3. OpenPulse Reference Discovery
4. Changes Requiring Attention
5. Upcoming Changes / Warning Windows
6. Category Overview
7. Evidence Quality
8. What OpenPulse Added This Month
9. For Your Environment
10. Detailed Appendix

 companion: the Lifecycle Posture view (deadlines soonest-first,
recent ends, coverage gaps, planning items, full matrix appendix).

Reports must not read as EOL catalogues. Lifecycle is one
intelligence category, not the product itself. The report must
visibly demonstrate the OpenPulse value proposition using real
discoveries. Do not fabricate metrics. Do not claim customer impact
in public intelligence.

## M4 — Intelligence Benchmark
STATUS: BUILD / VALIDATION

Formalize 10–15 golden scenarios (`tests/test_golden.py` and the
matrix suite). Required coverage:

- Bitnami ✅ (formalized)
- iText ✅ (formalized)
- MinIO ✅ (formalized)
- Django ✅ (formalized)
- Redis, PostgreSQL, Kubernetes, cert-manager, Kafka, Grafana,
  Terraform (to formalise)
- at least one AI/ML project (to formalise)

Each scenario must answer:

1. What changed?
2. What evidence proves it?
3. What identity is involved?
4. What dependency is affected?
5. What versions/artifacts are affected?
6. When does it matter?
7. What should the customer investigate?
8. Why is this not merely a lifecycle/SCA database record?

Each scenario must include a “why OpenPulse?” assertion — the
differentiation the scenario proves.

## M5 — Customer Dependency Intelligence
STATUS: NEXT MAJOR PRODUCT MILESTONE

Public intelligence answers “what is changing in OSS?” — necessary
but not commercial. The commercial question is “does this affect MY
software?”, and only dependency context can answer it. That is why
customer impact is the key next step: everything in M1–M4 is built to
feed it.

Inputs: YAML watchlist, SBOM, package manifests, lockfiles, container
image inventories, GitHub repositories.

Output per dependency: affected dependency, not affected, unknown —
each with evidence, identity, applicability, confidence, timing, and
recommended investigation.

Customer flow: customer dependency → canonical identity → OpenPulse
intelligence → applicability → impact → evidence → action.

The watchlist CLI (`openpulse check`) is the local-first preview of
this milestone. Build toward this rather than building generic SCA
functionality.

## M6 — Early Warning SaaS
STATUS: FUTURE

Capabilities: continuous monitoring, alerts, digest,
email/Slack/webhooks, dependency dashboards, warning deadlines,
first-detection history, event timeline, CI/PR checks.

Commercial question: “What is changing in MY software?”

Do not publish average lead-time metrics until there are
independently verified customer-impact cases.

## M7 — Intelligence Network
STATUS: FUTURE

Potential: emerging signals, community observations, confidence
progression, cross-source triangulation, long-term event history,
anonymized cross-customer intelligence.

Only start when customer monitoring is working.

## M8 — AI Dependency Intelligence
STATUS: STRATEGIC / FUTURE

Use the SafeAI/OpenPulse relationship:

- SafeAI: “What can this AI agent do?”
- OpenPulse: “What does the software it creates depend on?”

Do not turn OpenPulse into an AI-agent security product. Use AI as a
dependency provenance/selection context only after core dependency
intelligence is proven.

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

## Roadmap metrics

Do NOT use these as primary success metrics: number of projects
monitored, number of collectors, number of findings, number of
lifecycle records. They measure activity, not intelligence.

Internal validation metrics instead: automatically discovered
non-lifecycle events, verified evidence-backed events,
identity-resolution accuracy, applicability accuracy, false-impact
rate, held-back weak findings, customer-confirmed affected events,
first-detection timestamps, verified early-warning cases.

Do not market these metrics until the methodology is stable.

## Next 90 Days

1. Real non-lifecycle discovery — formalize the M2 acceptance set
   from live sweep output (nginx/python/mongo-class pruning events
   are the first candidates); add repository/archive-change detection.
2. Report/productization — keep the monthly briefing ahead of the
   intelligence it carries; no new sections without a reader need.
3. Golden benchmark — formalize Redis, PostgreSQL, Kubernetes,
   cert-manager, Kafka; start Grafana/Terraform/AI-ML.
4. Customer dependency ingestion — SBOM/lockfile/manifest readers
   feeding the existing verdict engine (no new matching semantics).
5. Early-warning prototype — first-detection history persisted per
   entity so warning windows survive across runs (watchlist-scoped).

Do not add unrelated features. This roadmap exists to stop OpenPulse
from becoming a feature-rich data aggregator and instead drive it
toward a defensible dependency-intelligence product.

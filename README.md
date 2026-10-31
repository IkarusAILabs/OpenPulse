# OpenPulse — Software Ecosystem Intelligence

[![ci](https://github.com/IkarusAILabs/OpenPulse/actions/workflows/ci.yml/badge.svg)](https://github.com/IkarusAILabs/OpenPulse/actions/workflows/ci.yml)
[![license](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
![python](https://img.shields.io/badge/python-%3E%3D3.10-blue.svg)

> **Watch what can change underneath your software.**
>
> OpenPulse is an evidence-first intelligence system that discovers meaningful changes in the open-source software ecosystem, establishes their identity and applicability, and produces machine-readable evidence about their potential impact on software dependencies.
>
> From *"What is happening in open source?"* to *"What is happening to MY software?"*

OpenPulse is the **Software Ecosystem Evidence Plane** of the [Ikarus AI Labs research programme](https://ikaruslabs.net/research) on Evidence-Based Assurance for AI-Mediated Software Change — not an EOL monitor, not an AI security product.

## Research status

OpenPulse is **academic research software**. It is developed by [Ikarus AI Labs](https://ikaruslabs.net), a non-profit research initiative based in Cambridge, UK. It is one of three research instruments in the programme [Evidence-Based Assurance for AI-Mediated Software Change](https://ikaruslabs.net/research), alongside [SafeAI](https://github.com/IkarusAILabs/SafeAI) and HaltAI ([project page](https://ikaruslabs.net/openpulse)).

- **What it is.** A working implementation built to study one question: what evidence should exist before a dependency is reported as affected, or as not affected? The technical report [TR-2026-01](papers/tr-2026-01/OpenPulse-TR-2026-01.pdf) describes its decision model and an audit of release v0.8.0.
- **What it is not.** It is not a commercial product or a certified security control.
  - Evidence and coverage remain bounded. The report lists the open defects and limitations.
  - Nothing beyond the Apache-2.0 licence is offered: no warranty and no service level.
  - Review a verdict before acting on it. *Related* does not mean affected, and *unknown* does not mean not affected.
- **How to read its claims.** The programme separates what is *established* (backed by published or reproducible evidence) from what is *observed* in the current implementation and what is still a *hypothesis*. The report's retrospective study is exploratory. Its prospective, independently labelled evaluation has not yet been run.
- **Collaboration.** We welcome independent replication, annotation and evaluation. The evaluation protocol is open ([`evaluation/REGISTRATION.md`](evaluation/REGISTRATION.md)). Contact us through [ikaruslabs.net](https://ikaruslabs.net).

<img width="1024" height="1024" alt="OpenPulse" src="https://github.com/user-attachments/assets/f7e4b9c9-6f7c-49fa-8950-a5d1594829b7" />

Most security tools tell you when your dependencies have a vulnerability.
OpenPulse watches for something different: **what can change underneath your software.**
We monitor the open-source ecosystem for end-of-life, support and license changes, registry and distribution changes, ownership changes, breaking changes and other supply-chain signals — then map those changes to the dependencies you actually use.
So instead of another giant list of things happening in open source, OpenPulse answers:

> *"Something changed upstream. Does it affect us?"* — with evidence.

## Know Your Agent. Know Your Dependencies.

OpenPulse is part of the [Ikarus AI Labs](https://ikaruslabs.net) research programme. SafeAI and OpenPulse are intentionally separate instruments — combined-model claims stay out of this repo until the joint experiment runs:

| Question | Project | Answer |
|---|---|---|
| What can this AI agent do? | [SafeAI](https://github.com/IkarusAILabs/SafeAI) — **KYA, Know Your Agent** | Agent capabilities, prompt risks, tool permissions |
| What does the software it creates depend on? | **OpenPulse — KYD, Know Your Dependencies** | Upstream change intelligence mapped to your dependencies |

AI can introduce dependencies faster than humans can review them. OpenPulse helps you understand what those dependencies depend on — and what happens when the ecosystem underneath them changes. **AI writes code fast. OpenPulse watches what that code depends on.**

The agents can now ask OpenPulse themselves: [`openpulse mcp`](docs/MCP.md) is an MCP server, so Claude Code, Cursor or Copilot can check whether a dependency is end-of-life, changed upstream or affected by advisories *before* adding it.

## Use it in GitHub Actions

Run OpenPulse on every pull request that touches a dependency file, and weekly to catch upstream changes no PR triggered. You get a job summary, SARIF for Code Scanning and evidence contracts. Pin the action to a full commit SHA:

```yaml
permissions:
  contents: read
steps:
  - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
    with: {persist-credentials: false}
  - uses: IkarusAILabs/OpenPulse@<full-commit-sha> # v0.8.0
    with:
      manifest: requirements.txt
      fail-on: action   # fail only on ACTION/CRITICAL findings
```

Inputs, permissions, SARIF levels and full workflows: [docs/GITHUB_ACTION.md](docs/GITHUB_ACTION.md).

## Use it from AI coding agents (MCP)

AI agents add and upgrade dependencies faster than anyone reviews them. `openpulse mcp` is an [MCP](https://modelcontextprotocol.io) server that lets Claude Code, Cursor, Copilot and other MCP clients ask OpenPulse **before** they change a dependency.

```bash
pip install "ikarus-openpulse[mcp] @ git+https://github.com/IkarusAILabs/OpenPulse@v0.8.0"
claude mcp add openpulse -- openpulse mcp      # Claude Code
```

> **Install name:** OpenPulse is distributed as **`ikarus-openpulse`**. The name `openpulse` on PyPI belongs to an unrelated project (OpenQASM's pulse AST), so never `pip install openpulse`. Until `ikarus-openpulse` is published on PyPI, install from the pinned release tag as shown. The command you run is still `openpulse`.

Other clients take the usual JSON entry:

```json
{ "mcpServers": { "openpulse": { "command": "openpulse", "args": ["mcp"] } } }
```

| Tool | Answers |
|---|---|
| `dependency_status` | Is this package version or image end-of-life or end-of-support? Is it hit by a curated upstream change (distribution, license, support model)? Which OSV advisories affect *this* version? |
| `check_dependency_file` | The same, for every pinned entry of a manifest, lockfile, SBOM or image list in the project |
| `project_lifecycle` | Which release lines of a project are still supported, so the agent can pick one |

Every answer cites its sources and lists what it could **not** establish. UNKNOWN never means safe, and the agent and its human make the decision.

How the server is limited:

- Every tool is read-only.
- File checks are confined to the project root (`--root`).
- Lookups go only to endoflife.date, OSV and the GitHub API, and are cached per session.
- `--offline` restricts it to the bundled curated events.

The SDK and its dependencies are an optional extra with its own audited lock (`requirements-mcp.lock`).

Setup for Claude Code, Cursor, VS Code/Copilot, Claude Desktop and Windsurf, the tool reference, an example answer and troubleshooting: [docs/MCP.md](docs/MCP.md).

## Send findings to DefectDojo

Security teams already triage in DefectDojo, so OpenPulse findings can go there directly. `attest --defectdojo` writes DefectDojo's **Generic Findings Import** format, built from the same evidence contracts as the JSONL and SARIF outputs.

```bash
openpulse attest --lockfile poetry.lock --event data/fixtures/django-eol/event.json   --defectdojo openpulse-defectdojo.json
```

```bash
curl -sS -X POST "$DEFECTDOJO_URL/api/v2/import-scan/" -H "Authorization: Token $DEFECTDOJO_TOKEN" -F scan_type="Generic Findings Import" -F engagement="$ENGAGEMENT_ID" -F file=@openpulse-defectdojo.json
```

In the UI, open the engagement and choose **Import Scan Results** with scan type *Generic Findings Import*.

| Contract | DefectDojo severity |
|---|---|
| Affected, CRITICAL impact | Critical |
| Affected, ACTION impact | High |
| Affected, REVIEW impact | Medium |
| Affected, WATCH or INFORMATIONAL impact | Low |
| RELATED, or a dependency no event applies to | Info |
| NOT_AFFECTED | not exported |

Each finding includes:

- the evidence URLs, the recommendation, and what could not be established;
- the hash of the evidence contract it came from;
- a stable `unique_id_from_tool`, so re-imports deduplicate instead of piling up.

## Send findings to Dependency-Track

Dependency-Track only tracks vulnerabilities, so OpenPulse findings go in as **INTERNAL vulnerabilities**, one per OpenPulse event (`OPENPULSE-<event id>`), assigned to the affected components of your DT project:

```bash
openpulse attest --sbom bom.json --event data/fixtures/django-eol/event.json --output contracts.jsonl
openpulse dependency-track --contracts contracts.jsonl --dry-run
```

```bash
OPENPULSE_DTRACK_API_KEY=... openpulse dependency-track --contracts contracts.jsonl --url https://dtrack.example --project-name my-app --project-version 1.4.0
```

- **What is pushed:** only *affected* pairs. RELATED and UNKNOWN pairs stay in the JSONL, SARIF and DefectDojo outputs, because DT treats anything assigned as vulnerable.
- **Matching:** components are matched by group, name and version inside the project. Dependencies that aren't components of the project are reported, never guessed onto a different component.
- **Re-runs:** pushing again reuses existing vulnerabilities, so nothing duplicates.
- **Credentials:** the API key is read only from `OPENPULSE_DTRACK_API_KEY`, never from the command line. It needs the `VULNERABILITY_MANAGEMENT` and `PORTFOLIO_MANAGEMENT` permissions.
- **Transport:** HTTPS is required unless you pass `--allow-http`, and redirects are never followed.

## The problem we solve

<img width="1024" height="1024" alt="The problem we solve 2" src="https://github.com/user-attachments/assets/be884e68-0482-4954-aba1-907286d258c6" />

In July 2025, Bitnami announced that effective **28 August 2025** its public `docker.io/bitnami` catalog would stop publishing versioned images: existing tags move to an unmaintained `bitnamilegacy` archive, the mainline goes `latest`-only community tier, and production use requires a Bitnami Secure Images subscription. Miss that one announcement and CI/CD pipelines, Helm releases, and production pulls break — with no CVE ever filed, so no scanner fires.

Bitnami is the pattern, not the exception:

| Signal | Example | Covered by traditional SCA? |
|---|---|---|
| CVE | Critical vulnerability | ✅ |
| EOL / EOS | `Node.js 18` unmaintained, support window ends | ⚠️ partial |
| License change | OSS → restrictive/commercial | ⚠️ partial |
| Distribution change | Registry/image deleted, tags moved | ❌ |
| Support change | Community → paid subscription | ❌ |
| Ownership / maintainer change | Project acquired, maintainer leaves | ❌ |
| Repo health collapse | Activity dies, releases stop | ⚠️ partial |
| Breaking roadmap | Major incompatible release | ⚠️ partial |
| AI selection risk | Coding agent picks an obsolete package | ❌ |

Every row above is a production incident waiting for a team that only watches CVEs.

## Intelligence, not aggregation

A report item should demonstrate intelligence, not repeat news. Not:

> Redis — EOL approaching.

But:

> **Redis 7.x — support lifecycle change detected**
> Evidence: official lifecycle information ·
> Potential impact: organisations running affected versions ·
> Recommended attention: migration planning

That is the bar for every OpenPulse event: **what changed, the evidence, who may be affected, and what to investigate.**

## One instrument, progressively more specific

<img width="1024" height="1024" alt="What is changing in MY dependencies2" src="https://github.com/user-attachments/assets/c2930ba2-0866-4de4-b6b5-b028014b8026" />


| Level | Question | OpenPulse answer | Status |
|---|---|---|---|
| Public | "What is happening in OSS?" | Monthly OSS Dependency Risk Report — first edition: [September 2026](reports/2026-09-openpulse.md) (100 projects, every item sourced) | ✅ Published |
| Projects | "What is changing in the OSS projects I care about?" | OSS Dependency Intelligence — this repo | 🔨 In development |
| Dependencies | "What is changing in MY dependencies?" | Dependency Early Warning — watchlist + impact matching (`openpulse check`, [scheduled runs](docs/SCHEDULED_CHECKS.md)) | Early preview |
| AI-mediated | "What dependencies is AI introducing?" | Know Your Dependencies: agents ask OpenPulse before they change a dependency ([`openpulse mcp`](docs/MCP.md)) | Early preview |

## The metric that matters: Early Warning Lead Time

Repositories monitored is a vanity metric. The one this research cares about is:

> **Early Warning Lead Time** — time between OpenPulse detecting a material upstream change and that change producing an observable impact on a user's environment.

"Detecting" means first trustworthy detection (`first_detected_at`), never the latest re-observation; unknown first detection means no lead-time claim. The goal: *"We identified an upstream change 47 days before it affected a user's pipeline."* We will not publish an average until independently measured incidents make it defensible — until then, verified case studies (Bitnami first).

## What OpenPulse does

```
Upstream world                      OpenPulse engine                    You
GitHub releases ─┐                    ┌───────────────┐
OSV / NVD / CVE ─┼─ collectors ─────▶ │ Change Analyst │── findings ──┐
CISA KEV ────────┤   (7 sources)      │ Security Analyst│             ▼
endoflife.date ──┤                    │ Evidence Analyst│── gate ─▶ OSSEvent ─▶ are YOU affected?
Docker Hub ──────┘                    │ Report Analyst │   (confidence + impact + evidence)
                                      └───────────────┘
```

<img width="1024" height="1024" alt="EarlyWarningLeadTime1" src="https://github.com/user-attachments/assets/04ebb832-2ae7-4e59-8e34-dba9ec0552dd" />

Principles that make it different:

- **Evidence-first.** Every event carries source URLs, announcement/effective dates, and a confidence level (`CONFIRMED` / `CORROBORATED` / `EMERGING` / `UNVERIFIED`). No black boxes.
- **No mystery scores.** Instead of `Risk: 72`, you see per-facet signals — activity, security, lifecycle, support, license, distribution, popularity.
- **Impact attribution.** `docker.io/bitnami/redis` and `docker.io/redis` resolve to *different* canonical projects, so a Bitnami distribution event alerts Bitnami users without false-alarming upstream Redis users.
- **Honest verdicts.** `RELATED ≠ AFFECTED`, `AFFECTS_PROJECT ≠ AFFECTS_VERSION`, `UNKNOWN ≠ NOT_AFFECTED` — same project never means affected, and cleared dependencies say `NOT_AFFECTED`, not "no match".
- **Analysts, not one giant agent.** Four small, deterministic, testable analysts. The evidence gate has veto power.

## What OpenPulse is not

| Existing category | Asks | OpenPulse instead asks |
|---|---|---|
| Lifecycle database (endoflife.date) | When does software reach EOL? | What is changing upstream, and does it affect what I depend on? |
| Vulnerability database (OSV/NVD) | Is this package vulnerable? | Same question, plus: is the match identity-strong or keyword-only? |
| SCA / scanners | What dependency risks exist in my code? | What changed upstream since we last looked? |
| Dependency updater | Should I upgrade? | What breaks if I don't — and by when? |

endoflife.date is one of our sources, not our definition: lifecycle data
enters as raw signals, gets correlated into stories, and is gated like
everything else. We do not compete on EOL record counts.

## Who it's for

- **Software security teams / AppSec** — extend vulnerability management beyond CVEs: EOL software, exploited-in-the-wild (CISA KEV) correlation, license and support-model drift, with evidence you can paste into a risk register.
- **Platform / DevOps engineers** — early warning before registry deletions, tag removals, and chart breakages hit pipelines. The Bitnami case is the reference implementation.
- **Engineering leaders** — useful lead time before an upstream change becomes a production problem, ranked by action-worthiness instead of CVE counts.
- **Researchers** — an inspectable decision model, an executable oracle, frozen study data and an open evaluation protocol to replicate, criticise or extend ([TR-2026-01](papers/tr-2026-01/OpenPulse-TR-2026-01.pdf), [`evaluation/`](evaluation/)).
- **Contributors** — a clean, typed Python codebase where every collector and analyst is a pure, tested function. See [Contributing](#contributing).

## Status — working today

- **7 collectors**: GitHub releases, OSV, NVD, MITRE CVE, CISA KEV, endoflife.date, Docker Hub registries. All degrade gracefully (errors become data, never crashes).
- **4 analysts**: Change, Security, Evidence, Report — plus an evidence gate (`UNVERIFIED` can never emit `ACTION`).
- **Change engine**: corruption-detecting digest-aware registry observations
  (hash-chained local history, frozen sealed records, per-repo locks;
  the chain is unkeyed, so it does not yet resist an adversary with
  write access to `.openpulse/` - keyed integrity is planned for v0.9.0),
  observation diffs (`openpulse observe`), catalog sweep with
  first-detection tracking (`openpulse sweep`, `report --with-sweep`).
- **Entity resolution**: canonical catalog with PURL builders,
  Bitnami-namespace rules, and identity trust (VERIFIED /
  REVIEW_REQUIRED / UNVERIFIED — untrusted mappings cap verdicts at
  EMERGING).
- **AI coding agents (MCP)**: `openpulse mcp` gives Claude Code, Cursor, Copilot and other MCP clients three read-only tools (`dependency_status`, `check_dependency_file`, `project_lifecycle`) backed by live endoflife.date, OSV and GitHub lookups and the same verdict engine as `check` ([docs/MCP.md](docs/MCP.md)).
- **Security-team tools**: `attest --defectdojo` writes DefectDojo Generic Findings, and `openpulse dependency-track` pushes affected findings into Dependency-Track as INTERNAL vulnerabilities. Both are built from the same evidence contracts as SARIF.
- **CLI**: validate events, run analysts live or offline, observe registries, sweep the catalog, render per-project Pulse, generate monthly reports, check watchlists, CycloneDX or SPDX SBOMs, npm/poetry/Cargo lockfiles, requirements/pyproject/pom/go.mod/Cargo manifests (namespaced Maven POMs included), and GitHub repositories (`--github-repo`, commit- and blob-SHA-pinned, with COMPLETE/PARTIAL/FAILED inspection coverage; manifests, lockfiles, SBOMs and image lists found in the repo are all read) with digest + webhook delivery, show upcoming deadlines (`openpulse digest`, `openpulse warnings`), emit evidence-contract v1.2 documents (`openpulse attest`), and replay the Bitnami case end to end. Webhook delivery enforces an SSRF policy (https by default; `--webhook-allow-http` opts in) and never prints the webhook URL path; pass the URL as `OPENPULSE_WEBHOOK_URL` and tokens as `GITHUB_TOKEN` to keep them out of the process list.
- **740+ offline tests** (count reported by CI), `ruff` clean, CI green (Linux + Windows, incl. CodeQL + pip-audit, lock-drift check, deterministic SBOM, secret tripwire).

## What's new in v0.8

v0.8.0 is the release that the technical report [TR-2026-01](papers/tr-2026-01/OpenPulse-TR-2026-01.pdf) describes. Full notes: [`CHANGELOG.md`](CHANGELOG.md).

- **Verdict change: please read before upgrading.** An audit of the verdict engine against a written specification found sixteen defects, thirteen of which could clear an affected dependency or show it as cleared. Fifteen are fixed; one (D16, untrusted identity mappings) is open. A NOT_AFFECTED now needs a scope declared complete *with a recorded basis*, a resolved identity, and evidence fetched within 90 days. Otherwise the answer is RELATED, never a clearance. Uncatalogued packages and images are therefore RELATED more often than before.
- **Bounded evidence age.** `check`, `attest`, `digest`, `warnings` and the MCP tools apply a 90-day bound by default. Pipelines that replay old fixtures should pass `--replay`.
- **Evidence contract 1.2.0.** Every verdict states what it does and does not assert (`verdict_meaning`), along with its scope's completeness and evaluation frame.

## What's new in v0.7

v0.7.0 "Channels" brings OpenPulse to where dependency decisions are made, and v0.7.1 hardens how it fetches and installs. Full notes: [`CHANGELOG.md`](CHANGELOG.md).

- **Verdict change: please read before upgrading.** End-of-life events are scoped to release lines (`4.2`, `13`), and versions used to be compared for equality. So `django==4.2.11` or `postgres:13.5` inside an end-of-life cycle was reported NOT_AFFECTED. They are now AFFECTED (#133). CI gates using `--fail-on` (or the Action's `fail-on`) may start failing on lockfiles that used to pass. That is the intended verdict.
- **AI coding agents.** `openpulse mcp` lets Claude Code, Cursor, Copilot and other MCP clients check a dependency *before* they add it ([docs/MCP.md](docs/MCP.md)).
- **Security-team tools.** `attest --defectdojo` writes DefectDojo findings, and `openpulse dependency-track` pushes affected findings into Dependency-Track.
- **Install name.** OpenPulse is distributed as **`ikarus-openpulse`**, because `openpulse` on PyPI is an unrelated project. If you installed it as `openpulse` from git before, run `pip uninstall openpulse` first.
- **v0.7.1 hardening.**
  - Every collector response is size-capped while it streams, so a gzip bomb or an oversized reply can't exhaust a run.
  - Every install in CI and in the GitHub Action is hash-checked against a complete lock, so a tampered or re-uploaded package fails the install.
- **Still true.** The local history stays *corruption-detecting*, not yet tamper-proof. Keyed integrity is planned for v0.9.0 ([`docs/NEXT_PHASES.md`](docs/NEXT_PHASES.md)).

## Quickstart

```bash
pip install -e ".[dev]"

# 1. Validate the Bitnami reference event (CONFIRMED/ACTION, 3 official evidences)
openpulse validate --event data/fixtures/bitnami/event.json --strict

# 2. Replay the north-star scenario offline:
#    Bitnami event -> evidence gate -> which sample dependencies are affected -> report
openpulse demo-bitnami

# 3. Run live analysts against a real project (network; degrades gracefully)
openpulse analyze --project redis
openpulse analyze --project bitnami

# 4. Record a registry observation and diff it against history
openpulse observe --namespace bitnami --repo redis

# 5. Generate the monthly report (offline bundles or live collectors)
openpulse report --month 2026-09 --raw-bundle-dir path/to/bundles

# 6. Check your watchlist against an event (Early Warning preview)
openpulse check --watchlist data/fixtures/watchlist_sample.yaml --event data/fixtures/bitnami/event.json

   # or feed a CycloneDX SBOM (composable with a watchlist)
openpulse check --sbom data/fixtures/sbom/cyclonedx.json --event data/fixtures/bitnami/event.json

   # SPDX 2.x SBOMs work the same way, and compose with both
openpulse check --spdx data/fixtures/sbom/spdx.json --event data/fixtures/bitnami/event.json

   # container image inventories compose too (one ref per line, or a YAML list)
openpulse check --images data/fixtures/images/inventory_sample.txt --event data/fixtures/bitnami/event.json

   # lockfiles too: package-lock.json, poetry.lock or Cargo.lock (pinned entries only,
   # unpinned/workspace entries are skipped with reasons, never range-guessed)
openpulse check --lockfile data/fixtures/lockfiles/poetry.lock --event data/fixtures/django-eol/event.json

    # emit one evidence-contract v1 JSON document per dependency x event pair (JSONL)
openpulse attest --watchlist data/fixtures/watchlist_sample.yaml --event data/fixtures/bitnami/event.json

    # same contracts as SARIF 2.1.0 (GitHub Code Scanning) + a Markdown summary;
    # the GitHub Action (action.yml, docs/GITHUB_ACTION.md) wraps this
openpulse attest --manifest data/fixtures/manifests/requirements.txt --event data/fixtures/django-eol/event.json --output contracts.jsonl --sarif openpulse.sarif --summary summary.md

    # verdict commands bound evidence age: a NOT_AFFECTED needs evidence fetched
    # within 90 days (--max-evidence-age-days, --as-of); --replay re-evaluates
    # recorded evidence with no bound and says so
openpulse check --lockfile data/fixtures/lockfiles/poetry.lock --event data/fixtures/django-eol/event.json --replay

    # and package manifests: requirements.txt, pyproject.toml, pom.xml, go.mod or Cargo.toml
    # (pinned entries only; ranges/property refs/non-registry sources are skipped with reasons)
openpulse check --manifest data/fixtures/manifests/requirements.txt --event data/fixtures/django-eol/event.json

# 7. Check a whole GitHub repository (public; for private repositories,
#    prefer GITHUB_TOKEN or a token file so the credential is not exposed in argv)
openpulse check --github-repo owner/repo --event data/fixtures/bitnami/event.json
openpulse check --github-repo owner/private-repo --github-token-file ~/.config/openpulse/github-token --event data/fixtures/bitnami/event.json

# 8. Upcoming deadlines for your dependencies (90-day window; `check --ledger` records first detection)
openpulse warnings --watchlist data/fixtures/watchlist_sample.yaml --event data/fixtures/django-eol/event.json
openpulse digest   --watchlist data/fixtures/watchlist_sample.yaml --event data/fixtures/django-eol/event.json

# 9. Post the check digest to Slack-style webhooks (URL via env var, never argv)
OPENPULSE_WEBHOOK_URL=https://hooks.slack.com/services/...   openpulse check --watchlist data/fixtures/watchlist_sample.yaml --event data/fixtures/bitnami/event.json --digest

# 10. Discover changes in what your dependencies name (repositories moved or archived),
#     then check offline against the events it writes
openpulse discover --manifest go.mod --images images.txt --out .openpulse/discovered
openpulse check --manifest go.mod --event .openpulse/discovered/<event>.json

# 11. Run the test suite
pytest -q
```

Expected `demo-bitnami` result: 🚨 on every `bitnami*` ref, ✅ on upstream `redis` / `postgres` / `nginx` — the distinction traditional tooling doesn't make.

## Outputs — what you get

Every month OpenPulse produces two decision-support briefings (see
`reports/` for real examples). They read like security intelligence,
not database exports: ranked findings with evidence confidence,
scope, timing, and a recommended investigation — never raw CVE/EOL
dumps, never claims about your environment without a watchlist.

![October 2026 monthly intelligence briefing]
<img width="1552" height="832" alt="OpenPulse_Report_Summary" src="https://github.com/user-attachments/assets/a1bcbf0d-c842-4c84-9060-5e4095fb2ba5" />

**Monthly intelligence** (`openpulse report --month YYYY-MM [--with-sweep]`):

- Executive Summary — material changes, attention items, upcoming
  warnings, non-lifecycle discoveries, evidence confidence, data gaps.
- Top Changes — deterministic evidence-aware ranking (non-lifecycle
  first, never raw counts). Every card shows announcement, effective,
  first-detected and last-verified dates, freshness status, evidence
  confidence, scope, and a recommended investigation.
- Discovery of the Month — the strongest non-lifecycle story, broken
  out as WHAT / WHY / HOW DETECTED / AFFECTED / NOT AFFECTED /
  EVIDENCE / ANNOUNCED / DETECTION / WARNING WINDOW.
- Changes Requiring Attention, Upcoming Changes (detection lead
  times from first trustworthy detection only), Changes by Category,
  Evidence Quality, What OpenPulse Watches, Methodology.
- What OpenPulse Added This Month — value demonstrated from the
  report's own data, ending in the public → watchlist → impact →
  warning progression.
- For Your Environment (public/customer boundary) and an appendix
  with historical findings, every current finding, sources, and gaps.
- Machine-readable companion: `report --metadata-out` writes a
  `.meta.json` sidecar (report ID, period, version, freshness policy,
  coverage, status/category counts) for web frontends.

**Lifecycle posture** (`openpulse lifecycle-report --month YYYY-MM`):

- Executive Summary, Upcoming Deadlines table (soonest first),
  Recently Ended, Coverage Gaps (NO-DATA is a limitation, never OK),
  Top Planning Items, and the full coverage matrix as an appendix.

## Repo layout

```
core/schema/        # v0.5.0 Intelligence Schema — the source of truth
core/entities/      # catalog + resolve() — canonical Project <-> Package/Artifact
core/evidence/      # policy + provenance + independence — the gate with veto power
core/observations/  # RegistryObservation + local history store + diffs
core/risk/          # match.py — event-vs-dependency impact matching
core/pulse.py       # compute_pulse() — findings/events to 7 facets
collectors/         # github, osv, nvd, cve, kev, endoflife, registries (+base)
analyzers/          # change_analyst, security_analyst, evidence_analyst, report_analyst
cli/                # openpulse CLI (validate, pulse, analyze, observe, report, check, attest, mcp, dependency-track, ...)
cli/mcp_server.py   # `openpulse mcp` - MCP server over the official SDK (optional extra)
core/agent_tools.py # SDK-free engine behind the MCP tools
core/sarif.py, core/defectdojo.py, core/dtrack.py  # SARIF / DefectDojo / Dependency-Track outputs
reports/            # generate.py — monthly ranked markdown reports
data/               # canonical_projects.yaml, openpulse100 seed, bitnami fixture
docs/               # METHODOLOGY, ROADMAP, ANALYSTS, ARCHITECTURE_REVIEW, ...
tests/              # 740+ offline tests (no network in CI)
```

## Docs

| Doc | Content |
|---|---|
| `docs/METHODOLOGY.md` | Sources, evidence rules, confidence levels, limitations |
| `docs/ROADMAP.md` | Research track R, M1–M9 milestones, track T (AI Dependency Trust Assurance, planned), principles, metrics |
| `docs/ANALYSTS.md` | The four analysts and their rules |
| `docs/ARCHITECTURE_REVIEW.md` | Architecture & security assessment, finding matrix, migration plan |
| `docs/BITNAMI_VALIDATION.md` | The Phase-3 acceptance gate |
| `docs/MCP.md` | OpenPulse for AI coding agents: setup per client, tools, example answer, security model |
| `docs/GITHUB_ACTION.md` | The GitHub Action: inputs, permissions, SARIF levels, workflows |
| `docs/EVIDENCE_CONTRACT.md` | Evidence contract v1 / v1.1 / v1.2 — machine-readable dependency verdicts |
| `docs/NEXT_PHASES.md` | Implementation plan v0.7 → v0.10: release and distribution, hardening, Anchored Trust, M6 operations, supply chain |
| `CHANGELOG.md` | What changed in each release |
| `SECURITY.md` | How to report a vulnerability, supported versions, known limitations |

## Roadmap

M1 Trusted Evidence ✅ done (maintenance) → M2 Upstream Discovery ✅ acceptance met (5 verified cases; 5 live-replayed) → M3 Report Product ✅ briefing + metadata live → M4 Benchmark 🔨 11 of 10–15 formalized → M5 Dependency Context ✅ (watchlist, SBOM, image inventory, lockfile, manifest and GitHub-repo inputs on one verdict engine) → M6 Early Warning 🔨 (ledger, digest, warnings, webhook shipped; delivery state, dedup/retry and CI/PR integration next) → M7 Network → M8 AI-mediated direction → M9 combined assurance experiment (research). Full sequence, layers, principles, metrics: [`docs/ROADMAP.md`](docs/ROADMAP.md); research framing: [`docs/research/RESEARCH_ALIGNMENT.md`](docs/research/RESEARCH_ALIGNMENT.md); P0–P3 backlog: [`docs/research/BACKLOG.md`](docs/research/BACKLOG.md).

Planned, not available: **AI Dependency Trust Assurance — Know Why You Trust Your Dependencies** (ROADMAP track T). It is a separate future study that would add evidence on package identity and impersonation, artifact provenance (Sigstore, SLSA, PEP 740), and reputation integrity to the MCP tools and CI policy. None of it ships today. OpenPulse does not detect malware, verify provenance, or score reputation, and an MCP answer is advice to the agent, not a security boundary.

Deliberately *not* on the roadmap: becoming an EOL database, another
generic SCA, collector-count vanity, AI reasoning in the trusted
decision path. They don't prove the core hypothesis.

## Contributing

Evidence-first means contributions are easy to review:

1. **Add a collector** — subclass `collectors/base.py:9`, add `parse_*` pure functions, offline fixture tests. Network failures must return `error` dicts, never raise.
2. **Add an analyst rule** — extend the relevant `analyzers/*_analyst.py`, document the rule in `docs/ANALYSTS.md`, cover it with tests.
3. **Add a project** — append to `data/canonical_projects.yaml` (lowercase, tag-free aliases; tests enforce hygiene and reject alias/docker-image collisions).
4. Every event needs: source URL + fetch date + confidence. `UNVERIFIED` can never be `ACTION`.

```bash
ruff check .   # must pass
pytest -q      # must pass (offline)
```

Good first issues are labeled [`good first issue`](https://github.com/IkarusAILabs/OpenPulse/labels/good%20first%20issue).

## Security

Found a vulnerability, including an input that makes OpenPulse confidently wrong? Please report it privately through GitHub's **Report a vulnerability** button (Security tab). Do not open a public issue. Scope, response times and known limitations: [`SECURITY.md`](SECURITY.md).

## Contributors

Thank you to everyone moving OpenPulse forward:

- **[@wufangyong973](https://github.com/wufangyong973)** — grew the canonical project catalog toward OpenPulse 100 (Airflow, Spark, MinIO, Celery, ZooKeeper) in [#11](https://github.com/IkarusAILabs/OpenPulse/pull/11). First of many.
- **[@DYNOSuprovo](https://github.com/DYNOSuprovo)** — ASCII-marker fallback for `openpulse check` on non-UTF-8 consoles in [#14](https://github.com/IkarusAILabs/OpenPulse/pull/14) (merged via [#17](https://github.com/IkarusAILabs/OpenPulse/pull/17)).
- **[@choksi2212](https://github.com/choksi2212)** — six good-first-issue contributions: Unicode fallback for every CLI command ([#21](https://github.com/IkarusAILabs/OpenPulse/pull/21)), OSV live wiring ([#22](https://github.com/IkarusAILabs/OpenPulse/pull/22)), catalog identity metadata for forks/renames/ecosystem mappings ([#23](https://github.com/IkarusAILabs/OpenPulse/pull/23)), intelligence-semantics documentation ([#24](https://github.com/IkarusAILabs/OpenPulse/pull/24)), SBOM artifact upload ([#25](https://github.com/IkarusAILabs/OpenPulse/pull/25)), and the Windows CI runner ([#26](https://github.com/IkarusAILabs/OpenPulse/pull/26)).

## License

Apache-2.0 — see [LICENSE](LICENSE). Use, modification and distribution, including commercial use, are permitted under the licence. OpenPulse is research software and comes with no warranty (see [Research status](#research-status)).

## Citing OpenPulse

If you use OpenPulse or its results in research, please cite the technical report. [`CITATION.cff`](CITATION.cff) gives the citation in machine-readable form.

> Mehmet Kış. *Evidence Before Impact: Upstream Change Intelligence for Dependency Decisions.* Technical Report TR-2026-01, Ikarus AI Labs, Cambridge, UK, 31 October 2026. OpenPulse v0.8.0. https://github.com/IkarusAILabs/OpenPulse

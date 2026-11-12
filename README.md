# OpenPulse — Evidence for Dependency Decisions

[![ci](https://github.com/IkarusAILabs/OpenPulse/actions/workflows/ci.yml/badge.svg)](https://github.com/IkarusAILabs/OpenPulse/actions/workflows/ci.yml)
[![license](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
![python](https://img.shields.io/badge/python-%3E%3D3.10-blue.svg)

> **Know why you trust your dependencies, and know when they change underneath you.**
>
> OpenPulse produces cited, machine-readable evidence for the two moments a dependency decision is made: **before** a package comes in (is it what it claims to be?), and **after** it is in (did something change upstream that affects us?). It answers where those decisions happen: in AI coding agents, in pre-commit and CI gates, and in the tools security teams already use.

OpenPulse is the **Software Ecosystem Evidence Plane** of the [Ikarus AI Labs research programme](https://ikaruslabs.net/research) on Evidence-Based Assurance for AI-Mediated Software Change.

## Research status

OpenPulse is **academic research software**. It is developed by [Ikarus AI Labs](https://ikaruslabs.net), a non-profit research initiative based in Cambridge, UK. It is one of three research instruments in the programme [Evidence-Based Assurance for AI-Mediated Software Change](https://ikaruslabs.net/research), alongside [SafeAI](https://github.com/IkarusAILabs/SafeAI) and HaltAI ([project page](https://ikaruslabs.net/openpulse)).

- **What it is.** A working implementation built to study one question: what evidence should exist before a dependency is reported as affected, as not affected, or as trustworthy enough to add? The technical report [TR-2026-01](papers/tr-2026-01/OpenPulse-TR-2026-01.pdf) describes its decision model and an audit of release v0.8.0.
- **What it is not.** It is not a commercial product or a certified security control.
  - Evidence and coverage remain bounded. The report and [Known limits](#known-limits) list them.
  - Nothing beyond the Apache-2.0 licence is offered: no warranty and no service level.
  - Review a verdict before acting on it. *Related* does not mean affected, *unknown* does not mean not affected, and no finding does not mean safe.
- **How to read its claims.** The programme separates what is *established* (backed by published or reproducible evidence) from what is *observed* in the current implementation and what is still a *hypothesis*. The report's retrospective study is exploratory. Its prospective, independently labelled evaluation has not yet been run.
- **Collaboration.** We welcome independent replication, annotation and evaluation. The evaluation protocol is open ([`evaluation/REGISTRATION.md`](evaluation/REGISTRATION.md)). Contact us through [ikaruslabs.net](https://ikaruslabs.net).

<img width="1024" height="1024" alt="OpenPulse" src="https://github.com/user-attachments/assets/f7e4b9c9-6f7c-49fa-8950-a5d1594829b7" />

## What OpenPulse offers

AI coding agents add and upgrade dependencies faster than anyone reviews them, and most of what can go wrong with a dependency never becomes a CVE: a name an agent invented and an attacker registered, a lockfile hash swapped for another artifact, a release published by someone new, an image catalog moved behind a subscription, a release line that reached end of life. OpenPulse turns those into evidence a person, a pipeline or an agent can act on.

| Your question | What OpenPulse gives you | Where |
|---|---|---|
| *Is this package what it claims to be?* | Trust evidence for PyPI and npm packages: published malicious-package records, registry existence, lockfile digests, build provenance, repository linkage, dependency confusion, lookalike names, and reputation indicators | AI agents ([MCP](docs/MCP.md)), `openpulse trust` |
| *Should this change be allowed in?* | A deterministic trust policy that fails pre-commit, CI and `check`/`attest` runs on the conditions you prohibit, and fails closed when it cannot check | `openpulse gate`, pre-commit hook, [GitHub Action](docs/GITHUB_ACTION.md), [policy](docs/TRUST_POLICY.md) |
| *Something changed upstream. Does it affect us?* | Applicability verdicts for your exact versions and images against curated, evidence-gated upstream events: end of life and support, distribution, licence, ownership and breaking changes, plus OSV advisories | `openpulse check`, `attest`, `digest`, `warnings`, the Action |
| *What is happening in the projects we depend on?* | Monthly intelligence and lifecycle reports over a 107-project catalog, with registry observation and discovery, published each month at [openpulse.ikaruslabs.net](https://openpulse.ikaruslabs.net/) | `openpulse report`, `lifecycle-report`, `observe`, `sweep`, `discover` |
| *How do we prove what we checked?* | Evidence contracts (JSON Schema, content-hashed) and SARIF, DefectDojo and Dependency-Track exports built from them | [`docs/EVIDENCE_CONTRACT.md`](docs/EVIDENCE_CONTRACT.md), [`docs/INTEGRATIONS.md`](docs/INTEGRATIONS.md) |

What makes the evidence usable:

- **Evidence, not scores.** Every result cites its sources and states one status from a closed vocabulary. There is no risk score and no SAFE status. Indicators are reported one by one and never summed.
- **Unknown stays unknown.** A source that did not answer, a spent lookup budget, or an unreadable file is reported as not established, never as clean. The pre-install gate fails closed on it.
- **Measured before it ships.** Every trust indicator's false-positive rate on real, legitimate packages is measured and published ([`docs/research/TRACK_T_MEASUREMENTS.md`](docs/research/TRACK_T_MEASUREMENTS.md)). An indicator that fires on legitimate packages can only be prohibited for packages you name; one without a measured rate is labelled experimental.
- **Honest verdicts.** `RELATED ≠ AFFECTED`, `AFFECTS_PROJECT ≠ AFFECTS_VERSION`, `UNKNOWN ≠ NOT_AFFECTED`. A NOT_AFFECTED needs a complete scope, a resolved identity and evidence fetched within 90 days.
- **No model in the decision path.** Verdicts, trust statuses and policy decisions are deterministic code. Upstream text is never passed to an agent as instructions.

## Get started

**For AI coding agents.** `openpulse mcp` is an [MCP](https://modelcontextprotocol.io) server, so Claude Code, Cursor, Copilot and other clients can ask before they change a dependency:

```bash
pip install "ikarus-openpulse[mcp] @ git+https://github.com/IkarusAILabs/OpenPulse@v0.20.0"
claude mcp add openpulse -- openpulse mcp      # Claude Code
```

> **Install name:** OpenPulse is distributed as **`ikarus-openpulse`**. The name `openpulse` on PyPI belongs to an unrelated project (OpenQASM's pulse AST), so never `pip install openpulse`. Until `ikarus-openpulse` is published on PyPI, install from the pinned release tag as shown. The command you run is still `openpulse`.

| Tool | Answers |
|---|---|
| `dependency_status` | For one package version or image: end of life or support, curated upstream changes, OSV advisories for *this* version, and a `trust` block with every trust check |
| `check_dependency_file` | The same verdicts for every pinned entry of a manifest, lockfile, SBOM or image list, with trust checks for the dependencies a change adds (`base_path`) or for all of them |
| `project_lifecycle` | Which release lines of a project are still supported, so the agent can pick one |

Every tool is read-only, file checks are confined to the project root, and every answer lists what it could not establish. An MCP answer is advice to the agent, not a security boundary: enforce with a policy (below). Setup for each client: [docs/MCP.md](docs/MCP.md).

**Before install: a trust policy and a gate.** Write `.openpulse/policy.yml`:

```yaml
version: 1
prohibit:
  - confirmed_malicious              # an OSV MAL- record, cited
  - not_found_in_registry            # a name nobody published (or an agent invented)
  - digest_mismatch                  # a locked artifact the registry does not serve
  - condition: lookalike_name        # indicators must name the packages they apply to
    packages: ["npm:@acme/*"]
blocklist:
  - "npm:event-stream"
```

```bash
openpulse gate requirements.txt poetry.lock --base-ref origin/main   # CI, before pip install
```

Only dependencies added or changed since the ref are checked; the blocklist covers everything. Exit 0 passes, 1 is a violation, 2 is a usage error or a file it cannot read. A prohibited check that could not run fails the gate unless the policy says `unchecked: pass`. The same gate runs as a pre-commit hook (add the `openpulse-gate` hook from this repository to your `.pre-commit-config.yaml`) and as the GitHub Action's `gate` input, which reads the policy from the base branch so a pull request cannot weaken its own gate. Conditions, labels and bypass routes: [docs/TRUST_POLICY.md](docs/TRUST_POLICY.md).

**In GitHub Actions.** Run OpenPulse on every pull request that touches a dependency file, and on a schedule to catch upstream changes no pull request triggered ([a scheduled watch](docs/GITHUB_ACTION.md#example-a-scheduled-watch-catches-upstream-changes-with-no-pr) tells you once about each). You get a job summary, SARIF for Code Scanning and evidence contracts. Pin the action to a full commit SHA:

```yaml
permissions:
  contents: read
steps:
  - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
    with: {persist-credentials: false}
  - uses: IkarusAILabs/OpenPulse@<full-commit-sha> # v0.20.0
    with:
      manifest: requirements.txt
      fail-on: action        # fail only on ACTION/CRITICAL upstream findings
      trust: pull-request    # trust-check what the pull request adds or changes
```

Inputs, permissions, SARIF levels and full workflows: [docs/GITHUB_ACTION.md](docs/GITHUB_ACTION.md).

**Upstream change checks from the command line.**

```bash
pip install -e ".[dev]"
openpulse demo-bitnami                     # the reference case, offline
openpulse check --lockfile poetry.lock --event data/fixtures/django-eol/event.json
openpulse trust requirements.txt --base base-requirements.txt
```

More commands are in the [Command reference](#command-reference).

## Trust evidence: before a dependency comes in

Track T of the [roadmap](docs/ROADMAP.md), *AI Dependency Trust Assurance*. Each check is evidence to review and never part of an upstream-change verdict. They run for PyPI and npm packages.

| Check | Question | Strongest result | Measured on legitimate packages |
|---|---|---|---|
| `malicious` | Does OSV publish a malicious-package (`MAL-`) record for it? | CONFIRMED_MALICIOUS, with the record cited | cited record |
| `registry_existence` | Do the package and version exist in their registry? (A name an agent invented does not.) | VERIFIED_FAILURE | failed check |
| `digest_integrity` | Is each hash a lockfile pins one the registry publishes? | VERIFIED_FAILURE | failed check |
| `provenance` | Do the PyPI release's PEP 740 attestations verify (Sigstore), and from which repository? | VERIFIED_FAILURE | failed check |
| `repository_linkage` | Is the package from the GitHub repository its metadata claims (starjacking)? | VERIFIED_FAILURE, or an indicator | failed check; indicator experimental |
| `dependency_confusion` | Does a public package carry one of your private names? | indicator | experimental |
| `lookalike` | Does the name resemble a popular one (separator, edit distance, confusable, scope)? | indicator | 18.8% of popular npm names |
| `publisher_change` | Was this release published by an account or provenance publisher the earlier releases did not use? | indicator | 4.6% of npm releases, 0.7% of PyPI releases |
| `repository_moved` | Does the claimed repository now answer under another name? | indicator | 4.1% of repositories |
| `young_popular_repository` | Is the repository younger than 180 days with at least 1000 stars? | indicator | experimental |

An indicator (SUSPICIOUS_INCONCLUSIVE) is never a verdict: legitimate projects change maintainers, move to organisations and launch to many stars. `publisher_change`, `repository_moved` and `young_popular_repository` shipped in v0.16.0. Rates and method: [`docs/research/TRACK_T_MEASUREMENTS.md`](docs/research/TRACK_T_MEASUREMENTS.md).

Where the evidence goes:

- **Agents:** the `trust` block in `dependency_status` and `check_dependency_file`, with what needs attention listed first.
- **People:** `openpulse trust FILE [--base EARLIER]` (report-only) and `openpulse confusion` for your private names.
- **Gates:** the trust policy in `openpulse gate`, `check --policy`, `attest --policy` and the Action.
- **Records:** `attest --trust` writes each dependency's checks into the evidence contract's `trust_assurance` (contract 2.4.0), covered by its content hash, and into SARIF and DefectDojo.

## Upstream change intelligence: after it is in

<img width="1024" height="1024" alt="The problem we solve" src="https://github.com/user-attachments/assets/be884e68-0482-4954-aba1-907286d258c6" />

In July 2025, Bitnami announced that from **28 August 2025** its public `docker.io/bitnami` catalog would stop publishing versioned images: existing tags moved to an unmaintained `bitnamilegacy` archive, and production use needed a subscription. Pipelines, Helm releases and production pulls broke, and no CVE was ever filed, so no scanner fired.

| Signal | Example | Covered by traditional SCA? |
|---|---|---|
| CVE | Critical vulnerability | ✅ |
| End of life or support | A release line stops receiving fixes | ⚠️ partial |
| Licence change | Open source to restrictive or commercial | ⚠️ partial |
| Distribution change | Registry or image deleted, tags moved | ❌ |
| Support model change | Community to paid subscription | ❌ |
| Ownership or maintainer change | Project transferred, maintainer leaves | ❌ |
| Breaking change | Major incompatible release | ⚠️ partial |

How OpenPulse answers *"does it affect us?"*:

- **Evidence-gated events.** Every event carries source URLs, announcement and effective dates, and a confidence level (`CONFIRMED`, `CORROBORATED`, `EMERGING`, `UNVERIFIED`). A source counts as official only when its host is on the project's allowlist, and sources sharing a registrable domain count once. `UNVERIFIED` can never produce an `ACTION`.
- **Identity before impact.** `docker.io/bitnami/redis` and `docker.io/redis` are different projects, so a Bitnami distribution event alerts Bitnami users without false-alarming upstream Redis users. Untrusted identity mappings cap the verdict.
- **Your exact versions.** Watchlists, CycloneDX and SPDX SBOMs, image lists, `package-lock.json`, `poetry.lock` and `Cargo.lock`, `requirements.txt` and its variants (`requirements-dev.txt`, `requirements/*.txt`, `constraints.txt`, in repositories), `pyproject.toml`, `pom.xml`, `go.mod`, `Cargo.toml`, and whole GitHub repositories (commit- and blob-pinned, with stated inspection coverage) all go through one verdict engine.
- **Early warning.** `digest` and `warnings` list upcoming deadlines; scheduled `check --webhook` posts each new alert once, with retries and signed posts ([`docs/SCHEDULED_CHECKS.md`](docs/SCHEDULED_CHECKS.md)). A detection ledger records when OpenPulse first saw each change, so lead time can be measured. With a history key the ledger is tamper-evident ([`docs/KEYED_INTEGRITY.md`](docs/KEYED_INTEGRITY.md)).
- **Discovery.** `openpulse discover` probes the repositories and images your files name, and `observe` and `sweep` diff registry observations, turning moves, archives and removed tags into events.

**The metric that matters: Early Warning Lead Time**, the time between OpenPulse first detecting a material upstream change and that change affecting a user. "Detecting" means first trustworthy detection, never the latest re-observation. Verified cases are in [`docs/LEAD_TIME_CASES.md`](docs/LEAD_TIME_CASES.md), each with its dates and how to reproduce it. No average is published: a forward detection lead has not yet been independently measured, and the Bitnami case is recorded as an announcement lead, not a detection.

## What OpenPulse is not

| Existing category | Asks | OpenPulse instead |
|---|---|---|
| Malicious-code scanners | Does this package's code behave maliciously? | Does not analyse code. It cites published malicious-package records and checks identity, integrity, provenance and reputation evidence, each with its status |
| Vulnerability databases (OSV, NVD) | Is this package vulnerable? | Uses them as sources, and says whether the match is identity-strong or keyword-only |
| Lifecycle databases (endoflife.date) | When does software reach end of life? | Uses it as one source; asks what changed upstream and whether it affects your exact versions |
| SCA scanners and dependency updaters | What risks exist in my code? Should I upgrade? | Asks what changed upstream since you last looked, what breaks if you don't act, and by when |
| Repository scorecards | How healthy is this project? | Reports individual, cited indicators with measured false-positive rates; never a score |

## Who it's for

- **Teams using AI coding agents:** agents check a dependency before adding it, and a policy gate holds whatever the agent decided to the same rules.
- **AppSec and supply-chain security:** trust evidence and gates before install, evidence beyond CVEs after, delivered into SARIF, DefectDojo and Dependency-Track.
- **Platform and DevOps engineers:** early warning before registry deletions, tag removals and support changes hit pipelines. The Bitnami case is the reference implementation.
- **Researchers:** an inspectable decision model, an executable oracle, frozen study data, published measurements and an open evaluation protocol to replicate, criticise or extend ([TR-2026-01](papers/tr-2026-01/OpenPulse-TR-2026-01.pdf), [`evaluation/`](evaluation/)).
- **Contributors:** a typed Python codebase where every collector, check and analyst is a pure, tested function. See [Contributing](#contributing).

## Known limits

- **Ecosystems.** Trust checks cover PyPI and npm. Upstream-change verdicts cover the formats listed above; Maven, Go and Cargo entries get verdicts but no trust checks.
- **Exact pins only.** Unpinned entries (`flask>=2`) are never range-guessed: they are listed as not checked. Gate the lockfile.
- **Curated events.** Upstream-change verdicts are as good as the events supplied: seven curated reference events ship in `data/fixtures/`, plus what `discover` and `sweep` find. The catalog covers 107 projects.
- **Live sources.** Checks depend on OSV, the registries and the GitHub API. Without `GITHUB_TOKEN`, GitHub allows 60 requests an hour, so GitHub-backed checks may be not performed on large runs; the gate then fails unless the policy says `unchecked: pass`.
- **Advice versus enforcement.** MCP answers are advice an agent can ignore; only a policy in a gate or CI enforces. A pre-commit hook can be skipped locally, so run the gate in CI as a required check.
- **Distribution.** Not yet on PyPI: install from a pinned release tag. Releases are built and attested in CI (`gh attestation verify <file> --repo IkarusAILabs/OpenPulse`).

The full list, including what an attacker with write access to local history can do: [`SECURITY.md`](SECURITY.md).

## Status — working today

- **Trust checks:** the ten checks above, a trust policy, `openpulse gate`, a pre-commit hook and the Action's `gate` and `trust` inputs, with bypass routes tested and documented.
- **Verdict engine:** identity resolution over a 107-project catalog with PURL builders and identity trust (VERIFIED, REVIEW_REQUIRED, UNVERIFIED), release-line-aware matching, bounded evidence age and stated meaning for every verdict.
- **Collectors:** GitHub, OSV, NVD, MITRE CVE, CISA KEV, endoflife.date and Docker Hub, plus PyPI, npm and the GitHub API for trust checks. Errors become data, never crashes; every response is size-capped while it streams.
- **Analysts:** Change, Security, Evidence and Report, behind an evidence gate with veto power.
- **History:** hash-chained registry observations and a detection ledger, MACed with a history key, with anchors kept outside the store. History committed to the repository is refused.
- **Outputs:** evidence contract 2.4.0 (older versions still validate), SARIF 2.1.0, Markdown summaries, DefectDojo, Dependency-Track, signed webhooks, and monthly and lifecycle reports.
- **Quality:** more than 2,100 offline tests (count reported by CI), `ruff` clean, CI on Linux and Windows with CodeQL, pip-audit, a lock-drift check, a deterministic SBOM and a secret tripwire. Every install is hash-checked against complete locks.

## What's new

**v0.20.0 "Change Evidence Beyond Lifecycle":** changes that are not end-of-life dates, each with the evidence it rests on.

- **Repository history:** `openpulse observe-github` keeps a hash-chained, keyed history of a GitHub repository; a license change, an archive or a move to a new owner between two observations is a finding for review (experimental until a real change is observed twice).
- **License changes between releases:** `openpulse release-license` compares the license npm or PyPI records for each release, in version order (React's BSD-3-Clause to MIT in 15.6.2).
- **Deprecated and withdrawn packages:** `openpulse deprecation` reads npm's `deprecated`, PyPI yanks and the Inactive classifier, for the package or your version.
- **Evidence rules:** each finding states its confidence and basis: an observed difference is EMERGING, the publisher's own flag CONFIRMED, and GitHub's license id is CORROBORATED only when the registry agrees. Lead time is claimed for lifecycle events only.
- **Verified cases:** `docs/DISCOVERIES.md` Cases 11-16 replay recorded registry responses, each confirmed by a source the check did not use.

**v0.19.0 "Evidence Consumer and Portability":** an evidence contract means the same thing outside OpenPulse.

- **Standalone consumer:** `conformance/consumer/` (`openpulse-evidence-consumer`, Python 3.11+, one dependency: `jsonschema`, hash-locked) imports nothing from OpenPulse. `openpulse-consumer check` validates each document against exactly the schema its version names and recomputes its content hash, 1.0 to 2.4.
- **Outcomes kept apart:** `openpulse-consumer summary` counts relationship, inspection coverage and trust separately, lists what each document leaves open, and has no pass.
- **Tested on every released version:** `conformance/contracts/` holds documents written by each version's own release, and one-rule negatives; CI runs the consumer, OpenPulse's validator and `verify.mjs` over them.
- **Fixed:** OpenPulse now verifies genuine 1.0 contracts (it hashed them with the 1.1 field list).

**v0.18.0 "Inspection Coverage Assurance":** repository coverage that never overstates itself.

- **More is read:** requirements variants (`requirements-dev.txt`, `requirements/*.txt`, `constraints.txt`), monorepo members under `packages/` (skipped before, a fix), npm workspace members through their lockfile, and Cargo workspace roots. A `-r`/`-c` include that was not inspected makes coverage PARTIAL.
- **What was searched is stated:** ref and commit, file patterns, skipped directories with counts, the limits that applied, files found and read; in `check` and `attest`, and as `inspection_coverage.scope` in evidence contract 2.4.0.
- **No all-clear over PARTIAL:** every summary that could read as clear names what was not inspected, by category and count.

**v0.17.0 "Gate-to-Install Integrity":** what `openpulse gate` passed is what gets installed, or the install is refused.

- **Receipts:** `openpulse gate --receipt PATH` records the SHA-256 of every file it judged, the policy, the decision and every violation.
- **Verify before install:** `openpulse gate --verify-receipt PATH FILE...` refuses (exit 1) any file that changed since the gate, was not gated, or comes from a gate that did not pass. `--require-receipt-for PATTERN` catches dependency files a build step generated after the gate. The Action's `gate` input writes receipts and names them in a `receipts` output.
- **Lockfile digests always checked by the gate:** once a policy exists, a hash edited in place fails the gate even if the policy never mentions `digest_mismatch`.
- **Tested end to end:** gate, verify and a real `pip install --require-hashes`, offline, on Linux and Windows.

**v0.16.1:** `openpulse gate` no longer crashes when a private-name list is in use (the Action passes one whenever the base branch has it).

**v0.16.0 "Reputation Evidence":**

- **Reputation indicators:** `publisher_change`, `repository_moved` and `young_popular_repository`, each measured on a recorded set of legitimate packages first, in the trust block, the policy, SARIF and DefectDojo.
- **Evidence contract 2.3.0:** `trust_assurance` may name the three new checks; 2.2 is published unchanged beside it.
- **The gate fails closed:** a file it cannot read exits 2, and a prohibited check that could not run fails the gate (`unchecked: pass` opts out). Entries it does not check are listed.
- **Local history must be local:** a store, ledger or delivery state that git tracks is refused.

**v0.15.0 "Pre-Install Gates":** `openpulse gate`, the pre-commit hook and the Action's `gate` input apply the trust policy before anything is installed.

Every release, with upgrade notes: [`CHANGELOG.md`](CHANGELOG.md).

## Command reference

```bash
pip install -e ".[dev]"

# Trust evidence and gates (PyPI and npm)
openpulse trust requirements.txt --base base-requirements.txt      # report-only
openpulse confusion .openpulse/private-packages.txt                # your private names, publicly?
openpulse gate requirements.txt poetry.lock --base-ref origin/main # the policy, before install

# Upstream change verdicts for your dependencies
openpulse validate --event data/fixtures/bitnami/event.json --strict
openpulse demo-bitnami                                             # offline reference case
openpulse check --watchlist data/fixtures/watchlist_sample.yaml --event data/fixtures/bitnami/event.json
openpulse check --sbom data/fixtures/sbom/cyclonedx.json --event data/fixtures/bitnami/event.json
openpulse check --spdx data/fixtures/sbom/spdx.json --event data/fixtures/bitnami/event.json
openpulse check --images data/fixtures/images/inventory_sample.txt --event data/fixtures/bitnami/event.json
openpulse check --lockfile data/fixtures/lockfiles/poetry.lock --event data/fixtures/django-eol/event.json
openpulse check --manifest data/fixtures/manifests/requirements.txt --event data/fixtures/django-eol/event.json
openpulse check --github-repo owner/repo --event data/fixtures/bitnami/event.json   # GITHUB_TOKEN for private repos
openpulse check --lockfile data/fixtures/lockfiles/poetry.lock --event data/fixtures/django-eol/event.json --replay

# Evidence contracts and exports
openpulse attest --manifest data/fixtures/manifests/requirements.txt --event data/fixtures/django-eol/event.json \
  --output contracts.jsonl --sarif openpulse.sarif --summary summary.md --trust
openpulse attest --lockfile poetry.lock --event data/fixtures/django-eol/event.json --defectdojo dojo.json
openpulse dependency-track --contracts contracts.jsonl --dry-run

# Early warning
openpulse warnings --watchlist data/fixtures/watchlist_sample.yaml --event data/fixtures/django-eol/event.json
openpulse digest   --watchlist data/fixtures/watchlist_sample.yaml --event data/fixtures/django-eol/event.json
OPENPULSE_WEBHOOK_URL=https://hooks.slack.com/services/... \
  openpulse check --watchlist data/fixtures/watchlist_sample.yaml --event data/fixtures/bitnami/event.json --digest

# Discovery, observation and reports
openpulse discover --manifest go.mod --images images.txt --out .openpulse/discovered
openpulse observe --namespace bitnami --repo redis
openpulse observe-github --repo minio/minio
openpulse release-license --ecosystem npm --package react --version 15.6.1
openpulse deprecation --ecosystem PyPI --package urllib3 --version 2.0.0
openpulse analyze --project redis
openpulse report --month 2026-09 --raw-bundle-dir path/to/bundles
openpulse lifecycle-report --month 2026-09

# Local history integrity
openpulse history-key generate
openpulse anchor --out anchors/latest.json
openpulse verify --anchor anchors/latest.json

pytest -q
```

Verdict commands bound evidence age: a NOT_AFFECTED needs evidence fetched within 90 days (`--max-evidence-age-days`, `--as-of`); `--replay` re-evaluates recorded evidence with no bound and says so. Expected `demo-bitnami` result: 🚨 on every `bitnami*` ref, ✅ on upstream `redis`, `postgres` and `nginx`.

## Reports

<img width="1552" height="832" alt="OpenPulse report summary" src="https://github.com/user-attachments/assets/a1bcbf0d-c842-4c84-9060-5e4095fb2ba5" />

OpenPulse publishes a monthly intelligence briefing and a lifecycle posture report over its catalog. Each edition is published at **[openpulse.ikaruslabs.net](https://openpulse.ikaruslabs.net/)**, and the reports `openpulse report` generated are kept in [`reports/`](reports/) (September to November 2026). The site presents the output of this research instrument: it is not a service, and the limits in [Research status](#research-status) and [Known limits](#known-limits) apply to it. They read like security intelligence, not database exports: ranked findings with evidence confidence, scope, timing and a recommended investigation, never claims about your environment without your dependency list. `report --metadata-out` writes a machine-readable sidecar for web frontends.

## Repo layout

```
core/schema/        # Intelligence Schema 0.7.0, the source of truth for events
core/entities/      # catalog + resolve(): canonical project <-> package/artifact
core/evidence/      # policy, provenance, independence: the gate with veto power
core/risk/          # event-vs-dependency impact matching
core/agent_tools.py # the engine behind the MCP tools, including the trust checks
core/*.py           # trust checks (malicious, registry_existence, provenance, ...),
                    # trust_policy, evidence_contract, sarif, defectdojo, dtrack
core/observations/  # registry observations, history store, diffs, sweep
collectors/         # github, osv, nvd, cve, kev, endoflife, registries
analyzers/          # change, security, evidence and report analysts
cli/                # the openpulse CLI and the MCP server (cli/mcp_server.py)
benchmarks/         # trust-check measurements and the organic reputation set
reports/            # monthly report generator and published reports
schemas/            # evidence-contract JSON Schemas, every version
data/               # catalog, seed, official domains, reference fixtures
tests/              # offline tests (no network in CI)
```

## Docs

| Doc | Content |
|---|---|
| [`docs/MCP.md`](docs/MCP.md) | OpenPulse for AI coding agents: setup per client, tools, the trust block, security model |
| [`docs/TRUST_POLICY.md`](docs/TRUST_POLICY.md) | Trust policy, `openpulse gate`, pre-commit, bypass routes |
| [`docs/GITHUB_ACTION.md`](docs/GITHUB_ACTION.md) | The GitHub Action: inputs, permissions, SARIF levels, workflows |
| [`docs/INTEGRATIONS.md`](docs/INTEGRATIONS.md) | DefectDojo and Dependency-Track |
| [`docs/EVIDENCE_CONTRACT.md`](docs/EVIDENCE_CONTRACT.md) | Evidence contract 2.4 and every earlier version |
| [`docs/research/TRACK_T_MEASUREMENTS.md`](docs/research/TRACK_T_MEASUREMENTS.md) | How each trust check is measured, with false-positive rates |
| [`docs/SCHEDULED_CHECKS.md`](docs/SCHEDULED_CHECKS.md) | Scheduled checks, the detection ledger, webhook delivery |
| [`docs/KEYED_INTEGRITY.md`](docs/KEYED_INTEGRITY.md) | History keys, anchors and what they protect against |
| [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) | Sources, evidence rules, confidence levels, limitations |
| [`docs/ANALYSTS.md`](docs/ANALYSTS.md) | The four analysts and their rules |
| [`docs/LEAD_TIME_CASES.md`](docs/LEAD_TIME_CASES.md) | Verified lead-time cases, never averaged |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Research track R, track T, milestones M1–M9, principles, metrics |
| [`docs/NEXT_PHASES.md`](docs/NEXT_PHASES.md) | The release-by-release implementation plan |
| [`CHANGELOG.md`](CHANGELOG.md) | What changed in each release, with upgrade notes |
| [`SECURITY.md`](SECURITY.md) | Reporting a vulnerability, supported versions, known limitations |

## Roadmap

Two tracks share one evidence model:

- **Upstream change intelligence:** M1 Trusted Evidence ✅ → M2 Upstream Discovery ✅ → M3 Report Product ✅ → M4 Benchmark 🔨 (11 formalized scenarios) → M5 Dependency Context ✅ → M6 Early Warning 🔨 (ledger, digest, warnings, signed webhook delivery with retries, and the GitHub Action shipped) → M7 Network → M8 AI-mediated direction → M9 combined assurance experiment (research).
- **Track T, AI Dependency Trust Assurance:** identity and integrity checks (v0.12), agent trust evidence and contract 2.2 (v0.13), trust policy and measurements (v0.14), pre-install gates (v0.15), reputation indicators and contract 2.3 (v0.16), gate-to-install integrity (v0.17). The research questions, such as whether trust evidence changes what agents and people choose, remain open.

Full sequence, principles and metrics: [`docs/ROADMAP.md`](docs/ROADMAP.md); research framing: [`docs/research/RESEARCH_ALIGNMENT.md`](docs/research/RESEARCH_ALIGNMENT.md).

Deliberately *not* on the roadmap: becoming an EOL database, a generic SCA or a malware scanner, risk scores, collector-count vanity, and AI reasoning in the trusted decision path.

## Contributing

Evidence-first means contributions are easy to review:

1. **Add a collector:** subclass `collectors/base.py`, add pure `parse_*` functions and offline fixture tests. Network failures must return `error` dicts, never raise.
2. **Add an analyst rule:** extend the relevant `analyzers/*_analyst.py`, document the rule in `docs/ANALYSTS.md`, cover it with tests.
3. **Add a project:** append to `data/canonical_projects.yaml` (lowercase, tag-free aliases; tests enforce hygiene and reject alias and image collisions).
4. **Add a trust check:** a fixed-template statement, a closed status, injected network seams with offline defaults, and a measurement in `benchmarks/trust.py` before it can be prohibited.
5. Every event needs a source URL, a fetch date and a confidence. `UNVERIFIED` can never be `ACTION`.

```bash
ruff check .   # must pass
pytest -q      # must pass (offline)
```

Good first issues are labelled [`good first issue`](https://github.com/IkarusAILabs/OpenPulse/labels/good%20first%20issue).

## Security

Found a vulnerability, including an input that makes OpenPulse confidently wrong or a way past the gate? Please report it privately through GitHub's **Report a vulnerability** button (Security tab). Do not open a public issue. Scope, response times and known limitations: [`SECURITY.md`](SECURITY.md).

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

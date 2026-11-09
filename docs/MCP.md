# OpenPulse for AI coding agents (MCP)

AI coding agents add, upgrade and pin dependencies faster than anyone reviews them. `openpulse mcp` is a [Model Context Protocol](https://modelcontextprotocol.io) server that lets an agent ask OpenPulse **before** it changes a dependency:

- Is this exact version end-of-life or out of support?
- Has the project or its distribution changed upstream (registry move, license change, support-model change)?
- Which advisories affect *this* version, not just this package?
- Which release lines are still supported, so I can pick one?

Every answer is evidence, not a decision. It names its sources, lists what it could not establish, and never presents UNKNOWN as safe. The agent and its human decide what to do.

> **Research software.** OpenPulse is an academic research instrument from [Ikarus AI Labs](https://ikaruslabs.net), not a commercial product or a security control. Agent behaviour with these tools has not been evaluated. See [Research status](../README.md#research-status).

## Install

```bash
pip install "ikarus-openpulse[mcp] @ git+https://github.com/IkarusAILabs/OpenPulse@v0.20.0"
openpulse mcp --help
```

To also verify PyPI provenance (attestations) in `dependency_status`, install the `provenance` extra as well (Python 3.11+): `ikarus-openpulse[mcp,provenance]`. It adds about 24 packages (sigstore and its dependencies), hash-locked in `requirements-provenance.lock`. Without it, the `provenance` field says NOT_PERFORMED and how to enable it.

OpenPulse is distributed as **`ikarus-openpulse`**. Don't `pip install openpulse`: that name on PyPI is an unrelated project (OpenQASM's pulse AST), and it has no `mcp` command. Until `ikarus-openpulse` is published on PyPI, install from the pinned release tag as above.

The MCP SDK is an **optional extra** and needs **Python 3.11 or newer** (MCP SDK 2.x requires it); the rest of OpenPulse still supports 3.10. Installing without `[mcp]` stays as small as before. The extra's dependencies are pinned and audited separately in [`requirements-mcp.lock`](../requirements-mcp.lock).

## Connect your agent

The server speaks MCP over **stdio**: the client starts `openpulse mcp` itself. Run it from your project's root (or pass `--root`) so `check_dependency_file` can read your manifests.

**Claude Code**

```bash
claude mcp add openpulse -- openpulse mcp
```

Add `--scope project` to share it with your team through the project's `.mcp.json`.

**Cursor** (`.cursor/mcp.json`), **Claude Desktop** (`claude_desktop_config.json`), **Windsurf** and most other clients:

```json
{
  "mcpServers": {
    "openpulse": { "command": "openpulse", "args": ["mcp"] }
  }
}
```

**VS Code / GitHub Copilot** (`.vscode/mcp.json`):

```json
{
  "servers": {
    "openpulse": { "type": "stdio", "command": "openpulse", "args": ["mcp"] }
  }
}
```

If `openpulse` is not on the client's `PATH` (common with virtualenvs and on Windows), either use the full path to the `openpulse` executable as `command`, or point the client at the virtualenv's Python interpreter:

```json
{
  "mcpServers": {
    "openpulse": {
      "command": "/path/to/venv/bin/python",
      "args": ["-I", "-m", "cli", "mcp"]
    }
  }
}
```

On Windows the interpreter is `Scripts\python.exe`, and JSON needs escaped backslashes:

```json
{
  "mcpServers": {
    "openpulse": {
      "command": "C:\\path\\to\\venv\\Scripts\\python.exe",
      "args": ["-I", "-m", "cli", "mcp"]
    }
  }
}
```

> **Keep `-I`.** MCP clients start servers inside your project, and a bare `python -m cli` puts the working directory first on Python's import path. Any project with its own `cli/` package (a common name) would then run *its* `cli/__main__.py` instead of OpenPulse. In a repository you don't trust, that means its code runs as soon as the client starts the server. `-I` (isolated mode, Python 3.10+) ignores the working directory, user site-packages and `PYTHON*` environment variables. On Python 3.11+ you can use `-P` instead, which only drops the working directory.

## Tools

| Tool | Arguments | Answers |
|---|---|---|
| `dependency_status` | `package` + `ecosystem` + `version`, **or** `image` | One dependency: end-of-life / end-of-support for its version, curated upstream changes, OSV advisories that affect this version, repository health as context |
| `check_dependency_file` | `path` (relative to the project root); optional `base_path` (an earlier copy of the file, also inside the root) or `trust_all` | Every pinned entry of a manifest (`requirements.txt`, `pyproject.toml`, `pom.xml`, `go.mod`, `Cargo.toml`), lockfile (`package-lock.json`, `poetry.lock`, `Cargo.lock`), CycloneDX/SPDX SBOM or image list. Unpinned entries are listed as skipped, never guessed. With `base_path`, the PyPI and npm dependencies added or changed since the base get trust checks (`trust`) |
| `project_lifecycle` | `project` (e.g. `django`, `nodejs`, `postgresql`) | Release cycles with end-of-life dates and which lines are supported today |

All three are annotated read-only. Agents typically call `dependency_status` before adding or upgrading a dependency, `check_dependency_file` after editing a manifest or lockfile, and `project_lifecycle` when choosing a version.

### Example answer

`dependency_status(package="django", version="4.2.11", ecosystem="PyPI")`, shown here with `--offline`:

```json
{
  "dependency": "django==4.2.11",
  "identity": { "project": "django", "resolved_via": "catalog", "identity_status": "VERIFIED" },
  "verdict": {
    "affected": true,
    "relationship": "AFFECTS_VERSION",
    "confidence": "CORROBORATED",
    "meaning": {
      "direct_scope": "member",
      "embedded_components": "not_evaluated",
      "availability": "not_evaluated",
      "maintenance_or_support": "not_evaluated",
      "security_consequence": "not_evaluated",
      "statement": "In the event's directly named scope. ..."
    },
    "reason": "django==4.2.11 is within event scope version 4.2"
  },
  "causes": [
    {
      "event": "evt-django-2026-eol-001",
      "type": "EOL",
      "relationship": "AFFECTS_VERSION",
      "direct_scope": "member",
      "scope_completeness": { "state": "declared", "basis": "...", "admits_negative": true },
      "evidence_confidence": "CONFIRMED",
      "evidence_urls": ["https://www.djangoproject.com/download/", "https://endoflife.date/django"]
    }
  ],
  "advisories": { "affecting_this_version": [], "package_level_unconfirmed_count": 0, "source": "osv.dev" },
  "sources": [
    { "source": "curated-events", "status": "ok", "records": 4 },
    { "source": "live lookups", "status": "disabled" }
  ],
  "not_established": ["live lookups"],
  "evaluation_context": {
    "mode": "current",
    "as_of": "2026-10-30T09:12:00Z",
    "max_evidence_age_days": 90,
    "freshness_bound_applied": true,
    "unresolved_identity": "undetermined"
  },
  "note": "OpenPulse evidence, not a decision: ... UNKNOWN means not established, never safe. NOT_AFFECTED means outside the cited evidence's directly named scope only, never safe: ..."
}
```

How to read an answer:

| Field | Meaning |
|---|---|
| `verdict.relationship` | `AFFECTS_VERSION` / `AFFECTS_ARTIFACT` / `AFFECTS_PACKAGE` (affected), `RELATED` (a match without established impact), `NOT_AFFECTED` (outside the directly named scope; not a clearance), `UNKNOWN` (nothing established) |
| `verdict.meaning` | Closed vocabularies to decide from, with no upstream text. `direct_scope` is member, excluded, undetermined, project_tie or no_association. `embedded_components`, `availability`, `maintenance_or_support` and `security_consequence` are `not_evaluated`: OpenPulse does not establish them, so neither a positive nor a negative says anything about them. `statement` is a fixed template. The same block is in evidence contract v1.2. |
| `causes` | The upstream events behind the verdict, only those about this project, each with its evidence URLs and `scope_completeness` (`state`, `basis`, `admits_negative`): whether the event's scope was declared complete, on what basis, and so whether it can support a negative at all |
| `evaluation_context` | The time frame of the answer, the same block as evidence contract v1.2 plus `mode`. The tools run in `current` mode: a NOT_AFFECTED needs evidence fetched within `max_evidence_age_days` (default 90) of `as_of` (now), and an older event becomes RELATED ("stale"), never a clearance. The Python API (`core.agent_tools`) also offers `mode="replay"` for re-evaluating recorded evidence; it applies no bound, sets `freshness_bound_applied: false`, adds "evidence currency" to `not_established` and says so in `note` |
| `advisories` | OSV advisories whose ranges include this version, listed with links. Advisories that only name the package are counted separately: their version applicability is not established |
| `sources` | Which sources answered, failed (`error`), had no data (`no-data`) or were off (`disabled`) |
| `trust` (`dependency_status`) | Every trust check for the dependency (track T, T-D, v0.13.0 X4), never part of the verdict. `checks`: `malicious`, `registry_existence`, `provenance`, `repository_linkage`, `dependency_confusion`, `lookalike`, and since v0.16.0 the reputation indicators `publisher_change`, `repository_moved` and `young_popular_repository`, described below. `summary`: counts per status. `attention`: each `CONFIRMED_MALICIOUS`, `VERIFIED_FAILURE` or `SUSPICIOUS_INCONCLUSIVE` record with its check and statement; review these. `selection_context`: what the agent said about why it asks (`intent`, capped and stripped; `name_source`, a closed vocabulary, `unrecognized` otherwise), labelled `supplied_by: agent` and `used_in_status: false`, or null. `time_frame`: records are live lookups at their `checked_at` (in replay mode, not as of the replay date) |
| `registry_existence` | `trust.checks` in `dependency_status` (track T, T-M1). Whether the PyPI or npm package and version exist in their registry, as records with a closed status: `VERIFIED_RELATIONSHIP` (found), `VERIFIED_FAILURE` (the registry answered 404: an identity fact, not evidence of malice), `NOT_PERFORMED` (unsupported ecosystem, offline, budget spent, registry unreachable, or a name outside the ecosystem's grammar). Each record has a fixed `statement`, the registry URL and `checked_at`. Never part of the verdict |
| `digest_integrity` | `check_dependency_file` on a `package-lock.json` or `poetry.lock` (track T, T-B4). Each locked digest is compared with what PyPI or npm publishes for that version. Counts per status: `VERIFIED_RELATIONSHIP` (every locked digest is published), `VERIFIED_FAILURE` (one isn't: the locked artifact is not the one the registry serves; each listed under `failures`), `MISSING_EVIDENCE` (the lockfile pins no usable digest), `NOT_PERFORMED` (the registry didn't answer, offline, budget spent, or capped past the per-file limit). Never part of a verdict |
| `provenance` | `trust.checks` in `dependency_status`, for a PyPI package with a version (track T, T-B1). PEP 740 attestations from PyPI's Integrity API are verified for up to 4 files of the release (wheels first) with `pypi-attestations`, and the publisher is cross-checked against the catalog's repository for curated packages. `VERIFIED_RELATIONSHIP` (verified; says where and how the files were built, **not** that they are benign), `VERIFIED_FAILURE` (an attestation doesn't verify, or the publisher names another repository), `MISSING_EVIDENCE` (no provenance published: most packages publish none, so not evidence of a problem), `NOT_PERFORMED` (the `[provenance]` extra isn't installed, offline, budget spent or PyPI unreachable). Never part of a verdict |
| `trust` (`check_dependency_file`) | With `base_path` (added or changed dependencies) or `trust_all` (every dependency); null otherwise (v0.12.0 U5). For PyPI and npm packages: `malicious`, `registry_existence`, `provenance` (PyPI), `repository_linkage`, `lookalike` and the three reputation indicators; for packages on the private-name list, `dependency_confusion` in place of `registry_existence`, `provenance`, `repository_linkage` and the reputation indicators, as in `dependency_status`. `counts` per check and status; `attention` lists each `CONFIRMED_MALICIOUS`, `VERIFIED_FAILURE` or `SUSPICIOUS_INCONCLUSIVE` record with its dependency. The live checks run for at most 40 packages per file (`live_checked`, `live_capped`), before the file-wide lookups so additions get the budget first; lookalike runs for every package. `not_supported` counts other ecosystems and images. Never part of a verdict. The CLI equivalent is `openpulse trust FILE --base EARLIER` |
| `dependency_confusion` | `trust.checks` in `dependency_status`, and `trust` for listed packages (track T, T-A3, v0.13.0 X2). Applies to PyPI and npm names on the project's private-name list, `.openpulse/private-packages.txt` under the server root: one `ecosystem:name` per line, `#` comments, read on every call. `SUSPICIOUS_INCONCLUSIVE`: a public package has the name, so if you did not publish it an installer may resolve it instead of yours. `MISSING_EVIDENCE`: no public package has it; the name is unclaimed and anyone can still register it. `NOT_PERFORMED`: no list, not listed, registry trouble, offline or budget. A listed package's `registry_existence` and `provenance` are `NOT_PERFORMED` (they describe the public package, not yours). Never part of a verdict. CLI: `openpulse confusion` |
| `repository_linkage` | `trust.checks` in `dependency_status` for PyPI and npm packages, and `trust` (track T, T-A4, v0.13.0 X3). Is the package from the GitHub repository its registry metadata claims (npm `repository`, PyPI `project_urls`)? Verified PyPI provenance settles it: `VERIFIED_RELATIONSHIP` if it names the claimed repository, `VERIFIED_FAILURE` if it names another. Otherwise the claimed repository's manifest at its default branch (`package.json`, `pyproject.toml`, `setup.cfg`; never `setup.py`) is read: `VERIFIED_RELATIONSHIP` if it names the package back, `SUSPICIOUS_INCONCLUSIVE` if it names another (monorepos and renames do this too). `MISSING_EVIDENCE`: no GitHub repository claimed, or no readable manifest. `NOT_PERFORMED`: registry or GitHub trouble, offline, budget, or a private package. Evidence: `claimed_repository`, `claimed_repositories`, `manifest`, `manifest_names` (when it is a valid name). Never part of a verdict |
| `malicious` | `trust.checks` in `dependency_status` for PyPI and npm packages, and `trust` (v0.13.0 X1). Asks OSV for malicious-package records (`MAL-`, the OpenSSF malicious-packages feed) for the package and version. `CONFIRMED_MALICIOUS` cites each record (`evidence.records`: id and osv.dev URL, 10 at most, `records_total`); a withdrawn record does not count. `MISSING_EVIDENCE` means no record, which is not evidence of safety: there is no verified outcome. `NOT_PERFORMED`: OSV gave no usable or complete answer, offline, or budget spent. Advisory text is never echoed. Never part of a verdict |
| `lookalike` | `trust.checks` in `dependency_status`, for PyPI and npm names (track T, T-A2). Rules: `separator` (equal without `-_.`), `edit_distance` (within 1 edit, 2 for names of 10+), `confusable` (UTS #39 ASCII skeleton: `1`/`I`/`|` as `l`, `0` as `O`, `m` as `rn`), `scope` (npm `@x/name` where `name` is a reference). References: the curated catalog and pinned popular-name lists (npm: npm-high-impact 1.13.0, MIT; PyPI: a dated download query, once a maintainer has run it). `SUSPICIOUS_INCONCLUSIVE` (rules fired, each naming its reference: an indicator, never a typosquat verdict), `VERIFIED_RELATIONSHIP` (the name is a reference), `MISSING_EVIDENCE` (nothing fired, which is not evidence the name is authentic). Local data only; never part of a verdict |
| `publisher_change` | `trust.checks` in `dependency_status` for PyPI and npm packages with a version, and `trust` (track T, T-C, threat T6, v0.16.0). Was this release published by someone the earlier releases were not? npm: `new_account` (the publishing account published none of the previous 9 releases, outside trusted publishing) and `trusted_publishing_dropped`. PyPI: `publisher_changed` (the verified provenance names another publisher than the latest earlier attested release, within 3 releases; `changed` names the fields) and `attestations_stopped`. `SUSPICIOUS_INCONCLUSIVE` names the rules that fired: handovers are legitimate, so never a takeover verdict. `VERIFIED_RELATIONSHIP`: the same publisher as before (continuity, not evidence of a benign release). `MISSING_EVIDENCE`: a first release, no publisher, no attestations to compare, or an npm release published through trusted publishing (its shared service account is no continuity, and npm names no repository to compare). `NOT_PERFORMED`: registry trouble, offline, budget, or a private package. npm accounts are compared as hashes and never named. Never part of a verdict |
| `repository_moved` | `trust.checks` in `dependency_status` for PyPI and npm packages, and `trust` (track T, T-C, v0.16.0). Does the claimed GitHub repository answer under another name? `SUSPICIOUS_INCONCLUSIVE` names both and the `move` (`renamed`: same owner; `transferred`: another owner); projects move to organisations routinely. `VERIFIED_RELATIONSHIP`: it answers under the claimed name, so the claim is current (not that the code is the package's; `repository_linkage` checks that). `MISSING_EVIDENCE`: no GitHub repository claimed, or GitHub does not know it. `NOT_PERFORMED`: registry or GitHub trouble, offline, budget, or a private package. Never part of a verdict |
| `young_popular_repository` | `trust.checks` in `dependency_status` for PyPI and npm packages, and `trust` (track T, T-C, threat T5, v0.16.0; experimental). `SUSPICIOUS_INCONCLUSIVE`: the claimed repository is younger than 180 days and has at least 1000 stars, with `age_days`, `stars` and both thresholds. Otherwise `MISSING_EVIDENCE`: stars are inputs, never trust evidence, so no star count verifies anything. `NOT_PERFORMED`: registry or GitHub trouble, offline, budget, or a private package. Shares one GitHub request with `repository_moved`. Never part of a verdict |
| `not_established` | What this answer does not cover. An unreachable source makes its part UNKNOWN, never "fine" |

## Where the answers come from

The tools use the same pipeline as `openpulse check`. There is one verdict engine, not a second matcher:

- **Lifecycle**: live [endoflife.date](https://endoflife.date) cycles go through the change analyst and the evidence gate and become events. A release line such as `4.2` covers its patch releases (`4.2.11`).
- **Curated upstream changes**: the same bundled events as the GitHub Action (Bitnami catalog, Bitnami Spark, Django 4.2 EOL, iText license).
- **Advisories**: [OSV](https://osv.dev) for the project's catalogued package.
- **Repository health**: GitHub repository metadata (archived flag, last push, license). This is shown as context only and never changes the verdict. Set `GITHUB_TOKEN` for higher rate limits.

Limits are stated in the answer, never applied silently (v0.11.0):

- **Lookup budget.** One server session makes at most 200 live lookups (one per project; cached answers are free). Every answer carries a `lookups` block: `budget`, `used`, `remaining`, `timeout_seconds_per_source` (10) and `cache_ttl_seconds` (3600). Past the budget, no lookup is made. The answer lists `live lookups (session lookup budget spent …)` under `not_established`, and `project_lifecycle` returns a tool error that says so. Curated events still answer.
- **Per-file cap.** A file check looks up at most 40 projects and 300 dependencies. Projects past the cap are listed in `live_lookups_capped`, and their answers say so under `not_established`.
- **Cache.** Lookups are cached for an hour within a session. `project_lifecycle` also caches across sessions on disk, in `OPENPULSE_CACHE_DIR` (default: the user cache directory, `openpulse/lookups`; set it to an empty value to disable), with the same one-hour TTL. A lookup with a source error is never cached. An answer served from the disk cache gives its age in `cached_age_seconds`.

## Security model

- **Read-only.** No tool writes or executes anything. The one exception is opt-in: with `--record DIR`, the server appends its own question-and-answer log to DIR (see *Recording* below).
- **Confined file access.** `check_dependency_file` only reads files inside the server's root (the directory it was started in, or `--root`). A prompt-injected agent cannot use OpenPulse to parse files elsewhere on the machine. Reads are size-bounded.
- **The private-name list is in the agent's reach.** An agent can edit `.openpulse/private-packages.txt` like any project file. Listing a public package there does not hide it: the existence and provenance checks give way to `dependency_confusion`, which reports the public package as `SUSPICIOUS_INCONCLUSIVE`, and `malicious` still runs. Review changes to the list like any other change to the project's dependencies.
- **Limited network.** The only hosts contacted are endoflife.date, api.osv.dev and api.github.com, plus, for the trust checks, pypi.org, registry.npmjs.org and raw.githubusercontent.com. `--offline` turns network access off entirely and answers from the curated events (`project_lifecycle` then explains that it needs live lookups).
- **No text comes back from the caller (v0.12.0).** Package names, versions, ecosystems and image refs must be identifiers (letters, digits and a few separators: no whitespace, control, bidi, zero-width or Markdown characters). A tool argument that isn't one is refused, and a file entry that isn't one is skipped. Neither is ever repeated in the answer, so a name can't carry an instruction back to the agent. The one free-text field, `intent` (v0.13.0), is returned only inside `trust.selection_context`, labelled `supplied_by: agent`, stripped of control, bidi and zero-width characters and capped at 280 characters.
- **Errors with reasons.** Bad input (a path outside the root, an unrecognised file, a missing package name) comes back to the agent as a tool error with the reason, not an opaque failure.

## Recording (opt-in, local)

`openpulse mcp --record DIR` appends one JSON line per tool call to `DIR/mcp-<session>.jsonl` (v0.13.0, M8). It is off unless you pass the flag, and **nothing is ever sent anywhere**: the files are yours to read, share or delete. It exists to answer research questions about how coding agents use dependency evidence: what they ask, what they are told, and what they say about why they ask (`intent`, `name_source`).

Each line (`schema: openpulse-mcp-record/1`) holds:
- `session`, `seq`, `at` and `openpulse_version`;
- `tool` and `arguments`, as the agent gave them, capped at 1000 characters each;
- `outcome`: `answer` or `error`, with the error message;
- `summary`: the verdict, trust statuses and selection context;
- `answer`: the full answer, unless it is over 256 KB, in which case `answer_omitted` is true.

What it does and doesn't do:
- **Answers:** recording never changes an answer.
- **Failures:** a write failure is reported once on stderr and stops recording; the tools keep working.
- **Permissions:** on POSIX the directory and files are owner-only.
- **Contents:** the log contains what the agent asked about, including file paths and package names. Treat it like any project log.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `the MCP server needs the optional SDK` | Install the `mcp` extra in the environment the client runs: the error message prints the exact command |
| `openpulse: command not found` after `pip install openpulse` | That installed an unrelated PyPI project. `pip uninstall openpulse`, then install `ikarus-openpulse` as above |
| Client cannot start the server | Use the absolute path to `openpulse` as `command`, or the venv interpreter with `["-I", "-m", "cli", "mcp"]` |
| Something other than OpenPulse starts (`python -m cli` config) | Your project has its own `cli/` package. Add `-I` before `-m` so the working directory is not searched |
| `outside the server's project root` | Start the server in your project (or pass `--root /path/to/project`) and pass paths relative to it |
| Everything is UNKNOWN | Check `sources`: a lookup may have failed (network, rate limit) or the project is not in endoflife.date / the catalog. UNKNOWN is not a clean result |

## Related

- [GitHub Action](GITHUB_ACTION.md): the same evidence in pull requests and Code Scanning.
- [Evidence contract](EVIDENCE_CONTRACT.md): the machine-readable verdict format behind `attest`, SARIF, DefectDojo and Dependency-Track output.
- [Methodology](METHODOLOGY.md): how verdicts, confidence and release-line scopes are decided.

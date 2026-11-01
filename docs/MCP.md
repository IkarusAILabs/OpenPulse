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
pip install "ikarus-openpulse[mcp] @ git+https://github.com/IkarusAILabs/OpenPulse@v0.9.0"
openpulse mcp --help
```

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
| `check_dependency_file` | `path` (relative to the project root) | Every pinned entry of a manifest (`requirements.txt`, `pyproject.toml`, `pom.xml`, `go.mod`, `Cargo.toml`), lockfile (`package-lock.json`, `poetry.lock`, `Cargo.lock`), CycloneDX/SPDX SBOM or image list. Unpinned entries are listed as skipped, never guessed |
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
| `not_established` | What this answer does not cover. An unreachable source makes its part UNKNOWN, never "fine" |

## Where the answers come from

The tools use the same pipeline as `openpulse check`. There is one verdict engine, not a second matcher:

- **Lifecycle**: live [endoflife.date](https://endoflife.date) cycles go through the change analyst and the evidence gate and become events. A release line such as `4.2` covers its patch releases (`4.2.11`).
- **Curated upstream changes**: the same bundled events as the GitHub Action (Bitnami catalog, Bitnami Spark, Django 4.2 EOL, iText license).
- **Advisories**: [OSV](https://osv.dev) for the project's catalogued package.
- **Repository health**: GitHub repository metadata (archived flag, last push, license). This is shown as context only and never changes the verdict. Set `GITHUB_TOKEN` for higher rate limits.

Live lookups are cached per server session, one fetch per project. A file check looks up at most 40 projects and 300 dependencies.

## Security model

- **Read-only.** No tool writes or executes anything.
- **Confined file access.** `check_dependency_file` only reads files inside the server's root (the directory it was started in, or `--root`). A prompt-injected agent cannot use OpenPulse to parse files elsewhere on the machine. Reads are size-bounded.
- **Limited network.** The only hosts contacted are endoflife.date, api.osv.dev and api.github.com. `--offline` turns network access off entirely and answers from the curated events (`project_lifecycle` then explains that it needs live lookups).
- **Errors with reasons.** Bad input (a path outside the root, an unrecognised file, a missing package name) comes back to the agent as a tool error with the reason, not an opaque failure.

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

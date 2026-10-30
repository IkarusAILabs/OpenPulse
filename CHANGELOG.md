# Changelog

All notable changes to OpenPulse. Versions follow semver; while the project is `0.x`, minor versions may change behavior and are called out under **Upgrade notes**. Intelligence-schema and evidence-contract versions are tracked separately (see `docs/EVIDENCE_CONTRACT.md`).

## Unreleased

### Fixed

- **A package name was an identity across ecosystems (F1).** This changes verdicts. Package dependencies resolved by name alone, so PyPI `redis` 6.2.0 was AFFECTS_VERSION under Redis server 6.2 end of life, although PyPI `redis` is redis-py, the Python client. The catalog also mapped the Redis server to PyPI `redis` for OSV queries, so redis-py advisories were attributed to the server. The decision-policy evaluation (`evaluation/`) found it; the conformance oracle could not, because it takes identity as given.
  - A package with a stated ecosystem now resolves through curated (ecosystem, name) mappings: the new `packages` list on catalog entries, plus their `osv` block.
  - A name that only shares an alias with a project whose packages are curated is now unresolved (RELATED), never that project.
  - Packages with no ecosystem (or purl's `generic`) resolve by name as before.
  - redis-py and node-redis are curated as their own projects, so PyPI and npm `redis` now have no association with Redis server events.
  - Redis declares no packages, and OSV queries for PyPI `redis` now go to `redis-py`.


**This changes verdicts.** All of the following could report NOT_AFFECTED (a clearance) for a dependency that is in an event's scope. They were found by the conformance audit in technical report TR-2026-01.

- **Multi-digest events checked only the first digest (D1).** When an event named several digests of one repository, a dependency pinning any digest after the first was cleared. Every named artifact is now compared: any match is AFFECTED, and one undetermined comparison (digest against tag) withholds the clearance.
- **OSV ranges collapsed to their last interval (D2).** `introduced 1.0, fixed 1.2, introduced 2.0, fixed 2.3` was read as `[2.0, 2.3)`, so `1.1` was cleared. Ranges are now walked as unions of intervals. `GIT` and unknown range types, and versions at or past a `limit`, are undetermined. An advisory is cleared only if every affected entry clears the version. Withdrawn advisories no longer assert anything.
- **A clearance from one event hid an unresolved one (D3).** The headline verdict is no longer NOT_AFFECTED while another event's cause is RELATED or AFFECTS_PROJECT. Per-cause verdicts were already kept, and `affected` is unchanged.
- **Heuristic identity excluded dependencies (D5).** "This image is a different project" now needs a VERIFIED resolution. `docker.io/bitnami/<x>` images that resolve only through the generic Bitnami namespace rule are RELATED to upstream `<x>` lifecycle events, not NOT_AFFECTED: they package that upstream release. Four goldens flipped, with the justification recorded in `tests/test_golden.py`.
- **Package-scoped events associated with every image.** An event scoped to packages (the iText licence change, for example) marked unrelated images RELATED. Only images of the event's project are now associated.
- **Version epochs were read as extra version segments (D6).** `1:1.0` (Debian/RPM) and `1!1.0` (PEP 440) were compared as `1.1.0`, so `2.5` against an OSV range `fixed: 1:1.0` was cleared although epoch 1 sorts above every epoch-0 version. Versions with an epoch separator are now not comparable: undetermined, never a clearance.
- **Numeric version suffixes were folded into the version (D8).** `1.0.0-1` was compared as `1.0.0.1`, so against an OSV `SEMVER` range `fixed: 1.0.0` the SemVer prereleases `1.0.0-0` and `1.0.0-1` were cleared, although they sort below `1.0.0`. The number after a prerelease marker was also ignored, so `1.0.0-rc1` equalled `rc2` and a fix in `rc2` cleared `rc1`. A version is now comparable only as a numeric core plus at most one known prerelease marker and number; bare numeric and build suffixes (`1.0.0-1`, `2.4.1-1`, `1.0.0+5`) are undetermined, and `rc1 < rc2`. `v`-prefixed versions (`v1.2`) are now comparable.
- **Different digests of one repository cleared each other.** OCI object levels are not recorded, so an event naming an image-index digest cleared a dependency pinned to one of its platform manifests. Digest inequality within a repository is now RELATED until levels are resolved.
- **Unmapped references named like a project were dropped as unrelated.** `github.com/etcd-io/etcd` resolves only to itself, so it was UNKNOWN against etcd events and ignored when summarising. An unmapped reference whose repository name is one the event's project is known by is now RELATED (identity unresolved). Four relocation goldens (capa, etcd, traefik, fbsdk) flipped UNKNOWN → RELATED for the new canonical path.
- **Any unmapped reference could be excluded or dropped (D10).** An unmapped reference resolves only to itself, and self-resolution was treated as a VERIFIED different project. So a version-scoped event (an EOL, say) cleared an unmapped mirror of its project, `docker.io/zzz/kvstore:3.5` against etcd 3.5, and an unmapped reference with an unrelated name was UNKNOWN against project-wide events, letting another event's clearance headline. Every unmapped reference is now RELATED (identity unresolved), whatever its name. Only a curated mapping to another project gives UNKNOWN or an identity exclusion. **This lowers the share of clearances for dependencies the catalog does not know.** The OpenTofu fork is now curated as its own project (`opentofu`), so Terraform EOL events still exclude it on that evidence.
- **Docker Hub host aliases were different registries (D9).** `index.docker.io/bitnami/nginx` and `registry-1.docker.io/bitnami/nginx` are the same image as `docker.io/bitnami/nginx`, but only the last was inside the Bitnami event's `docker.io/bitnami/*` scope, so the others were cleared. Both hosts now canonicalise to `docker.io`, for matching and identity alike.
- **SemVer prerelease ordering under SEMVER ranges (D11).** One generic comparator served every OSV range, and its marker table (`dev` < `alpha` < `beta` < `rc`, with `a` = `alpha` and `c` = `rc`) is PEP 440's, not SemVer's. SemVer orders prerelease identifiers lexically, so `1.0.0-dev` against `introduced 1.0.0-beta, fixed 1.0.1`, `1.0.0-a` against `fixed 1.0.0-alpha`, and `1.0.0-c` against `fixed 1.0.0-rc` were all cleared. Each range is now compared under its own scheme: `SEMVER` ranges by SemVer 2.0 precedence; `ECOSYSTEM` ranges by the advisory's ecosystem (PyPI: the generic grammar, which agrees with PEP 440 on the forms it accepts; npm, Go, crates.io: SemVer). Any other or missing ecosystem compares plain dotted numbers only, and equality reached only by zero padding (`1.0` vs `1.0.0`, which Debian orders) is undetermined.
- **`docker.io/<name>` was a different repository from `docker.io/library/<name>` (D12).** A two-segment reference whose first segment is a registry host was parsed with the host as the namespace, so `docker.io/redis:7.2` (Docker's spelling of the official image) was cleared by complete scopes naming `docker.io/library/redis`. Found by the TR-2026-01 conformance matrix (`conformance/`). Single-name repositories now go under `library` on Docker Hub only. The registry sweep's bare-namespace rule (`docker.io/<namespace>` names a catalogue) is now explicit instead of relying on the old parse.
- **Unmapped packages were dropped as unrelated (D13).** A package that resolves only to itself was "no applicable evidence" for other projects' events, the package-side twin of D10. It is now RELATED against project-wide, release-line and package scopes, and still has no association with container-image and registry scopes. **This makes uncatalogued packages RELATED to loaded lifecycle and licence events; the reason says the identity is unresolved.** `boto3` and `serde` are now curated as their own projects.
- **A repository element did not cover digest pins (D14).** `docker.io/acme/app` (or `:*`) against `docker.io/acme/app@sha256:...` was RELATED; a repository element covers every reference to the repository, so it is now AFFECTS_ARTIFACT.
- **A named example hid the event's scope (D15).** When a named affected artifact left a reference undetermined (a tag against an example digest), the event's own scope was never evaluated, so a member of its release line was only RELATED. Named examples and the scope are now evaluated together and the strongest result wins. Found by randomised differential testing against the TR-2026-01 oracle.
- **An image curated as another project is now "no association" for a release-line event, not an exclusion.** It was NOT_AFFECTED under a complete scope and RELATED under a partial one; a curated mapping to another project needs no complete scope (TR-2026-01 S2), and identity is now decided before the tag is read. Goldens for `docker.io/bitnami/redis` against a redis EOL and for OpenTofu against a Terraform EOL now expect UNKNOWN.
- **A package name absent from a package scope cleared the dependency.** Package names are not canonicalised per ecosystem, so a different spelling of the same package was NOT_AFFECTED under a complete package scope. Inequality is now RELATED.

### Added

- **Completeness basis (TR-2026-01 N3)**, intelligence schema 0.6.0 → **0.7.0** (additive). `Scope.basis` records why a scope declared complete is complete: `definitional`, `announced`, `corroborated` or `verified`. A declaration **without a basis never clears**: `exhaustive: true` alone now gives RELATED. The analyst's seven definitional declarations, and the Django EOL, Bitnami Spark (`definitional`) and Bitnami catalogue (`announced`) fixtures, record their basis. **Producers that set `exhaustive` must now set `basis` too.** The evidence contract does not carry it yet.
- **Event admissibility (TR-2026-01 N4, N5).** `OSSEvent.withdrawn` and `OSSEvent.superseded_by`: such events are not evaluated at all. An event whose own evidence includes a `contradicts` relation can associate a dependency but never clear it. `check_dependency` and `check_watchlist` take an opt-in freshness bound (`as_of`, `max_evidence_age`): a negative from an event whose newest evidence is older than the bound becomes RELATED (stale). The bound is off by default, since replaying recorded fixtures would otherwise make every negative stale.

- **`Scope.exhaustive` (D4)**, intelligence schema 0.5.0 → **0.6.0** (additive, **default `false`**: completeness is opt-in). A dependency outside a scope is NOT_AFFECTED only when the producer declares the scope complete; unspecified or partial scopes give RELATED. Analysts declare it where the scope is the event itself (one release line's EOL/EOS/support change, one repository's distribution or registry change); the Django EOL and Bitnami Spark fixtures declare it; package-removal, breaking-change, licence and support-change lists stay partial. The evidence contract is unchanged.
- **Namespace scope elements.** An artifact scope entry `<registry>/<namespace>/*` covers every repository under it. The curated Bitnami event now states its catalogue-wide scope this way (`docker.io/bitnami/*`, `docker.io/bitnamilegacy/*`, `registry-1.docker.io/bitnamicharts/*`) instead of five example images that were read as the complete scope -- which had cleared unlisted Bitnami images such as `bitnami/nginx`.
- **Element roles and tag predicates (TR-2026-01, envelope-aware positives; D7).** A plain namespace element (`docker.io/acme/*`) is now an *envelope*: it bounds the affected set, so membership is RELATED ("possibly in scope") and only exclusion from it is decisive. Every other element is *exact*, and membership is AFFECTS_ARTIFACT. Two tag predicates make exact elements expressible: `:<version>` (version-like tags such as `1.25` or `7.2.4-debian-12-r3`, not `latest`) and `:*` (every tag). A named affected artifact with a literal tag (`redis:7.2`) now establishes that tag only: another tag of the same repository is RELATED, not AFFECTS_ARTIFACT (D7). A scope element with a literal tag excludes the repository's other tags. A ref with no tag is read as `latest`; a digest-only ref under a tag-restricted element is RELATED. **This changes verdicts:** the Bitnami scope is now `docker.io/bitnami/*:<version>` (exact) plus `docker.io/bitnami/*` (envelope), with `bitnamilegacy/*:*` and `bitnamicharts/*:*`, so versioned Bitnami images stay affected while `bitnami/redis:latest` becomes RELATED instead of a false impact.

## 0.7.1 — 2026-10-28

A hardening patch. No verdict or output changes.

### Security

- **Collector responses are size-capped** (#155). Every collector (endoflife.date, OSV, GitHub, registries) now streams its HTTP response and stops at a byte cap (32 MiB by default), counting *decoded* bytes so a gzip bomb is caught. Oversized responses fail that source with an error instead of exhausting memory. This closes A6b, the last unbounded input channel.
- **Every install is hash-checked** (#156). CI, the MCP job and the GitHub Action install with `pip install --require-hashes` from complete, hash-pinned locks generated by `scripts/compile_locks.py`. A re-uploaded or tampered package with the same version now fails the install. `scripts/check_lock.py --exact` also fails CI on any installed package the lock doesn't list. The Action installs `requirements-runtime.lock` (no dev tools), then OpenPulse with `--no-deps`.

### Fixed

- **The lock was incomplete** (#156). `typing-inspection` (pulled in by pydantic) and `colorama` (Windows) weren't listed, so they floated. The locks are now resolved for every platform at once.

### Notes

- The `mcp` extra needs Python 3.11 or newer (MCP SDK 2.x requires it). The rest of OpenPulse still supports 3.10.

## 0.7.0 — 2026-10-28 "Channels"

OpenPulse reaches the places where dependency decisions are made: AI coding agents (MCP), DefectDojo and Dependency-Track. **This release changes verdicts** (#133, below), and the install name is now `ikarus-openpulse`. Read the upgrade notes before upgrading CI gates.

### Fixed

- **End-of-life events missed real version pins** (#133). Lifecycle events are scoped to release lines (`4.2`, `13`), but versions were compared for equality, so `django==4.2.11` or `postgres:13.5` against an end-of-life cycle was reported NOT_AFFECTED. Lockfiles and SBOMs always pin patch versions, so end-of-life detection rarely fired on real projects in `check`, `attest`, the GitHub Action and digests. A release line now covers its patch releases, variant tags like `13.5-alpine` match, and a version that cannot be compared is RELATED, never NOT_AFFECTED.
- **Installed packages shipped without their data** (#132). A non-editable install (PyPI or `pip install git+...`) had no catalog, so identities silently fell back to themselves, and `attest` had no contract schemas. The wheel now ships both, and CI installs the built wheel in a clean environment and tests it.

### Upgrade notes

- **Install name is now `ikarus-openpulse`.** `openpulse` on PyPI is an unrelated project (OpenQASM's pulse AST), and `pip install "openpulse[mcp]"` installed it. Install with `pip install "ikarus-openpulse[mcp] @ git+https://github.com/IkarusAILabs/OpenPulse@v0.7.0"` until the PyPI release lands. If you previously installed OpenPulse from git under the old name, run `pip uninstall openpulse` first, so two distributions don't claim the same modules. The CLI command is still `openpulse`.
- **Gates may start failing.** Because of #133, pinned dependencies inside an end-of-life release line now report AFFECTED. That is the intended verdict, but a CI gate using `--fail-on` (or the Action's `fail-on`) may now fail where it used to pass.

### Added

- **`python -m cli`** (#146) runs OpenPulse through the interpreter, for MCP clients that can't find the `openpulse` executable. Configure it as `["-I", "-m", "cli", "mcp"]`, or `-P` on Python 3.11+. Without the flag, the working directory is searched first, so a project's own `cli/` package would run instead of OpenPulse: in an untrusted repository, that means its code runs. See [`docs/MCP.md`](docs/MCP.md), which also shows the Windows interpreter path. Help and usage text read `openpulse` either way.
- **`openpulse mcp`: an MCP server for AI coding agents** (optional extra, `pip install "openpulse[mcp]"`). It provides three read-only tools:
  - `dependency_status`: end-of-life/end-of-support status, curated upstream changes and version-specific OSV advisories for one dependency.
  - `check_dependency_file`: the same checks for every pinned entry in a project file.
  - `project_lifecycle`: which release lines of a project are still supported.
- **Answers come from live sources.** Lifecycle data from endoflife.date, advisories from OSV and repository health from GitHub go through the same evidence gate and verdict engine as `check`. Results are cached per session.
- **Limits.** `check_dependency_file` only reads files inside `--root`. `--offline` limits answers to the bundled curated events.
- **Separate lock for the SDK.** The SDK and its dependencies are pinned in `requirements-mcp.lock`. A dedicated CI job installs that set, audits it and runs a real stdio session with the SDK client.
- **Guide:** [`docs/MCP.md`](docs/MCP.md) covers setup for Claude Code, Cursor, VS Code/Copilot, Claude Desktop and Windsurf, the tools, an example answer, the security model and troubleshooting.
- **DefectDojo export: `openpulse attest --defectdojo FILE`.** It writes DefectDojo's *Generic Findings Import* JSON, built from the same evidence contracts as the JSONL and SARIF outputs and producing one finding per SARIF result.
  - Severity follows impact: Critical, High, Medium, Low, or Info for RELATED and unknown dependencies. NOT_AFFECTED pairs are left out.
  - Each finding carries its evidence URLs, the recommendation, what could not be established, and the evidence-contract hash.
  - A stable `unique_id_from_tool` lets re-imports deduplicate.
- **Dependency-Track upload: `openpulse dependency-track --contracts FILE`.** It pushes affected findings as INTERNAL vulnerabilities, one per OpenPulse event (`OPENPULSE-<event id>`), each assigned to the matching components of a DT project.
  - Only affected pairs are pushed, and unmatched dependencies are reported.
  - Re-runs are idempotent.
  - The API key comes from `OPENPULSE_DTRACK_API_KEY` only.
  - HTTPS is required unless `--allow-http` is passed.
  - `--dry-run` shows the plan without sending anything.

## 0.6.3 — 2026-10-23

### Fixed

- **The action could not be published to the GitHub Marketplace.** Its `description` was 189 characters, and the Marketplace limit is under 125. It is now 105, and `tests/test_action_metadata.py` enforces the limit. No behavior change.

## 0.6.2 — 2026-10-23

Adds the GitHub Action. Intelligence schema **0.5.0** and evidence contract **v1.1** are unchanged.

### Upgrade notes

- `check --fail-on` now exits 1 when the threshold is breached without `--digest` too. If your CI used `--fail-on` without `--digest`, it may start failing on findings it used to pass.
- The action is used as `IkarusAILabs/OpenPulse@<sha>`. Its metadata file is the root `action.yml`, and its docs are in `docs/GITHUB_ACTION.md`.

### Added

- **GitHub Action** (root `action.yml`, Phase C3). A composite action runs `openpulse attest` on manifests, lockfiles, SBOMs and image lists, or discovers them in the repository. It writes a job summary, a SARIF 2.1.0 log for Code Scanning and the evidence-contract JSONL. It fails only on the `fail-on` threshold (default `action`). Coverage other than COMPLETE is a warning, never a pass. CI dogfoods the action against `data/fixtures` on Linux and Windows. Not yet on the Marketplace.
- `attest --sarif PATH`, `--summary PATH` and `--fail-on`. Every SARIF result cites its evidence URLs and the contract's `content_hash`. NOT_AFFECTED results are omitted. A dependency that no event applies to is reported once as an UNKNOWN note.

### Security

- CI build tooling moves to setuptools 84.1.0 (GHSA-xmj3-9gf7-h52w: a crafted wheel could write an `__init__.py` outside the install directory on Windows). The build requirement is now `setuptools>=84.1.0`.

### Fixed

- **`check --fail-on` was ignored without `--digest`.** The threshold only gated the digest output, so `check --fail-on action` exited 0 on an ACTION finding. It now gates both output shapes.

## 0.6.1 — 2026-10-21

The first release since **v0.5.0**. v0.6.0 was never tagged, so this release also ships everything listed under 0.6.0 below. Intelligence schema **0.5.0**, evidence contract **v1.1**.

### Fixed

- **Maven POMs with a namespace returned no dependencies** (#112). Almost every real `pom.xml` declares `xmlns="http://maven.apache.org/POM/4.0.0"`, and those files parsed to zero dependencies with no warning. They are now read correctly. If you checked Java projects with v0.6.0, re-run `check`.
- **Private-registry image refs collapsed to the hostname** (#113). `localhost:5000/team/redis:7` used to resolve to `localhost`, so every image on that registry shared one identity. Ports now stay part of the registry name.
- **SBOMs found inside GitHub repositories were never read** (#117). Repository inspection now ingests CycloneDX and SPDX files, where it used to mark coverage PARTIAL and skip them.
- **Locks could spin forever or be held twice** (#116). The observation store and the detection ledger now use OS advisory locks (`fcntl.flock` / `msvcrt.locking`). A crashed run releases its lock automatically, and a busy lock ends in a clean timeout.

### Security

- **Webhook secrets no longer leak into logs** (#115). On an HTTP error, `check --webhook` printed the full webhook URL, and for Slack/Teams/Discord the URL path is the credential. Errors now show only the status code and host. Redaction also covers `Bearer` credentials and GitHub/Slack token formats.
- **Every input file read is bounded** (#118). Size limits are now enforced on the read itself, so FIFOs and files that grow while being read are handled. Deeply nested JSON is a clean error instead of a crash. Covers SBOMs, lockfiles, manifests, image lists, events, watchlists and `--raw-bundle-dir` bundles.
- **Malformed identifiers are refused before any request** (#119). GitHub `owner/repo` values and Docker Hub namespace/repo names are validated before they are used in API URLs.
- **POM hardening** (#112). `<!DOCTYPE` is refused, and nesting depth and element count are capped.
- **certifi 2026.10.19** (PYSEC-2026-4320). The pinned CA bundle no longer trusts the compromised emSign root.
- **Vulnerability reporting.** `SECURITY.md` was added and GitHub private vulnerability reporting is enabled (#120).

### Added

- **`OPENPULSE_WEBHOOK_URL`** environment variable for `check --webhook`, so the URL stays out of the process list. GitHub tokens already read `GITHUB_TOKEN` / `GH_TOKEN`.

### Upgrade notes

- **Lock files.** `.lock` and `.ledger-lock` files now stay in `.openpulse/` as empty markers. That is expected; don't delete them while a run is in progress.
- **Webhook error text.** Delivery errors now read `webhook returned HTTP <code> from <scheme://host>`. Update any scripts that matched the old text.
- **GitHub URLs.** For `https://github.com/owner/repo.git`, the repository name is now `repo`; it used to be `repo.git`. Identifiers with `..`, `?`, `#` or extra separators are rejected.
- **POMs with a DTD** are refused with a clear error.

### Known limitations

These are planned for v0.7.0 (`docs/NEXT_PHASES.md`).

- **Local history is not tamper-proof yet.** The observation history and detection ledger are *corruption-detecting* (unkeyed hashes). Someone with write access to `.openpulse/` can rewrite them.
- **Webhook DNS rebinding.** The webhook SSRF check is still open to DNS rebinding.
- **Collector responses are uncapped.** HTTP response bodies from the data collectors are not yet size-capped.

## 0.6.0 — 2026-10-19 (not tagged; shipped in 0.6.1)

Everything since v0.5.0 (2026-10-04).

### Added

- **More dependency inputs.** These all go to the same verdict engine and work with both `check` and `attest`:
  - SPDX 2.x SBOMs (`--spdx`, #56)
  - npm / poetry / Cargo lockfiles (`--lockfile`, #58)
  - container image inventories with a tag-vs-digest pinning policy (`--images`, #59)
  - requirements.txt / pyproject.toml / pom.xml / go.mod / Cargo.toml manifests (`--manifest`, #69)
  - **GitHub repositories** (`--github-repo`, #92 / #100). Files are discovered recursively, and inspection is pinned to the commit and each file's blob SHA.
- **Inspection coverage.** Each repository inspection reports COMPLETE, PARTIAL or FAILED, with reasons. An inspection that couldn't read something is never reported as "no dependencies" (#100).
- **Early-warning views.**
  - `openpulse digest` shows upcoming and newly-effective changes from the detection ledger (#71).
  - `openpulse warnings` shows ranked deadlines with severity bands, with lead times measured from first trustworthy detection (#73).
  - Replayable lead-time case studies: `docs/LEAD_TIME_CASES.md`.
- **Evidence contract.**
  - `openpulse attest` emits one JSON document per dependency × event (#60, #70).
  - Standalone JSON Schema, a dependency-free validator, and a clock-independent content hash.
  - v1.1 adds the required `inspection_coverage` block. The v1.0 schema is unchanged.
- **Benchmark (M4) now has 11 scenarios**, with new golden scenarios for PostgreSQL, Kubernetes, Kafka, cert-manager, Grafana and Terraform. **M2 acceptance set closed:** capa and etcd ownership moves, traefik move, fbsdk archive + move, and the bitnami/spark empty mainline (#54, #55, #68, #72, #84, #85).
- **`openpulse --version`**, single-sourced from package metadata.

### Changed

- Intelligence schema 0.4.0 → **0.5.0** (additive).

### Security

- **Pagination guard.** Docker Hub pagination stays on the same host, so a response can't redirect requests elsewhere (#45).
- **CI updates.** CodeQL v4 (#46, #98); the lockfile was refreshed, and `check_lock.py` now also checks the `pyproject` version floors. CI fails if any test file is excluded, and its tooling is pinned (#100).
- **Dependabot** now only scans real dependencies; orphaned fixture manifests were removed (#99).

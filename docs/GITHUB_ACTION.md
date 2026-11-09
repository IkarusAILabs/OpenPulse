# OpenPulse GitHub Action

Runs `openpulse attest` on your dependency files in CI. It reports which upstream changes affect your dependencies: EOL, distribution and registry moves, license and support-model changes. Each finding cites its evidence. Results go to three places:

- **Job summary**: a Markdown table in `$GITHUB_STEP_SUMMARY` (verdict, impact, evidence links, contract hash).
- **SARIF 2.1.0**: a log you can upload to GitHub Code Scanning.
- **Evidence contracts**: one schema-valid 2.1 JSON document per dependency × event pair (see `docs/EVIDENCE_CONTRACT.md`).

The action needs no install step and no secrets. It runs on Linux, macOS and Windows runners.

> **Research software.** OpenPulse is an academic research instrument from [Ikarus AI Labs](https://ikaruslabs.net), and it comes with no warranty or service level. A passing run means no warning was raised, not that every dependency was cleared. See [Research status](../README.md#research-status).

## Verdicts and SARIF levels

| Verdict | SARIF level | Fails the job (default `fail-on: action`) |
|---|---|---|
| Affected, ACTION or CRITICAL impact | `error` | yes |
| Affected, REVIEW impact | `warning` | no (`fail-on: review` makes it fail) |
| Affected, WATCH/INFORMATIONAL impact | `note` | no |
| RELATED, AFFECTS_PROJECT, UNKNOWN | `note` | never |
| NOT_AFFECTED | omitted (counted in the summary) | never |

**Trust checks** (`trust` input, v0.14.0) are separate results under `openpulse/trust/<check>`, one per file, dependency, check and status. They are never verdicts, and the level is never a risk score:

| Trust record | SARIF level |
|---|---|
| Prohibited by the trust policy (including a blocklisted package) | `error`, and the step fails |
| CONFIRMED_MALICIOUS or VERIFIED_FAILURE, not prohibited | `warning` |
| SUSPICIOUS_INCONCLUSIVE, not prohibited | `note` |
| MISSING_EVIDENCE, VERIFIED_RELATIONSHIP, NOT_PERFORMED | omitted, unless the policy prohibits them |

The job summary lists them in their own *Trust checks* table.

Every result carries the evidence URLs and the `provenance.content_hash` of the contract it renders. You can recompute the hash from the contract's content.

**Unknown stays unknown.** If no event applies to a dependency, the action reports it once as a `note` under `openpulse/no-applicable-evidence`. It is never dropped. If repository inspection coverage is `PARTIAL` or `FAILED`, you get a warning annotation and the SARIF carries a tool notification. Both, and the job summary's coverage line, name what was not inspected by category with counts (unsupported dependency files, files over the size limit, a truncated tree, ...), and the SARIF run properties carry them as `inspection_coverage_categories` (v0.18.0). Partial coverage is never reported as a pass. With any `fail-on` other than `none`, FAILED coverage (a repository OpenPulse could not read) fails the job.

## Inputs

| Input | Default | Meaning |
|---|---|---|
| `manifest` | | `requirements.txt` / `pyproject.toml` / `pom.xml` / `go.mod` / `Cargo.toml` |
| `lockfile` | | `package-lock.json` / `poetry.lock` / `Cargo.lock` |
| `sbom` | | CycloneDX JSON |
| `spdx` | | SPDX 2.x JSON |
| `images` | | Container image inventory |
| `github-repo` | `${{ github.repository }}` | Used only when no path input is set: discovers dependency files through the GitHub API. It reads the **default branch**, so on `pull_request` use path inputs instead. |
| `events` | curated set | Event JSON paths, separated by whitespace or newlines. The default is the curated events bundled with the action: Bitnami catalog, Bitnami Spark, Django 4.2 EOL and the iText license change. The other files under `data/fixtures/` are test scenarios, not defaults. |
| `fail-on` | `action` | `affected`, `review`, `action`, `critical` or `none` |
| `github-token` | `${{ github.token }}` | Used for `github-repo` discovery and, with `trust: pull-request`, to read the base copies of the path inputs (needs `contents: read`). It is passed as an environment variable, never in argv, and is unset before `openpulse attest` runs with path inputs. |
| `trust` | `off` | `off`, `pull-request` (dependencies a pull request adds or changes) or `all`. Live lookups; see *Trust checks and a trust policy* |
| `registry-changes` | `off` | `off` or `all`: read npm and PyPI for each dependency's own release (live lookups); see *Registry changes of your dependencies* |
| `policy` | (empty) | Trust policy file; empty uses `.openpulse/policy.yml` when present |
| `gate` | (empty) | Dependency files for the pre-install gate. When set, the step runs only `openpulse gate`; see *Before install: the `gate` input* |
| `base-sha` | the pull request's base | Base commit for `trust: pull-request` and `gate` |
| `sarif-file` | `openpulse.sarif` | Where to write the SARIF log |
| `contracts-file` | `openpulse-contracts.jsonl` | Where to write the evidence-contract JSONL |
| `upload-sarif` | `false` | Upload the SARIF to Code Scanning (needs `security-events: write`) |
| `python-version` | `3.11` | Python version that runs OpenPulse, in an isolated venv |

**Outputs:** `sarif-file`, `contracts-file`, `inspection-coverage` (`COMPLETE`/`PARTIAL`/`FAILED`, or `NOT_APPLICABLE` when the run inspected no repository) and `threshold-breached` (`true` when `fail-on` or the trust policy failed the step).

The action installs OpenPulse's runtime dependencies from its own checkout with `pip install --require-hashes -r requirements-runtime.lock`, so every package is hash-checked against the reviewed lock, and then OpenPulse itself with `--no-deps`. The install goes into a venv under `$RUNNER_TEMP`, and the action exports that venv's path as `OPENPULSE_BIN`.

## Permissions

Grant the least privilege you need:

```yaml
permissions:
  contents: read          # always enough for path inputs and public-repo discovery
  security-events: write  # ONLY when upload-sarif: true (or a separate upload step)
```

On pull requests from forks, the token is read-only and SARIF upload fails. Keep `upload-sarif: false` there and rely on the job summary.


## Registry changes of your dependencies (v0.21.0)

`registry-changes: all` reads npm and PyPI for each npm and PyPI dependency's own release:

- the publisher's deprecation (npm `deprecated`) of the package or of your release;
- a yanked release (PEP 592) and a project that declares itself Inactive (PyPI);
- license changes in the releases after yours, which an upgrade would bring.

Each is a `warning` result under `openpulse/deprecation` or `openpulse/license-change`, with the registry page as evidence and an evidence contract like any other result. It is a `REVIEW` result, so it fails the step only with `fail-on: review` or `fail-on: affected`. A flag on one release is reported for that release only. The log says how many dependencies were read and names any whose registry gave no answer; other ecosystems are counted, not read. Off by default: an existing workflow stays offline and unchanged.

```yaml
      - uses: IkarusAILabs/OpenPulse@<full-commit-sha> # v0.20.0
        with:
          lockfile: package-lock.json
          registry-changes: all
          fail-on: action          # report registry changes, do not fail on them
```

## Trust checks and a trust policy (v0.14.0)

Two inputs bring track T's trust checks into the job. Both are off by default, so an existing workflow stays offline and unchanged.

| Input | Values | What it does |
|---|---|---|
| `trust` | `off` (default), `pull-request`, `all` | Trust checks with live lookups: known-malicious records, registry existence, provenance, repository linkage, lookalike names, and the reputation indicators (publisher change, moved repository, young repository with many stars). `pull-request` checks only the dependencies a pull request adds or changes, compared with the base branch's copy of `manifest` and `lockfile`. `all` checks every dependency on every run. Results are recorded in each contract's `trust_assurance` (evidence contract 2.4.0) |
| `policy` | a path, or empty | A trust policy ([`docs/TRUST_POLICY.md`](TRUST_POLICY.md)). Empty uses `.openpulse/policy.yml` when the repository has one. A prohibited condition fails the step, even with `fail-on: none` |

```yaml
on: pull_request
permissions:
  contents: read          # the base copies of the dependency files
jobs:
  openpulse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with: {persist-credentials: false}
      - uses: IkarusAILabs/OpenPulse@<full-commit-sha> # v0.20.0
        with:
          manifest: requirements.txt
          lockfile: poetry.lock
          trust: pull-request
          policy: .openpulse/policy.yml
```

How `trust: pull-request` works:
- **Base copies:** the action reads each file's base copy (`base-sha`, by default the pull request's base commit) through the GitHub contents API with `github-token`. The token goes to that one step as an environment variable and is unset before `openpulse attest` runs.
- **New files:** a file the pull request adds has no base copy, so all its dependencies count as added.
- **Unreadable base:** if a base copy can't be read for any other reason, the action warns and checks **every** dependency. A failure never narrows the checks.
- **Other events:** without a base commit (on `push` or `schedule`), trust checks are skipped with a notice. Use `trust: all` there.
- **Blocklist:** the policy's blocklist always applies to every dependency, since it needs no lookups.
- **Gate settings from the base branch:** the action also reads the base branch's copy of the policy (`.openpulse/policy.yml`, or the `policy` path) and of `.openpulse/private-packages.txt`, and uses them when they exist, so a pull request cannot weaken its own gate. If they can't be read, the action warns and uses the pull request's copies. Make the OpenPulse job a required status check so that removing the step blocks the merge. See *Bypass routes* in [`docs/TRUST_POLICY.md`](TRUST_POLICY.md).
- **`threshold-breached`:** this output is `true` when either `fail-on` or the policy failed the step. The log names each violation (`policy: PROHIBITED <condition>: <dependency>`).

## Before install: the `gate` input (v0.15.0)

Put the action before the step that installs dependencies, with `gate` naming the dependency files. It then runs only [`openpulse gate`](TRUST_POLICY.md#before-install-openpulse-gate): the trust policy, with no events, contracts or SARIF. A violation fails the step, so nothing is installed:

```yaml
on: pull_request
permissions:
  contents: read          # the base copies and the base branch's policy
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with: {persist-credentials: false}
      - id: openpulse
        uses: IkarusAILabs/OpenPulse@<full-commit-sha> # v0.20.0
        with:
          gate: requirements.txt poetry.lock
      # ... other steps ...
      - name: Install what the gate passed (verify first)
        env:
          RECEIPTS: ${{ steps.openpulse.outputs.receipts }}
        run: |
          "$OPENPULSE_BIN/openpulse" gate --verify-receipt "$RECEIPTS" \
            --require-receipt-for 'requirements*.txt' --require-receipt-for poetry.lock
          pip install --require-hashes -r requirements.txt
```

- **Pull requests:** each file is compared with its copy on the base commit, read through the contents API like `trust: pull-request`. A shallow checkout is enough. Only dependencies the pull request adds or changes are trust-checked. A file the pull request adds is checked in full.
- **Unreadable base:** the action warns and checks every dependency in that file. A failure never narrows the checks.
- **Settings from the base branch:** the policy (`.openpulse/policy.yml`, or a repository-relative `policy` path) and `.openpulse/private-packages.txt` come from the base branch when it has them. A pull request that weakens or deletes its policy is still gated by the base branch's.
- **Other events:** without a base commit (`push`, `schedule`), every dependency is checked.
- **Isolation:** OpenPulse runs in its own virtual environment, installed from its hash-locked runtime set, so the gate itself installs none of your dependencies. The job token reads the base files only and is removed before the trust lookups.
- **Outputs:** `threshold-breached` is `true` on a violation. `receipts` is the directory of gate receipts, one per gated file (v0.17.0 item G2). `sarif-file`, `contracts-file` and `inspection-coverage` are empty, and `upload-sarif` is ignored.
- **Verify before install:** the gate judges the files as they are when it runs. Run `openpulse gate --verify-receipt` on the `receipts` directory and the same files in the step that installs, so a file a later step changed is refused (exit 1) instead of installed. `--require-receipt-for` adds every existing file matching a pattern, so a dependency file a build step generated after the gate is refused too (v0.17.0 item G4). If the build generates a lockfile, put the action after that step. The action's virtual environment stays on `$OPENPULSE_BIN` for the rest of the job. See *Verify before install* in [`docs/TRUST_POLICY.md`](TRUST_POLICY.md).
- **Without a policy** the gate passes and says so.

## Pinning

Pin the action to a full commit SHA, as `.github/workflows/ci.yml` does for every action it uses:

```yaml
- uses: IkarusAILabs/OpenPulse@<full-commit-sha> # v0.20.0
```

The action pins its own dependencies by SHA too: `actions/setup-python` and `github/codeql-action/upload-sarif`.

## Example: pull requests that touch dependency files

```yaml
name: openpulse
on:
  pull_request:
    paths:
      - requirements*.txt
      - pyproject.toml
      - poetry.lock
      - package-lock.json
      - Cargo.toml
      - Cargo.lock
      - go.mod
      - pom.xml
      - images.txt
permissions:
  contents: read
jobs:
  openpulse:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write   # for upload-sarif; drop it with upload-sarif: false
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with: {persist-credentials: false}
      - uses: IkarusAILabs/OpenPulse@<full-commit-sha> # v0.20.0
        with:
          manifest: requirements.txt
          lockfile: poetry.lock
          fail-on: action
          upload-sarif: ${{ github.event.pull_request.head.repo.full_name == github.repository }}
```

## Example: weekly schedule (catches upstream changes with no PR)

Upstream changes happen whether or not you touch your dependencies. A scheduled run catches them.

```yaml
name: openpulse-weekly
on:
  schedule:
    - cron: '17 6 * * 1'   # Mondays 06:17 UTC
  workflow_dispatch:
permissions:
  contents: read
jobs:
  openpulse:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      # With no path inputs, the action discovers dependency files on the
      # default branch through the GitHub API. The checkout is only there
      # so the SARIF upload can resolve the commit and file paths.
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with: {persist-credentials: false}
      - id: openpulse
        uses: IkarusAILabs/OpenPulse@<full-commit-sha> # v0.20.0
        with:
          upload-sarif: 'true'
          fail-on: none            # report, do not fail the scheduled run
      - uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        with:
          name: openpulse-contracts
          path: ${{ steps.openpulse.outputs.contracts-file }}
```

## Limits (current)

- The gate counts ACTION/CRITICAL causes. Phase C3 asks for causes *backed by keyed-valid evidence*, which depends on keyed integrity (Phase B3), and that has not shipped yet. Until it does, the gate trusts the event's evidence as `attest` validates it today.
- Results are anchored to the input file, not to a line. Code Scanning shows them at file level.
- Image refs can produce `note` (RELATED) results for events scoped to packages: the engine cannot compare them, so it says so instead of guessing.
- Gate receipts are not signed: they prove, within one job, that the files installed are the ones the gate passed. Verify them in the same job that wrote them (the `receipts` output), never from an artifact a pull request controls.
- `--verify-receipt` checks the files it is given and those its `--require-receipt-for` patterns match. An install command that rewrites its lockfile while installing (`npm install`, not `npm ci`) changes it after the check.
- Not published to the GitHub Marketplace yet. That needs a tagged release.

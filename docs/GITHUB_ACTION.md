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

Every result carries the evidence URLs and the `provenance.content_hash` of the contract it renders. You can recompute the hash from the contract's content.

**Unknown stays unknown.** If no event applies to a dependency, the action reports it once as a `note` under `openpulse/no-applicable-evidence`. It is never dropped. If repository inspection coverage is `PARTIAL` or `FAILED`, you get a warning annotation and the SARIF carries a tool notification. Partial coverage is never reported as a pass. With any `fail-on` other than `none`, FAILED coverage (a repository OpenPulse could not read) fails the job.

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
| `policy` | (empty) | Trust policy file; empty uses `.openpulse/policy.yml` when present |
| `base-sha` | the pull request's base | Base commit for `trust: pull-request` |
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


## Trust checks and a trust policy (v0.14.0)

Two inputs bring track T's trust checks into the job. Both are off by default, so an existing workflow stays offline and unchanged.

| Input | Values | What it does |
|---|---|---|
| `trust` | `off` (default), `pull-request`, `all` | Trust checks with live lookups: known-malicious records, registry existence, provenance, repository linkage and lookalike names. `pull-request` checks only the dependencies a pull request adds or changes, compared with the base branch's copy of `manifest` and `lockfile`. `all` checks every dependency on every run. Results are recorded in each contract's `trust_assurance` (evidence contract 2.2.0) |
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
      - uses: IkarusAILabs/OpenPulse@<full-commit-sha> # v0.13.0
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
- **`threshold-breached`:** this output is `true` when either `fail-on` or the policy failed the step. The log names each violation (`policy: PROHIBITED <condition>: <dependency>`).

## Pinning

Pin the action to a full commit SHA, as `.github/workflows/ci.yml` does for every action it uses:

```yaml
- uses: IkarusAILabs/OpenPulse@<full-commit-sha> # v0.13.0
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
      - uses: IkarusAILabs/OpenPulse@<full-commit-sha> # v0.13.0
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
        uses: IkarusAILabs/OpenPulse@<full-commit-sha> # v0.13.0
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
- Not published to the GitHub Marketplace yet. That needs a tagged release.

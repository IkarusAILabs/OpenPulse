# Trust policy

A trust policy makes chosen trust conditions fail `openpulse check` and `openpulse attest` (track T, T-E1, v0.14.0). It is evaluated deterministically, with no model involved. Advisory MCP answers are not a security boundary: an agent can skip the call or ignore the answer. A policy in CI does not depend on the agent.

**Nothing blocks unless your policy names it.** Without a policy, gates behave exactly as before.

## The file

`.openpulse/policy.yml` is used when present. `--policy PATH` names another file.

```yaml
version: 1
prohibit:
  - confirmed_malicious              # any package
  - not_found_in_registry
  - digest_mismatch
  - condition: lookalike_name        # an indicator: name the packages it applies to
    packages: ["npm:@acme/*"]
  - condition: missing_provenance    # "provenance required for these packages"
    packages: ["PyPI:acme-*"]
blocklist:
  - "npm:event-stream"
  - "PyPI:requests==2.19.0"
```

- **Package patterns:**
  - written `ECOSYSTEM:NAME` or `ECOSYSTEM:NAME==VERSION`;
  - `*` and `?` are wildcards in the name;
  - PyPI names compare in normalized form (`Acme_Billing` matches `acme-*`).
- **Blocklist:** a package on it fails the run without any lookup.
- **Validation:** an invalid policy (unknown key or condition, a bad pattern, an indicator without `packages`) is refused with the reason, and the run stops.

## Conditions

Each condition is one trust check reaching one status. The labels come from the measurements in [`docs/research/TRACK_T_MEASUREMENTS.md`](research/TRACK_T_MEASUREMENTS.md).

| Condition | Check, status | Packages | Label |
|---|---|---|---|
| `confirmed_malicious` | `malicious`, CONFIRMED_MALICIOUS (an OSV `MAL-` record, cited) | any | measured |
| `not_found_in_registry` | `registry_existence`, VERIFIED_FAILURE | any | measured |
| `digest_mismatch` | `digest_integrity`, VERIFIED_FAILURE (lockfiles: `--lockfile`) | any | measured |
| `provenance_failure` | `provenance`, VERIFIED_FAILURE | any | measured |
| `repository_mismatch` | `repository_linkage`, VERIFIED_FAILURE | any | measured |
| `missing_provenance` | `provenance`, MISSING_EVIDENCE | **required** | measured |
| `lookalike_name` | `lookalike`, SUSPICIOUS_INCONCLUSIVE | **required** | indicator: fires on 18.8% of real popular npm names |
| `public_private_name` | `dependency_confusion`, SUSPICIOUS_INCONCLUSIVE | **required** | experimental |
| `unconfirmed_repository` | `repository_linkage`, SUSPICIOUS_INCONCLUSIVE | **required** | experimental |
| `blocklisted` (via `blocklist`) | the package matches a blocklist pattern | the list | — |

- **Experimental conditions** print a warning when a policy uses them: there is no organic false-positive set for them yet.
- **`not_found_in_registry`** also fires for an internal package served by a private index. List internal names in `.openpulse/private-packages.txt` first: listed packages skip the public-registry checks.

## How a run decides

- **Network:** the trust checks run only when the policy needs them. A blocklist-only policy makes no lookups.
- **Budget:** each dependency is checked once per run, within the same bounded budget as `attest --trust`. Digest checks need `--lockfile`.
- **Silence never blocks:** `NOT_PERFORMED` (a source unreachable, a spent budget) and `MISSING_EVIDENCE` never fail a run by themselves. Only a scoped condition such as `missing_provenance` makes missing evidence fail.
- **When it fails:** a violation prints `policy: PROHIBITED <condition>: <ecosystem>:<name>==<version>` with the check's fixed statement. The run exits 1 **after** every output is written (contracts, SARIF, DefectDojo, digest, webhook), alongside `--fail-on`.
- **Model-free:** the same files and the same source answers give the same decision.

## Before install: `openpulse gate`

`openpulse gate FILE...` applies the policy to dependency files on their own (track T, T-E2, v0.15.0). It needs no events, because it checks trust, not upstream changes. Run it where dependencies enter, before anything is installed:

```bash
openpulse gate requirements.txt poetry.lock --base-ref origin/main   # CI, before pip install
openpulse gate package-lock.json --base-ref HEAD                     # pre-commit
```

- **Comparison:** with `--base-ref`, each file is compared with its copy at that git ref (read with `git show`). Trust checks run only for dependencies added or changed since then; a file that is new since the ref counts entirely as added. `--base FILE` (one per file, in order) gives the copies explicitly. With neither, every dependency is checked.
- **The same evaluation as `check` and `attest`:**
  - the blocklist covers every dependency;
  - lockfile digests are checked for every entry whose hash changed;
  - `NOT_PERFORMED` never blocks.
- **Exit codes:** 0 when nothing prohibited is found, 1 on a violation, 2 on a usage error (an unknown ref, not a git repository, mismatched `--base`). Without a policy it passes and says so.
- **Files a hook may pass:** deleted files and files that are not dependency files are skipped with a note.
- **First commit:** in a repository with no commits yet, `--base-ref HEAD` treats every file as new. Any other unknown ref is still a usage error.

### In CI, before install

Gate the files before the step that installs them. With the GitHub Action, set its `gate` input (see *Before install* in [`docs/GITHUB_ACTION.md`](GITHUB_ACTION.md)). It reads the base copies and the base branch's policy through the API, so a shallow checkout is enough. Elsewhere, run the CLI from its own environment with the full history of the base branch:

```bash
git fetch --no-tags origin "$BASE_BRANCH"     # e.g. main; a shallow clone lacks it
openpulse gate requirements.txt poetry.lock --base-ref "origin/$BASE_BRANCH"
pip install --require-hashes -r requirements.txt
```

Install OpenPulse apart from the project (a separate virtual environment or `pipx`), so the gate runs before any project dependency is installed. The CLI reads the policy from the checked-out tree; protect `.openpulse/` with CODEOWNERS, or use the Action, which reads the base branch's.

### Pre-commit hook

The repository ships a [pre-commit](https://pre-commit.com) hook, `openpulse-gate` (v0.15.0 item Z2). Add it to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/IkarusAILabs/OpenPulse
    rev: v0.15.0  # the first release with the hook
    hooks:
      - id: openpulse-gate
```

- **What it runs:** `openpulse gate --base-ref HEAD` on the staged files named `requirements*.txt`, `pyproject.toml`, `poetry.lock`, `package-lock.json`, `Cargo.toml`, `Cargo.lock`, `go.mod` or `pom.xml`. A commit that touches none of them does not run it.
- **What it compares:** pre-commit hides unstaged changes while hooks run, so the gate sees the commit being made and checks only the dependencies it adds or changes.
- **Settings:** the policy and the private-name list are read from `.openpulse/policy.yml` and `.openpulse/private-packages.txt` at the repository root. Without a policy the hook passes.
- **Install:** pre-commit installs OpenPulse into its own environment (`language: python`). The trust checks query public sources; one that does not answer never blocks.
- **Not a boundary on its own:** `git commit --no-verify` skips every hook. Run the same gate in CI before install, as a required status check.

## Where violations and trust records show up

`openpulse attest --sarif` and `--defectdojo` (and the GitHub Action) report trust records and violations as their own results, never as verdicts. The level and the severity follow your policy, never an OpenPulse risk score:

| Trust record | SARIF level | DefectDojo severity |
|---|---|---|
| Prohibited by your policy, or blocklisted | `error` | High |
| CONFIRMED_MALICIOUS or VERIFIED_FAILURE, not prohibited | `warning` | Low |
| SUSPICIOUS_INCONCLUSIVE, not prohibited | `note` | Info |
| MISSING_EVIDENCE, VERIFIED_RELATIONSHIP, NOT_PERFORMED | omitted unless prohibited | omitted unless prohibited |

- **Grouping:** each record appears once per file, dependency, check and status, under `openpulse/trust/<check>`, with the https references the record cites.
- **Stable identities:** SARIF and DefectDojo share one identity per record, so re-imports deduplicate.
- **Job summary:** it has its own *Trust checks* table.
- **Without `--trust`:** trust records reach these outputs only through policy violations.

## Bypass routes

A gate is only as good as the routes around it. Each route below is pinned by a test in `tests/test_gate_bypass.py` (track T evaluation category 8: v0.14.0 Y5, and the pre-install routes v0.15.0 Z4), so a change in what the gate covers cannot pass unnoticed.

| Route | Covered? | How, or what to do instead |
|---|---|---|
| A dependency added only to the lockfile | Yes | `--lockfile` with `--base-lockfile` (the Action's `trust: pull-request`) checks every added or changed entry |
| A lockfile hash edited in place (same name and version, another artifact) | Yes | With `--base-lockfile`, digests are checked for every entry whose locked digests changed, not only for new versions |
| A blocklisted name respelled (`Evil_Pkg` for `evil-pkg`) | Yes | PyPI names compare in normalized form |
| An agent that ignores the MCP warning | Yes | CI evaluates the files again, with no model involved |
| A pull request that weakens its own policy or private-name list | Yes, in the Action with `trust: pull-request` | The Action uses the **base branch's** `.openpulse/policy.yml` (or the `policy` path) and `.openpulse/private-packages.txt` when they exist. A policy the pull request adds is used as is. With `trust: off` or `all`, the policy comes from the checked-out tree: protect `.openpulse/` with CODEOWNERS |
| A pull request that removes or edits the workflow step | No (outside OpenPulse) | Make the OpenPulse job a **required status check** with branch protection. A job that never runs then blocks the merge |
| An unpinned entry (`evil-pkg>=1.0`) | No | Unpinned entries are skipped, never guessed. Pin dependencies, or gate on the lockfile |
| A blocklist entry pinned to one version | No, by design | `PyPI:flask==3.0.0` matches that version only. Use `PyPI:flask` to block every version |
| A source that does not answer (offline, rate-limited) | No, by design | `NOT_PERFORMED` never blocks: silence is not evidence. The step log and `trust_assurance` record it |
| A dependency installed outside the files (`pip install x` in a build script) | No | The gate sees only its inputs. Install from the lockfile you gate, e.g. `pip install --require-hashes -r requirements.lock` |
| `git commit --no-verify` (or a hook never installed) | Yes, in CI | The hook is a convenience, not a boundary: every hook can be skipped locally. The CI gate compares with the base branch, so the skipped commit's additions are still checked. Run it as a required status check |
| A dependency file the hook's pattern does not name (`requirements/base.txt`, `constraints.txt`) | No, at commit | The hook selects `requirements*.txt` and the standard manifest and lockfile names. Widen it with `files:` in your `.pre-commit-config.yaml`, and list every file in the CI gate |
| A lockfile regenerated after the gate (`poetry lock`, `npm install` in a later step) | No | The gate judges the file as it is when it runs. Install with commands that refuse to change the lock (`npm ci`, `pip install --require-hashes`, `poetry install` after `poetry check --lock`), or run the gate again after any step that rewrites it |
| An install from a file the gate was not given (`pip install -r requirements-dev.txt`) | No | The gate sees only its inputs. Name every file you install from in the `gate` input or the `openpulse gate` command |
| An internal package missing from the private-name list | Partly | `not_found_in_registry` fires, but the public checks describe someone else's package. List internal names before prohibiting it |

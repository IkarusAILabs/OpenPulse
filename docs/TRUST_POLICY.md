# Trust policy

A trust policy makes chosen trust conditions fail `openpulse check` and `openpulse attest` (track T, T-E1, v0.14.0). It is evaluated deterministically, with no model involved. Advisory MCP answers are not a security boundary: an agent can skip the call or ignore the answer. A policy in CI does not depend on the agent.

**Nothing blocks unless your policy names it.** Without a policy, gates behave exactly as before. One exception: once a policy exists, `openpulse gate` also enforces `digest_mismatch` (v0.17.0, see *Before install*).

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
- **`unchecked: fail`** (the default) or **`unchecked: pass`:** what `openpulse gate` does when a prohibited check applied to a dependency but did not run. See "How a run decides".
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
| `publisher_change` | `publisher_change`, SUSPICIOUS_INCONCLUSIVE (a release published by an account, or a provenance publisher, the earlier releases did not use; or trusted publishing or attestations stopped) | **required** | indicator: fires on 4.6% of legitimate npm releases (`new_account`) and under 1% of PyPI releases |
| `repository_moved` | `repository_moved`, SUSPICIOUS_INCONCLUSIVE (the claimed repository answers under another name) | **required** | indicator: fires on 4.1% of legitimate repositories, all transfers to an organisation |
| `young_popular_repository` | `young_popular_repository`, SUSPICIOUS_INCONCLUSIVE (younger than 180 days, at least 1000 stars) | **required** | experimental: the organic set has one young repository |
| `blocklisted` (via `blocklist`) | the package matches a blocklist pattern | the list | — |

- **Experimental conditions** print a warning when a policy uses them: there is no organic false-positive set for them yet.
- **`not_found_in_registry`** also fires for an internal package served by a private index. List internal names in `.openpulse/private-packages.txt` first: listed packages skip the public-registry checks.

## How a run decides

- **Network:** the trust checks run only when the policy needs them. A blocklist-only policy makes no lookups.
- **Budget:** each dependency is checked once per run, within the same bounded budget as `attest --trust`. Digest checks need `--lockfile`.
- **Missing evidence:** `MISSING_EVIDENCE` never fails a run by itself. Only a scoped condition such as `missing_provenance` makes missing evidence fail.
- **A check that did not run:** a prohibited check that applied to a dependency but returned `NOT_PERFORMED` (a source unreachable or rate-limited, a spent lookup budget) is *unchecked*.
  - `openpulse gate` fails on it (exit 1, `policy: PROHIBITED unchecked <condition>: ...`), because a pre-install gate must not pass because a source was down. `unchecked: pass` in the policy restores the old behaviour.
  - `check --policy` and `attest --policy` print how many there were and do not fail on them.
  - A check that does not apply is never unchecked: npm packages have no PyPI provenance, a name on the private-name list skips the public-registry checks, `publisher_change` needs a version.
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
  - except that a prohibited check that did not run fails the gate (see above);
  - and except that the gate always enforces `digest_mismatch`, whatever the policy says (v0.17.0 item G3, decision 14). Every lockfile entry the change adds, or whose locked digests changed, is compared with the registry, and a digest the registry does not serve fails the gate. A policy without the rule gets it for every package (the gate prints `policy: digest_mismatch is implied by the gate`); a rule scoped to some packages is widened to all. A digest that could not be checked is unchecked, so it fails the gate unless the policy says `unchecked: pass`. `check` and `attest` still enforce the policy as written.
- **Exit codes:** 0 when nothing prohibited is found, 1 on a violation, 2 on a usage error (an unknown ref, not a git repository, mismatched `--base`) or a named file it cannot read. Without a policy it passes and says so.
- **Files it cannot read fail closed:** a named file that is not a readable dependency file (a malformed `package-lock.json`, a broken `pyproject.toml`, a README) exits 2: nothing in it was checked, so it is never a pass. Deleted files are skipped with a note.
- **Entries it does not check are listed:** lines that are not exactly pinned PyPI or npm packages (`flask>=2`, a bare `requests`) are printed as not checked. The lockfile pins them: gate the lockfile too.
- **First commit:** in a repository with no commits yet, `--base-ref HEAD` treats every file as new. Any other unknown ref is still a usage error.
- **Receipt:** `--receipt PATH` writes what was gated, whatever the outcome (v0.17.0 item G1), and `--verify-receipt` checks it before install (G2). See below.

### Gate receipts

The gate judges files as they are when it runs. `--receipt receipt.json` records that judgement, so the install step can show it installs the same bytes:

```bash
openpulse gate requirements.txt poetry.lock --base-ref origin/main --receipt gate-receipt.json
```

A receipt is a JSON document (`receipt_version` `1.0`) with a fixed set of fields:

| Field | Meaning |
|---|---|
| `tool` | `openpulse` and its version |
| `created_at` | when the gate ran (UTC) |
| `decision`, `exit_code` | `passed` (0), `failed` (1) or `error` (2) |
| `files` | every named file: `path` (normalised, forward slashes), `sha256`, and `status` `gated`, `unreadable` or `missing` |
| `policy`, `private_names` | path and SHA-256 of the policy and private-name list used, or `null` |
| `base` | `{"ref": ...}`, `{"files": [{path, sha256}]}`, or `null` without a base |
| `counts` | dependencies read, added or changed (`null` without a base), violations, unchecked checks |
| `violations` | each violation's `condition`, `check`, `status` and `dependency` label |

- **Hashed once, judged once:** each file is hashed before it is read and again after. A file that changed in between is an error (exit 2), so a receipt never names bytes the gate did not judge.
- **No upstream text:** violations carry the condition, the check, the status and the dependency label from your own file, never a statement (statements can quote advisory records).
- **Not a signature:** anyone who can write the files can write a receipt. It is an integrity record within one pipeline run: keep it in the job's workspace and verify it right before install (below).

### Verify before install

The gate judges the files as they are when it runs. Between the gate and the install, a later step can rewrite them. `--verify-receipt` checks, immediately before install, that the files are the bytes a passing gate judged (v0.17.0 item G2):

```bash
openpulse gate requirements.txt poetry.lock --base-ref origin/main --receipt gate-receipt.json
# ... other build steps ...
openpulse gate --verify-receipt gate-receipt.json requirements.txt poetry.lock \
  && pip install --require-hashes -r requirements.txt
```

- **Exit 0** only when every named file was recorded as gated by a receipt whose gate passed, and its SHA-256 now is the one recorded.
- **Exit 1**, with a `gate: REFUSED` line per problem, when a file changed since the gate, was not given to the gate, was recorded as unreadable or missing, or is missing now, or when a receipt records a gate that did not pass. Changed means reinspect: run the gate again.
- **Exit 2** when a receipt cannot be read (not JSON, not `receipt_version` 1.x, a malformed file list) or a directory holds no receipt: never a pass.
- **Several receipts:** `--verify-receipt` takes a receipt file or a directory of them (every `*.json` in it), and can be repeated. Every receipt must be a passing one, and a file recorded in several must match each. The GitHub Action writes one receipt per gated file into a directory (its `receipts` output).
- **Paths:** a named file matches a recorded path when both name the same file from the working directory, whatever the spelling (`./poetry.lock`, an absolute path). Verify from the directory the gate ran in.
- **It checks only what it is given.** Name every file the install reads, or give a pattern (below), and install with commands that do not rewrite them (`npm ci`, `pip install --require-hashes`).

### Generated dependency files

A lockfile a build step writes (`poetry lock`, `uv lock`, `npm install`, `pip-compile`) is a new file to the gate: what it pins was decided by that step, not by the change under review. Gate it **after** it is generated, and make sure nothing installs a generated file the gate did not see (v0.17.0 item G4):

1. **Generate**, then **gate** the generated files, with a receipt.
2. Any later step that rewrites them must be followed by the gate again.
3. **Verify** immediately before install, with a pattern for every dependency file the build can produce:

```bash
poetry lock
openpulse gate poetry.lock --receipt gate-receipt.json
# ... other build steps ...
openpulse gate --verify-receipt gate-receipt.json \
  --require-receipt-for poetry.lock --require-receipt-for '**/package-lock.json' \
  && poetry install --sync
```

- **`--require-receipt-for PATTERN`** (repeatable, with `--verify-receipt`): every existing file matching the glob, relative to the working directory, is verified like a named file. A generated file the gate never saw is refused (`not in the receipt`), and one regenerated after the gate is refused (`changed since the gate`). A pattern that matches nothing is noted, not refused: that file was not generated. With no named file and no match, there is nothing to verify, which is an error (exit 2). A pattern that leaves the project (`..`, an absolute path) is an error.
- **Still not covered:** an install command that rewrites the lockfile while it installs (`npm install`, `poetry install` without a current lock). It runs after the last check, so no gate can see what it pins. Install with commands that refuse to change the lock: `npm ci`, `pip install --require-hashes`, `poetry install` after `poetry check --lock`, `uv sync --locked`.

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
- **Install:** pre-commit installs OpenPulse into its own environment (`language: python`). The trust checks query public sources; a prohibited check that does not get an answer fails the hook unless the policy says `unchecked: pass` (see "How a run decides").
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
| A lockfile hash edited in place (same name and version, another artifact) | Yes | `openpulse gate` checks the digests of every entry whose locked digests changed, whatever the policy says (v0.17.0). `check` and `attest` do with `--base-lockfile` when the policy prohibits `digest_mismatch` |
| A blocklisted name respelled (`Evil_Pkg` for `evil-pkg`) | Yes | PyPI names compare in normalized form |
| An agent that ignores the MCP warning | Yes | CI evaluates the files again, with no model involved |
| A pull request that weakens its own policy or private-name list | Yes, in the Action with `trust: pull-request` | The Action uses the **base branch's** `.openpulse/policy.yml` (or the `policy` path) and `.openpulse/private-packages.txt` when they exist. A policy the pull request adds is used as is. With `trust: off` or `all`, the policy comes from the checked-out tree: protect `.openpulse/` with CODEOWNERS |
| A pull request that removes or edits the workflow step | No (outside OpenPulse) | Make the OpenPulse job a **required status check** with branch protection. A job that never runs then blocks the merge |
| An unpinned entry (`evil-pkg>=1.0`) | No | Unpinned entries are never guessed; the gate lists them as not checked. Pin dependencies, or gate on the lockfile |
| A blocklist entry pinned to one version | No, by design | `PyPI:flask==3.0.0` matches that version only. Use `PyPI:flask` to block every version |
| A source that does not answer (offline, rate-limited), or a spent lookup budget | Yes, in `openpulse gate` | A prohibited check that did not run fails the gate unless the policy says `unchecked: pass`. `check` and `attest` report the count without failing |
| A malformed or unrecognised dependency file | Yes, in `openpulse gate` | Exit 2: a file the gate cannot read is never a pass |
| A dependency installed outside the files (`pip install x` in a build script) | No | The gate sees only its inputs. Install from the lockfile you gate, e.g. `pip install --require-hashes -r requirements.lock` |
| `git commit --no-verify` (or a hook never installed) | Yes, in CI | The hook is a convenience, not a boundary: every hook can be skipped locally. The CI gate compares with the base branch, so the skipped commit's additions are still checked. Run it as a required status check |
| A dependency file the hook's pattern does not name (`requirements/base.txt`, `constraints.txt`) | No, at commit | The hook selects `requirements*.txt` and the standard manifest and lockfile names. Widen it with `files:` in your `.pre-commit-config.yaml`, and list every file in the CI gate |
| A file changed after the gate, before install (a later step rewrites `requirements.txt` or the lockfile) | Yes, with `--verify-receipt` | Write a receipt at the gate and run `openpulse gate --verify-receipt` on the same files immediately before install (v0.17.0). A changed file exits 1 |
| A lockfile regenerated after the gate (`poetry lock`, `npm install` in a later step) | Yes, with `--verify-receipt` | The regenerated file no longer has the gated SHA-256, so verification refuses it (v0.17.0). Gate again after any step that rewrites it |
| A dependency file generated after the gate, that the install step was not told about | Yes, with `--require-receipt-for` | Verify with a pattern for every dependency file the build can produce (`--require-receipt-for '**/package-lock.json'`): a matching file the gate never saw is refused (v0.17.0 item G4) |
| A lockfile the install command itself rewrites (`npm install`, `poetry install` with a stale lock) | No | It changes after the last check. Install with commands that refuse to change the lock (`npm ci`, `pip install --require-hashes`, `poetry install` after `poetry check --lock`, `uv sync --locked`) |
| An install from a file the gate was not given (`pip install -r requirements-dev.txt`) | No | The gate sees only its inputs. Name every file you install from in the `gate` input or the `openpulse gate` command |
| An internal package missing from the private-name list | Partly | `not_found_in_registry` fires, but the public checks describe someone else's package. List internal names before prohibiting it |

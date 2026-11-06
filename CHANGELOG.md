# Changelog

All notable changes to OpenPulse. Versions follow semver; while the project is `0.x`, minor versions may change behavior and are called out under **Upgrade notes**. Intelligence-schema and evidence-contract versions are tracked separately (see `docs/EVIDENCE_CONTRACT.md`).

## Unreleased

### Added

- **Gate receipts (v0.17.0 item G1).** `openpulse gate --receipt PATH` writes what the gate judged, whatever the outcome:
  - the SHA-256 of every named file (with its status: gated, unreadable or missing), of the policy and of the private-name list;
  - the base it compared with, the OpenPulse version, and the decision with its exit code;
  - every violation and unchecked check, as condition, check, status and dependency label, never a statement.

  Each file is hashed before and after it is read; a file that changed in between fails the gate (exit 2). A receipt is an integrity record within one pipeline run, not a signature. See "Gate receipts" in [`docs/TRUST_POLICY.md`](docs/TRUST_POLICY.md). Verifying it before install is item G2.
- **Verify before install (v0.17.0 item G2).** `openpulse gate --verify-receipt RECEIPT FILE...` exits 0 only when every named file was gated by a passing gate and still has the SHA-256 it recorded. A file that changed, was not gated, or comes from a gate that did not pass exits 1; an unreadable receipt exits 2. It takes a receipt or a directory of receipts, repeatable. The GitHub Action's `gate` input writes one receipt per file and names their directory in a new `receipts` output, so the install step can verify first. See "Verify before install" in [`docs/TRUST_POLICY.md`](docs/TRUST_POLICY.md).
- **Generated dependency files (v0.17.0 item G4).** `--verify-receipt` takes `--require-receipt-for PATTERN` (repeatable): every existing file matching the glob must be covered by a passing receipt, so a lockfile a build step generated or regenerated after the gate cannot reach install unverified. A pattern that matches nothing is noted, not refused. The generate-then-gate-then-verify order is documented under "Generated dependency files" in [`docs/TRUST_POLICY.md`](docs/TRUST_POLICY.md). `openpulse gate` with no file is now a usage error from the gate itself (exit 2, as before).

### Changed

- **`openpulse gate` always checks changed lockfile digests (v0.17.0 item G3, decision 14).** Once a policy exists, the gate enforces `digest_mismatch` for every package, whatever the policy says. A lockfile hash edited in place (same name and version, another artifact) can no longer pass a policy that forgot the rule. A scoped `digest_mismatch` rule is widened to every package in the gate. `check` and `attest` enforce the policy as written.

### Upgrade notes

- **A gate with a policy now asks the registry about changed lockfile entries**, even when the policy does not prohibit `digest_mismatch`. If PyPI or npm cannot be reached, that check is unchecked and fails the gate, as any prohibited check does. Set `unchecked: pass` in the policy to restore passing on unchecked checks. A gate without a policy is unchanged.

## 0.16.1 — 2026-11-03

A patch for one crash. Nothing else changes; no upgrade notes.

### Fixed

- **`openpulse gate` no longer crashes when a private-name list is in use.** Since v0.15.0 the gate loaded `.openpulse/private-packages.txt` (or `--private-names`) and then passed the loaded names where a file path was expected, so any gate whose policy needs trust checks died with a `TypeError` (exit 1) instead of gating. The GitHub Action passes the base branch's list whenever it has one, so every Action gate in such a repository failed this way. `attest` now also tells the policy which dependencies are private, so they are no longer counted as unchecked. Regression tests in `tests/test_gate_command.py`.

## 0.16.0 "Reputation Evidence" — 2026-11-03

Track T Phase 2 (T-C): three reputation indicators, each measured on a recorded set of real, legitimate packages before it shipped, and each reported on its own, never summed and never a verdict.
- **`publisher_change`:** a release published by an npm account, or a PyPI provenance publisher, that the earlier releases did not use, or without the trusted publishing or attestations they had.
- **`repository_moved`:** the claimed repository answers on GitHub under another name (renamed or transferred).
- **`young_popular_repository`:** a repository younger than 180 days with at least 1000 stars (experimental: too few young repositories to measure a rate).
- **Where they appear:** the `trust` block, evidence contract 2.3.0 (additive; 2.2 unchanged beside it), the trust policy (scoped to named packages), SARIF and DefectDojo.

The release also closes a security review: the gate fails closed, history committed to the repository is refused, and `--github-repo` no longer reports COMPLETE coverage after skipping files it cannot read. Verdicts and the frozen evaluation are unchanged. **Upgrade notes** below cover the stricter gate, refused tracked state and contract 2.3.0.

### Upgrade notes

- **`openpulse gate` fails closed.** A named file it cannot read exits 2 (it was skipped with exit 0). A check your policy prohibits that could not run (a source down, a spent lookup budget) fails the gate as `PROHIBITED unchecked <condition>`. To keep the old behaviour for unreachable sources, set `unchecked: pass` in `.openpulse/policy.yml`. Nothing changes without a policy except unreadable files.
- **Tracked local history is refused.** `check`, `digest`, `warnings`, `report`, `observe` and `sweep` exit 2 when git tracks the observation store, the detection ledger or the webhook delivery state. Untrack the file, or point `--store`, `--ledger` or `--delivery-state` outside the repository.
- **`openpulse attest` emits evidence contract 2.3.0.** A consumer that accepts exactly 2.2.0 rejects it; validate against `schemas/evidence-contract/v2.3/schema.json`. Documents without the three new check names are otherwise identical to 2.2.
- **`--github-repo` may now read PARTIAL where it read COMPLETE.** Dependency files OpenPulse cannot read (`yarn.lock`, `uv.lock`, `requirements-dev.txt`, ...) are listed as not inspected. `check --fail-on-partial` therefore fails on such a repository; `--fail-on` and `--strict` still fail only on FAILED coverage.

### Added

- **The organic reputation set, measured first (track T Phase 2, T-C; v0.16.0 item Q1).** The reputation indicators (publisher change, moved repository, young repository claiming popularity) are measured on real, legitimate packages before they ship.
  - **Recorder:** `benchmarks/record_reputation.py` records 60 npm packages (a fixed-stride sample of the pinned high-impact list) and 80 PyPI packages (the curated catalog and OpenPulse's own locked dependencies), each with its latest 10 releases and its GitHub repository, into `benchmarks/fixtures/reputation/organic-<date>.json`.
  - **What is stored:** who published each release (npm accounts only as hashes; the trusted-publishing provider; PyPI's provenance publisher), whether it carries attestations, and the repository's answered name, age, stars and flags. Every upstream string is validated first; no account name or e-mail is stored.
  - **Baseline:** `benchmarks/trust.py` reports the raw signal rates on the set (see [`docs/research/TRACK_T_MEASUREMENTS.md`](docs/research/TRACK_T_MEASUREMENTS.md)): the upper bounds each indicator rule has to improve on.
- **`publisher_change`: was this release published by someone the earlier ones were not? (threat T6; v0.16.0 item Q2).** `core/publisher_change.py` compares one release with the releases before it and names each rule that fires, as `SUSPICIOUS_INCONCLUSIVE` (an indicator, never a takeover verdict):
  - **npm `new_account`:** the publishing account published none of the previous 9 releases, and the release was not published through trusted publishing (which uses one shared service account).
  - **npm `trusted_publishing_dropped`:** an earlier release used trusted publishing, this one did not.
  - **PyPI `publisher_changed`:** the provenance names another publisher than the latest earlier attested release's (within 3 releases); the record says which fields changed.
  - **PyPI `attestations_stopped`:** no provenance, after a release that had it.
  - **Measured on the organic set:** `new_account` flags 4.6% of legitimate npm releases (projects with several maintainers), `publisher_changed` 0.3% and `attestations_stopped` 0.4% of PyPI releases, `trusted_publishing_dropped` none. Same publisher as before is `VERIFIED_RELATIONSHIP` (continuity, not evidence of a benign release). npm accounts are compared as hashes, never named.
- **`repository_moved`: does the claimed repository answer under another name? (v0.16.0 item Q3).** `core/repository_moved.py` asks GitHub for the repository a package claims, following one redirect within `api.github.com` only.
  - **Another name:** `SUSPICIOUS_INCONCLUSIVE`, naming both and whether it was `renamed` (same owner) or `transferred`. **Same name** (case ignored): `VERIFIED_RELATIONSHIP`, meaning only that the claim is current. No claim, or GitHub does not know the repository: `MISSING_EVIDENCE`.
  - **Measured on the organic set:** 5 of 123 legitimate repositories (4.1%) were moved, all transferred to an organisation, so this is an indicator to scope, not a gate.
- **`young_popular_repository`: many stars on a young repository? (threat T5; v0.16.0 item Q4).** `core/young_popular_repository.py` reads the creation date and star count of the repository a package claims (the same GitHub request as `repository_moved`).
  - **Younger than 180 days with at least 1000 stars:** `SUSPICIOUS_INCONCLUSIVE`, with the age, the count and both thresholds. Anything else is `MISSING_EVIDENCE`: stars are inputs, never trust evidence, so no star count verifies anything.
  - **Experimental:** the organic set holds one repository younger than 180 days, a legitimate project the rule flags (1 of 123, 0.8%). That is too few young repositories to measure a firing rate, so the indicator ships experimental.

- **The reputation indicators in the trust results, evidence contract 2.3.0 and the trust policy (v0.16.0 item Q5).**
  - **Trust block:** `dependency_status`, `check_dependency_file` and `openpulse trust` report `publisher_change`, `repository_moved` and `young_popular_repository` beside the existing checks, for PyPI and npm packages. A package on the private-name list gets `NOT_PERFORMED` for all three. Each spends one lookup from the session budget; `repository_moved` and `young_popular_repository` share one GitHub request. `attest --trust` allows 7 lookups per dependency (was 4).
  - **Evidence contract 2.3.0:** additive. `trust_assurance` may name the three new checks; nothing else changes, and the 2.2 schema is published unchanged beside it. `openpulse attest` emits 2.3.0. See [`docs/EVIDENCE_CONTRACT.md`](docs/EVIDENCE_CONTRACT.md).
  - **Trust policy:** three new conditions, each requiring `packages`: `publisher_change` and `repository_moved` (indicators, with the organic rates measured), and `young_popular_repository` (experimental: a policy that uses it gets a warning). See [`docs/TRUST_POLICY.md`](docs/TRUST_POLICY.md).
  - **SARIF and DefectDojo:** the indicators appear as `openpulse/trust/<check>` notes, or errors where the policy prohibits them, like the other trust checks.
  - **Measurements:** synthetic cases for the three checks (no false positive on the negatives) and the degraded runs (no claim without evidence when sources are down or the budget is spent).

### Fixed

- **`publisher_change` no longer reads npm trusted publishing as continuity (v0.16.0 item Q6).** A release published through trusted publishing carries npm's one shared service account, so matching an earlier trusted release's account was reported `VERIFIED_RELATIONSHIP` even when the trusted-publishing configuration had moved to another repository (npm's metadata names no repository or workflow to compare). Such a release is now `MISSING_EVIDENCE` ("trusted_publishing"). Dropping back from trusted publishing to a token still fires `trusted_publishing_dropped`. New synthetic case rp-3b.
- **End-to-end echo, degraded-run and adversarial identity tests for the reputation indicators (v0.16.0 item Q6).** `tests/test_reputation_adversarial.py` runs the indicators through the trust block, contract 2.3.0, SARIF, the summary and DefectDojo:
  - hostile repository names, publisher accounts, provider ids and repository metadata reach no output;
  - GitHub or registry trouble is `NOT_PERFORMED`, and a prohibited indicator that did not run is reported unchecked;
  - a claimed GitHub page (`sponsors`, `orgs`, `marketplace`, `*.github.io`, gists) is no repository and GitHub is never asked about it;
  - a claim of someone else's popular repository verifies only that the claim is current: stars are no indicator, and `repository_linkage` flags the name mismatch;
  - a transfer to an unrelated owner is an indicator, never a verdict.
- **`--github-repo` no longer drops dependency files it cannot read (track T Phase 12, S1).** Discovery recognised exact file names only, so a repository whose dependencies live in `yarn.lock`, `pnpm-lock.yaml`, `uv.lock`, `Pipfile`, `Pipfile.lock`, `bun.lock`/`bun.lockb`, `gradle.lockfile`, `environment.yml`, `setup.py`, `setup.cfg`, a requirements variant (`requirements-dev.txt`, `requirements/*.txt`, `constraints*.txt`) or a `package.json` with no `package-lock.json` beside it was inspected with no skip reason and could read **COMPLETE**. Each such file is now listed as "dependency file not supported; its dependencies were not inspected" and coverage is **PARTIAL**. Nothing new is parsed; files under `node_modules`, `vendor` and hidden directories stay out of scope as before.
- **`openpulse gate` fails closed (security review P1-1, P1-2).**
  - **A file it cannot read** (a malformed `package-lock.json`, a broken `pyproject.toml`, any named file that is not a dependency file) now exits 2. It used to be skipped with exit 0, so a file pip or npm would still consume could pass the gate unchecked.
  - **A prohibited check that did not run** (a source unreachable or rate-limited, a spent lookup budget) now fails the gate as `PROHIBITED unchecked <condition>`. It used to pass, so an OSV outage or a change with many dependencies switched off `confirmed_malicious`. Checks that do not apply (npm has no PyPI provenance, private names skip the public checks) never count. The policy key `unchecked: pass` restores the old behaviour; `check` and `attest` print the count and do not fail on it.
  - **Entries it does not check are listed:** lines that are not exactly pinned packages (`flask>=2`, a requirements file of bare names) are printed as not checked instead of being skipped silently.
- **Local history committed to the repository is refused (security review P1-3).** `check`, `digest`, `warnings`, `report`, `observe` and `sweep` exit 2 when git tracks the observation store, the detection ledger or the webhook delivery state: state from the repository could move lead-time claims or mark alerts as already delivered. Untrack it, or point `--store`, `--ledger` or `--delivery-state` elsewhere.
- **`SECURITY.md` and the roadmap describe the current product (security review P1-4).** `SECURITY.md` no longer says there are no package-trust checks or that 0.11.x is the supported release; the track T roadmap section is marked active with what each release implemented.
- **GitHub pages are no longer read as repositories.** A project URL such as `https://github.com/sponsors/<user>` (a Funding link) was parsed as the repository `sponsors/<user>`; GitHub's reserved paths (`sponsors`, `orgs`, `marketplace` and others) are now rejected. This affects `repository_linkage`, which could look up such a page as the claimed repository, and the reputation recorder, which now ranks claims like the checks do.

## 0.15.0 "Pre-Install Gates" — 2026-11-02

Track T Phase 4 (T-E2): the v0.14 trust policy now also applies where dependencies enter, before anything is installed. The same policy that fails CI fails a commit and a pre-install CI step, with no model involved.
- **`openpulse gate`:** applies the policy to dependency files alone, comparing with a git ref so only what changed is trust-checked.
- **Pre-commit hook:** `openpulse-gate` checks the dependencies a commit adds or changes.
- **The Action's `gate` input:** runs before `pip install` or `npm ci`, with the base branch's files and policy, on a shallow checkout.
- **Bypass routes:** `--no-verify` is caught by the CI gate. A lockfile regenerated after the gate, an ungated file, and file names outside the hook's pattern are documented limits, each with a workaround.

Nothing new blocks without a policy, and verdicts, the evidence contract and the frozen evaluation are unchanged. No upgrade notes.

### Added

- **`openpulse gate`: the trust policy before install (track T, T-E2, v0.15.0 item Z1).** `openpulse gate FILE... [--base-ref REF | --base FILE...] [--policy PATH]` applies the trust policy to dependency files alone, with no events needed. It is for a CI step before `pip install` or `npm ci` (`--base-ref origin/main`), and for a pre-commit hook (`--base-ref HEAD`). See [`docs/TRUST_POLICY.md`](docs/TRUST_POLICY.md), "Before install".
  - **Comparison:** with `--base-ref`, each file's copy at that ref is read with `git show`, and trust checks run only for added or changed dependencies. A file new since the ref counts as added.
  - **The same evaluation as `check` and `attest`:** the blocklist covers every dependency, lockfile hashes edited in place are caught, and `NOT_PERFORMED` never blocks.
  - **Exit codes:** 0 pass, 1 violation, 2 usage error. Without a policy it passes and says so. Deleted and non-dependency files are skipped.
- **Pre-commit hook `openpulse-gate` (v0.15.0 item Z2).** `.pre-commit-hooks.yaml` runs `openpulse gate --base-ref HEAD` on staged dependency files (`requirements*.txt`, `pyproject.toml`, `poetry.lock`, `package-lock.json`, `Cargo.toml`, `Cargo.lock`, `go.mod`, `pom.xml`), so a commit is checked only for the dependencies it adds or changes. See [`docs/TRUST_POLICY.md`](docs/TRUST_POLICY.md), "Pre-commit hook".
  - **First commit:** `openpulse gate --base-ref HEAD` in a repository with no commits treats every file as new instead of failing. Any other unknown ref is still a usage error.
- **The Action's `gate` input: the trust policy before install (v0.15.0 item Z3).** With `gate: <dependency files>`, the Action runs only `openpulse gate` (no events, contracts or SARIF), so it can sit before `pip install` or `npm ci`. See [`docs/GITHUB_ACTION.md`](docs/GITHUB_ACTION.md), "Before install".
  - **Pull requests:** base copies come through the contents API (a shallow checkout is enough), and only added or changed dependencies are trust-checked. An unreadable base copy means that file is checked in full.
  - **Settings:** the policy and the private-name list come from the base branch when it has them, so a pull request cannot weaken or delete its own gate.
  - **Dogfood:** CI runs the gate input on every push, once passing and once blocked by the blocklist.
  - **CLI without the Action:** `docs/TRUST_POLICY.md`, "In CI, before install".
- **Pre-install bypass routes pinned by tests (v0.15.0 item Z4).** `tests/test_gate_bypass.py` now also covers the routes around the hook and the CI gate:
  - **Covered:** `git commit --no-verify` is caught by the CI gate, which compares with the base branch.
  - **Documented limits:** dependency files outside the hook's name pattern, a lockfile regenerated after the gate, and an install from a file the gate was not given.
  - Each is listed with what to do instead in [`docs/TRUST_POLICY.md`](docs/TRUST_POLICY.md), "Bypass routes".

### Changed

- **`openpulse gate`: a missing or invalid policy file is a usage error (exit 2),** not a violation (exit 1).

## 0.14.0 "Enforced Trust" — 2026-11-02

Track T Phase 4 (T-E1): trust conditions you prohibit now fail CI deterministically, with no model involved, because advisory answers to an agent are not a security boundary.
- **Trust policy:** `.openpulse/policy.yml` prohibits trust conditions, read by `check`, `attest` and the GitHub Action. It is backed by measured false-positive rates: lookalike names fire on 18.8% of real popular npm names, so indicators must name the packages they apply to.
- **The Action on pull requests:** it checks trust for the dependencies a pull request adds or changes, and uses the base branch's policy so a pull request cannot weaken its own gate.
- **Exports:** trust results appear in SARIF, the job summary and DefectDojo, with levels set by your policy, never by a risk score.
- **Bypass tests:** they found and closed two pull-request bypasses, and document the routes the gate cannot cover.

Nothing new blocks without a policy, and verdicts and the frozen evaluation are unchanged. **One upgrade note:** `dependency_status` drops the v0.12 top-level trust fields, which were deprecated in v0.13.0; read `trust.checks`.

### Upgrade notes

- **`dependency_status` no longer repeats `registry_existence`, `provenance` and `lookalike` at the top level (v0.14.0 item Y6).** They were deprecated in v0.13.0. Read them from `trust.checks`, where they have been since v0.13.0 with the same values. The `deprecated` field is gone too. Nothing else in the answer changes, and verdicts are unchanged.

### Security

- **A lockfile hash edited in place no longer passes the pull-request gate (v0.14.0 item Y5).** With `--base-lockfile` (the Action's `trust: pull-request`), the digest check ran only for entries with a new name or version. A pull request that kept an entry's name and version but changed its hash, swapping the artifact, was never checked. Digests are now checked for every entry whose locked digests differ from the base. Found by the new bypass tests.
- **A pull request can no longer weaken its own trust gate in the Action (v0.14.0 item Y5).** With `trust: pull-request`, the action used the pull request's own `.openpulse/policy.yml` and `.openpulse/private-packages.txt`, so a pull request could delete its prohibitions or list a malicious name as private. The action now uses the base branch's copies when they exist. A policy the pull request adds is still used, because there was nothing to weaken. If the base copies can't be read, the action warns and uses the pull request's.

### Added

- **Gate bypass tests (track T evaluation category 8, v0.14.0 item Y5).** `tests/test_gate_bypass.py` pins each route around the trust gate. `docs/TRUST_POLICY.md`, "Bypass routes", lists each route as covered or not, with what to do instead.
  - **Covered:** lockfile-only additions, hashes edited in place, respelled blocklisted names, an agent ignoring the MCP warning, and a pull request weakening its own policy.
  - **Not covered:** removing the workflow step (use a required status check), unpinned entries, version-pinned blocklist entries, sources that don't answer, installs outside the gated files, and internal names missing from the private-name list.

- **Trust records in SARIF, the job summary and DefectDojo (track T, T-E1, v0.14.0 item Y4).** This answers an open question from the Phase 0 trust design: how T-F1 statuses map onto these outputs without implying a risk score.
  - **Where they appear:** `attest --sarif` and `--defectdojo` (and the GitHub Action) report trust records from contract 2.2.0 `trust_assurance`, plus trust policy violations, as their own results under `openpulse/trust/<check>`. Each appears once per file, dependency, check and status, with the https references it cites.
  - **Levels follow your policy, not a score:**
    - prohibited by your policy (including the blocklist): SARIF `error`, DefectDojo High;
    - otherwise CONFIRMED_MALICIOUS or VERIFIED_FAILURE: `warning`, Low;
    - otherwise SUSPICIOUS_INCONCLUSIVE: `note`, Info;
    - other statuses are omitted unless prohibited.

    No `security-severity` is emitted.
  - **Job summary:** a separate *Trust checks* table.
  - **Consistency:** SARIF and DefectDojo share one item list and one identity per record. Verdict results are unchanged (tested).

- **The GitHub Action checks trust on pull requests (track T, T-E1, v0.14.0 item Y3).** New action inputs, both off by default so existing workflows stay offline and unchanged:
  - **`trust`:** `off`, `pull-request` or `all`. With `pull-request`, the action reads the base branch's copy of `manifest` and `lockfile` through the GitHub contents API with `github-token`. The token is in the environment of that one step only. Trust checks then run only for the dependencies the pull request adds or changes.
    - **New files:** a file the pull request adds counts entirely as added.
    - **Unreadable base:** if a base copy can't be read, every dependency is checked; a failure never narrows the checks.
  - **`policy`:** a trust policy file (default `.openpulse/policy.yml` when present). A violation fails the step even with `fail-on: none`.
  - **CLI:** `openpulse attest --base-manifest PATH --base-lockfile PATH` does the same from the command line. Trust checks and the policy's trust conditions apply to added or changed dependencies, and the blocklist to all of them.
  - **CI:** the action job now dogfoods a blocklist policy that must fail the step.

- **Trust policy: prohibited conditions fail the run (track T, T-E1, v0.14.0 item Y2).** `.openpulse/policy.yml` (or `--policy PATH`) is read by `openpulse check` and `openpulse attest` and evaluated without any model. See [`docs/TRUST_POLICY.md`](docs/TRUST_POLICY.md).
  - **`prohibit`:** for any package, `confirmed_malicious`, `not_found_in_registry`, `digest_mismatch`, `provenance_failure` and `repository_mismatch`. For named packages only, `missing_provenance`, `lookalike_name`, `public_private_name` and `unconfirmed_repository`. A policy that names an indicator without packages is refused, because the Y1 measurements show lookalike fires on 18.8% of real popular npm names. Conditions with no organic false-positive set warn that they are experimental.
  - **`blocklist`:** `ECOSYSTEM:NAME[==VERSION]` patterns; no lookups needed.
  - **What never blocks:** silence. `NOT_PERFORMED` and `MISSING_EVIDENCE` never fail a run unless a scoped condition says so.
  - **When it fails:** a violation exits 1 after every output is written, alongside `--fail-on`. With no policy, gates are unchanged.

- **Track T measurements (v0.14.0 item Y1).** `python benchmarks/trust.py` measures every trust check offline and writes `benchmarks/results/trust.json` and `docs/research/TRACK_T_MEASUREMENTS.md`. The owner accepted these measurements as the false-positive prerequisite for policy gates (T-E1, decision 11). They are not the registered study.
  - **Synthetic cases:** 33 cases with 37 labelled expectations, from the roadmap's evaluation plan (existence, lookalike, dependency confusion, provenance and repository linkage, digest integrity, known-malicious records). They run against a stub world in the reserved `opfx-` namespace. Every case gets its expected status, with no false positives on the synthetic negatives; that shows the checks do what they claim, not how often real attacks are caught.
  - **Degraded sources:** with every source unreachable, or the budget spent, no live check claims anything (0 of 284 records).
  - **Untrusted text:** hostile names are refused before any request and never echoed. An instruction in an OSV summary never reaches a record.
  - **Organic control (the informative number):** leave-one-out lookalike over 1000 real popular npm names. 18.8% look like another popular name; 9.7% without the `scope` rule, which fires on legitimate `@types/<name>`-style packages. So lookalike stays an indicator: a policy should prohibit it only for a named scope.
  - **Labels per policy condition:** each condition a policy can prohibit is labelled *measured*, *measured; indicator* or *experimental* (no organic set yet: dependency confusion, unconfirmed repository linkage).
  - Tests run a quick sample and check that the committed report matches the committed results.

## 0.13.0 "Agent Trust Evidence" — 2026-11-02

Track T Phase 3: trust evidence reaches agents in one place and goes into the evidence contract, with three new checks that each hold or fail against a cited source.
- **Known-malicious packages:** OSV `MAL-` records for any PyPI or npm name are the first `CONFIRMED_MALICIOUS` answers, always with the record cited.
- **Dependency confusion:** checked against your own private-name list.
- **Starjacking:** repository linkage checks whether a package is really from the repository it claims.
- **One `trust` block** in `dependency_status`, with the agent's stated reasons (`intent`, `name_source`) recorded but never used.
- **Evidence contract 2.2.0:** `openpulse attest --trust` records the trust checks in `trust_assurance`.
- **Opt-in local recording** of agent questions and answers (`openpulse mcp --record`), for research on how agents choose dependencies.

Verdicts and the frozen evaluation are unchanged. **Two upgrade notes:**
- `attest` now emits contract 2.2.0;
- agents should read trust results from `dependency_status`'s `trust.checks`. The v0.12 top-level copies stay until v0.14.0.

### Upgrade notes

- **`openpulse attest` emits evidence contract 2.2.0 (v0.13.0 item X5).** It is 2.1 plus one required field, `trust_assurance`, which is null unless you pass `--trust`. Validate against `schemas/evidence-contract/v2.2/schema.json`; a 2.1 validator rejects the new field. The hash rule is unchanged. The 2.1 schema stays published byte-for-byte.
- **`dependency_status` gathers its trust checks into one `trust` block (v0.13.0 item X4).** Read them from `trust.checks`. The v0.12.0 top-level fields `registry_existence`, `provenance` and `lookalike` are still there with the same values, listed under `deprecated`, and are removed in v0.14.0. The checks added in v0.13.0 (`malicious`, `dependency_confusion`, `repository_linkage`) are only in `trust.checks`. File checks keep their own `trust` block unchanged. Verdicts are unchanged.

### Added

- **Opt-in local recording of agent questions and answers (M8, v0.13.0 item X6).** `openpulse mcp --record DIR` appends one JSON line per tool call to `DIR/mcp-<session>.jsonl`. Each line holds the tool, its arguments, the outcome and a research summary: verdict, trust statuses, and the agent's `intent` and `name_source`. The full answer is included unless it is over 256 KB. It is off by default and local only: nothing is sent anywhere. Recording never changes an answer, a write failure stops recording without failing a tool, and on POSIX the files are owner-only. This is the data source for the track T research questions on how agents choose dependencies (RQ1, RQ4).
- **Evidence contract 2.2.0 with `trust_assurance` (track T, T-F2, v0.13.0 item X5).** `openpulse attest --trust` checks each PyPI and npm dependency once per run and records it in every contract for that dependency:
  - **The checks:** malicious records, registry existence, provenance, repository linkage, dependency confusion and lookalike.
  - **Record shape:** each record is fixed: check, T-F1 status, a fixed statement, `checked_at` and the https URIs it cites. A summary counts every status, and `used_in_verdict` is always `false`. Free-form evidence stays out, so the public shape is stable.
  - **Hash:** the JCS content hash covers the block, so `verify.mjs` checks it with no change.
  - **Budget:** at most 4 lookups per dependency and 2000 per run. `--private-names` names the private-name list (default `.openpulse/private-packages.txt` when present).
  - **Never part of a verdict:** assessments are identical with and without `--trust` (tested).
  - **Schema:** `schemas/evidence-contract/v2.2/` is derived from 2.1, which stays untouched, and its bytes are now pinned by a test.

- **One trust block, and the agent's reasons (track T, T-D, v0.13.0 item X4).** `dependency_status` answers carry `trust`:
  - `checks`: every trust record (`malicious`, `registry_existence`, `provenance`, `repository_linkage`, `dependency_confusion`, `lookalike`);
  - `summary`: counts per status;
  - `attention`: each `CONFIRMED_MALICIOUS`, `VERIFIED_FAILURE` or `SUSPICIOUS_INCONCLUSIVE` record, with its check and statement;
  - `time_frame`: the records are live lookups at their `checked_at`, and in replay mode it says they are not as of the replay date.
  - **`selection_context`:** agents may say why they ask. `intent` is a short sentence, stripped of control, bidi and zero-width characters and capped at 280 characters. `name_source` is one of `user_request`, `existing_code`, `documentation`, `search_result`, `model_suggestion` or `other`; any other value is recorded as `unrecognized`, not echoed. Both are recorded as `supplied_by: agent`, `used_in_status: false`, and never change a status or verdict (tested). This is the input for the M8 research questions on how agents choose dependencies.

- **Repository linkage in `dependency_status` `trust.checks` (track T, T-A4, v0.13.0 item X3).** Registry metadata can claim any repository: npm `repository`, PyPI `project_urls`. A package that claims a popular one borrows its stars ("starjacking", threat T4). The new `repository_linkage` record checks whether the claim holds in either direction:
  - **Verified PyPI provenance settles it**, without reading GitHub. If it names the claimed repository as publisher, the result is `VERIFIED_RELATIONSHIP`. If it names a different one, the result is `VERIFIED_FAILURE`: the artifact was not built from the repository it claims.
  - **Otherwise the claimed repository's manifest is read** at its default branch (`package.json`, following npm's `repository.directory`, or `pyproject.toml` then `setup.cfg`). If it names the package back, the result is `VERIFIED_RELATIONSHIP`. If it names a different package, the result is `SUSPICIOUS_INCONCLUSIVE`, an indicator only, since monorepos and renames do this too.
  - **`MISSING_EVIDENCE`:** no GitHub repository is claimed, or the repository has no readable manifest. **`NOT_PERFORMED`:** registry or GitHub trouble, offline, a spent budget, or a package on the private-name list.
  - **Bounds and parsing:** one budgeted lookup per package, cached per session. Manifests are parsed and never executed (`setup.py` is never read), and capped at 1 MB. Repository names, directories and the manifest's name are validated before they appear. GitHub repositories only.
  - **Trust block:** file checks run it for every non-private package in `trust`. Never part of a verdict (tested).

- **Dependency confusion against your private-name list (track T, T-A3, v0.13.0 item X2).** List your internal package names in `.openpulse/private-packages.txt`, one `ecosystem:name` per line (`PyPI:acme-billing`, `npm:@acme/ui-kit`). OpenPulse asks the public registry about those names, and only those.
  - **`SUSPICIOUS_INCONCLUSIVE`:** a public package has the name. If you did not publish it, an installer that also consults the public registry may resolve it instead of yours.
  - **`MISSING_EVIDENCE`:** no public package has the name. It is unclaimed, which also means anyone can still register it.
  - **`NOT_PERFORMED`:** the registry gave no usable answer, offline, budget spent, or the package is not on the list (or there is no list).
  - **MCP:** `dependency_status` gains a `dependency_confusion` record in `trust.checks`, and the server reads the list from its project root on every call. A listed package skips the public-registry `registry_existence` and `provenance` checks, which describe someone else's package, so a private dependency no longer reads as a hallucinated name. `malicious` and `lookalike` still run.
  - **Trust block:** `check_dependency_file` runs it for listed packages in `trust`.
  - **CLI:** `openpulse confusion [LIST]` checks every listed name, and `openpulse trust --private-names LIST` uses a list (the default file when present). Both are report-only.
  - **Validation:** names are validated against the registry grammars, PyPI spellings are normalized (PEP 503), and a bad line is skipped by line number without echoing its text. The list is capped at 500 names and 256 KB. Never part of a verdict (tested).

- **Known-malicious records in `dependency_status` `trust.checks` (v0.13.0 item X1).** For any PyPI or npm package, catalogued or not, the new `malicious` record asks OSV whether it publishes a malicious-package record (`MAL-`, the OpenSSF malicious-packages feed) for that package and version.
  - **`CONFIRMED_MALICIOUS`** cites each record by id and osv.dev URL (10 at most, with a total). This is the first check that can return this status, and only from a cited record, never from OpenPulse's own indicators. A record listed only under an alias counts; a withdrawn record does not.
  - **`MISSING_EVIDENCE`:** no such record. The feed covers reported packages only, so this is not evidence of safety. There is no "verified" outcome.
  - **`NOT_PERFORMED`:** OSV gave no usable answer, paged its answer without a record on the first page, offline, or a spent budget.
  - **Trust checks:** `check_dependency_file` runs it too, on added dependencies or with `trust_all`, and lists a hit under `trust.attention`. So does `openpulse trust`.
  - **Bounds:** one budgeted lookup per package, cached per session (failures never cached), and a capped response. Record ids are validated before they appear, and no advisory text is echoed. Never part of a verdict (tested).

 — 2026-11-02

Track T Phase 1: for PyPI and npm, MCP answers now carry checks on whether a dependency can be trusted, so an AI coding agent sees them before it adds or changes one.
- **Registry digests:** locked digests are compared with what the registry publishes.
- **PyPI provenance:** attestations are verified with the new optional `[provenance]` extra.
- **Lookalike names:** names that resemble popular packages are flagged as indicators.
- **Added dependencies:** a file check against an earlier copy checks only what was added or changed, and `openpulse trust` does the same from the CLI.
- **Untrusted text:** text from files and upstreams never reaches an agent unvalidated.

Every check uses the closed T-F1 status vocabulary and is never part of a verdict. Verdicts, contracts and the frozen evaluation are unchanged. No upgrade steps are needed. The new `trust`, `provenance`, `lookalike` and `digest_integrity` fields are additive.

### Added

- **Trust checks on added dependencies (track T, v0.12.0 item U5).** `check_dependency_file` takes an earlier copy of the file as `base_path`; the PyPI and npm dependencies added or changed since then get registry existence, provenance (PyPI) and lookalike indicators in a new `trust` block. It holds counts per check and status, and lists every `CONFIRMED_MALICIOUS`, `VERIFIED_FAILURE` or `SUSPICIOUS_INCONCLUSIVE` record under `attention`.
  - `trust_all` checks every dependency instead. With neither, `trust` is null and nothing extra is fetched.
  - **Budget:** trust checks run before the file-wide lookups, so the additions get the session budget first. The live checks are capped at 40 packages per file (the W4 bound), and the rest are counted as capped. Lookalike is local data, so every package gets it.
  - **MCP:** `base_path` is confined to the project root like `path`.
  - **CLI:** `openpulse trust FILE [--base EARLIER] [--offline] [--json]` prints the same block. It is report-only and never exits non-zero.
  - Never part of a verdict (tested). PyPI spelling variants (`Zope_Interface`, `zope.interface`) are the same dependency, not an addition.
  - **Not yet:** the GitHub Action on pull requests. It needs the base file from git, and gating on trust statuses is T-E1 (track T Phase 4).

- **Lookalike-name indicators in `dependency_status` (track T, T-A2, v0.12.0 item U4).** A PyPI or npm name is compared with the curated catalog and a pinned popular-name list. Every rule that fires is named, with the reference it matched:
  - `separator`: equal once `-`, `_` and `.` are removed;
  - `edit_distance`: within 1 edit, or 2 for names of 10+ characters, where a swap counts as one;
  - `confusable`: equal under the UTS #39 skeleton restricted to ASCII;
  - `scope`: npm `@x/name` where `name` is a reference.
  - **Outcomes:** `SUSPICIOUS_INCONCLUSIVE` is an indicator, never a typosquat verdict. A reference name is `VERIFIED_RELATIONSHIP`. Nothing firing is `MISSING_EVIDENCE`, not evidence of authenticity. Local data only: no network, no budget, never part of a verdict.
  - **Reference data (owner-approved sources),** each built and pinned by the new `scripts/refresh_reference_names.py` and listed in the new `NOTICE`:
    - `npm-high-impact` 1.13.0 (MIT, 17,335 names), checked against npm's sha512 integrity and read as text, never executed;
    - the ASCII mappings of UTS #39 `confusables.txt` 18.0.0 (Unicode License v3), pinned by sha256.
  - **PyPI's popular list:** a dated BigQuery query over the CC BY 4.0 download dataset, printed by the tool for a maintainer with a Google Cloud account to run. Until then, PyPI names are compared with the curated catalog only, and answers show the empty list.
- **PyPI provenance in `dependency_status` (track T, T-B1, v0.12.0 item U3).** For a PyPI package with a version, the new `provenance` field verifies the release's PEP 740 attestations from PyPI's Integrity API, for up to 4 files (wheels first), each against the file's sha256. Verification uses `pypi-attestations` (Sigstore), never cryptography of our own.
  - **Repository cross-check:** for curated packages, the attestation's publisher is compared with the catalog's GitHub repository; a different repository is `VERIFIED_FAILURE` (starjacking).
  - **Other outcomes:** an attestation that doesn't verify is `VERIFIED_FAILURE`. No published provenance is `MISSING_EVIDENCE`, never a failure, because most packages publish none. `VERIFIED_RELATIONSHIP` says where and how the files were built, never that they are benign (Ultralytics' first malicious releases carried valid provenance).
  - **Untrusted text:** publisher fields and file names are validated before they appear or reach a URL.
  - **New optional extra `[provenance]`** (owner-approved, Phase 0 decision 5), Python 3.11+: `pypi-attestations` and its ~24 dependencies, hash-locked in the new `requirements-provenance.lock`, which `scripts/compile_locks.py` generates, constrained to the core, mcp and audit-tool pins. Without the extra, the field is `NOT_PERFORMED` with how to enable it. A new CI `provenance` job installs it from the lock, checks drift, audits it and runs its tests.
  - **Lock checker fixes:** `scripts/check_lock.py` now reads the provenance lock and parses `>=` floors that carry an environment marker.
  - **Unchanged:** verdicts.
- **Digest integrity for lockfiles (track T, T-B4, v0.12.0 item U2).** `check_dependency_file` (MCP) compares each digest a `package-lock.json` (`integrity`) or `poetry.lock` (`files[].hash`) pins with what npm (`dist.integrity`, or `dist.shasum` for old sha1 locks) or PyPI (`urls[].digests.sha256`) publishes for that version. A locked digest the registry doesn't publish is `VERIFIED_FAILURE`, listed under `digest_integrity.failures`: the locked artifact is not the one the registry serves (substituted, re-uploaded or tampered).
  - **Other outcomes:** no usable locked digest is `MISSING_EVIDENCE`, and no usable registry answer is `NOT_PERFORMED`, never a failure.
  - **Safety:** lockfile digests are validated before use, and names before any URL. Each check spends one lookup from the session budget, under the 40-per-file cap.
  - **Reader output unchanged:** `core.lockfile_reader.lockfile_digests` reads the digests separately, so the dependency entries the verdict engine, contracts and ledger use are untouched.
  - **Unchanged:** verdicts. No new dependency; hashing only.
### Security

- **Reader skip messages never carry file text to an agent (track T, T-F3, v0.12.0 item U1).** `check_dependency_file` (MCP) passed the readers' skip messages through as written. Those messages quote the file's own lines, and the agent writes the files it asks about. A quoted value is now shown only when it has a requirement shape (`requests>=2.31.0`, `junit:junit`, `^4.2`: no whitespace, no Markdown link). Any other value becomes `<not shown>`, and messages are stripped of control, bidi and zero-width characters and capped at 240 characters. The CLI keeps the full messages for humans, stripped of control and bidi characters.

## 0.11.1 — 2026-11-01

A patch release:
- **Complete monthly reports.** Whole-catalog reports no longer lose NVD advisories to NVD's rate limit. Requests are paced, retried, and can use `NVD_API_KEY`. A source that still fails is named in the report as "unknown, not absent" instead of reading as "nothing found". The November 2026 report run, and the 2026-10-30 early edition before it, each silently lost a different set of projects' advisories.
- **Five untrusted-text hardening fixes for the MCP tools** (track T, T-F3).

No contract or verdict changes.

### Security

- **Lifecycle cycle strings and engine reasons are checked at the agent boundary (track T, T-F3 fix B, v0.12.0 item U1).** Release-cycle names come from endoflife.date and become event scope versions, which the engine interpolates into `reason` strings returned to MCP agents. A bridged lifecycle event whose scope isn't version-shaped is now withheld from the answer. It is counted under `sources` (`status: withheld`) and in `not_established`, never dropped silently. `verdict.reason` and `causes[].reason` also go through `strip_unsafe`. This is checked in `core/agent_tools` on purpose: `analyzers/lifecycle_events.py` is imported by the frozen evaluation's replay, so the engine, the CLI and the evaluation are unchanged. Every real cycle in the bundled fixtures (24) is version-shaped.
- **Error text carries no control, bidi or zero-width characters (track T, T-F3 fix C, v0.12.0 item U1).** `collectors.errors.redact`, and with it `safe_message`, every collector error record, the GitHub reader's skip reasons and webhook delivery errors, now turns C0/C1 control characters into a space and removes bidi overrides and isolates, directional marks and zero-width characters (`strip_unsafe`). This error text reaches terminals, webhooks and MCP agents, where those characters could reorder or hide what is shown. Stripping runs before redaction, so a hidden character can't split a secret past it.
- **Repository metadata is validated field by field (track T, T-F3 fix E, v0.12.0 item U1).** The MCP answer's `repository` block passed GitHub's `full_name`, `url`, `license` and `pushed_at` through as given. Each now must have its shape (the GitHub owner/name grammar, an SPDX-style id, an ISO timestamp) or it is `null`. The URL is built from the validated name, never taken from the API. The GitHub repository grammar also used `re.match` with `$`, which accepted a trailing newline (`"owner
"`). It now uses `fullmatch`.
- **Advisory ids are validated before they are listed or put in a URL (track T, T-F3 fix D, v0.12.0 item U1).** The MCP answer's `advisories` listed every advisory id and built `https://osv.dev/vulnerability/<id>` from it. These ids are upstream strings. Only an id with the OSV `<DB>-<ENTRYID>` shape (CVE, GHSA, PYSEC, RUSTSEC, GO, MAL, RHSA…) is now listed, percent-encoded in its URL. Anything else is withheld and counted in the new `ids_withheld` field. The verdict and `affecting_this_version_count` are unchanged.
- **Agent inputs must be identifiers, and are never echoed (track T, T-F3 fix A, v0.12.0 item U1).** The MCP tools took package names, versions, ecosystems and image refs as free text and repeated them in `dependency`, `verdict.reason` and `causes[].reason`. So an agent, or text injected into it, could make OpenPulse return arbitrary instructions inside fields the agent trusts.
  - **What's accepted:** these values must now match a general identifier shape (letters, digits and `@ / . _ : + ~ -` for names; similar sets for versions, ecosystems and image refs). Every ecosystem's real names fit, including legacy npm names with capitals.
  - **Tool arguments:** a failing argument is refused with a reason that doesn't repeat it.
  - **File entries:** `check_dependency_file` skips a failing entry like an unpinned one ("entry N: package is not an identifier - skipped, value not shown"). The agent writes the files it asks about.
  - **Unchanged:** every dependency in the bundled fixtures passes the shape.

### Fixed

- **NVD requests stay inside NVD's rate limit, are retried, and can use an API key (`NVD_API_KEY`).** A whole-catalog `openpulse report` makes one NVD request per project, unpaced and keyless. NVD allows 5 requests per 30 s without a key and answers the excess with 403, so each run silently lost a different set of projects' advisories: vitess in November 2026, timescaledb in the early edition.
  - **Pacing:** requests are now paced process-wide, 6.5 s apart without a key and 0.7 s with one.
  - **Retry:** a 403, 429 or 503 is retried up to 3 times, honouring `Retry-After` or waiting out NVD's 30 s window.
  - **Key:** read from `NVD_API_KEY` when none is passed, and never logged.
  - **Cost:** a keyless whole-catalog report takes about 12 minutes longer; a key (free from NVD) removes most of that.
- **The monthly report names sources that did not answer, instead of reading them as "nothing found".** The November 2026 run lost vitess's NVD advisories to NVD's rate limit, and the report showed vitess as having no security changes. Each project's failed sources (name, error category and HTTP status, never the error text) are now listed in the executive summary and in "Data gaps and limitations", as "unknown, not absent", and counted in the metadata sidecar under `coverage.source_errors`. A report without failures is unchanged.

## 0.11.0 "Early Warning Operations" — 2026-11-01

Scheduled alerts an operator can leave running, and a first track T check for AI coding agents.
- **Webhooks:** a scheduled webhook posts each alert once. Failed posts are retried and dead-lettered, not lost, and with a secret every post is signed.
- **CI:** jobs can gate on upcoming deadlines (`warnings --fail-on`).
- **MCP:** answers state their lookup limits, and `dependency_status` says whether a PyPI or npm package and version exist.

**This release changes webhook output:** a scheduled `check --webhook` posts only new alerts, so cache `.openpulse/deliveries` in CI. Verdicts, contracts and the frozen evaluation are unchanged. Read the upgrade notes before upgrading scheduled jobs.

### Upgrade notes

- **A scheduled `check --webhook` posts each alert once (#78, v0.11.0 item W1).** It used to post the whole digest on every run. It now posts only alerts not delivered before, and nothing when there are none. An alert is one affected cause of a verdict (dependency, event, relationship, impact and the event's content), or a repository whose inspection was not COMPLETE. State is kept in `.openpulse/deliveries/alerts.json`; in GitHub Actions, carry it in the cache like the ledger (`docs/SCHEDULED_CHECKS.md`). `--delivery-state ''` restores the old behaviour. Terminal output, verdicts and exit codes are unchanged.

### Added

- **Does this package exist? (track T, T-M1).** `dependency_status` (MCP) now reports whether a PyPI or npm package and version exist in their registry (`registry_existence`). The common hallucination shapes are covered: an invented package, and a real package with an invented version.
  - **Statuses:** records use the closed T-F1 vocabulary. A 404 is `VERIFIED_FAILURE`, an identity fact and never evidence of malice. Anything else (a 5xx, 429, redirect, timeout, offline, a spent budget, an unsupported ecosystem) is `NOT_PERFORMED`, never "absent".
  - **Untrusted text (T-F3):** names and versions are validated against the ecosystem's grammar before they go into a URL, and refused otherwise. Requests are HEAD only, so no upstream text is read. Statements are fixed templates.
  - **Limits:** each check spends one lookup from the session budget (W4). It is cached per session, and `NOT_PERFORMED` is never cached.
  - **Unchanged:** the verdict, the contract and the frozen evaluation. No new dependency.
- **MCP: stated lookup limits and a cross-session cache (v0.11.0 item W4, C5).**
  - **Budget:** one server session makes at most 200 live lookups; cached answers are free. Every tool answer carries a `lookups` block (budget, used, remaining, per-source timeout, cache TTL).
  - **Past the budget:** no lookup is made. The answer lists it under `not_established` with the reason, and `project_lifecycle` returns a tool error that says so.
  - **Per-file cap:** `check_dependency_file` names the projects its 40-project cap skipped (`live_lookups_capped`). It used to skip them silently.
  - **Cache:** `project_lifecycle` caches successful lookups on disk across sessions (`OPENPULSE_CACHE_DIR`; empty disables) with the session's one-hour TTL. Failures are never cached, and an answer served from the cache gives its age (`cached_age_seconds`).
- **Signed webhook payloads (#78, v0.11.0 item W3).** With `OPENPULSE_WEBHOOK_SECRET` or `--webhook-secret-file` (at least 32 characters), every `check --webhook` post carries `X-OpenPulse-Timestamp` and `X-OpenPulse-Signature: v1=<hex>`, an HMAC-SHA256 over `"<timestamp>." + body` on the exact bytes sent. `core/webhook_signing.verify_webhook_signature` (stdlib only) verifies it over the raw body, in constant time, and rejects a timestamp more than 300 seconds off, which bounds replay. The secret is never printed or stored. Without a secret, posts are byte-for-byte unchanged.
- **`warnings --fail-on {overdue,critical,high,medium,low}` (#78, v0.11.0 item W2).** A CI job can fail on deadlines. The command exits 1 when a warning at or above the severity is in the window; the order is OVERDUE > CRITICAL > HIGH > MEDIUM > LOW, so `critical` includes OVERDUE. As with every gate, it also exits 1 on FAILED repository coverage. The reason goes to stderr, so `--output json` stays parseable. Without the flag, `warnings` only reports, as before.
- **Persistent alert delivery state (#78, v0.11.0 item W1, C1).** `core/delivery.py` gives each alert a stable ID and records its delivery.
  - **Retry:** a failed post is retried once in the run, then left `pending`. Later runs retry it after a backoff (5 minutes, doubling, at most 6 hours).
  - **Dead letter:** after 5 failed runs the alert becomes `dead_letter`. It is kept with its last (redacted) error and never posted again, and the run says so.
  - **One run at a time:** the state is written atomically under an OS lock held across load, post and save, so two runs at once can't both send. A corrupt state file is moved aside, never overwritten.
  - **Configuration:** `--delivery-state` / `OPENPULSE_DELIVERY_STATE`.

## 0.10.0 "Verified Releases & Safe Gates" — 2026-11-01

Every release is now built from its tag with hash-locked tools and carries signed build provenance, and no output or CI gate treats an input OpenPulse did not fully read as clean. **This release changes outputs and gates**:
- `--fail-on` (CLI and Action) now fails on a repository it could not read.
- `openpulse attest` emits evidence contract 2.1.0, where runs with no repository say `NOT_APPLICABLE` coverage.
- A token file with two non-empty lines is refused.

Webhooks connect only to the address that passed the SSRF check. Verdicts and the frozen evaluation are unchanged. Read the upgrade notes before upgrading CI gates or contract consumers.

### Upgrade notes

- **`openpulse attest` emits evidence contract 2.1.0, and runs with no repository say `NOT_APPLICABLE` coverage (#109, v0.10.0 item V3).** Contracts from `--watchlist`, `--sbom`, `--spdx`, `--lockfile`, `--manifest` or `--images` runs said `inspection_coverage.status: COMPLETE` although no repository was scanned; they now say `NOT_APPLICABLE`. A consumer validating against the 2.0 schema must switch to `schemas/evidence-contract/v2.1/schema.json`, and one that switches on the status must accept the new value. Runs with `--github-repo` are unchanged. The Action's `inspection-coverage` output can be `NOT_APPLICABLE`, which raises no warning. Hash and every other value are unchanged.
- **`--github-token-file` accepts exactly one non-empty line, holding a visible-ASCII token (#138, v0.10.0 item V5).** A leading blank line is now skipped instead of rejected. A file with two non-empty lines, which used the first and ignored the rest, is now refused, because it's ambiguous which line is the token. A token with a space, a control character or a non-ASCII character is refused with a clear message, instead of failing later inside the HTTP client. No message contains the token. The read goes through the shared bounded reader (`core.bounded_io`), so its size error now reads "is N bytes (limit 4096)".
- **`--fail-on` now fails on FAILED repository coverage (#101, v0.10.0 item V2).** `check --fail-on`, `attest --fail-on` and the GitHub Action's `fail-on` exited 0 when a `--github-repo` scan FAILED, so a CI gate could pass on a repository OpenPulse could not read. They now exit 1 (after writing every output, for `attest`), as `--strict` already did, and say why. PARTIAL coverage is unchanged: it fails only `--fail-on-partial`. Without a gating flag, FAILED coverage stays report-only.
- **Webhook delivery ignores `HTTP(S)_PROXY` (finding M5, v0.10.0 item V4, #242).** A proxy resolves the webhook host itself, which would undo the DNS pinning below, so `--webhook` delivery now connects directly. A host that can only reach the webhook through a proxy can no longer deliver.

### Security

- **DNS-pinned webhook transport (finding M5, v0.10.0 item V4, #242).** The webhook SSRF check resolved the host, then httpx connected by hostname and resolved it again, so a resolver that answered with a public address first and `127.0.0.1` or `169.254.169.254` second (DNS rebinding) steered delivery past the check. The host is now resolved once, every returned address is checked, and the connection goes to a validated IP while TLS SNI, certificate verification and the `Host` header stay on the original hostname (a custom httpcore network backend under httpx's transport; no new dependency). IPv4-mapped (`::ffff:a.b.c.d`), 6to4 (`2002::/16`) and NAT64 (`64:ff9b::/96`, `64:ff9b:1::/48`) addresses are unwrapped first, and a refusal names the embedded IPv4 and its wrapping. The rest of the policy is unchanged: https only unless `--webhook-allow-http`, no redirects, capped response bodies, and no URL path in output.

### Added

- **A warning when the GitHub token file is readable by other users (#139, v0.10.0 item V5).** On POSIX, if the file's mode grants group or other access (`mode & 0o077`), `check`, `digest`, `warnings`, `attest` and `discover` print `warning: GitHub token file <path> is readable by other users; run chmod 600 <path>` to stderr. The run continues; the warning prints the path, never the token. The README example now runs `chmod 600`.
- **Attested releases (#111, v0.10.0 item V1).** A `v*` tag runs `.github/workflows/release.yml`.
  - **Build:** `scripts/build_release.py` builds the sdist and wheel from the tagged tree. It uses setuptools' own PEP 517 hooks with the hash-locked setuptools from `.github/ci-tools.lock`, without build isolation, so no build tool is fetched at build time.
  - **Refused builds:** a tag that differs from the package version, and a locked setuptools below `[build-system].requires`.
  - **Checks before publishing:** the wheel is smoke-tested in a clean venv from outside the checkout, and the deterministic SBOM is regenerated twice and compared.
  - **Provenance:** every file gets Sigstore-signed SLSA build provenance (`actions/attest-build-provenance`); verify with `gh attestation verify <file> --repo IkarusAILabs/OpenPulse`.
  - **On the GitHub release:** the sdist, wheel, `sbom.cdx.json` and `SHA256SUMS`, attached without replacing files that are already there.
  - **Permissions:** each job gets only what it needs: `id-token` only for the job that signs, `contents: write` only for the job that attaches.
  - **Not done:** nothing is published to PyPI; that waits on owner decision 7.

### Fixed

- **Digest, warnings and the webhook body now say when a repository was not fully read (#102, v0.10.0 item V3).** With a FAILED or PARTIAL `--github-repo` scan, `openpulse digest` and `openpulse warnings` used to drop the inspection result. Their body read "Nothing upcoming or newly-effective within the warning window", with no hint that the repository was never read, and `check --digest --webhook` posted the same. All three now carry `> ⚠️ Repository inspection coverage: <status> — <reasons>. Results are not a clean bill of health.` in the rendered body (and `coverage_note` in `--output json`), so it reaches the webhook too. Output is unchanged when coverage is COMPLETE or no repository is inspected.
- **The CI tools lock now satisfies the build floor.** Dependabot raised `[build-system].requires` to `setuptools>=84.2.1`, while `.github/ci-tools.lock` stayed at 84.1.0. The lock now pins 84.2.1, with the hashes PyPI publishes, and a test fails if the two drift apart again.

## 0.9.0 "Anchored Trust" — 2026-11-01

Authority, independence and history integrity now rest on verifiable facts or a secret key, never on strings the caller supplies. With a history key, regular `openpulse anchor` checkpoints kept outside `.openpulse/` and `openpulse verify` in the schedule, local history is **tamper-evident**; without a key it stays corruption-detecting. **This release changes outputs**: without a history key no lead time or sweep first-detection date is published, `openpulse attest` emits evidence contract 2.0.0 with a new content hash, and a chained history with no tip is refused. Verdicts of the frozen evaluation are unchanged. Read the upgrade notes before upgrading CI gates or contract consumers.

### Upgrade notes

- **`openpulse attest` emits evidence contract 2.0.0 (v0.9.0 item B7).** A consumer that validates against the 1.2 schema must switch to `schemas/evidence-contract/v2/schema.json`, because a 2.0 document fails the 1.2 `contract_version` const. A consumer that checks `provenance.content_hash` must recompute it with RFC 8785 (JCS), as `docs/EVIDENCE_CONTRACT.md` describes. Every other value is unchanged. SARIF, DefectDojo and Dependency-Track exports read contract fields and need no change.
- **Sweeps without a history key no longer publish first-detection dates (completes v0.9.0 item B3c).** `sweep`, `observe` and `report --with-sweep` now give a change a `first_detected_at` only when the repository's observation history verifies under a history key (VALID_KEYED), and never earlier than its adoption. Without a key, distribution findings carry no first detection or lead time, and the monthly report narrates them with "First detected by OpenPulse: Unknown", leaves them out of the lead-time list under "Upcoming Changes", and adds the unkeyed note. Stored records keep their dates; only the published claim is withheld. Change detection, diffs and findings are unchanged.
- **A chained observation history with no tip pointer is now refused (v0.9.0 item B4).** It was adopted silently, so a truncated history with its `tip.json` deleted went unnoticed. `observe` and `sweep` now report it as ROLLBACK_SUSPECTED and write nothing. A history saved by an OpenPulse old enough to write no tip is refused the same way. Accept it once, after checking it, with `openpulse observe --namespace <ns> --repo <repo> --rebaseline --reason "..."`.
- **Lead times now come only from keyed history (v0.9.0 item B3c).** `digest`, `warnings`, `report` and `check` publish a first detection and a lead time only from detection-ledger entries that verify under a history key. **Without `OPENPULSE_HISTORY_KEY` (or `--history-key-file`), no lead time is published**, and the digest, warnings and report say so in a note. Verdicts, deadlines and severities are unchanged. Make a key with `openpulse history-key generate`; the next keyed `check --ledger` run adopts existing entries, and their lead times count from that adoption. The GitHub Action gains its `history-key` input in B3d.

### Added

- **Evidence contract 2.0.0: an RFC 8785 (JCS) content hash (v0.9.0 item B7, finding L8).**
  - **The hash:** `content_hash` is SHA-256 over the JCS form of the document, without the hash itself, the build time and the signature fields. Any consumer with a JCS library recomputes it without OpenPulse's serializer. The new required `provenance.content_hash_method` is `jcs-sha256`.
  - **Code:** `core/jcs.py` is an RFC 8785 encoder (stdlib only). It rejects what JCS cannot represent: NaN, infinities, integers beyond 2**53, lone surrogates and non-string keys. `build_contract`, `v2_content_hash`, `verify_content_hash` and `validate_contract` are new; the last two dispatch on `contract_version`.
  - **Verifier:** `conformance/evidence-contract/verify.mjs` is a standalone Node verifier with no dependencies.
  - **Unchanged:** the 1.0, 1.1 and 1.2 schemas, and the 1.x builder `build_v1_contract`, which the frozen evaluation uses.
- **History anchors: `openpulse anchor` and `openpulse verify` (v0.9.0 item B5, finding H2).** They catch deletions that take their own evidence with them, which the store cannot see from inside: a repository's whole history folder (tip included), a ledger entry, the rotation log.
  - **`openpulse anchor [--out FILE]`** writes a checkpoint with:
    - each observation history's tip, record count and re-baseline count;
    - one leaf per ledger entry (`first_seen`, `adopted_at`), plus an RFC 6962 Merkle root over the leaves;
    - a hash of each rotation-log entry.

    With a history key it is MACed (`key_id`, `mac`). It refuses to write inside `.openpulse/`: keep it in git or as a CI artifact.
  - **`openpulse verify --anchor FILE`** exits 1 on any violation: an anchored tip no longer in its chain (ROLLBACK), a wiped history (WIPED), a deleted or backdated ledger entry (LEDGER_DELETED, LEDGER_REWRITTEN), a dropped rotation or re-baseline log entry, or an anchor whose MAC fails.
    - Growth after the anchor is fine.
    - A re-baseline after the anchor is a notice only when its log entry verifies under the key.
    - `--require-signed` also refuses an anchor the supplied key did not sign. `--json` prints the result.
  - **Docs:** `docs/SCHEDULED_CHECKS.md` adds anchoring to the scheduled CI recipe. README, METHODOLOGY and SECURITY now say that local history is tamper-evident with a history key plus anchors kept out of the store, and corruption-detecting without a key.
- **Rollback and downgrade detection for observation history (v0.9.0 item B4, finding H2).**
  - **New refusals:** ROLLBACK_SUSPECTED, for a chained history whose tip pointer is missing (before, it was adopted). DOWNGRADE, for an unchained record after chained ones, or an unkeyed record after keyed ones. They join ROLLBACK and BROKEN, and the refusal message says how to re-baseline.
  - **Explicit re-baseline:** `openpulse observe --rebaseline --reason "..."` (one line, up to 500 characters). A rollback whose remaining chain verifies is accepted at its current tip. A broken or downgraded history, or a tip with no data, is moved to `quarantine-<time>/`, never deleted, and the chain restarts at genesis.
  - **Logging:** every re-baseline is logged in `rebaselines.json` (time, reason, previous status, accepted tip or quarantine folder), MACed under the history key when one is set. The new record is a baseline: no change claims cross a re-baseline.
  - **Not covered:** a full wipe of a repository's folder, tip included, still looks like a first run. So does deleting the ledger's `rotations.json`. Detecting those needs an anchor outside the store (B5).
- **Lead times now come only from keyed history (v0.9.0 item B3c).** `digest`, `warnings`, `report` and `check` publish a first detection and a lead time only from detection-ledger entries that verify under a history key. **Without `OPENPULSE_HISTORY_KEY` (or `--history-key-file`), no lead time is published**, and the digest, warnings and report say so in a note. Verdicts, deadlines and severities are unchanged. Make a key with `openpulse history-key generate`; the next keyed `check --ledger` run adopts existing entries, and their lead times count from that adoption. The GitHub Action is unaffected: it runs `attest`, which neither records nor publishes lead times (corrected in B3d; the B3c note said otherwise). Scheduled CI that runs `check --ledger` needs the key as a secret and a ledger carried between runs: see `docs/SCHEDULED_CHECKS.md`.

### Added

- **Keyed history in scheduled CI, documented (v0.9.0 item B3d).** `docs/SCHEDULED_CHECKS.md` shows how to keep the history key in an Actions secret, carry `.openpulse/` between scheduled runs with `actions/cache`, and rotate the key. B3d was planned as a `history-key` input on the GitHub Action; the Action runs `attest`, which keeps no history, so such an input would do nothing and is not added. It is reconsidered if the Action ever records history.
- **Keyed adoption of older history (v0.9.0 item B3c, finding H2).** History written before a key existed is adopted, never re-MACed as if it had always been keyed.
  - **Observations:** unkeyed records followed only by keyed ones now verify VALID_KEYED. The first keyed record's chain hash pins the older records, and `verify_keyed_history` reports its `observed_at` as `adopted_at`. An unkeyed record after a keyed one is still VALID_UNKEYED. A change's `first_detected_at` from a keyed sweep is never earlier than the adoption.
  - **Ledger:** a keyed write to an unkeyed entry adopts it. It keeps `first_seen` as context, gains `adopted_at` (covered by the MAC), and later keyed writes keep that time. The new `keyed_first_seen(..., keys)` returns the later of `first_seen` and `adopted_at`, and only for a VALID_KEYED entry, with the rotation log applied.
  - **Readers:** `build_digest`, `build_warnings`, `prepare_report` and `build_report` take `history_keys`. `digest` and `warnings` gain `--history-key-file` and `--history-previous-keys-file`. Without keys they publish no lead time and set `lead_time_note`.
- **History key rotation (v0.9.0 item B3b, finding H2).** A key can now be retired without losing its history, and a leaked retired key cannot extend it.
  - Retired keys are verify-only: `OPENPULSE_HISTORY_KEYS_PREVIOUS` (comma- or space-separated) or `--history-previous-keys-file` (one per line, `#` comments) on `observe`, `sweep`, `report` and `check`. They need a current key. New records are always MACed with the current key.
  - **Observations:** when a history's newest keyed run is under a retired key, the next record is a handover: it carries `previous_key_id` and `handover_mac`, a MAC under the retired key. `verify_keyed_history` now walks keyed runs. A record under the retired key after its handover, a key change without a handover, or a handover that does not follow its key's run is BROKEN. A history keyed with a key that is neither current nor supplied as retired is still refused (`KEY_MISMATCH`).
  - **Ledger:** an entry under a retired key is verified with it and rewritten under the current key, and the handover is logged once in `rotations.json` at the ledger root, MACed by both keys. `entry_integrity(entry, keys, rotations)` treats an entry under a retired key with a sighting after its rotation as BROKEN. Forged log entries are ignored. Deleting the log cannot be detected locally; B5's external anchors are what detect it (corrected in B4).
  - Without a key, nothing changes. No golden, fixture or verdict changes.
- **Keyed history integrity, first slice (v0.9.0 item B3a, finding H2).** Local history used unkeyed SHA-256, so anyone who could write `.openpulse/` could edit a record, recompute its hashes and still verify as VALID.
  - A history key (`OPENPULSE_HISTORY_KEY`, or `--history-key-file` on `observe`, `sweep`, `report` and `check`) adds an HMAC-SHA256 to every new observation record (`key_id`, `history_mac`, over the chain hash and `first_detected_at`) and every new detection-ledger entry (over its content hash). `openpulse history-key generate` prints a fresh 32-byte key; nothing is written.
  - New states: VALID_KEYED, VALID_UNKEYED, BROKEN, UNKNOWN (`verify_keyed_history`, `ledger.entry_integrity`). `observe` prints the history's state.
  - A keyed history is never appended to without its key (`KEY_REQUIRED`, `KEY_MISMATCH`), and a keyed ledger entry is left as it is. Records and entries written before the key stay unkeyed: keyed adoption, with lead times clamped to it, is the next slice (B3c).
  - A key shorter than 32 bytes, or a key file inside `.openpulse/` or a history store, is refused. The key is never printed or stored in history.
  - Stdlib only. Without a key, nothing changes. Reports do not yet restrict lead times to keyed history (B3c), and the README keeps calling history corruption-detecting until B3–B5 hold.

### Fixed

- **Two pages on one site no longer count as two independent sources (v0.9.0 item B2, finding M2).** Independence fell back to the source name, so renamed copies, or different declared families on one site, could reach CORROBORATED.
  - Each source's URL now gives it a family: its registrable domain (`blog.redis.io` and `redis.io` are both `redis.io`), or the host plus owner on shared hosts (`github.com/bitnami`).
  - Sources are grouped when their URL families, declared families or names match, or one is `derived_from` the other. A declared family can merge sources but never split one site.
  - No public-suffix dependency: the registrable domain is the last two labels, or three under a short list of two-level suffixes (`co.uk`, `github.io`, …). An unlisted suffix only makes a family wider, which withholds corroboration and never grants it.
  - The gate's CORROBORATED rule and `assess_confidence` use the new count. No fixture, golden or dependency verdict changes.
- **A source's `official` authority is derived, not taken on trust (v0.9.0 item B1, finding M1).** Before, any source that said `authority: official` could carry an event to CONFIRMED.
  - A source now counts as official only when its URL is https and names a location on the event project's allowlist, in the new `data/official_domains.yaml`. An entry is a host, which also covers its subdomains, or a host with a path, such as `github.com/django`. Shared hosts are only listed with a path.
  - Lookalike hosts (`evil-redis.io`, `redis.io.evil.com`), `http://`, userinfo, other ports and non-ASCII hosts never match. A project with no entry has no official sources.
  - A source that fails is read as `secondary`. The gate's CONFIRMED rule and its ACTION/CRITICAL provenance rule read the derived value, and a gate failure names each downgraded source. `assess_confidence` (now taking the project slug) and the lifecycle bridge derive CONFIRMED the same way.
  - The first allowlist covers the six projects with curated official fixtures: bitnami, bitnami-spark, django, itext, react and terraform. All their fixtures still pass the gate. The synthetic `pypi-package-removal` fixture (`leftpad`) no longer passes `validate --strict`, because its only official source is a GitHub user page.
  - No dependency verdict changes: `check` reads an event file's stated confidence and does not run the gate.
- **Detection-ledger stamps are bound to the wall clock (clock trust, finding L7, v0.9.0 item B6).** A lead time is only as trustworthy as the first-detection date behind it.
  - `record_detection` refuses a stamp more than five minutes from UTC wall-clock time, or one that is not an ISO-8601 time, with `ClockSkewError`, and writes nothing. Before, a caller could pass any `detected_at`, including a backdated one or garbage.
  - An entry's `first_seen` is fixed when the entry is created. A re-detection stamped earlier than that is a sighting the ledger never witnessed, so it no longer moves `first_seen` earlier.
  - The observation store's fallback stamp is UTC, not naive local time.
  - `openpulse check --ledger` always stamped the current time, so CLI runs are unaffected. Existing ledger entries are kept as they are; keyed history (B3) is what will tell a legitimate old entry from a rewritten one.
- **One large dependency file no longer uses up a repository's whole inspection budget (#103, #148).** The per-file cap was 50 MB, equal to the 50 MB total budget, so a single 50 MB lockfile left every other manifest in the repository uninspected. The per-file cap is now the smallest of three limits: the parser cap, GitHub's 100 MB blobs-API limit, and half the budget, which is 25 MB today. A larger file is skipped on its own, with a PARTIAL reason, and the rest are still read.
- **A catalog alias collision now fails loudly instead of resolving to the first entry (#144, #151).** If two entries in `data/canonical_projects.yaml` claim the same alias or Docker image, `catalog_alias_map` raises `CatalogCollisionError`, naming the alias and both slugs.
  - The resolver no longer turns a broken catalog into an empty one. Before, one bad entry silently made every reference resolve to itself. Now `{}` is used only when the catalog file is missing.
  - Every CLI command, including `openpulse mcp`, checks the catalog at start-up and exits with a one-line message instead of a traceback.

### Documentation

- **OpenPulse is presented as academic research software.** The README has a new *Research status* section. It says what OpenPulse is (a research instrument of the [Ikarus AI Labs](https://ikaruslabs.net/research) programme, described in TR-2026-01) and what it is not (a commercial product or a certified security control). It also says how to read the project's claims and how to collaborate. The README's product and commercial wording is reframed, and the mentions of a separate SaaS layer are removed. `SECURITY.md`, `docs/MCP.md` and `docs/GITHUB_ACTION.md` carry a short research-software note, and the package description now says the same.
- **`CITATION.cff`** added; it cites TR-2026-01. The README has a *Citing OpenPulse* section.
- **`SECURITY.md`** now lists the latest 0.8.x release as supported. It also uses the renumbered roadmap: keyed history is planned for v0.9.0 and the DNS-pinned webhook transport for v0.10.0.

## 0.8.0 — 2026-10-31

The release that TR-2026-01 describes. **This release changes verdicts**: the audit fixes (D1–D15, F1–F4) withhold clearances the earlier engine gave, completeness now needs a recorded basis, and the CLI and MCP tools bound evidence age by default. Read the upgrade notes before upgrading CI gates.

### Upgrade notes

- **The CLI's verdict commands bound evidence age (TR-2026-01 N4).** This changes verdicts, as it did for the agent tools in PR #200. `check`, `attest`, `digest` and `warnings` now run in the *current* mode: a NOT_AFFECTED needs evidence fetched within 90 days of the start of today (UTC). Older evidence makes it RELATED ("stale"), never a clearance. `--max-evidence-age-days N` and `--as-of DATE` set the frame. `--replay` re-evaluates recorded evidence with no bound and says so on stderr, and contracts record the frame in `evaluation_context`. Contradicted events never clear in either mode. Pipelines that replay old fixtures should pass `--replay`.

### Documentation

- **Roadmap: track T, AI Dependency Trust Assurance (planned; a separate future study).** `docs/ROADMAP.md` adds the following:
  - what exists today and what is planned;
  - an initial threat model that separates demonstrated techniques from unmeasured prevalence;
  - six workstreams: identity and impersonation, provenance and integrity, reputation integrity, AI selection evidence, policy enforcement, and evidence contracts;
  - phases 0–4, with a small first milestone: registry existence for PyPI and npm;
  - a proposed evaluation plan with research questions RQ1–RQ5.

  Nothing is implemented, and no behaviour, interface, contract or dependency changes. Track R and the TR-2026-01 registration are unchanged.

### Added

- **Adversarial-input tests** (`tests/test_adversarial_inputs.py`). They pin, for each attacker capability the twelfth review lists, what the event-scope engine does:
  - **inputs that cannot yield a negative:** contradicting evidence, a contradictory event pair, stale or retracted events, unresolvable references, and injected upstream text;
  - **two trusted inputs:** a wrong completeness declaration, and a curated bare-name alias for a package without an ecosystem.
- **Evaluation: strata, pair-level bounds, deduplicated burden** (`evaluation/registration.py`, `run.py`):
  - results by completeness basis and identity status (REGISTRATION §4);
  - the pair-level false-clear share, with both an independent-pairs exact bound and an event-clustered bound;
  - per inventory and cycle, the actionable share and the unique review items after deduplication.

- **Evaluation: the registration amendments of 2026-10-30, implemented** (`evaluation/REGISTRATION.md` §2, §4, §5, §5a). This adds:
  - policy R, the existing-representation baseline: written rules for encoding an event as OSV or OpenVEX (`evaluation/representations/ENCODING.md`), and a careful consumer (`evaluation/existing_representation.py`) with exact purl identity and V's pinned comparators. Each event's encoding is frozen by SHA-256 in the case set, and `run.py --require-encodings` refuses an event without one;
  - test S3 (C − R, Holm-corrected with S1 and S2), guardrail G4, and the attribution steps B→R→V→C;
  - the review-burden measures W1–W3 (`run.py --inventories`) and the reliability measures D1–D2 (`--annotations`).

  Six development-set events are encoded (dataset revision 2026.10.30-3), so R's numbers there are illustrative only. No OpenPulse verdict changes.
- **Ecosystem-qualified package scopes (F3).** A package-scope value may be a purl without a version (`pkg:pypi/redis`). It names exactly one package: a dependency of that ecosystem and name is AFFECTS_PACKAGE whatever its curated project, a package of another ecosystem is excluded (only from a scope declared complete with a basis), and anything unreadable is undetermined. Bare values keep working and are read through curated identity.
- **Evidence contract 1.2.0: what a verdict does and does not assert** (TR-2026-01 sections 5.1-5.2, ROADMAP R-B6). Every document now carries three new things:
  - `verdict_meaning`: direct scope membership as a closed vocabulary; embedded components, availability, maintenance and security consequence marked `not_evaluated`; and a fixed statement with no upstream text;
  - `scope.completeness`: whether the scope was declared complete, its basis, and whether that admits a negative;
  - `evaluation_context`: whether a freshness bound was applied.

  `openpulse attest` emits 1.2. The 1.1 and 1.0 schemas are unchanged and their documents still validate and verify. **Upgrade note:** a consumer that validates against the 1.1 schema must switch to `schemas/evidence-contract/v1.2/schema.json`, because a 1.2 document fails 1.1 validation (`additionalProperties: false`).
- **MCP answers bound evidence age (TR-2026-01 N4).** This changes verdicts. `dependency_status` and `check_dependency_file` now run in a current-assessment mode: a negative needs evidence fetched within 90 days (configurable) of now, so a stale event can associate a dependency but no longer clear it. Answers carry an `evaluation_context` block (contract 1.2 fields plus `mode`), and every cause carries its `scope_completeness`. An explicit replay mode (Python API only) disables the bound and says so in `evaluation_context`, `not_established` and `note`.
- **MCP responses state verdict meaning.** `verdict.meaning` carries the same closed vocabularies, every cause carries `direct_scope`, and the fixed note now says that NOT_AFFECTED is not a clearance either.

### Fixed

- **A package named like an uncatalogued event project was treated as that project (F4).** This changes verdicts. A package that resolves only to itself, because no curated mapping exists, is now RELATED (identity unresolved) against that project's events, even when its name is the project's. It was previously version-tested, and could be cleared. Images already behaved this way (D10). capa (PyPI `flare-capa`) and react-native-fbsdk (npm) are now curated, so their package pins keep their project tie.
- **Package names in a package scope compare in canonical form (F2).** This changes verdicts. A Maven `groupId:artifactId` dependency now matches a listed `groupId/artifactId`, and PyPI names fold per PEP 503 (`Apache.Airflow` = `apache_airflow`). A scope value naming the event's own project still covers every package curated as that project; that rule is now part of the specification (TR-2026-01 §5.3, `conformance/independent/SPEC.md` §4.4) and of the conformance gate.
- **Every catalog entry now curates its packages (F1, completed).** This changes verdicts.
  - Libraries list the packages that are the project, Maven coordinates included. `groupId:artifactId` from manifests and SBOMs now matches the catalog's `groupId/artifactId`.
  - Servers and tools declare none, so a package that only shares their name is unresolved (RELATED), not the project. Examples: PyPI `kubernetes` (the Python client), npm `mongodb` (the Node.js driver), npm `angular` (AngularJS 1.x), PyPI `kafka` and PyPI `postgres`.
  - Curated iText modules such as `com.itextpdf:sign` now resolve to iText.
  - Packages with no stated ecosystem resolve by name, as before. A catalog test requires every new entry to state its packages.
- **MCP tools resolved package identity by name (F1, follow-up).** `dependency_status` and `check_dependency_file` now resolve packages per ecosystem, as the verdict engine does. PyPI `redis` is reported, and looked up, as redis-py.

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

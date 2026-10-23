# Changelog

All notable changes to OpenPulse. Versions follow semver; while the project is `0.x`, minor versions may change behavior and are called out under **Upgrade notes**. Intelligence-schema and evidence-contract versions are tracked separately (see `docs/EVIDENCE_CONTRACT.md`).

## Unreleased

### Added

- **GitHub Action** (`integrations/github-action/`, Phase C3). A composite action runs `openpulse attest` on manifests, lockfiles, SBOMs and image lists, or discovers them in the repository. It writes a job summary, a SARIF 2.1.0 log for Code Scanning and the evidence-contract JSONL. It fails only on the `fail-on` threshold (default `action`). Coverage other than COMPLETE is a warning, never a pass. CI dogfoods the action against `data/fixtures` on Linux and Windows. Not yet on the Marketplace.
- `attest --sarif PATH`, `--summary PATH` and `--fail-on`. Every SARIF result cites its evidence URLs and the contract's `content_hash`. NOT_AFFECTED results are omitted. A dependency that no event applies to is reported once as an UNKNOWN note.

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

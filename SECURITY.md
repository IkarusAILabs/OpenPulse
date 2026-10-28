# Security Policy

OpenPulse produces evidence that people use to decide whether a dependency
is affected. A defect that makes OpenPulse **wrong with confidence** is a
security issue, even if nothing crashes. That includes a silent
"no dependencies", a forged CONFIRMED, or a rewritten detection history.

## Supported versions

| Version | Supported |
|---|---|
| `main` | ✅ |
| latest 0.6.x release | ✅ |
| older releases | ❌ (upgrade to the latest release) |

## Reporting a vulnerability

**Please do not open a public issue for a vulnerability.**

Report it privately through GitHub private vulnerability reporting: use the
"Report a vulnerability" button on this repository's **Security** tab
(<https://github.com/IkarusAILabs/OpenPulse/security/advisories/new>).

Include the affected version or commit, the component (file and function if
known), reproduction steps or a minimal input file, and the impact you
observed. Inputs that make a verdict wrong are as welcome as crashes.

What to expect:

- **Acknowledgement** within 3 business days.
- **Initial assessment and severity** within 10 business days.
- **Fix and advisory:** coordinated with you. Our target is 30 days for
  High and Critical issues, and we credit reporters unless you ask us not to.

## In scope

- **Verdict integrity.** Any path that turns UNKNOWN into NOT_AFFECTED,
  makes partial inspection look complete, or lets weak or self-declared
  evidence reach CONFIRMED / ACTION.
- **Input handling.** SBOM, lockfile, manifest, image inventory, watchlist,
  event and bundle parsing: resource exhaustion, parser confusion, path
  traversal.
- **Outbound requests.** Webhook SSRF, credential leakage in errors or
  logs, and token handling for GitHub and the registries.
- **Local history.** The observation chain and the detection ledger.
  Today these are corruption-detecting, not keyed; see "Known
  limitations" below.
- **Evidence contract.** Documents that validate but misstate what
  OpenPulse established.
- **The project's own supply chain.** CI workflows, the lockfile and the
  release artifacts.

## Out of scope

- Vulnerabilities in upstream projects that OpenPulse *reports on*. Report
  those to the upstream project.
- Findings that require an attacker who already controls the machine
  running OpenPulse. The exception is attacks on the local history, which
  is explicitly in scope.
- Missing rate limiting on third-party APIs that OpenPulse calls.

## Known limitations (documented, not silent)

- **Unkeyed local history.** The observation chain and the detection ledger
  use unkeyed hashes. An adversary with write access to `.openpulse/` can
  recompute them, and a deleted `tip.json` is adopted. Keyed integrity and
  rollback detection are planned for v0.8.0 (`docs/NEXT_PHASES.md`).
- **Webhook DNS rebinding.** The webhook SSRF check resolves DNS before
  connecting, so it is open to DNS rebinding. A DNS-pinned transport is
  planned for v0.9.0.
- **Unsigned contracts.** Evidence-contract documents are not signed. Their
  `signature` fields are always `null` in v1.

## Hardening already in place

- Only safe YAML loading is used.
- TLS verification is on everywhere, and collectors never follow
  redirects.
- GitHub inspection is pinned to commit and blob SHAs, with bounds.
- Webhooks are https-only, with an IP blocklist and a body cap.
- Every file read is bounded.
- CI actions are pinned by SHA and run with least privilege. CI also runs
  CodeQL, pip-audit, a lock-drift check, a deterministic SBOM and a secret
  tripwire.

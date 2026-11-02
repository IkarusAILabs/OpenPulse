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

# B3 keyed integrity: key-management design (proposal)

Status: **APPROVED by the owner on 2026-11-01**, all four questions as recommended below (`docs/NEXT_PHASES.md`, Phase 2, decision 5). B4, B5 and C1 depend on it. Implementation is split into slices: B3a (key, MACs, keyed states), B3b (rotation), B3c (keyed adoption and lead-time clamp), B3d (CI documentation; see Decision 1).

Finding: H2 (`docs/ARCHITECTURE_REVIEW.md`). The observation chain and the detection ledger use unkeyed SHA-256. Anyone who can write `.openpulse/` can edit a record, recompute every hash and produce a history that verifies as VALID. Lead time, the headline metric, rests on that history. Today it is *corruption-detecting*, not *tamper-evident*.

## Goal and non-goals

Goal: a record edited without the key can never verify as VALID_KEYED. Published lead times come only from VALID_KEYED history.

Not in B3:
- **Rollback.** Deleting the newest records is B4's job.
- **External anchoring.** B5 does this.
- **Protection against an attacker who holds the key.** B5 bounds that case.
- **Signatures that third parties can verify.** HMAC is a shared secret: it proves integrity to the key holder only. Public verification is contract v2 signature work, still null.

## Threat model

| Attacker can | Outcome after B3 |
|---|---|
| Read and write `.openpulse/`, but has no key | Can corrupt or delete records, but cannot make an edited record verify as VALID_KEYED |
| Read CI logs or artifacts | Gets no key: the key is never printed, written to `.openpulse/` or included in artifacts |
| Hold the current key | Can forge anything signed with it. Rotation limits the window and B5 anchors bound it |
| Hold only an old, rotated-out key | Cannot extend history past the rotation handover (see Rotation) |

## Mechanism (for reference; decided by the B3 PR, not here)

- `mac = HMAC-SHA256(key, "openpulse-history-v1\0" + canonical_fields + previous_mac)` on each observation record. Each ledger entry gets `mac = HMAC-SHA256(key, "openpulse-ledger-v1\0" + content-hash material)`.
- **Domain separation:** the prefix strings keep a MAC for one record type from ever being accepted for the other.
- **Existing fields stay:** the unkeyed `chain_hash` and `content_hash` keep detecting corruption without a key, and old tooling keeps working.
- **New fields:** each record carries `key_id = "hk1:" + first 16 hex of SHA-256(key)` and `chain_version: 2`.
- **`first_detected_at` is chained:** version-2 records add it to the chained fields. Version-1 records verify with the old field set.
- **States:**
  - **VALID_KEYED:** the MAC verifies under a known key.
  - **VALID_UNKEYED:** the hashes verify but there is no MAC, or no key was supplied.
  - **BROKEN:** a hash or MAC fails.
  - **UNKNOWN:** a legacy record, or a `key_id` with no key available.
- **Comparison:** MACs are compared with `hmac.compare_digest`.
- **Dependencies:** stdlib only (`hmac`, `hashlib`, `secrets`). No new runtime dependency.

## Decision 1: where the key lives

**Recommendation: an environment variable or a key file, never inside `.openpulse/`. No OS keyring.**

- **Sources:** `OPENPULSE_HISTORY_KEY` (environment), or `--history-key-file PATH` on the commands that write or verify history (`sweep`, `check --ledger`, `digest`, `warnings`, `verify`). This is the convention `GITHUB_TOKEN` / `--github-token-file` already uses.
- **Key file handling:** the file is read with `bounded_io` (H5): first non-empty line, at least 32 bytes after decoding. A warning is printed when other users can read it (H6).
- **Refusals:** a key file inside the store root, or inside the checkout's `.openpulse/`, is refused. So is a key shorter than 256 bits.
- **CI:** a repository or organisation secret, exported as `OPENPULSE_HISTORY_KEY` to the steps that run `check --ledger`, `digest`, `warnings` or `report` (`docs/SCHEDULED_CHECKS.md`). The Action was to gain a `history-key` input, but it runs `attest`, which keeps no history, so the input is not added (B3d, 2026-11-01); it is reconsidered if the Action ever records history.
- **Generation:** `openpulse history-key generate` prints a fresh 32-byte key (`secrets.token_bytes`, base64) and its `key_id`. It writes no file.
- **Why not the OS keyring:** it needs the `keyring` package, a new runtime dependency that needs sign-off. CI runners have no keyring, so the CI path would need the environment variable anyway.
- **Without a key:** everything works as today. New records are written VALID_UNKEYED, and reports say lead times are unpublished because history is unkeyed. Nothing fails closed into an error, because the ledger is an enrichment, never a prerequisite.

## Decision 2: rotation

**Recommendation: one current key, verify-only previous keys, and a cross-signed handover record.**

- **Current and previous keys:** `OPENPULSE_HISTORY_KEY` is the current key, used for every new MAC. `OPENPULSE_HISTORY_KEYS_PREVIOUS` (or `--history-previous-keys-file`) lists retired keys, which are accepted for verification only.
- **Handover record:** the first write under a new key appends a record to each chain. It carries `previous_key_id` and is MAC'd with both keys. A verifier accepts records under a retired key only up to that chain's handover. A record MAC'd with the retired key after the handover is BROKEN, so a leaked old key cannot extend history.
- **Rotate when:** the key may have leaked, someone with access leaves, or on a schedule. We recommend at least yearly, as guidance only, with no enforcement.
- **Compromise:** rotate at once. Records MAC'd with the compromised key are not proved honest after the compromise date. B5 anchors made before that date still prove what existed then, and the B3 PR documents how to read that case.
- **Lost key:** history signed only with that key drops to VALID_UNKEYED, never BROKEN. It is not forged, it just can no longer be proved. Its lead times are no longer published.

## Decision 3: histories created before the key

**Recommendation: keyed adoption. Never re-MAC old records as if they had been keyed all along.**

- **Adoption record:** the first keyed write to an existing unkeyed chain appends an adoption record. It is MAC'd with the key, covers the unkeyed tip hash and stamps `adopted_at` (wall clock, bounded by B6 clock trust). Ledger entries get the same treatment entry by entry.
- **What adoption proves:** only that the earlier history existed in this form at `adopted_at`. That is a true statement. Re-MACing every old record would claim that each one existed when written, which is false.
- **Lead time from adopted history:** it is published from `max(first_detected_at, adopted_at)`. That is an honest lower bound, never an overstatement. The unkeyed earlier date can be shown as context, labelled "unkeyed, not used for lead time".
- **Alternative rejected:** never publishing lead time from pre-key history at all. That is safer but discards months of real observations. The clamped value never overstates, so it keeps the "never estimated, never inflated" rule.

## Exit criteria (from NEXT_PHASES, unchanged)

- Without the key, an edited record whose hashes were recomputed is not VALID_KEYED.
- Reports cite lead times from keyed-valid detections only, clamped at adoption.
- README, METHODOLOGY and ROADMAP say "tamper-evident (keyed)" only once B3–B5 all hold.

## What the owner needs to answer

1. **Storage:** environment variable plus key file, no keyring?
2. **Rotation:** verify-only previous keys and a cross-signed handover?
3. **Pre-key histories:** keyed adoption, with lead time clamped to `adopted_at`?
4. **The Action:** may it gain an optional `history-key` input? That is a public interface change.

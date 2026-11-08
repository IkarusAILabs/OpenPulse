# Released-contract corpus

Evidence contracts as each released contract version's own producer wrote them, and documents that must be rejected (v0.19.0 P5).

| Version | Producer | Why this one |
| --- | --- | --- |
| 1.0.0 | commit `d68f533` | 1.0 was never in a tagged release: the parent of `f772695`, which replaced it with 1.1 |
| 1.1.0 | `v0.6.1` | first tag emitting 1.1 |
| 1.2.0 | `v0.8.0` | first tag emitting 1.2 |
| 2.0.0 | `v0.9.0` | first tag emitting 2.0 |
| 2.1.0 | `v0.10.0` | first tag emitting 2.1 |
| 2.2.0 | `v0.13.0` | first tag emitting 2.2 |
| 2.3.0 | `v0.16.0` | first tag emitting 2.3 |
| 2.4.0 | `v0.18.0` | first tag emitting 2.4 |

## Files

- **`<version>/documents.jsonl`:** what `openpulse attest` at the producer commit wrote from the fixtures in that same tree (`data/fixtures/watchlist_sample.yaml` and the django EOL event; `--replay` where the release has it). Today's code does not touch them.
- **`<version>/negatives.jsonl`:** copies of the first document, each breaking one rule:
  - changed after hashing;
  - an unknown field;
  - a missing field;
  - an unpublished version;
  - a `provenance.contract_version` that differs from the top level;
  - a relationship outside the vocabulary;
  - an impossible date;
  - (2.x only) another hash method.

  A negative that only the schema should catch is re-hashed, so its content hash is valid and cannot catch it first.
- **`MANIFEST.json`:** for each version:
  - the producer's ref and pinned commit;
  - each document's content hash;
  - each negative's mutation and the JSON path it must be rejected at.

## Regenerating

From the repository root, with full git history:

```bash
python conformance/contracts/regenerate.py
```

```bash
python conformance/contracts/regenerate.py --check
```

**Regenerating:** the script refuses a ref that no longer resolves to its pinned commit. Producers run in an environment with tokens, keys and `OPENPULSE*`/`GITHUB*`/`PYTHON*` variables removed.

**`--check`:** regenerates into a temporary directory and exits 1 if any content hash or negative differs. Two runs differ only in `provenance.generation_timestamp`, which no hash covers.

## Where it runs

- **`tests/test_contract_corpus.py`:**
  - the consumer and OpenPulse's validator accept every document;
  - both reject every negative at the path `MANIFEST.json` names;
  - `verify.mjs` agrees on 2.x;
  - the `--check` regeneration runs when the producers' commits are in the clone.
- **The `consumer` CI job:**
  - runs the standalone consumer over every file;
  - runs `verify.mjs` over the 2.x documents;
  - on Linux, runs `regenerate.py --check`.

A new contract version adds a row to `PRODUCERS` in `regenerate.py`, pinned to the first tag that emits it, and a regeneration.

# Independent oracle kit (ROADMAP R-B7)

**For:** an engineer or researcher who has **not** worked on OpenPulse's verdict engine.
**Purpose:** to check OpenPulse's applicability rules independently of the people who wrote both the implementation and its oracle.

OpenPulse's conformance evidence (TR-2026-01 §6) compares the implementation with an oracle that the same team wrote. Both can share a wrong assumption and still agree. Your work breaks that circularity in three ways:

1. **Review** the decision rules for errors, gaps and ambiguity.
2. **Implement** your own oracle from the rules alone.
3. **Write edge cases**, each with an expected outcome and your rationale.

Every disagreement you find is a result, whichever side turns out to be wrong.

## What to read, and what not to read

| Read | Do not read until you have submitted |
|---|---|
| this README | `core/`, `analyzers/`, `cli/` (the implementation) |
| [`SPEC.md`](SPEC.md) (the rules, self-contained) | `conformance/oracle.py`, `matrix.py`, `randomized.py`, `mutation.py` |
| [`vocabulary.json`](vocabulary.json) | `conformance/results/`, `tests/` |
| [`examples.jsonl`](examples.jsonl) (format only) | `kit.py` (the team's comparison side) |
| TR-2026-01, if you want the motivation | |

If you have to look at anything in the right-hand column, say what and when in your attestation. That doesn't invalidate the work, but the record must show it.

## Deliverables

Put everything in one directory, `conformance/independent/submissions/<your-handle>-<date>/`:

1. **`review.md`:** your review of SPEC.md. Cover:
   - rules you think are wrong, and why;
   - cases the rules do not decide, or decide ambiguously;
   - places where SPEC.md and TR-2026-01 disagree;
   - anything in §8 ("Known open points") you would treat differently.

   Cite section numbers.
2. **Your oracle:** source code in any language, with a one-line command that reads a cases file (JSONL) and writes a verdicts file (JSONL, format below). It must not import or call OpenPulse.
3. **`edge_cases.jsonl`:** your hand-labelled cases. Aim for 50–150, chosen to break things rather than to be typical. Include ambiguous, stale, incomplete and conflicting evidence. Each case carries `expected` (format below):
   - `summary` and `per_event`: what **the rules** give;
   - `judgement`: what **you believe is correct** in the real world.

   They may differ. Where they do, you have found a candidate specification defect.
4. **`verdicts.jsonl`:** your oracle's output on your edge cases, and on an exported random set the team gives you (`kit.py export`, seed agreed in advance).
5. **`ATTESTATION.md`:**
   - your name, affiliation and dates;
   - what you read and what you did not;
   - whether you discussed the rules with the OpenPulse team, and if so what;
   - any conflict of interest.

## Case format (JSONL, one case per line)

```json
{
  "id": "your-unique-id",
  "dependency": {"kind": "image", "ref": "docker.io/redis:7.2"},
  "belongs_to": "redis",
  "events": [
    {
      "id": "e1",
      "project": "redis",
      "scope": {"kind": "release_line", "values": ["7.2"]},
      "named": ["docker.io/library/redis:7.2"],
      "completeness": "declared",
      "basis": "definitional",
      "admissibility": "current"
    }
  ],
  "expected": {
    "per_event": {"e1": "AFFECTS"},
    "summary": "affected",
    "rationale": "SPEC 4.3 ...",
    "judgement": "in_scope"
  },
  "note": "optional free text"
}
```

- **`dependency`:** either `{"kind": "image", "ref": ...}` or `{"kind": "package", "package": ..., "version": ...}`; the `version` may be omitted or null.
- **`belongs_to`:** the project a curated mapping assigns, or `null`. It must match `vocabulary.json`, because the implementation resolves identity from its catalog, and a mismatch would compare two different questions. Tags, digests and versions are free; only the repository path or package name must come from the vocabulary. If you need a reference that is not there, ask: the team will add one, curated or unmapped as you specify.
- **`events[].scope`:** either `null` (a project-wide event) or one kind (`artifact`, `release_line`, `package` or `registry`) with a non-empty list of values. `artifact` values are references, including namespace forms such as `docker.io/library/*` and the tag predicates `:<version>` and `:*`.
- **`completeness`:** `partial` (the default) or `declared`. A `basis` is required for a negative to be admissible, and is `null` when `completeness` is `partial`.
- **`admissibility`:** `current` (the default), `withdrawn`, `superseded`, `contested` or `stale`.
- **`expected`:** optional for exported cases, and required for your edge cases.
  - `per_event` values: `AFFECTS`, `RELATED`, `AFFECTS_PROJECT`, `NOT_AFFECTED`, `UNKNOWN`, `UNLOADED`.
  - `summary`: `affected`, `unresolved`, `cleared` or `no association`.
  - `judgement`: optional; `in_scope`, `out_of_scope` or `undeterminable`.

**Verdicts file:** one line per case: `{"id": ..., "per_event": {"e1": "AFFECTS", ...}, "summary": "affected"}`.

Check your files before submitting:

```bash
python conformance/independent/kit.py validate edge_cases.jsonl
```

`validate` only checks the format and the vocabulary. It does not reveal any answer.

## What the team does with a submission

```bash
python conformance/independent/kit.py compare --cases edge_cases.jsonl --verdicts verdicts.jsonl --out report.json
```

The report sets four sources side by side for every case:
- your `expected` outcome;
- your oracle;
- the team's oracle;
- the implementation.

It records the SHA-256 of the SPEC.md you implemented, lists every disagreement with its severity, and lists every case where your `judgement` contradicts what the rules give.

Each disagreement is **adjudicated**, jointly with you, into exactly one of:

| Outcome | Then |
|---|---|
| specification defect | SPEC.md and TR-2026-01 are corrected, and the correction is published with your case |
| implementation defect | fixed with a regression test that cites your case, and listed in the defect inventory |
| team-oracle defect | the oracle is fixed |
| independent-oracle defect | recorded, and not counted against the rules |
| label error | your expected outcome is corrected, with the reason recorded |

Everything is published:
- your cases, your review, the comparison report, and the adjudication record, in `conformance/independent/results/`;
- the disagreements, including those resolved against OpenPulse.

You are credited by name unless you ask not to be.

## Scope of what this validates

It validates the **decision rules** and their implementation on the inputs the case format can express. Identity is an input here, so the resolver is not tested; nor are discovery, event correctness or evidence quality. Those are measured separately (evaluation/PROTOCOL.md). A clean comparison means "the rules, as written, are implemented as written, and an independent reader found no defect in them". It does not mean the rules are right for every real-world change. Your `judgement` labels are the first evidence on that.

Contact: https://ikaruslabs.net/

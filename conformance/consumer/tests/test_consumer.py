"""The standalone consumer, tested on its own (v0.19.0 P1).

Standard library ``unittest`` and the consumer's one dependency only, so it
runs in an environment where OpenPulse is not installed. Against the
installed package, from any directory (CI copies only ``tests/`` out of the
checkout first):

    python -m unittest discover -s path/to/tests

``fixtures/attest-2.4.0.jsonl`` holds real documents written by
``openpulse attest`` (watchlist sample, django EOL and Bitnami events).
"""

from __future__ import annotations

import ast
import contextlib
import copy
import io
import json
import tempfile
import unittest
from dataclasses import fields
from pathlib import Path

from openpulse_consumer import check, outcome, read_jsonl, schemas, summarize, supported_versions
from openpulse_consumer.__main__ import main
from openpulse_consumer.hashes import (
    CanonicalizationError,
    canonicalize,
    hash_problem,
    v1_content_hash,
    v2_content_hash,
)
from openpulse_consumer.summary import COVERAGE, RELATIONSHIPS, TRUST_STATUSES, Outcome, Summary

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "attest-2.4.0.jsonl"
PACKAGE = Path(check.__code__.co_filename).resolve().parent
OPENPULSE_MODULES = {"core", "cli", "analyzers", "collectors", "reports", "benchmarks", "openpulse"}


def _docs() -> list[dict]:
    return [doc for _n, doc in read_jsonl(FIXTURE)]


def _run(*args: str) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = main(list(args))
    return code, out.getvalue()


class Schemas(unittest.TestCase):
    def test_every_published_version_is_bundled_once(self):
        self.assertEqual(
            supported_versions(),
            ["1.0.0", "1.1.0", "1.2.0", "2.0.0", "2.1.0", "2.2.0", "2.3.0", "2.4.0"],
        )
        self.assertEqual(len(schemas()), 8)


class Validation(unittest.TestCase):
    def test_documents_openpulse_wrote_are_valid(self):
        docs = _docs()
        self.assertEqual(len(docs), 6)
        for doc in docs:
            result = check(doc)
            self.assertTrue(result.valid, result.errors)
            self.assertEqual(result.version, "2.4.0")

    def test_a_version_without_a_published_schema_is_not_read(self):
        doc = copy.deepcopy(_docs()[0])
        doc["contract_version"] = "2.9.0"
        result = check(doc)
        self.assertFalse(result.valid)
        self.assertIn("no published schema for '2.9.0'", result.errors[0])

    def test_each_document_is_held_to_exactly_its_own_schema(self):
        """A 2.4 document relabelled 2.3 fails: 2.3 has no inspection_coverage.scope."""
        doc = copy.deepcopy(_docs()[0])
        doc["contract_version"] = "2.3.0"
        result = check(doc)
        self.assertFalse(result.valid)
        self.assertTrue(any(e.startswith("$.inspection_coverage") for e in result.errors))

    def test_missing_fields_and_unknown_fields_are_errors_with_their_path(self):
        doc = copy.deepcopy(_docs()[0])
        del doc["assessment"]
        doc["surprise"] = True
        result = check(doc)
        self.assertFalse(result.valid)
        joined = "\n".join(result.errors)
        self.assertIn("'assessment' is a required property", joined)
        self.assertIn("'surprise' was unexpected", joined)

    def test_things_that_are_not_contracts(self):
        self.assertEqual(check([1, 2]).errors, ["$: a contract is a JSON object"])
        self.assertEqual(check({}).errors, ["$.contract_version: missing or not a string"])
        self.assertIsNone(check({"contract_version": 2}).version)


class ExactVersions(unittest.TestCase):
    """P2: a document is held to exactly the schema its version names."""

    def test_only_exact_published_version_strings_are_read(self):
        for version in ("2.4", "v2.4.0", " 2.4.0", "2.4.0-rc1", "2.10.0", "3.0.0"):
            doc = copy.deepcopy(_docs()[0])
            doc["contract_version"] = version
            result = check(doc)
            self.assertFalse(result.valid, version)
            self.assertIn("no published schema", result.errors[0], version)

    def test_provenance_must_name_the_same_version(self):
        doc = copy.deepcopy(_docs()[0])
        doc["provenance"]["contract_version"] = "2.3.0"
        result = check(doc)
        self.assertFalse(result.valid)
        self.assertEqual(
            result.errors[0],
            "$.provenance.contract_version: '2.3.0' differs from the top-level "
            "contract_version '2.4.0'",
        )

    def test_formats_are_checked_as_openpulse_checks_them(self):
        cases = {
            ("temporal", "announcement_date"): "1st April",
            ("provenance", "generation_timestamp"): "yesterday",
            ("evidence_refs", 0, "url"): "www.example.com/no-scheme",
        }
        for path, bad in cases.items():
            doc = copy.deepcopy(_docs()[0])
            target = doc
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = bad
            result = check(doc)
            where = "$" + "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in path)
            self.assertFalse(result.valid, path)
            self.assertTrue(any(e.startswith(where + ":") for e in result.errors), result.errors)

    def test_well_formed_values_of_each_format_pass(self):
        doc = copy.deepcopy(_docs()[0])
        doc["temporal"]["announcement_date"] = "2026-01-31"
        doc["provenance"]["generation_timestamp"] = "2026-11-08T10:00:00+03:00"
        doc["evidence_refs"][0]["url"] = "urn:isbn:0451450523"
        doc["provenance"]["content_hash"] = v2_content_hash(doc)  # edited, so re-hashed
        self.assertTrue(check(doc).valid, check(doc).errors)

    def test_every_bundled_schema_is_closed_at_the_top(self):
        """An unknown top-level field fails in every version: no version is lenient."""
        for version, schema in schemas().items():
            self.assertIs(schema.get("additionalProperties"), False, version)


V1_FIXTURE = HERE / "fixtures" / "openpulse-1.x.jsonl"


def _all_docs() -> list[dict]:
    return _docs() + [doc for _n, doc in read_jsonl(V1_FIXTURE)]


class Hashes(unittest.TestCase):
    """P3: the content hash of 1.x and 2.x documents, recomputed."""

    def test_every_fixture_verifies_in_every_version(self):
        versions = set()
        for doc in _all_docs():
            self.assertIsNone(hash_problem(doc), doc["contract_version"])
            self.assertTrue(check(doc).valid, check(doc).errors)
            versions.add(doc["contract_version"])
        self.assertEqual(versions, {"1.0.0", "1.1.0", "1.2.0", "2.4.0"})

    def test_a_changed_document_fails_in_every_version(self):
        for doc in _all_docs():
            tampered = copy.deepcopy(doc)
            tampered["identity"]["dependency"] = "someone-else"
            result = check(tampered)
            self.assertFalse(result.valid, doc["contract_version"])
            self.assertEqual(
                result.errors,
                [
                    "$.provenance.content_hash: does not match the document: "
                    "it was changed after it was hashed"
                ],
            )

    def test_the_unhashed_timestamp_may_change(self):
        for doc in _all_docs():
            later = copy.deepcopy(doc)
            later["provenance"]["generation_timestamp"] = "2030-01-01T00:00:00Z"
            self.assertIsNone(hash_problem(later), doc["contract_version"])

    def test_the_cli_reports_a_tampered_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.jsonl"
            tampered = copy.deepcopy(_docs()[0])
            tampered["assessment"]["affected"] = not tampered["assessment"]["affected"]
            path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
            code, out = _run("check", str(path))
        self.assertEqual(code, 1)
        self.assertIn("$.provenance.content_hash: does not match the document", out)


class Canonicalization(unittest.TestCase):
    """RFC 8785's own examples (sections 3.2.2 and 3.2.3)."""

    def test_the_rfc_sample(self):
        value = json.loads(
            '{"numbers":[333333333.33333329,1E30,4.50,2e-3,0.000000000000000000000000001],'
            '"string":"\\u20ac$\\u000F\\u000aA\'\\u0042\\u0022\\u005c\\\\\\"\\/",'
            '"literals":[null,true,false]}'
        )
        self.assertEqual(
            canonicalize(value).decode("utf-8"),
            '{"literals":[null,true,false],"numbers":[333333333.3333333,1e+30,4.5,0.002,1e-27],'
            '"string":"\u20ac$\\u000f\\nA\'B\\"\\\\\\\\\\"/"}',
        )

    def test_members_are_sorted_by_utf16_code_units(self):
        names = ["\u20ac", "\r", "\ufb33", "1", "\U0001f600", "\u0080", "\u00f6"]
        text = canonicalize({name: 0 for name in names}).decode("utf-8")
        order = [json.loads(text)]  # parse back and read the key order
        self.assertEqual(
            list(order[0]),
            ["\r", "1", "\u0080", "\u00f6", "\u20ac", "\U0001f600", "\ufb33"],
        )

    def test_numbers_as_ecmascript_writes_them(self):
        cases = [
            (0.0, "0"),
            (-0.0, "0"),
            (1.0, "1"),
            (1e21, "1e+21"),
            (1e20, "100000000000000000000"),
            (1e-7, "1e-7"),
            (0.000001, "0.000001"),
            (-1.5, "-1.5"),
            (2**53, "9007199254740992"),
        ]
        for value, expected in cases:
            self.assertEqual(canonicalize(value).decode(), expected, value)

    def test_what_jcs_cannot_represent_is_refused(self):
        for value in (float("nan"), float("inf"), 2**53 + 1, "\ud800"):
            with self.assertRaises(CanonicalizationError):
                canonicalize(value)


def _rehash(doc: dict) -> dict:
    """Re-hash a document edited on purpose, so only its outcome is under test."""
    if doc["contract_version"].startswith("2."):
        doc["provenance"]["content_hash"] = v2_content_hash(doc)
    else:
        doc["provenance"]["content_hash"] = v1_content_hash(doc)
    return doc


def _by_relationship(relationship: str) -> dict:
    found = next(d for d in _docs() if d["assessment"]["relationship"] == relationship)
    return copy.deepcopy(found)


def _clear_negative() -> dict:
    """NOT_AFFECTED with every condition a negative needs met."""
    doc = _by_relationship("NOT_AFFECTED")
    doc["scope"]["completeness"]["admits_negative"] = True
    doc["inspection_coverage"]["status"] = "COMPLETE"
    doc["evaluation_context"].update(
        as_of="2026-11-01T00:00:00Z", max_evidence_age_days=30, freshness_bound_applied=True
    )
    return _rehash(doc)


def _record(status: str) -> dict:
    return {
        "check": "registry_existence",
        "status": status,
        "statement": "fixed template",
        "checked_at": None,
        "references": [],
    }


def _with_trust(doc: dict, statuses: list[str]) -> dict:
    counts = dict.fromkeys(TRUST_STATUSES, 0)
    for status in statuses:
        counts[status] += 1
    doc["trust_assurance"] = {
        "checks": [_record(s) for s in statuses],
        "summary": counts,
        "used_in_verdict": False,
    }
    return _rehash(doc)


class Outcomes(unittest.TestCase):
    """P4: documents built to tempt a summary into a pass it should not give."""

    def test_the_fixtures_are_valid_so_every_tempting_document_is_too(self):
        for doc in (_clear_negative(), _with_trust(_clear_negative(), ["MISSING_EVIDENCE"])):
            self.assertTrue(check(doc).valid, check(doc).errors)

    def test_not_affected_related_and_unknown_stay_apart(self):
        related = _by_relationship("UNKNOWN")
        related["assessment"]["relationship"] = "RELATED"
        docs = [_clear_negative(), _by_relationship("UNKNOWN"), _rehash(related)]
        self.assertTrue(all(not d["assessment"]["affected"] for d in docs))
        summary = summarize(docs)
        self.assertEqual(summary.valid, 3)
        self.assertEqual(
            {k: v for k, v in summary.relationships.items() if v},
            {"NOT_AFFECTED": 1, "UNKNOWN": 1, "RELATED": 1},
        )
        self.assertEqual(summary.outcomes[0].open, ())
        self.assertIn("relationship UNKNOWN", summary.outcomes[1].open[0])
        self.assertIn("relationship RELATED", summary.outcomes[2].open[0])
        self.assertEqual(summary.with_open_items, 2)

    def test_every_value_of_every_axis_is_reported_even_at_zero(self):
        summary = summarize([])
        self.assertEqual(list(summary.relationships), list(RELATIONSHIPS))
        self.assertEqual(len(RELATIONSHIPS), 7)
        self.assertEqual(list(summary.coverage), list(COVERAGE))
        self.assertEqual(list(summary.trust_records), list(TRUST_STATUSES))
        self.assertEqual(summary.valid, 0)

    def test_a_negative_with_partial_coverage_is_counted_on_both_axes(self):
        doc = _clear_negative()
        doc["inspection_coverage"].update(status="PARTIAL", reasons=["file cap reached"])
        summary = summarize([_rehash(doc)])
        self.assertEqual(summary.relationships["NOT_AFFECTED"], 1)
        self.assertEqual(summary.coverage["PARTIAL"], 1)
        self.assertEqual(summary.coverage["COMPLETE"], 0)
        self.assertEqual(summary.outcomes[0].open, ("inspection coverage PARTIAL",))
        self.assertEqual(summary.outcomes[0].coverage_reasons, ("file cap reached",))

    def test_a_failed_inspection_is_open(self):
        doc = _clear_negative()
        doc["inspection_coverage"].update(status="FAILED", reasons=["tree not enumerable"])
        self.assertEqual(outcome(_rehash(doc)).open, ("inspection coverage FAILED",))

    def test_a_negative_the_scope_does_not_admit_is_open(self):
        doc = _clear_negative()
        doc["scope"]["completeness"].update(state="partial", basis=None, admits_negative=False)
        self.assertEqual(
            outcome(_rehash(doc)).open, ("NOT_AFFECTED, but the scope does not admit a negative",)
        )

    def test_a_negative_without_a_freshness_bound_is_open(self):
        doc = _clear_negative()
        doc["evaluation_context"].update(
            as_of=None, max_evidence_age_days=None, freshness_bound_applied=False
        )
        (item,) = outcome(_rehash(doc)).open
        self.assertIn("no freshness bound", item)

    def test_missing_evidence_and_not_performed_are_counted_and_open(self):
        statuses = ["MISSING_EVIDENCE", "NOT_PERFORMED", "NOT_PERFORMED", "VERIFIED_RELATIONSHIP"]
        summary = summarize([_with_trust(_clear_negative(), statuses)])
        self.assertEqual(summary.trust_records["MISSING_EVIDENCE"], 1)
        self.assertEqual(summary.trust_records["NOT_PERFORMED"], 2)
        self.assertEqual(summary.trust_records["VERIFIED_RELATIONSHIP"], 1)
        self.assertEqual(summary.trust_not_checked, 0)
        self.assertEqual(
            summary.outcomes[0].open, ("trust: 1 MISSING_EVIDENCE", "trust: 2 NOT_PERFORMED")
        )

    def test_every_trust_status_but_verified_relationship_is_open(self):
        for status in TRUST_STATUSES:
            found = outcome(_with_trust(_clear_negative(), [status])).open
            expected = () if status == "VERIFIED_RELATIONSHIP" else (f"trust: 1 {status}",)
            self.assertEqual(found, expected)

    def test_trust_not_checked_is_not_a_check_that_found_nothing(self):
        unchecked = _clear_negative()
        self.assertIsNone(unchecked["trust_assurance"])
        empty = _with_trust(_clear_negative(), [])
        summary = summarize([unchecked, empty])
        self.assertEqual(summary.trust_not_checked, 1)
        self.assertIsNone(summary.outcomes[0].trust)
        self.assertEqual(summary.outcomes[1].trust, dict.fromkeys(TRUST_STATUSES, 0))

    def test_the_trust_records_are_counted_not_their_summary(self):
        doc = _with_trust(_clear_negative(), ["MISSING_EVIDENCE"])
        doc["trust_assurance"]["summary"]["MISSING_EVIDENCE"] = 0
        doc["trust_assurance"]["summary"]["VERIFIED_RELATIONSHIP"] = 1
        result = outcome(_rehash(doc))
        self.assertEqual(result.trust["MISSING_EVIDENCE"], 1)
        self.assertEqual(result.trust["VERIFIED_RELATIONSHIP"], 0)
        self.assertIn("disagrees with its records", result.open[0])

    def test_contract_1_0_reports_no_coverage_and_is_never_complete(self):
        v10 = [doc for _n, doc in read_jsonl(V1_FIXTURE) if doc["contract_version"] == "1.0.0"]
        summary = summarize(v10)
        self.assertEqual(summary.coverage["NOT_REPORTED"], len(v10))
        self.assertEqual(summary.coverage["COMPLETE"], 0)
        self.assertTrue(all("inspection coverage NOT_REPORTED" in o.open for o in summary.outcomes))
        negative = copy.deepcopy(v10[0])
        negative["assessment"].update(relationship="NOT_AFFECTED", affected=False)
        open_items = outcome(_rehash(negative)).open
        self.assertIn("does not report whether the scope admits a negative", open_items[0])

    def test_an_invalid_document_contributes_no_outcome(self):
        tampered = _clear_negative()
        tampered["assessment"]["relationship"] = "UNKNOWN"  # not re-hashed
        summary = summarize([tampered, None, {"contract_version": "2.4.0"}, _clear_negative()])
        self.assertEqual((summary.valid, summary.invalid), (1, 3))
        self.assertEqual(summary.relationships["UNKNOWN"], 0)
        self.assertEqual(summary.relationships["NOT_AFFECTED"], 1)

    def test_nothing_offers_a_pass(self):
        words = ("pass", "ok", "clean", "safe", "success", "clear", "green")
        names = [f.name for f in fields(Summary)] + [f.name for f in fields(Outcome)]
        names += list(summarize(_docs()).to_dict())
        for name in names:
            self.assertFalse(any(w in name.lower() for w in words), name)

    def test_the_real_fixtures_summarise(self):
        summary = summarize(_docs() + [doc for _n, doc in read_jsonl(V1_FIXTURE)])
        self.assertEqual((summary.valid, summary.invalid), (12, 0))
        self.assertEqual(summary.relationships["UNKNOWN"], 3)
        self.assertEqual(summary.relationships["NOT_AFFECTED"], 2)
        self.assertEqual(summary.coverage["NOT_APPLICABLE"], 6)
        self.assertEqual(summary.trust_not_checked, 12)


class Reading(unittest.TestCase):
    def test_blank_lines_are_skipped_and_bad_lines_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.jsonl"
            path.write_text('\n{"a": 1}\n\nnot json\n', encoding="utf-8")
            self.assertEqual(list(read_jsonl(path)), [(2, {"a": 1}), (4, None)])


class Cli(unittest.TestCase):
    def test_check_passes_a_file_of_valid_contracts(self):
        code, out = _run("check", str(FIXTURE))
        self.assertEqual(code, 0, out)
        self.assertIn("6 valid, 0 invalid", out)

    def test_check_fails_on_any_invalid_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mixed.jsonl"
            bad = copy.deepcopy(_docs()[0])
            bad["contract_version"] = "2.9.0"
            lines = [json.dumps(_docs()[1]), json.dumps(bad), "{oops"]
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            code, out = _run("check", str(path))
        self.assertEqual(code, 1)
        self.assertIn("1 valid, 2 invalid", out)
        self.assertIn(":2: INVALID (contract 2.9.0)", out)
        self.assertIn(":3: INVALID: not JSON", out)

    def test_an_unreadable_or_empty_file_is_an_error_not_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.jsonl"
            empty.write_text("\n", encoding="utf-8")
            self.assertEqual(_run("check", str(empty))[0], 2)
            self.assertEqual(_run("check", str(Path(tmp) / "missing.jsonl"))[0], 2)

    def test_summary_prints_every_axis_and_no_verdict(self):
        code, out = _run("summary", str(FIXTURE))
        self.assertEqual(code, 0, out)
        self.assertIn("documents: 6 valid and summarised, 0 invalid", out)
        self.assertIn("NOT_AFFECTED 2", out)
        self.assertIn("RELATED 0", out)
        self.assertIn("UNKNOWN 3", out)
        self.assertIn("MISSING_EVIDENCE 0", out)
        self.assertIn("trust not checked: 6 document(s)", out)
        self.assertIn("open: relationship UNKNOWN", out)
        self.assertIn("not a pass or fail", out)

    def test_summary_json_and_invalid_documents(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mixed.jsonl"
            bad = copy.deepcopy(_docs()[0])
            bad["assessment"]["relationship"] = "NOT_AFFECTED"
            path.write_text(
                json.dumps(_docs()[1]) + "\n" + json.dumps(bad) + "\n", encoding="utf-8"
            )
            code, out = _run("summary", str(path))
            self.assertEqual(code, 1)
            self.assertIn(":2: INVALID, not summarised", out)
            code, out = _run("summary", "--json", str(path))
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual((data["valid"], data["invalid"]), (1, 1))
        self.assertEqual(data["relationships"]["NOT_AFFECTED"], 0)

    def test_summary_of_an_empty_file_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.jsonl"
            empty.write_text("\n", encoding="utf-8")
            self.assertEqual(_run("summary", str(empty))[0], 2)

    def test_versions_lists_the_readable_versions(self):
        code, out = _run("versions")
        self.assertEqual(code, 0)
        self.assertEqual(out.split(), supported_versions())


class Independence(unittest.TestCase):
    def test_the_package_imports_nothing_from_openpulse(self):
        for path in PACKAGE.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    names = [node.module]
                for name in names:
                    self.assertNotIn(name.split(".")[0], OPENPULSE_MODULES, f"{path.name}: {name}")


if __name__ == "__main__":
    unittest.main()

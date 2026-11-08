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
from pathlib import Path

from openpulse_consumer import check, read_jsonl, schemas, supported_versions
from openpulse_consumer.__main__ import main

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
        self.assertTrue(check(doc).valid, check(doc).errors)

    def test_every_bundled_schema_is_closed_at_the_top(self):
        """An unknown top-level field fails in every version: no version is lenient."""
        for version, schema in schemas().items():
            self.assertIs(schema.get("additionalProperties"), False, version)


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

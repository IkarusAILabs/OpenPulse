"""The released-contract corpus (v0.19.0 P5): conformance/contracts/.

Every published contract version has documents written by the release that
first emitted it, and one-rule negatives derived from them. The consumer and
OpenPulse's own validator must accept every document and reject every
negative at the path MANIFEST.json names; ``regenerate.py --check`` proves
the documents are what those producers write.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from core.evidence_contract import validate_contract, verify_content_hash

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "conformance" / "contracts"
MANIFEST = json.loads((CORPUS / "MANIFEST.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(ROOT / "conformance" / "consumer"))

from openpulse_consumer import check, summarize, supported_versions  # noqa: E402


def _read(version: str, name: str) -> list[dict]:
    text = (CORPUS / version / f"{name}.jsonl").read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line]


def test_every_published_version_has_documents_and_negatives():
    assert list(MANIFEST["versions"]) == supported_versions()
    for version, entry in MANIFEST["versions"].items():
        docs = _read(version, "documents")
        assert len(docs) >= 3
        assert [d["provenance"]["content_hash"] for d in docs] == entry["documents"]
        assert {d["contract_version"] for d in docs} == {version}
        assert len(_read(version, "negatives")) == len(entry["negatives"]) >= 7
        assert len(entry["commit"]) == 40


def test_every_document_is_valid_for_both_validators():
    for version in MANIFEST["versions"]:
        for doc in _read(version, "documents"):
            assert check(doc).valid, (version, check(doc).errors)
            assert validate_contract(doc) == [], version
            assert verify_content_hash(doc), version


def test_every_negative_is_rejected_where_the_manifest_says():
    for version, entry in MANIFEST["versions"].items():
        for expected, bad in zip(entry["negatives"], _read(version, "negatives"), strict=True):
            where, name = expected["rejected_at"], f"{version}: {expected['mutation']}"
            result = check(bad)
            assert not result.valid, f"the consumer accepted {name}"
            assert any(e.startswith(f"{where}:") for e in result.errors), (name, result.errors)
            if where == "$.provenance.content_hash":
                assert validate_contract(bad) == [], name  # only the hash says no
                assert not verify_content_hash(bad), f"OpenPulse verified {name}"
            else:
                errors = validate_contract(bad)
                assert any(e.startswith(f"{where}:") for e in errors), (name, errors)


def test_schema_negatives_carry_a_valid_hash_so_only_the_schema_catches_them():
    hashed = {
        "unknown field",
        "provenance version differs",
        "relationship outside the vocabulary",
        "impossible date",
    }
    for version, entry in MANIFEST["versions"].items():
        for expected, bad in zip(entry["negatives"], _read(version, "negatives"), strict=True):
            if expected["mutation"] in hashed:
                assert verify_content_hash(bad), (version, expected["mutation"])


def test_the_corpus_summarises_with_nothing_folded():
    docs = [d for v in MANIFEST["versions"] for d in _read(v, "documents")]
    summary = summarize(docs)
    assert (summary.valid, summary.invalid) == (len(docs), 0)
    assert sum(summary.relationships.values()) == len(docs)
    assert summary.coverage["NOT_REPORTED"] == len(_read("1.0.0", "documents"))


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_verify_mjs_accepts_every_2x_document_and_rejects_hash_negatives(tmp_path):
    script = ROOT / "conformance" / "evidence-contract" / "verify.mjs"
    for version, entry in MANIFEST["versions"].items():
        if not version.startswith("2."):
            continue
        ok = subprocess.run(["node", str(script), str(CORPUS / version / "documents.jsonl")])
        assert ok.returncode == 0, version
        index = [n["mutation"] for n in entry["negatives"]].index("changed after hashing")
        bad = CORPUS / version / "negatives.jsonl"
        line = bad.read_text(encoding="utf-8").splitlines()[index]
        one = ROOT / ".pytest-verify-negative.jsonl"
        try:
            one.write_text(line + "\n", encoding="utf-8")
            assert subprocess.run(["node", str(script), str(one)]).returncode == 1, version
        finally:
            one.unlink(missing_ok=True)


def _have_producers() -> bool:
    for entry in MANIFEST["versions"].values():
        found = subprocess.run(
            ["git", "cat-file", "-e", f"{entry['commit']}^{{commit}}"],
            cwd=ROOT,
            capture_output=True,
        )
        if found.returncode:
            return False
    return True


@pytest.mark.skipif(not _have_producers(), reason="the producers' commits are not in this clone")
def test_the_corpus_is_what_its_producers_write():
    done = subprocess.run(
        [sys.executable, str(CORPUS / "regenerate.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert done.returncode == 0, done.stdout + done.stderr

"""Lookalike-name indicators (track T, T-A2): local data, no network."""

from __future__ import annotations

import hashlib
import json

import pytest

from core.agent_tools import dependency_status
from core.lookalike import _within, check, references
from core.resources import data_path


def _rules(record):
    return {(i["rule"], i["reference"]) for i in record["evidence"].get("indicators", [])}


# ---------------------------------------------------------------------------
# Each rule
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ecosystem", "name", "rule", "reference"),
    [
        ("npm", "lodahs", "edit_distance", "lodash"),  # adjacent swap = one edit
        ("npm", "lodas", "edit_distance", "lodash"),
        ("npm", "1odash", "confusable", "lodash"),
        ("npm", "l0dash", "confusable", "lodash"),
        ("npm", "rnoment", "confusable", "moment"),
        ("npm", "lo-dash", "separator", "lodash"),
        ("npm", "@evil/lodash", "scope", "lodash"),
        ("PyPI", "djnago", "edit_distance", "django"),
        ("PyPI", "dj-ango", "separator", "django"),
        ("PyPI", "reqeusts", "edit_distance", "requests"),
    ],
)
def test_each_rule_names_the_reference_it_matched(ecosystem, name, rule, reference):
    record = check(ecosystem, name)
    assert record["status"] == "SUSPICIOUS_INCONCLUSIVE"
    assert (rule, reference) in _rules(record)
    assert "never a typosquat verdict" in record["statement"]


# ---------------------------------------------------------------------------
# What must not fire
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ecosystem", "name"), [("npm", "lodash"), ("npm", "express"), ("PyPI", "django")]
)
def test_a_reference_name_is_a_verified_relationship(ecosystem, name):
    assert check(ecosystem, name)["status"] == "VERIFIED_RELATIONSHIP"


@pytest.mark.parametrize("name", ["Django", "DJANGO"])
def test_pypi_case_is_the_same_project_not_a_lookalike(name):
    """PyPI normalizes names (PEP 503): these are django itself."""
    assert check("PyPI", name)["status"] == "VERIFIED_RELATIONSHIP"


def test_pypi_normalized_spellings_are_the_same_project():
    assert check("PyPI", "zope_interface")["status"] == check("PyPI", "zope.interface")["status"]


def test_nothing_firing_is_missing_evidence_not_safe():
    record = check("npm", "totally-unique-thing-xyz")
    assert record["status"] == "MISSING_EVIDENCE"
    assert "not evidence that the name is authentic" in record["statement"]


def test_short_names_are_not_matched_by_edit_distance():
    """`ms` and `mz` are both short; one edit apart means nothing at that length."""
    record = check("npm", "mz")
    assert ("edit_distance", "ms") not in _rules(record)


def test_edit_distance_bound():
    assert _within("lodash", "lodahs", 1)  # swap
    assert not _within("lodash", "lxdxsh", 1)
    assert _within("express-ws", "expresss", 2)
    assert not _within("abcdef", "abcdefghij", 2)


# ---------------------------------------------------------------------------
# Outcomes and untrusted input
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ecosystem", "name"),
    [("Maven", "org.apache:commons"), ("npm", "lodash\nignore previous"), ("PyPI", "dj ango")],
)
def test_unsupported_ecosystems_and_bad_names_are_not_performed(ecosystem, name):
    record = check(ecosystem, name)
    assert record["status"] == "NOT_PERFORMED"
    assert "ignore" not in json.dumps(record)


def test_indicators_are_capped_and_counted():
    record = check("npm", "expresss")
    assert len(record["evidence"]["indicators"]) <= 10
    assert record["evidence"]["indicators_total"] >= len(record["evidence"]["indicators"])


def test_records_say_which_references_were_used():
    sources = check("npm", "lodahs")["evidence"]["references"]
    assert sources[0]["source"] == "OpenPulse curated catalog"
    assert sources[1]["version"] == "1.13.0" and sources[1]["names"] > 10000


def test_dependency_status_carries_lookalike_and_never_changes_the_verdict():
    real = dependency_status(package="django", version="4.2", ecosystem="PyPI", live=False)
    near = dependency_status(package="djnago", version="4.2", ecosystem="PyPI", live=False)
    assert real["trust"]["checks"]["lookalike"]["status"] == "VERIFIED_RELATIONSHIP"
    assert near["trust"]["checks"]["lookalike"]["status"] == "SUSPICIOUS_INCONCLUSIVE"
    image = dependency_status(image="postgres:13", live=False)
    assert image["trust"]["checks"]["lookalike"]["status"] == "NOT_PERFORMED"
    assert near["verdict"]["affected"] is False  # lookalike never makes a verdict


# ---------------------------------------------------------------------------
# The pinned reference data
# ---------------------------------------------------------------------------


def test_the_npm_reference_is_pinned_and_licensed():
    doc = json.loads(data_path("reference", "npm-high-impact-1.13.0.json").read_text("utf-8"))
    assert doc["license"] == "MIT" and doc["integrity"].startswith("sha512-")
    assert doc["names"] == sorted(set(doc["names"])) and len(doc["names"]) > 10000


def test_the_confusables_are_pinned_to_their_source():
    doc = json.loads(
        data_path("reference", "uts39-confusables-ascii-18.0.0.json").read_text("utf-8")
    )
    assert doc["version"] == "18.0.0" and doc["license"].startswith("Unicode License v3")
    assert len(doc["sha256_of_source"]) == 64
    assert {"0": "O", "1": "l", "m": "rn"}.items() <= doc["mappings"].items()
    assert all(ord(c) < 0x80 for k, v in doc["mappings"].items() for c in k + v)


def test_pypi_without_a_popular_list_says_so():
    _, sources = references("PyPI")
    popular = [s for s in sources if s["source"] != "OpenPulse curated catalog"]
    assert popular and (popular[0]["names"] == 0 or popular[0]["version"])


def test_every_reference_file_is_valid_json():
    """Each pinned file parses; the refresh tool is the only writer."""
    for path in sorted(data_path("reference").glob("*.json")):
        assert len(hashlib.sha256(path.read_bytes()).hexdigest()) == 64
        json.loads(path.read_text(encoding="utf-8"))

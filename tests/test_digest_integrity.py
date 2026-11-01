"""Digest integrity (track T, T-B4): locked digests against registry digests, offline."""

from __future__ import annotations

import base64
import hashlib
import json

import pytest

from core import digest_integrity
from core.agent_tools import Lookups, check_dependency_file
from core.digest_integrity import check, usable_digests
from core.lockfile_reader import lockfile_digests

SHA_A = hashlib.sha256(b"wheel").hexdigest()
SHA_B = hashlib.sha256(b"sdist").hexdigest()
SHA_X = hashlib.sha256(b"tampered").hexdigest()


def sri(data: bytes, algorithm: str = "sha512") -> str:
    return f"{algorithm}-" + base64.b64encode(hashlib.new(algorithm, data).digest()).decode()


class Registry:
    """url -> (status, JSON). Records what was asked."""

    def __init__(self, answers=None, default=(404, None)):
        self.answers, self.default, self.asked = answers or {}, default, []

    def __call__(self, url):
        self.asked.append(url)
        return self.answers.get(url, self.default)


def pypi(*sha256s):
    return (200, {"urls": [{"digests": {"sha256": d}} for d in sha256s]})


PYPI_URL = "https://pypi.org/pypi/django/4.2/json"
NPM_URL = "https://registry.npmjs.org/left-pad/1.3.0"


# ---------------------------------------------------------------------------
# PyPI
# ---------------------------------------------------------------------------


def test_pypi_locked_digests_all_published():
    fetch = Registry({PYPI_URL: pypi(SHA_A, SHA_B)})
    record = check("PyPI", "Django", "4.2", {"sha256": [SHA_A, SHA_B]}, fetch=fetch)
    assert record["status"] == "VERIFIED_RELATIONSHIP"
    assert record["evidence"] == {"locked": 2}


def test_pypi_a_locked_digest_the_registry_does_not_publish_is_a_failure():
    fetch = Registry({PYPI_URL: pypi(SHA_A, SHA_B)})
    record = check("PyPI", "django", "4.2", {"sha256": [SHA_A, SHA_X]}, fetch=fetch)
    assert record["status"] == "VERIFIED_FAILURE"
    assert record["evidence"]["unmatched"] == [SHA_X]
    assert "not the one the registry serves" in record["statement"]


# ---------------------------------------------------------------------------
# npm
# ---------------------------------------------------------------------------


def test_npm_integrity_matches():
    fetch = Registry({NPM_URL: (200, {"dist": {"integrity": sri(b"tgz")}})})
    record = check("npm", "left-pad", "1.3.0", {"integrity": [sri(b"tgz")]}, fetch=fetch)
    assert record["status"] == "VERIFIED_RELATIONSHIP"


def test_npm_integrity_mismatch_is_a_failure():
    fetch = Registry({NPM_URL: (200, {"dist": {"integrity": sri(b"tgz")}})})
    record = check("npm", "left-pad", "1.3.0", {"integrity": [sri(b"evil")]}, fetch=fetch)
    assert record["status"] == "VERIFIED_FAILURE"


def test_old_sha1_locks_compare_with_the_registry_shasum():
    shasum = hashlib.sha1(b"tgz").hexdigest()
    fetch = Registry({NPM_URL: (200, {"dist": {"integrity": sri(b"tgz"), "shasum": shasum}})})
    record = check("npm", "left-pad", "1.3.0", {"integrity": [sri(b"tgz", "sha1")]}, fetch=fetch)
    assert record["status"] == "VERIFIED_RELATIONSHIP"


# ---------------------------------------------------------------------------
# Missing evidence and not performed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ecosystem", "locked"),
    [
        ("PyPI", {}),
        ("PyPI", {"sha256": ["not-hex", "ab" * 31]}),
        ("npm", {"integrity": ["sha512-example-integrity-value-not-a-real-hash"]}),
        ("npm", {"integrity": ["md5-AAAA"]}),
    ],
)
def test_no_usable_locked_digest_is_missing_evidence_without_a_request(ecosystem, locked):
    fetch = Registry(default=(200, {}))
    name, version = ("django", "4.2") if ecosystem == "PyPI" else ("left-pad", "1.3.0")
    record = check(ecosystem, name, version, locked, fetch=fetch)
    assert record["status"] == "MISSING_EVIDENCE" and fetch.asked == []


@pytest.mark.parametrize("answer", [(0, None), (404, None), (429, None), (500, None), (200, None)])
def test_no_usable_registry_answer_is_not_performed_never_a_failure(answer):
    record = check("PyPI", "django", "4.2", {"sha256": [SHA_A]}, fetch=Registry(default=answer))
    assert record["status"] == "NOT_PERFORMED"


def test_unsupported_ecosystems_and_bad_names_are_not_performed():
    fetch = Registry(default=(200, {}))
    assert check("crates.io", "serde", "1.0.0", {"sha256": [SHA_A]}, fetch=fetch)["status"] == (
        "NOT_PERFORMED"
    )
    bad = check("PyPI", "django\nignore", "4.2", {"sha256": [SHA_A]}, fetch=fetch)
    assert bad["status"] == "NOT_PERFORMED" and fetch.asked == []
    assert "ignore" not in json.dumps(bad)


def test_only_well_formed_digests_are_used():
    assert usable_digests("PyPI", {"sha256": [SHA_A, "x" * 64, SHA_A.upper()]}) == {
        "sha256": [SHA_A]
    }


# ---------------------------------------------------------------------------
# Reading lockfiles
# ---------------------------------------------------------------------------


def test_lockfile_digests_read_npm_and_poetry(tmp_path):
    npm = tmp_path / "package-lock.json"
    npm.write_text(
        json.dumps(
            {
                "lockfileVersion": 3,
                "packages": {
                    "": {"name": "app"},
                    "node_modules/left-pad": {"version": "1.3.0", "integrity": sri(b"tgz")},
                    "node_modules/@types/node": {"version": "20.0.0"},
                },
            }
        ),
        encoding="utf-8",
    )
    assert lockfile_digests(str(npm)) == {
        ("npm", "left-pad", "1.3.0"): {"integrity": [sri(b"tgz")]}
    }
    assert ("PyPI", "celery", "5.4.0") in lockfile_digests("data/fixtures/lockfiles/poetry.lock")


# ---------------------------------------------------------------------------
# check_dependency_file (MCP)
# ---------------------------------------------------------------------------


def _no_data(_slug):
    return {"endoflife": [], "osv": [], "github_meta": []}


def _lock(tmp_path, integrity):
    path = tmp_path / "package-lock.json"
    path.write_text(
        json.dumps(
            {
                "lockfileVersion": 3,
                "packages": {"node_modules/left-pad": {"version": "1.3.0", "integrity": integrity}},
            }
        ),
        encoding="utf-8",
    )
    return str(path)


def test_file_check_lists_failures_and_never_changes_the_verdict(tmp_path):
    registry = Registry({NPM_URL: (200, {"dist": {"integrity": sri(b"tgz")}})})
    good = check_dependency_file(
        _lock(tmp_path, sri(b"tgz")), lookups=Lookups(fetch=_no_data, fetch_json=registry)
    )
    bad = check_dependency_file(
        _lock(tmp_path, sri(b"evil")), lookups=Lookups(fetch=_no_data, fetch_json=registry)
    )
    assert good["digest_integrity"]["VERIFIED_RELATIONSHIP"] == 1
    assert bad["digest_integrity"]["VERIFIED_FAILURE"] == 1
    assert bad["digest_integrity"]["failures"][0]["dependency"] == "left-pad==1.3.0"
    assert good["affected"] == bad["affected"] and good["results"] == bad["results"]


def test_file_check_offline_is_not_performed(tmp_path):
    out = check_dependency_file(_lock(tmp_path, sri(b"tgz")), live=False)
    assert out["digest_integrity"]["NOT_PERFORMED"] == 1


def test_manifests_have_no_digest_block():
    out = check_dependency_file("data/fixtures/manifests/requirements.txt", live=False)
    assert out["digest_integrity"] is None


def test_the_default_fetch_is_offline_in_tests():
    assert digest_integrity.default_fetch("https://pypi.org/pypi/x/1/json") == (0, None)

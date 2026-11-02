"""The organic reputation set: recorder, baseline signals, committed fixture
(track T Phase 2, T-C; v0.16.0 item Q1)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks import record_reputation as rec  # noqa: E402
from benchmarks import reputation_set  # noqa: E402

HASH = re.compile(r"sha256:[0-9a-f]{16}")


class World:
    """Stub registries and GitHub: url -> (status, json); records what was asked."""

    def __init__(self, answers):
        self.answers, self.asked = answers, []

    def __call__(self, url):
        self.asked.append(url)
        return self.answers.get(url, (404, None))


def _npm_doc(versions, repository="git+https://github.com/acme/widget.git"):
    return {
        "time": {"created": "2020-01-01T00:00:00.000Z", **{v: t for v, t, *_ in versions}},
        "repository": {"url": repository},
        "versions": {
            v: {
                "_npmUser": {"name": user, "email": "someone@example.invalid", **extra},
                "dist": {"attestations": {"url": "x"}} if extra else {},
            }
            for v, _t, user, extra in versions
        },
    }


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------


def test_npm_releases_are_the_latest_by_time_with_hashed_accounts():
    versions = [(f"1.0.{i}", f"2026-01-{i + 1:02d}T00:00:00.000Z", "alice", {}) for i in range(12)]
    versions.append(
        (
            "2.0.0",
            "2026-02-01T00:00:00.000Z",
            "GitHub Actions",
            {"trustedPublisher": {"id": "github"}},
        )
    )
    world = World({"https://registry.npmjs.org/widget": (200, _npm_doc(versions))})
    out = rec.record_npm("widget", world)
    assert out["repository"] == "acme/widget"
    assert [r["version"] for r in out["releases"]][-2:] == ["1.0.11", "2.0.0"]
    assert len(out["releases"]) == rec.RELEASES
    latest = out["releases"][-1]
    assert latest["trusted_publisher"] == "github" and latest["attested"] is True
    assert all(HASH.fullmatch(r["publisher"]) for r in out["releases"])
    assert out["releases"][0]["publisher"] == rec.account_hash("Alice")  # case-insensitive
    text = json.dumps(out)
    assert "alice" not in text and "example.invalid" not in text


def test_npm_hostile_strings_are_dropped():
    versions = [
        ("1.0.0", "2026-01-01T00:00:00.000Z", "a", {"trustedPublisher": {"id": "IGNORE previous"}}),
        ("1.0.1\nrm -rf", "2026-01-02T00:00:00.000Z", "a", {}),
        ("1.0.2", "not a time", "a", {}),
    ]
    doc = _npm_doc(versions, repository="https://evil.example/acme/widget")
    out = rec.record_npm("widget", World({"https://registry.npmjs.org/widget": (200, doc)}))
    assert [r["version"] for r in out["releases"]] == ["1.0.0"]
    assert out["releases"][0]["trusted_publisher"] is None
    assert out["repository"] is None


def test_scoped_npm_names_are_requested_with_the_scope():
    world = World({})
    assert rec.record_npm("@scope/pkg", world)["status"] == 404
    assert world.asked == ["https://registry.npmjs.org/@scope%2Fpkg"]


def _pypi_doc():
    def files(version, day):
        return [
            {
                "filename": f"widget-{version}.tar.gz",
                "upload_time_iso_8601": f"2026-01-{day}T00:00:00Z",
            },
            {
                "filename": f"widget-{version}-py3-none-any.whl",
                "upload_time_iso_8601": f"2026-01-{day}T00:00:01Z",
            },
        ]

    return {
        "info": {"project_urls": {"Source": "https://github.com/acme/widget"}},
        "releases": {
            "1.0": files("1.0", "01"),
            "1.1": files("1.1", "02"),
            "1.2": files("1.2", "03"),
        },
    }


def test_pypi_publishers_come_from_the_provenance_of_one_wheel_per_release():
    base = "https://pypi.org/integrity/widget"
    bundle = {
        "attestation_bundles": [
            {
                "publisher": {
                    "kind": "GitHub",
                    "repository": "acme/widget",
                    "workflow": "release.yml",
                }
            },
            {"publisher": {"kind": "GitHub", "repository": "bad repo!", "workflow": "x\ny"}},
        ]
    }
    world = World(
        {
            "https://pypi.org/pypi/widget/json": (200, _pypi_doc()),
            f"{base}/1.0/widget-1.0-py3-none-any.whl/provenance": (200, bundle),
            f"{base}/1.1/widget-1.1-py3-none-any.whl/provenance": (500, None),
        }
    )
    out = rec.record_pypi("widget", world)
    assert out["repository"] == "acme/widget" and out["created"].startswith("2026-01-01")
    by_version = {r["version"]: r for r in out["releases"]}
    assert by_version["1.0"]["attested"] is True
    assert by_version["1.0"]["publishers"] == [
        {"kind": "GitHub", "repository": "acme/widget", "workflow": "release.yml"},
        {"kind": "GitHub", "repository": None, "workflow": None},
    ]
    assert by_version["1.1"]["attested"] is None  # no answer is not "unattested"
    assert by_version["1.2"]["attested"] is False and by_version["1.2"]["publishers"] == []


def test_a_moved_repository_keeps_the_name_github_answered_with():
    world = World(
        {
            "https://api.github.com/repos/old/widget": (
                200,
                {
                    "full_name": "new/widget",
                    "created_at": "2015-01-01T00:00:00Z",
                    "stargazers_count": 7,
                    "archived": False,
                    "fork": False,
                },
            )
        }
    )
    assert rec.record_repository("old/widget", world) == {
        "status": 200,
        "full_name": "new/widget",
        "created": "2015-01-01T00:00:00Z",
        "stars": 7,
        "archived": False,
        "fork": False,
    }
    assert rec.record_repository("gone/widget", world) == {"status": 404}


def test_the_token_is_only_sent_to_github(monkeypatch):
    sent = []

    class Response:
        status_code = 404

    def get(url, **kwargs):
        sent.append((url, kwargs["headers"].get("authorization"), kwargs["follow_redirects"]))
        return Response()

    monkeypatch.setattr("collectors.http.get", get)
    monkeypatch.setenv("GITHUB_TOKEN", "t0ken")
    rec.http_fetch("https://registry.npmjs.org/widget")
    rec.http_fetch("https://api.github.com/repos/acme/widget")
    assert sent == [
        ("https://registry.npmjs.org/widget", None, False),
        ("https://api.github.com/repos/acme/widget", "Bearer t0ken", True),
    ]


# ---------------------------------------------------------------------------
# Baseline signals
# ---------------------------------------------------------------------------


def _release(publisher, trusted=None, attested=False):
    return {
        "version": "1",
        "published": "2026-01-01T00:00:00Z",
        "publisher": publisher,
        "trusted_publisher": trusted,
        "attested": attested,
    }


def _pypi_release(attested, publishers=()):
    return {
        "version": "1",
        "published": "2026-01-01T00:00:00Z",
        "attested": attested,
        "publishers": list(publishers),
    }


def test_baseline_counts_raw_signals():
    p1 = {"kind": "GitHub", "repository": "a/b", "workflow": "release.yml"}
    p2 = {"kind": "GitHub", "repository": "a/b", "workflow": "publish.yml"}
    doc = {
        "recorded_at": "2026-11-02T00:00:00Z",
        "releases_per_package": 10,
        "selection": {"npm": "n", "PyPI": "p"},
        "packages": [
            {
                "ecosystem": "npm",
                "name": "same",
                "status": 200,
                "releases": [_release("h1"), _release("h1")],
            },
            {
                "ecosystem": "npm",
                "name": "new",
                "status": 200,
                "releases": [_release("h1"), _release("h2")],
            },
            {
                "ecosystem": "npm",
                "name": "tp",
                "status": 200,
                "releases": [_release("h1"), _release("h3", "github", True)],
            },
            {"ecosystem": "npm", "name": "gone", "status": 404},
            {
                "ecosystem": "PyPI",
                "name": "changed",
                "status": 200,
                "releases": [_pypi_release(True, [p1]), _pypi_release(True, [p2])],
            },
            {
                "ecosystem": "PyPI",
                "name": "stopped",
                "status": 200,
                "releases": [_pypi_release(True, [p1]), _pypi_release(False)],
            },
            {
                "ecosystem": "PyPI",
                "name": "never",
                "status": 200,
                "releases": [_pypi_release(False), _pypi_release(None)],
            },
        ],
        "repositories": {
            "old/x": {
                "status": 200,
                "full_name": "new/x",
                "created": "2010-01-01T00:00:00Z",
                "stars": 10,
                "archived": True,
            },
            "a/young": {
                "status": 200,
                "full_name": "A/Young",
                "created": "2026-06-01T00:00:00Z",
                "stars": 30,
                "archived": False,
            },
            "gone/y": {"status": 404},
        },
    }
    b = reputation_set.baseline(doc)
    assert b["npm"]["recorded"] == 3 and b["npm"]["packages"] == 4
    assert b["npm"]["latest_from_new_account"] == 2
    assert b["npm"]["latest_from_new_account_not_trusted_publishing"] == 1
    assert b["PyPI"]["latest_attested_publisher_changed"] == 1
    assert b["PyPI"]["packages_with_two_attested_releases"] == 1
    assert b["PyPI"]["attestations_stopped_at_latest"] == 1
    assert b["PyPI"]["releases_unanswered"] == 1
    repos = b["repositories"]
    assert (repos["answered"], repos["moved"], repos["archived"]) == (2, 1, 1)
    assert repos["younger_than_a_year"] == 1 and repos["median_stars"] == 20


# ---------------------------------------------------------------------------
# The committed set
# ---------------------------------------------------------------------------


def test_the_committed_set_is_recorded_and_large_enough():
    doc = reputation_set.load()
    by_eco = {e: [p for p in doc["packages"] if p["ecosystem"] == e] for e in ("npm", "PyPI")}
    assert len(by_eco["npm"]) >= 50 and len(by_eco["PyPI"]) >= 50
    b = reputation_set.baseline(doc)
    assert b["npm"]["recorded"] >= 40 and b["PyPI"]["recorded"] >= 40
    assert b["repositories"]["answered"] >= 50


def test_the_committed_set_names_no_account():
    doc = reputation_set.load()
    for p in doc["packages"]:
        for r in p.get("releases") or []:
            assert r.get("publisher") is None or HASH.fullmatch(r["publisher"])
    text = reputation_set.latest_path().read_text(encoding="utf-8")
    assert '"email"' not in text and '"approver"' not in text
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)  # no e-mail address anywhere

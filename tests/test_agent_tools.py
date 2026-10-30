"""Agent tools (core/agent_tools.py) - the MCP server's SDK-free engine."""

import json
from datetime import date

import pytest

from core import agent_tools
from core.agent_tools import (
    Lookups,
    check_dependency_file,
    dependency_status,
    project_lifecycle,
)

TODAY = date(2026, 10, 24)
_PG = json.load(open("data/fixtures/postgresql/raw_bundle.json", encoding="utf-8"))
_NO_DATA = {
    "endoflife": [{"collector": "endoflife", "skipped": "no product"}],
    "osv": [],
    "github_meta": [],
}


def _lookups(calls=None):
    def fetch(slug):
        if calls is not None:
            calls.append(slug)
        return _PG if slug == "postgresql" else _NO_DATA

    return Lookups(fetch=fetch)


def test_live_lifecycle_eol_reaches_the_verdict_with_evidence():
    out = dependency_status(image="docker.io/postgres:13", lookups=_lookups(), today=TODAY)
    assert out["identity"]["project"] == "postgresql"
    assert out["verdict"]["affected"] is True
    assert out["verdict"]["relationship"] == "AFFECTS_VERSION"
    eol = [c for c in out["causes"] if c["type"] == "EOL"]
    assert eol and eol[0]["evidence_urls"]
    assert out["note"].startswith("OpenPulse evidence, not a decision")


def test_supported_line_is_cleared_not_flagged():
    out = dependency_status(image="docker.io/postgres:17", lookups=_lookups(), today=TODAY)
    assert out["verdict"]["affected"] is False
    assert out["verdict"]["relationship"] == "NOT_AFFECTED"


def test_causes_only_concern_the_asked_project():
    """Curated Bitnami/iText events must not clutter a Postgres answer."""
    out = dependency_status(image="docker.io/postgres:13", lookups=_lookups(), today=TODAY)
    assert {c["event"].split("-")[1] for c in out["causes"]} == {"postgresql"}


def test_curated_event_answers_offline():
    out = dependency_status(package="django", version="4.2", ecosystem="PyPI", live=False)
    assert out["verdict"]["affected"] is True
    assert [c["event"] for c in out["causes"]] == ["evt-django-2026-eol-001"]
    assert {"source": "live lookups", "status": "disabled"} in out["sources"]
    assert "live lookups" in out["not_established"]


def test_unreachable_source_is_unknown_never_safe():
    def down(slug):
        err = {"collector": "endoflife", "error": True, "safe_message": "ConnectError"}
        return {"endoflife": [err], "osv": [], "github_meta": []}

    # A curated package with no applicable event: an unmapped one would be
    # unresolved (RELATED), not unknown (TR-2026-01 D13).
    out = dependency_status(
        package="serde", version="1.0.0", ecosystem="crates.io", lookups=Lookups(fetch=down)
    )
    assert out["verdict"]["affected"] is False
    assert out["verdict"]["relationship"] == "UNKNOWN"
    assert "endoflife.date" in out["not_established"]


def test_missing_version_is_reported_as_not_established():
    out = dependency_status(package="django", ecosystem="PyPI", live=False)
    assert any(u.startswith("version") for u in out["not_established"])


def test_no_dependency_given_is_an_error():
    with pytest.raises(ValueError, match="package name"):
        dependency_status(live=False)


def test_live_lookups_are_cached_per_project():
    calls = []
    lookups = _lookups(calls)
    dependency_status(image="postgres:13", lookups=lookups, today=TODAY)
    dependency_status(image="postgres:17", lookups=lookups, today=TODAY)
    assert calls == ["postgresql"]


def test_dependency_file_reports_skips_and_affected():
    out = check_dependency_file("data/fixtures/manifests/requirements.txt", live=False)
    assert out["format"] == "requirements"
    assert out["affected"] == ["django==4.2"]
    assert any("never range-guessed" in s for s in out["skipped"])
    assert out["dependencies_checked"] == len(out["results"]) + len(out["unflagged"])


def test_dependency_file_bounds_live_lookups(monkeypatch):
    monkeypatch.setattr(agent_tools, "MAX_LIVE_PROJECTS", 1)
    calls = []
    out = check_dependency_file(
        "data/fixtures/lockfiles/poetry.lock", lookups=_lookups(calls), today=TODAY
    )
    assert out["live_projects_looked_up"] == 1
    assert len(set(calls)) == 1


def test_unrecognized_file_is_refused(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("# hello\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not a recognized dependency file"):
        check_dependency_file(str(path), live=False)


def test_project_lifecycle_lists_supported_cycles():
    out = project_lifecycle("postgres", lookups=_lookups(), today=TODAY)
    assert out["project"] == "postgresql"
    assert out["supported_cycles"] == ["17"]
    assert {c["cycle"]: c["status"] for c in out["cycles"]} == {
        "13": "end-of-life",
        "17": "supported",
    }


def test_advisories_are_summarized_version_specific_first():
    from collectors.osv.collector import parse_vulns

    in_range = {
        "id": "GHSA-in-range",
        "aliases": ["CVE-2026-0001"],
        "affected": [
            {
                "package": {"name": "django", "ecosystem": "PyPI"},
                "ranges": [
                    {"type": "ECOSYSTEM", "events": [{"introduced": "4.2"}, {"fixed": "4.2.20"}]}
                ],
            }
        ],
    }
    no_ranges = {
        "id": "GHSA-old",
        "aliases": ["CVE-2012-0002"],
        "affected": [{"package": {"name": "django", "ecosystem": "PyPI"}}],
    }
    osv = parse_vulns("django", "PyPI", {"vulns": [in_range, no_ranges]})
    bundle = {"endoflife": [], "github_meta": [], "osv": osv}
    out = dependency_status(
        package="django",
        version="4.2.11",
        ecosystem="PyPI",
        lookups=Lookups(fetch=lambda _slug: bundle),
    )
    adv = out["advisories"]
    assert [a["id"] for a in adv["affecting_this_version"]] == ["CVE-2026-0001"]
    assert adv["affecting_this_version"][0]["url"] == (
        "https://osv.dev/vulnerability/CVE-2026-0001"
    )
    assert adv["package_level_unconfirmed_count"] == 1
    assert all(c["type"] != "SECURITY" for c in out["causes"])


def test_long_reasons_are_shortened():
    from core.agent_tools import _short

    assert _short("a; b; c") == "a; b; c"
    assert _short("a; b; c; d; e") == "a; b; c; ... (+2 more)"


def test_verdict_carries_closed_vocabulary_meaning():
    """R-B6: an agent can decide from structured fields, never from prose."""
    out = dependency_status(image="docker.io/postgres:13", lookups=_lookups(), today=TODAY)
    meaning = out["verdict"]["meaning"]
    assert meaning["direct_scope"] == "member"
    assert meaning["security_consequence"] == "not_evaluated"
    assert all(c["direct_scope"] == "member" for c in out["causes"] if c["affected"])
    assert "NOT_AFFECTED means outside" in out["note"]


def test_package_identity_follows_the_ecosystem():
    """F1: PyPI redis is redis-py, not the Redis server, in the agent view too."""
    calls = []
    out = dependency_status(
        package="redis", version="6.2.0", ecosystem="PyPI", lookups=_lookups(calls), today=TODAY
    )
    assert out["identity"]["project"] == "redis-py"
    assert calls == ["redis-py"]

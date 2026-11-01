"""Agent tools (core/agent_tools.py) - the MCP server's SDK-free engine."""

import json
from datetime import date, datetime, timezone

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


# --- Freshness bound (TR-2026-01 N4; review 11, point 3.3) -------------------

_STALE_AS_OF = datetime(2027, 6, 1, tzinfo=timezone.utc)  # curated evidence: 2026-09


def test_current_mode_is_the_default_and_bounds_evidence_age():
    out = dependency_status(
        package="django", version="5.0", ecosystem="PyPI", live=False, today=TODAY
    )
    assert out["evaluation_context"] == {
        "mode": "current",
        "as_of": "2026-10-24T00:00:00Z",
        "max_evidence_age_days": agent_tools.DEFAULT_MAX_EVIDENCE_AGE_DAYS,
        "freshness_bound_applied": True,
        "unresolved_identity": "undetermined",
    }
    assert out["verdict"]["relationship"] == "NOT_AFFECTED"  # 2026-09 evidence is fresh
    assert out["note"] == agent_tools.NOTE


def test_stale_curated_event_cannot_clear_in_current_mode():
    out = dependency_status(
        package="django", version="5.0", ecosystem="PyPI", live=False, as_of=_STALE_AS_OF
    )
    assert out["verdict"]["relationship"] == "RELATED"
    assert out["verdict"]["affected"] is False
    assert out["verdict"]["meaning"]["direct_scope"] == "undetermined"
    assert "stale" in out["causes"][0]["reason"]
    assert out["evaluation_context"]["as_of"] == "2027-06-01T00:00:00Z"


def test_stale_lifecycle_event_cannot_clear_in_current_mode():
    """The live path too: a cached EOL observation ages out of clearing."""
    out = dependency_status(
        image="docker.io/postgres:17", lookups=_lookups(), today=TODAY, as_of=_STALE_AS_OF
    )
    assert out["verdict"]["relationship"] != "NOT_AFFECTED"
    assert any("freshness bound" in c["reason"] for c in out["causes"])


def test_bound_is_configurable():
    out = dependency_status(
        package="django",
        version="5.0",
        ecosystem="PyPI",
        live=False,
        today=TODAY,
        max_evidence_age_days=7,
    )
    assert out["evaluation_context"]["max_evidence_age_days"] == 7
    assert out["verdict"]["relationship"] == "RELATED"


def test_replay_mode_disables_the_bound_and_says_so():
    out = dependency_status(
        package="django",
        version="5.0",
        ecosystem="PyPI",
        live=False,
        as_of=_STALE_AS_OF,
        mode="replay",
    )
    assert out["verdict"]["relationship"] == "NOT_AFFECTED"  # as before the bound existed
    assert out["evaluation_context"] == {
        "mode": "replay",
        "as_of": None,
        "max_evidence_age_days": None,
        "freshness_bound_applied": False,
        "unresolved_identity": "undetermined",
    }
    assert "NO FRESHNESS BOUND" in out["note"]
    assert any(u.startswith("evidence currency") for u in out["not_established"])


def test_replay_mode_matches_the_unbounded_engine():
    from core.risk.check import check_dependency

    dep = {"kind": "image", "ref": "docker.io/postgres:17"}
    out = dependency_status(image=dep["ref"], lookups=_lookups(), today=TODAY, mode="replay")
    events = agent_tools.curated_events() + agent_tools.lifecycle_events(
        "postgresql", _PG, today=TODAY
    )
    engine = check_dependency(dep, events, {"postgresql": _PG})
    assert out["verdict"]["relationship"] == engine.relationship == "NOT_AFFECTED"


def test_unknown_mode_is_refused():
    with pytest.raises(ValueError, match="mode must be one of"):
        dependency_status(
            package="django", version="5.0", ecosystem="PyPI", live=False, mode="lenient"
        )


def test_causes_carry_scope_completeness():
    out = dependency_status(package="django", version="4.2", ecosystem="PyPI", live=False)
    completeness = out["causes"][0]["scope_completeness"]
    assert set(completeness) == {"state", "basis", "admits_negative"}
    assert isinstance(completeness["admits_negative"], bool)


def test_file_check_carries_evaluation_context():
    out = check_dependency_file("data/fixtures/manifests/requirements.txt", live=False, today=TODAY)
    assert out["evaluation_context"]["freshness_bound_applied"] is True
    replay = check_dependency_file(
        "data/fixtures/manifests/requirements.txt", live=False, mode="replay"
    )
    assert replay["evaluation_context"]["freshness_bound_applied"] is False
    assert "NO FRESHNESS BOUND" in replay["note"]
    assert all("evaluation_context" in r for r in replay["results"])


# ---------------------------------------------------------------------------
# W4 (v0.11.0, C5): lookup budget, stated limits, cross-session cache
# ---------------------------------------------------------------------------


def _budget_lookups(budget, calls=None, **kwargs):
    lookups = _lookups(calls)
    return Lookups(fetch=lookups._fetch, budget=budget, **kwargs)


def test_every_answer_carries_the_lookup_status():
    lookups = _budget_lookups(5)
    out = dependency_status(image="docker.io/postgres:13", lookups=lookups, today=TODAY)
    assert out["lookups"] == {
        "budget": 5,
        "used": 1,
        "remaining": 4,
        "timeout_seconds_per_source": agent_tools.LOOKUP_TIMEOUT_SECONDS,
        "cache_ttl_seconds": 3600,
    }
    again = dependency_status(image="docker.io/postgres:14", lookups=lookups, today=TODAY)
    assert again["lookups"]["used"] == 1  # a cache hit spends nothing


def test_a_spent_budget_is_stated_never_silent():
    calls = []
    lookups = _budget_lookups(1, calls)
    dependency_status(image="docker.io/postgres:13", lookups=lookups, today=TODAY)
    out = dependency_status(
        package="django", version="4.2", ecosystem="PyPI", lookups=lookups, today=TODAY
    )
    assert calls == ["postgresql"]  # no fetch past the budget
    assert {"source": "live lookups", "status": "budget-exhausted"}.items() <= next(
        s for s in out["sources"] if s["source"] == "live lookups"
    ).items()
    assert any("budget spent" in u for u in out["not_established"])
    assert out["lookups"]["remaining"] == 0
    # The curated django event still answers: the budget limits lookups, not the engine.
    assert out["verdict"]["affected"] is True


def test_the_per_file_cap_names_the_projects_it_skipped(monkeypatch):
    monkeypatch.setattr(agent_tools, "MAX_LIVE_PROJECTS", 1)
    out = check_dependency_file(
        "data/fixtures/lockfiles/poetry.lock", lookups=_lookups([]), today=TODAY
    )
    assert out["live_projects_looked_up"] == 1
    assert out["live_lookups_capped"]
    assert out["lookups"]["used"] == 1


def test_project_lifecycle_refuses_past_the_budget():
    lookups = _budget_lookups(0)
    with pytest.raises(agent_tools.BudgetExhausted, match="budget spent"):
        project_lifecycle("postgres", lookups=lookups, today=TODAY)


class _Clock:
    def __init__(self, now=1_800_000_000.0):
        self.now = now

    def __call__(self):
        return self.now


def test_project_lifecycle_is_cached_across_sessions(tmp_path):
    clock, calls = _Clock(), []
    first = project_lifecycle(
        "postgres", lookups=_budget_lookups(5, calls, cache_dir=tmp_path, clock=clock), today=TODAY
    )
    assert calls == ["postgresql"] and first["cached_age_seconds"] is None
    clock.now += 600
    second = project_lifecycle(
        "postgres", lookups=_budget_lookups(5, calls, cache_dir=tmp_path, clock=clock), today=TODAY
    )
    assert calls == ["postgresql"]  # a new session, no new fetch
    assert second["cached_age_seconds"] == 600
    assert second["cycles"] == first["cycles"]
    assert second["lookups"]["used"] == 0


def test_the_cache_expires_with_the_session_ttl(tmp_path):
    clock, calls = _Clock(), []
    for _ in range(2):
        project_lifecycle(
            "postgres",
            lookups=_budget_lookups(5, calls, cache_dir=tmp_path, clock=clock),
            today=TODAY,
        )
        clock.now += 3600
    assert calls == ["postgresql", "postgresql"]


def test_a_failed_lookup_is_never_cached(tmp_path):
    def down(_slug):
        return {
            "endoflife": [{"error": True, "safe_message": "timeout"}],
            "osv": [],
            "github_meta": [],
        }

    project_lifecycle("postgres", lookups=Lookups(fetch=down, cache_dir=tmp_path), today=TODAY)
    assert list(tmp_path.glob("*.json")) == []


def test_a_corrupt_or_foreign_cache_entry_is_ignored(tmp_path):
    calls = []
    (tmp_path / "postgresql.json").write_text("{not json", encoding="utf-8")
    project_lifecycle(
        "postgres", lookups=_budget_lookups(5, calls, cache_dir=tmp_path), today=TODAY
    )
    assert calls == ["postgresql"]
    entry = json.loads((tmp_path / "postgresql.json").read_text(encoding="utf-8"))
    entry["slug"] = "something-else"
    (tmp_path / "postgresql.json").write_text(json.dumps(entry), encoding="utf-8")
    project_lifecycle(
        "postgres", lookups=_budget_lookups(5, calls, cache_dir=tmp_path), today=TODAY
    )
    assert calls == ["postgresql", "postgresql"]


def test_the_cache_dir_follows_the_environment(monkeypatch, tmp_path):
    monkeypatch.setenv(agent_tools.CACHE_DIR_ENV, str(tmp_path))
    assert agent_tools.default_cache_dir() == tmp_path
    monkeypatch.setenv(agent_tools.CACHE_DIR_ENV, "")
    assert agent_tools.default_cache_dir() is None  # '' disables the cache

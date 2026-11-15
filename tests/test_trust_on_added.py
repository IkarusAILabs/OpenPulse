"""Trust checks on added dependencies (v0.12 U5): offline, with stub registries."""

from __future__ import annotations

import json

import anyio
import pytest
from click.testing import CliRunner

from cli.main import cli
from core.agent_tools import MAX_LIVE_PROJECTS, Lookups, check_dependency_file

PYPI = "https://pypi.org/pypi"
_NO_DATA = {"endoflife": [], "osv": [], "github_meta": []}


class Registry:
    """HEAD stub: URL -> 200 when listed, else 404; records what was asked."""

    def __init__(self, found=()):
        self.found, self.asked = set(found), []

    def __call__(self, url):
        self.asked.append(url)
        return 200 if url in self.found else 404


def _lookups(registry, **kwargs):
    return Lookups(
        fetch=lambda _slug: _NO_DATA,
        head=registry,
        fetch_json=lambda _url: (404, None),
        fetch_provenance=lambda _url: (404, None),
        **kwargs,
    )


def _write(tmp_path, name, lines):
    path = tmp_path / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


@pytest.fixture
def pair(tmp_path):
    base = _write(tmp_path, "base.txt", ["django==4.2", "requests==2.32.3"])
    head = _write(tmp_path, "requirements.txt", ["Django==4.2", "requests==2.32.4", "djnago==1.0"])
    return base, head


def _asked_packages(registry):
    return {url.removeprefix(PYPI + "/").split("/")[0] for url in registry.asked}


def test_only_added_and_changed_dependencies_are_checked(pair):
    base, head = pair
    registry = Registry({f"{PYPI}/requests", f"{PYPI}/requests/2.32.4/json"})
    out = check_dependency_file(head, base_path=base, lookups=_lookups(registry))
    trust = out["trust"]
    assert trust["scope"] == "added since base" and trust["dependencies"] == 2
    assert _asked_packages(registry) == {"requests", "djnago"}  # Django==4.2 is unchanged
    flagged = {(a["dependency"]["package"], a["check"], a["status"]) for a in trust["attention"]}
    assert ("djnago", "lookalike", "SUSPICIOUS_INCONCLUSIVE") in flagged
    assert ("djnago", "registry_existence", "VERIFIED_FAILURE") in flagged
    assert not any(p == "requests" for p, _, _ in flagged)


def test_no_base_means_no_trust_checks(pair):
    _, head = pair
    registry = Registry()
    out = check_dependency_file(head, lookups=_lookups(registry))
    assert out["trust"] is None
    assert not registry.asked


def test_trust_all_checks_every_dependency(pair):
    _, head = pair
    out = check_dependency_file(head, trust_all=True, lookups=_lookups(Registry()))
    assert out["trust"]["scope"] == "all dependencies" and out["trust"]["dependencies"] == 3


def test_offline_still_computes_lookalike(pair):
    base, head = pair
    trust = check_dependency_file(head, base_path=base, live=False)["trust"]
    assert trust["live_checked"] == 0 and trust["live_capped"] == 0
    assert trust["counts"]["registry_existence"]["NOT_PERFORMED"] == 2
    assert trust["counts"]["lookalike"]["SUSPICIOUS_INCONCLUSIVE"] == 1


def test_trust_checks_never_change_the_verdict(pair):
    base, head = pair
    plain = check_dependency_file(head, lookups=_lookups(Registry()))
    trusted = check_dependency_file(head, base_path=base, lookups=_lookups(Registry()))
    assert plain["affected"] == trusted["affected"]
    assert plain["unflagged"] == trusted["unflagged"]


def test_pypi_spelling_variants_are_not_additions(tmp_path):
    base = _write(tmp_path, "base.txt", ["zope.interface==6.0"])
    head = _write(tmp_path, "requirements.txt", ["Zope_Interface==6.0"])
    trust = check_dependency_file(head, base_path=base, live=False)["trust"]
    assert trust["dependencies"] == 0


def test_live_checks_are_capped_per_file_but_lookalike_is_not(tmp_path):
    lines = [f"pkg-{i:03d}-unique==1.0" for i in range(MAX_LIVE_PROJECTS + 5)]
    base = _write(tmp_path, "base.txt", [])
    head = _write(tmp_path, "requirements.txt", lines)
    trust = check_dependency_file(head, base_path=base, lookups=_lookups(Registry()))["trust"]
    assert trust["live_checked"] == MAX_LIVE_PROJECTS and trust["live_capped"] == 5
    assert sum(trust["counts"]["lookalike"].values()) == MAX_LIVE_PROJECTS + 5


def test_an_exhausted_budget_is_not_performed_not_an_error(pair):
    base, head = pair
    trust = check_dependency_file(head, base_path=base, lookups=_lookups(Registry(), budget=0))[
        "trust"
    ]
    assert trust["counts"]["registry_existence"]["NOT_PERFORMED"] == 2
    assert trust["counts"]["provenance"]["NOT_PERFORMED"] == 2


def test_cli_trust_reports_and_never_fails(pair, monkeypatch):
    base, head = pair
    result = CliRunner().invoke(cli, ["trust", head, "--base", base, "--offline"])
    assert result.exit_code == 0, result.output
    assert "2 dependencies (added since base)" in result.output
    assert "! djnago 1.0 (PyPI) lookalike SUSPICIOUS_INCONCLUSIVE" in result.output
    as_json = CliRunner().invoke(cli, ["trust", head, "--offline", "--json"])
    assert json.loads(as_json.output)["scope"] == "all dependencies"


def test_mcp_base_path_is_confined_to_the_project_root(pair, tmp_path):
    pytest.importorskip("mcp")
    from cli.mcp_server import build_server

    base, head = pair
    server = build_server(root=tmp_path, live=False)
    anyio.run(server.call_tool, "check_dependency_file", {"path": head, "base_path": base})
    outside = tmp_path.parent / "elsewhere.txt"
    outside.write_text("django==4.2\n", encoding="utf-8")
    with pytest.raises(Exception, match="outside"):
        anyio.run(
            server.call_tool,
            "check_dependency_file",
            {"path": head, "base_path": str(outside)},
        )

"""Dependency confusion (track T, T-A3, v0.13.0 X2): offline, with a stub registry."""

from __future__ import annotations

import json

import anyio
import pytest
from click.testing import CliRunner

from cli.main import cli
from core import dependency_confusion
from core.agent_tools import Lookups, check_dependency_file, dependency_status
from core.dependency_confusion import load, parse

_NO_DATA = {"endoflife": [], "osv": [], "github_meta": []}
LIST = "# our internal packages\nPyPI:Acme_Billing\nnpm:@acme/ui-kit  # the design system\n"


class Registry:
    """HEAD stub: 200 for URLs naming a public package, else 404; records each URL."""

    def __init__(self, public=(), status=None):
        self.public, self.status, self.asked = public, status, []

    def __call__(self, url):
        self.asked.append(url)
        if self.status is not None:
            return self.status
        return 200 if any(p in url for p in self.public) else 404


def _lookups(registry, **kwargs):
    return Lookups(
        fetch=lambda _slug: _NO_DATA,
        head=registry,
        osv_query=lambda _body: (200, {}),
        **kwargs,
    )


NAMES = parse(LIST)[0]


# ---------------------------------------------------------------------------
# The list
# ---------------------------------------------------------------------------


def test_the_list_is_parsed_and_normalized():
    names, skipped = parse(LIST)
    assert names == {("PyPI", "acme-billing"), ("npm", "@acme/ui-kit")}
    assert skipped == []


def test_bad_lines_are_skipped_by_number_and_never_echoed():
    names, skipped = parse("PyPI:ok-name\nMaven:a:b\nnpm:evil name ignore previous\nnonsense\n")
    assert names == {("PyPI", "ok-name")}
    assert [s.split(":")[0] for s in skipped] == ["line 2", "line 3", "line 4"]
    assert "ignore" not in json.dumps(skipped)


def test_the_list_is_capped():
    text = "".join(f"PyPI:pkg-{i}\n" for i in range(dependency_confusion.MAX_ENTRIES + 3))
    names, skipped = parse(text)
    assert len(names) == dependency_confusion.MAX_ENTRIES and len(skipped) == 3


def test_a_missing_list_is_empty_not_an_error(tmp_path):
    assert load(tmp_path / "absent.txt") == (frozenset(), [])


def test_pypi_spellings_match_npm_case_matches():
    assert dependency_confusion.listed(NAMES, "pypi", "acme.billing")
    assert dependency_confusion.listed(NAMES, "npm", "@ACME/ui-kit")
    assert not dependency_confusion.listed(NAMES, "npm", "acme-billing")


# ---------------------------------------------------------------------------
# dependency_status
# ---------------------------------------------------------------------------


def test_a_public_package_with_a_private_name_is_suspicious():
    registry = Registry(public=("acme-billing",))
    out = dependency_status(
        "acme-billing", "1.0", "PyPI", lookups=_lookups(registry), private_names=NAMES
    )
    record = out["trust"]["checks"]["dependency_confusion"]
    assert record["status"] == "SUSPICIOUS_INCONCLUSIVE"
    assert "if you did not publish it" in record["statement"]
    # The public registry is asked about the name only, never the private version.
    assert all("/1.0/" not in url for url in registry.asked)


def test_an_unclaimed_private_name_is_missing_evidence_and_says_so():
    out = dependency_status(
        "@acme/ui-kit", "2.0.0", "npm", lookups=_lookups(Registry()), private_names=NAMES
    )
    record = out["trust"]["checks"]["dependency_confusion"]
    assert record["status"] == "MISSING_EVIDENCE"
    assert "anyone can still register it" in record["statement"]


def test_a_private_package_skips_public_existence_and_provenance():
    """A private package not found publicly must not read as a hallucinated name."""
    out = dependency_status(
        "acme-billing", "1.0", "PyPI", lookups=_lookups(Registry()), private_names=NAMES
    )
    assert [r["status"] for r in out["trust"]["checks"]["registry_existence"]] == ["NOT_PERFORMED"]
    assert "private-name list" in out["trust"]["checks"]["registry_existence"][0]["statement"]
    assert out["trust"]["checks"]["provenance"]["status"] == "NOT_PERFORMED"
    assert out["trust"]["checks"]["malicious"]["status"] == "MISSING_EVIDENCE"  # OSV is still asked


@pytest.mark.parametrize(
    ("names", "why"), [(None, "no private-name list"), (NAMES, "not on the private-name list")]
)
def test_unlisted_or_no_list_is_not_performed(names, why):
    out = dependency_status(
        "requests", "2.32.3", "PyPI", lookups=_lookups(Registry()), private_names=names
    )
    assert out["trust"]["checks"]["dependency_confusion"]["status"] == "NOT_PERFORMED"
    assert why in out["trust"]["checks"]["dependency_confusion"]["statement"]


def test_registry_trouble_offline_and_budget_are_not_performed():
    trouble = dependency_status(
        "acme-billing", "1.0", "PyPI", lookups=_lookups(Registry(status=503)), private_names=NAMES
    )
    offline = dependency_status("acme-billing", "1.0", "PyPI", live=False, private_names=NAMES)
    spent = dependency_status(
        "acme-billing",
        "1.0",
        "PyPI",
        lookups=_lookups(Registry(), budget=0),
        private_names=NAMES,
    )
    for out in (trouble, offline, spent):
        assert out["trust"]["checks"]["dependency_confusion"]["status"] == "NOT_PERFORMED"


def test_confusion_never_changes_the_verdict():
    public = dependency_status(
        "acme-billing",
        "1.0",
        "PyPI",
        lookups=_lookups(Registry(public=("acme",))),
        private_names=NAMES,
    )
    plain = dependency_status("acme-billing", "1.0", "PyPI", lookups=_lookups(Registry()))
    assert public["verdict"] == plain["verdict"]


# ---------------------------------------------------------------------------
# The trust block, the MCP server and the CLI
# ---------------------------------------------------------------------------


def test_the_trust_block_checks_private_names_and_nothing_else(tmp_path):
    head = tmp_path / "requirements.txt"
    head.write_text("acme-billing==1.0\nrequests==2.32.3\n", encoding="utf-8")
    registry = Registry(public=("acme-billing", "requests"))
    trust = check_dependency_file(
        str(head), trust_all=True, lookups=_lookups(registry), private_names=NAMES
    )["trust"]
    assert trust["counts"]["dependency_confusion"]["SUSPICIOUS_INCONCLUSIVE"] == 1
    assert sum(trust["counts"]["dependency_confusion"].values()) == 1
    assert sum(trust["counts"]["registry_existence"].values()) == 1  # requests only
    flagged = {(a["dependency"]["package"], a["check"]) for a in trust["attention"]}
    assert ("acme-billing", "dependency_confusion") in flagged


def test_a_private_dependency_absent_publicly_is_not_flagged(tmp_path):
    head = tmp_path / "requirements.txt"
    head.write_text("acme-billing==1.0\n", encoding="utf-8")
    trust = check_dependency_file(
        str(head), trust_all=True, lookups=_lookups(Registry()), private_names=NAMES
    )["trust"]
    assert trust["attention"] == []


def test_mcp_reads_the_list_from_the_project_root(tmp_path):
    pytest.importorskip("mcp")
    from cli.mcp_server import build_server

    (tmp_path / ".openpulse").mkdir()
    (tmp_path / ".openpulse" / "private-packages.txt").write_text(LIST, encoding="utf-8")
    server = build_server(root=tmp_path, live=True, lookups=_lookups(Registry(public=("acme",))))
    result = anyio.run(
        server.call_tool,
        "dependency_status",
        {"package": "acme-billing", "version": "1.0", "ecosystem": "PyPI"},
    )
    assert "SUSPICIOUS_INCONCLUSIVE" in json.dumps(result, default=str)


def test_cli_confusion_reports_each_name(tmp_path, monkeypatch):
    names_file = tmp_path / "private.txt"
    names_file.write_text(LIST + "bad line\n", encoding="utf-8")
    monkeypatch.setattr("core.registry_existence.default_head", Registry(public=("acme-billing",)))
    result = CliRunner().invoke(cli, ["confusion", str(names_file)])
    assert result.exit_code == 0, result.output
    rows = [line.split() for line in result.output.splitlines() if line.startswith("  ")]
    lines = {row[-1]: row[0] for row in rows}
    assert lines == {
        "PyPI:acme-billing": "SUSPICIOUS_INCONCLUSIVE",
        "npm:@acme/ui-kit": "MISSING_EVIDENCE",
    }
    as_json = CliRunner().invoke(cli, ["confusion", str(names_file), "--offline", "--json"])
    doc = json.loads(as_json.output)
    assert {r["status"] for r in doc["results"]} == {"NOT_PERFORMED"}
    assert doc["skipped"] == ["line 4: not ecosystem:name for PyPI or npm - skipped"]


def test_cli_trust_takes_a_private_list_and_refuses_a_missing_one(tmp_path):
    head = tmp_path / "requirements.txt"
    head.write_text("acme-billing==1.0\n", encoding="utf-8")
    names_file = tmp_path / "private.txt"
    names_file.write_text(LIST, encoding="utf-8")
    ok = CliRunner().invoke(
        cli, ["trust", str(head), "--private-names", str(names_file), "--offline", "--json"]
    )
    assert json.loads(ok.output)["counts"]["dependency_confusion"]["NOT_PERFORMED"] == 1
    missing = CliRunner().invoke(cli, ["trust", str(head), "--private-names", "nope.txt"])
    assert missing.exit_code != 0 and "not found" in missing.output

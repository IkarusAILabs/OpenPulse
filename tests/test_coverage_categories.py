"""No all-clear over PARTIAL coverage (v0.18.0 item S4): the categories of
what was not inspected, named in every summary that can read as clear."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from cli.main import cli
from core import coverage, github_reader
from core.sarif import build_sarif, render_summary
from tests.test_check import _patch_inspection

# Each reason template github_reader writes, as it writes it.
TEMPLATES = {
    "repository tree truncated by GitHub": "truncated tree",
    f"yarn.lock: {github_reader.UNSUPPORTED_REASON}": "unsupported dependency files",
    f"web/package.json: {github_reader.UNSUPPORTED_REASON} (no package-lock.json beside it)": (
        "unsupported dependency files"
    ),
    "requirements.txt: includes deps/prod.txt (-r/-c), which was not inspected; "
    "its dependencies were not inspected": "requirements includes not inspected",
    "requirements.txt: includes a requirements file outside the repository (-r/-c); "
    "its dependencies were not inspected": "requirements includes not inspected",
    f"poetry.lock: 9 bytes exceeds {github_reader.MAX_BLOB_BYTES}-byte inspection limit": (
        "files over the size limit"
    ),
    f"x.lock: repository size cap ({github_reader.MAX_DISCOVERED_BYTES} bytes) reached; "
    "remaining dependency files not inspected": "repository size cap reached",
    f"file cap ({github_reader.MAX_FILES}) reached; remaining dependency files not inspected": (
        "file-count cap reached"
    ),
    "a/../b: rejected unsafe repository path": "unsafe paths",
    "poetry.lock: blob sha mismatch": coverage.UNREADABLE,
    "sbom.json: not a valid CycloneDX or SPDX SBOM: bad": coverage.UNREADABLE,
}


@pytest.mark.parametrize(("reason", "expected"), sorted(TEMPLATES.items()))
def test_every_reader_template_has_its_category(reason, expected):
    assert coverage.category(reason) == expected


def test_the_templates_above_are_the_reader_s(monkeypatch):
    """Drive the reader into each discovery template, so a reworded one fails here."""
    paths = [
        ("yarn.lock", 10),
        ("web/package.json", 10),
        ("big/poetry.lock", github_reader.MAX_BLOB_BYTES + 1),
        ("requirements.txt", 20),
    ]
    tree = [
        {"type": "blob", "path": p, "size": s, "sha": f"s{i}"} for i, (p, s) in enumerate(paths)
    ]
    tree.append({github_reader._TREE_TRUNCATED_KEY: True})
    monkeypatch.setattr(
        github_reader, "_get_repo_revision", lambda repo, token, timeout: ("main", "c" * 40)
    )
    monkeypatch.setattr(github_reader, "_get_repo_tree", lambda *a, **k: tree)
    monkeypatch.setattr(
        github_reader,
        "_get_blob_content",
        lambda repo, sha, token, timeout=30.0: ("-r deps/prod.txt\ndjango==4.2\n", None),
    )
    inspection = github_reader.inspect_github_repo("owner/repo")

    assert coverage.categories(inspection.coverage_reasons) == {
        "truncated tree": 1,
        "unsupported dependency files": 2,
        "requirements includes not inspected": 1,
        "files over the size limit": 1,
    }


def test_describe_names_each_category_with_its_count():
    reasons = list(TEMPLATES)
    line = coverage.describe("PARTIAL", reasons)
    assert line.startswith("PARTIAL - not inspected: truncated tree (1), ")
    assert "unsupported dependency files (2)" in line
    assert line.endswith(f"{coverage.UNREADABLE} (2)")
    assert coverage.describe("COMPLETE", reasons) == "COMPLETE"
    assert coverage.describe("NOT_APPLICABLE", []) == "NOT_APPLICABLE"
    assert "could not be read" in coverage.describe("FAILED", [])
    assert "not recorded" in coverage.describe("PARTIAL", [])


# ---------------------------------------------------------------------------
# Every summary that can read as clear
# ---------------------------------------------------------------------------

ARGS = [
    "--watchlist",
    "data/fixtures/watchlist_sample.yaml",
    "--github-repo",
    "owner/repo",
    "--event",
    "data/fixtures/django-eol/event.json",
    "--replay",
    "--ledger",
    "",
]


def test_check_never_ends_on_a_bare_count_over_partial_coverage(monkeypatch):
    _patch_inspection(monkeypatch, "PARTIAL")
    out = CliRunner().invoke(cli, ["check", *ARGS])
    assert out.exit_code == 0, out.output
    assert "repository inspection coverage: PARTIAL - not inspected: " in out.output
    last = [line for line in out.output.splitlines() if "dependencies affected" in line][-1]
    assert last.endswith(
        "over PARTIAL repository coverage: what was not inspected was not checked (see above)"
    )


def test_check_over_complete_coverage_is_unchanged(monkeypatch):
    _patch_inspection(monkeypatch, "COMPLETE")
    out = CliRunner().invoke(cli, ["check", *ARGS])
    last = [line for line in out.output.splitlines() if "dependencies affected" in line][-1]
    assert last.endswith("dependencies affected")


def test_sarif_and_the_job_summary_name_the_categories():
    reasons = [
        f"yarn.lock: {github_reader.UNSUPPORTED_REASON}",
        "repository tree truncated by GitHub",
    ]
    log = build_sarif([], tool_version="0", coverage={"status": "PARTIAL", "reasons": reasons})
    props = log["runs"][0]["properties"]
    assert props["inspection_coverage_categories"] == {
        "truncated tree": 1,
        "unsupported dependency files": 1,
    }
    note = log["runs"][0]["invocations"][0]["toolExecutionNotifications"][0]["message"]["text"]
    assert note.startswith(
        "repository inspection coverage PARTIAL - not inspected: truncated tree (1), "
        "unsupported dependency files (1). Details: "
    )
    summary = render_summary(log)
    assert (
        "- Repository inspection coverage: **PARTIAL** - not inspected: truncated tree (1), "
        "unsupported dependency files (1)"
    ) in summary


def test_sarif_over_complete_or_no_repository_has_no_categories():
    for status in ("COMPLETE", "NOT_APPLICABLE"):
        log = build_sarif([], tool_version="0", coverage={"status": status, "reasons": []})
        assert log["runs"][0]["properties"]["inspection_coverage_categories"] == {}
        summary = render_summary(log)
        assert f"- Repository inspection coverage: **{status}**" in summary
        assert "not inspected" not in summary

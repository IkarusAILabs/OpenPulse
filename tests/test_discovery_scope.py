"""What a repository inspection searched (v0.18.0 item S3): the scope in
``RepoInspection``, in evidence contract 2.4.0 and in the CLI output."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from cli.main import cli
from core import github_reader
from core.evidence_contract import (
    SCHEMA_V2_3_PATH,
    SCHEMA_V2_4_PATH,
    build_contract,
    load_v2_3_schema,
    validate_contract,
    validate_v1_contract,
    verify_content_hash,
)
from core.github_reader import COVERAGE_COMPLETE, COVERAGE_PARTIAL, inspect_github_repo
from core.risk.check import check_dependency
from core.schema.models import OSSEvent


def _inspect(monkeypatch, tree, blobs, truncated=False):
    entries = [
        {"type": "blob", "path": p, "size": size, "sha": f"sha-{i}"}
        for i, (p, size) in enumerate(tree)
    ]
    if truncated:
        entries.append({github_reader._TREE_TRUNCATED_KEY: True})
    monkeypatch.setattr(
        github_reader, "_get_repo_revision", lambda repo, token, timeout: ("main", "c" * 40)
    )
    monkeypatch.setattr(
        github_reader, "_get_repo_tree", lambda repo, token, revision, timeout=30.0: entries
    )
    by_sha = {f"sha-{i}": blobs[p] for i, (p, _s) in enumerate(tree) if p in blobs}
    monkeypatch.setattr(
        github_reader,
        "_get_blob_content",
        lambda repo, sha, token, timeout=30.0: (
            (by_sha[sha], None) if sha in by_sha else (None, {"safe_message": "fetch failed"})
        ),
    )
    return inspect_github_repo("owner/repo")


# ---------------------------------------------------------------------------
# The scope
# ---------------------------------------------------------------------------


def test_the_scope_names_ref_commit_patterns_and_counts(monkeypatch):
    inspection = _inspect(
        monkeypatch,
        [
            ("requirements.txt", 20),
            ("web/package-lock.json", 40),
            ("node_modules/a/package.json", 10),
            ("node_modules/b/package.json", 10),
            ("vendor/x/go.mod", 10),
            ("README.md", 10),
        ],
        {
            "requirements.txt": "django==4.2\n",
            "web/package-lock.json": '{"lockfileVersion": 3, "packages": {}}',
        },
    )

    scope = inspection.scope
    assert inspection.coverage == COVERAGE_COMPLETE
    assert (scope["repository"], scope["ref"], scope["commit"]) == ("owner/repo", "main", "c" * 40)
    assert "requirements.txt" in scope["file_patterns"]
    assert "requirements*.txt" in scope["file_patterns"]
    assert "yarn.lock" in scope["recognised_not_read"]
    assert scope["skipped_directories"] == [
        {"directory": "node_modules", "files": 2},
        {"directory": "vendor", "files": 1},
    ]
    assert scope["tree_entries"] == 6
    assert (scope["files_found"], scope["files_read"]) == (2, 2)
    assert scope["limits_reached"] == []
    assert scope["limits"]["max_files"] == github_reader.MAX_FILES


def test_the_limits_that_applied_are_named(monkeypatch):
    big = github_reader.MAX_BLOB_BYTES + 1
    inspection = _inspect(
        monkeypatch,
        [("requirements.txt", 20), ("poetry.lock", big)],
        {"requirements.txt": "django==4.2\n"},
        truncated=True,
    )

    assert inspection.coverage == COVERAGE_PARTIAL
    assert inspection.scope["limits_reached"] == ["tree_truncated", "max_file_bytes"]
    assert (inspection.scope["files_found"], inspection.scope["files_read"]) == (1, 1)


def test_a_file_that_could_not_be_read_is_found_but_not_read(monkeypatch):
    inspection = _inspect(
        monkeypatch,
        [("requirements.txt", 20), ("poetry.lock", 20)],
        {"requirements.txt": "django==4.2\n"},
    )

    assert inspection.coverage == COVERAGE_PARTIAL
    assert (inspection.scope["files_found"], inspection.scope["files_read"]) == (2, 1)


def test_unusual_directory_names_are_counted_not_named(monkeypatch):
    tree = [("requirements.txt", 20), ("vendor/a.txt", 1), ("node_modules/<script>/x.json", 1)]
    tree += [(f".d{i}/f", 1) for i in range(60)]
    inspection = _inspect(monkeypatch, tree, {"requirements.txt": "django==4.2\n"})

    skipped = inspection.scope["skipped_directories"]
    assert len(skipped) == github_reader.MAX_SCOPE_DIRS + 1
    assert skipped[-1]["directory"] is None
    assert sum(d["files"] for d in skipped) == 62
    assert all("<" not in (d["directory"] or "") for d in skipped)


def test_no_scope_when_the_repository_could_not_be_enumerated(monkeypatch):
    monkeypatch.setattr(
        github_reader,
        "_get_repo_revision",
        lambda repo, token, timeout: [{"error": True, "safe_message": "not found"}],
    )
    assert inspect_github_repo("owner/repo").scope is None


def test_an_empty_repository_still_says_what_was_searched(monkeypatch):
    inspection = _inspect(monkeypatch, [("README.md", 10)], {})

    assert inspection.coverage == COVERAGE_COMPLETE
    assert inspection.scope["files_found"] == 0 and inspection.scope["tree_entries"] == 1


# ---------------------------------------------------------------------------
# Evidence contract 2.4.0
# ---------------------------------------------------------------------------


@pytest.fixture
def event():
    return OSSEvent.model_validate(
        json.loads(open("data/fixtures/django-eol/event.json", encoding="utf-8").read())
    )


def _doc(event, scope):
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    return build_contract(
        event,
        check_dependency(dep, [event]),
        inspection_coverage={"status": "COMPLETE", "reasons": []},
        inspection_scope=scope,
    )


def test_a_2_4_document_carries_the_scope_and_validates(monkeypatch, event):
    inspection = _inspect(
        monkeypatch,
        [("requirements.txt", 20), ("node_modules/x/package.json", 1)],
        {"requirements.txt": "django==4.2\n"},
    )
    doc = _doc(event, inspection.scope)

    assert doc["contract_version"] == "2.4.0"
    assert doc["inspection_coverage"]["scope"] == inspection.scope
    assert validate_contract(doc) == [] and verify_content_hash(doc)


def test_the_scope_is_strictly_shaped(event):
    for scope in ({"repository": "owner/repo"}, {"anything": 1}, "everything"):
        doc = _doc(event, None)
        doc["inspection_coverage"]["scope"] = scope
        errors = validate_contract(doc)
        assert any(e.startswith("$.inspection_coverage.scope:") for e in errors), errors


def test_a_2_3_consumer_rejects_the_scope(event):
    doc = _doc(event, None)
    doc["contract_version"] = doc["provenance"]["contract_version"] = "2.3.0"
    errors = validate_v1_contract(doc, load_v2_3_schema())
    assert any("unexpected property `scope`" in e for e in errors)


def test_the_2_4_schema_is_2_3_plus_the_scope():
    v23 = json.loads(SCHEMA_V2_3_PATH.read_text(encoding="utf-8"))
    v24 = json.loads(SCHEMA_V2_4_PATH.read_text(encoding="utf-8"))
    coverage = v24["properties"]["inspection_coverage"]
    coverage["properties"].pop("scope")
    coverage["required"].remove("scope")
    coverage["description"] = v23["properties"]["inspection_coverage"]["description"]
    for schema in (v23, v24):
        for key in ("$id", "title", "description"):
            schema.pop(key)
    assert json.dumps(v24).replace("2.4.0", "2.3.0") == json.dumps(v23)


# ---------------------------------------------------------------------------
# The CLI
# ---------------------------------------------------------------------------


def _fake_repo(monkeypatch):
    def fake(repo_spec, cli_token=None, timeout=30.0):
        return github_reader.RepoInspection(
            dependencies=[
                {
                    "kind": "package",
                    "package": "django",
                    "ecosystem": "PyPI",
                    "version": "4.2",
                    "path": "requirements.txt",
                    "inspection_coverage": COVERAGE_COMPLETE,
                    "inspection_coverage_reasons": [],
                }
            ],
            coverage=COVERAGE_COMPLETE,
            branch="main",
            commit="c" * 40,
            scope={
                "repository": "owner/repo",
                "ref": "main",
                "commit": "c" * 40,
                "file_patterns": ["requirements.txt"],
                "recognised_not_read": ["yarn.lock"],
                "skipped_directories": [{"directory": "node_modules", "files": 7}],
                "tree_entries": 42,
                "limits": {
                    "max_tree_entries": 20000,
                    "max_files": 200,
                    "max_file_bytes": 1,
                    "max_total_bytes": 2,
                },
                "limits_reached": [],
                "files_found": 1,
                "files_read": 1,
            },
        )

    monkeypatch.setattr(github_reader, "inspect_github_repo", fake)


def test_attest_puts_the_scope_on_every_contract(monkeypatch):
    _fake_repo(monkeypatch)
    out = CliRunner().invoke(
        cli,
        [
            "attest",
            "--github-repo",
            "owner/repo",
            "--event",
            "data/fixtures/django-eol/event.json",
            "--replay",
        ],
    )
    assert out.exit_code == 0, out.output
    docs = [json.loads(ln) for ln in out.output.splitlines() if ln.startswith("{")]
    assert docs and all(d["inspection_coverage"]["scope"]["tree_entries"] == 42 for d in docs)
    assert all(validate_contract(d) == [] for d in docs)
    assert "searched owner/repo main@cccccccccccc: 1/1 dependency file(s) read" in out.output
    assert "skipped directories: node_modules (7)" in out.output


def test_check_says_what_was_searched(monkeypatch):
    _fake_repo(monkeypatch)
    out = CliRunner().invoke(
        cli,
        [
            "check",
            "--github-repo",
            "owner/repo",
            "--event",
            "data/fixtures/django-eol/event.json",
            "--replay",
        ],
    )
    assert out.exit_code == 0, out.output
    assert "from 42 tree entries; skipped directories: node_modules (7); limits reached: none" in (
        out.output
    )

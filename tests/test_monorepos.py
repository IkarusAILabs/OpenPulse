"""Monorepos and nested workspaces (v0.18.0 item S5).

Each layout is a real-world shape. The rule from the phase's exit: every
member is found and read, or listed as not inspected. Coverage is never
COMPLETE over a member nobody read, and never PARTIAL over one that was.
"""

from __future__ import annotations

import json

from core import github_reader
from core.github_reader import COVERAGE_COMPLETE, COVERAGE_PARTIAL, inspect_github_repo


def _inspect(monkeypatch, files: dict[str, str]):
    paths = list(files)
    tree = [
        {"type": "blob", "path": p, "size": len(files[p]) or 1, "sha": f"sha-{i}"}
        for i, p in enumerate(paths)
    ]
    by_sha = {f"sha-{i}": files[p] for i, p in enumerate(paths)}
    monkeypatch.setattr(
        github_reader, "_get_repo_revision", lambda repo, token, timeout: ("main", "c" * 40)
    )
    monkeypatch.setattr(github_reader, "_get_repo_tree", lambda *a, **k: tree)
    monkeypatch.setattr(
        github_reader,
        "_get_blob_content",
        lambda repo, sha, token, timeout=30.0: (by_sha[sha], None),
    )
    return inspect_github_repo("owner/repo")


def _found(inspection):
    return sorted({(d["package"], d.get("version"), d["path"]) for d in inspection.dependencies})


# ---------------------------------------------------------------------------
# npm workspaces
# ---------------------------------------------------------------------------

NPM_LOCK = json.dumps(
    {
        "lockfileVersion": 3,
        "packages": {
            "": {"workspaces": ["packages/*"]},
            "packages/api": {"name": "api", "version": "1.0.0"},
            "packages/web": {"name": "web", "version": "1.0.0"},
            "node_modules/api": {"resolved": "packages/api", "link": True},
            "node_modules/express": {"version": "4.19.2"},
            "node_modules/react": {"version": "18.3.1"},
        },
    }
)


def test_npm_workspace_members_are_read_through_the_root_lockfile(monkeypatch):
    inspection = _inspect(
        monkeypatch,
        {
            "package.json": '{"workspaces": ["packages/*"]}',
            "package-lock.json": NPM_LOCK,
            "packages/api/package.json": '{"dependencies": {"express": "^4"}}',
            "packages/web/package.json": '{"dependencies": {"react": "^18"}}',
        },
    )

    assert inspection.coverage == COVERAGE_COMPLETE, inspection.coverage_reasons
    assert ("express", "4.19.2", "package-lock.json") in _found(inspection)
    assert ("react", "18.3.1", "package-lock.json") in _found(inspection)


def test_a_package_json_the_lockfile_does_not_list_is_not_inspected(monkeypatch):
    inspection = _inspect(
        monkeypatch,
        {
            "package.json": "{}",
            "package-lock.json": NPM_LOCK,
            "tools/script/package.json": '{"dependencies": {"left-pad": "^1"}}',
        },
    )

    assert inspection.coverage == COVERAGE_PARTIAL
    assert inspection.coverage_reasons == [
        "tools/script/package.json: dependency file not supported; its dependencies were not "
        "inspected (no package-lock.json beside it)"
    ]


def test_pnpm_workspaces_are_listed_as_not_inspected(monkeypatch):
    inspection = _inspect(
        monkeypatch,
        {
            "pnpm-workspace.yaml": "packages: ['packages/*']\n",
            "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
            "package.json": "{}",
            "packages/api/package.json": "{}",
        },
    )

    assert inspection.coverage == COVERAGE_PARTIAL
    for path in ("pnpm-lock.yaml", "package.json", "packages/api/package.json"):
        assert any(
            r.startswith(f"{path}: dependency file not supported")
            for r in (inspection.coverage_reasons)
        ), path


# ---------------------------------------------------------------------------
# Members under packages/ (the conventional monorepo directory)
# ---------------------------------------------------------------------------


def test_members_under_packages_are_searched(monkeypatch):
    inspection = _inspect(
        monkeypatch,
        {
            "packages/api/pyproject.toml": (
                '[project]\nname = "api"\ndependencies = ["fastapi==0.111.0"]\n'
            ),
            "packages/worker/go.mod": (
                "module example.com/worker\n\ngo 1.22\n\nrequire github.com/google/uuid v1.6.0\n"
            ),
        },
    )

    assert inspection.coverage == COVERAGE_COMPLETE, inspection.coverage_reasons
    assert [p for _n, _v, p in _found(inspection)] == [
        "packages/api/pyproject.toml",
        "packages/worker/go.mod",
    ]
    assert not any(d["directory"] == "packages" for d in inspection.scope["skipped_directories"])


# ---------------------------------------------------------------------------
# Cargo workspaces
# ---------------------------------------------------------------------------

CARGO_LOCK = (
    "version = 3\n\n"
    '[[package]]\nname = "serde"\nversion = "1.0.200"\n'
    'source = "registry+https://github.com/rust-lang/crates.io-index"\n\n'
    '[[package]]\nname = "core"\nversion = "0.1.0"\n'
)


def test_a_cargo_workspace_root_and_its_members_are_read(monkeypatch):
    inspection = _inspect(
        monkeypatch,
        {
            "Cargo.toml": '[workspace]\nmembers = ["crates/*"]\n\n'
            '[workspace.dependencies]\nserde = "=1.0.200"\n',
            "Cargo.lock": CARGO_LOCK,
            "crates/core/Cargo.toml": '[package]\nname = "core"\nversion = "0.1.0"\n\n'
            "[dependencies]\nserde = { workspace = true }\n",
        },
    )

    assert inspection.coverage == COVERAGE_COMPLETE, inspection.coverage_reasons
    assert inspection.scope["files_read"] == 3  # the virtual root is read, not refused
    assert ("serde", "1.0.200") in [(n, v) for n, v, _p in _found(inspection)]


# ---------------------------------------------------------------------------
# Python projects in subdirectories
# ---------------------------------------------------------------------------


def test_poetry_projects_in_subdirectories_are_read(monkeypatch):
    lock = '[[package]]\nname = "django"\nversion = "4.2"\n\n[metadata]\nlock-version = "2.1"\n'
    inspection = _inspect(
        monkeypatch,
        {
            "services/api/pyproject.toml": '[tool.poetry]\nname = "api"\n\n'
            '[tool.poetry.dependencies]\npython = "^3.11"\ndjango = "4.2"\n',
            "services/api/poetry.lock": lock,
        },
    )

    assert inspection.coverage == COVERAGE_COMPLETE, inspection.coverage_reasons
    # Both files read; the dependency is reported once (deduplicated by identity).
    assert inspection.scope["files_read"] == 2
    assert [(n, v) for n, v, _p in _found(inspection)] == [("django", "4.2")]


def test_uv_projects_in_subdirectories_are_listed_as_not_inspected(monkeypatch):
    inspection = _inspect(
        monkeypatch,
        {
            "services/api/pyproject.toml": '[project]\nname = "api"\ndependencies = []\n',
            "services/api/uv.lock": "version = 1\n",
        },
    )

    assert inspection.coverage == COVERAGE_PARTIAL
    assert any(
        r.startswith("services/api/uv.lock: dependency file not supported")
        for r in (inspection.coverage_reasons)
    )


# ---------------------------------------------------------------------------
# Go multi-module repositories
# ---------------------------------------------------------------------------


def test_every_go_module_is_read(monkeypatch):
    inspection = _inspect(
        monkeypatch,
        {
            "go.work": "go 1.22\n\nuse (\n\t./api\n\t./cli\n)\n",
            "api/go.mod": "module example.com/api\n\ngo 1.22\n\n"
            "require github.com/gorilla/mux v1.8.1\n",
            "cli/go.mod": "module example.com/cli\n\ngo 1.22\n\n"
            "require github.com/spf13/cobra v1.8.0\n",
        },
    )

    assert inspection.coverage == COVERAGE_COMPLETE, inspection.coverage_reasons
    assert {p for _n, _v, p in _found(inspection)} == {"api/go.mod", "cli/go.mod"}


# ---------------------------------------------------------------------------
# Maven multi-module builds
# ---------------------------------------------------------------------------

POM = (
    '<project xmlns="http://maven.apache.org/POM/4.0.0">'
    "<modelVersion>4.0.0</modelVersion>{body}</project>"
)


def test_maven_modules_are_read_and_inherited_versions_are_not_guessed(monkeypatch):
    parent = POM.format(
        body="<groupId>g</groupId><artifactId>parent</artifactId><version>1</version>"
        "<packaging>pom</packaging><modules><module>core</module></modules>"
        "<dependencyManagement><dependencies><dependency><groupId>com.google.guava</groupId>"
        "<artifactId>guava</artifactId><version>33.2.0-jre</version></dependency>"
        "</dependencies></dependencyManagement>"
    )
    module = POM.format(
        body="<parent><groupId>g</groupId><artifactId>parent</artifactId><version>1</version>"
        "</parent><artifactId>core</artifactId><dependencies>"
        "<dependency><groupId>com.google.guava</groupId><artifactId>guava</artifactId>"
        "</dependency><dependency><groupId>org.slf4j</groupId><artifactId>slf4j-api</artifactId>"
        "<version>2.0.13</version></dependency></dependencies>"
    )
    inspection = _inspect(monkeypatch, {"pom.xml": parent, "core/pom.xml": module})

    assert inspection.coverage == COVERAGE_COMPLETE, inspection.coverage_reasons
    found = _found(inspection)
    assert any(n.endswith("slf4j-api") and v == "2.0.13" for n, v, _p in found)
    # guava's version lives in the parent: recorded as skipped, never guessed.
    assert not any(n.endswith("guava") and v and v != "33.2.0-jre" for n, v, _p in found)
    assert any("core/pom.xml" in s and "guava" in s for s in inspection.skipped)


# ---------------------------------------------------------------------------
# Edges
# ---------------------------------------------------------------------------


def test_a_nuget_restore_folder_under_packages_is_still_skipped(monkeypatch):
    inspection = _inspect(
        monkeypatch,
        {
            "packages/api/package-lock.json": NPM_LOCK,
            "packages/Newtonsoft.Json.13.0.1/content/package.json": "{}",
        },
    )

    assert inspection.coverage == COVERAGE_COMPLETE, inspection.coverage_reasons
    assert {"directory": "packages-nuget-restore", "files": 1} in inspection.scope[
        "skipped_directories"
    ]


def test_a_workspace_below_the_repository_root(monkeypatch):
    inspection = _inspect(
        monkeypatch,
        {
            "apps/site/package-lock.json": NPM_LOCK,
            "apps/site/packages/api/package.json": "{}",
            "apps/site/packages/web/package.json": "{}",
            "apps/other/package.json": "{}",
        },
    )

    assert inspection.coverage == COVERAGE_PARTIAL
    assert [r.split(":")[0] for r in inspection.coverage_reasons] == ["apps/other/package.json"]


def test_an_unreadable_lockfile_covers_no_member(monkeypatch):
    inspection = _inspect(
        monkeypatch,
        {"package-lock.json": "{not json", "packages/api/package.json": "{}"},
    )

    assert inspection.coverage == COVERAGE_PARTIAL
    assert any(r.startswith("packages/api/package.json:") for r in inspection.coverage_reasons)


def test_a_cargo_package_that_declares_nothing_is_still_refused():
    import pytest

    from core.manifest_reader import load_cargo_toml_doc

    deps, notes = load_cargo_toml_doc({"workspace": {"members": ["a"]}})
    assert deps == [] and notes[0].startswith("virtual workspace manifest")
    with pytest.raises(ValueError):
        load_cargo_toml_doc({"package": {"name": "x"}})
    deps, _ = load_cargo_toml_doc(
        {"workspace": {"members": ["a"], "dependencies": {"serde": "=1.0.200"}}}
    )
    assert [(d["package"], d["version"]) for d in deps] == [("serde", "1.0.200")]

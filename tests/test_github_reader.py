"""Tests for GitHub repository dependency reader."""

import pytest

from core.github_reader import (
    COVERAGE_COMPLETE,
    COVERAGE_FAILED,
    COVERAGE_PARTIAL,
    _git_blob_sha1,
    _is_dependency_file,
    _safe_repo_path,
    deduplicate_dependencies,
    get_github_token,
    inspect_github_repo,
    parse_github_repo,
    read_github_repo,
)


class TestParseGitHubRepo:
    def test_owner_repo(self):
        repo = parse_github_repo("owner/repo")
        assert repo.owner == "owner"
        assert repo.name == "repo"

    def test_https_url(self):
        repo = parse_github_repo("https://github.com/owner/repo")
        assert repo.owner == "owner"
        assert repo.name == "repo"

    def test_https_url_with_trailing_slash(self):
        repo = parse_github_repo("https://github.com/owner/repo/")
        assert repo.owner == "owner"
        assert repo.name == "repo"

    def test_git_url(self):
        repo = parse_github_repo("git@github.com:owner/repo.git")
        assert repo.owner == "owner"
        assert repo.name == "repo"

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            parse_github_repo("invalid")
        with pytest.raises(ValueError):
            parse_github_repo("owner/repo/extra")
        with pytest.raises(ValueError):
            parse_github_repo("https://gitlab.com/owner/repo")


class TestIsDependencyFile:
    def test_manifests(self):
        for fname in [
            "requirements.txt",
            "pyproject.toml",
            "pom.xml",
            "go.mod",
            "Cargo.toml",
            "composer.json",
            "build.gradle",
            "build.gradle.kts",
            "Package.swift",
            "my.csproj",
        ]:
            is_supported, ftype = _is_dependency_file(fname)
            assert is_supported is True
            assert ftype == "manifest"

    def test_lockfiles(self):
        for fname in [
            "package-lock.json",
            "poetry.lock",
            "Cargo.lock",
            "composer.lock",
            "packages.lock.json",
            "go.sum",
        ]:
            is_supported, ftype = _is_dependency_file(fname)
            assert is_supported is True
            assert ftype == "lockfile"

    def test_sboms(self):
        for fname in ["sbom.json", "cyclonedx.json", "spdx.json"]:
            is_supported, ftype = _is_dependency_file(fname)
            assert is_supported is True
            assert ftype == "sbom"

    def test_inventories(self):
        for fname in ["images.txt", "inventory.txt", "images.yaml", "inventory.yaml"]:
            is_supported, ftype = _is_dependency_file(fname)
            assert is_supported is True
            assert ftype == "inventory"

    def test_unsupported(self):
        is_supported, ftype = _is_dependency_file("random.txt")
        assert is_supported is False
        assert ftype is None


class TestDeduplicateDependencies:
    def test_deduplicate_packages(self):
        deps = [
            {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2.7"},
            {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2.7"},
            {"kind": "package", "package": "requests", "ecosystem": "PyPI", "version": "2.31.0"},
        ]
        result = deduplicate_dependencies(deps)
        assert len(result) == 2
        assert result[0]["package"] == "django"
        assert result[1]["package"] == "requests"

    def test_deduplicate_images(self):
        deps = [
            {"kind": "image", "ref": "docker.io/redis:7.2"},
            {"kind": "image", "ref": "docker.io/redis:7.2"},
            {"kind": "image", "ref": "docker.io/postgres:15"},
        ]
        result = deduplicate_dependencies(deps)
        assert len(result) == 2

    def test_merge_paths(self):
        deps = [
            {
                "kind": "package",
                "package": "django",
                "ecosystem": "PyPI",
                "version": "4.2.7",
                "path": "requirements.txt",
            },
            {
                "kind": "package",
                "package": "django",
                "ecosystem": "PyPI",
                "version": "4.2.7",
                "path": "pyproject.toml",
            },
        ]
        result = deduplicate_dependencies(deps)
        assert len(result) == 1
        paths = result[0].get("_source_paths", [])
        assert "requirements.txt" in paths
        assert "pyproject.toml" in paths


class TestGetGitHubToken:
    def test_cli_token_priority(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "env_token")
        assert get_github_token(cli_token="cli_token") == "cli_token"

    def test_env_token(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "env_token")
        monkeypatch.delenv("GH_TOKEN", raising=False)
        assert get_github_token(cli_token=None) == "env_token"

    def test_gh_token_fallback(self, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setenv("GH_TOKEN", "gh_token")
        assert get_github_token(cli_token=None) == "gh_token"

    def test_no_token(self, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)
        assert get_github_token(cli_token=None) is None


# Integration tests would require network access - using fixtures instead
# These would be in a separate test file that requires network


class TestGitHubRepositoryIntegration:
    def _patch_common(self, monkeypatch, tree, blobs):
        from core import github_reader

        monkeypatch.setattr(
            github_reader,
            "_get_repo_revision",
            lambda repo, token, timeout: ("main", "abc123"),
        )
        monkeypatch.setattr(
            github_reader,
            "_get_repo_tree",
            lambda repo, token, revision, timeout=30.0: tree,
        )
        monkeypatch.setattr(
            github_reader,
            "_get_blob_content",
            lambda repo, blob_sha, token, timeout=30.0: blobs.get(blob_sha, (None, None)),
        )

    def test_repository_revision_and_manifest_converge(self, monkeypatch):
        """Exercise the complete adapter path without network access."""
        self._patch_common(
            monkeypatch,
            tree=[
                {"type": "blob", "path": "requirements.txt", "size": 20, "sha": "file1"},
                {
                    "type": "blob",
                    "path": "packages/app/requirements.txt",
                    "size": 20,
                    "sha": "file2",
                },
                {
                    "type": "blob",
                    "path": "node_modules/x/package-lock.json",
                    "size": 10,
                    "sha": "skip",
                },
            ],
            blobs={
                "file1": ("requests==2.32.0\n", None),
                "file2": ("requests==2.32.0\n", None),
            },
        )

        deps, skipped, errors = read_github_repo("owner/repo")

        assert not errors
        assert not skipped
        assert len(deps) == 1
        assert deps[0]["package"] == "requests"
        assert deps[0]["version"] == "2.32.0"
        assert deps[0]["repository"] == "owner/repo"
        assert deps[0]["repository_branch"] == "main"
        assert deps[0]["repository_commit"] == "abc123"
        assert deps[0]["path"] in {"requirements.txt", "packages/app/requirements.txt"}
        assert deps[0]["inspection_coverage"] == COVERAGE_COMPLETE

    def test_empty_supported_files_is_distinct_from_fetch_failure(self, monkeypatch):
        self._patch_common(monkeypatch, tree=[], blobs={})

        deps, skipped, errors = read_github_repo("owner/repo")

        assert deps == []
        assert not errors
        assert "inspected successfully" in skipped[0]

    def test_tree_limit_is_reported_as_error(self, monkeypatch):
        from core import github_reader

        self._patch_common(
            monkeypatch,
            tree=[
                {"type": "blob", "path": f"f{i}.txt", "size": 1, "sha": f"s{i}"}
                for i in range(github_reader.MAX_TREE_ENTRIES + 1)
            ],
            blobs={},
        )

        deps, skipped, errors = read_github_repo("owner/repo")

        assert deps == []
        assert skipped == []
        assert errors
        assert "tree exceeds" in errors[0]["safe_message"]

    def test_head_moving_between_tree_and_fetch_still_uses_tree_sha(self, monkeypatch):
        """F1: content is fetched by the tree's blob SHA, not a mutable ref."""
        calls = []
        from core import github_reader

        monkeypatch.setattr(
            github_reader,
            "_get_repo_revision",
            lambda repo, token, timeout: ("main", "commit-at-tree"),
        )
        monkeypatch.setattr(
            github_reader,
            "_get_repo_tree",
            lambda repo, token, revision, timeout=30.0: [
                {"type": "blob", "path": "requirements.txt", "size": 20, "sha": "blob-pinned"}
            ],
        )

        def fake_blob(repo, blob_sha, token, timeout=30.0):
            calls.append(blob_sha)
            return "requests==2.32.0\n", None

        monkeypatch.setattr(github_reader, "_get_blob_content", fake_blob)

        inspection = inspect_github_repo("owner/repo")

        assert calls == ["blob-pinned"]
        assert inspection.commit == "commit-at-tree"
        assert inspection.coverage == COVERAGE_COMPLETE
        assert inspection.dependencies[0]["repository_commit"] == "commit-at-tree"

    def test_large_lockfile_is_read_not_silently_empty(self, monkeypatch):
        """F2: a 2 MB lockfile must parse, not become 'no dependencies'."""
        import json

        packages = {
            f"node_modules/pkg{i}": {
                "version": "1.0.0",
                "resolved": "https://registry.npmjs.org/x",
                "integrity": "sha512-AAAA",
            }
            for i in range(25_000)
        }
        content = json.dumps({"name": "app", "lockfileVersion": 3, "packages": packages})
        assert len(content.encode()) > 2 * 1024 * 1024

        self._patch_common(
            monkeypatch,
            tree=[
                {
                    "type": "blob",
                    "path": "package-lock.json",
                    "size": len(content),
                    "sha": "big-lock",
                }
            ],
            blobs={"big-lock": (content, None)},
        )

        inspection = inspect_github_repo("owner/repo")

        assert inspection.coverage == COVERAGE_COMPLETE
        assert len(inspection.dependencies) == 25_000

    @pytest.mark.parametrize(
        "path,fixture",
        [
            ("sbom.json", "data/fixtures/sbom/cyclonedx.json"),
            ("spdx.json", "data/fixtures/sbom/spdx.json"),
        ],
    )
    def test_repository_sboms_are_ingested(self, monkeypatch, path, fixture):
        """Regression: SBOM blobs were handed to the path readers as a dict
        (TypeError), so every repository SBOM degraded to PARTIAL."""
        from core.sbom_reader import read_sbom, read_spdx

        with open(fixture, encoding="utf-8") as f:
            content = f.read()
        expected, _ = (read_spdx if "spdx" in path else read_sbom)(fixture)
        assert expected
        self._patch_common(
            monkeypatch,
            tree=[{"type": "blob", "path": path, "size": len(content), "sha": "bom"}],
            blobs={"bom": (content, None)},
        )

        inspection = inspect_github_repo("owner/repo")

        assert inspection.coverage == COVERAGE_COMPLETE
        deps = inspection.dependencies
        got = {(d.get("package") or d.get("ref"), d.get("version")) for d in deps}
        want = {(d.get("package") or d.get("ref"), d.get("version")) for d in expected}
        assert got == want
        assert all(d["path"] == path for d in inspection.dependencies)

    def test_oversized_repository_sbom_is_partial_not_empty(self, monkeypatch):
        from core import github_reader

        monkeypatch.setattr(github_reader, "MAX_SBOM_BYTES", 10)
        content = '{"bomFormat": "CycloneDX", "specVersion": "1.5", "components": []}'
        self._patch_common(
            monkeypatch,
            tree=[{"type": "blob", "path": "sbom.json", "size": len(content), "sha": "bom"}],
            blobs={"bom": (content, None)},
        )

        inspection = inspect_github_repo("owner/repo")

        assert inspection.coverage == COVERAGE_PARTIAL
        assert any("limit" in r for r in inspection.coverage_reasons + inspection.skipped)

    def test_truncated_tree_reports_partial(self, monkeypatch):
        self._patch_common(
            monkeypatch,
            tree=[
                {"type": "blob", "path": "requirements.txt", "size": 20, "sha": "file1"},
                {"_openpulse_tree_truncated": True},
            ],
            blobs={"file1": ("requests==2.32.0\n", None)},
        )

        inspection = inspect_github_repo("owner/repo")

        assert inspection.coverage == COVERAGE_PARTIAL
        assert any("truncated" in reason for reason in inspection.coverage_reasons)
        assert inspection.dependencies[0]["inspection_coverage"] == COVERAGE_PARTIAL

    def test_fetch_failure_is_partial_not_zero_dependencies(self, monkeypatch):
        """A failed fetch must never look like a clean, empty inspection."""
        from collectors.errors import as_error

        error = as_error("github_repo", Exception("boom"), context="get_blob")
        self._patch_common(
            monkeypatch,
            tree=[
                {"type": "blob", "path": "requirements.txt", "size": 20, "sha": "file1"},
                {"type": "blob", "path": "pyproject.toml", "size": 20, "sha": "file2"},
            ],
            blobs={"file1": (None, error), "file2": ("requests==2.32.0\n", None)},
        )

        inspection = inspect_github_repo("owner/repo")

        assert inspection.coverage == COVERAGE_PARTIAL
        assert any("requirements.txt" in reason for reason in inspection.coverage_reasons)
        assert len(inspection.dependencies) == 1
        assert inspection.dependencies[0]["inspection_coverage"] == COVERAGE_PARTIAL

    def test_no_dependencies_never_returned_on_revision_failure(self, monkeypatch):
        from collectors.errors import as_error

        error = as_error("github_repo", Exception("not found"), context="get_repo_revision")
        from core import github_reader

        monkeypatch.setattr(
            github_reader,
            "_get_repo_revision",
            lambda repo, token, timeout: [error],
        )

        inspection = inspect_github_repo("owner/repo")

        assert inspection.coverage == COVERAGE_FAILED
        assert inspection.errors


class TestPathSafety:
    def test_accepts_normal_paths(self):
        assert _safe_repo_path("requirements.txt")
        assert _safe_repo_path("packages/app/requirements.txt")

    def test_rejects_traversal_and_absolute(self):
        assert not _safe_repo_path("../evil/requirements.txt")
        assert not _safe_repo_path("a/../../evil")
        assert not _safe_repo_path("/etc/passwd")
        assert not _safe_repo_path("C:/Windows/requirements.txt")
        assert not _safe_repo_path("packages\\app\\requirements.txt")


class TestGitBlobSha:
    def test_matches_git_object_id(self):
        # echo -n 'hi' | git hash-object --stdin
        assert _git_blob_sha1(b"hi\n") == "45b983be36b73c0788dc9cbcb76cbb80fc7bb057"

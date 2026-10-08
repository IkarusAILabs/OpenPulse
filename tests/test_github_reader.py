"""Tests for GitHub repository dependency reader."""

import pytest

from core.github_reader import (
    _is_dependency_file,
    deduplicate_dependencies,
    get_github_token,
    parse_github_repo,
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
    def test_repository_revision_and_manifest_converge(self, monkeypatch):
        """Exercise the complete adapter path without network access."""
        from core import github_reader

        monkeypatch.setattr(
            github_reader,
            "_get_repo_revision",
            lambda repo, token, timeout: ("main", "abc123"),
        )
        monkeypatch.setattr(
            github_reader,
            "_get_repo_tree",
            lambda repo, token, revision, timeout=30.0: [
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
        )
        monkeypatch.setattr(
            github_reader,
            "_get_file_content",
            lambda repo, path, token, timeout=30.0: "requests==2.32.0\n",
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
        assert deps[0]["_source_paths"] == ["requirements.txt", "packages/app/requirements.txt"]

    def test_empty_supported_files_is_distinct_from_fetch_failure(self, monkeypatch):
        from core import github_reader

        monkeypatch.setattr(
            github_reader,
            "_get_repo_revision",
            lambda repo, token, timeout: ("main", "abc123"),
        )
        monkeypatch.setattr(
            github_reader,
            "_get_repo_tree",
            lambda repo, token, revision, timeout=30.0: [],
        )

        deps, skipped, errors = read_github_repo("owner/repo")

        assert deps == []
        assert not errors
        assert "inspected successfully" in skipped[0]

    def test_tree_limit_is_reported_as_error(self, monkeypatch):
        from core import github_reader

        monkeypatch.setattr(
            github_reader,
            "_get_repo_revision",
            lambda repo, token, timeout: ("main", "abc123"),
        )
        monkeypatch.setattr(
            github_reader,
            "_get_repo_tree",
            lambda repo, token, revision, timeout=30.0: [
                {"type": "blob", "path": f"f{i}.txt", "size": 1}
                for i in range(github_reader.MAX_TREE_ENTRIES + 1)
            ],
        )

        deps, skipped, errors = read_github_repo("owner/repo")

        assert deps == []
        assert skipped == []
        assert errors
        assert "tree exceeds" in errors[0]["safe_message"]

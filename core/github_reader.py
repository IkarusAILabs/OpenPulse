"""GitHub repository dependency ingestion — discovers dependency files
in a GitHub repo and normalizes them via existing manifest/lockfile/SBOM readers.

This is an INPUT ADAPTER, not a new matching engine. It discovers files,
downloads them, and feeds them through the existing readers
(manifest_reader, lockfile_reader, sbom_reader, image_inventory) so
the same identity and matching semantics apply regardless of input source.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Any

import httpx

from collectors.errors import as_error, redact
from core.image_inventory import read_image_inventory
from core.lockfile_reader import read_lockfile
from core.manifest_reader import read_manifest
from core.sbom_reader import read_sbom, read_spdx

GITHUB_API = "https://api.github.com"
DEFAULT_TIMEOUT = 30.0
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB per file
MAX_FILES = 200  # max dependency files to process
MAX_TREE_ENTRIES = 20_000  # bound recursive Git tree expansion before filtering
MAX_DISCOVERED_BYTES = 50 * 1024 * 1024  # 50MB total supported-file budget


@dataclass(frozen=True)
class GitHubRepo:
    owner: str
    name: str
    token: str | None = None

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"

    def __str__(self) -> str:
        return self.full_name


SUPPORTED_MANIFESTS = {
    "requirements.txt",
    "pyproject.toml",
    "pom.xml",
    "go.mod",
    "Cargo.toml",
    "composer.json",
    "build.gradle",
    "build.gradle.kts",
    "Package.swift",
}

SUPPORTED_LOCKFILES = {
    "package-lock.json",
    "poetry.lock",
    "Cargo.lock",
    "composer.lock",
    "packages.lock.json",
    "go.sum",
}

SUPPORTED_SBOMS = {
    "sbom.json",
    "cyclonedx.json",
    "spdx.json",
}

SUPPORTED_INVENTORIES = {
    "images.txt",
    "inventory.txt",
    "images.yaml",
    "inventory.yaml",
}

# Files that indicate a project root (for monorepo detection)
PROJECT_ROOT_INDICATORS = (
    SUPPORTED_MANIFESTS | SUPPORTED_LOCKFILES | SUPPORTED_SBOMS | SUPPORTED_INVENTORIES
)

# Files to skip (not dependency files)
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    "target",
    ".gradle",
    "vendor",
    "packages",
    ".terraform",
}


def parse_github_repo(url_or_name: str) -> GitHubRepo:
    """Parse a GitHub repository identifier.

    Accepts:
    - "owner/repo"
    - "https://github.com/owner/repo"
    - "https://github.com/owner/repo/"
    - "git@github.com:owner/repo.git"

    Returns GitHubRepo or raises ValueError.
    """
    s = url_or_name.strip()
    # Handle git@github.com:owner/repo.git
    if s.startswith("git@github.com:"):
        s = s[len("git@github.com:") :]
        if s.endswith(".git"):
            s = s[: -len(".git")]
        owner, name = s.split("/", 1)
        return GitHubRepo(owner=owner, name=name)

    # Handle https://github.com/owner/repo
    if s.startswith("https://github.com/"):
        s = s[len("https://github.com/") :]
        if s.endswith("/"):
            s = s[:-1]
        parts = s.split("/")
        if len(parts) >= 2:
            owner, name = parts[0], parts[1]
            return GitHubRepo(owner=owner, name=name)

    # Handle owner/repo
    if "/" in s and not s.startswith("http"):
        parts = s.split("/")
        if len(parts) == 2:
            owner, name = parts[0], parts[1]
            if owner and name:
                return GitHubRepo(owner=owner, name=name)

    raise ValueError(
        f"Invalid GitHub repository identifier: {url_or_name}. "
        "Use 'owner/repo' or 'https://github.com/owner/repo'"
    )


def get_github_token(cli_token: str | None = None) -> str | None:
    """Get GitHub token from CLI arg or environment.

    Priority: CLI arg > GITHUB_TOKEN > GH_TOKEN.
    """
    if cli_token:
        return cli_token
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def _headers(token: str | None = None) -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _handle_response(
    response: httpx.Response, context: str, repo: GitHubRepo
) -> list[dict[str, Any]]:
    """Handle GitHub API response, return error dicts on failure."""
    if response.status_code == 404:
        return [as_error("github_repo", Exception("not found"), repo=str(repo), context=context)]
    if response.status_code == 401:
        return [as_error("github_repo", Exception("unauthorized"), repo=str(repo), context=context)]
    if response.status_code == 403:
        # Check if rate limited
        if "rate limit" in response.text.lower():
            return [
                as_error("github_repo", Exception("rate limited"), repo=str(repo), context=context)
            ]
        return [as_error("github_repo", Exception("forbidden"), repo=str(repo), context=context)]
    if response.status_code == 429:
        return [as_error("github_repo", Exception("rate limited"), repo=str(repo), context=context)]
    if response.status_code >= 500:
        return [
            as_error(
                "github_repo",
                Exception(f"server error {response.status_code}"),
                repo=str(repo),
                context=context,
            )
        ]

    try:
        response.raise_for_status()
    except Exception as e:
        return [as_error("github_repo", e, repo=str(repo), context=context)]

    return []


def _get_repo_revision(
    repo: GitHubRepo, token: str | None, timeout: float = DEFAULT_TIMEOUT
) -> tuple[str, str] | list[dict[str, Any]]:
    """Resolve the default branch to an immutable commit SHA.

    Dependency inspection must be reproducible: a mutable HEAD is not
    sufficient evidence for what was actually inspected.
    """
    try:
        with httpx.Client(timeout=timeout, headers=_headers(token)) as client:
            meta = client.get(f"{GITHUB_API}/repos/{repo.full_name}")
            errors = _handle_response(meta, "get_repo_metadata", repo)
            if errors:
                return errors
            default_branch = str(meta.json().get("default_branch") or "")
            if not default_branch:
                return [
                    as_error(
                        "github_repo",
                        Exception("repository has no default branch"),
                        repo=str(repo),
                        context="get_repo_metadata",
                    )
                ]
            ref = client.get(
                f"{GITHUB_API}/repos/{repo.full_name}/commits/{default_branch}"
            )
            errors = _handle_response(ref, "get_repo_revision", repo)
            if errors:
                return errors
            sha = str(ref.json().get("sha") or "")
            if not sha:
                return [
                    as_error(
                        "github_repo",
                        Exception("default branch has no commit SHA"),
                        repo=str(repo),
                        context="get_repo_revision",
                    )
                ]
            return default_branch, sha
    except Exception as e:
        return [
            as_error(
                "github_repo",
                e,
                repo=str(repo),
                context="get_repo_revision",
            )
        ]


def _get_repo_tree(
    repo: GitHubRepo,
    token: str | None,
    revision: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> list[dict[str, Any]]:
    """Get recursive tree of repository contents.

    Returns list of tree entries or error dicts.
    """
    url = f"{GITHUB_API}/repos/{repo.full_name}/git/trees/{revision}?recursive=1"
    try:
        with httpx.Client(timeout=timeout, headers=_headers(token)) as client:
            resp = client.get(url)
            errors = _handle_response(resp, "get_repo_tree", repo)
            if errors:
                return errors
            data = resp.json()
            return data.get("tree", [])
    except Exception as e:
        return [as_error("github_repo", e, repo=str(repo), context="get_repo_tree")]


def _get_file_content(
    repo: GitHubRepo, path: str, token: str | None, timeout: float = DEFAULT_TIMEOUT
) -> str | list[dict[str, Any]]:
    """Get file content from GitHub (base64 decoded).

    Returns decoded content string or error dicts.
    """
    url = f"{GITHUB_API}/repos/{repo.full_name}/contents/{path}"
    try:
        with httpx.Client(timeout=timeout, headers=_headers(token)) as client:
            resp = client.get(url)
            errors = _handle_response(resp, f"get_file:{path}", repo)
            if errors:
                return errors
            data = resp.json()
            if data.get("encoding") == "base64":
                content = base64.b64decode(data["content"]).decode("utf-8")
                return content
            return str(data.get("content", ""))
    except UnicodeDecodeError:
        return [
            as_error(
                "github_repo",
                Exception("binary file"),
                repo=str(repo),
                path=path,
                context="decode",
            )
        ]
    except Exception as e:
        return [as_error("github_repo", e, repo=str(repo), path=path, context="get_file")]


def _is_dependency_file(filename: str) -> tuple[bool, str | None]:
    """Check if a file is a supported dependency file.

    Returns (is_supported, file_type) where file_type is one of:
    'manifest', 'lockfile', 'sbom', 'inventory', or None.
    """
    # Exact matches
    if filename in SUPPORTED_MANIFESTS:
        return True, "manifest"
    if filename in SUPPORTED_LOCKFILES:
        return True, "lockfile"
    if filename in SUPPORTED_SBOMS:
        return True, "sbom"
    if filename in SUPPORTED_INVENTORIES:
        return True, "inventory"

    # Pattern matches
    if filename.endswith(".csproj"):
        return True, "manifest"
    if filename.endswith(".lock.json") and "package" not in filename:
        return True, "lockfile"

    return False, None


def _should_skip_dir(dirname: str) -> bool:
    return dirname in SKIP_DIRS or dirname.startswith(".")


def discover_dependency_files(
    repo: GitHubRepo,
    token: str | None = None,
    revision: str = "HEAD",
) -> list[dict[str, Any]]:
    """Discover dependency files at a repository revision.

    Returns a list of {path, type, size} dicts, or error dicts on failure.
    """
    tree = _get_repo_tree(repo, token, revision)
    if tree and isinstance(tree[0], dict) and tree[0].get("error"):
        return tree

    files: list[dict[str, Any]] = []
    total_size = 0

    for entry in tree:
        if entry.get("type") != "blob":
            continue
        path = entry.get("path", "")
        if not path:
            continue

        # Check if in skipped directory
        parts = path.split("/")
        if any(_should_skip_dir(p) for p in parts[:-1]):
            continue

        filename = parts[-1]
        is_supported, file_type = _is_dependency_file(filename)
        if not is_supported:
            continue

        size = entry.get("size", 0)
        if size > MAX_FILE_SIZE:
            continue  # skip oversized files

        total_size += size
        if total_size > MAX_DISCOVERED_BYTES:
            break  # stop if repo is too large

        files.append({"path": path, "type": file_type, "size": size})

        if len(files) >= MAX_FILES:
            break

    return files


def parse_dependency_file(
    repo: GitHubRepo,
    file_info: dict[str, Any],
    token: str | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Parse a single dependency file and return normalized dependencies.

    Returns (dependencies, skipped_reasons).
    Each dependency includes source context: {source, repository, path}.
    """
    path = file_info["path"]
    file_type = file_info["type"]
    content_or_errors = _get_file_content(repo, path, token)

    if isinstance(content_or_errors, list):  # error list
        return [], [f"{path}: {e.get('safe_message', 'unknown error')}" for e in content_or_errors]

    content = content_or_errors

    deps: list[dict[str, Any]] = []
    skipped: list[str] = []

    try:
        if file_type == "manifest":
            parsed_deps, parsed_skipped, _ = read_manifest_from_content(content, path)
            deps.extend(parsed_deps)
            skipped.extend([f"{path}: {s}" for s in parsed_skipped])
        elif file_type == "lockfile":
            parsed_deps, parsed_skipped, _ = read_lockfile_from_content(content, path)
            deps.extend(parsed_deps)
            skipped.extend([f"{path}: {s}" for s in parsed_skipped])
        elif file_type == "sbom":
            # Try CycloneDX first, then SPDX
            try:
                parsed_deps, parsed_skipped = read_sbom_from_content(content)
            except ValueError:
                try:
                    parsed_deps, parsed_skipped = read_spdx_from_content(content)
                except ValueError as e:
                    return [], [f"{path}: not a valid CycloneDX or SPDX SBOM: {e}"]
            deps.extend(parsed_deps)
            skipped.extend([f"{path}: {s}" for s in parsed_skipped])
        elif file_type == "inventory":
            parsed_deps, parsed_skipped = read_image_inventory_from_content(content, path)
            deps.extend(parsed_deps)
            skipped.extend([f"{path}: {s}" for s in parsed_skipped])
    except Exception as e:
        return [], [f"{path}: {redact(str(e))}"]

    # Add source context to each dependency
    for dep in deps:
        dep["source"] = "github"
        dep["repository"] = str(repo)
        dep["path"] = path

    return deps, skipped


def read_manifest_from_content(
    content: str, path: str
) -> tuple[list[dict[str, Any]], list[str], str]:
    """Read manifest from content string (reuses manifest_reader logic)."""
    import os
    import tempfile

    basename = os.path.basename(path)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=basename, delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        tmp_path = f.name
    try:
        return read_manifest(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def read_lockfile_from_content(
    content: str, path: str
) -> tuple[list[dict[str, Any]], list[str], str]:
    """Read lockfile from content string (reuses lockfile_reader logic)."""
    import os
    import tempfile

    basename = os.path.basename(path)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=basename, delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        tmp_path = f.name
    try:
        return read_lockfile(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def read_sbom_from_content(content: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Read CycloneDX SBOM from content string."""
    import json

    doc = json.loads(content)
    return read_sbom(doc)


def read_spdx_from_content(content: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Read SPDX SBOM from content string."""
    import json

    doc = json.loads(content)
    return read_spdx(doc)


def read_image_inventory_from_content(
    content: str, path: str
) -> tuple[list[dict[str, Any]], list[str]]:
    """Read image inventory from content string."""
    import os
    import tempfile

    basename = os.path.basename(path)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=basename, delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        tmp_path = f.name
    try:
        return read_image_inventory(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def deduplicate_dependencies(deps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate dependencies deterministically.

    Two dependencies are considered the same if they have the same
    identity (kind + package/ref + ecosystem + version).
    """
    seen: dict[tuple, dict[str, Any]] = {}
    for dep in deps:
        if dep["kind"] == "package":
            pkg = dep.get("package", "")
            eco = dep.get("ecosystem", "")
            ver = dep.get("version", "")
            key = ("package", pkg, eco, ver)
        elif dep["kind"] == "image":
            key = ("image", dep.get("ref", ""))
        else:
            key = (dep["kind"], str(dep))

        if key not in seen:
            seen[key] = dep
        else:
            # Merge paths - keep the first one as primary, but note other locations
            existing_paths = seen[key].get("_source_paths", [seen[key].get("path")])
            new_path = dep.get("path")
            if new_path and new_path not in existing_paths:
                existing_paths.append(new_path)
            seen[key]["_source_paths"] = existing_paths

    return list(seen.values())


def read_github_repo(
    repo_spec: str,
    cli_token: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    """Main entry point: discover and parse all dependencies in a GitHub repo.

    Returns (dependencies, skipped_reasons, errors).
    - dependencies: normalized dependency objects with source context
    - skipped_reasons: human-readable skip reasons per file
    - errors: structured error dicts for API/network failures
    """
    repo = parse_github_repo(repo_spec)
    token = get_github_token(cli_token)

    # Discover files
    file_infos = discover_dependency_files(repo, token)
    errors = [e for e in file_infos if e.get("error")]
    file_infos = [f for f in file_infos if not f.get("error")]

    if errors:
        # Return early if we couldn't even list the repo
        return [], [], errors

    if not file_infos:
        return [], ["no supported dependency files found in repository"], []

    # Parse each file
    all_deps: list[dict[str, Any]] = []
    all_skipped: list[str] = []

    for file_info in file_infos:
        deps, skipped = parse_dependency_file(repo, file_info, token)
        all_deps.extend(deps)
        all_skipped.extend(skipped)

    # Deduplicate
    unique_deps = deduplicate_dependencies(all_deps)

    return unique_deps, all_skipped, errors

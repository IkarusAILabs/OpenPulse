"""GitHub repository dependency ingestion — discovers dependency files
in a GitHub repo and normalizes them via existing manifest/lockfile/SBOM readers.

This is an INPUT ADAPTER, not a new matching engine. It discovers files,
downloads them, and feeds them through the existing readers
(manifest_reader, lockfile_reader, sbom_reader, image_inventory) so
the same identity and matching semantics apply regardless of input source.
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

from collectors.errors import as_error, redact
from core.image_inventory import read_image_inventory
from core.lockfile_reader import read_lockfile
from core.manifest_reader import read_manifest
from core.sbom_reader import MAX_SBOM_BYTES, load_sbom_doc, load_spdx_doc

GITHUB_API = "https://api.github.com"
DEFAULT_TIMEOUT = 30.0
# GitHub's blobs API serves base64 payloads up to 100 MB, but every reader
# refuses input over the shared 50 MB parser cap (`MAX_SBOM_BYTES`), so a
# larger blob is skipped by its tree-declared size before download instead
# of being fetched only to be rejected. Over the cap is an explicit PARTIAL
# skip, never a silent "no dependencies" (F2). Pinned equal to the parser
# cap by tests.
MAX_BLOB_BYTES = 50 * 1024 * 1024
MAX_FILES = 200  # max dependency files to process
MAX_TREE_ENTRIES = 20_000  # bound recursive Git tree expansion before filtering
MAX_DISCOVERED_BYTES = 50 * 1024 * 1024  # 50MB total supported-file budget

#: Repository inspection coverage. COMPLETE means every discovered
#: dependency file was read, integrity-verified and parsed; PARTIAL means
#: at least one file or tree region was not (skips, caps, truncation,
#: fetch/parse errors); FAILED means the repository could not be
#: enumerated at all (revision or tree unavailable).
COVERAGE_COMPLETE = "COMPLETE"
COVERAGE_PARTIAL = "PARTIAL"
COVERAGE_FAILED = "FAILED"

#: Sentinel appended to a tree listing when GitHub reports the recursive
#: tree as truncated; discovery downgrades coverage to PARTIAL.
_TREE_TRUNCATED_KEY = "_openpulse_tree_truncated"
_TREE_TRUNCATED_MARKER = {_TREE_TRUNCATED_KEY: True}


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


@dataclass
class RepoInspection:
    """Outcome of inspecting one repository revision.

    ``coverage`` is COMPLETE/PARTIAL/FAILED; ``coverage_reasons`` lists
    every downgrade cause (tree truncated, size/file cap, fetch error,
    binary, parse error, rejected path). Every returned dependency is
    stamped with the same repository-level coverage, so a verdict can
    never look fully inspected when part of the tree was not read.
    """

    dependencies: list[dict[str, Any]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    coverage: str = COVERAGE_COMPLETE
    coverage_reasons: list[str] = field(default_factory=list)
    branch: str = ""
    commit: str = ""


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

    Returns GitHubRepo or raises ValueError. Owner and name must match
    GitHub's own charsets: they are interpolated into API URLs, so `..`,
    `?`, `#` or extra path segments must never reach a request.
    """
    s = url_or_name.strip()
    owner = name = None
    # Handle git@github.com:owner/repo.git
    if s.startswith("git@github.com:"):
        parts = s[len("git@github.com:") :].removesuffix(".git").split("/")
        if len(parts) == 2:
            owner, name = parts
    # Handle https://github.com/owner/repo
    elif s.startswith("https://github.com/"):
        parts = s[len("https://github.com/") :].rstrip("/").split("/")
        if len(parts) >= 2:
            owner, name = parts[0], parts[1].removesuffix(".git")
    # Handle owner/repo
    elif "/" in s and not s.startswith("http"):
        parts = s.split("/")
        if len(parts) == 2:
            owner, name = parts

    if owner is not None and name is not None and _valid_repo_parts(owner, name):
        return GitHubRepo(owner=owner, name=name)
    raise ValueError(
        f"Invalid GitHub repository identifier: {url_or_name}. "
        "Use 'owner/repo' or 'https://github.com/owner/repo'"
    )


#: GitHub logins: alphanumerics and single hyphens, <= 39 chars (underscore
#: tolerated for enterprise/legacy accounts). Repo names: [A-Za-z0-9._-].
_GITHUB_OWNER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,38}$")
_GITHUB_REPO_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")


def _valid_repo_parts(owner: str, name: str) -> bool:
    return (
        bool(_GITHUB_OWNER_RE.match(owner))
        and bool(_GITHUB_REPO_RE.match(name))
        and name not in (".", "..")
    )


MAX_GITHUB_TOKEN_FILE_BYTES = 4096


def get_github_token(cli_token: str | None = None, token_file: str | None = None) -> str | None:
    """Get a GitHub token without requiring it to appear in argv.

    Priority: CLI arg > token file > GITHUB_TOKEN > GH_TOKEN.
    """
    if cli_token:
        return cli_token
    if token_file:
        with open(token_file, "rb") as handle:
            raw = handle.read(MAX_GITHUB_TOKEN_FILE_BYTES + 1)
        if len(raw) > MAX_GITHUB_TOKEN_FILE_BYTES:
            raise ValueError(f"GitHub token file exceeds {MAX_GITHUB_TOKEN_FILE_BYTES} bytes")
        try:
            token = raw.decode("utf-8").splitlines()[0].strip() if raw else ""
        except UnicodeDecodeError as exc:
            raise ValueError("GitHub token file is not UTF-8 text") from exc
        if not token:
            raise ValueError("GitHub token file does not contain a token")
        return token
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
            tree = list(data.get("tree", []))
            if data.get("truncated"):
                # GitHub caps the recursive listing; an entry we cannot
                # see is a file we cannot inspect - never treat the
                # partial listing as the whole repository.
                tree.append(dict(_TREE_TRUNCATED_MARKER))
            return tree
    except Exception as e:
        return [as_error("github_repo", e, repo=str(repo), context="get_repo_tree")]


def _tree_is_truncated(tree: list[dict[str, Any]]) -> bool:
    return any(_TREE_TRUNCATED_KEY in entry for entry in tree)


def _git_blob_sha1(payload: bytes) -> str:
    """Git object id of a blob: sha1("blob {len}\\0" + payload)."""
    header = f"blob {len(payload)}".encode("ascii") + b"\x00"
    return hashlib.sha1(header + payload).hexdigest()  # noqa: S324 - Git object id, not a security hash


def _get_blob_content(
    repo: GitHubRepo,
    blob_sha: str,
    token: str | None,
    timeout: float = DEFAULT_TIMEOUT,
) -> tuple[str | None, dict[str, Any] | None]:
    """Fetch one blob by its immutable git SHA and verify the returned
    content hashes back to that SHA before decoding.

    Returns ``(content, None)`` on success or ``(None, error_dict)`` on
    any failure. The blobs API always returns base64 (up to 100 MB), so a
    file is either fully read or an explicit error - never an empty
    string standing in for a body nobody fetched (F1/F2).
    """
    if not blob_sha:
        return None, as_error(
            "github_repo", Exception("tree entry has no blob SHA"), repo=str(repo), context="blob"
        )
    url = f"{GITHUB_API}/repos/{repo.full_name}/git/blobs/{blob_sha}"
    try:
        with httpx.Client(timeout=timeout, headers=_headers(token)) as client:
            resp = client.get(url)
            errors = _handle_response(resp, f"get_blob:{blob_sha}", repo)
            if errors:
                return None, errors[0]
            data = resp.json()
    except Exception as e:
        return None, as_error("github_repo", e, repo=str(repo), context="get_blob")

    if data.get("encoding") != "base64" or not isinstance(data.get("content"), str):
        return None, as_error(
            "github_repo",
            Exception(f"blob {blob_sha} returned encoding {data.get('encoding')!r}, not base64"),
            repo=str(repo),
            context="blob_encoding",
        )
    try:
        payload = base64.b64decode(data["content"])
    except (ValueError, TypeError):
        return None, as_error(
            "github_repo",
            Exception(f"blob {blob_sha} returned undecodable base64"),
            repo=str(repo),
            context="blob_decode",
        )
    actual = _git_blob_sha1(payload)
    if actual != blob_sha:
        return None, as_error(
            "github_repo",
            Exception(f"blob SHA mismatch: requested {blob_sha}, content hashes to {actual}"),
            repo=str(repo),
            context="blob_integrity",
        )
    try:
        return payload.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, as_error(
            "github_repo",
            Exception("binary file"),
            repo=str(repo),
            sha=blob_sha,
            context="blob_decode",
        )


def _safe_repo_path(path: str) -> bool:
    """Whether a tree path is safe to materialize.

    Rejects absolute paths, drive-qualified paths, backslashes and any
    ``..`` segment so a hostile tree entry cannot escape the temp
    directory it is parsed from (F8).
    """
    if not path or path.startswith(("/", "\\")):
        return False
    if ":" in path or "\\" in path:
        return False
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return False
    return True


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


@dataclass
class _Discovery:
    """Result of enumerating dependency files at one revision."""

    files: list[dict[str, Any]] = field(default_factory=list)
    skip_reasons: list[str] = field(default_factory=list)
    truncated: bool = False
    error: dict[str, Any] | None = None


def discover_dependency_files(
    repo: GitHubRepo,
    token: str | None = None,
    revision: str = "HEAD",
) -> _Discovery:
    """Discover dependency files at an immutable repository revision.

    Each returned file is ``{path, type, size, sha}`` where ``sha`` is
    the git blob id taken from the pinned tree - the exact object the
    content fetch must return. Every dropped file (oversize, cap, unsafe
    path) is recorded as a skip reason so coverage can degrade to
    PARTIAL instead of silently shrinking the inspected set.
    """
    tree = _get_repo_tree(repo, token, revision)
    if tree and isinstance(tree[0], dict) and tree[0].get("error"):
        return _Discovery(error=tree[0])

    truncated = _tree_is_truncated(tree)
    entries = [e for e in tree if _TREE_TRUNCATED_KEY not in e]

    if len(entries) > MAX_TREE_ENTRIES:
        return _Discovery(
            error={
                "error": True,
                "safe_message": f"repository tree exceeds {MAX_TREE_ENTRIES} entries",
                "category": "github_repo",
            }
        )

    files: list[dict[str, Any]] = []
    skip_reasons: list[str] = []
    total_size = 0

    for entry in entries:
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

        if not _safe_repo_path(path):
            skip_reasons.append(f"{path}: rejected unsafe repository path")
            continue

        size = int(entry.get("size", 0) or 0)
        if size > MAX_BLOB_BYTES:
            skip_reasons.append(
                f"{path}: {size} bytes exceeds {MAX_BLOB_BYTES}-byte inspection limit"
            )
            continue

        total_size += size
        if total_size > MAX_DISCOVERED_BYTES:
            skip_reasons.append(
                f"{path}: repository size cap ({MAX_DISCOVERED_BYTES} bytes) reached; "
                "remaining dependency files not inspected"
            )
            break

        files.append({"path": path, "type": file_type, "size": size, "sha": entry.get("sha", "")})

        if len(files) >= MAX_FILES:
            skip_reasons.append(
                f"file cap ({MAX_FILES}) reached; remaining dependency files not inspected"
            )
            break

    return _Discovery(files=files, skip_reasons=skip_reasons, truncated=truncated)


def parse_dependency_file(
    repo: GitHubRepo,
    file_info: dict[str, Any],
    token: str | None = None,
) -> tuple[list[dict[str, Any]], list[str], bool]:
    """Parse a single dependency file and return normalized dependencies.

    Returns ``(dependencies, skipped_reasons, readable)`` where
    ``readable`` is False when the blob could not be fetched, verified or
    parsed - the signal that coverage must degrade to PARTIAL. Reader
    skips (e.g. unpinned entries) keep ``readable`` True: they are
    findings about content that was fully read, not reading failures.
    """
    path = file_info["path"]
    file_type = file_info["type"]
    blob_sha = str(file_info.get("sha") or "")

    content, error = _get_blob_content(repo, blob_sha, token)
    if error is not None:
        return [], [f"{path}: {error.get('safe_message', 'unknown error')}"], False

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
                    return [], [f"{path}: not a valid CycloneDX or SPDX SBOM: {e}"], False
            deps.extend(parsed_deps)
            skipped.extend([f"{path}: {s}" for s in parsed_skipped])
        elif file_type == "inventory":
            parsed_deps, parsed_skipped = read_image_inventory_from_content(content, path)
            deps.extend(parsed_deps)
            skipped.extend([f"{path}: {s}" for s in parsed_skipped])
    except Exception as e:
        return [], [f"{path}: {redact(str(e))}"], False

    # Add source context to each dependency
    for dep in deps:
        dep["source"] = "github"
        dep["repository"] = str(repo)
        dep["path"] = path

    return deps, skipped, True


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


def _parse_sbom_json(content: str, label: str) -> Any:
    """Size-bounded JSON parse - the same cap the on-disk SBOM readers apply."""
    import json

    size = len(content.encode("utf-8"))
    if size > MAX_SBOM_BYTES:
        raise ValueError(f"{label} is {size} bytes (limit {MAX_SBOM_BYTES})")
    return json.loads(content)


def read_sbom_from_content(content: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Read CycloneDX SBOM from content string.

    Goes through the doc-level loader: the path readers (`read_sbom`)
    take a filename, and handing them a parsed dict raised TypeError,
    so repository SBOMs were never ingested.
    """
    return load_sbom_doc(_parse_sbom_json(content, "sbom"))


def read_spdx_from_content(content: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Read SPDX SBOM from content string (doc-level loader, size-bounded)."""
    return load_spdx_doc(_parse_sbom_json(content, "spdx"))


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


def inspect_github_repo(
    repo_spec: str,
    cli_token: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> RepoInspection:
    """Discover and parse every dependency file at the pinned commit.

    The tree and every blob are read at the same immutable commit SHA and
    each blob is verified against the SHA the tree declared. Coverage is
    COMPLETE only when the whole tree was enumerated and every discovered
    file was read and parsed; PARTIAL when anything was skipped, capped,
    truncated or failed; FAILED when the repository could not be
    enumerated. A fetch failure can never surface as zero dependencies
    with COMPLETE coverage.
    """
    repo = parse_github_repo(repo_spec)
    token = get_github_token(cli_token)

    revision_info = _get_repo_revision(repo, token, timeout)
    if isinstance(revision_info, list):
        return RepoInspection(errors=revision_info, coverage=COVERAGE_FAILED)
    default_branch, commit_sha = revision_info

    # Discover files at the immutable commit; content is fetched by the
    # blob SHA this tree declares, never from a mutable ref (F1).
    discovery = discover_dependency_files(repo, token, commit_sha)
    if discovery.error is not None:
        return RepoInspection(
            errors=[discovery.error],
            coverage=COVERAGE_FAILED,
            branch=default_branch,
            commit=commit_sha,
        )

    coverage_reasons: list[str] = []
    if discovery.truncated:
        coverage_reasons.append("repository tree truncated by GitHub")
    coverage_reasons.extend(discovery.skip_reasons)

    if not discovery.files:
        if not coverage_reasons:
            return RepoInspection(
                skipped=[
                    "repository inspected successfully at its default-branch commit, "
                    "but no supported dependency files were found"
                ],
                coverage=COVERAGE_COMPLETE,
                branch=default_branch,
                commit=commit_sha,
            )
        return RepoInspection(
            skipped=list(coverage_reasons),
            coverage=COVERAGE_PARTIAL,
            coverage_reasons=list(coverage_reasons),
            branch=default_branch,
            commit=commit_sha,
        )

    all_deps: list[dict[str, Any]] = []
    all_skipped: list[str] = []
    for file_info in discovery.files:
        deps, skipped, readable = parse_dependency_file(repo, file_info, token)
        if not readable:
            coverage_reasons.extend(skipped)
        for dep in deps:
            dep["repository_branch"] = default_branch
            dep["repository_commit"] = commit_sha
        all_deps.extend(deps)
        all_skipped.extend(skipped)

    unique_deps = deduplicate_dependencies(all_deps)

    coverage = COVERAGE_PARTIAL if coverage_reasons else COVERAGE_COMPLETE
    for dep in unique_deps:
        dep["inspection_coverage"] = coverage
        dep["inspection_coverage_reasons"] = list(coverage_reasons)

    return RepoInspection(
        dependencies=unique_deps,
        skipped=all_skipped,
        errors=[],
        coverage=coverage,
        coverage_reasons=list(coverage_reasons),
        branch=default_branch,
        commit=commit_sha,
    )


def read_github_repo(
    repo_spec: str,
    cli_token: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    """Main entry point: discover and parse all dependencies in a GitHub repo.

    Thin wrapper over :func:`inspect_github_repo` preserving the original
    3-tuple shape. Returns (dependencies, skipped_reasons, errors).
    - dependencies: normalized dependency objects with source context
      (each stamped with ``inspection_coverage``/``inspection_coverage_reasons``)
    - skipped_reasons: human-readable skip reasons per file
    - errors: structured error dicts for API/network failures
    """
    inspection = inspect_github_repo(repo_spec, cli_token, timeout)
    return inspection.dependencies, inspection.skipped, inspection.errors

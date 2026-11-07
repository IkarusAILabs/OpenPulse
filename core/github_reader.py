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
from core.bounded_io import read_bytes
from core.image_inventory import read_image_inventory
from core.lockfile_reader import read_lockfile
from core.manifest_reader import load_requirements_txt_doc, read_manifest
from core.sbom_reader import MAX_SBOM_BYTES, load_sbom_doc, load_spdx_doc

GITHUB_API = "https://api.github.com"
DEFAULT_TIMEOUT = 30.0
MAX_FILES = 200  # max dependency files to process
MAX_TREE_ENTRIES = 20_000  # bound recursive Git tree expansion before filtering
MAX_DISCOVERED_BYTES = 50 * 1024 * 1024  # 50MB total supported-file budget
#: GitHub's blobs API serves base64 payloads up to 100 MB.
GITHUB_BLOB_API_LIMIT = 100 * 1024 * 1024
# Per-file cap, checked against the tree-declared size before download: the
# smallest of what a reader will parse (MAX_SBOM_BYTES), what the blobs API
# serves, and half the repository budget, so one large file cannot use up
# the whole budget and leave every other manifest uninspected (#103). Over
# the cap is an explicit PARTIAL skip, never a silent "no dependencies"
# (F2). The invariants are pinned in tests/test_bounded_io.py.
MAX_BLOB_BYTES = min(MAX_SBOM_BYTES, GITHUB_BLOB_API_LIMIT, MAX_DISCOVERED_BYTES // 2)

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
    #: What was searched (v0.18.0 S3): see :func:`discovery_scope`. None
    #: when the repository could not be enumerated at all.
    scope: dict[str, Any] | None = None


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

# Dependency files OpenPulse recognises but cannot read. Discovery lists
# each one as a skip reason so coverage degrades to PARTIAL instead of a
# repository built on them reading COMPLETE (unknown stays unknown).
UNSUPPORTED_DEPENDENCY_FILES = {
    "yarn.lock",
    "pnpm-lock.yaml",
    "uv.lock",
    "Pipfile",
    "Pipfile.lock",
    "bun.lock",
    "bun.lockb",
    "gradle.lockfile",
    "environment.yml",
    "environment.yaml",
    "setup.py",
    "setup.cfg",
}

UNSUPPORTED_REASON = "dependency file not supported; its dependencies were not inspected"

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
    # fullmatch: with re.match, "$" also matches before a trailing newline,
    # so "owner\n" passed (T-F3 fix E).
    return (
        bool(_GITHUB_OWNER_RE.fullmatch(owner))
        and bool(_GITHUB_REPO_RE.fullmatch(name))
        and name not in (".", "..")
    )


MAX_GITHUB_TOKEN_FILE_BYTES = 4096


#: A GitHub token is visible ASCII: no spaces, controls or non-ASCII.
_TOKEN_SHAPE = re.compile(r"[\x21-\x7e]+")


def _token_from_file(token_file: str) -> str:
    """The one non-empty line of a token file, validated (#138).

    Messages never contain the token: a malformed file may still hold
    most of a real one.
    """
    raw = read_bytes(token_file, MAX_GITHUB_TOKEN_FILE_BYTES, "GitHub token file")
    try:
        # utf-8-sig: Windows editors (Notepad) write a BOM, which strip()
        # keeps and which would make the Authorization header unencodable.
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("GitHub token file is not UTF-8 text") from exc
    # Secret-manager templates may lead with a blank line; take the
    # non-empty one, and refuse to guess between two.
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("GitHub token file does not contain a token")
    if len(lines) > 1:
        raise ValueError(
            f"GitHub token file has more than one non-empty line ({len(lines)}); "
            "keep only the token"
        )
    if not _TOKEN_SHAPE.fullmatch(lines[0]):
        raise ValueError(
            "GitHub token file does not hold a valid token: it contains spaces, "
            "control characters or non-ASCII characters"
        )
    return lines[0]


def get_github_token(cli_token: str | None = None, token_file: str | None = None) -> str | None:
    """Get a GitHub token without requiring it to appear in argv.

    Priority: CLI arg > token file > GITHUB_TOKEN > GH_TOKEN.
    """
    if cli_token:
        return cli_token
    if token_file:
        return _token_from_file(token_file)
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


def _is_requirements_variant(path: str) -> bool:
    """A pip requirements file other than ``requirements.txt`` (v0.18.0 S2):
    ``requirements*.txt`` (``requirements-dev.txt``, ``requirements_test.txt``),
    ``constraints*.txt``, and any ``.txt`` in a ``requirements/`` directory,
    the pre-commit hook's pattern widened to constraints and that directory.
    """
    directory, _, filename = path.rpartition("/")
    if not filename.endswith(".txt") or filename == "requirements.txt":
        return False
    return (
        filename.startswith(("requirements", "constraints"))
        or directory.rpartition("/")[2] == "requirements"
    )


#: ``-r FILE`` / ``--requirement FILE`` and ``-c FILE`` / ``--constraint FILE``,
#: with or without a space or ``=`` (pip's own spellings).
_INCLUDE = re.compile(r"^(?:-r|-c|--requirement|--constraint)(?:\s*=\s*|\s+|(?<=-r)|(?<=-c))(\S+)")


def requirements_includes(content: str) -> list[str]:
    """The files a requirements file pulls in with ``-r`` or ``-c``, as written.

    Their lines are never in this file, so the reader records the option
    line as skipped; the caller checks that each target was inspected
    itself, or coverage is PARTIAL.
    """
    found = []
    for raw in content.splitlines():
        line = raw.split(" #", 1)[0].strip()
        match = _INCLUDE.match(line)
        if match:
            found.append(match.group(1))
    return found


def _include_target(path: str, target: str) -> str | None:
    """The repository path ``target`` names from the file at ``path``, or None
    when it names nothing inside the repository (a URL, an absolute path, a
    path that climbs out)."""
    import posixpath

    if "://" in target or target.startswith(("/", "\\")) or ":" in target or "\\" in target:
        return None
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
    return resolved if _safe_repo_path(resolved) else None


def _unsupported_reason(path: str, npm_lock_dirs: set[str]) -> str | None:
    """Why a recognised but unreadable dependency file was not inspected.

    Returns None for files that are not dependency files. ``package.json``
    is read through the ``package-lock.json`` beside it, so it is only
    reported when that lockfile is absent. Requirements variants are read
    (v0.18.0 S2) and never reach here.
    """
    directory, _, filename = path.rpartition("/")
    if filename in UNSUPPORTED_DEPENDENCY_FILES:
        return f"{path}: {UNSUPPORTED_REASON}"
    if filename == "package.json":
        if directory in npm_lock_dirs:
            return None
        return f"{path}: {UNSUPPORTED_REASON} (no package-lock.json beside it)"
    return None


def _should_skip_dir(dirname: str) -> bool:
    return dirname in SKIP_DIRS or dirname.startswith(".")


@dataclass
class _Discovery:
    """Result of enumerating dependency files at one revision."""

    files: list[dict[str, Any]] = field(default_factory=list)
    skip_reasons: list[str] = field(default_factory=list)
    truncated: bool = False
    error: dict[str, Any] | None = None
    tree_entries: int = 0
    #: skipped directory name -> files under it that were not looked at
    skipped_dirs: dict[str, int] = field(default_factory=dict)
    limits_reached: list[str] = field(default_factory=list)


def discover_dependency_files(
    repo: GitHubRepo,
    token: str | None = None,
    revision: str = "HEAD",
) -> _Discovery:
    """Discover dependency files at an immutable repository revision.

    Each returned file is ``{path, type, size, sha}`` where ``sha`` is
    the git blob id taken from the pinned tree - the exact object the
    content fetch must return. Every dropped file (oversize, cap, unsafe
    path, recognised but unsupported format) is recorded as a skip reason
    so coverage can degrade to PARTIAL instead of silently shrinking the
    inspected set.
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
    skipped_dirs: dict[str, int] = {}
    limits: list[str] = []
    total_size = 0
    npm_lock_dirs = {
        e.get("path", "").rpartition("/")[0]
        for e in entries
        if e.get("type") == "blob" and e.get("path", "").rpartition("/")[2] == "package-lock.json"
    }

    for entry in entries:
        if entry.get("type") != "blob":
            continue
        path = entry.get("path", "")
        if not path:
            continue

        # Check if in skipped directory
        parts = path.split("/")
        skipped = next((p for p in parts[:-1] if _should_skip_dir(p)), None)
        if skipped is not None:
            skipped_dirs[skipped] = skipped_dirs.get(skipped, 0) + 1
            continue

        filename = parts[-1]
        is_supported, file_type = _is_dependency_file(filename)
        if not is_supported and _is_requirements_variant(path):
            is_supported, file_type = True, "requirements"
        if not is_supported:
            reason = _unsupported_reason(path, npm_lock_dirs)
            if reason is not None:
                skip_reasons.append(reason)
            continue

        if not _safe_repo_path(path):
            skip_reasons.append(f"{path}: rejected unsafe repository path")
            continue

        size = int(entry.get("size", 0) or 0)
        if size > MAX_BLOB_BYTES:
            skip_reasons.append(
                f"{path}: {size} bytes exceeds {MAX_BLOB_BYTES}-byte inspection limit"
            )
            if "max_file_bytes" not in limits:
                limits.append("max_file_bytes")
            continue

        total_size += size
        if total_size > MAX_DISCOVERED_BYTES:
            skip_reasons.append(
                f"{path}: repository size cap ({MAX_DISCOVERED_BYTES} bytes) reached; "
                "remaining dependency files not inspected"
            )
            limits.append("max_total_bytes")
            break

        files.append({"path": path, "type": file_type, "size": size, "sha": entry.get("sha", "")})

        if len(files) >= MAX_FILES:
            skip_reasons.append(
                f"file cap ({MAX_FILES}) reached; remaining dependency files not inspected"
            )
            limits.append("max_files")
            break

    return _Discovery(
        files=files,
        skip_reasons=skip_reasons,
        truncated=truncated,
        tree_entries=len(entries),
        skipped_dirs=skipped_dirs,
        limits_reached=limits,
    )


#: What discovery looks for, in the order a reader would scan the list.
DISCOVERY_PATTERNS = (
    *sorted(SUPPORTED_MANIFESTS | SUPPORTED_LOCKFILES | SUPPORTED_SBOMS | SUPPORTED_INVENTORIES),
    "*.csproj",
    "*.lock.json",
    "requirements*.txt",
    "constraints*.txt",
    "requirements/*.txt",
)
#: Skipped directories named in a scope, at most; the rest are summed.
MAX_SCOPE_DIRS = 50
_SCOPE_DIR = re.compile(r"[A-Za-z0-9._-]{1,100}")


def discovery_scope(
    repo: GitHubRepo,
    branch: str,
    commit: str,
    discovery: _Discovery,
    files_read: int,
) -> dict[str, Any]:
    """What one repository inspection searched (v0.18.0 S3), in a fixed shape.

    The ref and commit, the file-name patterns read and the recognised
    names that are not, the directories skipped with how many files each
    held, the tree size, the limits and which of them applied, and how
    many dependency files were found and read. A directory name outside a
    plain character set is counted, not named.
    """
    named = sorted(
        (d for d in discovery.skipped_dirs if _SCOPE_DIR.fullmatch(d)),
        key=lambda d: (-discovery.skipped_dirs[d], d),
    )[:MAX_SCOPE_DIRS]
    other = sum(n for d, n in discovery.skipped_dirs.items() if d not in named)
    skipped = [{"directory": d, "files": discovery.skipped_dirs[d]} for d in named]
    if other:
        skipped.append({"directory": None, "files": other})
    limits = list(discovery.limits_reached)
    if discovery.truncated:
        limits.insert(0, "tree_truncated")
    return {
        "repository": str(repo),
        "ref": branch,
        "commit": commit,
        "file_patterns": list(DISCOVERY_PATTERNS),
        "recognised_not_read": sorted(UNSUPPORTED_DEPENDENCY_FILES)
        + ["package.json (without package-lock.json)"],
        "skipped_directories": skipped,
        "tree_entries": discovery.tree_entries,
        "limits": {
            "max_tree_entries": MAX_TREE_ENTRIES,
            "max_files": MAX_FILES,
            "max_file_bytes": MAX_BLOB_BYTES,
            "max_total_bytes": MAX_DISCOVERED_BYTES,
        },
        "limits_reached": limits,
        "files_found": len(discovery.files),
        "files_read": files_read,
    }


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

    if file_type == "requirements" or path.rpartition("/")[2] == "requirements.txt":
        file_info["includes"] = requirements_includes(content or "")

    try:
        if file_type == "requirements":
            # Known to be pip requirements by its name: parsed as such, so a
            # file of only `-r base.txt` or unpinned lines is read, not refused.
            parsed_deps, parsed_skipped = load_requirements_txt_doc(content)
            deps.extend(parsed_deps)
            skipped.extend([f"{path}: {s}" for s in parsed_skipped])
        elif file_type == "manifest":
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
        scope = discovery_scope(repo, default_branch, commit_sha, discovery, 0)
        if not coverage_reasons:
            return RepoInspection(
                skipped=[
                    "repository inspected successfully at its default-branch commit, "
                    "but no supported dependency files were found"
                ],
                coverage=COVERAGE_COMPLETE,
                branch=default_branch,
                commit=commit_sha,
                scope=scope,
            )
        return RepoInspection(
            skipped=list(coverage_reasons),
            coverage=COVERAGE_PARTIAL,
            coverage_reasons=list(coverage_reasons),
            branch=default_branch,
            commit=commit_sha,
            scope=scope,
        )

    all_deps: list[dict[str, Any]] = []
    all_skipped: list[str] = []
    files_read = 0
    for file_info in discovery.files:
        deps, skipped, readable = parse_dependency_file(repo, file_info, token)
        files_read += readable
        if not readable:
            coverage_reasons.extend(skipped)
        for dep in deps:
            dep["repository_branch"] = default_branch
            dep["repository_commit"] = commit_sha
        all_deps.extend(deps)
        all_skipped.extend(skipped)

    # A `-r` / `-c` include pulls in lines this run read only if the target
    # was itself inspected; anything else is unknown, so coverage is PARTIAL.
    inspected = {f["path"] for f in discovery.files}
    for file_info in discovery.files:
        for target in file_info.get("includes") or []:
            resolved = _include_target(file_info["path"], target)
            if resolved is None:
                coverage_reasons.append(
                    f"{file_info['path']}: includes a requirements file outside the "
                    "repository (-r/-c); its dependencies were not inspected"
                )
            elif resolved not in inspected:
                coverage_reasons.append(
                    f"{file_info['path']}: includes {resolved} (-r/-c), which was not "
                    "inspected; its dependencies were not inspected"
                )

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
        scope=discovery_scope(repo, default_branch, commit_sha, discovery, files_read),
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

"""Lockfile readers - pinned entries become checkable dependencies.

Three formats, one discipline: package-lock.json (npm v1/v2/v3),
poetry.lock, and Cargo.lock all normalize into the same dep shapes
the watchlist and SBOM paths use (`{kind: package, package,
ecosystem, version}`) and feed `core.risk.check.check_dependency`
without touching matching semantics. A pinned version is REQUIRED:
entries without a resolved version, or whose identity would be a
guess (workspace links, path/git-sourced cargo crates), are skipped
and recorded - never range-guessed, never name-guessed.

Size cap and malformed-input refusal reuse the SBOM reader's policy:
multi-MB inputs are legitimate, unbounded reads are not. Format
detection is structural (npm's integer `lockfileVersion`, poetry's
`lock-version` marker, Cargo's root `version`), and anything the
markers cannot name is refused rather than guessed. No new
dependencies; no network. TOML parsing uses the stdlib `tomllib`
(Python 3.11+, matching CI); on 3.10 the TOML formats refuse with a
clean error instead of pulling a parser in.
"""

from __future__ import annotations

import json
import os
from typing import Any

from core import sbom_reader

#: Lockfiles share the SBOM reader's size cap - the same bounded-read
#: policy (real package-lock.json and poetry.lock files routinely run
#: multi-MB), not a second unbounded channel.
MAX_LOCKFILE_BYTES = sbom_reader.MAX_SBOM_BYTES


def _pinned_dep(package: str, ecosystem: str, version: str) -> dict[str, Any]:
    """One pinned entry -> the exact shape watchlist/SBOM deps use."""
    return {"kind": "package", "package": package, "ecosystem": ecosystem, "version": version}


def _name_from_lock_path(key: str) -> str:
    """`.../node_modules/<name>` -> `<name>` (scoped names included).

    The dependency's npm name is the segment after the LAST
    `node_modules/`: nested installs (`a/node_modules/b`) repeat the
    marker per level, so rsplit, not split.
    """
    return key.rsplit("node_modules/", 1)[1]


def load_package_lock_doc(doc: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate a parsed package-lock.json into pinned dep entries.

    Returns (dependencies, skipped) - same contract as
    `sbom_reader.load_sbom_doc`. v2/v3 read `packages` (path-keyed);
    v1 reads `dependencies` (name-keyed, nested). A v2 lock carries
    BOTH - only the richer `packages` view is read, so no entry is
    counted twice. Root (`""`), workspace members (paths without a
    `node_modules/` segment), and workspace links are not
    third-party pins: each is skipped with its reason, keeping the
    accounting complete.
    """
    if not isinstance(doc, dict):
        raise ValueError("package-lock must be a mapping")
    if not isinstance(doc.get("lockfileVersion"), int):
        raise ValueError("package-lock needs an integer `lockfileVersion`")
    deps: list[dict[str, Any]] = []
    skipped: list[str] = []
    packages = doc.get("packages")
    if isinstance(packages, dict):
        for key, entry in packages.items():
            label = str(key) if key else "root"
            if not isinstance(entry, dict):
                skipped.append(f"`{label}`: not a mapping")
                continue
            if "node_modules/" not in key:
                if key == "":
                    skipped.append('root project entry (`packages[""]`): not a dependency')
                else:
                    skipped.append(f"`{label}`: workspace member, not an installed dependency")
                continue
            name = _name_from_lock_path(str(key))
            if not name or name.startswith("."):
                # npm-internal metadata keys (e.g. `.package-lock.json`)
                # are bookkeeping, never a package identity.
                skipped.append(f"`{label}`: npm-internal metadata key, not a package")
                continue
            if entry.get("link"):
                skipped.append(f"`{name}`: workspace link - no pinned registry version")
                continue
            version = entry.get("version")
            if not isinstance(version, str) or not version:
                skipped.append(f"`{name}`: no resolved version - skipped, never range-guessed")
                continue
            deps.append(_pinned_dep(name, "npm", version))
        return deps, skipped
    v1 = doc.get("dependencies")
    if isinstance(v1, dict):
        _walk_v1_dependencies(v1, deps, skipped)
        return deps, skipped
    raise ValueError(
        "package-lock needs a `packages` mapping (lockfileVersion 2/3) "
        "or a `dependencies` mapping (lockfileVersion 1)"
    )


def _walk_v1_dependencies(
    node: dict[str, Any], deps: list[dict[str, Any]], skipped: list[str]
) -> None:
    """v1 lockfiles nest installed deps inside `dependencies` - walk all levels."""
    for name, entry in node.items():
        if not isinstance(entry, dict):
            skipped.append(f"`{name}`: not a mapping")
            continue
        version = entry.get("version")
        if not isinstance(version, str) or not version:
            skipped.append(f"`{name}`: no resolved version - skipped, never range-guessed")
            continue
        deps.append(_pinned_dep(str(name), "npm", version))
        nested = entry.get("dependencies")
        if isinstance(nested, dict):
            _walk_v1_dependencies(nested, deps, skipped)


def load_poetry_lock_doc(doc: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate a parsed poetry.lock into pinned dep entries.

    Same contract as `load_package_lock_doc`. The `lock-version`
    marker is what names the format (unambiguous against Cargo.lock);
    a lockfile without it predates Poetry 1.1 and is refused rather
    than guessed at. A lock with zero packages is valid state (the
    project has no deps) - it yields zero deps, not an error.
    """
    if not isinstance(doc, dict):
        raise ValueError("poetry.lock must be a mapping")
    if "lock-version" not in doc:
        raise ValueError(
            "poetry.lock needs a `lock-version` marker (Poetry 1.1+); "
            "older formats are refused rather than guessed at"
        )
    packages = doc.get("package", [])
    if not isinstance(packages, list):
        raise ValueError("poetry.lock `package` must be a list of tables")
    deps: list[dict[str, Any]] = []
    skipped: list[str] = []
    for i, entry in enumerate(packages):
        if not isinstance(entry, dict):
            skipped.append(f"package #{i}: not a mapping")
            continue
        name = entry.get("name")
        label = str(name) if name is not None else f"package #{i}"
        if not name:
            skipped.append(f"package #{i}: no name")
            continue
        version = entry.get("version")
        if not isinstance(version, str) or not version:
            skipped.append(f"`{label}`: no pinned version - skipped, never range-guessed")
            continue
        deps.append(_pinned_dep(str(name), "PyPI", version))
    return deps, skipped


def load_cargo_lock_doc(doc: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate a parsed Cargo.lock into pinned dep entries.

    Same contract as `load_package_lock_doc`. Only registry-sourced
    crates are checkable: a `registry+` source ties the name+version
    to the crates.io identity OSV/NVD records describe. Path and git
    sources are real dependencies but their registry identity would
    be a guess (a local crate may share a name with a published one),
    so they are skipped and recorded instead.
    """
    if not isinstance(doc, dict):
        raise ValueError("Cargo.lock must be a mapping")
    if not isinstance(doc.get("version"), int):
        raise ValueError("Cargo.lock needs an integer root `version`")
    packages = doc.get("package", [])
    if not isinstance(packages, list):
        raise ValueError("Cargo.lock `package` must be a list of tables")
    deps: list[dict[str, Any]] = []
    skipped: list[str] = []
    for i, entry in enumerate(packages):
        if not isinstance(entry, dict):
            skipped.append(f"package #{i}: not a mapping")
            continue
        name = entry.get("name")
        label = str(name) if name is not None else f"package #{i}"
        if not name:
            skipped.append(f"package #{i}: no name")
            continue
        version = entry.get("version")
        if not isinstance(version, str) or not version:
            skipped.append(f"`{label}`: no pinned version - skipped, never range-guessed")
            continue
        source = entry.get("source")
        if not (isinstance(source, str) and source.startswith("registry+")):
            skipped.append(
                f"`{label}`: source `{source}` is not a registry pin "
                "(path/git/workspace) - identity would be a guess"
            )
            continue
        deps.append(_pinned_dep(str(name), "crates.io", version))
    return deps, skipped


def _toml_module() -> Any:
    """stdlib tomllib (3.11+); on 3.10 refuse instead of adding a dependency."""
    try:
        import tomllib
    except ImportError:  # pragma: no cover - exercised only on Python 3.10
        raise ValueError(
            "TOML lockfiles (poetry.lock/Cargo.lock) need Python 3.11+ "
            "(stdlib tomllib); no new dependency was added for 3.10"
        ) from None
    return tomllib


def read_lockfile(path: str) -> tuple[list[dict[str, Any]], list[str], str]:
    """One lockfile from disk -> (dependencies, skipped, format).

    Format is detected from unambiguous structural markers, never
    from the filename: JSON with an integer `lockfileVersion` is npm;
    TOML with `lock-version` is poetry; TOML with an integer root
    `version` is Cargo. Anything else is refused with a clean error
    naming what was tried. Both branches share the SBOM-sized cap.
    """
    size = os.path.getsize(path)
    if size > MAX_LOCKFILE_BYTES:
        raise ValueError(f"lockfile is {size} bytes (limit {MAX_LOCKFILE_BYTES})")
    with open(path, "rb") as f:
        data = f.read()
    try:
        doc = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError):
        doc = None
    if isinstance(doc, dict):
        if isinstance(doc.get("lockfileVersion"), int):
            return (*load_package_lock_doc(doc), "npm")
        raise ValueError("valid JSON but no integer `lockfileVersion` - not a package-lock.json")
    tomllib = _toml_module()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"lockfile is not UTF-8 text: {e}") from None
    try:
        toml_doc = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"lockfile is neither npm JSON nor valid TOML: {e}") from None
    if "lock-version" in toml_doc:
        return (*load_poetry_lock_doc(toml_doc), "poetry")
    if isinstance(toml_doc.get("version"), int):
        return (*load_cargo_lock_doc(toml_doc), "cargo")
    raise ValueError(
        "TOML input with neither a poetry `lock-version` marker nor a Cargo "
        "root `version` - refusing to guess the lockfile format"
    )

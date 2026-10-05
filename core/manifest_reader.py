"""Package manifest readers - declared dependencies become checkable deps.

Five formats, one discipline: requirements.txt, pyproject.toml,
pom.xml, go.mod and Cargo.toml all normalize into the same dep
shapes the watchlist/SBOM/lockfile paths use (`{kind: package,
package, ecosystem, version}`) and feed
`core.risk.check.check_dependency` without touching matching
semantics. A pinned version is REQUIRED: entries without an exact
version - or whose identity would be a guess (unpinned ranges,
path/git/workspace sources, unresolvable property references) -
are skipped and recorded, never range-guessed, never name-guessed.

Manifests differ from lockfiles in one load-bearing way: they
declare intent, not resolved truth. A lockfile records what the
build produced; a manifest can say `django>=4.2` where the resolved
install was `4.2.13`. The reader honors that split instead of
guessing: a range is a real declaration with no checkable version,
so it is skipped with its reason, while an `==` pin in
requirements.txt, an exact PEP 621 dependency, a literal
`<version>` in pom.xml, a `vX.Y.Z` require in go.mod or an `=x.y.z`
req in Cargo.toml is the manifest's own exact-version statement and
becomes a checkable dep.

Size cap and malformed-input refusal reuse the SBOM reader's
policy. Format detection is structural, never by filename: pom.xml's
`<project>` root, pyproject's `[project]`/`[tool.poetry]` tables,
Cargo's `[package]`/`[workspace]` tables, go.mod's `module`
directive, requirements.txt pinned-line density. Anything the
markers cannot name is refused rather than guessed. No new
dependencies; no network. TOML parsing uses the stdlib `tomllib`
(Python 3.11+, matching CI); on 3.10 the TOML formats refuse with a
clean error instead of pulling a parser in.
"""

from __future__ import annotations

import os
import re
from typing import Any

from core import sbom_reader

#: Manifests share the SBOM reader's size cap - the same bounded-read
#: policy (real pom.xml and Cargo.toml files routinely run multi-MB),
#: not a second unbounded channel.
MAX_MANIFEST_BYTES = sbom_reader.MAX_SBOM_BYTES

#: PEP 508 name grammar - the start of every requirements.txt line
#: and PEP 621 dependency string.
_REQ_NAME_RE = re.compile(r"[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?")


def _pinned_dep(package: str, ecosystem: str, version: str) -> dict[str, Any]:
    """One pinned entry -> the exact shape watchlist/SBOM/lockfile deps use."""
    return {"kind": "package", "package": package, "ecosystem": ecosystem, "version": version}


def _toml_module() -> Any:
    """stdlib tomllib (3.11+); on 3.10 refuse instead of adding a dependency."""
    try:
        import tomllib
    except ImportError:  # pragma: no cover - exercised only on Python 3.10
        raise ValueError(
            "TOML manifests (pyproject.toml/Cargo.toml) need Python 3.11+ "
            "(stdlib tomllib); no new dependency was added for 3.10"
        ) from None
    return tomllib


def _strip_req_comment(line: str) -> str:
    """Drop a trailing ` # comment` (pip-compile style annotations)."""
    if " #" in line:
        return line.split(" #", 1)[0]
    return line


def _parse_pep508_requirement(line: str) -> tuple[dict[str, Any] | None, str]:
    """One requirement string -> (dep, None) or (None, skip reason).

    Accepts the pinned form `name==1.2.3` (extras and environment
    markers allowed); everything else - ranges, bare names, URLs,
    editable installs, local paths - is refused, never guessed.
    Always a 2-tuple so callers can unpack either leg safely.
    """
    text = line.strip()
    m = _REQ_NAME_RE.match(text)
    if m is None:
        return None, f"`{line}` does not start with a valid package name"
    name = text[: m.end()]
    rest = text[m.end() :].strip()
    if rest.startswith("["):
        end = rest.find("]")
        if end == -1:
            return None, f"`{line}`: unterminated extras list"
        rest = rest[end + 1 :].strip()
    if ";" in rest:
        # An environment marker gates the line's applicability to the
        # current interpreter, not the declared dependency itself -
        # the manifest still depends on the package. Drop the marker
        # and keep the requirement.
        rest = rest.rsplit(";", 1)[0].strip()
    if rest.startswith("=="):
        version = rest[2:].strip().strip(chr(34) + chr(39))
        if _exact_version(version):
            return _pinned_dep(name, "PyPI", version), ""
    return None, f"`{line}`: no `==` pin - skipped, never range-guessed"


def load_requirements_txt_doc(text: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Parse requirements.txt text into pinned dep entries.

    Returns (dependencies, skipped) - same contract as
    `sbom_reader.load_sbom_doc`. Comments, blank lines and pip
    options are skipped (options are recorded - `-r` includes and
    `-c` constraints expand to lines we never see, so refusing the
    option line keeps the accounting honest); unpinned/URL/editable/
    path entries are skipped and recorded with their reason.
    """
    deps: list[dict[str, Any]] = []
    skipped: list[str] = []
    for i, raw in enumerate(text.splitlines()):
        line = _strip_req_comment(raw.strip())
        if not line or line.startswith("#"):
            continue
        if line.startswith("-"):
            skipped.append(f"line {i + 1}: pip option `{line}` - not a dependency")
            continue
        dep, reason = _parse_pep508_requirement(line)
        if dep is None:
            skipped.append(f"line {i + 1}: {reason}")
        else:
            deps.append(dep)
    return deps, skipped


def _looks_like_requirements(text: str) -> bool:
    """Pinned-line density: at least one `name==version` line.

    The structural detector for requirements.txt after XML, go.mod
    and TOML declined: a file whose only structure is pinned
    requirement lines. Comments/options alone do NOT mark the
    format (they could be a stray txt); at least one real pin must
    be present. Reuses `_parse_pep508_requirement` - one grammar
    for detection and parsing, not two that can drift.
    """
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue
        dep, _ = _parse_pep508_requirement(_strip_req_comment(stripped))
        if dep is not None:
            return True
    return False


def _deps_from_pep508_list(items: Any, origin: str) -> tuple[list[dict[str, Any]], list[str]]:
    """PEP 621 dependency-string lists -> (deps, skipped)."""
    deps: list[dict[str, Any]] = []
    skipped: list[str] = []
    if not isinstance(items, list):
        return deps, [f"`{origin}` must be a list of dependency strings"]
    for i, item in enumerate(items):
        if not isinstance(item, str):
            skipped.append(f"`{origin}` entry #{i + 1}: not a string")
            continue
        dep, reason = _parse_pep508_requirement(item)
        if dep is None:
            skipped.append(f"`{origin}` entry #{i + 1}: {reason}")
        else:
            deps.append(dep)
    return deps, skipped


def _exact_version(v: str) -> bool:
    """True when `v` is an exact version literal (no range operators).

    A bare `1.2.3` IS exact in the manifest grammar (poetry writes
    exact constraints bare, cargo reqs accept `=1.2.3`); any range
    operator, wildcard or whitespace makes it not-a-pin.
    """
    v = v.strip()
    if not v or any(c.isspace() for c in v):
        return False
    return not re.search(r"[<>=!^~*,;#\[\]()\|]", v)


def _poetry_exact(constraint: str) -> str | None:
    """Poetry constraint -> the exact version it names, or None.

    Poetry spells exact requirements bare (`1.2.3`) or with an
    equality operator (`==1.2.3`, `=1.2.3` - both exact in
    poetry's constraint grammar); every other spelling (caret,
    tilde, ranges, wildcards) is a constraint the build resolves,
    not a pin the checker can use.
    """
    v = constraint.strip()
    if v.startswith("=="):
        v = v[2:].strip()
    elif v.startswith("="):
        v = v[1:].strip()
    if _exact_version(v):
        return v
    return None


def _deps_from_poetry_table(table: Any, origin: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Poetry dependency table -> (deps, skipped).

    A string value is a poetry version constraint - only exact
    spellings pin (bare `1.2.3`, `==1.2.3`, `=1.2.3`); ranges/
    carets/wildcards are skipped. A table value with a non-registry
    source (git/path/url) is skipped like the lockfile reader; a
    table with an exact `version` key pins. Poetry's main table
    always carries a `python` key - the interpreter constraint for
    the project itself, never a PyPI package - so it is skipped
    explicitly instead of inventing a `python` dependency.
    """
    deps: list[dict[str, Any]] = []
    skipped: list[str] = []
    if table is None:
        return deps, skipped
    if not isinstance(table, dict):
        return deps, [f"`{origin}` must be a mapping"]
    for name, spec in table.items():
        label = f"`{origin}.{name}`"
        if str(name) == "python" and origin == "tool.poetry.dependencies":
            skipped.append(f"{label}: the Python interpreter constraint, not a package")
            continue
        if isinstance(spec, str):
            v = _poetry_exact(spec)
            if v is not None:
                deps.append(_pinned_dep(str(name), "PyPI", v))
            else:
                skipped.append(
                    f"{label}: `{spec.strip()}` is a constraint, not a pin - "
                    "skipped, never range-guessed"
                )
        elif isinstance(spec, dict):
            if any(k in spec for k in ("git", "path", "url")):
                skipped.append(
                    f"{label}: non-registry source (git/path/url) - identity would be a guess"
                )
                continue
            version = spec.get("version")
            v = _poetry_exact(version) if isinstance(version, str) else None
            if v is None:
                skipped.append(f"{label}: no exact `version` - skipped, never guessed")
            else:
                deps.append(_pinned_dep(str(name), "PyPI", v))
        else:
            skipped.append(f"{label}: unsupported spec type {type(spec).__name__}")
    return deps, skipped


def load_pyproject_doc(doc: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Parse a pyproject.toml document into pinned dep entries.

    PEP 621 `[project]` tables first (dependencies +
    optional-dependencies groups); the legacy poetry
    `[tool.poetry]` layout (dependencies + group-dependencies) is
    read when PEP 621 is absent, so poetry-core projects still
    ingest. Zero pinned deps is valid state (the project declares no
    exact versions) - it yields zero deps plus skip lines, not an
    error.
    """
    if not isinstance(doc, dict):
        raise ValueError("pyproject must be a mapping")
    tool = doc.get("tool")
    has_project = isinstance(doc.get("project"), dict)
    has_poetry = isinstance(tool, dict) and isinstance(tool.get("poetry"), dict)
    if not has_project and not has_poetry:
        raise ValueError("pyproject needs a `[project]` (PEP 621) or `[tool.poetry]` table")
    deps: list[dict[str, Any]] = []
    skipped: list[str] = []
    if has_project:
        project = doc["project"]
        # An absent `dependencies` key is valid PEP 621 (the project
        # declares none); a present-but-malformed one is a skip line.
        if "dependencies" in project:
            d, s = _deps_from_pep508_list(project["dependencies"], "project.dependencies")
            deps.extend(d)
            skipped.extend(s)
        opt = project.get("optional-dependencies")
        if opt is not None:
            if not isinstance(opt, dict):
                skipped.append("`project.optional-dependencies` must be a mapping of group -> list")
            else:
                for group, items in opt.items():
                    d, s = _deps_from_pep508_list(items, f"project.optional-dependencies.{group}")
                    deps.extend(d)
                    skipped.extend(s)
    else:
        poetry = tool["poetry"]
        d, s = _deps_from_poetry_table(poetry.get("dependencies"), "tool.poetry.dependencies")
        deps.extend(d)
        skipped.extend(s)
        groups = poetry.get("group")
        if groups is not None:
            if not isinstance(groups, dict):
                skipped.append("`tool.poetry.group` must be a mapping of group -> table")
            else:
                for gname, gtable in groups.items():
                    if not isinstance(gtable, dict):
                        skipped.append(f"`tool.poetry.group.{gname}`: not a mapping")
                        continue
                    d, s = _deps_from_poetry_table(
                        gtable.get("dependencies"),
                        f"tool.poetry.group.{gname}.dependencies",
                    )
                    deps.extend(d)
                    skipped.extend(s)
        d, s = _deps_from_poetry_table(
            poetry.get("dev-dependencies"), "tool.poetry.dev-dependencies"
        )
        deps.extend(d)
        skipped.extend(s)
    return deps, skipped


def _local_name(tag: str) -> str:
    """Strip a namespace prefix (`{ns}tag` -> `tag`)."""
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _pom_properties(root: Any) -> dict[str, str]:
    """The pom's own `<properties>` table - property resolution source."""
    props: dict[str, str] = {}
    props_elem = root.find("properties")
    if props_elem is None:
        return props
    for child in props_elem:
        tag = _local_name(child.tag)
        if tag and child.text is not None:
            props[tag] = child.text.strip()
    return props


def _resolve_pom_version(raw: str, props: dict[str, str]) -> str | None:
    """One `<version>` text -> the literal it names, or None.

    Maven resolves `${property}` references from the pom's own
    `<properties>` table (build time resolves more - profiles,
    parent poms, CI overrides - which is exactly why unresolved
    references stay skips: the tool never guesses what a build would
    produce). `${revision}`/`${sha1}`/`${changelist}` are CI-friendly
    placeholders with no per-pom literal, so they never resolve.
    """
    if raw is None:
        return None
    text = raw.strip()
    m = re.match(r"^\$\{([A-Za-z0-9._-]+)\}$", text)
    if m is None:
        return text
    return props.get(m.group(1))


def load_pom_xml_doc(text: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Parse pom.xml text into pinned dep entries.

    Uses stdlib `xml.etree.ElementTree` - Maven POMs are plain XML.
    Only direct `<dependencies>` blocks (children of `<project>`,
    or inside `<profiles>`/`<build>` at depth 1, i.e. what Maven
    calls effective runtime deps of this project) are read;
    `<dependencyManagement>` blocks are the version template table,
    never a dep source. groupId + artifactId + a resolvable literal
    `<version>` -> one Maven dep in the colon form
    (`com.itextpdf:itext-core`) the catalog aliases and OSV/NVD
    records spell. A direct dep missing `<version>` whose
    groupId:artifactId IS in the managed table resolves to the
    managed literal - that is the table's purpose. `<scope>test</scope>`
    entries are skipped as not runtime deps. Unresolvable
    property refs are skipped, never guessed.
    """
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise ValueError(f"pom.xml is not parseable XML: {e}") from None
    if _local_name(root.tag) != "project":
        raise ValueError("pom.xml needs a `<project>` root element")
    properties = _pom_properties(root)
    # Collect dependency blocks classified by ancestor chain: direct
    # (project-level or profile/build-nested) vs managed.
    direct_blocks: list[Any] = []
    managed_blocks: list[Any] = []
    parent_of: dict[int, Any] = {}
    for parent in root.iter():
        for child in parent:
            parent_of[id(child)] = parent
    for block in (e for e in root.iter() if _local_name(e.tag) == "dependencies"):
        chain: list[Any] = []
        node = block
        while node is not None and node is not root:
            node = parent_of.get(id(node))
            if node is not None:
                chain.append(node)
        names = [_local_name(e.tag) for e in chain]
        if "dependencyManagement" in names:
            managed_blocks.append(block)
        elif any(n in ("plugin", "plugins", "reporting", "reportPlugin") for n in names):
            # plugin/reporting dependencies run build tools, not the
            # shipped artifact - not runtime identity.
            continue
        else:
            direct_blocks.append(block)
    if not direct_blocks and not managed_blocks:
        raise ValueError("pom.xml declares no `<dependencies>` block")
    # Managed table: groupId:artifactId -> resolved literal version.
    managed: dict[tuple[str, str], str] = {}
    for block in managed_blocks:
        for dep_elem in block.findall("dependency"):
            gid = dep_elem.findtext("groupId")
            aid = dep_elem.findtext("artifactId")
            ver = dep_elem.findtext("version")
            if gid is None or aid is None:
                continue
            key = (gid, aid)
            if key in managed:
                continue  # first wins; a conflict is a build concern, not ours
            resolved = _resolve_pom_version(ver, properties)
            if resolved:
                managed[key] = resolved
    deps: list[dict[str, Any]] = []
    skipped: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for block in direct_blocks:
        for dep_elem in block.findall("dependency"):
            gid = dep_elem.findtext("groupId")
            aid = dep_elem.findtext("artifactId")
            raw_ver = dep_elem.findtext("version")
            scope = dep_elem.findtext("scope")
            label = f"`{gid or chr(63)}:{aid or chr(63)}`"
            if gid is None or aid is None:
                skipped.append(f"{label}: missing groupId or artifactId")
                continue
            if scope == "test":
                skipped.append(f"{label}: test scope - not a runtime dependency")
                continue
            if raw_ver is None:
                managed_hit = managed.get((gid, aid))
                if managed_hit is not None:
                    raw_ver = managed_hit
                else:
                    skipped.append(
                        f"{label}: no `<version>` and no managed pin - skipped, never guessed"
                    )
                    continue
            ver = _resolve_pom_version(raw_ver, properties)
            if ver is None:
                skipped.append(
                    f"{label}: version property `{raw_ver}` - unresolvable without a build"
                )
                continue
            if (gid, aid, ver) in seen:
                continue
            seen.add((gid, aid, ver))
            deps.append(_pinned_dep(f"{gid}:{aid}", "Maven", ver))
    return deps, skipped


def load_go_mod_doc(text: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Parse go.mod text into pinned dep entries.

    `require` directives (single-line and the parenthesized block)
    pin `module-path vX.Y.Z` - the module path IS the Go identity
    (matching the golang purl namespace/name join the sbom reader
    maps). `// indirect` entries are real dependency edges Go itself
    records - they become deps. `replace` and `retract` directives
    are accounting-only (a local override is not an identity; a
    withdrawn version is not a dependency) and are skipped and
    recorded. An empty `require` block is valid state (the module
    declares nothing) - zero deps plus the block accounting, not an
    error. A go.mod with no `require` directive at all is refused:
    without it the module marker alone says nothing about deps.
    """
    deps: list[dict[str, Any]] = []
    skipped: list[str] = []
    in_require_block = False
    saw_require = False
    for i, raw in enumerate(text.splitlines()):
        stripped = raw.strip()
        if not stripped or stripped.startswith("//"):
            continue
        if in_require_block:
            if stripped.startswith(")"):
                in_require_block = False
                continue
            if stripped.startswith("require"):
                continue
            _read_go_require(stripped, deps, skipped, f"line {i + 1}")
            continue
        if stripped.startswith("require") and stripped.endswith("("):
            in_require_block = True
            saw_require = True
            continue
        if stripped.startswith("require "):
            saw_require = True
            _read_go_require(stripped[len("require ") :], deps, skipped, f"line {i + 1}")
            continue
        if stripped.startswith("replace"):
            skipped.append(f"line {i + 1}: `replace` directive - a local override, not an identity")
            continue
        if stripped.startswith("retract"):
            skipped.append(
                f"line {i + 1}: `retract` directive - version withdrawal, not a dependency"
            )
            continue
    if not saw_require:
        raise ValueError("go.mod declares no `require` directive")
    return deps, skipped


#: A full go module version: `v` + semver core (X.Y.Z, no leading
#: zeros), optional prerelease (a `v0.0.0-20240101120000-abcdef123456`
#: pseudo-version is the prerelease shape Go computes from a commit),
#: optional build metadata (`+incompatible` is build metadata). Go
#: require lines always carry a resolved full version; partials and
#: aliases never appear in a written go.mod.
_GO_VERSION_RE = re.compile(
    r"^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?"
    r"(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$"
)


def _exact_go_version(version: str) -> bool:
    """True for exact go.mod version spellings.

    `vX.Y.Z` release tags, `vX.Y.Z-rc1` prerelease tags, `v0.0.0-...`
    pseudo-versions Go computes from a commit, and `vX.Y.Z+incompatible`
    major-version escapes are all exact pins. Partials (`v1`, `v1.2`),
    ranges and aliases (`latest`) are not module versions the checker
    can pin - refused, never guessed.
    """
    return _GO_VERSION_RE.match(version) is not None


def _read_go_require(
    entry: str, deps: list[dict[str, Any]], skipped: list[str], origin: str
) -> None:
    """One go.mod require entry -> pinned dep or skip-and-record.

    The entry must carry `module-path vX.Y.Z`; a missing version or
    a non-`v` version is skipped, never guessed. The trailing `//
    indirect` comment carries no identity meaning - it is a real
    dependency edge Go itself recorded.
    """
    parts = entry.split()
    if len(parts) < 2:
        skipped.append(f"{origin}: `{entry}` - no version on the require line")
        return
    path, version = parts[0], parts[1]
    if not _exact_go_version(version):
        skipped.append(
            f"{origin}: `{path} {version}` - `{version}` is not a `vX.Y.Z` module version"
        )
        return
    deps.append(_pinned_dep(path, "Go", version))


def _cargo_spec_to_dep(name: str, spec: Any) -> tuple[dict[str, Any] | None, str | None]:
    """One Cargo dependency spec -> (dep, None) or (None, reason).

    String specs: only `=x.y.z` is the exact req - a bare `x.y.z`
    is caret semantics in cargo, a floor not a pin, so ranges and
    bare reqs are skipped, never range-guessed. Table specs:
    `workspace = true` resolves only at build time; path/git sources
    are identity guesses. In the table form the `version` key follows
    the same rule: a bare `x.y.z` is caret semantics (the Cargo
    Book's default requirement strategy), so only `version = "=x.y.z"`
    pins - never the bare spelling.
    """
    if isinstance(spec, str):
        v = spec.strip()
        if v.startswith("="):
            v = v[1:].strip()
            if _exact_version(v):
                return _pinned_dep(name, "crates.io", v), None
            return None, "exact req with a non-literal version"
        # A bare `x.y.z` req is caret semantics (`^x.y.z`) in cargo -
        # a floor, not a pin; only the explicit `=` req pins.
        return (
            None,
            f"`{v}` is a range req (bare means caret), "
            "not an exact pin - skipped, never range-guessed",
        )
    if isinstance(spec, dict):
        if spec.get("workspace") is True:
            return (
                None,
                "workspace inheritance (`workspace = true`) - resolves only at build time",
            )
        if "path" in spec or "git" in spec:
            return None, "non-registry source (path/git) - identity would be a guess"
        version = spec.get("version")
        if not isinstance(version, str):
            return None, "no exact `version` key - skipped, never guessed"
        v = version.strip()
        # Same rule as the string form: a bare `x.y.z` in the version
        # key is caret semantics (`^x.y.z`) - the Cargo Book's default
        # requirement strategy - so only the explicit `=` req pins.
        if not v.startswith("="):
            return (
                None,
                f"`{v}` in `version` is a caret req (bare means caret), "
                "not an exact pin - skipped, never range-guessed",
            )
        v = v[1:].strip()
        if not _exact_version(v):
            return None, "exact req with a non-literal version"
        return _pinned_dep(name, "crates.io", v), None
    return None, f"unsupported spec type {type(spec).__name__}"


def load_cargo_toml_doc(doc: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Parse a Cargo.toml document into pinned dep entries.

    `[dependencies]` / `[dev-dependencies]` / `[build-dependencies]`
    are read; path/git/workspace specs are skipped with reasons,
    exactly like the lockfile reader's discipline. A Cargo.toml
    with none of the three tables is refused (a manifest declaring
    nothing) rather than read as empty.
    """
    if not isinstance(doc, dict):
        raise ValueError("Cargo.toml must be a mapping")
    has_package = isinstance(doc.get("package"), dict)
    has_workspace = isinstance(doc.get("workspace"), dict)
    if not has_package and not has_workspace:
        raise ValueError("Cargo.toml needs a `[package]` (or `[workspace]`) table")
    deps: list[dict[str, Any]] = []
    skipped: list[str] = []
    saw_table = False
    for section in ("dependencies", "dev-dependencies", "build-dependencies"):
        table = doc.get(section)
        if table is None:
            continue
        saw_table = True
        if not isinstance(table, dict):
            skipped.append(f"`[{section}]` must be a mapping")
            continue
        for name, spec in table.items():
            dep, reason = _cargo_spec_to_dep(str(name), spec)
            if dep is None:
                skipped.append(f"`[{section}].{name}`: {reason}")
            else:
                deps.append(dep)
    if not saw_table:
        raise ValueError(
            "Cargo.toml declares no `[dependencies]`/`[dev-dependencies]`/"
            "`[build-dependencies]` table"
        )
    return deps, skipped


def _looks_like_go_mod(text: str) -> bool:
    """True when the text opens with a go.mod `module` directive.

    go.mod is not TOML (no `=` between key and value), so it must be
    detected before the TOML attempt: a first non-comment line of
    `module <path>` is the unambiguous go.mod marker.
    """
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("//"):
            continue
        return stripped.startswith("module ")
    return False


def read_manifest(path: str) -> tuple[list[dict[str, Any]], list[str], str]:
    """One manifest from disk -> (dependencies, skipped, format).

    Format is detected from unambiguous structural markers, never
    from the filename: a leading `<?xml`/`<project` element is
    pom.xml; a first directive `module` is go.mod; a parseable TOML
    doc with `[project]`/`[tool.poetry]` is pyproject and with
    `[package]`/`[workspace]` is Cargo; pinned-line density is
    requirements.txt. Anything the markers cannot name is refused
    with a clean error naming what was tried - never guessed. The
    read is bounded by the SBOM cap (multi-MB pom.xml/Cargo.toml
    are legitimate; the cap keeps reads bounded, not unbounded).
    """
    size = os.path.getsize(path)
    if size > MAX_MANIFEST_BYTES:
        raise ValueError(f"manifest is {size} bytes (limit {MAX_MANIFEST_BYTES})")
    with open(path, "rb") as f:
        data = f.read()
    try:
        # utf-8-sig = utf-8 that tolerates a leading BOM: the BOM is
        # encoding metadata, not content, but `lstrip()` would leave
        # it in place and break every structural marker below.
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise ValueError(f"manifest is not UTF-8 text: {e}") from None
    stripped = text.lstrip()
    if stripped.startswith("<?xml") or stripped.startswith("<project"):
        return (*load_pom_xml_doc(text), "pom")
    if _looks_like_go_mod(text):
        return (*load_go_mod_doc(text), "go")
    if "[" in stripped:
        tomllib = _toml_module()
        try:
            toml_doc = tomllib.loads(text)
        except tomllib.TOMLDecodeError:
            toml_doc = None
        if isinstance(toml_doc, dict):
            tool = toml_doc.get("tool")
            if isinstance(toml_doc.get("project"), dict) or (
                isinstance(tool, dict) and isinstance(tool.get("poetry"), dict)
            ):
                return (*load_pyproject_doc(toml_doc), "pyproject")
            if isinstance(toml_doc.get("package"), dict) or isinstance(
                toml_doc.get("workspace"), dict
            ):
                return (*load_cargo_toml_doc(toml_doc), "cargo")
    if _looks_like_requirements(text):
        return (*load_requirements_txt_doc(text), "requirements")
    raise ValueError(
        "input has none of the manifest structural markers "
        "(pom.xml `<project>` root, go.mod `module` directive, pyproject "
        "`[project]`/`[tool.poetry]` tables, Cargo `[package]`/`[workspace]` "
        "tables, or requirements.txt pinned lines) - refusing to guess the format"
    )

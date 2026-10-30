"""Policy R: the existing-representation baseline (REGISTRATION.md §2).

R asks what TR-2026-01's model adds over formats that already exist,
read with care. Each event is re-encoded from its primary sources alone
as an OSV record or OpenVEX statements, under the written rules of
``representations/ENCODING.md``, and frozen with its SHA-256 before any
policy runs. R reads only that encoding, never the replayed event's
typed scope:

- identity is exact purl equality. The dependency's purl is built by
  the fixed rule of ENCODING.md §4, the same rule the encoder follows;
  there is no curated catalogue and no name matching;
- an OSV range is evaluated with the pinned ecosystem comparators that
  baseline V uses (``ecosystem_versions``; PyPI with ``packaging``); a
  version a comparator cannot decide is unresolved;
- *affected*: an OSV range (or ``versions`` entry) for the dependency's
  package includes its version, or an ``affected`` statement names its
  exact purl;
- *not affected*: only an OSV record for the same package whose ranges
  exclude the version, or a ``not_affected`` statement naming the exact
  purl;
- everything else, including an event with no encoding, is unresolved.

R has no typed namespace elements, no completeness declaration, no
freshness bound and no curated identity.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "conformance"))

import oracle  # noqa: E402
from packaging.version import InvalidVersion, Version  # noqa: E402

from core.schema.models import OSSEvent  # noqa: E402

HERE = Path(__file__).resolve().parent

#: OpenVEX statuses the encoder may write (ENCODING.md §6).
VEX_STATUSES = ("affected", "not_affected", "under_investigation")
#: Encoding-loss codes (ENCODING.md §7).
LOSS_CODES = ("L1", "L2", "L3", "L4", "L5", "L6", "L7")

#: Source-code hosts whose repositories are ``pkg:<type>/<owner>/<repo>``.
_SOURCE_HOSTS = {"github.com": "github", "gitlab.com": "gitlab", "bitbucket.org": "bitbucket"}
#: Dependency or OSV ecosystem -> purl type (ENCODING.md §4).
_PURL_TYPES = {"pypi": "pypi", "npm": "npm", "maven": "maven", "go": "golang", "golang": "golang"}
_NUMERIC = re.compile(r"\d+(?:\.\d+)*")

#: The run's encodings by replayed event id, installed by ``use_encodings``.
_ENCODINGS: dict[str, dict[str, Any]] = {}
#: Pinned bridges for npm, Go and Maven, installed by ``use_comparators``.
_BRIDGES: Any = None


def use_encodings(encodings: dict[str, dict[str, Any]] | None) -> None:
    """Install (or, with None, remove) the run's frozen encodings by event id."""
    global _ENCODINGS
    _ENCODINGS = dict(encodings or {})


def use_comparators(comparators: Any) -> None:
    """Install (or, with None, remove) the run's pinned ecosystem bridges."""
    global _BRIDGES
    _BRIDGES = comparators


# --- frozen encodings --------------------------------------------------------


def load_encoding(spec: dict[str, Any], event: str) -> dict[str, Any]:
    """An event's encoding file, verified against its recorded SHA-256.

    ``spec`` is the dataset event's ``encoding`` entry: ``file`` (relative
    to ``evaluation/``) and ``sha256``. A mismatch or a malformed encoding
    fails closed: an encoding revised after freezing is never read.
    """
    raw = (HERE / spec["file"]).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != spec["sha256"]:
        raise ValueError(f"{event}: encoding SHA-256 {digest} does not match {spec['sha256']}")
    encoding = json.loads(raw)
    problems = validate_encoding(encoding)
    if encoding.get("event") != event:
        problems.append(f"encodes {encoding.get('event')!r}, not {event!r}")
    if problems:
        raise ValueError(f"{event}: malformed encoding: {'; '.join(problems)}")
    return encoding


def validate_encoding(encoding: dict[str, Any]) -> list[str]:
    """The structural rules of ENCODING.md §8; an empty list is valid."""
    problems = []
    for key in ("event", "encoder", "encoded_on", "sources", "osv", "openvex", "loss"):
        if key not in encoding:
            problems.append(f"missing {key}")
    if problems:
        return problems
    if not encoding["sources"]:
        problems.append("no primary source")
    for record in encoding["osv"]:
        for affected in record.get("affected", []):
            package = affected.get("package", {})
            if _package_key(package.get("ecosystem", ""), package.get("name", "")) is None:
                problems.append(f"OSV package {package} has no supported purl type")
            for rng in affected.get("ranges", []):
                if rng.get("type") not in ("ECOSYSTEM", "SEMVER"):
                    problems.append(f"OSV range type {rng.get('type')!r} is not read")
    vex = encoding["openvex"]
    for statement in vex.get("statements", []) if vex else []:
        status = statement.get("status")
        if status not in VEX_STATUSES:
            problems.append(f"OpenVEX status {status!r}")
        if status == "not_affected" and not (
            statement.get("justification") or statement.get("impact_statement")
        ):
            problems.append("not_affected without a justification or impact statement")
        for product in statement.get("products", []):
            if not str(product.get("@id", "")).startswith("pkg:"):
                problems.append(f"OpenVEX product {product.get('@id')!r} is not a purl")
    for entry in encoding["loss"]:
        if entry.get("code") not in LOSS_CODES or not entry.get("what"):
            problems.append(f"loss entry {entry} needs a code in {LOSS_CODES} and a description")
    return problems


# --- purls: the one construction rule (ENCODING.md §4) ------------------------


def _package_key(ecosystem: str, name: str) -> str | None:
    """The versionless purl of a package, or None for an unsupported ecosystem."""
    eco = str(ecosystem or "").strip().lower()
    purl_type = _PURL_TYPES.get(eco)
    if purl_type is None or not name:
        return None
    _, key = oracle.canonical_package("go" if purl_type == "golang" else eco, name)
    return f"pkg:{purl_type}/" + "/".join(quote(part, safe="") for part in key.split("/"))


def dependency_purl(dep: dict[str, Any]) -> str | None:
    """The dependency's purl, with its version, or None if it has none."""
    if dep["kind"] == "image":
        ref = oracle.parse_ref(str(dep["ref"]))
        host = _SOURCE_HOSTS.get(ref.registry)
        if host is not None:
            return f"pkg:{host}/{ref.namespace}/{ref.name}" if ref.namespace else None
        version = ref.digest or ref.tag or "latest"
        path = f"{ref.namespace}/{ref.name}" if ref.namespace else ref.name
        qualifier = "" if ref.registry == "docker.io" else f"?repository_url={ref.registry}"
        return f"pkg:docker/{path}@{quote(version, safe='')}{qualifier}"
    key = _package_key(str(dep.get("ecosystem") or ""), str(dep.get("package") or ""))
    if key is None:
        return None
    version = dep.get("version")
    return f"{key}@{quote(str(version), safe='')}" if version else key


# --- versions: the pinned comparators -------------------------------------------


def _compare(ecosystem: str, a: str, b: str) -> int | None:
    """-1, 0 or 1 under the ecosystem's comparator; None when undecidable."""
    if ecosystem == "pypi":
        try:
            x, y = Version(a), Version(b)
        except InvalidVersion:
            return None
        return (x > y) - (x < y)
    if _BRIDGES is not None and _BRIDGES.supports(ecosystem):
        return _BRIDGES.compare(ecosystem, a, b)
    # No pinned comparator: plain dotted numbers only, as baseline V.
    if not (_NUMERIC.fullmatch(a) and _NUMERIC.fullmatch(b)):
        return None
    x, y = [int(n) for n in a.split(".")], [int(n) for n in b.split(".")]
    width = max(len(x), len(y))
    x, y = x + [0] * (width - len(x)), y + [0] * (width - len(y))
    return (x > y) - (x < y)


def _in_range(version: str, rng: dict[str, Any], ecosystem: str) -> bool | None:
    """OSV range evaluation over events listed in ascending order (ENCODING.md §5)."""
    if rng.get("type") not in ("ECOSYSTEM", "SEMVER"):
        return None
    inside = False
    for event in rng.get("events", []):
        if "introduced" in event:
            if event["introduced"] == "0":
                inside = True
                continue
            c = _compare(ecosystem, version, event["introduced"])
            if c is None:
                return None
            inside = inside or c >= 0
        elif "fixed" in event or "last_affected" in event:
            bound = event.get("fixed", event.get("last_affected"))
            c = _compare(ecosystem, version, bound)
            if c is None:
                return None
            if c > 0 or (c == 0 and "fixed" in event):
                inside = False
    return inside


# --- reading one encoding -------------------------------------------------------


def _from_osv(dep: dict[str, Any], records: list[dict[str, Any]]) -> set[str]:
    if dep["kind"] == "image":
        return set()
    ecosystem = str(dep.get("ecosystem") or "").strip().lower()
    key = _package_key(ecosystem, str(dep.get("package") or ""))
    if key is None:
        return set()
    ecosystem = "go" if _PURL_TYPES[ecosystem] == "golang" else ecosystem
    version = dep.get("version")
    found: set[str] = set()
    for record in records:
        if record.get("withdrawn"):
            continue
        for affected in record.get("affected", []):
            package = affected.get("package", {})
            if _package_key(package.get("ecosystem", ""), package.get("name", "")) != key:
                continue
            ranges, versions = affected.get("ranges", []), affected.get("versions", [])
            if not version or not (ranges or versions):
                found.add("unresolved")
                continue
            if str(version) in versions:
                found.add("affected")
                continue
            inside = {_in_range(str(version), r, ecosystem) for r in ranges}
            if True in inside:
                found.add("affected")
            elif None in inside:
                found.add("unresolved")
            else:
                found.add("cleared")
    return found


_VEX_OUTCOME = {"affected": "affected", "not_affected": "cleared"}


def _from_vex(dep: dict[str, Any], document: dict[str, Any] | None) -> set[str]:
    purl = dependency_purl(dep)
    if purl is None or not document:
        return set()
    return {
        _VEX_OUTCOME.get(statement.get("status"), "unresolved")
        for statement in document.get("statements", [])
        if purl in {p.get("@id") for p in statement.get("products", [])}
    }


def per_event(dep: dict[str, Any], encoding: dict[str, Any] | None) -> str:
    """One event's encoding -> affected | cleared | unresolved."""
    if encoding is None:
        return "unresolved"
    found = _from_osv(dep, encoding["osv"]) | _from_vex(dep, encoding["openvex"])
    for outcome in ("affected", "unresolved", "cleared"):
        if outcome in found:
            return outcome
    return "unresolved"


def existing_representation(
    dep: dict[str, Any], events: list[OSSEvent], **_: Any
) -> dict[str, Any]:
    """Policy R over every current event, summarised as V's (TR Table 8)."""
    current = [e for e in events if e.is_current_record()]
    if not current:
        return {"outcome": "no_association", "encoded": True, "encoding_loss": False}
    encodings = [_ENCODINGS.get(e.id) for e in current]
    outcomes = {per_event(dep, enc) for enc in encodings}
    outcome = next(o for o in ("affected", "unresolved", "cleared") if o in outcomes)
    return {
        "outcome": outcome,
        "encoded": all(enc is not None for enc in encodings),
        "encoding_loss": any(enc is None or enc["loss"] for enc in encodings),
    }

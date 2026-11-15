"""Dependency confusion: does a public package carry one of your private names? (T-A3).

An installer that consults the public registry as well as a private one may
resolve a public package with an internal package's name instead of the
internal one (threat T3, Birsan 2021). The user lists the private names; this
check asks the public registry about each, and only those. Nothing is
inferred about names the user did not list.

The list is a text file, by default ``.openpulse/private-packages.txt``
under the project root, one ``ecosystem:name`` per line::

    # comments and blank lines are ignored
    PyPI:acme-billing
    npm:@acme/ui-kit

T-F1 records:

- a public package has the name: SUSPICIOUS_INCONCLUSIVE. If you did not
  publish it, an installer may pick it instead of yours;
- no public package has it: MISSING_EVIDENCE. The name is unclaimed, which
  also means anyone can still register it;
- the registry gave no usable answer, offline, budget: NOT_PERFORMED.

Names are validated against the registry grammars before any request; a
bad line is skipped by number and its text is never echoed (T-F3). Nothing
here feeds a verdict.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from core.registry_existence import (
    _NPM_NAME,
    _PYPI_NAME,
    MISSING_EVIDENCE,
    NOT_PERFORMED,
    SUSPICIOUS_INCONCLUSIVE,
    VERIFIED_FAILURE,
    VERIFIED_RELATIONSHIP,
    _now,
    ecosystem_of,
)

CHECK = "dependency_confusion"
DEFAULT_LIST = Path(".openpulse") / "private-packages.txt"
MAX_LIST_BYTES = 256 * 1024
MAX_ENTRIES = 500

_STATEMENTS = {
    SUSPICIOUS_INCONCLUSIVE: (
        "a public package on {host} has this private name at {at}; if you did not publish "
        "it, an installer that consults the public registry may resolve it instead of yours"
    ),
    MISSING_EVIDENCE: (
        "no public package on {host} has this private name at {at}; the name is unclaimed, "
        "so anyone can still register it"
    ),
    NOT_PERFORMED: "dependency confusion not checked: {why}",
}
_WHY = {
    "no_list": "no private-name list is configured",
    "not_listed": "the package is not on the private-name list",
    "unsupported": "checked for PyPI and npm packages only",
    "offline": "live lookups are off",
    "budget": "the session lookup budget is spent",
    "unreachable": "the public registry gave no usable answer",
}
_HOSTS = {"PyPI": "pypi.org", "npm": "registry.npmjs.org"}


def normalize(ecosystem: str, name: str) -> str:
    """The registry's own identity for a name: PEP 503 for PyPI, lowercase for npm."""
    return re.sub(r"[-_.]+", "-", name).lower() if ecosystem == "PyPI" else name.lower()


def parse(text: str) -> tuple[frozenset[tuple[str, str]], list[str]]:
    """({(ecosystem, normalized name)}, skip messages) from list text."""
    names: set[tuple[str, str]] = set()
    skipped: list[str] = []
    for number, line in enumerate(text.splitlines(), 1):
        entry = line.split("#", 1)[0].strip()
        if not entry:
            continue
        ecosystem, _, name = entry.partition(":")
        eco = ecosystem_of(ecosystem)
        grammar = _PYPI_NAME if eco == "PyPI" else _NPM_NAME
        if eco is None or not grammar.fullmatch(name if eco == "PyPI" else name.lower()):
            skipped.append(f"line {number}: not ecosystem:name for PyPI or npm - skipped")
            continue
        if len(names) >= MAX_ENTRIES:
            skipped.append(f"line {number}: more than {MAX_ENTRIES} entries - skipped")
            continue
        names.add((eco, normalize(eco, name)))
    return frozenset(names), skipped


def load(path: str | Path) -> tuple[frozenset[tuple[str, str]], list[str]]:
    """Read a list file (bounded). A missing file is an empty list, not an error."""
    from core.bounded_io import read_text

    if not Path(path).is_file():
        return frozenset(), []
    return parse(read_text(str(path), MAX_LIST_BYTES, "private-name list"))


def listed(names: frozenset[tuple[str, str]], ecosystem: str | None, name: str) -> bool:
    eco = ecosystem_of(ecosystem)
    return eco is not None and (eco, normalize(eco, name)) in names


def not_performed(why: str) -> dict[str, Any]:
    return _record(NOT_PERFORMED, _now(), why=why)


def from_existence(ecosystem: str, existence: list[dict[str, Any]]) -> dict[str, Any]:
    """Map a package-level registry existence record (T-A1) to this check."""
    record = existence[0] if existence else {}
    status = record.get("status")
    at = str(record.get("checked_at") or _now())
    host = _HOSTS.get(ecosystem, "")
    if status == VERIFIED_RELATIONSHIP:
        return _record(SUSPICIOUS_INCONCLUSIVE, at, host=host, source=record.get("source"))
    if status == VERIFIED_FAILURE:
        return _record(MISSING_EVIDENCE, at, host=host, source=record.get("source"))
    return _record(NOT_PERFORMED, at, why="unreachable")


def _record(status: str, at: str, *, host: str = "", why: str = "", **evidence: Any):
    return {
        "check": CHECK,
        "status": status,
        "statement": _STATEMENTS[status].format(host=host, at=at, why=_WHY.get(why, "")),
        "checked_at": at,
        "evidence": evidence,
    }


__all__ = [
    "CHECK",
    "DEFAULT_LIST",
    "from_existence",
    "listed",
    "load",
    "normalize",
    "not_performed",
    "parse",
]

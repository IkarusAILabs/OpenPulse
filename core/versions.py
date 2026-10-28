"""Version applicability — explicit, conservative, dependency-free.

Evaluates OSV range events (introduced/fixed/last_affected) and NVD
CPE range attributes (versionStart/EndIncluding/Excluding) plus exact
versions. Returns True/False, or None when applicability cannot be
determined — uncertainty never becomes a stronger claim.

Not a universal solver: numeric-core comparison with documented
best-effort prerelease handling. Ecosystems with exotic schemes fall
back to None rather than a guessed answer.
"""

from __future__ import annotations

import re
from typing import Any

_PRE = {
    "dev": -4,
    "a": -3,
    "alpha": -3,
    "b": -2,
    "beta": -2,
    "rc": -1,
    "c": -1,
    "pre": -1,
    "preview": -1,
}

# Ecosystem schemes OpenPulse understands. Anything else (apk/rpm
# suffixes, distro tags, date revisions) is UNKNOWN — never guessed.
KNOWN_SCHEMES = ("generic", "semver", "pep440")


def detect_scheme(version: str) -> str:
    """generic: leading numeric core + optional known prerelease marker.
    Everything else (distro/build suffixes, unknown alphas) is unknown."""
    tokens = re.findall(r"\d+|[a-z]+", str(version).lower().lstrip("v"))
    if not tokens or not tokens[0].isdigit():
        return "unknown"
    for token in tokens:
        if not token.isdigit() and token not in _PRE:
            return "unknown"
    return "generic"


def _key(version: str) -> tuple[tuple[int, ...], int] | None:
    """(numeric core, prerelease rank); None when no digits at all."""
    tokens = re.findall(r"\d+|[a-z]+", str(version).lower())
    nums: list[int] = []
    for token in tokens:
        if token.isdigit():
            nums.append(int(token))
        else:
            break
    if not nums:
        return None
    rank = 0
    for token in tokens[len(nums) :]:
        if not token.isdigit() and token in _PRE:
            rank = _PRE[token]
            break
    return (tuple(nums), rank)


def compare(a: str, b: str, scheme: str | None = None) -> int | None:
    """-1/0/1, or None when either side is unparseable or not generic.

    An explicit unsupported `scheme` forces None; otherwise both sides
    must detect as generic (unknown distro/build suffixes are not
    comparable — never guess).
    """
    if scheme is not None and scheme not in KNOWN_SCHEMES:
        return None
    if detect_scheme(a) != "generic" or detect_scheme(b) != "generic":
        return None
    ka, kb = _key(a), _key(b)
    if ka is None or kb is None:
        return None
    (na, ra), (nb, rb) = ka, kb
    length = max(len(na), len(nb))
    na += (0,) * (length - len(na))
    nb += (0,) * (length - len(nb))
    if na != nb:
        return -1 if na < nb else 1
    if ra != rb:
        return -1 if ra < rb else 1
    return 0


def in_release_line(version: str, line: str) -> bool | None:
    """Is ``version`` the release line ``line`` or a release within it?

    Event version scopes name release lines (endoflife.date cycles such as
    ``4.2``, ``13``, ``18``), while dependencies pin releases (``4.2.11``,
    ``13.5``). A line covers every version whose leading segments equal
    it: ``4.2`` covers ``4.2.11`` but not ``4.20.1``. None when either side
    is not comparable - the caller must report that as not established,
    never as outside the scope.
    """
    exact = compare(str(version), str(line))
    if exact is None:
        return None
    if exact == 0:
        return True
    width = len(str(line).split("."))
    head = ".".join(str(version).split(".")[:width])
    within = compare(head, str(line))
    return None if within is None else within == 0


def satisfies(version: str, constraint: dict[str, Any], scheme: str | None = None) -> bool | None:
    """One range constraint (OSV or CPE style) against a version."""
    if not constraint:
        return None
    lower: list[tuple[str, bool]] = []  # (bound, inclusive)
    upper: list[tuple[str, bool]] = []
    if "introduced" in constraint:
        introduced = constraint["introduced"]
        if introduced not in ("0", "0.0", ""):
            lower.append((introduced, True))
    if "versionStartIncluding" in constraint:
        lower.append((constraint["versionStartIncluding"], True))
    if "versionStartExcluding" in constraint:
        lower.append((constraint["versionStartExcluding"], False))
    if "fixed" in constraint:
        upper.append((constraint["fixed"], False))
    if "last_affected" in constraint:
        upper.append((constraint["last_affected"], True))
    if "versionEndIncluding" in constraint:
        upper.append((constraint["versionEndIncluding"], True))
    if "versionEndExcluding" in constraint:
        upper.append((constraint["versionEndExcluding"], False))
    if "exact" in constraint:
        result = compare(version, constraint["exact"], scheme)
        return result == 0 if result is not None else None
    if not lower and not upper:
        return None
    for bound, inclusive in lower:
        result = compare(version, bound, scheme)
        if result is None:
            return None
        if result < 0 or (result == 0 and not inclusive):
            return False
    for bound, inclusive in upper:
        result = compare(version, bound, scheme)
        if result is None:
            return None
        if result > 0 or (result == 0 and not inclusive):
            return False
    return True


def osv_applicable(
    version: str | None, affected: dict[str, Any], scheme: str | None = None
) -> bool | None:
    """OSV affected entry vs a deployed version."""
    if not version:
        return None
    for known in affected.get("versions", []) or []:
        if compare(version, str(known), scheme) == 0:
            return True
    ranges = affected.get("ranges", []) or []
    if not ranges:
        return None
    undecided = False
    for rng in ranges:
        result = _osv_range(version, rng, scheme)
        if result is True:
            return True
        if result is None:
            undecided = True
    return None if undecided else False


#: OSV range types whose events are versions. GIT ranges name commits
#: and need commit-graph reasoning: always undetermined here.
_OSV_VERSION_RANGES = ("SEMVER", "ECOSYSTEM")
_OSV_ZERO = ("0", "0.0", "")


def _osv_range(version: str, rng: dict[str, Any], scheme: str | None) -> bool | None:
    """One OSV range: a UNION of intervals, per the OSV evaluation rule.

    Events are sorted by version and walked in order: ``introduced``
    opens an interval, ``fixed`` (exclusive) and ``last_affected``
    (inclusive) close it, so ``introduced 1.0, fixed 1.2, introduced
    2.0, fixed 2.3`` covers [1.0, 1.2) and [2.0, 2.3). A version at or
    past a ``limit`` is undetermined (never a clearance), as is any
    event or range type that cannot be compared.
    """
    if str(rng.get("type") or "ECOSYSTEM").upper() not in _OSV_VERSION_RANGES:
        return None
    keyed: list[tuple[str, str]] = []
    for event in rng.get("events", []) or []:
        for key, value in event.items():
            if key in ("introduced", "fixed", "last_affected", "limit"):
                keyed.append((key, str(value)))
    if not keyed:
        return None
    for key, value in keyed:
        if key == "limit":
            below = compare(version, value, scheme)
            if below is None or below >= 0:
                return None
    walk = [(k, v) for k, v in keyed if k != "limit"]
    if not any(k == "introduced" for k, _ in walk):
        # Malformed but seen in the wild: a range with only a fix. Read
        # it as open from the start (the lenient pre-walk behavior), so
        # a missing bound can never become a clearance.
        walk.insert(0, ("introduced", "0"))
    positions: list[tuple[int, int, str]] = []  # (version vs event, order, kind)
    for order, (key, value) in enumerate(walk):
        if key == "introduced" and value in _OSV_ZERO:
            positions.append((1, order, key))  # version is past "0" by definition
            continue
        result = compare(version, value, scheme)
        if result is None:
            return None
        positions.append((result, order, key))
    # Sorted walk without sorting the events themselves: an event
    # applies once the version has reached it (introduced/fixed: >=;
    # last_affected: >). The latest-applying event in version order
    # decides, so sort the applying events by their own version.
    applying = [
        (key, walk[order][1])
        for result, order, key in positions
        if (result > 0) or (result == 0 and key != "last_affected")
    ]
    if not applying:
        return False
    latest_key = _latest_event(applying, scheme)
    if latest_key is None:
        return None
    return latest_key == "introduced"


def _latest_event(applying: list[tuple[str, str]], scheme: str | None) -> str | None:
    """Kind of the highest-versioned applying event; None if not comparable.

    Ties between an opening and a closing event at the same version
    resolve to the closing one (a fix at X wins over an introduction
    at X, matching OSV's sorted-order rule where both apply).
    """
    best_key, best_value = applying[0]
    for key, value in applying[1:]:
        if best_value in _OSV_ZERO and best_key == "introduced":
            best_key, best_value = key, value
            continue
        if value in _OSV_ZERO and key == "introduced":
            continue
        order = compare(value, best_value, scheme)
        if order is None:
            return None
        if order > 0 or (order == 0 and key != "introduced"):
            best_key, best_value = key, value
    return best_key


def cpe_applicable(
    version: str | None, cpe: dict[str, Any], scheme: str | None = None
) -> bool | None:
    """NVD CPE match entry vs a deployed version."""
    if cpe.get("vulnerable") is False:
        return False
    if not version:
        return None
    constraint = {
        k: cpe[k]
        for k in (
            "versionStartIncluding",
            "versionStartExcluding",
            "versionEndIncluding",
            "versionEndExcluding",
        )
        if k in cpe
    }
    if constraint:
        return satisfies(version, constraint, scheme)
    exact = _cpe_version(cpe.get("criteria", ""))
    if exact and exact not in ("*", "-"):
        result = compare(version, exact, scheme)
        return result == 0 if result is not None else None
    return None


def _cpe_version(criteria: str) -> str:
    parts = str(criteria).split(":")
    if len(parts) >= 6 and parts[0] == "cpe" and parts[1] == "2.3":
        return parts[5]
    return ""

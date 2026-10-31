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
# "generic"/"pep440" use the closed generic grammar, whose orderings
# agree with PEP 440 on every form it accepts; "semver" is SemVer 2.0
# precedence; "numeric" accepts plain dotted numbers only.
KNOWN_SCHEMES = ("generic", "semver", "pep440", "numeric")

#: OSV ``ECOSYSTEM`` ranges are ordered by their ecosystem's own rules.
#: Only ecosystems whose ordering one of our schemes reproduces get it;
#: every other ecosystem (Maven, Debian, RubyGems, ...) or a missing one
#: falls back to "numeric" (TR-2026-01 D11).
_ECOSYSTEM_SCHEMES = {
    "pypi": "pep440",
    "npm": "semver",
    "go": "semver",
    "crates.io": "semver",
}


#: Epoch separators: Debian/RPM ``1:2.3`` and PEP 440 ``1!2.3``. An
#: epoch outranks every release number, so reading it as one more
#: dotted segment (``1.2.3``) inverts orderings -- never comparable.
_EPOCH_SEPARATORS = (":", "!")


#: The whole generic grammar: a dotted numeric core, then at most one
#: known prerelease marker with an optional number (``2.0.0-rc.1``,
#: ``1.0b2``). Anything else is unknown, in particular a bare numeric
#: suffix: SemVer ``1.0.0-1`` is a prerelease *below* 1.0.0, a Debian
#: ``1.0.0-1`` is a revision *above* it, and ``1.0.0+5`` is build
#: metadata that SemVer ignores -- folding any of them into the core
#: (``1.0.0.1``) can clear an affected version (TR-2026-01 D8).
_GENERIC = re.compile(
    r"v?(?P<core>\d+(?:\.\d+)*)"
    r"(?:[-._]?(?P<pre>" + "|".join(sorted(_PRE, key=len, reverse=True)) + r")"
    r"[-._]?(?P<num>\d+)?)?"
)


def detect_scheme(version: str) -> str:
    """generic: numeric core + optional known prerelease marker and
    number (``_GENERIC``). Everything else (distro/build suffixes,
    numeric suffixes, epochs, unknown alphas) is unknown."""
    if _GENERIC.fullmatch(str(version).lower()) is None:
        return "unknown"
    return "generic"


def _key(version: str) -> tuple[tuple[int, ...], int, int] | None:
    """(numeric core, prerelease rank, prerelease number); None unless generic.

    The prerelease number orders ``rc1`` below ``rc2``; a release has
    rank 0 and sorts above every prerelease of the same core.
    """
    match = _GENERIC.fullmatch(str(version).lower())
    if match is None:
        return None
    nums = tuple(int(n) for n in match["core"].split("."))
    rank = _PRE[match["pre"]] if match["pre"] else 0
    return (nums, rank, int(match["num"] or 0))


def compare(a: str, b: str, scheme: str | None = None) -> int | None:
    """-1/0/1, or None when either side is unparseable or not generic.

    An explicit unsupported `scheme` forces None; otherwise both sides
    must detect as generic (unknown distro/build suffixes are not
    comparable — never guess).
    """
    if scheme is not None and scheme not in KNOWN_SCHEMES:
        return None
    if scheme == "semver":
        return _semver_compare(a, b)
    if scheme == "numeric":
        return _numeric_compare(a, b)
    if detect_scheme(a) != "generic" or detect_scheme(b) != "generic":
        return None
    ka, kb = _key(a), _key(b)
    if ka is None or kb is None:
        return None
    (na, ra, pa), (nb, rb, pb) = ka, kb
    length = max(len(na), len(nb))
    na += (0,) * (length - len(na))
    nb += (0,) * (length - len(nb))
    if na != nb:
        return -1 if na < nb else 1
    if (ra, pa) != (rb, pb):
        return -1 if (ra, pa) < (rb, pb) else 1
    return 0


#: SemVer 2.0 (https://semver.org), leniently allowing a ``v`` prefix and
#: a one- or two-part core (``1``, ``1.2`` read as ``1.0.0``, ``1.2.0``).
_SEMVER = re.compile(
    r"v?(?P<core>\d+(?:\.\d+){0,2})"
    r"(?:-(?P<pre>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)


def _semver_key(version: str) -> tuple[tuple[int, int, int], list[str] | None] | None:
    match = _SEMVER.fullmatch(str(version).strip())
    if match is None:
        return None
    parts = [int(n) for n in match["core"].split(".")]
    core = (parts + [0, 0])[:3]
    pre = match["pre"].split(".") if match["pre"] else None
    for ident in pre or []:
        if ident.isdigit() and len(ident) > 1 and ident.startswith("0"):
            return None  # leading zeros are invalid in numeric identifiers
    return (core[0], core[1], core[2]), pre


def _semver_compare(a: str, b: str) -> int | None:
    """SemVer 2.0 precedence; None unless both sides are SemVer.

    A release outranks its prereleases. Prerelease identifiers compare
    left to right: numeric ones numerically, alphanumeric ones in ASCII
    order, numeric below alphanumeric, and a shorter list below a longer
    one it prefixes. So ``1.0.0-dev`` sorts above ``1.0.0-beta`` and
    ``1.0.0-a`` below ``1.0.0-alpha`` -- unlike the generic marker table
    (TR-2026-01 D11). Build metadata is ignored.
    """
    ka, kb = _semver_key(a), _semver_key(b)
    if ka is None or kb is None:
        return None
    (ca, pa), (cb, pb) = ka, kb
    if ca != cb:
        return -1 if ca < cb else 1
    if pa is None or pb is None:
        if pa is pb:
            return 0
        return 1 if pa is None else -1
    for x, y in zip(pa, pb):
        if x == y:
            continue
        if x.isdigit() and y.isdigit():
            return -1 if int(x) < int(y) else 1
        if x.isdigit() != y.isdigit():
            return -1 if x.isdigit() else 1
        return -1 if x < y else 1
    if len(pa) != len(pb):
        return -1 if len(pa) < len(pb) else 1
    return 0


_NUMERIC = re.compile(r"v?\d+(?:\.\d+)*")


def _numeric_compare(a: str, b: str) -> int | None:
    """Plain dotted numbers only, for ecosystems we do not model.

    Numeric segments order the same way in every common scheme, but
    zero padding does not: Debian sorts ``1.0`` below ``1.0.0`` where
    PEP 440 and Maven call them equal. Equality reached only by padding
    is therefore undetermined.
    """
    if _NUMERIC.fullmatch(str(a).lower()) is None or _NUMERIC.fullmatch(str(b).lower()) is None:
        return None
    na = [int(n) for n in str(a).lower().lstrip("v").split(".")]
    nb = [int(n) for n in str(b).lower().lstrip("v").split(".")]
    length = max(len(na), len(nb))
    pa = na + [0] * (length - len(na))
    pb = nb + [0] * (length - len(nb))
    if pa != pb:
        return -1 if pa < pb else 1
    return 0 if len(na) == len(nb) else None


def range_scheme(range_type: str | None, ecosystem: str | None = None) -> str:
    """Comparison scheme for one OSV range (``SEMVER`` or ``ECOSYSTEM``)."""
    if str(range_type or "ECOSYSTEM").upper() == "SEMVER":
        return "semver"
    return _ECOSYSTEM_SCHEMES.get(str(ecosystem or "").strip().lower(), "numeric")


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
    version: str | None,
    affected: dict[str, Any],
    scheme: str | None = None,
    ecosystem: str | None = None,
) -> bool | None:
    """OSV affected entry vs a deployed version.

    Each range is compared under its own scheme (``range_scheme``):
    SemVer for ``SEMVER`` ranges, the advisory ecosystem's ordering for
    ``ECOSYSTEM`` ranges. An explicit ``scheme`` overrides that choice.
    """
    if not version:
        return None
    ecosystem = ecosystem or (affected.get("package") or {}).get("ecosystem")
    listed = [str(v) for v in affected.get("versions", []) or []]
    listed_scheme = scheme or range_scheme("ECOSYSTEM", ecosystem)
    comparable = True
    for known in listed:
        if str(version) == known:
            return True
        result = compare(version, known, listed_scheme)
        if result == 0:
            return True
        comparable = comparable and result is not None
    ranges = affected.get("ranges", []) or []
    if not ranges:
        # The affected set is the union of ranges and listed versions (OSV
        # schema). With no range, a version comparable with, and unequal
        # to, every listed one is outside this entry; any incomparable
        # listed version withholds the negative.
        return False if listed and comparable else None
    undecided = False
    for rng in ranges:
        result = _osv_range(version, rng, scheme or range_scheme(rng.get("type"), ecosystem))
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

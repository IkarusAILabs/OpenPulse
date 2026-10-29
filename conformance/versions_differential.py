"""Differential version tests (TR-2026-01, Section 10).

Run from the repository root:

    python conformance/versions_differential.py   # writes conformance/results/versions.json

PEP 440: ``core.versions.compare(a, b, "pep440")`` against ``packaging``
(PyPA's reference implementation), over every ordered pair of a generated
set. The implementation may abstain (None); it must never *disagree*.
OSV ranges for the PyPI ecosystem are checked the same way against
intervals evaluated with ``packaging``.

SemVer: no independent SemVer library is available offline, so SemVer is
checked against the specification's own precedence vectors (semver.org
section 11) and for order consistency. That is weaker than a differential
test and is reported as such.
"""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packaging.version import InvalidVersion, Version  # noqa: E402

from core.versions import compare, osv_applicable  # noqa: E402

CORES = ["0", "1", "1.0", "1.0.0", "1.0.1", "1.1", "1.10", "1.2", "2", "2.0.0", "10.0"]
MARKERS = [
    "",
    "dev",
    "dev1",
    "a",
    "a1",
    "alpha2",
    "b",
    "b2",
    "beta",
    "rc",
    "rc1",
    "rc2",
    "c1",
    "pre1",
    "preview2",
]
SEPARATORS = ["", ".", "-"]
OUTSIDE = [
    "1.0.post1",
    "1.0+local",
    "1!1.0",
    "1.0-1",
    "1.0.0-SNAPSHOT",
    "1.0a1.dev1",
    "1.0.dev1+x",
    "latest",
    "v1.0",
    "1.0rc1.post2",
]


def pep440_versions() -> list[str]:
    out = set(OUTSIDE)
    for core, marker, sep in itertools.product(CORES, MARKERS, SEPARATORS):
        if not marker and sep:
            continue
        out.add(f"{core}{sep}{marker}")
    return sorted(out)


def _reference(a: str, b: str) -> int | None:
    try:
        va, vb = Version(a), Version(b)
    except InvalidVersion:
        return None
    return (va > vb) - (va < vb)


def pep440_pairs() -> dict:
    versions = pep440_versions()
    agree = abstain = 0
    disagreements = []
    reference_invalid = 0
    for a, b in itertools.product(versions, repeat=2):
        ref = _reference(a, b)
        got = compare(a, b, "pep440")
        if ref is None:
            reference_invalid += 1
            if got is not None:
                disagreements.append({"a": a, "b": b, "packaging": "invalid", "openpulse": got})
            continue
        if got is None:
            abstain += 1
        elif got == ref:
            agree += 1
        else:
            disagreements.append({"a": a, "b": b, "packaging": ref, "openpulse": got})
    return {
        "versions": len(versions),
        "pairs": len(versions) ** 2,
        "agree": agree,
        "abstain": abstain,
        "reference_invalid": reference_invalid,
        "disagreements": disagreements,
    }


def pypi_ranges() -> dict:
    """introduced/fixed intervals over the same set, PyPI ecosystem."""
    versions = [v for v in pep440_versions() if _reference(v, v) is not None]
    bounds = ["0", "1.0", "1.0rc1", "1.0.1", "1.1", "2.0.0"]
    agree = abstain = 0
    disagreements = []
    for low, high in itertools.permutations(bounds, 2):
        if low != "0" and Version(low) >= Version(high):
            continue
        affected = {
            "ranges": [{"type": "ECOSYSTEM", "events": [{"introduced": low}, {"fixed": high}]}]
        }
        for v in versions:
            inside = (low == "0" or Version(v) >= Version(low)) and Version(v) < Version(high)
            got = osv_applicable(v, affected, ecosystem="PyPI")
            if got is None:
                abstain += 1
            elif got == inside:
                agree += 1
            else:
                disagreements.append(
                    {
                        "version": v,
                        "introduced": low,
                        "fixed": high,
                        "packaging_inside": inside,
                        "openpulse": got,
                    }
                )
    return {"agree": agree, "abstain": abstain, "disagreements": disagreements}


SEMVER_PRECEDENCE = [
    "1.0.0-alpha",
    "1.0.0-alpha.1",
    "1.0.0-alpha.beta",
    "1.0.0-beta",
    "1.0.0-beta.2",
    "1.0.0-beta.11",
    "1.0.0-rc.1",
    "1.0.0",
    "1.0.1",
    "1.1.0",
    "2.0.0",
]


def semver_checks() -> dict:
    failures = []
    for i, low in enumerate(SEMVER_PRECEDENCE):
        for high in SEMVER_PRECEDENCE[i + 1 :]:
            if compare(low, high, "semver") != -1 or compare(high, low, "semver") != 1:
                failures.append({"low": low, "high": high})
    pool = SEMVER_PRECEDENCE + ["1.0.0+build", "1.0.0-0", "1.0.0-a", "1.0.0-dev", "1.0.0-c"]
    inconsistent = 0
    for a, b, c in itertools.product(pool, repeat=3):
        ab, bc, ac = compare(a, b, "semver"), compare(b, c, "semver"), compare(a, c, "semver")
        if None in (ab, bc, ac):
            continue
        if ab <= 0 and bc <= 0 and ac > 0:
            inconsistent += 1
        if compare(b, a, "semver") != -ab:
            inconsistent += 1
    return {
        "specification_vectors": len(SEMVER_PRECEDENCE),
        "vector_failures": failures,
        "order_inconsistencies": inconsistent,
    }


def run() -> dict:
    return {"pep440_pairs": pep440_pairs(), "pypi_ranges": pypi_ranges(), "semver": semver_checks()}


if __name__ == "__main__":
    result = run()
    out = ROOT / "conformance" / "results"
    out.mkdir(exist_ok=True)
    (out / "versions.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    p = result["pep440_pairs"]
    print(
        f"PEP 440 pairs: {p['pairs']} over {p['versions']} versions; agree {p['agree']}, "
        f"abstain {p['abstain']}, reference-invalid {p['reference_invalid']}, "
        f"disagree {len(p['disagreements'])}"
    )
    r = result["pypi_ranges"]
    print(
        f"PyPI ranges: agree {r['agree']}, abstain {r['abstain']}, "
        f"disagree {len(r['disagreements'])}"
    )
    s = result["semver"]
    print(
        f"SemVer: vector failures {len(s['vector_failures'])}, "
        f"order inconsistencies {s['order_inconsistencies']}"
    )
    for d in (p["disagreements"] + r["disagreements"])[:15]:
        print("  ", d)

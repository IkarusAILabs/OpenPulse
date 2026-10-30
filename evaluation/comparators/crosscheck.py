"""Cross-check OpenPulse's own version comparison against the pinned tools.

Run from the repository root, with every bridge installed:

    python evaluation/comparators/crosscheck.py [--out report.json]

For npm, Go and Maven it builds a version corpus (release cores crossed
with each ecosystem's pre-release and qualifier forms), then compares:

- ordering: ``core.versions.compare`` under the scheme OpenPulse uses for
  the ecosystem's OSV ranges, against the bridge's ``compare``;
- release-line membership: ``core.versions.in_release_line`` against the
  adapter's ``in_line`` (the specification's release rule).

Every pair is classified: agree; OpenPulse abstains where the reference
decides (coverage, not risk); OpenPulse decides where the reference
rejects the version; or disagree (both decide, differently). A
disagreement is a candidate defect of the D8/D11 kind, and the script
exits non-zero on any. OpenPulse's comparator is not changed by this
check; findings are fixed in their own PR.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE.parent))

from ecosystem_versions import Comparators  # noqa: E402

from core.versions import compare, in_release_line, range_scheme  # noqa: E402

CORES = ["0.9.0", "1.0.0", "1.0.1", "1.2.0", "1.10.0", "2.0.0"]
FORMS = {
    "npm": ["", "-alpha", "-alpha.1", "-beta.2", "-beta.11", "-rc.1", "-0", "-1", "+5"],
    "go": ["", "-alpha", "-alpha.1", "-beta.2", "-rc.1", "-0", "+incompatible"],
    "maven": ["", "-alpha-1", "-beta", "-rc1", "-SNAPSHOT", "-sp1", "-1", ".1"],
}
SHORT = {"npm": [], "go": ["1.2", "2"], "maven": ["1", "1.0", "1.2", "2.0"]}
LINES = ["0", "1", "1.0", "1.2", "1.10", "2"]
ECOSYSTEM = {"npm": "npm", "go": "Go", "maven": "Maven"}


def corpus(name: str) -> list[str]:
    return [c + f for c in CORES for f in FORMS[name]] + SHORT[name]


def _reference_form(name: str, version: str) -> str:
    return "v" + version if name == "go" else version


def classify(ours: object, theirs: object, reference_valid: bool) -> str:
    if not reference_valid:
        return "agree" if ours is None else "openpulse decides; reference rejects"
    if theirs is None:
        return "agree" if ours is None else "openpulse decides; reference undecided"
    if ours is None:
        return "openpulse abstains"
    return "agree" if ours == theirs else "disagree"


def run() -> dict:
    tools = Comparators(required=True)
    report: dict = {"pins": {n: s["reported"] for n, s in tools.status.items()}, "ecosystems": {}}
    try:
        for name, bridge in tools.bridges.items():
            versions = corpus(name)
            scheme = range_scheme("ECOSYSTEM", ECOSYSTEM[name])
            counts: Counter = Counter()
            examples: dict[str, list] = {}

            def note(kind: str, item: dict) -> None:
                counts[kind] += 1
                if kind != "agree" and len(examples.setdefault(kind, [])) < 12:
                    examples[kind].append(item)

            for a, b in itertools.permutations(versions, 2):
                ra, rb = _reference_form(name, a), _reference_form(name, b)
                valid = bool(bridge.parse(ra).get("valid")) and bool(bridge.parse(rb).get("valid"))
                theirs = bridge.compare(ra, rb) if valid else None
                ours = compare(a, b, scheme)
                note(
                    "order: " + classify(ours, theirs, valid),
                    {"a": a, "b": b, "openpulse": ours, "reference": theirs},
                )
            for v, line in itertools.product(versions, LINES):
                valid = bool(bridge.parse(_reference_form(name, v)).get("valid"))
                theirs = tools.in_line(ECOSYSTEM[name], v, line) if valid else None
                ours = in_release_line(v, line)
                note(
                    "line: " + classify(ours, theirs, valid),
                    {"version": v, "line": line, "openpulse": ours, "reference": theirs},
                )
            report["ecosystems"][name] = {
                "openpulse_scheme": scheme,
                "versions": len(versions),
                "counts": dict(sorted(counts.items())),
                "examples": examples,
            }
    finally:
        tools.close()
    report["disagreements"] = sum(
        n for e in report["ecosystems"].values() for k, n in e["counts"].items() if "disagree" in k
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run()
    if args.out:
        args.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    for name, block in report["ecosystems"].items():
        print(f"{name} (OpenPulse scheme {block['openpulse_scheme']}): {block['counts']}")
    print(f"disagreements: {report['disagreements']}")
    return 1 if report["disagreements"] else 0


if __name__ == "__main__":
    sys.exit(main())

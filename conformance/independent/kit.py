"""Independent-oracle kit: export cases, validate submissions, compare (R-B7).

Run from the repository root:

    python conformance/independent/kit.py export --cases 5000 --seed 11 --out cases.jsonl
    python conformance/independent/kit.py validate edge_cases.jsonl
    python conformance/independent/kit.py compare --cases edge_cases.jsonl \\
        [--verdicts their_verdicts.jsonl] [--out report.json]

The kit's files are written for an outside author: SPEC.md (the rules),
README.md (the process and the case format) and vocabulary.json (the
references a case may use). This script is the team's side. It imports
the team oracle and the implementation, which the author must not read,
and puts up to four sources side by side:

    expected      the author's hand-labelled outcome (edge cases only)
    independent   the author's own oracle, run on the same cases
    team_oracle   conformance/oracle.py
    implementation  core.risk.check.check_dependency

Disagreements are classified by severity, as in the randomised harness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE.parent))

import oracle  # noqa: E402
import randomized  # noqa: E402

from core.entities.identity import resolution_trust  # noqa: E402
from core.risk.check import check_dependency  # noqa: E402

SPEC = HERE / "SPEC.md"
VOCABULARY = HERE / "vocabulary.json"

PER_EVENT = ("AFFECTS", "RELATED", "AFFECTS_PROJECT", "NOT_AFFECTED", "UNKNOWN", "UNLOADED")
SUMMARIES = ("affected", "unresolved", "cleared", "no association")
SCOPE_KINDS = ("artifact", "release_line", "package", "registry")
COMPLETENESS = ("partial", "declared")
BASES = (None, "definitional", "announced", "corroborated", "verified")
ADMISSIBILITY = ("current", "withdrawn", "superseded", "contested", "stale")

#: Kit scope kind -> the randomised harness's event kind (implementation adapter).
_IMPL_KIND = {
    "artifact": "artifact",
    "release_line": "version",
    "package": "package",
    "registry": "registry",
}
#: Implementation relationship -> the specification's per-event label.
_IMPL_LABEL = {
    "AFFECTS_ARTIFACT": "AFFECTS",
    "AFFECTS_VERSION": "AFFECTS",
    "AFFECTS_PACKAGE": "AFFECTS",
    "RELATED": "RELATED",
    "AFFECTS_PROJECT": "AFFECTS_PROJECT",
    "NOT_AFFECTED": "NOT_AFFECTED",
    "UNKNOWN": "UNKNOWN",
}


def spec_sha256() -> str:
    return hashlib.sha256(SPEC.read_bytes()).hexdigest()


# --- validation -----------------------------------------------------------


def _curated_project(dep: dict[str, Any]) -> str | None:
    """The project the catalog's curated mappings assign, or None."""
    trust = resolution_trust(str(dep["ref"] if dep["kind"] == "image" else dep["package"]))
    if trust["via"] in ("explicit", "catalog") and trust["identity_status"] == "VERIFIED":
        return str(trust["slug"])
    return None


def validate_case(case: Any) -> list[str]:
    """Problems with one case; [] means valid. Fail closed on anything unknown."""
    if not isinstance(case, dict):
        return ["case is not an object"]
    cid = case.get("id", "?")
    errors: list[str] = []
    allowed = {"id", "dependency", "belongs_to", "events", "expected", "note"}
    errors += [f"{cid}: unknown field {k!r}" for k in case if k not in allowed]
    dep = case.get("dependency")
    if not isinstance(dep, dict) or dep.get("kind") not in ("image", "package"):
        return errors + [f"{cid}: dependency must be {{kind: image|package, ...}}"]
    if dep["kind"] == "image" and not isinstance(dep.get("ref"), str):
        errors.append(f"{cid}: an image dependency needs a string ref")
    if dep["kind"] == "package" and not isinstance(dep.get("package"), str):
        errors.append(f"{cid}: a package dependency needs a string package")
    if errors:
        return errors
    curated = _curated_project(dep)
    if case.get("belongs_to") != curated:
        errors.append(
            f"{cid}: belongs_to {case.get('belongs_to')!r} but the curated catalog says "
            f"{curated!r}; pick a reference from vocabulary.json or match its project"
        )
    events = case.get("events")
    if not isinstance(events, list) or not events:
        return errors + [f"{cid}: events must be a non-empty list"]
    seen = set()
    for ev in events:
        errors += [f"{cid}: {e}" for e in _validate_event(ev)]
        if isinstance(ev, dict):
            if ev.get("id") in seen:
                errors.append(f"{cid}: duplicate event id {ev.get('id')!r}")
            seen.add(ev.get("id"))
    expected = case.get("expected")
    if expected is not None:
        errors += [f"{cid}: {e}" for e in _validate_expected(expected, seen)]
    return errors


def _validate_event(ev: Any) -> list[str]:
    if not isinstance(ev, dict):
        return ["event is not an object"]
    errors = []
    allowed = {"id", "project", "scope", "named", "completeness", "basis", "admissibility"}
    errors += [f"event {ev.get('id')!r}: unknown field {k!r}" for k in ev if k not in allowed]
    if not isinstance(ev.get("id"), str) or not isinstance(ev.get("project"), str):
        errors.append("every event needs string id and project")
    scope = ev.get("scope")
    if scope is not None:
        if not isinstance(scope, dict) or scope.get("kind") not in SCOPE_KINDS:
            errors.append(f"event {ev.get('id')!r}: scope.kind must be one of {SCOPE_KINDS}")
        elif not isinstance(scope.get("values"), list) or not scope["values"]:
            errors.append(f"event {ev.get('id')!r}: scope.values must be a non-empty list")
    if not all(isinstance(n, str) for n in ev.get("named", [])):
        errors.append(f"event {ev.get('id')!r}: named must be a list of strings")
    if ev.get("completeness", "partial") not in COMPLETENESS:
        errors.append(f"event {ev.get('id')!r}: completeness must be one of {COMPLETENESS}")
    if ev.get("basis") not in BASES:
        errors.append(f"event {ev.get('id')!r}: basis must be one of {BASES}")
    if ev.get("completeness", "partial") == "partial" and ev.get("basis") is not None:
        errors.append(f"event {ev.get('id')!r}: a partial scope has no basis")
    if scope is None and ev.get("completeness", "partial") != "partial":
        errors.append(f"event {ev.get('id')!r}: a project-wide event has no completeness")
    if ev.get("admissibility", "current") not in ADMISSIBILITY:
        errors.append(f"event {ev.get('id')!r}: admissibility must be one of {ADMISSIBILITY}")
    return errors


def _validate_expected(expected: Any, event_ids: set) -> list[str]:
    if not isinstance(expected, dict):
        return ["expected must be an object"]
    errors = []
    per_event = expected.get("per_event", {})
    if set(per_event) - event_ids:
        errors.append(
            f"expected.per_event names unknown events {sorted(set(per_event) - event_ids)}"
        )
    errors += [
        f"expected.per_event {v!r} not in {PER_EVENT}"
        for v in per_event.values()
        if v not in PER_EVENT
    ]
    if expected.get("summary") not in SUMMARIES:
        errors.append(f"expected.summary must be one of {SUMMARIES}")
    if not expected.get("rationale"):
        errors.append("expected.rationale is required: say why, citing SPEC.md sections")
    judgement = expected.get("judgement")
    if judgement not in (None, "in_scope", "out_of_scope", "undeterminable"):
        errors.append("expected.judgement must be in_scope, out_of_scope or undeterminable")
    return errors


# --- the two team-side sources ----------------------------------------------


def _identity(case: dict[str, Any], project: str) -> str:
    owner = case.get("belongs_to")
    if owner is None:
        return "unresolved"
    return "project" if owner == project else "other"


_ORACLE_KIND = {
    "artifact": "artifact",
    "release_line": "release_line",
    "package": "package",
    "registry": "registry",
}


def team_oracle(case: dict[str, Any]) -> dict[str, Any]:
    dep = case["dependency"]
    per_event = {}
    for ev in case["events"]:
        elements = [oracle.Element("artifact", n, example=True) for n in ev.get("named", [])]
        scope = ev.get("scope")
        if scope is None:
            elements.append(oracle.Element("project", ev["project"]))
        else:
            elements += [oracle.Element(_ORACLE_KIND[scope["kind"]], v) for v in scope["values"]]
        o_dep = oracle.Dependency(
            dep["kind"],
            ref=dep.get("ref", ""),
            package=dep.get("package", ""),
            version=dep.get("version"),
            identity=_identity(case, ev["project"]),
        )
        o_event = oracle.Event(
            ev["project"],
            elements,
            ev.get("completeness", "partial"),
            ev.get("basis"),
            ev.get("admissibility", "current"),
        )
        per_event[ev["id"]] = oracle.applicability(o_dep, o_event)
    return {"per_event": per_event, "summary": randomized.summary(list(per_event.values()))}


def _impl_event(ev: dict[str, Any]) -> dict[str, Any]:
    scope = ev.get("scope")
    return {
        "id": ev["id"],
        "slug": ev["project"],
        "kind": None if scope is None else _IMPL_KIND[scope["kind"]],
        "values": [] if scope is None else list(scope["values"]),
        "named": list(ev.get("named", [])),
        "chi": ev.get("completeness", "partial") == "declared",
        "basis": ev.get("basis"),
        "admissibility": ev.get("admissibility", "current"),
    }


def implementation(case: dict[str, Any]) -> dict[str, Any]:
    dep = dict(case["dependency"])
    if dep["kind"] == "package":
        dep["ecosystem"] = ""  # identities are by name, as the vocabulary defines them
    events = [randomized.implementation_event(_impl_event(ev)) for ev in case["events"]]
    verdict = check_dependency(
        dep, events, as_of=randomized.AS_OF, max_evidence_age=randomized.MAX_AGE
    )
    by_event = {
        str(c.get("event_id")): str(c.get("relationship"))
        for c in verdict.verdicts
        if c.get("cause") == "upstream_change"
    }
    per_event = {}
    for ev in case["events"]:
        if ev.get("admissibility") in ("withdrawn", "superseded"):
            per_event[ev["id"]] = "UNLOADED"
        else:
            per_event[ev["id"]] = _IMPL_LABEL.get(by_event.get(ev["id"], "UNKNOWN"), "RELATED")
    summary = randomized.summary([verdict.relationship])
    return {"per_event": per_event, "summary": summary}


# --- export -------------------------------------------------------------------


def export_cases(n: int, seed: int) -> list[dict[str, Any]]:
    """Seeded random cases in the kit format, with no expected outcomes."""
    rng = random.Random(seed)
    out = []
    for i in range(n):
        dep = randomized.random_dependency(rng)
        events = [randomized.random_event(rng, j) for j in range(rng.randint(1, 3))]
        case = {"id": f"r{seed}-{i}", "dependency": dep, "events": []}
        case["belongs_to"] = _curated_project(dep)
        for ev in events:
            kind = {v: k for k, v in _IMPL_KIND.items()}.get(ev["kind"])
            case["events"].append(
                {
                    "id": ev["id"],
                    "project": ev["slug"],
                    "scope": None if kind is None else {"kind": kind, "values": ev["values"]},
                    "named": ev["named"],
                    "completeness": "declared" if ev["chi"] else "partial",
                    "basis": ev["basis"],
                    "admissibility": ev["admissibility"],
                }
            )
        out.append(case)
    return out


# --- compare --------------------------------------------------------------------


def _severity(reference: str, other: str) -> str:
    if reference == other:
        return "agree"
    return randomized._SUMMARY_SEVERITY.get((reference, other), "other")


def _event_class(label: str) -> str:
    return randomized.summary([label])


def compare(cases: list[dict[str, Any]], verdicts: dict[str, dict] | None = None) -> dict:
    """Every source side by side, with every disagreement listed."""
    rows = []
    for case in cases:
        sources: dict[str, dict] = {
            "team_oracle": team_oracle(case),
            "implementation": implementation(case),
        }
        if case.get("expected"):
            sources["expected"] = case["expected"]
        if verdicts is not None and case["id"] in verdicts:
            sources["independent"] = verdicts[case["id"]]
        rows.append({"id": case["id"], "case": case, "sources": sources})
    pairs = [
        ("expected", "team_oracle"),
        ("expected", "implementation"),
        ("expected", "independent"),
        ("independent", "team_oracle"),
        ("independent", "implementation"),
        ("team_oracle", "implementation"),
    ]
    agreement: dict[str, Counter] = {}
    disagreements = []
    for left, right in pairs:
        counter: Counter = Counter()
        for row in rows:
            s = row["sources"]
            if left not in s or right not in s:
                continue
            sev = _severity(s[left]["summary"], s[right]["summary"])
            per_event_match = all(
                _event_class(s[left]["per_event"].get(k, "UNKNOWN"))
                == _event_class(s[right]["per_event"].get(k, "UNKNOWN"))
                for k in s[left].get("per_event", {})
            )
            counter["summary " + sev] += 1
            counter["per-event " + ("agree" if per_event_match else "differ")] += 1
            if sev != "agree" or not per_event_match:
                disagreements.append(
                    {
                        "id": row["id"],
                        "between": [left, right],
                        "severity": sev,
                        left: s[left],
                        right: s[right],
                    }
                )
        if counter:
            agreement[f"{left} vs {right}"] = counter
    judged = [r for r in rows if (r["sources"].get("expected") or {}).get("judgement")]
    return {
        "spec_sha256": spec_sha256(),
        "cases": len(rows),
        "agreement": {k: dict(v) for k, v in agreement.items()},
        "disagreements": disagreements,
        # Where the author's view of the real-world answer differs from what
        # the rules give: candidate specification defects, for adjudication.
        "judgement_vs_rules": [
            {
                "id": r["id"],
                "rules_summary": r["sources"]["expected"]["summary"],
                "judgement": r["sources"]["expected"]["judgement"],
                "rationale": r["sources"]["expected"]["rationale"],
            }
            for r in judged
            if not _judgement_consistent(r["sources"]["expected"])
        ],
        "rows": rows,
    }


def _judgement_consistent(expected: dict[str, Any]) -> bool:
    summary, judgement = expected["summary"], expected["judgement"]
    if judgement == "in_scope":
        return summary in ("affected", "unresolved")
    if judgement == "out_of_scope":
        return summary in ("cleared", "no association", "unresolved")
    return summary in ("unresolved",)


# --- CLI -------------------------------------------------------------------------


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    ex = sub.add_parser("export")
    ex.add_argument("--cases", type=int, default=5000)
    ex.add_argument("--seed", type=int, default=11)
    ex.add_argument("--out", type=Path, required=True)
    va = sub.add_parser("validate")
    va.add_argument("cases", type=Path)
    co = sub.add_parser("compare")
    co.add_argument("--cases", type=Path, required=True)
    co.add_argument("--verdicts", type=Path)
    co.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    if args.command == "export":
        cases = export_cases(args.cases, args.seed)
        args.out.write_text("".join(json.dumps(c) + "\n" for c in cases), encoding="utf-8")
        print(f"wrote {len(cases)} cases (seed {args.seed}) to {args.out}")
        return 0
    cases = _read_jsonl(args.cases)
    problems = [p for c in cases for p in validate_case(c)]
    if args.command == "validate" or problems:
        for p in problems:
            print(p)
        print(f"{len(cases)} cases, {len(problems)} problems")
        return 1 if problems else 0
    verdicts = None
    if args.verdicts:
        verdicts = {v["id"]: v for v in _read_jsonl(args.verdicts)}
    result = compare(cases, verdicts)
    if args.out:
        args.out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(f"{result['cases']} cases, SPEC.md sha256 {result['spec_sha256'][:12]}")
    for pair, counts in result["agreement"].items():
        print(f"  {pair:34} {counts}")
    print(
        f"  disagreements: {len(result['disagreements'])}; "
        f"judgement differs from rules: {len(result['judgement_vs_rules'])}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

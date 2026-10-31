"""Decision invariants I1-I8 as executable properties (research/RESEARCH_PROTOCOL.md §3).

Run from the repository root:

    python conformance/invariants.py [--cases 4000] [--seeds 11 12 13]

The oracle (``oracle.py``) says what each verdict should be. These
properties say what no verdict may ever do, whatever the oracle says:
they are stated on the production engine's outputs only, so they also
cover inputs the oracle does not model (untrusted identity mappings,
TR-2026-01 D16). Cases come from the randomised generator
(``randomized.py``), widened with heuristic identity mappings, and every
case is reproducible from its seed and index.

    I1  an unresolved identity is never excluded or disassociated by an
        identity-dependent scope (project, release line, bare package);
    I2  NOT_AFFECTED needs a complete scope with a recorded basis, from a
        current, uncontested, fresh event;
    I3  a heuristic or unreviewed mapping (not VERIFIED) is treated as I1;
    I4  an unresolved per-event verdict keeps the summary unresolved, and
        every machine-readable surface reads it as "not a clearance";
    I5  the evidence contract states the engine's relationship, and is valid;
    I6  adding look-alike elements (same name, other namespace or tag; a
        similar package name) never removes an affected verdict;
    I7  every per-event NOT_AFFECTED is the oracle's NOT_AFFECTED, and a
        summary clearance has a clearing event and nothing unresolved;
    I8  every non-UNKNOWN verdict names its events, each cause names its
        event, relationship and reason, and cited evidence exists.

A violation carries the seed, the case index and the inputs, so it can
be replayed and kept as a regression test.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import randomized  # noqa: E402

from core.evidence_contract import build_v1_contract, validate_v1_contract  # noqa: E402
from core.risk.check import check_dependency  # noqa: E402
from core.verdict_meaning import verdict_meaning  # noqa: E402

INVARIANTS = ("I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8")
DEFAULT_SEEDS = (11, 12, 13)

#: Image references that resolve to another project only through the
#: Bitnami namespace heuristic (REVIEW_REQUIRED): never curated, never
#: proof of another project (D16).
HEURISTIC_REPOS = ["docker.io/bitnami/mysql", "docker.io/bitnami/postgresql"]

_AFFECTED = {"AFFECTS_ARTIFACT", "AFFECTS_VERSION", "AFFECTS_PACKAGE"}
_UNRESOLVED = {"RELATED", "AFFECTS_PROJECT"}
#: Scope kinds whose test depends on the dependency's identity (None is
#: a project-wide event).
_IDENTITY_SCOPES = (None, "version")


def random_dependency(rng: random.Random) -> dict[str, Any]:
    """The randomised generator's dependency, or a heuristic-mapped image."""
    if rng.random() < 0.15:
        tag = rng.choice(randomized.TAGS)
        repo = rng.choice(HEURISTIC_REPOS)
        return {"kind": "image", "ref": repo if tag is None else f"{repo}:{tag}"}
    return randomized.random_dependency(rng)


def identity(dep: dict[str, Any], slug: str) -> str:
    """Ground truth: project | other | unresolved | untrusted."""
    if dep["kind"] == "image" and dep["ref"].split("@")[0].rsplit(":", 1)[0] in HEURISTIC_REPOS:
        return "untrusted"
    return randomized._identity(dep, slug)


def generate(seed: int, cases: int):
    """(index, dependency, event specs), reproducible from the seed."""
    rng = random.Random(seed)
    for index in range(cases):
        dep = random_dependency(rng)
        events = [randomized.random_event(rng, i) for i in range(rng.randint(1, 3))]
        yield index, dep, events


def _engine_dep(dep: dict[str, Any]) -> dict[str, Any]:
    # As in randomized.run: packages without an ecosystem are named by PROJECTS.
    return dep if dep["kind"] == "image" else {"ecosystem": "", **dep}


def _verdict(dep: dict[str, Any], specs: list[dict[str, Any]]):
    events = [randomized.implementation_event(ev) for ev in specs]
    verdict = check_dependency(
        _engine_dep(dep), events, as_of=randomized.AS_OF, max_evidence_age=randomized.MAX_AGE
    )
    return events, verdict


def _per_event(verdict) -> dict[str, dict[str, Any]]:
    return {
        str(c.get("event_id")): c for c in verdict.verdicts if c.get("cause") == "upstream_change"
    }


def _identity_dependent(ev: dict[str, Any]) -> bool:
    if ev["kind"] in _IDENTITY_SCOPES:
        return True
    # A bare package value is decided by identity; a purl value by
    # (ecosystem, name), which needs no resolved identity (F3).
    return ev["kind"] == "package" and not any(v.startswith("pkg:") for v in ev["values"])


def _lookalike(ev: dict[str, Any]) -> dict[str, Any]:
    """ev with look-alike elements put first: same names, other places.

    First, because element order must not matter: an engine that let the
    first look-alike decide would show it here.
    """
    out = copy.deepcopy(ev)
    out["named"] = ["ghcr.io/zzz/redis:7.2", "docker.io/zzz/kvstore:latest", *out["named"]]
    if out["kind"] == "package":
        out["values"] = ["redis-py", "other-pkg", *out["values"]]
    elif out["kind"] == "artifact":
        out["values"] = ["ghcr.io/zzz/redis:<version>", "ghcr.io/zzz/mysql:8.0", *out["values"]]
    return out


def check_case(
    dep: dict[str, Any], specs: list[dict[str, Any]], exercised: Counter | None = None
) -> list[tuple[str, str]]:
    """Every invariant violated by one case, as (invariant, explanation).

    ``exercised`` counts the checks whose precondition held, so that a
    property that never fires can be told from one that is never tested.
    """
    found: list[tuple[str, str]] = []
    ran = exercised if exercised is not None else Counter()
    events, verdict = _verdict(dep, specs)
    by_event = _per_event(verdict)
    ids = {e.id for e in events}

    for ev, event in zip(specs, events):
        cause = by_event.get(ev["id"])
        if cause is None:
            continue  # withdrawn or superseded: not evaluated
        rel = str(cause.get("relationship"))
        who = identity(dep, ev["slug"])
        if _identity_dependent(ev) and who in ("unresolved", "untrusted"):
            ran["I1" if who == "unresolved" else "I3"] += 1
        if _identity_dependent(ev) and rel in ("NOT_AFFECTED", "UNKNOWN"):
            if who == "unresolved":
                found.append(("I1", f"{ev['id']}: unresolved identity gave {rel}"))
            elif who == "untrusted":
                found.append(("I3", f"{ev['id']}: heuristic mapping gave {rel}"))
        if rel == "NOT_AFFECTED":
            ran["I2"] += 1
            ran["I7"] += who != "untrusted"
            admits = ev["chi"] and ev["basis"] is not None and ev["admissibility"] == "current"
            if not admits:
                found.append(
                    (
                        "I2",
                        f"{ev['id']}: NOT_AFFECTED with chi={ev['chi']} basis={ev['basis']} "
                        f"admissibility={ev['admissibility']}",
                    )
                )
            # The oracle models no untrusted identity; I3 covers that case.
            if who != "untrusted":
                spec = randomized.oracle_verdict(dep, ev)
                if spec != "NOT_AFFECTED":
                    found.append(("I7", f"{ev['id']}: NOT_AFFECTED where the model says {spec}"))
        # I5: the contract a consumer receives states this relationship.
        single = check_dependency(
            _engine_dep(dep), [event], as_of=randomized.AS_OF, max_evidence_age=randomized.MAX_AGE
        )
        if single.relationship != "UNKNOWN":
            ran["I5"] += 1
            contract = build_v1_contract(
                event, single, as_of=randomized.AS_OF, max_evidence_age=randomized.MAX_AGE
            )
            problems = validate_v1_contract(contract)
            if problems:
                found.append(("I5", f"{ev['id']}: invalid contract: {problems[:2]}"))
            expected = verdict_meaning(single.relationship)["direct_scope"]
            if contract["verdict_meaning"]["direct_scope"] != expected:
                found.append(
                    (
                        "I5",
                        f"{ev['id']}: contract direct_scope "
                        f"{contract['verdict_meaning']['direct_scope']} for {single.relationship}",
                    )
                )
            if single.relationship in _UNRESOLVED and contract["verdict_meaning"][
                "direct_scope"
            ] not in ("undetermined", "project_tie"):
                found.append(("I4", f"{ev['id']}: contract reads unresolved as decided"))

    # I4: unresolved survives aggregation and every reading of it.
    per_event = {str(c.get("relationship")) for c in by_event.values()}
    summary = verdict.relationship
    ran["I4"] += bool(per_event & _UNRESOLVED)
    if per_event & _UNRESOLVED and summary in ("NOT_AFFECTED", "UNKNOWN"):
        found.append(("I4", f"per-event {sorted(per_event)} summarised as {summary}"))
    if summary in _UNRESOLVED:
        meaning = verdict_meaning(summary)
        if meaning["direct_scope"] not in ("undetermined", "project_tie"):
            found.append(("I4", f"{summary} read as {meaning['direct_scope']}"))
        if "Not a clearance" not in meaning["statement"]:
            found.append(("I4", f"{summary} statement does not disclaim a clearance"))
    # I7: a summary clearance stands on a clearing event and nothing open.
    if summary == "NOT_AFFECTED" and (
        "NOT_AFFECTED" not in per_event or per_event - {"NOT_AFFECTED", "UNKNOWN"}
    ):
        found.append(("I7", f"summary NOT_AFFECTED over per-event {sorted(per_event)}"))
    # I8: traceability.
    if summary != "UNKNOWN":
        ran["I8"] += 1
        if not verdict.events or not set(verdict.events) <= ids:
            found.append(("I8", f"verdict events {verdict.events} not within {sorted(ids)}"))
        if not verdict.reason:
            found.append(("I8", "verdict without a reason"))
        for cause in by_event.values():
            if not cause.get("relationship") or not (cause.get("reason") or cause.get("detail")):
                found.append(("I8", f"cause for {cause.get('event_id')} without rule or reason"))
        cited = {e.source.name for event in events for e in event.evidences}
        if not set(verdict.evidence) <= cited:
            found.append(("I8", f"evidence {verdict.evidence} not among {sorted(cited)}"))
    # I6: look-alike elements never remove an affected verdict.
    for ev in specs:
        cause = by_event.get(ev["id"])
        if cause is None or str(cause.get("relationship")) not in _AFFECTED:
            continue
        ran["I6"] += 1
        _, widened = _verdict(dep, [_lookalike(ev)])
        if widened.relationship not in _AFFECTED:
            found.append(
                ("I6", f"{ev['id']}: affected, but {widened.relationship} with look-alikes")
            )
    return found


def run(cases: int = 4000, seeds: tuple[int, ...] = DEFAULT_SEEDS) -> dict[str, Any]:
    checked: Counter = Counter()
    exercised: Counter = Counter()
    violations: Counter = Counter()
    examples: dict[str, list[dict[str, Any]]] = {}
    for seed in seeds:
        for index, dep, specs in generate(seed, cases):
            checked["cases"] += 1
            for name, why in check_case(dep, specs, exercised):
                violations[name] += 1
                bucket = examples.setdefault(name, [])
                if len(bucket) < 3:
                    bucket.append(
                        {
                            "seed": seed,
                            "index": index,
                            "why": why,
                            "dependency": dep,
                            "events": specs,
                        }
                    )
    return {
        "seeds": list(seeds),
        "cases_per_seed": cases,
        "cases": checked["cases"],
        "invariants": list(INVARIANTS),
        "exercised": {name: exercised[name] for name in INVARIANTS},
        "violations": {name: violations[name] for name in INVARIANTS},
        "counterexamples": examples,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=4000, help="cases per seed")
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    parser.add_argument("--out", type=Path, default=ROOT / "conformance" / "results")
    args = parser.parse_args()
    result = run(args.cases, tuple(args.seeds))
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "invariants.json").write_text(
        json.dumps(result, indent=1, default=str) + "\n", encoding="utf-8"
    )
    print(f"{result['cases']} cases, seeds {result['seeds']}")
    for name in INVARIANTS:
        print(
            f"  {name}: {result['exercised'][name]} checks, {result['violations'][name]} violations"
        )
    sys.exit(1 if any(result["violations"].values()) else 0)

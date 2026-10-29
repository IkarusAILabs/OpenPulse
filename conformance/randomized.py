"""Randomised differential testing: oracle vs implementation (TR-2026-01).

Run from the repository root:

    python conformance/randomized.py [--cases 20000] [--seed 2026]

Unlike the matrix, cases here combine everything at once: one to three
events per dependency, from two projects, each with a random scope of
one to four elements of mixed kinds, random named examples, random
completeness, basis and admissibility, and a random dependency. Both
the per-event verdicts and the cross-event summary are compared. The
generator is seeded, so a run is reproducible from its seed.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import oracle  # noqa: E402

from core.risk.check import check_dependency  # noqa: E402
from core.schema.models import Artifact, Evidence, OSSEvent, Scope, Source  # noqa: E402

FETCHED = datetime(2026, 10, 28, tzinfo=timezone.utc)
DIGESTS = ["sha256:" + c * 64 for c in "abc"]

#: Two curated projects and their references (ground-truth identity by
#: the catalog's meaning), plus unmapped references.
PROJECTS = {
    "redis": {
        "repos": ["docker.io/library/redis", "docker.io/redis"],
        "packages": ["redis"],
        "lines": ["6", "6.2", "7", "7.2", "8"],
    },
    "mysql": {
        "repos": ["docker.io/library/mysql"],
        "packages": ["mysql"],
        "lines": ["5.7", "8", "8.0"],
    },
}
UNMAPPED_REPOS = ["docker.io/zzz/kvstore", "ghcr.io/zzz/redis"]
#: Curated as a third project (bitnami-redis-stack): "other" to both.
CURATED_OTHER_REPOS = ["docker.io/bitnami/redis"]
UNMAPPED_PACKAGES = ["zzzpkg", "redis-py"]
TAGS = [None, "latest", "7.2", "7.2.4", "7.2.4-alpine", "8.0", "6.2.1-debian-12-r3", "5.7.44"]
PKG_VERSIONS = [None, "7.2.0", "8.1", "6.2.14", "5.7.1"]


def _owner(ref_or_package: str) -> str | None:
    for slug, p in PROJECTS.items():
        if ref_or_package in p["packages"]:
            return slug
        base = ref_or_package.split("@")[0].rsplit(":", 1)[0] if "/" in ref_or_package else ""
        if base in p["repos"]:
            return slug
    return None


def random_dependency(rng: random.Random) -> dict:
    if rng.random() < 0.65:
        curated = [r for p in PROJECTS.values() for r in p["repos"]]
        repo = rng.choice(curated + UNMAPPED_REPOS + CURATED_OTHER_REPOS)
        if rng.random() < 0.2:
            ref = f"{repo}@{rng.choice(DIGESTS)}"
        else:
            tag = rng.choice(TAGS)
            ref = repo if tag is None else f"{repo}:{tag}"
        return {"kind": "image", "ref": ref}
    package = rng.choice([n for p in PROJECTS.values() for n in p["packages"]] + UNMAPPED_PACKAGES)
    return {"kind": "package", "package": package, "version": rng.choice(PKG_VERSIONS)}


def _artifact_element(rng: random.Random, slug: str) -> str:
    repo = rng.choice(PROJECTS[slug]["repos"] + UNMAPPED_REPOS[:1])
    form = rng.choice(["repo", "tag", "version", "any", "object", "ns", "ns-version"])
    if form == "repo":
        return repo
    if form == "tag":
        return f"{repo}:{rng.choice(['7.2', '8.0', 'latest'])}"
    if form == "version":
        return f"{repo}:<version>"
    if form == "any":
        return f"{repo}:*"
    if form == "object":
        return f"{repo}@{rng.choice(DIGESTS)}"
    namespace = repo.rsplit("/", 1)[0] if repo.count("/") >= 2 else "docker.io/library"
    return f"{namespace}/*" if form == "ns" else f"{namespace}/*:<version>"


def random_event(rng: random.Random, index: int) -> dict:
    slug = rng.choice(list(PROJECTS))
    kind = rng.choice([None, "artifact", "artifact", "version", "package", "registry"])
    size = rng.randint(1, 4)
    if kind == "artifact":
        values = [_artifact_element(rng, slug) for _ in range(size)]
    elif kind == "version":
        values = rng.sample(PROJECTS[slug]["lines"], min(size, len(PROJECTS[slug]["lines"])))
    elif kind == "package":
        values = rng.sample(PROJECTS[slug]["packages"] + ["other-pkg"], 1 + (size > 2))
    elif kind == "registry":
        values = [rng.choice(["docker.io", "ghcr.io"])]
    else:
        values = []
    named = [_artifact_element(rng, slug) for _ in range(rng.choice([0, 0, 1, 2]))]
    named = [n for n in named if "*" not in n.rsplit("/", 1)[-1].split(":")[0]]  # no namespaces
    chi = kind is not None and rng.random() < 0.6
    basis = rng.choice([None, "definitional", "announced"]) if chi else None
    admissibility = rng.choices(
        ["current", "contested", "withdrawn", "superseded", "stale"], [6, 1, 1, 1, 1]
    )[0]
    return {
        "id": f"e{index}",
        "slug": slug,
        "kind": kind,
        "values": values,
        "named": named,
        "chi": chi,
        "basis": basis,
        "admissibility": admissibility,
    }


def _identity(dep: dict, slug: str) -> str:
    if dep["kind"] == "image" and dep["ref"].split("@")[0].rsplit(":", 1)[0] in CURATED_OTHER_REPOS:
        return "other"
    owner = _owner(dep["ref"] if dep["kind"] == "image" else dep["package"])
    if owner is None:
        return "unresolved"
    return "project" if owner == slug else "other"


_KIND = {
    "artifact": "artifact",
    "version": "release_line",
    "package": "package",
    "registry": "registry",
}


def oracle_verdict(dep: dict, ev: dict) -> str:
    elements = [oracle.Element("artifact", n, example=True) for n in ev["named"]]
    if ev["kind"] is None:
        elements.append(oracle.Element("project", ev["slug"]))
    else:
        elements += [oracle.Element(_KIND[ev["kind"]], v) for v in ev["values"]]
    o_dep = oracle.Dependency(
        dep["kind"],
        ref=dep.get("ref", ""),
        package=dep.get("package", ""),
        version=dep.get("version"),
        identity=_identity(dep, ev["slug"]),
    )
    event = oracle.Event(
        ev["slug"],
        elements,
        "declared" if ev["chi"] else "partial",
        ev["basis"],
        ev["admissibility"],
    )
    return oracle.applicability(o_dep, event)


AS_OF = FETCHED + timedelta(days=100)
MAX_AGE = timedelta(days=30)


def implementation_event(ev: dict) -> OSSEvent:
    # Only a stale event's evidence is older than the freshness bound.
    fetched = FETCHED if ev["admissibility"] == "stale" else AS_OF - timedelta(days=1)
    source = Source(
        name=f"src/{ev['id']}",
        url="https://example.org/r",
        authority="official",
        fetched_at=fetched,
    )
    evidences = [Evidence(source=source, excerpt="x")]
    if ev["admissibility"] == "contested":
        evidences.append(Evidence(source=source, excerpt="y", relation="contradicts"))
    scope = None
    if ev["kind"] is not None:
        field = {
            "artifact": "artifacts",
            "version": "versions",
            "package": "packages",
            "registry": "registries",
        }[ev["kind"]]
        scope = Scope(
            kind=ev["kind"], exhaustive=ev["chi"], basis=ev["basis"], **{field: list(ev["values"])}
        )
    return OSSEvent(
        id=ev["id"],
        project_slug=ev["slug"],
        event_type="DISTRIBUTION_CHANGE",
        title="r",
        summary="r",
        confidence="CONFIRMED",
        impact="ACTION",
        evidences=evidences,
        affected_artifacts=[Artifact(kind="docker-image", ref=n) for n in ev["named"]],
        scope=scope,
        withdrawn=ev["admissibility"] == "withdrawn",
        superseded_by="later" if ev["admissibility"] == "superseded" else None,
    )


_AFFECTS = {"AFFECTS_ARTIFACT", "AFFECTS_VERSION", "AFFECTS_PACKAGE", "AFFECTS"}
_UNRESOLVED = {"RELATED", "AFFECTS_PROJECT"}


def summary(verdicts: list[str]) -> str:
    """Cross-event summary (report Table 7)."""
    present = {v for v in verdicts if v not in ("UNLOADED",)}
    if present & _AFFECTS:
        return "affected"
    if present & _UNRESOLVED:
        return "unresolved"
    if "NOT_AFFECTED" in present:
        return "cleared"
    return "no association"


_SUMMARY_SEVERITY = {
    ("affected", "cleared"): "unsafe",
    ("unresolved", "cleared"): "unsafe",
    ("affected", "no association"): "unsafe",
    ("unresolved", "no association"): "unsafe",
    ("cleared", "affected"): "false impact",
    ("unresolved", "affected"): "false impact",
    ("no association", "affected"): "false impact",
    ("affected", "unresolved"): "under-positive",
    ("cleared", "unresolved"): "over-cautious",
    ("no association", "unresolved"): "over-cautious",
    ("cleared", "no association"): "label",
    ("no association", "cleared"): "label",
}


def run(cases: int, seed: int) -> dict:
    rng = random.Random(seed)
    severities: Counter = Counter()
    per_event: Counter = Counter()
    examples: dict[str, list] = {}
    for _ in range(cases):
        dep = random_dependency(rng)
        events = [random_event(rng, i) for i in range(rng.randint(1, 3))]
        spec = [oracle_verdict(dep, ev) for ev in events]
        impl_dep = dep if dep["kind"] == "image" else {**dep, "ecosystem": "PyPI"}
        verdict = check_dependency(
            impl_dep,
            [implementation_event(ev) for ev in events],
            as_of=AS_OF,
            max_evidence_age=MAX_AGE,
        )
        by_event = {
            str(c.get("event_id")): str(c.get("relationship"))
            for c in verdict.verdicts
            if c.get("cause") == "upstream_change"
        }
        for ev, s in zip(events, spec):
            o = summary([s])
            i = summary([by_event.get(ev["id"], "UNKNOWN")])
            per_event["conform" if o == i else _SUMMARY_SEVERITY.get((o, i), "other")] += 1
        spec_summary, impl_summary = summary(spec), summary([verdict.relationship])
        severity = (
            "conform"
            if spec_summary == impl_summary
            else _SUMMARY_SEVERITY.get((spec_summary, impl_summary), "other")
        )
        severities[severity] += 1
        if severity not in ("conform", "label") and len(examples.setdefault(severity, [])) < 5:
            examples[severity].append(
                {
                    "dependency": dep,
                    "events": events,
                    "oracle": spec,
                    "implementation": verdict.relationship,
                    "reason": verdict.reason,
                }
            )
    return {
        "seed": seed,
        "cases": cases,
        "summary_severity": dict(severities),
        "per_event_severity": dict(per_event),
        "examples": examples,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    result = run(args.cases, args.seed)
    out = ROOT / "conformance" / "results"
    out.mkdir(exist_ok=True)
    (out / "randomized.json").write_text(
        json.dumps(result, indent=1, default=str), encoding="utf-8"
    )
    print(f"seed {result['seed']}, {result['cases']} cases")
    for label in ("summary_severity", "per_event_severity"):
        print(label)
        for severity, count in sorted(result[label].items(), key=lambda kv: -kv[1]):
            print(f"{count:7}  {severity}")

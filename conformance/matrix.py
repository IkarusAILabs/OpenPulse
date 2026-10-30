"""Generated conformance matrix: specification oracle vs implementation.

Run from the repository root:

    python conformance/matrix.py   # summary; writes counts and every disagreement

Every case is one dependency against one event. The oracle (``oracle.py``)
decides from the report's text. The implementation decides through
``core.risk.check.check_dependency`` on the equivalent ``OSSEvent``.
Every disagreement is recorded and classified by severity; none is
silently dropped.
"""

from __future__ import annotations

import itertools
import json
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

PROJECT = "redis"
FETCHED = datetime(2026, 10, 28, tzinfo=timezone.utc)
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64

#: Dependencies with ground-truth identity, by the curated catalog's
#: meaning: docker.io/library/redis and the PyPI name "redis" are curated
#: as project redis, docker.io/library/mysql as mysql, and the zzz/ names
#: are unmapped. ``docker.io/redis`` is Docker's own spelling of
#: ``docker.io/library/redis``.
IMAGES = [
    ("docker.io/library/redis:7.2", "project"),
    ("docker.io/library/redis:7.2.4-alpine", "project"),
    ("docker.io/library/redis:8.0", "project"),
    ("docker.io/library/redis:latest", "project"),
    ("docker.io/library/redis", "project"),
    (f"docker.io/library/redis@{DIGEST_A}", "project"),
    (f"docker.io/library/redis@{DIGEST_B}", "project"),
    ("docker.io/redis:7.2", "project"),
    ("index.docker.io/library/redis:7.2", "project"),
    ("docker.io/library/mysql:8.0", "other"),
    ("docker.io/zzz/kvstore:7.2", "unresolved"),
    (f"docker.io/zzz/kvstore@{DIGEST_A}", "unresolved"),
    ("ghcr.io/zzz/redis:7.2", "unresolved"),
]
PACKAGES = [
    ("redis", "7.2.0", "project"),
    ("redis", None, "project"),
    ("redis-server", "7.2.0", "project"),  # a name that is not the slug (F2)
    ("mysql", "8.0.1", "other"),
    ("zzzpkg", "1.0", "unresolved"),
    # With a stated ecosystem (F3): PyPI `redis` is redis-py and npm `redis`
    # node-redis, both curated as other projects; PyPI `mysql` is unmapped.
    ("redis", "6.2.0", "other", "PyPI"),
    ("redis", "4.6.0", "other", "npm"),
    ("mysql", "8.0.1", "unresolved", "PyPI"),
]

#: Scopes, each as (label, implementation scope kind, values, named artifacts).
SCOPES = [
    ("project", None, [], []),
    ("project+named-tag", None, [], ["docker.io/library/redis:7.2"]),
    ("repository", "artifact", ["docker.io/library/redis"], []),
    ("tag", "artifact", ["docker.io/library/redis:7.2"], []),
    ("repo:<version>", "artifact", ["docker.io/library/redis:<version>"], []),
    ("repo:*", "artifact", ["docker.io/library/redis:*"], []),
    ("object", "artifact", [f"docker.io/library/redis@{DIGEST_A}"], []),
    ("namespace envelope", "artifact", ["docker.io/library/*"], []),
    ("namespace:<version>", "artifact", ["docker.io/library/*:<version>"], []),
    (
        "namespace:<version>+envelope",
        "artifact",
        ["docker.io/library/*:<version>", "docker.io/library/*"],
        [],
    ),
    ("other repository", "artifact", ["docker.io/bitnami/redis"], []),
    ("release line 7.2", "version", ["7.2"], []),
    ("release line 7", "version", ["7"], []),
    ("package redis", "package", ["redis"], []),
    ("package redis-py", "package", ["redis-py"], []),
    ("package zzzpkg (bare)", "package", ["zzzpkg"], []),
    ("package pkg:pypi/redis", "package", ["pkg:pypi/redis"], []),
    ("package pkg:npm/redis", "package", ["pkg:npm/redis"], []),
    ("package pkg:pypi/mysql + bare redis", "package", ["pkg:pypi/mysql", "redis"], []),
    ("registry docker.io", "registry", ["docker.io"], []),
    ("registry ghcr.io", "registry", ["ghcr.io"], []),
]
COMPLETENESS = [
    ("partial", False, None),
    ("declared, no basis", True, None),
    ("declared, definitional", True, "definitional"),
]
ADMISSIBILITY = ["current", "contested", "withdrawn", "superseded", "stale"]

_ORACLE_ELEMENT_KIND = {
    "artifact": "artifact",
    "version": "release_line",
    "package": "package",
    "registry": "registry",
}


def oracle_event(scope_kind, values, named, chi, basis, admissibility) -> oracle.Event:
    elements = [oracle.Element("artifact", ref, example=True) for ref in named]
    if scope_kind is None:
        elements.append(oracle.Element("project", PROJECT))
    else:
        kind = _ORACLE_ELEMENT_KIND[scope_kind]
        elements += [oracle.Element(kind, v) for v in values]
    return oracle.Event(PROJECT, elements, "declared" if chi else "partial", basis, admissibility)


def implementation_event(scope_kind, values, named, chi, basis, admissibility) -> OSSEvent:
    source = Source(
        name="conformance/source",
        url="https://example.org/c",
        authority="official",
        fetched_at=FETCHED,
    )
    evidences = [Evidence(source=source, excerpt="announced")]
    if admissibility == "contested":
        evidences.append(Evidence(source=source, excerpt="disputed", relation="contradicts"))
    scope = None
    if scope_kind is not None:
        field = {
            "artifact": "artifacts",
            "version": "versions",
            "package": "packages",
            "registry": "registries",
        }[scope_kind]
        scope = Scope(kind=scope_kind, exhaustive=chi, basis=basis, **{field: list(values)})
    return OSSEvent(
        id="conformance",
        project_slug=PROJECT,
        event_type="DISTRIBUTION_CHANGE",
        title="c",
        summary="c",
        confidence="CONFIRMED",
        impact="ACTION",
        evidences=evidences,
        affected_artifacts=[Artifact(kind="docker-image", ref=r) for r in named],
        scope=scope,
        withdrawn=admissibility == "withdrawn",
        superseded_by="conformance-2" if admissibility == "superseded" else None,
    )


_FAMILY = {
    "AFFECTS_ARTIFACT": "AFFECTS",
    "AFFECTS_VERSION": "AFFECTS",
    "AFFECTS_PACKAGE": "AFFECTS",
}


def classify(spec: str, impl: str) -> str:
    """Severity of a disagreement, from the implementation's side."""
    spec = "UNKNOWN" if spec == "UNLOADED" else spec
    if spec == impl:
        return "conform"
    unresolved = {"RELATED", "AFFECTS_PROJECT"}
    if impl == "NOT_AFFECTED" and spec in unresolved | {"AFFECTS"}:
        return "unsafe: clears what the specification does not"
    if impl == "UNKNOWN" and spec in unresolved | {"AFFECTS"}:
        return "unsafe: drops an association the specification keeps"
    if impl == "AFFECTS":
        return "false impact: positive the specification does not support"
    if spec == "AFFECTS":
        return "under-positive: specification is affected, implementation unresolved"
    if impl in unresolved and spec in {"NOT_AFFECTED", "UNKNOWN"}:
        return "over-cautious: implementation withholds a decisive verdict"
    if {impl, spec} <= unresolved:
        return "label: both unresolved"
    return "label: both non-blocking (no association vs exclusion)"


def cases():
    deps = [oracle.Dependency("image", ref=r, identity=i) for r, i in IMAGES]
    deps += [
        oracle.Dependency("package", package=p, version=v, identity=i, ecosystem=e)
        for p, v, i, *rest in PACKAGES
        for e in [rest[0] if rest else ""]
    ]
    for (label, kind, values, named), (clabel, chi, basis), adm in itertools.product(
        SCOPES, COMPLETENESS, ADMISSIBILITY
    ):
        if kind is None and clabel != "partial":
            continue  # a project-wide event has no completeness to declare
        for dep in deps:
            yield {
                "scope": label,
                "completeness": clabel,
                "admissibility": adm,
                "dep": dep,
                "event": (kind, values, named, chi, basis, adm),
            }


def run() -> dict:
    rows = []
    for case in cases():
        dep: oracle.Dependency = case["dep"]
        spec = oracle.applicability(dep, oracle_event(*case["event"]))
        if dep.kind == "image":
            impl_dep = {"kind": "image", "ref": dep.ref}
        else:
            impl_dep = {
                "kind": "package",
                "package": dep.package,
                # Without an ecosystem the package stands for the project of
                # its name; with one, PACKAGES records its curated identity.
                "ecosystem": dep.ecosystem,
                "version": dep.version,
            }
        stale = case["admissibility"] == "stale"
        verdict = check_dependency(
            impl_dep,
            [implementation_event(*case["event"])],
            as_of=FETCHED + timedelta(days=100) if stale else None,
            max_evidence_age=timedelta(days=30) if stale else None,
        )
        impl = _FAMILY.get(verdict.relationship, verdict.relationship)
        rows.append(
            {
                "scope": case["scope"],
                "completeness": case["completeness"],
                "admissibility": case["admissibility"],
                "dependency": dep.ref or f"{dep.package}=={dep.version}",
                "identity": dep.identity,
                "specification": spec,
                "implementation": impl,
                "severity": classify(spec, impl),
                "reason": verdict.reason,
            }
        )
    return {
        "cases": len(rows),
        "rows": rows,
        "by_severity": dict(Counter(r["severity"] for r in rows)),
    }


if __name__ == "__main__":
    result = run()
    out = ROOT / "conformance" / "results"
    out.mkdir(exist_ok=True)
    # Counts plus every disagreement; conforming rows are regenerable.
    recorded = {
        "cases": result["cases"],
        "by_severity": result["by_severity"],
        "disagreements": [r for r in result["rows"] if r["severity"] != "conform"],
    }
    (out / "matrix.json").write_text(json.dumps(recorded, indent=1), encoding="utf-8")
    print(f"{result['cases']} cases")
    for severity, count in sorted(result["by_severity"].items(), key=lambda kv: -kv[1]):
        print(f"{count:6}  {severity}")

"""Defect re-injection: does the harness catch each known failure class?

Run from the repository root:

    python conformance/mutation.py     # writes conformance/results/mutation.json

Each mutant re-introduces one historical defect (D1-D15) or disables one
enforced rule (N3-N5, roles, S2) by patching a single function of the
running implementation. Three detectors are then run against it:

  A  the oracle conformance matrix (any change from the clean baseline);
  B  randomised differential testing, 5,000 cases (any disagreement);
  C  the false-clear regression tests (tests/test_false_clear.py);
  D  the version differential tests against ``packaging`` (PEP 440).

A mutant is *caught* if any detector reports it. Mutants that cannot be
expressed as one function-level change of the current code (D2, D6) are
listed as not re-injected rather than approximated.
"""

from __future__ import annotations

import contextlib
import importlib
import inspect
import io
import json
import sys
import textwrap
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import matrix  # noqa: E402
import randomized  # noqa: E402
import versions_differential  # noqa: E402

#: Modules whose imported names must follow a patched function.
_MODULES = [
    "core.versions",
    "core.entities.resolve",
    "core.entities.identity",
    "core.risk.match",
    "core.risk.check",
    "core.schema.models",
    "analyzers.security_analyst",
    "core.observations.sweep",
    "core.agent_tools",
    "matrix",
    "randomized",
]

#: (id, what it re-introduces, module, function, old text, new text)
MUTANTS = [
    (
        "D1",
        "first unequal digest of a repository excludes",
        "core.risk.match",
        "_artifact_candidates",
        """            if policy["relationship"] == "RELATED":
                undetermined = undetermined or policy""",
        """            if policy["relationship"] == "RELATED":
                return {**policy, "relationship": "NOT_AFFECTED"}""",
    ),
    (
        "D3",
        "a clearance headlines over an unresolved event",
        "core.risk.check",
        "winning_cause",
        """    if str(top.get("relationship")) != "NOT_AFFECTED":
        return top""",
        """    if True:
        return top""",
    ),
    (
        "D4",
        "unspecified completeness admits negatives",
        "core.schema.models",
        "Scope.admits_negative",
        "return self.exhaustive and self.basis is not None",
        "return True",
    ),
    (
        "N3",
        "a declaration without a basis admits negatives",
        "core.schema.models",
        "Scope.admits_negative",
        "return self.exhaustive and self.basis is not None",
        "return self.exhaustive",
    ),
    (
        "D10",
        "unmapped references are unrelated",
        "core.risk.match",
        "_unresolved_identity",
        """    if trust["via"] != "self" or UNRESOLVED_IDENTITY.get() == "unrelated":
        return None""",
        """    if True:
        return None""",
    ),
    (
        "D7",
        "tags are ignored",
        "core.risk.match",
        "_tag_membership",
        "    return dep_tag == element_tag",
        "    return True",
    ),
    (
        "Roles",
        "envelopes give positives",
        "core.risk.match",
        "element_role",
        '        return "envelope"',
        '        return "exact"',
    ),
    (
        "D8",
        "pre-release numbers are ignored",
        "core.versions",
        "_key",
        'return (nums, rank, int(match["num"] or 0))',
        "return (nums, rank, 0)",
    ),
    (
        "D9",
        "Docker Hub host aliases are other registries",
        "core.entities.resolve",
        "normalize_ref",
        '    r = _DOCKER_HUB_HOSTS.sub(r"\\1docker.io/", r)\n',
        "",
    ),
    (
        "D11",
        "SEMVER ranges use the generic marker table",
        "core.versions",
        "range_scheme",
        '        return "semver"',
        '        return "pep440"',
    ),
    (
        "D12",
        "docker.io/<name> is namespace docker.io",
        "core.risk.match",
        "split_image_ref",
        "if len(parts) >= 2 and",
        "if len(parts) >= 3 and",
    ),
    (
        "D13",
        "unmapped packages are unrelated",
        "core.risk.check",
        "_scope_cause",
        """        if trust["via"] != "self" or UNRESOLVED_IDENTITY.get() == "unrelated":
            return None  # curated as another project: no association""",
        """        if True:
            return None  # curated as another project: no association""",
    ),
    (
        "D14",
        "repository elements do not cover digest pins",
        "core.risk.match",
        "_artifact_candidates",
        "        if digest_of(candidate) is None and element_tag in (None, TAG_ANY):",
        "        if False:",
    ),
    (
        "D15",
        "a named example hides the scope",
        "core.risk.match",
        "_event_affects_ref",
        "    return _strongest(named, scoped) or scoped",
        "    return named or scoped",
    ),
    (
        "N4-withdrawn",
        "withdrawn and superseded events are evaluated",
        "core.risk.check",
        "_check_dependency",
        "    events = [event for event in events if event.is_current_record()]",
        "    events = list(events)",
    ),
    (
        "N4-stale",
        "stale events may clear",
        "core.risk.check",
        "inadmissible_reason",
        "        if as_of - newest > max_evidence_age:",
        "        if False:",
    ),
    (
        "N5",
        "contested events may clear",
        "core.risk.check",
        "inadmissible_reason",
        '    if any(e.relation == "contradicts" for e in event.evidences):',
        "    if False:",
    ),
    (
        "Package",
        "package-name inequality excludes",
        "core.risk.check",
        "_scope_cause",
        """            "relationship": "RELATED",
            "affected": False,
            "match_method": "event_scope_package",""",
        """            "relationship": "NOT_AFFECTED",
            "affected": False,
            "match_method": "event_scope_package",""",
    ),
    (
        "S2",
        "a curated other project is excluded, not unassociated",
        "core.risk.match",
        "_scope_result",
        '''                "relationship": "UNKNOWN",
                "detail": (
                    f"{ref} resolves to project {slug}, not {event.project_slug}: "''',
        '''                "relationship": "NOT_AFFECTED",
                "detail": (
                    f"{ref} resolves to project {slug}, not {event.project_slug}: "''',
    ),
]
NOT_REINJECTED = {
    "D2": "union of OSV intervals: a multi-line walk, not a one-function change",
    "D5": "heuristic exclusion: subsumed by D10 and S2 in the current resolver",
    "D6": "epochs: the closed grammar rejects them before any comparison",
}


def _resolve(module_name: str, qualname: str):
    module = importlib.import_module(module_name)
    owner, name = module, qualname
    if "." in qualname:
        cls, name = qualname.split(".")
        owner = getattr(module, cls)
    return module, owner, name, getattr(owner, name)


@contextlib.contextmanager
def mutated(module_name: str, qualname: str, old: str, new: str):
    module, owner, name, original = _resolve(module_name, qualname)
    source = textwrap.dedent(inspect.getsource(original))
    if source.count(old.strip("\n")) != 1 and source.count(textwrap.dedent(old)) != 1:
        raise ValueError(f"mutation anchor not found once in {qualname}")
    needle = old if source.count(old) == 1 else textwrap.dedent(old)
    patched = source.replace(needle, new if needle == old else textwrap.dedent(new))
    namespace = dict(vars(module))
    exec(compile(patched, f"<mutant {qualname}>", "exec"), namespace)  # noqa: S102
    replacement = namespace[name]
    rebound = []
    setattr(owner, name, replacement)
    for other in _MODULES:
        mod = importlib.import_module(other)
        for attr, value in list(vars(mod).items()):
            if value is original:
                setattr(mod, attr, replacement)
                rebound.append((mod, attr))
    try:
        yield
    finally:
        setattr(owner, name, original)
        for mod, attr in rebound:
            setattr(mod, attr, original)


def _matrix_signature() -> Counter:
    result = matrix.run()
    return Counter(
        (r["scope"], r["completeness"], r["admissibility"], r["dependency"], r["severity"])
        for r in result["rows"]
        if r["severity"] != "conform"
    )


def _randomized_failures() -> int:
    result = randomized.run(5000, 2026)
    return sum(v for k, v in result["summary_severity"].items() if k != "conform")


def _differential_failures() -> int:
    result = versions_differential.run()
    return (
        len(result["pep440_pairs"]["disagreements"])
        + len(result["pypi_ranges"]["disagreements"])
        + len(result["semver"]["vector_failures"])
        + result["semver"]["order_inconsistencies"]
        + len(result["semver"]["range_failures"])
    )


def _regression_failures() -> int:
    import pytest

    for name in [m for m in sys.modules if m.startswith("tests.") or m == "test_false_clear"]:
        del sys.modules[name]
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = pytest.main(
            [
                "-q",
                "-p",
                "no:cacheprovider",
                "-x",
                "--no-header",
                str(ROOT / "tests" / "test_false_clear.py"),
            ]
        )
    return 0 if code == 0 else 1


def main() -> None:
    baseline = {
        "matrix": _matrix_signature(),
        "random": _randomized_failures(),
        "tests": _regression_failures(),
        "versions": _differential_failures(),
    }
    assert baseline["random"] == baseline["tests"] == baseline["versions"] == 0, baseline
    rows = []
    for mutant_id, description, module, qualname, old, new in MUTANTS:
        with mutated(module, qualname, old, new):
            a = _matrix_signature() != baseline["matrix"]
            b = _randomized_failures() > 0
            c = _regression_failures() > 0
            d = _differential_failures() > 0
        rows.append(
            {
                "mutant": mutant_id,
                "reintroduces": description,
                "matrix": a,
                "randomized": b,
                "regression_tests": c,
                "version_differential": d,
                "caught": a or b or c or d,
                "caught_without_regression_tests": a or b or d,
            }
        )
        print(
            f"{mutant_id:13} matrix={a!s:5} random={b!s:5} tests={c!s:5} "
            f"versions={d!s:5}  {description}"
        )
    caught = sum(r["caught"] for r in rows)
    independent = sum(r["caught_without_regression_tests"] for r in rows)
    print(
        f"caught {caught} of {len(rows)} mutants ({independent} without the regression "
        f"tests); not re-injected: {sorted(NOT_REINJECTED)}"
    )
    out = ROOT / "conformance" / "results"
    out.mkdir(exist_ok=True)
    (out / "mutation.json").write_text(
        json.dumps(
            {
                "mutants": rows,
                "caught": caught,
                "total": len(rows),
                "caught_without_regression_tests": independent,
                "not_reinjected": NOT_REINJECTED,
            },
            indent=1,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

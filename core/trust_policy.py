"""Trust policy: conditions the user prohibits, evaluated without a model (T-E1).

Advisory MCP answers are not a security boundary: an agent can skip the
call or ignore the answer (threat T11). A policy file makes chosen trust
conditions fail ``openpulse check`` and ``openpulse attest`` (and the
GitHub Action) deterministically. Nothing blocks unless the policy names
it: with no policy, gates behave exactly as before.

``.openpulse/policy.yml``::

    version: 1
    prohibit:
      - confirmed_malicious            # any package
      - not_found_in_registry
      - condition: lookalike_name      # indicators need a package scope
        packages: ["npm:@acme/*"]
      - condition: missing_provenance  # "provenance required for these"
        packages: ["PyPI:acme-*"]
    blocklist:
      - "npm:event-stream"
      - "PyPI:requests==2.19.0"

A condition maps to one trust check and one T-F1 status. Failed checks and
cited records (``measured`` in ``docs/research/TRACK_T_MEASUREMENTS.md``)
may be prohibited for any package. Indicators fire on legitimate packages
(lookalike flags 18.8% of real popular npm names), so they must name the
packages they apply to; conditions without an organic false-positive set
are ``experimental`` and say so when used. MISSING_EVIDENCE and
NOT_PERFORMED never block by themselves, only through a scoped condition.
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_POLICY = Path(".openpulse") / "policy.yml"
MAX_POLICY_BYTES = 64 * 1024
MAX_PATTERNS = 1000

#: condition -> (check, status, needs a package scope, measurement label)
CONDITIONS: dict[str, tuple[str, str, bool, str]] = {
    "confirmed_malicious": ("malicious", "CONFIRMED_MALICIOUS", False, "measured"),
    "not_found_in_registry": ("registry_existence", "VERIFIED_FAILURE", False, "measured"),
    "digest_mismatch": ("digest_integrity", "VERIFIED_FAILURE", False, "measured"),
    "provenance_failure": ("provenance", "VERIFIED_FAILURE", False, "measured"),
    "repository_mismatch": ("repository_linkage", "VERIFIED_FAILURE", False, "measured"),
    "lookalike_name": ("lookalike", "SUSPICIOUS_INCONCLUSIVE", True, "indicator"),
    "public_private_name": (
        "dependency_confusion",
        "SUSPICIOUS_INCONCLUSIVE",
        True,
        "experimental",
    ),
    "unconfirmed_repository": (
        "repository_linkage",
        "SUSPICIOUS_INCONCLUSIVE",
        True,
        "experimental",
    ),
    "missing_provenance": ("provenance", "MISSING_EVIDENCE", True, "measured"),
    # Reputation indicators (track T Phase 2, T-C, v0.16.0): each fires on
    # legitimate packages at the organic rate measured, so each needs a scope.
    "publisher_change": ("publisher_change", "SUSPICIOUS_INCONCLUSIVE", True, "indicator"),
    "repository_moved": ("repository_moved", "SUSPICIOUS_INCONCLUSIVE", True, "indicator"),
    "young_popular_repository": (
        "young_popular_repository",
        "SUSPICIOUS_INCONCLUSIVE",
        True,
        "experimental",
    ),
}
BLOCKLISTED = "blocklisted"

_PATTERN = re.compile(r"([A-Za-z][A-Za-z0-9.-]{0,30}):([^\s=]{1,214})(?:==([^\s]{1,128}))?")


class PolicyError(ValueError):
    """The policy file is not valid; the message says why."""


@dataclass(frozen=True)
class Rule:
    condition: str
    packages: tuple[tuple[str, str, str | None], ...] = ()  # (ecosystem, name glob, version)


@dataclass
class Policy:
    rules: list[Rule] = field(default_factory=list)
    blocklist: tuple[tuple[str, str, str | None], ...] = ()
    source: str = ""

    @property
    def needs_trust(self) -> bool:
        return any(CONDITIONS[r.condition][0] != "digest_integrity" for r in self.rules)

    @property
    def needs_digests(self) -> bool:
        return any(CONDITIONS[r.condition][0] == "digest_integrity" for r in self.rules)

    @property
    def experimental(self) -> list[str]:
        return sorted(
            {r.condition for r in self.rules if CONDITIONS[r.condition][3] == "experimental"}
        )


def _normalize(ecosystem: str, name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower() if ecosystem == "pypi" else name.lower()


def _pattern(value: Any, where: str) -> tuple[str, str, str | None]:
    match = _PATTERN.fullmatch(str(value).strip()) if isinstance(value, str) else None
    if not match:
        raise PolicyError(f"{where}: expected ECOSYSTEM:NAME or ECOSYSTEM:NAME==VERSION")
    ecosystem = match.group(1).lower()
    return ecosystem, _normalize(ecosystem, match.group(2)), match.group(3)


def _patterns(values: Any, where: str) -> tuple[tuple[str, str, str | None], ...]:
    if not isinstance(values, list) or not values:
        raise PolicyError(f"{where}: expected a non-empty list of package patterns")
    if len(values) > MAX_PATTERNS:
        raise PolicyError(f"{where}: more than {MAX_PATTERNS} patterns")
    return tuple(_pattern(v, f"{where}[{i}]") for i, v in enumerate(values))


def parse(doc: Any, source: str = "") -> Policy:
    """A validated Policy from the YAML document; PolicyError with the reason otherwise."""
    if not isinstance(doc, dict):
        raise PolicyError("policy: expected a mapping with version, prohibit and blocklist")
    unknown = set(doc) - {"version", "prohibit", "blocklist"}
    if unknown:
        raise PolicyError(f"policy: unknown key(s) {', '.join(sorted(map(str, unknown)))}")
    if doc.get("version") != 1:
        raise PolicyError("policy: version must be 1")
    rules: list[Rule] = []
    for i, entry in enumerate(doc.get("prohibit") or []):
        where = f"prohibit[{i}]"
        if isinstance(entry, str):
            entry = {"condition": entry}
        if not isinstance(entry, dict) or set(entry) - {"condition", "packages"}:
            raise PolicyError(f"{where}: expected a condition name or {{condition, packages}}")
        condition = entry.get("condition")
        if condition not in CONDITIONS:
            raise PolicyError(f"{where}: unknown condition; one of {', '.join(sorted(CONDITIONS))}")
        packages = _patterns(entry["packages"], f"{where}.packages") if "packages" in entry else ()
        if CONDITIONS[condition][2] and not packages:
            raise PolicyError(
                f"{where}: {condition} is an indicator and fires on legitimate packages "
                "(docs/research/TRACK_T_MEASUREMENTS.md); name the packages it applies to"
            )
        rules.append(Rule(condition, packages))
    blocklist = _patterns(doc["blocklist"], "blocklist") if doc.get("blocklist") else ()
    if not rules and not blocklist:
        raise PolicyError("policy: prohibits nothing; add prohibit or blocklist entries")
    return Policy(rules=rules, blocklist=blocklist, source=source)


def load(path: str | Path) -> Policy:
    """Read and validate a policy file (bounded read, YAML safe_load)."""
    import yaml

    from core.bounded_io import read_text

    try:
        doc = yaml.safe_load(read_text(str(path), MAX_POLICY_BYTES, "policy"))
    except yaml.YAMLError as exc:
        raise PolicyError(f"{path}: not valid YAML ({exc.__class__.__name__})") from None
    return parse(doc, source=str(path))


def _matches(patterns: tuple[tuple[str, str, str | None], ...], dep: dict[str, Any]) -> bool:
    if dep.get("kind") != "package":
        return False
    ecosystem = str(dep.get("ecosystem") or "").lower()
    name = _normalize(ecosystem, str(dep.get("package") or ""))
    version = dep.get("version")
    return any(
        eco == ecosystem
        and fnmatch.fnmatchcase(name, glob)
        and (pinned is None or pinned == str(version))
        for eco, glob, pinned in patterns
    )


def evaluate(policy: Policy, dep: dict[str, Any], records: list[dict[str, Any]]) -> list[dict]:
    """Violations for one dependency, given its trust records ({check, status, statement})."""
    violations: list[dict[str, Any]] = []
    label = _label(dep)
    if policy.blocklist and _matches(policy.blocklist, dep):
        violations.append(
            {
                "condition": BLOCKLISTED,
                "dependency": label,
                "statement": "the package is on the policy's blocklist",
            }
        )
    for rule in policy.rules:
        check, status, _scoped, measured = CONDITIONS[rule.condition]
        if rule.packages and not _matches(rule.packages, dep):
            continue
        for record in records:
            if record.get("check") == check and record.get("status") == status:
                violations.append(
                    {
                        "condition": rule.condition,
                        "dependency": label,
                        "check": check,
                        "status": status,
                        "statement": record.get("statement", ""),
                        "label": measured,
                    }
                )
                break
    return violations


def _label(dep: dict[str, Any]) -> str:
    if dep.get("kind") != "package":
        return str(dep.get("ref") or "")
    version = f"=={dep['version']}" if dep.get("version") else ""
    return f"{dep.get('ecosystem')}:{dep.get('package')}{version}"


__all__ = [
    "BLOCKLISTED",
    "CONDITIONS",
    "DEFAULT_POLICY",
    "Policy",
    "PolicyError",
    "evaluate",
    "load",
    "parse",
]

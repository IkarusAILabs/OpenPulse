"""The organic reputation set: loading and baseline signal rates (v0.16.0 item Q1).

The set (``benchmarks/fixtures/reputation/organic-<date>.json``, written by
``benchmarks/record_reputation.py``) holds real, legitimate packages. Every
reputation indicator (Q2-Q4) is measured on it before it ships: whatever
fires here fires on legitimate projects.

``baseline`` reports how often the raw signals occur before any rule
narrows them, for example how often the latest release comes from an
account the earlier recorded releases did not use. These are the upper
bounds the indicator rules have to improve on, not indicator rates.
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "reputation"
YOUNG_DAYS = 365


def latest_path() -> Path:
    found = sorted(FIXTURES.glob("organic-*.json"))
    if not found:
        raise FileNotFoundError(f"no organic reputation set in {FIXTURES}")
    return found[-1]


def load(path: Path | None = None) -> dict[str, Any]:
    return json.loads((path or latest_path()).read_text(encoding="utf-8"))


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def _when(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _npm(packages: list[dict[str, Any]]) -> dict[str, Any]:
    recorded = [p for p in packages if p.get("status") == 200 and len(p.get("releases") or []) >= 2]
    releases = [r for p in recorded for r in p["releases"]]
    multi = new = new_untrusted = 0
    for p in recorded:
        accounts = [r["publisher"] for r in p["releases"]]
        multi += len({a for a in accounts if a}) > 1
        latest, earlier = p["releases"][-1], {a for a in accounts[:-1] if a}
        if latest["publisher"] and latest["publisher"] not in earlier:
            new += 1
            new_untrusted += not latest.get("trusted_publisher")
    return {
        "packages": len(packages),
        "recorded": len(recorded),
        "releases": len(releases),
        "releases_attested": _ratio(sum(r["attested"] for r in releases), len(releases)),
        "releases_trusted_publisher": _ratio(
            sum(bool(r.get("trusted_publisher")) for r in releases), len(releases)
        ),
        "packages_with_several_accounts": multi,
        "latest_from_new_account": new,
        "latest_from_new_account_rate": _ratio(new, len(recorded)),
        "latest_from_new_account_not_trusted_publishing": new_untrusted,
        "latest_from_new_account_not_trusted_publishing_rate": _ratio(
            new_untrusted, len(recorded)
        ),
    }


def _pypi(packages: list[dict[str, Any]]) -> dict[str, Any]:
    recorded = [p for p in packages if p.get("status") == 200 and len(p.get("releases") or []) >= 2]
    releases = [r for p in recorded for r in p["releases"]]
    answered = [r for r in releases if r["attested"] is not None]
    attested_any = changed = two_attested = stopped = 0
    for p in recorded:
        attested = [r for r in p["releases"] if r["attested"]]
        attested_any += bool(attested)
        if len(attested) >= 2:
            two_attested += 1
            changed += attested[-1]["publishers"] != attested[-2]["publishers"]
        latest = p["releases"][-1]
        stopped += latest["attested"] is False and any(r["attested"] for r in p["releases"][:-1])
    return {
        "packages": len(packages),
        "recorded": len(recorded),
        "releases": len(releases),
        "releases_unanswered": len(releases) - len(answered),
        "releases_attested": _ratio(sum(bool(r["attested"]) for r in answered), len(answered)),
        "packages_with_attestations": attested_any,
        "packages_with_two_attested_releases": two_attested,
        "latest_attested_publisher_changed": changed,
        "latest_attested_publisher_changed_rate": _ratio(changed, two_attested),
        "attestations_stopped_at_latest": stopped,
        "attestations_stopped_at_latest_rate": _ratio(stopped, attested_any),
    }


def _repositories(repos: dict[str, dict[str, Any]], recorded_at: str) -> dict[str, Any]:
    answered = {k: v for k, v in repos.items() if v.get("status") == 200}
    moved = sum(
        bool(v.get("full_name")) and v["full_name"].lower() != k.lower()
        for k, v in answered.items()
    )
    now = _when(recorded_at)
    young = sum(
        bool(v.get("created")) and (now - _when(v["created"])).days < YOUNG_DAYS
        for v in answered.values()
    )
    stars = [v["stars"] for v in answered.values() if isinstance(v.get("stars"), int)]
    return {
        "repositories": len(repos),
        "answered": len(answered),
        "moved": moved,
        "moved_rate": _ratio(moved, len(answered)),
        "archived": sum(bool(v.get("archived")) for v in answered.values()),
        "younger_than_a_year": young,
        "younger_than_a_year_rate": _ratio(young, len(answered)),
        "median_stars": statistics.median(stars) if stars else None,
    }


def baseline(doc: dict[str, Any] | None = None) -> dict[str, Any]:
    doc = doc or load()
    packages = doc["packages"]
    return {
        "recorded_at": doc["recorded_at"],
        "releases_per_package": doc["releases_per_package"],
        "selection": doc["selection"],
        "npm": _npm([p for p in packages if p["ecosystem"] == "npm"]),
        "PyPI": _pypi([p for p in packages if p["ecosystem"] == "PyPI"]),
        "repositories": _repositories(doc["repositories"], doc["recorded_at"]),
    }


def publisher_change(doc: dict[str, Any] | None = None) -> dict[str, Any]:
    """The production publisher-change rules (v0.16.0 Q2) on every recorded release.

    Each release is compared with the recorded releases before it, within the
    check's window (npm ``NPM_WINDOW``, PyPI ``PYPI_WINDOW``). Every legitimate
    release a rule flags is a false positive of that rule.
    """
    from core import publisher_change as pc

    doc = doc or load()
    out: dict[str, Any] = {}
    for ecosystem, rules, window in (
        ("npm", pc.npm_rules, pc.NPM_WINDOW),
        ("PyPI", pc.pypi_rules, pc.PYPI_WINDOW),
    ):
        compared = 0
        statuses: dict[str, int] = {}
        fired: dict[str, int] = {}
        packages: dict[str, set[str]] = {}
        changed: dict[str, int] = {}
        latest = latest_compared = 0
        for p in doc["packages"]:
            if p["ecosystem"] != ecosystem or p.get("status") != 200:
                continue
            releases = p.get("releases") or []
            for i in range(1, len(releases)):
                status, names, _why = rules(releases[i], releases[max(0, i - window) : i])
                compared += 1
                statuses[status] = statuses.get(status, 0) + 1
                for rule in names:
                    fired[rule] = fired.get(rule, 0) + 1
                    packages.setdefault(rule, set()).add(p["name"])
                if "publisher_changed" in names:
                    earlier = [e for e in releases[max(0, i - window) : i] if e.get("attested")]
                    for field in pc.changed_fields(releases[i], earlier[-1]):
                        changed[field] = changed.get(field, 0) + 1
                if i == len(releases) - 1:
                    latest_compared += 1
                    latest += bool(names)
        out[ecosystem] = {
            "releases_compared": compared,
            "statuses": dict(sorted(statuses.items())),
            "flagged": statuses.get("SUSPICIOUS_INCONCLUSIVE", 0),
            "false_positive_rate": _ratio(statuses.get("SUSPICIOUS_INCONCLUSIVE", 0), compared),
            "by_rule": {
                rule: {
                    "releases": count,
                    "rate": _ratio(count, compared),
                    "packages": len(packages[rule]),
                }
                for rule, count in sorted(fired.items())
            },
            "publisher_changed_fields": dict(sorted(changed.items())),
            "latest_release_flagged": latest,
            "latest_release_rate": _ratio(latest, latest_compared),
        }
    return out


def repository_moved(doc: dict[str, Any] | None = None) -> dict[str, Any]:
    """The production ``repository_moved`` classification (v0.16.0 Q3) on every
    recorded repository. Every package is legitimate, so every move flagged is a
    false positive. Claims the current parser rejects (GitHub pages such as
    ``sponsors/<user>``, which the 2026-11-02 recording still took from Funding
    links) are excluded and counted.
    """
    from core import repository_moved as rm
    from core.repository_linkage import github_repository

    doc = doc or load()
    statuses: dict[str, int] = {}
    moves: dict[str, int] = {}
    excluded = 0
    for claimed, repo in sorted(doc["repositories"].items()):
        if github_repository(claimed) is None:
            excluded += 1
            continue
        if repo.get("status") == 404:
            status = "MISSING_EVIDENCE"
        elif repo.get("status") == 200 and repo.get("full_name"):
            status, move = rm.classify(claimed, repo["full_name"])
            if move:
                moves[move] = moves.get(move, 0) + 1
        else:
            status = "NOT_PERFORMED"
        statuses[status] = statuses.get(status, 0) + 1
    answered = statuses.get("SUSPICIOUS_INCONCLUSIVE", 0) + statuses.get(
        "VERIFIED_RELATIONSHIP", 0
    )
    flagged = statuses.get("SUSPICIOUS_INCONCLUSIVE", 0)
    return {
        "repositories": len(doc["repositories"]) - excluded,
        "excluded_not_repositories": excluded,
        "statuses": dict(sorted(statuses.items())),
        "answered": answered,
        "flagged": flagged,
        "false_positive_rate": _ratio(flagged, answered),
        "moves": dict(sorted(moves.items())),
    }


def young_popular_repository(doc: dict[str, Any] | None = None) -> dict[str, Any]:
    """The production ``young_popular_repository`` rule (v0.16.0 Q4) on every
    recorded repository, aged at the recording time. Every package is
    legitimate, so every repository flagged is a false positive. The rate is
    only as informative as the number of young repositories in the set, which
    is reported beside it.
    """
    from core import young_popular_repository as yp
    from core.repository_linkage import github_repository

    doc = doc or load()
    now = _when(doc["recorded_at"])
    judged = young = flagged = 0
    fired: list[str] = []
    for claimed, repo in sorted(doc["repositories"].items()):
        if github_repository(claimed) is None or repo.get("status") != 200:
            continue
        if not repo.get("created") or not isinstance(repo.get("stars"), int):
            continue
        judged += 1
        age = max(0, (now - _when(repo["created"])).days)
        young += age < yp.MAX_AGE_DAYS
        if yp.fires(age, repo["stars"]):
            flagged += 1
            fired.append(repo.get("full_name") or claimed)
    return {
        "max_age_days": yp.MAX_AGE_DAYS,
        "min_stars": yp.MIN_STARS,
        "repositories": judged,
        "younger_than_max_age": young,
        "flagged": flagged,
        "false_positive_rate": _ratio(flagged, judged),
        "flagged_repositories": fired,
    }

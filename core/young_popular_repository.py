"""Young popular repository: many stars on a young repository (track T Phase 2,
T-C, threat T5; v0.16.0 item Q4).

Stars can be bought: He et al. (ICSE 2026, "Six Million (Suspected) Fake
Stars in GitHub") measured the market. A repository younger than ``MAX_AGE_DAYS`` with at least
``MIN_STARS`` stars has a popularity its age has had little time to earn.
Real projects launch to many stars too, so this is an indicator:

- the claimed repository is younger than ``MAX_AGE_DAYS`` and has at least
  ``MIN_STARS`` stars: SUSPICIOUS_INCONCLUSIVE, with the age, the star count
  and both thresholds;
- it is older, or has fewer stars: MISSING_EVIDENCE ("no indicator to
  report"). Stars are inputs, never trust evidence, so no star count ever
  verifies anything;
- no GitHub repository is claimed, or GitHub does not know it:
  MISSING_EVIDENCE;
- unsupported, invalid, GitHub or the registry unreachable or rate-limited,
  no creation date or star count in the answer, budget spent: NOT_PERFORMED.

The organic reputation set holds too few young repositories to measure a
firing rate (``docs/research/TRACK_T_MEASUREMENTS.md``), so the indicator is
experimental. The repository is the one ``repository_moved`` looks up, over
the same GitHub request (one redirect, only within https://api.github.com).
Dates and counts are validated before they appear (T-F3). Nothing here
feeds a verdict.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core import repository_moved
from core.registry_existence import (
    MISSING_EVIDENCE,
    NOT_PERFORMED,
    SUSPICIOUS_INCONCLUSIVE,
    _now,
)
from core.repository_moved import API, FetchJson, answered_name, claimed_repository

CHECK = "young_popular_repository"
MAX_AGE_DAYS = 180
MIN_STARS = 1000

_STATEMENTS = {
    SUSPICIOUS_INCONCLUSIVE: (
        "the claimed repository is younger than {max_age_days} days and has at least "
        "{min_stars} stars; real projects launch to many stars too, and stars are inputs, "
        "never trust evidence, so this is an experimental indicator to check, never a "
        "verdict of manipulation"
    ),
    MISSING_EVIDENCE: "no indicator to report: {why}",
    NOT_PERFORMED: "repository age and stars not checked: {why}",
}
_WHY = {
    "below": "the repository is older or has fewer stars than the thresholds; stars are "
    "never trust evidence, so this verifies nothing",
    "no_repository": "the package claims no GitHub repository",
    "unknown": "GitHub does not know the claimed repository (deleted, private or never existed)",
    "unsupported": "checked for PyPI and npm packages only",
    "invalid": "the name or version does not match the ecosystem's grammar",
    "registry": "the registry gave no usable answer",
    "github": "GitHub gave no usable answer (unreachable, rate-limited, or no creation date "
    "or star count)",
    "offline": "live lookups are off",
    "budget": "the session lookup budget is spent",
    "private": "the package is on your private-name list; a public repository claim does not apply",
}


def created_at(doc: Any) -> datetime | None:
    """The repository's validated creation time (UTC), or None."""
    text = doc.get("created_at") if isinstance(doc, dict) else None
    if not isinstance(text, str) or len(text) > 40:
        return None
    try:
        when = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return when.astimezone(timezone.utc) if when.tzinfo else None


def stars_of(doc: Any) -> int | None:
    """The validated star count, or None."""
    stars = doc.get("stargazers_count") if isinstance(doc, dict) else None
    return stars if type(stars) is int and stars >= 0 else None


def fires(age_days: int, stars: int) -> bool:
    return age_days < MAX_AGE_DAYS and stars >= MIN_STARS


def _record(status: str, why: str = "", **evidence: Any) -> dict:
    return {
        "check": CHECK,
        "status": status,
        "statement": _STATEMENTS[status].format(
            max_age_days=MAX_AGE_DAYS, min_stars=MIN_STARS, why=_WHY.get(why, "")
        ),
        "checked_at": _now(),
        "evidence": evidence,
    }


def not_performed(why: str) -> dict[str, Any]:
    return _record(NOT_PERFORMED, why)


def check(
    ecosystem: str | None,
    name: str,
    version: str | None = None,
    *,
    fetch_json: FetchJson | None = None,
    fetch_github: FetchJson | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """One T-F1 record for one package. Never raises on registry or GitHub trouble."""
    why, claimed, status = claimed_repository(ecosystem, name, version, fetch_json)
    if why in ("unsupported", "invalid"):
        return not_performed(why)
    if why == "registry":
        return _record(NOT_PERFORMED, "registry", http_status=status)
    if why == "no_repository" or claimed is None:
        return _record(MISSING_EVIDENCE, "no_repository")
    fetch = fetch_github or repository_moved.default_fetch_github
    status, repo = fetch(API.format(repo=claimed))
    if status == 404:
        return _record(MISSING_EVIDENCE, "unknown", claimed_repository=claimed)
    answered = answered_name(repo) if status == 200 else None
    created, stars = created_at(repo), stars_of(repo)
    if answered is None or created is None or stars is None:
        return _record(
            NOT_PERFORMED, "github", claimed_repository=claimed, http_status=status or None
        )
    age_days = max(0, ((now or datetime.now(timezone.utc)) - created).days)
    evidence = {
        "claimed_repository": claimed,
        "answered_repository": answered,
        "created": created.date().isoformat(),
        "age_days": age_days,
        "stars": stars,
        "max_age_days": MAX_AGE_DAYS,
        "min_stars": MIN_STARS,
        "url": f"https://github.com/{answered}",
    }
    if fires(age_days, stars):
        return _record(SUSPICIOUS_INCONCLUSIVE, **evidence)
    return _record(MISSING_EVIDENCE, "below", **evidence)


__all__ = [
    "CHECK",
    "MAX_AGE_DAYS",
    "MIN_STARS",
    "check",
    "created_at",
    "fires",
    "not_performed",
    "stars_of",
]

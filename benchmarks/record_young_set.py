"""Record the young organic set: star histories of young, linked repositories
(track T Phase 2, T-C2; study protocol §4, item TR3).

Run from the repository root, with network access:

    GITHUB_TOKEN=... python benchmarks/record_young_set.py

The organic reputation set is popular and old: one repository in it is
younger than 180 days. The star-history indicators matter most for young
repositories, so their false-positive rate has to be measured there. This
recorder builds that control set:

1. **Candidates.** GitHub repository search, one query per creation month of
   the last 12 months (ending 30 days ago, so each has some history) and per
   language (Python, JavaScript, TypeScript): ``stars:>=50 fork:false
   archived:false``, up to ``PER_QUERY`` results each, most-starred first.
2. **Linked both ways.** A candidate is kept only when the registry package
   named like the repository (PyPI for Python, npm otherwise) claims exactly
   that repository, as the production linkage check reads claims. A
   repository promoted with fake stars is rarely also the declared home of
   a published package of the same name; this is the selection's main guard.
3. **No malicious record.** The package has no OSV ``MAL-`` record.
4. **Not flagged.** With ``--exclude`` (StarScout's data directory), any
   repository StarScout flagged is dropped.
5. **Sample.** A fixed-seed sample of ``SAMPLE`` kept repositories; each one's
   weekly star history is recorded as ``record_star_history`` does.

Being young, linked and unflagged makes a fake-star campaign unlikely, not
impossible; the protocol reports that residual risk. Writes
``benchmarks/fixtures/reputation/stars-young-<date>.json``.
"""

from __future__ import annotations

import argparse
import calendar
import json
import random
import sys
import time
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks import record_star_history as stars  # noqa: E402

SEARCH = (
    "https://api.github.com/search/repositories?q={q}&sort=stars&order=desc"
    "&per_page=100&page={page}"
)
LANGUAGES = {"Python": "PyPI", "JavaScript": "npm", "TypeScript": "npm"}
MONTHS = 12
PER_QUERY = 200
MIN_STARS = 50
SAMPLE = 500
SEED = stars.SEED
SEARCH_PAUSE = 2.2  # GitHub allows 30 search requests a minute with a token

Fetch = Callable[[str], tuple[int, Any]]
Query = Callable[[dict[str, Any]], tuple[int, Any]]


def months(today: date, count: int = MONTHS) -> list[tuple[date, date]]:
    """(first, last) day of each of the ``count`` creation months, newest
    first, ending 30 days before ``today``."""
    end = today - timedelta(days=30)
    out = []
    year, month = end.year, end.month
    for _ in range(count):
        last = min(date(year, month, calendar.monthrange(year, month)[1]), end)
        out.append((date(year, month, 1), last))
        year, month = (year, month - 1) if month > 1 else (year - 1, 12)
    return out


def search_queries(today: date) -> list[tuple[str, str]]:
    """(language, query) pairs, in a fixed order."""
    return [
        (
            language,
            f"created:{first.isoformat()}..{last.isoformat()} stars:>={MIN_STARS} "
            f"fork:false archived:false language:{language}",
        )
        for first, last in months(today)
        for language in LANGUAGES
    ]


def candidates(github: Fetch, today: date, pause: float = SEARCH_PAUSE, log=print):
    """Unique repositories from the searches: {full_name: {created, stars, ecosystem}}."""
    from core.github_reader import _valid_repo_parts

    found: dict[str, dict[str, Any]] = {}
    for language, query in search_queries(today):
        for page in range(1, PER_QUERY // 100 + 1):
            status, doc = github(SEARCH.format(q=quote(query), page=page))
            if pause:
                time.sleep(pause)
            items = doc.get("items") if status == 200 and isinstance(doc, dict) else None
            if not isinstance(items, list):
                log(f"search {language} {query[8:29]} page {page}: {status}")
                break
            for item in items:
                name = str(item.get("full_name") or "")
                owner, _, repo = name.partition("/")
                count = item.get("stargazers_count")
                if not _valid_repo_parts(owner, repo) or type(count) is not int:
                    continue
                found.setdefault(
                    name,
                    {
                        "created": stars_time(item.get("created_at")),
                        "stars": count,
                        "ecosystem": LANGUAGES[language],
                    },
                )
            if len(items) < 100:
                break
    return dict(sorted(found.items(), key=lambda kv: kv[0].lower()))


def stars_time(value: Any) -> str | None:
    text = str(value or "")
    try:
        datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None
    return text


def linked_package(repo: str, ecosystem: str, registry: Fetch) -> str | None:
    """The package named like the repository when it claims exactly that
    repository (case ignored), else None."""
    from core.repository_linkage import _claimed

    name = repo.partition("/")[2].lower()
    if ecosystem == "PyPI":
        status, doc = registry(f"https://pypi.org/pypi/{quote(name)}/json")
    else:
        status, doc = registry(f"https://registry.npmjs.org/{quote(name)}")
    if status != 200 or not isinstance(doc, dict):
        return None
    claims = _claimed(ecosystem, doc)
    return name if claims and claims[0][0].lower() == repo.lower() else None


def has_malicious_record(ecosystem: str, package: str, osv: Query) -> bool | None:
    """True when OSV lists a MAL- record for the package; None without an answer."""
    status, doc = osv({"package": {"name": package, "ecosystem": ecosystem}})
    if status != 200 or not isinstance(doc, dict):
        return None
    return any(str(v.get("id", "")).startswith("MAL-") for v in doc.get("vulns") or [])


def flagged_by_starscout(directory: Path | None) -> set[str]:
    if directory is None:
        return set()
    return {r["repository"].lower() for r in stars.positive_repositories(directory, sample=0)}


def select(
    found: dict[str, dict[str, Any]],
    registry: Fetch,
    osv: Query,
    flagged: set[str],
    log=print,
) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    """The repositories that pass steps 2-4, with how many each step dropped."""
    kept: dict[str, dict[str, Any]] = {}
    dropped = {"starscout": 0, "not_linked": 0, "malicious_record": 0, "osv_unanswered": 0}
    for index, (repo, info) in enumerate(found.items(), 1):
        if repo.lower() in flagged:
            dropped["starscout"] += 1
            continue
        package = linked_package(repo, info["ecosystem"], registry)
        if package is None:
            dropped["not_linked"] += 1
            continue
        malicious = has_malicious_record(info["ecosystem"], package, osv)
        if malicious is None:
            dropped["osv_unanswered"] += 1
            continue
        if malicious:
            dropped["malicious_record"] += 1
            continue
        kept[repo] = {**info, "package": package}
        if index % 50 == 0:
            log(f"linkage {index}/{len(found)}: {len(kept)} kept")
    return kept, dropped


def sample(kept: dict[str, dict[str, Any]], size: int = SAMPLE, seed: int = SEED):
    names = sorted(kept, key=str.lower)
    if size and len(names) > size:
        names = sorted(random.Random(seed).sample(names, size), key=str.lower)  # noqa: S311 - seeded, reproducible sampling; not a secret
    return {n: kept[n] for n in names}


def record(
    github: Fetch,
    registry: Fetch,
    osv: Query,
    today: date,
    flagged: set[str],
    *,
    size: int = SAMPLE,
    pause: float = SEARCH_PAUSE,
    log=print,
) -> dict[str, Any]:
    found = candidates(github, today, pause=pause, log=log)
    kept, dropped = select(found, registry, osv, flagged, log=log)
    chosen = sample(kept, size)
    doc = stars.record(
        github,
        {repo: info["created"] for repo, info in chosen.items()},
        label="young",
        source="GitHub repository search, linked both ways to a PyPI or npm package",
        log=log,
    )
    for repo, info in chosen.items():
        doc["repositories"][repo]["selection"] = info
    doc["selection"] = {
        "queries": [q for _, q in search_queries(today)],
        "per_query": PER_QUERY,
        "candidates": len(found),
        "dropped": dropped,
        "kept": len(kept),
        "sampled": len(chosen),
        "seed": SEED,
        "starscout_excluded": bool(flagged),
    }
    return doc


def main(argv: list[str] | None = None) -> int:
    from benchmarks import record_reputation
    from core import malicious

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--exclude", type=Path, help="StarScout data directory to exclude")
    parser.add_argument("--sample", type=int, default=SAMPLE)
    args = parser.parse_args(argv)
    started = time.perf_counter()
    doc = record(
        stars.http_fetch,
        record_reputation.http_fetch,
        malicious.http_query,
        datetime.now(timezone.utc).date(),
        flagged_by_starscout(args.exclude),
        size=args.sample,
    )
    out = stars.FIXTURES / f"stars-young-{doc['recorded_at'][:10]}.json"
    stars._write(doc, out)
    print(json.dumps(doc["selection"]["dropped"]), f"kept {doc['selection']['kept']}")
    print(f"done in {time.perf_counter() - started:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())

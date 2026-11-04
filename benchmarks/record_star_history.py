"""Record weekly star histories for the reputation sets (track T Phase 2, T-C2).

Run from the repository root, with network access (once per refresh):

    GITHUB_TOKEN=... python benchmarks/record_star_history.py
    GITHUB_TOKEN=... python benchmarks/record_star_history.py \\
        --positives path/to/StarScout/data/250101 --sample 1000

GitHub restricted the stargazer listings to admins and collaborators in 2026,
so no third party can read who starred a repository, or when. Its
star-history endpoint (``GET /repos/{owner}/{repo}/stargazers/history``,
API version 2026-03-10, added 2026-09-04) gives counts instead: one bucket
per week, newest first, with a per-day breakdown, and no stargazer. That is
everything recorded here, so the star-history indicators are measured
offline before they ship (``docs/research/TRACK_T_STUDY_PROTOCOL.md``).

Two sets:

- **Organic** (committed): every repository of the latest organic reputation
  set (``benchmarks/fixtures/reputation/organic-*.json``), written to
  ``benchmarks/fixtures/reputation/stars-organic-<date>.json``.
- **Positives** (``--positives``, local only): repositories that StarScout
  (He et al., ICSE 2026; https://github.com/hehao98/StarScout) flagged for
  fake-star campaigns, read from its ``fake_stars_*_repos.csv`` files and
  sampled with a fixed seed. StarScout's authors ask that the data not be
  used to name individual repositories, and its labels are heuristic, so
  this file goes to ``benchmarks/fixtures/reputation/local/`` (git-ignored)
  and only aggregate measurements are published.

A repository is fetched page by page (30 weeks per page, at most 100 pages)
until a short page or its creation week. Each week is validated (an integer
week, seven non-negative daily counts summing to the total) and anything
else makes the repository's series ``invalid``. Only weeks with stars are
stored, as ``[week, d0, ..., d6]``; the zero weeks between are implied. The
token (environment only, never stored) raises GitHub's rate limit.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FIXTURES = ROOT / "benchmarks" / "fixtures" / "reputation"
LOCAL = FIXTURES / "local"
API = "https://api.github.com/repos/{repo}/stargazers/history?per_page={per_page}&page={page}"
API_VERSION = "2026-03-10"
PER_PAGE = 30
MAX_PAGES = 100
SAMPLE = 1000
SEED = 20261103
MAX_BYTES = 1024 * 1024
RETRIES = 3
MAX_WAIT = 3700.0  # one rate-limit window
POSITIVE_FILES = {
    "fake_stars_clustered_repos.csv": "clustered",
    "fake_stars_low_activity_repos.csv": "low_activity",
}

#: url -> (http status, decoded JSON or None)
Fetch = Callable[[str], tuple[int, Any]]


def http_fetch(url: str) -> tuple[int, Any]:
    from collectors import http
    from core.registry_existence import user_agent

    headers = {
        "user-agent": user_agent(),
        "accept": "application/vnd.github+json",
        "x-github-api-version": API_VERSION,
    }
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        headers["authorization"] = f"Bearer {token}"
    for _attempt in range(RETRIES + 1):
        try:
            # A moved repository answers with a redirect within api.github.com;
            # follow it, as record_reputation does, so its history is read where it is.
            response = http.get(
                url, max_bytes=MAX_BYTES, timeout=60, headers=headers, follow_redirects=True
            )
        except Exception:  # network trouble or an oversized body: no answer
            return 0, None
        wait = rate_limit_wait(response.status_code, response.headers, time.time())
        if wait is None:
            break
        time.sleep(wait)  # a rate limit is not an answer about the repository
    else:
        return 0, None
    if response.status_code != 200:
        return response.status_code, None
    try:
        return 200, response.json()
    except ValueError:
        return 0, None


def rate_limit_wait(status: int, headers: Any, now: float) -> float | None:
    """Seconds to wait before retrying a rate-limited answer, or None when the
    answer is about the repository (a 403 for a blocked one stays a 403)."""
    if status not in (403, 429):
        return None
    retry_after = str(headers.get("retry-after") or "")
    if retry_after.isdigit():
        return min(float(retry_after), MAX_WAIT)
    if str(headers.get("x-ratelimit-remaining") or "") == "0":
        reset = str(headers.get("x-ratelimit-reset") or "")
        if reset.isdigit():
            return min(max(float(reset) - now, 0.0) + 5.0, MAX_WAIT)
        return MAX_WAIT
    return None


def _week(bucket: Any) -> list[int] | None:
    """``[week, d0..d6]`` for a valid bucket, else None."""
    if not isinstance(bucket, dict):
        return None
    week, total, days = bucket.get("week"), bucket.get("total"), bucket.get("days")
    if type(week) is not int or week < 0 or type(total) is not int:
        return None
    if not isinstance(days, list) or len(days) != 7:
        return None
    if any(type(d) is not int or d < 0 for d in days) or sum(days) != total:
        return None
    return [week, *days]


def _created_week(created: str | None) -> int | None:
    if not created:
        return None
    try:
        when = datetime.strptime(created[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return int(when.timestamp()) - 7 * 86400  # one week of slack for bucket alignment


def record_repository(repo: str, fetch: Fetch, created: str | None = None) -> dict[str, Any]:
    """One repository's weekly star history, newest page first."""
    from core.github_reader import _valid_repo_parts

    owner, _, name = repo.partition("/")
    if not _valid_repo_parts(owner, name):
        return {"status": "invalid_name"}
    stop = _created_week(created)
    weeks: list[list[int]] = []
    pages = 0
    for page in range(1, MAX_PAGES + 1):
        status, doc = fetch(API.format(repo=repo, per_page=PER_PAGE, page=page))
        pages += 1
        if status != 200 or not isinstance(doc, list):
            if page == 1:
                return {"status": status or "unreachable", "pages": pages}
            return {"status": "incomplete", "http_status": status, "pages": pages}
        parsed = [_week(b) for b in doc]
        if any(p is None for p in parsed):
            return {"status": "invalid", "pages": pages}
        weeks += [p for p in parsed if p is not None]
        if len(doc) < PER_PAGE or (stop is not None and parsed and parsed[-1][0] <= stop):
            break
    else:
        return _series(weeks, pages, status="capped")
    return _series(weeks, pages, status=200)


def _series(weeks: list[list[int]], pages: int, status: Any) -> dict[str, Any]:
    ordered = sorted({w[0]: w for w in weeks}.values())
    return {
        "status": status,
        "pages": pages,
        "first_week": ordered[0][0] if ordered else None,
        "last_week": ordered[-1][0] if ordered else None,
        "weeks_seen": len(ordered),
        "stars": sum(sum(w[1:]) for w in ordered),
        "weeks": [w for w in ordered if any(w[1:])],
    }


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------


def organic_repositories() -> tuple[str, dict[str, str | None]]:
    """(source fixture, {answered repository: creation time}) of the organic set."""
    latest = sorted(FIXTURES.glob("organic-*.json"))[-1]
    doc = json.loads(latest.read_text(encoding="utf-8"))
    repos: dict[str, str | None] = {}
    for claimed, info in (doc.get("repositories") or {}).items():
        if info.get("status") != 200:
            continue
        repos[info.get("full_name") or claimed] = info.get("created")
    return latest.name, dict(sorted(repos.items(), key=lambda kv: kv[0].lower()))


def positive_repositories(directory: Path, sample: int, seed: int = SEED) -> list[dict[str, Any]]:
    """A fixed-seed sample of StarScout's flagged repositories, with its labels."""
    rows: dict[str, dict[str, Any]] = {}
    for filename, method in POSITIVE_FILES.items():
        path = directory / filename
        if not path.is_file():
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                repo = str(row.get("repo_name") or "")
                if "/" not in repo:
                    continue
                entry = rows.setdefault(repo, {"repository": repo, "methods": []})
                entry["methods"].append(method)
    ordered = sorted(rows.values(), key=lambda r: r["repository"].lower())
    if sample and len(ordered) > sample:
        ordered = sorted(random.Random(seed).sample(ordered, sample), key=lambda r: r["repository"])
    return ordered


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------


def record(
    fetch: Fetch,
    repositories: dict[str, str | None],
    *,
    label: str,
    source: str,
    log=print,
) -> dict[str, Any]:
    from core.version import openpulse_version

    histories = {}
    for index, (repo, created) in enumerate(repositories.items(), 1):
        histories[repo] = record_repository(repo, fetch, created)
        log(f"{label} {index}/{len(repositories)} {histories[repo]['status']}")
    return {
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "recorder": "benchmarks/record_star_history.py",
        "openpulse_version": openpulse_version(),
        "endpoint": "GET /repos/{owner}/{repo}/stargazers/history",
        "api_version": API_VERSION,
        "set": label,
        "source": source,
        "week_format": "[week (epoch seconds, GitHub's week start), stars per day x7]; "
        "weeks without stars are omitted",
        "repositories": histories,
    }


def _write(doc: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, separators=(",", ":"), sort_keys=True) + "\n", "utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--positives",
        type=Path,
        help="StarScout data directory with fake_stars_*_repos.csv (local output only)",
    )
    parser.add_argument("--sample", type=int, default=SAMPLE, help="positives to sample")
    parser.add_argument("--skip-organic", action="store_true", help="record positives only")
    args = parser.parse_args(argv)
    started = time.perf_counter()
    if not args.skip_organic:
        source, repos = organic_repositories()
        doc = record(http_fetch, repos, label="organic", source=source)
        _write(doc, FIXTURES / f"stars-organic-{doc['recorded_at'][:10]}.json")
    if args.positives:
        flagged = positive_repositories(args.positives, args.sample)
        doc = record(
            http_fetch,
            {r["repository"]: None for r in flagged},
            label="positives",
            source=f"StarScout {args.positives.name}, fixed-seed sample of {len(flagged)}",
        )
        methods = {r["repository"]: r["methods"] for r in flagged}
        for repo, history in doc["repositories"].items():
            history["starscout"] = methods[repo]
        _write(doc, LOCAL / f"stars-positives-{doc['recorded_at'][:10]}.json")
    print(f"done in {time.perf_counter() - started:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""The young organic set recorder (track T, T-C2; protocol item TR3), offline."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks import record_young_set as young  # noqa: E402

TODAY = date(2026, 11, 3)
WEEK = 7 * 86400


def _repo(name, stars=120, created="2026-05-10T00:00:00Z"):
    return {"full_name": name, "stargazers_count": stars, "created_at": created}


class GitHub:
    """Search answers by language, and a short star history for any repository."""

    def __init__(self, by_language):
        self.by_language, self.asked = by_language, []

    def __call__(self, url):
        self.asked.append(url)
        if "/search/repositories" in url:
            query = unquote(url.split("q=", 1)[1].split("&", 1)[0])
            language = query.rsplit("language:", 1)[1]
            month = query.split("created:", 1)[1][:7]
            items = [i for i in self.by_language.get(language, []) if i["created_at"][:7] == month]
            return 200, {"items": items}
        return 200, [{"week": 1_790_000_000, "total": 3, "days": [1, 1, 1, 0, 0, 0, 0]}]


class Registry:
    def __init__(self, docs):
        self.docs, self.asked = docs, []

    def __call__(self, url):
        self.asked.append(url)
        return (200, self.docs[url]) if url in self.docs else (404, None)


def _osv(malicious=(), down=()):
    def query(body):
        name = body["package"]["name"]
        if name in down:
            return 503, None
        return 200, {"vulns": [{"id": "MAL-2026-1"}]} if name in malicious else {}

    return query


def test_months_are_twelve_calendar_months_ending_thirty_days_ago():
    spans = young.months(TODAY)
    assert len(spans) == 12
    assert spans[0] == (date(2026, 10, 1), date(2026, 10, 4))
    assert spans[-1] == (date(2025, 11, 1), date(2025, 11, 30))
    assert all(first <= last for first, last in spans)


def test_queries_cover_each_month_and_language_with_the_star_floor():
    queries = young.search_queries(TODAY)
    assert len(queries) == 12 * 3
    assert all("stars:>=50 fork:false archived:false" in q for _, q in queries)
    assert {lang for lang, _ in queries} == {"Python", "JavaScript", "TypeScript"}


def test_only_repositories_their_package_claims_back_are_kept(monkeypatch):
    github = GitHub(
        {
            "Python": [_repo("acme/widget"), _repo("hype/cheat-tool"), _repo("acme/other")],
            "TypeScript": [_repo("acme/tsthing")],
        }
    )
    registry = Registry(
        {
            "https://pypi.org/pypi/widget/json": {
                "info": {"project_urls": {"Source": "https://github.com/acme/widget"}}
            },
            # Same name, but the package claims someone else's repository.
            "https://pypi.org/pypi/other/json": {
                "info": {"project_urls": {"Source": "https://github.com/elsewhere/other"}}
            },
            "https://registry.npmjs.org/tsthing": {
                "repository": {"url": "git+https://github.com/ACME/tsthing.git"}
            },
        }
    )
    doc = young.record(github, registry, _osv(), TODAY, set(), pause=0, log=lambda _m: None)
    assert sorted(doc["repositories"]) == ["acme/tsthing", "acme/widget"]
    assert doc["selection"]["dropped"]["not_linked"] == 2
    widget = doc["repositories"]["acme/widget"]
    assert widget["selection"]["package"] == "widget" and widget["status"] == 200
    assert doc["set"] == "young"


def test_malicious_records_starscout_flags_and_osv_outages_are_dropped():
    found = {
        "acme/bad": {"created": None, "stars": 60, "ecosystem": "npm"},
        "acme/flagged": {"created": None, "stars": 60, "ecosystem": "npm"},
        "acme/unknown": {"created": None, "stars": 60, "ecosystem": "npm"},
        "acme/good": {"created": None, "stars": 60, "ecosystem": "npm"},
    }
    registry = Registry(
        {
            f"https://registry.npmjs.org/{n}": {"repository": f"github:acme/{n}"}
            for n in ("bad", "flagged", "unknown", "good")
        }
    )
    kept, dropped = young.select(
        found, registry, _osv(malicious={"bad"}, down={"unknown"}), {"acme/flagged"}, log=print
    )
    assert list(kept) == ["acme/good"]
    assert dropped == {
        "starscout": 1,
        "not_linked": 0,
        "malicious_record": 1,
        "osv_unanswered": 1,
    }


def test_the_sample_is_fixed_by_its_seed():
    kept = {f"o/r{i}": {"created": None} for i in range(40)}
    assert young.sample(kept, 10) == young.sample(kept, 10)
    assert len(young.sample(kept, 10)) == 10 and len(young.sample(kept, 100)) == 40


def test_search_failures_end_that_query_without_inventing_results():
    def broken(url):
        return 403, None

    assert young.candidates(broken, TODAY, pause=0, log=lambda _m: None) == {}

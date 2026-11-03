"""The star-history recorder (track T Phase 2, T-C2): offline, against a stub GitHub."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks import record_star_history as rec  # noqa: E402

WEEK = 7 * 86400
NOW = 1_793_491_200  # a Sunday in late 2026


class GitHub:
    """Pages of weekly buckets, newest first; url -> (status, json)."""

    def __init__(self, series=None, status=200, fail_on_page=None):
        self.series = series or {}
        self.status, self.fail_on_page = status, fail_on_page
        self.asked: list[str] = []

    def __call__(self, url):
        self.asked.append(url)
        repo = url.split("/repos/")[1].split("/stargazers")[0]
        page = int(url.rsplit("page=", 1)[1])
        if self.status != 200 or page == self.fail_on_page:
            return (self.status if self.status != 200 else 503), None
        weeks = self.series.get(repo, [])
        chunk = weeks[(page - 1) * rec.PER_PAGE : page * rec.PER_PAGE]
        return 200, [{"week": w, "total": sum(days), "days": days} for w, days in chunk]


def _weeks(n, start=NOW, stars=lambda i: [0, 0, 0, 0, 0, 0, 0]):
    """n consecutive weeks, newest first."""
    return [(start - i * WEEK, stars(i)) for i in range(n)]


def test_a_history_is_read_page_by_page_until_a_short_page():
    gh = GitHub({"acme/widget": _weeks(70, stars=lambda i: [1, 0, 0, 0, 0, 0, i % 2])})
    out = rec.record_repository("acme/widget", gh)
    assert out["status"] == 200 and out["pages"] == 3
    assert out["weeks_seen"] == 70
    assert out["stars"] == 70 + 35
    assert out["weeks"] == sorted(out["weeks"])  # oldest first
    assert out["weeks"][0][0] == NOW - 69 * WEEK and out["last_week"] == NOW
    assert all(len(w) == 8 for w in out["weeks"])


def test_zero_weeks_are_implied_not_stored():
    series = _weeks(10, stars=lambda i: [5, 0, 0, 0, 0, 0, 0] if i == 3 else [0] * 7)
    out = rec.record_repository("acme/widget", GitHub({"acme/widget": series}))
    assert out["weeks_seen"] == 10 and out["weeks"] == [[NOW - 3 * WEEK, 5, 0, 0, 0, 0, 0, 0]]


def test_reading_stops_at_the_creation_week():
    created_ts = NOW - 40 * WEEK
    from datetime import datetime, timezone

    created = datetime.fromtimestamp(created_ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    gh = GitHub({"acme/widget": _weeks(200, stars=lambda i: [1, 0, 0, 0, 0, 0, 0])})
    out = rec.record_repository("acme/widget", gh, created)
    assert out["pages"] == 2  # weeks 0-29, then 30-59 reach the creation week


def test_the_page_cap_is_recorded():
    n = rec.PER_PAGE * rec.MAX_PAGES + 5
    gh = GitHub({"acme/widget": _weeks(n, start=NOW + n * WEEK)})  # all weeks after 1970
    out = rec.record_repository("acme/widget", gh)
    assert out["status"] == "capped" and out["pages"] == rec.MAX_PAGES


def test_unknown_unreachable_and_broken_series_are_named():
    assert rec.record_repository("acme/gone", GitHub(status=404))["status"] == 404
    assert rec.record_repository("acme/x", GitHub(status=0))["status"] == "unreachable"
    gh = GitHub({"acme/widget": _weeks(70)}, fail_on_page=2)
    assert rec.record_repository("acme/widget", gh)["status"] == "incomplete"
    assert rec.record_repository("../etc", GitHub())["status"] == "invalid_name"


def test_a_bucket_that_does_not_add_up_invalidates_the_series():
    class Liar(GitHub):
        def __call__(self, url):
            return 200, [{"week": NOW, "total": 9, "days": [1, 1, 1, 1, 1, 1, 1]}]

    assert rec.record_repository("acme/widget", Liar())["status"] == "invalid"
    for bad in (
        {"week": "1", "total": 0, "days": [0] * 7},
        {"week": NOW, "total": 0, "days": [0] * 6},
        {"week": NOW, "total": -1, "days": [-1, 0, 0, 0, 0, 0, 0]},
        {"week": NOW, "total": 1, "days": [True, 0, 0, 0, 0, 0, 0]},
        {"week": NOW, "total": 0, "days": [0] * 7, "user": "x"},
    ):
        expected_valid = "user" in bad  # extra fields are ignored, never stored
        assert (rec._week(bad) is not None) is expected_valid, bad


def test_positives_are_a_fixed_seed_sample_with_their_methods(tmp_path):
    (tmp_path / "fake_stars_clustered_repos.csv").write_text(
        "repo_id,repo_name,n_stars\n"
        + "".join(f",owner{i}/repo{i},10\n" for i in range(50))
        + ",not-a-repo,1\n",
        encoding="utf-8",
    )
    (tmp_path / "fake_stars_low_activity_repos.csv").write_text(
        "repo_id,repo_name,n_stars\n,owner1/repo1,3\n,solo/one,4\n", encoding="utf-8"
    )
    everything = rec.positive_repositories(tmp_path, sample=0)
    assert len(everything) == 51
    both = next(r for r in everything if r["repository"] == "owner1/repo1")
    assert both["methods"] == ["clustered", "low_activity"]
    first = rec.positive_repositories(tmp_path, sample=10)
    assert first == rec.positive_repositories(tmp_path, sample=10)
    assert len(first) == 10


def test_the_organic_set_reads_the_answered_repositories():
    source, repos = rec.organic_repositories()
    assert source.startswith("organic-") and len(repos) > 50
    assert "babel/babel-standalone" in repos  # moved repositories are read where they answer
    assert all("/" in r for r in repos)


def test_a_record_names_its_source_and_endpoint():
    gh = GitHub({"acme/widget": _weeks(3, stars=lambda i: [1] * 7)})
    doc = rec.record(
        gh, {"acme/widget": None}, label="organic", source="x.json", log=lambda _m: None
    )
    assert doc["api_version"] == "2026-03-10" and doc["set"] == "organic"
    assert doc["repositories"]["acme/widget"]["stars"] == 21


def test_local_positives_are_never_committed():
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", str(rec.LOCAL / "stars-positives-2026-11-03.json")],
        cwd=ROOT,
        check=False,
    )
    assert ignored.returncode == 0


def test_the_default_fetch_is_offline_in_tests():
    """conftest blocks network; the recorder is only called with a stub here."""
    assert callable(rec.http_fetch)

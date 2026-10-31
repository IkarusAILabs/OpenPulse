"""The CLI's verdict commands admit negatives as the agent tools do (TR-2026-01 N4).

`check`, `attest`, `digest` and `warnings` run in the *current* mode by
default: a negative needs evidence fetched within 90 days of the start
of today (UTC), so a stale event can associate a dependency but never
clear it. `--replay` drops the bound for recorded evidence and says so.
Contradicted events never clear in either mode.
"""

import json

import pytest
from click.testing import CliRunner

from cli.main import cli

DJANGO_EOL = "data/fixtures/django-eol/event.json"  # complete scope, fetched 2026-09-25


@pytest.fixture
def watchlist(tmp_path):
    path = tmp_path / "watchlist.yaml"
    path.write_text(
        "version: 1\ndependencies:\n"
        '  - package: django\n    ecosystem: PyPI\n    version: "5.1.2"\n',
        encoding="utf-8",
    )
    return str(path)


def _attest(watchlist, *flags, event=DJANGO_EOL):
    out = CliRunner().invoke(cli, ["attest", "--watchlist", watchlist, "--event", event, *flags])
    assert out.exit_code == 0, out.output
    (doc,) = [json.loads(line) for line in out.stdout.splitlines() if line.startswith("{")]
    return doc, out.stderr


def test_a_fresh_complete_scope_clears(watchlist):
    doc, notice = _attest(watchlist, "--as-of", "2026-10-01")
    assert doc["assessment"]["relationship"] == "NOT_AFFECTED"
    assert doc["evaluation_context"] == {
        "as_of": "2026-10-01T00:00:00Z",
        "freshness_bound_applied": True,
        "max_evidence_age_days": 90,
        "unresolved_identity": "undetermined",
    }
    assert "90-day freshness bound as of 2026-10-01" in notice


def test_a_stale_event_cannot_clear_by_default(watchlist):
    doc, _ = _attest(watchlist, "--as-of", "2027-06-01")
    assert doc["assessment"]["relationship"] == "RELATED"
    assert "older than the 90-day freshness bound (stale)" in doc["assessment"]["reason"]


def test_the_bound_is_configurable(watchlist):
    doc, _ = _attest(watchlist, "--as-of", "2026-10-01", "--max-evidence-age-days", "3")
    assert doc["assessment"]["relationship"] == "RELATED"
    assert doc["evaluation_context"]["max_evidence_age_days"] == 3


def test_replay_drops_the_bound_and_says_so(watchlist):
    doc, notice = _attest(watchlist, "--replay")
    assert doc["assessment"]["relationship"] == "NOT_AFFECTED"
    assert doc["evaluation_context"]["freshness_bound_applied"] is False
    assert "replay, no freshness bound" in notice


def test_replay_refuses_a_bound(watchlist):
    out = CliRunner().invoke(
        cli,
        ["attest", "--watchlist", watchlist, "--event", DJANGO_EOL, "--replay", "--as-of", "2026"],
    )
    assert out.exit_code != 0
    assert "--replay applies no freshness bound" in out.output


def test_a_contradicted_event_never_clears_even_in_replay(watchlist, tmp_path):
    data = json.loads(open(DJANGO_EOL, encoding="utf-8").read())
    data["evidences"][1]["relation"] = "contradicts"
    contested = tmp_path / "contested.json"
    contested.write_text(json.dumps(data), encoding="utf-8")
    for flags in (("--as-of", "2026-10-01"), ("--replay",)):
        doc, _ = _attest(watchlist, *flags, event=str(contested))
        assert doc["assessment"]["relationship"] == "RELATED", flags
        assert "contested by contradicting evidence" in doc["assessment"]["reason"]


def test_check_applies_the_same_bound(watchlist):
    out = CliRunner().invoke(
        cli, ["check", "--watchlist", watchlist, "--event", DJANGO_EOL, "--as-of", "2027-06-01"]
    )
    assert out.exit_code == 0, out.output
    assert "RELATED" in out.stdout and "NOT_AFFECTED" not in out.stdout

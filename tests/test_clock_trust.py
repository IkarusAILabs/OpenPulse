"""Clock trust (finding L7, NEXT_PHASES B6).

A detection ledger stamp must lie near UTC wall-clock time, and an entry's
first sighting is fixed when it is created. Without these, a caller could
backdate ``first_seen`` and inflate a published lead time. These tests do
not use the ``ledger_clock_at_stamp`` seeding fixture.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest

from core.detections import ledger
from core.observations import store

WALL = "2026-11-01T12:00:00+00:00"


@pytest.fixture
def root(tmp_path):
    return tmp_path / "ledger"


@pytest.fixture
def wall_clock(monkeypatch):
    monkeypatch.setattr(ledger, "now_iso", lambda: WALL)


def _at(offset: timedelta) -> str:
    return (datetime.fromisoformat(WALL) + offset).isoformat()


@pytest.mark.usefixtures("wall_clock")
@pytest.mark.parametrize(
    "stamp",
    [
        _at(-timedelta(days=90)),
        _at(-ledger.MAX_CLOCK_SKEW - timedelta(seconds=1)),
        _at(ledger.MAX_CLOCK_SKEW + timedelta(seconds=1)),
        _at(timedelta(days=30)),
    ],
    ids=["backdated-90d", "just-past-bound", "just-future-bound", "future-30d"],
)
def test_stamp_far_from_wall_clock_is_refused(root, stamp):
    with pytest.raises(ledger.ClockSkewError):
        ledger.record_detection("django", "lifecycle", "EOL", ["4.2"], detected_at=stamp, root=root)
    assert ledger.first_seen("django", "lifecycle", "EOL", ["4.2"], root=root) is None
    assert not list(root.rglob("*.json"))


@pytest.mark.usefixtures("wall_clock")
@pytest.mark.parametrize("stamp", ["", "yesterday", "2026-13-45T00:00:00"])
def test_unparseable_stamp_is_refused(root, stamp):
    """Before L7 a garbage stamp was stored as first_seen."""
    with pytest.raises(ledger.ClockSkewError):
        ledger.record_detection(
            "django", "lifecycle", "EOL", ["4.2"], detected_at=stamp or " ", root=root
        )


@pytest.mark.usefixtures("wall_clock")
def test_stamp_within_bound_is_recorded(root):
    stamp = _at(-ledger.MAX_CLOCK_SKEW)
    entry = ledger.record_detection(
        "django", "lifecycle", "EOL", ["4.2"], detected_at=stamp, root=root
    )
    assert entry["recorded_now"] is True
    assert entry["first_seen"] == stamp


def test_earlier_stamp_cannot_move_existing_first_seen(root, monkeypatch):
    """A re-detection stamped before the entry existed is not taken."""
    monkeypatch.setattr(ledger, "now_iso", lambda: WALL)
    ledger.record_detection("redis", "security", "CVE-1", [], root=root)
    earlier = _at(-timedelta(minutes=4))
    entry = ledger.record_detection(
        "redis", "security", "CVE-1", [], detected_at=earlier, root=root
    )
    assert entry["first_seen"] == WALL
    assert ledger.first_seen("redis", "security", "CVE-1", [], root=root) == WALL


def test_backdated_entry_rewrite_is_still_caught_by_the_hash(root, monkeypatch):
    """Clock trust adds to the content hash; it does not replace it."""
    monkeypatch.setattr(ledger, "now_iso", lambda: WALL)
    ledger.record_detection("django", "lifecycle", "EOL", ["4.2"], root=root)
    path = next(root.rglob("*.json"))
    entry = json.loads(path.read_text(encoding="utf-8"))
    entry["first_seen"] = "2026-01-01T00:00:00+00:00"
    path.write_text(json.dumps(entry), encoding="utf-8")
    assert ledger.first_seen("django", "lifecycle", "EOL", ["4.2"], root=root) is None


def test_check_cli_records_with_the_wall_clock(tmp_path):
    """Where users hit it: `openpulse check --ledger` stamps now, in UTC."""
    from click.testing import CliRunner

    from cli.main import cli as _cli

    watchlist = tmp_path / "watchlist.yaml"
    watchlist.write_text(
        'dependencies:\n  - package: django\n    ecosystem: PyPI\n    version: "4.2"\n',
        encoding="utf-8",
    )
    ledger_root = tmp_path / "ledger"
    before = datetime.now(timezone.utc)
    result = CliRunner().invoke(
        _cli,
        [
            "check",
            "--watchlist",
            str(watchlist),
            "--event",
            "data/fixtures/django-eol/event.json",
            "--ledger",
            str(ledger_root),
            "--replay",
        ],
    )
    after = datetime.now(timezone.utc)
    assert result.exit_code in (0, 1), result.output
    entries = [json.loads(p.read_text(encoding="utf-8")) for p in ledger_root.rglob("*.json")]
    assert entries, result.output
    for entry in entries:
        seen = datetime.fromisoformat(entry["first_seen"])
        assert seen.tzinfo is not None
        assert before <= seen <= after


def test_observation_without_timestamp_is_stamped_in_utc(tmp_path):
    """The store's fallback stamp was naive local time."""
    obs = {"registry": "docker.io", "namespace": "library", "repository": "redis"}
    before = datetime.now(timezone.utc).replace(microsecond=0)
    path = store.save_observation(obs, root=tmp_path)
    stamp = path.name.split("-", 1)[0]
    moment = datetime.strptime(stamp[:15], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
    assert stamp[15:].rstrip("0123456789.").endswith("Z")
    assert before - timedelta(seconds=1) <= moment <= datetime.now(timezone.utc)

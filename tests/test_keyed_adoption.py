"""Keyed adoption and keyed lead times (v0.9.0 item B3c, finding H2).

Design (docs/KEYED_INTEGRITY.md, decision 3): history written before the
key is adopted, never re-MACed as if it had always been keyed, and a lead
time counts from the adoption at the earliest. Exit criterion: reports cite
lead times from keyed-valid detections only.
"""

import json
from datetime import date, datetime, timedelta, timezone

from click.testing import CliRunner

from core.detections import ledger
from core.digest import UNKEYED_LEAD_TIME_NOTE, build_digest, render_digest_md
from core.history_key import ENV_VAR, keyring
from core.observations.chain import chain_hash, order_history, verify_keyed_history
from core.observations.store import list_observations, load_all
from core.observations.sweep import observe_repository
from core.risk.check import check_dependency
from core.schema.models import OSSEvent
from core.warnings import build_warnings
from tests.history_keys import TEST_KEY, TEST_KEY_TEXT, TEST_KEYS

T0 = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Observation chains
# ---------------------------------------------------------------------------


def _probe(latest_digest):
    return {
        "collector": "registries",
        "registry": "docker.io",
        "namespace": "demo",
        "repo": "app",
        "tags_sample": ["latest", "1.0"],
        "digests": {"latest": [f"sha256:{latest_digest}"], "1.0": ["sha256:1.0"]},
        "count": 2,
        "has_versioned_tags": True,
        "latest_only": False,
    }


def _observe(root, minutes, digest, key=None):
    return observe_repository(
        "docker.io",
        "demo",
        "app",
        _probe(digest),
        store_root=root,
        observed_at=T0 + timedelta(minutes=minutes),
        history_key=key,
    )


def _ordered(root):
    ordered, ok = order_history(load_all("docker.io", "demo", "app", root=root))
    assert ok
    return ordered


def test_unkeyed_history_followed_by_keyed_records_is_adopted(tmp_path):
    _observe(tmp_path, 0, "a")
    _observe(tmp_path, 1, "b")
    result = _observe(tmp_path, 2, "c", key=TEST_KEY)
    assert result["history_integrity"] == "VALID_KEYED"
    verdict = verify_keyed_history(_ordered(tmp_path), TEST_KEYS)
    assert verdict["status"] == "VALID_KEYED"
    assert verdict["unkeyed"] == [0, 1]
    assert verdict["adopted_at"].startswith("2026-11-01T12:02")
    # The adopted records are not re-MACed.
    assert not any(r.get("history_mac") for r in _ordered(tmp_path)[:2])


def test_keyed_from_genesis_has_no_adoption(tmp_path):
    _observe(tmp_path, 0, "a", key=TEST_KEY)
    assert verify_keyed_history(_ordered(tmp_path), TEST_KEYS)["adopted_at"] is None


def test_unkeyed_record_after_keyed_ones_is_not_adoption(tmp_path):
    _observe(tmp_path, 0, "a", key=TEST_KEY)
    # Strip the MAC from the newest of two keyed records: unkeyed after keyed.
    _observe(tmp_path, 1, "b", key=TEST_KEY)
    path = list_observations("docker.io", "demo", "app", root=tmp_path)[-1]
    record = json.loads(path.read_text(encoding="utf-8"))
    record.update(history_mac=None, key_id=None)
    path.write_text(json.dumps(record), encoding="utf-8")
    verdict = verify_keyed_history(_ordered(tmp_path), TEST_KEYS)
    assert verdict["status"] == "VALID_UNKEYED"
    assert verdict["adopted_at"] is None


def test_adoption_pins_the_adopted_records(tmp_path):
    """Editing a pre-adoption record (hashes recomputed) breaks the keyed record after it."""
    _observe(tmp_path, 0, "a")
    _observe(tmp_path, 1, "b", key=TEST_KEY)
    path = list_observations("docker.io", "demo", "app", root=tmp_path)[0]
    record = json.loads(path.read_text(encoding="utf-8"))
    record["observed_at"] = "2025-01-01T00:00:00Z"
    record["chain_hash"] = chain_hash(record, record["previous_observation_hash"])
    path.write_text(json.dumps(record), encoding="utf-8")
    ordered, ok = order_history(load_all("docker.io", "demo", "app", root=tmp_path))
    assert not ok or verify_keyed_history(ordered, TEST_KEYS)["status"] == "BROKEN"


def test_unkeyed_run_publishes_no_first_detection(tmp_path):
    """latest moved at minute 1 and again at minute 2, all unkeyed: no date proved."""
    _observe(tmp_path, 0, "a")
    _observe(tmp_path, 1, "b")
    unkeyed = _observe(tmp_path, 2, "c")
    assert unkeyed["changes"][0]["first_detected_at"] is None


def test_change_first_detection_is_clamped_at_adoption(tmp_path):
    _observe(tmp_path, 0, "a")
    _observe(tmp_path, 1, "b")
    keyed = _observe(tmp_path, 2, "c", key=TEST_KEY)
    change = keyed["changes"][0]
    assert change["type"] == "latest_moved"
    # Detected first at minute 1, but nothing before adoption (minute 2) is proved.
    assert change["first_detected_at"].startswith("2026-11-01T12:02")


# ---------------------------------------------------------------------------
# Detection ledger
# ---------------------------------------------------------------------------


def _record(root, key, clock, monkeypatch):
    monkeypatch.setattr(ledger, "now_iso", lambda: clock)
    return ledger.record_detection(
        "django", "lifecycle", "EOL", ["4.2"], root=root, history_key=key
    )


def _keyed_first(root, keys=TEST_KEYS):
    return ledger.keyed_first_seen("django", "lifecycle", "EOL", ["4.2"], root=root, keys=keys)


def test_unkeyed_ledger_entry_is_adopted_and_counts_from_adoption(tmp_path, monkeypatch):
    _record(tmp_path, None, "2026-07-01T00:00:00+00:00", monkeypatch)
    assert _keyed_first(tmp_path) is None  # unkeyed: no lead time
    entry = _record(tmp_path, TEST_KEY, "2026-10-01T00:00:00+00:00", monkeypatch)
    assert entry["first_seen"] == "2026-07-01T00:00:00+00:00"  # kept as context
    assert entry["adopted_at"] == "2026-10-01T00:00:00+00:00"
    assert _keyed_first(tmp_path) == "2026-10-01T00:00:00+00:00"
    # Adoption time is kept by later keyed writes.
    entry = _record(tmp_path, TEST_KEY, "2026-10-05T00:00:00+00:00", monkeypatch)
    assert entry["adopted_at"] == "2026-10-01T00:00:00+00:00"
    assert _keyed_first(tmp_path) == "2026-10-01T00:00:00+00:00"


def test_entry_keyed_from_creation_counts_from_first_seen(tmp_path, monkeypatch):
    _record(tmp_path, TEST_KEY, "2026-07-01T00:00:00+00:00", monkeypatch)
    _record(tmp_path, TEST_KEY, "2026-10-01T00:00:00+00:00", monkeypatch)
    assert _keyed_first(tmp_path) == "2026-07-01T00:00:00+00:00"


def test_adoption_time_is_under_the_mac(tmp_path, monkeypatch):
    _record(tmp_path, None, "2026-07-01T00:00:00+00:00", monkeypatch)
    _record(tmp_path, TEST_KEY, "2026-10-01T00:00:00+00:00", monkeypatch)
    path = tmp_path / "django" / f"{ledger.fact_key('django', 'lifecycle', 'EOL', ['4.2'])}.json"
    entry = json.loads(path.read_text(encoding="utf-8"))
    entry["adopted_at"] = "2026-07-01T00:00:00+00:00"  # try to move adoption back
    path.write_text(json.dumps(entry), encoding="utf-8")
    assert ledger.entry_integrity(entry, TEST_KEYS) == "BROKEN"
    assert _keyed_first(tmp_path) is None


def test_keyed_first_seen_needs_keys(tmp_path, monkeypatch):
    _record(tmp_path, TEST_KEY, "2026-07-01T00:00:00+00:00", monkeypatch)
    assert _keyed_first(tmp_path, keys={}) is None
    assert _keyed_first(tmp_path, keys=None) is None


# ---------------------------------------------------------------------------
# Readers: digest, warnings
# ---------------------------------------------------------------------------


def _event():
    data = json.load(open("data/fixtures/django-eol/event.json", encoding="utf-8"))
    data["id"] = "evt-django-future-eol"
    for evidence in data["evidences"]:
        evidence["effective_date"] = "2026-12-31"
        evidence["announcement_date"] = "2026-09-30"
    data["affected_versions"] = ["4.2"]
    return OSSEvent(**data)


def _verdict(event):
    dep = {"kind": "package", "package": "django", "ecosystem": "PyPI", "version": "4.2"}
    return check_dependency(dep, [event])


def test_digest_without_keys_publishes_no_lead_time(tmp_path, monkeypatch):
    _record(tmp_path, TEST_KEY, "2026-07-01T00:00:00+00:00", monkeypatch)
    event = _event()
    digest = build_digest(
        [_verdict(event)], [event], ledger_root=str(tmp_path), today=date(2026, 10, 6)
    )
    assert digest["entries"], "the event must be in the window"
    assert all(
        e["first_detected"] is None and e["lead_time_days"] is None for e in digest["entries"]
    )
    assert digest["lead_time_note"] == UNKEYED_LEAD_TIME_NOTE
    assert UNKEYED_LEAD_TIME_NOTE in render_digest_md(digest)


def test_digest_with_keys_uses_keyed_first_detection(tmp_path, monkeypatch):
    _record(tmp_path, TEST_KEY, "2026-07-01T00:00:00+00:00", monkeypatch)
    event = _event()
    digest = build_digest(
        [_verdict(event)],
        [event],
        ledger_root=str(tmp_path),
        today=date(2026, 10, 6),
        history_keys=TEST_KEYS,
    )
    entry = digest["entries"][0]
    assert entry["first_detected"] == "2026-07-01"
    assert "lead_time_note" not in digest


def test_warnings_lead_time_counts_from_adoption(tmp_path, monkeypatch):
    _record(tmp_path, None, "2026-07-01T00:00:00+00:00", monkeypatch)
    _record(tmp_path, TEST_KEY, "2026-10-01T00:00:00+00:00", monkeypatch)
    event = _event()
    built = build_warnings(
        [_verdict(event)],
        [event],
        ledger_root=str(tmp_path),
        today=date(2026, 10, 6),
        history_keys=TEST_KEYS,
    )
    warning = built["warnings"][0]
    assert warning["first_detected"] == "2026-10-01"
    assert warning["lead_time_days"] == (date(2026, 12, 31) - date(2026, 10, 1)).days


def test_retired_key_entries_still_count_with_the_keyring(tmp_path, monkeypatch):
    """Lead times survive a rotation: retired keys verify (B3b)."""
    import base64

    from core.history_key import parse_key

    old = parse_key(base64.b64encode(b"r" * 32).decode())
    _record(tmp_path, old, "2026-07-01T00:00:00+00:00", monkeypatch)
    assert _keyed_first(tmp_path, keys=keyring(TEST_KEY, (old,))) == "2026-07-01T00:00:00+00:00"


# ---------------------------------------------------------------------------
# Where users hit it: the CLI
# ---------------------------------------------------------------------------


def _digest_cli(tmp_path, env):
    from cli.main import cli

    watchlist = tmp_path / "wl.yaml"
    watchlist.write_text(
        'version: 1\ndependencies:\n  - package: django\n    ecosystem: PyPI\n    version: "4.2"\n',
        encoding="utf-8",
    )
    args = [
        "digest",
        "--watchlist",
        str(watchlist),
        "--event",
        "data/fixtures/django-eol/event.json",
        "--ledger",
        str(tmp_path / "ledger"),
        "--replay",
        "--window-days",
        "100000",
    ]
    return CliRunner().invoke(cli, args, env=env)


def test_digest_cli_without_a_key_says_lead_times_are_unpublished(tmp_path):
    result = _digest_cli(tmp_path, {ENV_VAR: ""})
    assert result.exit_code == 0, result.output
    assert "Lead times are not published" in result.output


def test_digest_cli_with_a_key_drops_the_note(tmp_path):
    result = _digest_cli(tmp_path, {ENV_VAR: TEST_KEY_TEXT})
    assert result.exit_code == 0, result.output
    assert "Lead times are not published" not in result.output

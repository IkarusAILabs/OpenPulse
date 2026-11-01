"""History key rotation (v0.9.0 item B3b, finding H2).

Design (docs/KEYED_INTEGRITY.md, decision 2): one current key, verify-only
previous keys, and a handover MACed by both keys, so a leaked retired key
cannot extend history past its rotation.
"""

import base64
import json
from datetime import datetime, timedelta, timezone

import pytest
from click.testing import CliRunner

from core.detections import ledger
from core.history_key import (
    PREVIOUS_ENV_VAR,
    HistoryKeyError,
    keyring,
    load_previous_keys,
    parse_key,
)
from core.observations.chain import chain_hash, order_history, verify_keyed_history
from core.observations.registry import RegistryObservation
from core.observations.store import list_observations, load_all, save_observation, write_tip
from core.observations.sweep import observe_repository


def _key(byte: bytes):
    return parse_key(base64.b64encode(byte * 32).decode())


OLD, NEW, THIRD = _key(b"o"), _key(b"n"), _key(b"t")
T0 = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Previous keys
# ---------------------------------------------------------------------------


def test_previous_keys_from_environment(monkeypatch):
    texts = [base64.b64encode(b * 32).decode() for b in (b"o", b"t")]
    monkeypatch.setenv(PREVIOUS_ENV_VAR, f"{texts[0]}, {texts[1]}")
    assert {k.key_id for k in load_previous_keys()} == {OLD.key_id, THIRD.key_id}


def test_previous_keys_file_skips_comments_and_the_current_key(tmp_path):
    path = tmp_path / "previous.keys"
    path.write_text(
        "# retired 2026-11\n"
        + base64.b64encode(b"o" * 32).decode()
        + "\n\n"
        + base64.b64encode(b"n" * 32).decode()
        + "\n",
        encoding="utf-8",
    )
    keys = load_previous_keys(str(path), current=NEW)
    assert [k.key_id for k in keys] == [OLD.key_id]


def test_previous_keys_file_inside_openpulse_is_refused(tmp_path):
    path = tmp_path / ".openpulse" / "previous.keys"
    path.parent.mkdir()
    path.write_text(base64.b64encode(b"o" * 32).decode(), encoding="utf-8")
    with pytest.raises(HistoryKeyError, match=".openpulse"):
        load_previous_keys(str(path))


# ---------------------------------------------------------------------------
# Observation chains
# ---------------------------------------------------------------------------


def _probe(tags):
    return {
        "collector": "registries",
        "registry": "docker.io",
        "namespace": "demo",
        "repo": "app",
        "tags_sample": list(tags),
        "digests": {tag: [f"sha256:{tag}"] for tag in tags},
        "count": len(tags),
        "has_versioned_tags": True,
        "latest_only": False,
    }


def _observe(root, minutes, key, previous=()):
    tags = ["1.0"] + [f"1.{i}" for i in range(1, minutes + 1)]
    return observe_repository(
        "docker.io",
        "demo",
        "app",
        _probe(tags),
        store_root=root,
        observed_at=T0 + timedelta(minutes=minutes),
        history_key=key,
        previous_keys=tuple(previous),
    )


def _ordered(root):
    ordered, ok = order_history(load_all("docker.io", "demo", "app", root=root))
    assert ok
    return ordered


def _rotated_history(root):
    """Two records under OLD, then a handover to NEW and one more under NEW."""
    _observe(root, 0, OLD)
    _observe(root, 1, OLD)
    handover = _observe(root, 2, NEW, previous=[OLD])
    _observe(root, 3, NEW, previous=[OLD])
    return handover


def test_rotation_writes_a_handover_and_stays_valid_keyed(tmp_path):
    handover = _rotated_history(tmp_path)
    assert handover["error"] is None
    assert handover["history_integrity"] == "VALID_KEYED"
    ordered = _ordered(tmp_path)
    assert [r["key_id"] for r in ordered] == [OLD.key_id] * 2 + [NEW.key_id] * 2
    assert ordered[2]["previous_key_id"] == OLD.key_id and ordered[2]["handover_mac"]
    assert not ordered[3].get("previous_key_id")
    verdict = verify_keyed_history(ordered, keyring(NEW, (OLD,)))
    assert verdict["status"] == "VALID_KEYED"
    assert verdict["active_key_id"] == NEW.key_id


def test_without_the_retired_key_the_old_run_is_unknown(tmp_path):
    _rotated_history(tmp_path)
    assert verify_keyed_history(_ordered(tmp_path), keyring(NEW))["status"] == "UNKNOWN"


def test_appending_with_only_the_new_key_still_works_after_handover(tmp_path):
    _rotated_history(tmp_path)
    assert _observe(tmp_path, 4, NEW)["error"] is None


def _append_forged(root, minutes, key, **fields):
    """Append a well-formed record MACed with ``key``, as a holder of that key can."""
    previous = _ordered(root)[-1]
    tags = ["1.0"] + [f"1.{i}" for i in range(1, minutes + 1)]
    obs = RegistryObservation(
        registry="docker.io",
        namespace="demo",
        repository="app",
        tags={t: [f"sha256:{t}"] for t in tags},
        observed_at=T0 + timedelta(minutes=minutes),
    ).seal()
    obs = obs.link(previous).keyed(key)
    if fields:
        obs = obs.model_copy(update=fields)
    path = save_observation(obs.model_dump(mode="json"), root=root)
    write_tip(path.parent, obs.chain_hash)


def test_leaked_retired_key_cannot_extend_history_past_its_handover(tmp_path):
    _rotated_history(tmp_path)
    _append_forged(tmp_path, 4, OLD)  # attacker holds only the retired key
    verdict = verify_keyed_history(_ordered(tmp_path), keyring(NEW, (OLD,)))
    assert verdict["status"] == "BROKEN"
    assert verdict["bad_macs"] == [4]
    # And a later run refuses to diff or append.
    assert _observe(tmp_path, 5, NEW, previous=[OLD])["history_status"] == "BROKEN"


def test_key_switch_without_handover_is_broken(tmp_path):
    _observe(tmp_path, 0, OLD)
    _append_forged(tmp_path, 1, NEW)
    assert verify_keyed_history(_ordered(tmp_path), keyring(NEW, (OLD,)))["status"] == "BROKEN"


def test_forged_handover_mac_is_broken(tmp_path):
    _observe(tmp_path, 0, OLD)
    _append_forged(
        tmp_path, 1, NEW, previous_key_id=OLD.key_id, handover_mac="hmac-sha256:" + "0" * 64
    )
    assert verify_keyed_history(_ordered(tmp_path), keyring(NEW, (OLD,)))["status"] == "BROKEN"


def test_handover_from_a_key_that_was_not_active_is_broken(tmp_path):
    _observe(tmp_path, 0, OLD)
    retired = _ordered(tmp_path)[-1]
    obs = (
        RegistryObservation(
            registry="docker.io",
            namespace="demo",
            repository="app",
            tags={"1.0": ["sha256:1.0"], "1.1": ["sha256:1.1"]},
            observed_at=T0 + timedelta(minutes=1),
        )
        .seal()
        .link(retired)
        .keyed(NEW, retired=THIRD)
    )
    path = save_observation(obs.model_dump(mode="json"), root=tmp_path)
    write_tip(path.parent, obs.chain_hash)
    ring = keyring(NEW, (OLD, THIRD))
    assert verify_keyed_history(_ordered(tmp_path), ring)["status"] == "BROKEN"


def test_unknown_newest_key_is_a_mismatch(tmp_path):
    _observe(tmp_path, 0, OLD)
    result = _observe(tmp_path, 1, NEW)  # OLD not supplied as previous
    assert result["history_status"] == "KEY_MISMATCH"
    assert len(list_observations("docker.io", "demo", "app", root=tmp_path)) == 1


def test_handover_record_is_covered_by_the_chain(tmp_path):
    """Recomputing hashes after editing the handover breaks both MACs."""
    _rotated_history(tmp_path)
    path = list_observations("docker.io", "demo", "app", root=tmp_path)[2]
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["previous_key_id"] == OLD.key_id
    record["first_detected_at"] = "2025-01-01T00:00:00Z"
    record["chain_hash"] = chain_hash(record, record["previous_observation_hash"])
    path.write_text(json.dumps(record), encoding="utf-8")
    ordered, _ = order_history(load_all("docker.io", "demo", "app", root=tmp_path))
    assert verify_keyed_history(ordered, keyring(NEW, (OLD,)))["status"] == "BROKEN"


# ---------------------------------------------------------------------------
# Detection ledger
# ---------------------------------------------------------------------------


def _record(root, key, previous=(), clock=None, monkeypatch=None):
    if clock is not None:
        monkeypatch.setattr(ledger, "now_iso", lambda: clock)
    return ledger.record_detection(
        "django",
        "lifecycle",
        "EOL",
        ["4.2"],
        root=root,
        history_key=key,
        previous_keys=tuple(previous),
    )


def _entry(root):
    path = root / "django" / f"{ledger.fact_key('django', 'lifecycle', 'EOL', ['4.2'])}.json"
    return path, json.loads(path.read_text(encoding="utf-8"))


def test_ledger_entry_is_rekeyed_and_the_rotation_logged(tmp_path, monkeypatch):
    first = _record(tmp_path, OLD, clock="2026-11-01T10:00:00+00:00", monkeypatch=monkeypatch)
    entry = _record(
        tmp_path, NEW, [OLD], clock="2026-11-01T12:00:00+00:00", monkeypatch=monkeypatch
    )
    assert entry["key_id"] == NEW.key_id
    assert entry["first_seen"] == first["first_seen"]
    rotations = ledger.load_rotations(tmp_path, keyring(NEW, (OLD,)))
    assert rotations == {OLD.key_id: datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)}
    _, stored = _entry(tmp_path)
    assert ledger.entry_integrity(stored, keyring(NEW, (OLD,)), rotations) == "VALID_KEYED"
    # Logged once, however many entries rotate.
    _record(tmp_path, NEW, [OLD], clock="2026-11-01T12:01:00+00:00", monkeypatch=monkeypatch)
    log = json.loads((tmp_path / ledger.ROTATIONS_FILE).read_text(encoding="utf-8"))
    assert len(log["rotations"]) == 1


def test_retired_key_cannot_add_ledger_sightings_after_rotation(tmp_path, monkeypatch):
    _record(tmp_path, OLD, clock="2026-11-01T10:00:00+00:00", monkeypatch=monkeypatch)
    _record(tmp_path, NEW, [OLD], clock="2026-11-01T12:00:00+00:00", monkeypatch=monkeypatch)
    # The attacker holds OLD and writes the entry back under it, seen later.
    path, stored = _entry(tmp_path)
    forged = {k: v for k, v in stored.items() if k not in ("key_id", "history_mac")}
    forged["last_seen"] = "2026-11-01T13:00:00+00:00"
    forged["content_hash"] = ledger._entry_content_hash(
        "django", "lifecycle", "EOL", ["4.2"], forged["first_seen"], forged["last_seen"]
    )
    forged = ledger._keyed(forged, OLD)
    path.write_text(json.dumps(forged), encoding="utf-8")
    ring = keyring(NEW, (OLD,))
    assert ledger.entry_integrity(forged, ring, ledger.load_rotations(tmp_path, ring)) == "BROKEN"
    # Before the rotation, the same key was fine.
    assert ledger.entry_integrity(forged, ring) == "VALID_KEYED"


def test_entry_under_an_unknown_key_is_left_alone(tmp_path, monkeypatch):
    _record(tmp_path, OLD, clock="2026-11-01T10:00:00+00:00", monkeypatch=monkeypatch)
    path, _ = _entry(tmp_path)
    before = path.read_bytes()
    refused = _record(tmp_path, NEW, clock="2026-11-01T12:00:00+00:00", monkeypatch=monkeypatch)
    assert refused["key_refused"] is True
    assert path.read_bytes() == before
    assert not (tmp_path / ledger.ROTATIONS_FILE).exists()


def test_forged_rotation_log_entry_is_ignored(tmp_path):
    (tmp_path / ledger.ROTATIONS_FILE).write_text(
        json.dumps(
            {
                "rotations": [
                    {
                        "from": OLD.key_id,
                        "to": NEW.key_id,
                        "at": "2026-01-01T00:00:00+00:00",
                        "mac_from": "hmac-sha256:00",
                        "mac_to": "hmac-sha256:00",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert ledger.load_rotations(tmp_path, keyring(NEW, (OLD,))) == {}


# ---------------------------------------------------------------------------
# Where users hit it: the CLI
# ---------------------------------------------------------------------------


def _check(tmp_path, env):
    from cli.main import cli

    watchlist = tmp_path / "wl.yaml"
    watchlist.write_text(
        'version: 1\ndependencies:\n  - package: django\n    ecosystem: PyPI\n    version: "4.2"\n',
        encoding="utf-8",
    )
    args = [
        "check",
        "--watchlist",
        str(watchlist),
        "--event",
        "data/fixtures/django-eol/event.json",
        "--ledger",
        str(tmp_path / "ledger"),
        "--replay",
    ]
    return CliRunner().invoke(cli, args, env=env)


def test_check_cli_rotates_the_ledger(tmp_path):
    old_text = base64.b64encode(b"o" * 32).decode()
    new_text = base64.b64encode(b"n" * 32).decode()
    assert _check(tmp_path, {"OPENPULSE_HISTORY_KEY": old_text}).exit_code in (0, 1)
    rotated = _check(tmp_path, {"OPENPULSE_HISTORY_KEY": new_text, PREVIOUS_ENV_VAR: old_text})
    assert rotated.exit_code in (0, 1), rotated.output
    entries = [
        json.loads(p.read_text("utf-8"))
        for p in (tmp_path / "ledger").rglob("*.json")
        if p.name != ledger.ROTATIONS_FILE
    ]
    assert entries and {e["key_id"] for e in entries} == {NEW.key_id}
    assert (tmp_path / "ledger" / ledger.ROTATIONS_FILE).exists()
    assert old_text not in rotated.output and new_text not in rotated.output


def test_previous_keys_without_a_current_key_are_refused(tmp_path):
    result = _check(tmp_path, {PREVIOUS_ENV_VAR: base64.b64encode(b"o" * 32).decode()})
    assert result.exit_code != 0
    assert "need a current key" in result.output

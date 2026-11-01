"""Keyed history integrity (v0.9.0 item B3, finding H2).

Exit criterion: without the key, an edited record whose hashes were
recomputed is not VALID_KEYED. Design: docs/KEYED_INTEGRITY.md.
"""

import base64
import json
from datetime import datetime, timedelta, timezone

import pytest
from click.testing import CliRunner

from core.detections import ledger
from core.evidence.provenance import hash_content
from core.history_key import (
    ENV_VAR,
    HistoryKeyError,
    generate_key,
    load_history_key,
    parse_key,
)
from core.observations.chain import chain_hash, order_history, verify_keyed_history
from core.observations.registry import verify_registry_history
from core.observations.store import list_observations, load_all, write_tip
from core.observations.sweep import observe_repository

KEY = parse_key(base64.b64encode(b"k" * 32).decode())
OTHER = parse_key(base64.b64encode(b"o" * 32).decode())
T0 = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# The key
# ---------------------------------------------------------------------------


def test_generated_key_parses_and_ids_are_stable():
    text, key_id = generate_key()
    key = parse_key(text)
    assert key.key_id == key_id and key_id.startswith("hk1:")
    assert parse_key(text).key_id == key_id
    assert text not in repr(key)


def test_url_safe_and_unpadded_base64_are_accepted():
    raw = bytes(range(200, 232))
    standard = base64.b64encode(raw).decode()
    url_safe = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    assert parse_key(url_safe).key_id == parse_key(standard).key_id


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "not base64!",
        base64.b64encode(b"short").decode(),
        base64.b64encode(b"x" * 31).decode(),
    ],
)
def test_malformed_or_short_keys_are_refused(text):
    with pytest.raises(HistoryKeyError):
        parse_key(text)


def test_key_from_environment(monkeypatch):
    monkeypatch.setenv(ENV_VAR, base64.b64encode(b"k" * 32).decode())
    assert load_history_key().key_id == KEY.key_id
    monkeypatch.delenv(ENV_VAR)
    assert load_history_key() is None


def test_key_file_reads_first_non_empty_line_with_bom(tmp_path):
    path = tmp_path / "history.key"
    path.write_bytes(b"\xef\xbb\xbf\n\n" + base64.b64encode(b"k" * 32) + b"\nignored\n")
    assert load_history_key(str(path)).key_id == KEY.key_id


def test_key_file_inside_openpulse_or_a_store_is_refused(tmp_path):
    inside = tmp_path / ".openpulse" / "history.key"
    inside.parent.mkdir()
    inside.write_text(base64.b64encode(b"k" * 32).decode(), encoding="utf-8")
    with pytest.raises(HistoryKeyError, match=".openpulse"):
        load_history_key(str(inside))
    store = tmp_path / "store"
    (store / "sub").mkdir(parents=True)
    in_store = store / "sub" / "k"
    in_store.write_text(base64.b64encode(b"k" * 32).decode(), encoding="utf-8")
    with pytest.raises(HistoryKeyError, match="inside history store"):
        load_history_key(str(in_store), (str(store),))


def test_oversized_key_file_is_refused(tmp_path):
    path = tmp_path / "k"
    path.write_bytes(b"a" * 5000)
    with pytest.raises(HistoryKeyError, match="exceeds"):
        load_history_key(str(path))


# ---------------------------------------------------------------------------
# Observation history
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


def _observe(root, tags, minutes, key=KEY):
    return observe_repository(
        "docker.io",
        "demo",
        "app",
        _probe(tags),
        store_root=root,
        observed_at=T0 + timedelta(minutes=minutes),
        history_key=key,
    )


def _ordered(root):
    ordered, ok = order_history(load_all("docker.io", "demo", "app", root=root))
    assert ok
    return ordered


def _rewrite_tip(root, mutate):
    """Edit the newest record and recompute every hash, as an attacker without the key can.

    The tip pointer is rewritten too, so only the MAC can catch the edit.
    """
    path = list_observations("docker.io", "demo", "app", root=root)[-1]
    record = json.loads(path.read_text(encoding="utf-8"))
    mutate(record)
    body = {
        "registry": record["registry"],
        "namespace": record["namespace"],
        "repository": record["repository"],
        "tags": record.get("tags") or {},
        "missing": bool(record.get("missing")),
    }
    record["content_hash"] = hash_content(body)
    record["chain_hash"] = chain_hash(record, record["previous_observation_hash"])
    path.write_text(json.dumps(record), encoding="utf-8")
    write_tip(path.parent, record["chain_hash"])


def test_keyed_history_verifies_as_valid_keyed(tmp_path):
    assert _observe(tmp_path, ["1.0"], 0)["history_integrity"] == "VALID_KEYED"
    result = _observe(tmp_path, ["1.0", "1.1"], 1)
    assert result["error"] is None
    assert result["history_integrity"] == "VALID_KEYED"
    assert all(r["key_id"] == KEY.key_id for r in _ordered(tmp_path))


def test_edited_record_with_recomputed_hashes_is_not_valid_keyed(tmp_path):
    """The H2 attack: the unkeyed chain still verifies; the keyed check does not."""
    _observe(tmp_path, ["1.0"], 0)
    _observe(tmp_path, ["1.0", "1.1"], 1)
    _rewrite_tip(tmp_path, lambda r: r["tags"].pop("1.1"))
    ordered = _ordered(tmp_path)
    assert verify_registry_history(ordered)["status"] == "VALID"  # unkeyed: fooled
    assert verify_keyed_history(ordered, {KEY.key_id: KEY})["status"] == "BROKEN"
    refused = _observe(tmp_path, ["1.0", "1.1"], 2)
    assert refused["history_status"] == "BROKEN"
    assert refused["saved_path"] is None


def test_first_detected_at_is_covered_by_the_mac(tmp_path):
    """first_detected_at is outside the chain hash (H2); the MAC covers it."""
    _observe(tmp_path, ["1.0"], 0)
    _rewrite_tip(tmp_path, lambda r: r.update(first_detected_at="2025-01-01T00:00:00Z"))
    ordered = _ordered(tmp_path)
    assert verify_registry_history(ordered)["status"] == "VALID"
    assert verify_keyed_history(ordered, {KEY.key_id: KEY})["status"] == "BROKEN"


def test_stripped_macs_are_never_valid_keyed(tmp_path):
    _observe(tmp_path, ["1.0"], 0)
    _rewrite_tip(tmp_path, lambda r: (r.pop("history_mac"), r.pop("key_id")))
    assert verify_keyed_history(_ordered(tmp_path), {KEY.key_id: KEY})["status"] == "VALID_UNKEYED"


def test_without_the_key_keyed_history_is_unknown(tmp_path):
    _observe(tmp_path, ["1.0"], 0)
    assert verify_keyed_history(_ordered(tmp_path))["status"] == "UNKNOWN"


def test_keyed_history_is_not_appended_to_without_its_key(tmp_path):
    _observe(tmp_path, ["1.0"], 0)
    no_key = _observe(tmp_path, ["1.0", "1.1"], 1, key=None)
    assert no_key["history_status"] == "KEY_REQUIRED"
    assert "OPENPULSE_HISTORY_KEY" in no_key["error"]["safe_message"]
    wrong = _observe(tmp_path, ["1.0", "1.1"], 2, key=OTHER)
    assert wrong["history_status"] == "KEY_MISMATCH"
    assert len(list_observations("docker.io", "demo", "app", root=tmp_path)) == 1


def test_unkeyed_history_stays_usable_without_a_key(tmp_path):
    assert _observe(tmp_path, ["1.0"], 0, key=None)["history_integrity"] == "VALID_UNKEYED"
    assert _observe(tmp_path, ["1.0", "1.1"], 1, key=None)["error"] is None


def test_key_on_unkeyed_history_does_not_claim_the_past(tmp_path):
    """The older records are adopted (B3c), never re-MACed: adopted_at marks the cut."""
    _observe(tmp_path, ["1.0"], 0, key=None)
    result = _observe(tmp_path, ["1.0", "1.1"], 1)
    assert result["error"] is None
    assert result["history_integrity"] == "VALID_KEYED"
    ordered = _ordered(tmp_path)
    assert not ordered[0].get("history_mac")
    adopted = verify_keyed_history(ordered, {KEY.key_id: KEY})["adopted_at"]
    assert adopted == ordered[1]["observed_at"]


# ---------------------------------------------------------------------------
# Detection ledger
# ---------------------------------------------------------------------------


def _entry_path(root):
    return root / "django" / f"{ledger.fact_key('django', 'lifecycle', 'EOL', ['4.2'])}.json"


def _record(root, key=KEY):
    return ledger.record_detection(
        "django", "lifecycle", "EOL", ["4.2"], root=root, history_key=key
    )


def test_keyed_ledger_entry_verifies(tmp_path):
    entry = _record(tmp_path)
    assert entry["key_id"] == KEY.key_id
    stored = json.loads(_entry_path(tmp_path).read_text(encoding="utf-8"))
    assert ledger.entry_integrity(stored, {KEY.key_id: KEY}) == "VALID_KEYED"
    assert ledger.entry_integrity(stored) == "UNKNOWN"
    assert _record(tmp_path)["first_seen"] == entry["first_seen"]


def test_backdated_ledger_entry_with_recomputed_hash_is_broken(tmp_path):
    _record(tmp_path)
    path = _entry_path(tmp_path)
    stored = json.loads(path.read_text(encoding="utf-8"))
    stored["first_seen"] = "2026-01-01T00:00:00+00:00"
    stored["content_hash"] = ledger._entry_content_hash(
        "django", "lifecycle", "EOL", ["4.2"], stored["first_seen"], stored["last_seen"]
    )
    path.write_text(json.dumps(stored), encoding="utf-8")
    assert ledger.verify_entry(stored)  # unkeyed: fooled
    assert ledger.entry_integrity(stored, {KEY.key_id: KEY}) == "BROKEN"
    # A keyed writer treats the forged entry as unknown and starts afresh.
    assert _record(tmp_path)["first_seen"] != "2026-01-01T00:00:00+00:00"


def test_keyed_ledger_entry_is_not_rewritten_without_its_key(tmp_path):
    _record(tmp_path)
    before = _entry_path(tmp_path).read_bytes()
    assert _record(tmp_path, key=None)["key_refused"] is True
    assert _record(tmp_path, key=OTHER)["key_refused"] is True
    assert _entry_path(tmp_path).read_bytes() == before


def test_unkeyed_ledger_entry_is_adopted_not_backdated(tmp_path):
    """B3c: the entry is MACed now, with adopted_at; first_seen stays as context."""
    first = _record(tmp_path, key=None)
    entry = _record(tmp_path)
    assert entry["key_id"] == KEY.key_id
    assert entry["first_seen"] == first["first_seen"]
    assert entry["adopted_at"] >= first["first_seen"]
    stored = json.loads(_entry_path(tmp_path).read_text(encoding="utf-8"))
    assert ledger.entry_integrity(stored, {KEY.key_id: KEY}) == "VALID_KEYED"


# ---------------------------------------------------------------------------
# Where users hit it: the CLI
# ---------------------------------------------------------------------------


def _watchlist(tmp_path):
    path = tmp_path / "wl.yaml"
    path.write_text(
        'version: 1\ndependencies:\n  - package: django\n    ecosystem: PyPI\n    version: "4.2"\n',
        encoding="utf-8",
    )
    return path


def _check(tmp_path, *extra, env=None):
    from cli.main import cli

    args = [
        "check",
        "--watchlist",
        str(_watchlist(tmp_path)),
        "--event",
        "data/fixtures/django-eol/event.json",
        "--ledger",
        str(tmp_path / "ledger"),
        "--replay",
        *extra,
    ]
    return CliRunner().invoke(cli, args, env=env or {})


def test_check_cli_keys_the_ledger_from_the_environment(tmp_path):
    result = _check(tmp_path, env={ENV_VAR: base64.b64encode(b"k" * 32).decode()})
    assert result.exit_code in (0, 1), result.output
    entries = [json.loads(p.read_text("utf-8")) for p in (tmp_path / "ledger").rglob("*.json")]
    assert entries
    assert {ledger.entry_integrity(e, {KEY.key_id: KEY}) for e in entries} == {"VALID_KEYED"}
    assert base64.b64encode(b"k" * 32).decode() not in result.output


def test_check_cli_refuses_a_key_file_inside_openpulse(tmp_path):
    bad = tmp_path / ".openpulse" / "history.key"
    bad.parent.mkdir()
    bad.write_text(base64.b64encode(b"k" * 32).decode(), encoding="utf-8")
    result = _check(tmp_path, "--history-key-file", str(bad))
    assert result.exit_code != 0
    assert ".openpulse" in result.output


def test_history_key_generate_cli():
    from cli.main import cli

    result = CliRunner().invoke(cli, ["history-key", "generate"])
    assert result.exit_code == 0
    key_line = result.output.strip().splitlines()[0]
    assert parse_key(key_line).key_id in result.output

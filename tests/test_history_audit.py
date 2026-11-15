"""Auditing a restored history before it is used (v0.21.0 item W2).

Exit criterion: the Action keeps its history in the Actions cache, and a
restored history that is broken, rolled back, downgraded, unkeyed or keyed
by someone else is refused, with what and why, before anything uses it. A
genuine keyed history, and nothing at all, pass. The cache is saved only
from the default branch and never after a refusal.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from cli.main import cli
from core.detections import ledger
from core.history_audit import EMPTY, OK, REFUSED, audit_history
from core.history_key import keyring, parse_key
from core.observations.store import list_observations, repo_dir
from core.observations.sweep import observe_repository

ROOT = Path(__file__).resolve().parents[1]
KEY = parse_key(base64.b64encode(b"a" * 32).decode())
OTHER = parse_key(base64.b64encode(b"b" * 32).decode())
OLD = parse_key(base64.b64encode(b"z" * 32).decode())
T0 = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


def _probe(namespace, tags):
    return {
        "collector": "registries",
        "registry": "docker.io",
        "namespace": namespace,
        "repo": "app",
        "tags_sample": list(tags),
        "digests": {tag: [f"sha256:{tag}"] for tag in tags},
        "count": len(tags),
        "has_versioned_tags": True,
        "latest_only": False,
    }


def _observe(store, namespace, minutes, key=KEY):
    tags = ["1.0"] + [f"1.{i}" for i in range(1, minutes + 1)]
    result = observe_repository(
        "docker.io",
        namespace,
        "app",
        _probe(namespace, tags),
        store_root=store,
        observed_at=T0 + timedelta(minutes=minutes),
        history_key=key,
    )
    assert result["error"] is None, result["error"]


@pytest.fixture
def roots(tmp_path):
    store, led = tmp_path / "observations", tmp_path / "detections"
    for minutes in (1, 2, 3):
        _observe(store, "alpha", minutes)
    ledger.record_detection("django", "lifecycle", "EOL", ["4.2"], root=led, history_key=KEY)
    return store, led


def _audit(store, led, keys=None, require_keyed=True):
    keys = keyring(KEY) if keys is None else keys
    return audit_history(store, led, keys, require_keyed=require_keyed)


def _statuses(result):
    return sorted((p["kind"], p["status"]) for p in result["problems"])


def _entry(led):
    [path] = list((led / "django").glob("*.json"))
    return path


def _history(store):
    return list_observations("docker.io", "alpha", "app", root=store)


# --- What passes -------------------------------------------------------------------------------


def test_nothing_stored_is_empty(tmp_path):
    result = _audit(tmp_path / "o", tmp_path / "d")
    assert result["status"] == EMPTY and result["problems"] == []


def test_a_genuine_keyed_history_passes(roots):
    result = _audit(*roots)
    assert result["status"] == OK
    assert (result["histories"], result["ledger_entries"]) == (1, 1)


def test_a_rotated_key_still_verifies_with_the_retired_key_supplied(tmp_path):
    store, led = tmp_path / "o", tmp_path / "d"
    _observe(store, "alpha", 1, key=OLD)
    observe_repository(
        "docker.io",
        "alpha",
        "app",
        _probe("alpha", ["1.0", "1.1", "1.2"]),
        store_root=store,
        observed_at=T0 + timedelta(minutes=2),
        history_key=KEY,
        previous_keys=(OLD,),
    )
    assert _audit(store, led, keyring(KEY, (OLD,)))["status"] == OK
    # Without the retired key, the older run cannot be checked.
    assert _statuses(_audit(store, led)) == [("observations", "UNKNOWN")]


# --- What is refused ---------------------------------------------------------------------------


def test_an_edited_ledger_entry_is_refused(roots):
    store, led = roots
    path = _entry(led)
    entry = json.loads(path.read_text(encoding="utf-8"))
    entry["first_seen"] = "2020-01-01T00:00:00+00:00"  # a backdated first detection
    path.write_text(json.dumps(entry), encoding="utf-8")
    result = _audit(store, led)
    assert result["status"] == REFUSED
    assert _statuses(result) == [("ledger", "BROKEN")]


def test_a_ledger_entry_that_is_not_json_is_refused(roots):
    store, led = roots
    _entry(led).write_text("not json", encoding="utf-8")
    assert _statuses(_audit(store, led)) == [("ledger", "BROKEN")]


def test_an_edited_observation_is_refused(roots):
    store, led = roots
    path = _history(store)[1]
    record = json.loads(path.read_text(encoding="utf-8"))
    record["tags"] = {"9.9": ["sha256:9.9"]}
    path.write_text(json.dumps(record), encoding="utf-8")
    assert _statuses(_audit(store, led)) == [("observations", "BROKEN")]


def test_a_dropped_newest_observation_is_a_rollback(roots):
    store, led = roots
    _history(store)[-1].unlink()
    assert _statuses(_audit(store, led)) == [("observations", "ROLLBACK")]


def test_an_unkeyed_record_after_keyed_ones_is_a_downgrade(roots):
    store, led = roots
    newest = _history(store)[-1]
    record = json.loads(newest.read_text(encoding="utf-8"))
    record.update(history_mac=None, key_id=None)  # chain hash unchanged: tip still agrees
    newest.write_text(json.dumps(record), encoding="utf-8")
    assert _statuses(_audit(store, led)) == [("observations", "DOWNGRADE")]


def test_a_foreign_history_is_refused(tmp_path):
    store, led = tmp_path / "o", tmp_path / "d"
    _observe(store, "alpha", 1, key=OTHER)
    ledger.record_detection("django", "lifecycle", "EOL", ["4.2"], root=led, history_key=OTHER)
    result = _audit(store, led)
    assert _statuses(result) == [("ledger", "UNKNOWN"), ("observations", "UNKNOWN")]
    assert "foreign" in result["problems"][0]["detail"]


def test_unkeyed_history_is_refused_only_when_keys_are_required(tmp_path):
    store, led = tmp_path / "o", tmp_path / "d"
    _observe(store, "alpha", 1, key=None)
    ledger.record_detection("django", "lifecycle", "EOL", ["4.2"], root=led)
    assert _statuses(_audit(store, led)) == [
        ("ledger", "VALID_UNKEYED"),
        ("observations", "VALID_UNKEYED"),
    ]
    assert _audit(store, led, require_keyed=False)["status"] == OK


def test_names_from_the_store_never_reach_the_report_unsafely(tmp_path):
    store, led = tmp_path / "o", tmp_path / "d"
    _observe(store, "alpha", 1)
    _observe(store, "alpha", 2)
    hostile = store / "docker.io" / "alpha" / "x y$(id)"
    repo_dir(store, "docker.io", "alpha", "app").rename(hostile)
    sorted(hostile.glob("*.json"))[-2].unlink()  # newest record (tip.json sorts last)
    result = _audit(store, led)
    [problem] = result["problems"]
    assert problem["subject"] == "docker.io/alpha/x_y__id_"
    assert "$" not in problem["detail"] and "id" not in problem["detail"]


# --- The command -------------------------------------------------------------------------------


def _run(store, led, *args, key=KEY):
    env = {"OPENPULSE_HISTORY_KEY": base64.b64encode(b"a" * 32).decode()} if key else {}
    return CliRunner().invoke(
        cli, ["history-audit", "--store", str(store), "--ledger", str(led), *args], env=env
    )


def test_the_command_exits_1_on_a_refusal_and_names_it(roots):
    store, led = roots
    _history(store)[-1].unlink()
    result = _run(store, led, "--require-keyed")
    assert result.exit_code == 1
    assert "history audit: REFUSED (1 observation history(s), 1 ledger entry(s))" in result.output
    assert "! observations docker.io/alpha/app: ROLLBACK" in result.output


def test_the_command_passes_a_genuine_history(roots):
    result = _run(*roots, "--require-keyed", "--json")
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["status"] == OK


def test_require_keyed_needs_a_key(roots):
    result = _run(*roots, "--require-keyed", key=None)
    assert result.exit_code != 0
    assert "--require-keyed needs a history key" in result.output


# --- The Action --------------------------------------------------------------------------------

ACTION = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))
STEPS = {s.get("id") or s.get("uses", "") or s.get("name"): s for s in ACTION["runs"]["steps"]}
CACHE = "@55cc8345863c7cc4c66a329aec7e433d2d1c52a9"


def _save_step():
    return next(s for s in ACTION["runs"]["steps"] if "actions/cache/save" in s.get("uses", ""))


def test_history_is_opt_in_and_needs_a_key():
    assert ACTION["inputs"]["history"]["default"] == "off"
    assert ACTION["inputs"]["history-key"]["default"] == ""
    setup = STEPS["history-setup"]
    assert setup["if"] == "inputs.history != 'off'"
    assert "history: on needs history-key" in setup["run"]
    # The key is never read into the setup step, only whether one was given.
    assert "inputs.history-key" not in json.dumps(setup["env"]).replace(
        "inputs.history-key != ''", ""
    )


def test_the_restored_history_is_audited_before_anything_runs():
    order = [s.get("id") or s.get("uses", "") for s in ACTION["runs"]["steps"]]
    assert order.index("history-restore") < order.index("history-audit") < order.index("run")
    audit = STEPS["history-audit"]
    assert "history-audit --require-keyed" in audit["run"]
    # Threat: the key in the process list or the script - env only.
    assert audit["env"]["OPENPULSE_HISTORY_KEY"] == "${{ inputs.history-key }}"
    assert "inputs." not in audit["run"]


def test_the_cache_actions_are_pinned_and_share_one_key():
    restore = STEPS["history-restore"]
    save = _save_step()
    assert restore["uses"].endswith(CACHE) and save["uses"].endswith(CACHE)
    assert restore["with"]["key"] == save["with"]["key"]
    assert restore["with"]["path"] == save["with"]["path"]
    assert restore["with"]["restore-keys"] == "openpulse-history-v1-${{ inputs.history-id }}-"


def test_the_history_is_saved_only_after_a_passed_audit_on_the_default_branch():
    condition = _save_step()["if"]
    assert "steps.history-audit.outcome == 'success'" in condition
    assert "github.event.repository.default_branch" in condition
    assert "!cancelled()" in condition


def test_history_id_is_validated():
    assert "^[A-Za-z0-9._-]{1,64}$" in STEPS["history-setup"]["run"]

"""Rollback and downgrade detection (v0.9.0 item B4, finding H2).

Exit criterion: deleting the tip plus the newest records is reported as
rollback. Chained-to-legacy and keyed-to-unkeyed downgrades are refused,
and only an explicit, reasoned re-baseline accepts a refused history.
"""

import base64
import json
from datetime import datetime, timedelta, timezone

import pytest
from click.testing import CliRunner

from core.history_key import REBASELINE_DOMAIN, parse_key
from core.observations.registry import RegistryObservation
from core.observations.store import (
    list_observations,
    read_rebaselines,
    read_tip,
    repo_dir,
    save_observation,
)
from core.observations.sweep import (
    MAX_REBASELINE_REASON,
    observe_repository,
    validate_rebaseline_reason,
)

KEY = parse_key(base64.b64encode(b"b" * 32).decode())
T0 = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


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


def _observe(root, minutes, key=None, reason=None):
    tags = ["1.0"] + [f"1.{i}" for i in range(1, minutes + 1)]
    return observe_repository(
        "docker.io",
        "demo",
        "app",
        _probe(tags),
        store_root=root,
        observed_at=T0 + timedelta(minutes=minutes),
        history_key=key,
        rebaseline_reason=reason,
    )


def _dir(root):
    return repo_dir(root, "docker.io", "demo", "app")


def _files(root):
    return list_observations("docker.io", "demo", "app", root=root)


def _history(root, n=3, key=None):
    for minutes in range(n):
        assert _observe(root, minutes, key=key)["error"] is None


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


def test_truncation_plus_tip_deletion_is_rollback_suspected(tmp_path):
    """The exit criterion. Before B4 a missing tip was adopted silently."""
    _history(tmp_path)
    _files(tmp_path)[-1].unlink()
    (_dir(tmp_path) / "tip.json").unlink()
    result = _observe(tmp_path, 3)
    assert result["history_status"] == "ROLLBACK_SUSPECTED"
    assert result["saved_path"] is None
    assert "--rebaseline" in result["error"]["safe_message"]
    assert len(_files(tmp_path)) == 2


def test_truncation_with_tip_kept_is_rollback(tmp_path):
    _history(tmp_path)
    _files(tmp_path)[-1].unlink()
    assert _observe(tmp_path, 3)["history_status"] == "ROLLBACK"


def test_chained_history_without_tip_is_rollback_suspected(tmp_path):
    """A pre-upgrade history (chained, no tip) needs one explicit re-baseline."""
    obs = (
        RegistryObservation(
            registry="docker.io",
            namespace="demo",
            repository="app",
            tags={"1.0": ["sha256:1.0"]},
            observed_at=T0,
        )
        .seal()
        .link(None)
    )
    save_observation(obs.model_dump(mode="json"), root=tmp_path)
    assert _observe(tmp_path, 1)["history_status"] == "ROLLBACK_SUSPECTED"


def test_unchained_record_after_chained_ones_is_downgrade(tmp_path):
    _history(tmp_path, n=2)
    legacy = RegistryObservation(
        registry="docker.io",
        namespace="demo",
        repository="app",
        tags={"1.0": ["sha256:1.0"]},
        observed_at=T0 + timedelta(minutes=5),
    ).seal()
    save_observation(legacy.model_dump(mode="json"), root=tmp_path)
    result = _observe(tmp_path, 6)
    assert result["history_status"] == "DOWNGRADE"
    assert "unchained record after chained" in result["error"]["safe_message"]


def test_unkeyed_record_after_keyed_ones_is_downgrade(tmp_path):
    _history(tmp_path, n=2, key=KEY)
    newest = _files(tmp_path)[-1]
    record = json.loads(newest.read_text(encoding="utf-8"))
    record.update(history_mac=None, key_id=None)  # chain hash unchanged: tip still agrees
    newest.write_text(json.dumps(record), encoding="utf-8")
    result = _observe(tmp_path, 2, key=KEY)
    assert result["history_status"] == "DOWNGRADE"
    assert "unkeyed record after keyed" in result["error"]["safe_message"]


def test_healthy_history_is_not_refused(tmp_path):
    _history(tmp_path)
    assert _observe(tmp_path, 3)["error"] is None


# ---------------------------------------------------------------------------
# Re-baseline
# ---------------------------------------------------------------------------


def test_rebaseline_accepts_a_rollback_at_its_current_tip(tmp_path):
    _history(tmp_path)
    _files(tmp_path)[-1].unlink()
    (_dir(tmp_path) / "tip.json").unlink()
    remaining = [json.loads(p.read_text(encoding="utf-8")) for p in _files(tmp_path)]
    result = _observe(tmp_path, 3, reason="restored from a backup taken before the last run")
    assert result["error"] is None
    assert result["history_status"] == "REBASELINED"
    assert result["changes"] == []  # no change claims cross a re-baseline
    (entry,) = read_rebaselines(_dir(tmp_path))
    assert entry["previous_status"] == "ROLLBACK_SUSPECTED"
    assert entry["accepted_tip"] == remaining[-1]["chain_hash"]
    assert entry["quarantine"] is None
    assert entry["reason"] == "restored from a backup taken before the last run"
    # The chain continues from the accepted tip, and the next run is normal.
    assert len(_files(tmp_path)) == 3
    assert (
        read_tip(_dir(tmp_path))["tip"]
        == json.loads(_files(tmp_path)[-1].read_text())["chain_hash"]
    )
    assert _observe(tmp_path, 4)["error"] is None


def test_rebaseline_quarantines_a_downgraded_history(tmp_path):
    _history(tmp_path, n=2)
    legacy = RegistryObservation(
        registry="docker.io",
        namespace="demo",
        repository="app",
        tags={"1.0": ["sha256:1.0"]},
        observed_at=T0 + timedelta(minutes=5),
    ).seal()
    save_observation(legacy.model_dump(mode="json"), root=tmp_path)
    result = _observe(tmp_path, 6, reason="legacy writer ran by mistake; investigated")
    assert result["history_status"] == "REBASELINED"
    (entry,) = read_rebaselines(_dir(tmp_path))
    assert entry["previous_status"] == "DOWNGRADE" and entry["accepted_tip"] is None
    quarantine = _dir(tmp_path) / entry["quarantine"]
    assert len(list(quarantine.glob("*.json"))) == 4  # 3 records + the tip, kept as evidence
    assert len(_files(tmp_path)) == 1  # a new genesis
    assert json.loads(_files(tmp_path)[0].read_text())["previous_observation_hash"] == "genesis"
    assert _observe(tmp_path, 7)["error"] is None


def test_rebaseline_of_a_wiped_history_with_a_surviving_tip(tmp_path):
    _history(tmp_path)
    for path in _files(tmp_path):
        path.unlink()
    assert _observe(tmp_path, 3)["history_status"] == "ROLLBACK"
    result = _observe(tmp_path, 3, reason="store moved to a new disk; old data lost")
    assert result["history_status"] == "REBASELINED"
    assert read_rebaselines(_dir(tmp_path))[0]["quarantine"]


def test_rebaseline_log_is_maced_under_the_key(tmp_path):
    _history(tmp_path, key=KEY)
    _files(tmp_path)[-1].unlink()
    result = _observe(tmp_path, 3, key=KEY, reason="known truncation during disk repair")
    assert result["error"] is None
    (entry,) = read_rebaselines(_dir(tmp_path))
    assert entry["key_id"] == KEY.key_id
    unsigned = {k: v for k, v in entry.items() if k not in ("key_id", "mac")}
    parts = [str(unsigned[k] or "") for k in sorted(unsigned)]
    assert KEY.verify(entry["mac"], REBASELINE_DOMAIN, *parts)


def test_healthy_history_ignores_a_reason(tmp_path):
    _history(tmp_path)
    result = _observe(tmp_path, 3, reason="nothing to accept")
    assert result["error"] is None
    assert result["history_status"] != "REBASELINED"
    assert read_rebaselines(_dir(tmp_path)) == []


def test_rebaseline_log_is_not_an_observation(tmp_path):
    _history(tmp_path)
    _files(tmp_path)[-1].unlink()
    _observe(tmp_path, 3, reason="accepted")
    assert all(p.name != "rebaselines.json" for p in _files(tmp_path))


@pytest.mark.parametrize("reason", ["", "   ", "two\nlines", "x" * (MAX_REBASELINE_REASON + 1)])
def test_bad_reasons_are_refused(reason):
    with pytest.raises(ValueError):
        validate_rebaseline_reason(reason)


# ---------------------------------------------------------------------------
# Where users hit it: the CLI
# ---------------------------------------------------------------------------


def _cli(tmp_path, monkeypatch, *extra, minutes=0):
    from cli.main import cli

    tags = ["1.0"] + [f"1.{i}" for i in range(1, minutes + 1)]
    monkeypatch.setattr(
        "collectors.registries.docker.RegistryCollector.check_image",
        lambda self, namespace, repo: _probe(tags),
    )
    args = ["observe", "--namespace", "demo", "--repo", "app", "--store", str(tmp_path), *extra]
    return CliRunner().invoke(cli, args, env={"OPENPULSE_HISTORY_KEY": ""})


def test_observe_cli_refuses_then_rebaselines(tmp_path, monkeypatch):
    assert _cli(tmp_path, monkeypatch).exit_code == 0
    assert _cli(tmp_path, monkeypatch, minutes=1).exit_code == 0
    (_dir(tmp_path) / "tip.json").unlink()
    refused = _cli(tmp_path, monkeypatch, minutes=2)
    assert refused.exit_code == 1
    assert "tip pointer is missing" in refused.output
    accepted = _cli(
        tmp_path, monkeypatch, "--rebaseline", "--reason", "tip lost in a migration", minutes=2
    )
    assert accepted.exit_code == 0, accepted.output
    assert "re-baselined" in accepted.output
    assert read_rebaselines(_dir(tmp_path))[0]["reason"] == "tip lost in a migration"


def test_observe_cli_rebaseline_needs_a_reason(tmp_path, monkeypatch):
    result = _cli(tmp_path, monkeypatch, "--rebaseline")
    assert result.exit_code != 0
    assert "needs --reason" in result.output


def test_observe_cli_reason_needs_rebaseline(tmp_path, monkeypatch):
    result = _cli(tmp_path, monkeypatch, "--reason", "why")
    assert result.exit_code != 0
    assert "only used with --rebaseline" in result.output

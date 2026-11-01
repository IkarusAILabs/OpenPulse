"""History anchors (v0.9.0 item B5, finding H2).

Each attack here is one B4's local checks cannot see, because it removes
its own evidence; an anchor kept outside the store catches it.
"""

import base64
import hashlib
import json
import shutil
from datetime import datetime, timedelta, timezone

import pytest
from click.testing import CliRunner

from core.anchor import build_anchor, merkle_root, verify_anchor
from core.detections import ledger
from core.history_key import keyring, parse_key
from core.observations.store import list_observations, repo_dir, write_tip
from core.observations.sweep import observe_repository

KEY = parse_key(base64.b64encode(b"a" * 32).decode())
OLD = parse_key(base64.b64encode(b"z" * 32).decode())
T0 = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Merkle root (RFC 6962)
# ---------------------------------------------------------------------------


def _h(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def test_merkle_root_follows_rfc6962():
    a, b, c = b"a", b"b", b"c"
    leaf = [_h(b"\x00" + x) for x in (a, b, c)]
    expected = _h(b"\x01" + _h(b"\x01" + leaf[0] + leaf[1]) + leaf[2])
    assert merkle_root([a, b, c]) == "sha256:" + expected.hex()
    assert merkle_root([a]) == "sha256:" + leaf[0].hex()
    assert merkle_root([]) == "sha256:" + hashlib.sha256(b"").hexdigest()
    assert merkle_root([a, b]) != merkle_root([b, a])


# ---------------------------------------------------------------------------
# Fixtures: a store with two histories and a ledger
# ---------------------------------------------------------------------------


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


def _observe(store, namespace, minutes, key=None, reason=None):
    tags = ["1.0"] + [f"1.{i}" for i in range(1, minutes + 1)]
    result = observe_repository(
        "docker.io",
        namespace,
        "app",
        _probe(namespace, tags),
        store_root=store,
        observed_at=T0 + timedelta(minutes=minutes),
        history_key=key,
        rebaseline_reason=reason,
    )
    assert result["error"] is None, result["error"]
    return result


@pytest.fixture
def roots(tmp_path):
    store, led = tmp_path / "observations", tmp_path / "detections"
    for namespace in ("alpha", "beta"):
        for minutes in range(3):
            _observe(store, namespace, minutes)
    ledger.record_detection("django", "lifecycle", "EOL", ["4.2"], root=led)
    ledger.record_detection("redis", "security", "CVE-1", [], root=led)
    return store, led


def _entry_path(led, project="django", cls="lifecycle", subject="EOL", scope=("4.2",)):
    return led / project / f"{ledger.fact_key(project, cls, subject, list(scope))}.json"


def _kinds(result):
    return sorted(v["kind"] for v in result["violations"])


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


def test_untouched_store_verifies(roots):
    store, led = roots
    anchor = build_anchor(store, led)
    assert set(anchor["observations"]) == {"docker.io/alpha/app", "docker.io/beta/app"}
    assert len(anchor["ledger"]["entries"]) == 2
    result = verify_anchor(anchor, store, led)
    assert result == {"status": "OK", "signature": "UNSIGNED", "violations": [], "notices": []}


def test_growth_after_the_anchor_is_fine(roots):
    store, led = roots
    anchor = build_anchor(store, led)
    _observe(store, "alpha", 3)
    _observe(store, "gamma", 0)
    ledger.record_detection("django", "lifecycle", "EOL", ["4.2"], root=led)  # new sighting
    ledger.record_detection("kafka", "lifecycle", "EOL", ["3.0"], root=led)  # new entry
    assert verify_anchor(anchor, store, led)["status"] == "OK"


def test_wiped_history_folder_is_caught(roots):
    """B4 sees a first run here; the anchor does not."""
    store, led = roots
    anchor = build_anchor(store, led)
    shutil.rmtree(repo_dir(store, "docker.io", "alpha", "app"))
    result = verify_anchor(anchor, store, led)
    assert result["status"] == "VIOLATED"
    assert _kinds(result) == ["WIPED"]
    assert result["violations"][0]["subject"] == "docker.io/alpha/app"


def test_truncation_with_a_rewritten_tip_is_caught(roots):
    """B4 sees a consistent history here: the tip was moved back to match."""
    store, led = roots
    anchor = build_anchor(store, led)
    files = list_observations("docker.io", "alpha", "app", root=store)
    files[-1].unlink()
    previous = json.loads(files[-2].read_text(encoding="utf-8"))
    write_tip(files[-2].parent, previous["chain_hash"])
    assert _kinds(verify_anchor(anchor, store, led)) == ["ROLLBACK"]


def test_deleted_ledger_entry_is_caught(roots):
    store, led = roots
    anchor = build_anchor(store, led)
    _entry_path(led).unlink()
    assert _kinds(verify_anchor(anchor, store, led)) == ["LEDGER_DELETED"]


def test_backdated_ledger_entry_is_caught(roots):
    """Even with its content hash recomputed (no key): first_seen differs from the anchor."""
    store, led = roots
    anchor = build_anchor(store, led)
    path = _entry_path(led)
    entry = json.loads(path.read_text(encoding="utf-8"))
    entry["first_seen"] = "2026-01-01T00:00:00+00:00"
    entry["content_hash"] = ledger._entry_content_hash(
        "django", "lifecycle", "EOL", ["4.2"], entry["first_seen"], entry["last_seen"]
    )
    path.write_text(json.dumps(entry), encoding="utf-8")
    assert ledger.verify_entry(entry)
    assert _kinds(verify_anchor(anchor, store, led)) == ["LEDGER_REWRITTEN"]


def test_deleted_rotation_log_is_caught(tmp_path):
    store, led = tmp_path / "observations", tmp_path / "detections"
    ledger.record_detection("django", "lifecycle", "EOL", ["4.2"], root=led, history_key=OLD)
    ledger.record_detection(
        "django", "lifecycle", "EOL", ["4.2"], root=led, history_key=KEY, previous_keys=(OLD,)
    )
    anchor = build_anchor(store, led, history_key=KEY)
    assert len(anchor["rotations"]) == 1
    (led / ledger.ROTATIONS_FILE).unlink()
    assert _kinds(verify_anchor(anchor, store, led, keyring(KEY))) == ["ROTATION_LOG"]


def test_dropped_rebaseline_log_is_caught(roots):
    store, led = roots
    files = list_observations("docker.io", "alpha", "app", root=store)
    files[-1].unlink()
    _observe(store, "alpha", 3, reason="known truncation")
    anchor = build_anchor(store, led)
    (repo_dir(store, "docker.io", "alpha", "app") / "rebaselines.json").unlink()
    assert "REBASELINE_LOG" in _kinds(verify_anchor(anchor, store, led))


# ---------------------------------------------------------------------------
# Signature and re-baselines
# ---------------------------------------------------------------------------


def test_keyed_anchor_signature(roots):
    store, led = roots
    anchor = build_anchor(store, led, history_key=KEY)
    assert verify_anchor(anchor, store, led, keyring(KEY))["signature"] == "VALID"
    assert verify_anchor(anchor, store, led)["signature"] == "UNKNOWN"
    # An attacker drops the wiped repository from the anchor to hide the wipe.
    shutil.rmtree(repo_dir(store, "docker.io", "alpha", "app"))
    forged = {
        **anchor,
        "observations": {"docker.io/beta/app": anchor["observations"]["docker.io/beta/app"]},
    }
    result = verify_anchor(forged, store, led, keyring(KEY))
    assert result["signature"] == "BROKEN"
    assert _kinds(result) == ["ANCHOR_SIGNATURE"]


def test_keyed_rebaseline_after_the_anchor_is_a_notice(tmp_path):
    store, led = tmp_path / "observations", tmp_path / "detections"
    for minutes in range(3):
        _observe(store, "alpha", minutes, key=KEY)
    # Anchored a day before the re-baseline below.
    anchor = build_anchor(store, led, history_key=KEY, now=T0 - timedelta(days=1))
    shutil.rmtree(repo_dir(store, "docker.io", "alpha", "app"))
    (repo_dir(store, "docker.io", "alpha", "app")).mkdir(parents=True)
    write_tip(repo_dir(store, "docker.io", "alpha", "app"), "sha256:gone")
    _observe(store, "alpha", 4, key=KEY, reason="disk replaced; history lost")
    keyed = verify_anchor(anchor, store, led, keyring(KEY))
    assert keyed["status"] == "OK"
    assert [n["kind"] for n in keyed["notices"]] == ["REBASELINED"]
    # Without the key, the re-baseline log proves nothing.
    assert verify_anchor(anchor, store, led)["status"] == "VIOLATED"


def test_unsupported_anchor_version(roots):
    store, led = roots
    anchor = {**build_anchor(store, led), "anchor_version": 99}
    assert _kinds(verify_anchor(anchor, store, led)) == ["ANCHOR_VERSION"]


# ---------------------------------------------------------------------------
# Where users hit it: the CLI
# ---------------------------------------------------------------------------


def _run(*args, env=None):
    from cli.main import cli

    return CliRunner().invoke(cli, list(args), env={"OPENPULSE_HISTORY_KEY": "", **(env or {})})


def test_anchor_and_verify_cli(roots, tmp_path):
    store, led = roots
    out = tmp_path / "anchors" / "anchor.json"
    out.parent.mkdir()
    made = _run("anchor", "--store", str(store), "--ledger", str(led), "--out", str(out))
    assert made.exit_code == 0, made.output
    assert json.loads(out.read_text(encoding="utf-8"))["anchor_version"] == 1
    ok = _run("verify", "--anchor", str(out), "--store", str(store), "--ledger", str(led))
    assert ok.exit_code == 0, ok.output
    assert "OK (signature UNSIGNED)" in ok.output
    shutil.rmtree(repo_dir(store, "docker.io", "beta", "app"))
    bad = _run("verify", "--anchor", str(out), "--store", str(store), "--ledger", str(led))
    assert bad.exit_code == 1
    assert "WIPED docker.io/beta/app" in bad.output


def test_verify_cli_require_signed(roots, tmp_path):
    store, led = roots
    out = tmp_path / "anchor.json"
    key_text = base64.b64encode(b"a" * 32).decode()
    assert (
        _run("anchor", "--store", str(store), "--ledger", str(led), "--out", str(out)).exit_code
        == 0
    )
    unsigned = _run(
        "verify",
        "--anchor",
        str(out),
        "--store",
        str(store),
        "--ledger",
        str(led),
        "--require-signed",
    )
    assert unsigned.exit_code == 1
    keyed = tmp_path / "keyed.json"
    env = {"OPENPULSE_HISTORY_KEY": key_text}
    assert (
        _run(
            "anchor", "--store", str(store), "--ledger", str(led), "--out", str(keyed), env=env
        ).exit_code
        == 0
    )
    signed = _run(
        "verify",
        "--anchor",
        str(keyed),
        "--store",
        str(store),
        "--ledger",
        str(led),
        "--require-signed",
        env=env,
    )
    assert signed.exit_code == 0, signed.output
    assert key_text not in signed.output


def test_anchor_cli_refuses_to_write_inside_openpulse(roots, tmp_path):
    store, led = roots
    inside = tmp_path / ".openpulse" / "anchor.json"
    inside.parent.mkdir()
    result = _run("anchor", "--store", str(store), "--ledger", str(led), "--out", str(inside))
    assert result.exit_code != 0
    assert "anchors nothing" in result.output

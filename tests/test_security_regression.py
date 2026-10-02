"""Security regression tests — hostile, malformed, and oversized inputs.

Everything here runs offline. Each test proves one corrupted input
degrades to an explicit error/negative — never to a stronger claim,
an exception escape, or a secret leak.
"""

import json

import pytest


def _catalog():
    return [{"slug": "demo", "docker_images": ["docker.io/demo/app"]}]


def _probe(tags):
    def run(namespace, repo):
        return {
            "collector": "registries",
            "registry": "docker.io",
            "namespace": namespace,
            "repo": repo,
            "digests": {tag: [f"sha256:{tag}"] for tag in tags},
            "count": len(tags),
        }

    return run


def test_malformed_image_refs_never_raise():
    from core.risk.match import event_affects_ref, split_image_ref

    for ref in ("", ":", "///", "docker.io/", "a" * 500, "HTTP://X/Y", "oci://", "@sha256:abc"):
        assert split_image_ref(ref)  # always a triple, never an exception
    from core.schema.models import OSSEvent

    event = OSSEvent(
        id="e",
        project_slug="x",
        event_type="EOL",
        title="t",
        summary="s",
        confidence="EMERGING",
        impact="WATCH",
        scope={"kind": "version", "versions": ["1.0"]},
        evidences=[
            {
                "source": {
                    "name": "s",
                    "url": "https://example.com/x",
                    "authority": "secondary",
                    "fetched_at": "2026-09-01T00:00:00Z",
                },
                "excerpt": "e",
                "relation": "supports",
            }
        ],
    )
    for ref in ("", ":", "///"):
        out = event_affects_ref(event, ref)
        assert out["affected"] is False


def test_malformed_registry_responses_recorded_not_raised(tmp_path):
    from core.observations.sweep import observe_repository

    for bad in (
        None,
        "not-a-dict",
        {"digests": ["not", "a", "dict"]},
        {"digests": None},
        {"digests": "sha256:abc"},
        {"digests": {"latest": "not-a-list"}},
    ):
        result = observe_repository("docker.io", "demo", "app", bad, store_root=tmp_path)
        assert result["error"] is not None
        assert result["changes"] == []


def test_unexpected_json_types_skipped(tmp_path):
    from core.observations import store

    directory = store.repo_dir(tmp_path, "docker.io", "demo", "app")
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "a.json").write_text("[1, 2]", encoding="utf-8")
    (directory / "b.json").write_text('"just a string"', encoding="utf-8")
    (directory / "c.json").write_text("{corrupt", encoding="utf-8")
    assert store.try_load(directory / "a.json") is None
    assert store.load_all("docker.io", "demo", "app", root=tmp_path) == []
    assert store.load_previous("docker.io", "demo", "app", root=tmp_path) is None


def test_path_traversal_stays_under_root(tmp_path):
    from core.observations import store

    for hostile in ("..", "../..", "../../etc", ".", "", "a/b", "x/../../y"):
        path = store.repo_dir(tmp_path, hostile, hostile, hostile)
        assert tmp_path.resolve() in path.resolve().parents or path.resolve() == tmp_path.resolve()


def test_save_and_load_roundtrip_under_hostile_names(tmp_path):
    from core.observations import store

    path = store.save_observation(
        {"registry": "..", "namespace": "..", "repository": "..", "observed_at": "2026-09-01"},
        root=tmp_path,
    )
    assert tmp_path.resolve() in path.resolve().parents


def test_malicious_exception_strings_redacted():
    from collectors.errors import as_error, redact

    evil = (
        "boom token=sk-live-abc https://admin:s3cret@hooks.example/x?api_key=1 "
        "at /home/deploy/.config/proxy C:\\Users\\ci\\secret"
    )
    assert "sk-live-abc" not in redact(evil)
    assert "s3cret@" not in redact(evil)
    assert "api_key=1" not in redact(evil)
    assert "/home/deploy" not in redact(evil)
    assert "C:\\Users\\ci" not in redact(evil)
    try:
        raise RuntimeError(evil)
    except RuntimeError as exc:
        err = as_error("registries", exc)
    assert "sk-live-abc" not in err["safe_message"]
    assert "s3cret" not in err["safe_message"]
    assert err["category"] == "unknown"


def test_corrupted_json_history_is_untrusted(tmp_path):

    from core.observations.sweep import sweep_catalog

    result = sweep_catalog(_catalog(), _probe(["latest"]), store_root=tmp_path)
    assert result["errors"] == []
    from core.observations.store import list_observations

    files = list_observations("docker.io", "demo", "app", root=tmp_path)
    assert len(files) == 1
    directory = files[0]
    record = json.loads(directory.read_text(encoding="utf-8"))
    record["observed_at"] = "not-a-timestamp"  # keep hashes: chain must still break
    directory.write_text(json.dumps(record), encoding="utf-8")
    rerun = sweep_catalog(_catalog(), _probe(["latest"]), store_root=tmp_path)
    assert rerun["changes"] == []
    assert any(e.get("integrity") == "BROKEN" for e in rerun["errors"])


def test_corrupted_hash_chain_walk():
    from core.evidence.provenance import hash_content
    from core.observations.registry import _raw_body, verify_registry_history

    assert verify_registry_history(["not-a-dict"])["status"] == "BROKEN"
    # A sealed-but-never-chained record is legacy: UNKNOWN, never VALID.
    legacy = {
        "registry": "docker.io",
        "namespace": "demo",
        "repository": "app",
        "tags": {"latest": ["sha256:A"]},
        "missing": False,
        "content_hash": "",
    }
    legacy["content_hash"] = hash_content(_raw_body(legacy))
    assert verify_registry_history([legacy])["status"] == "UNKNOWN"


def test_duplicate_observations_no_changes(tmp_path):

    from core.observations.registry import verify_registry_history
    from core.observations.store import load_all
    from core.observations.sweep import sweep_catalog

    sweep_catalog(_catalog(), _probe(["latest", "1.0"]), store_root=tmp_path)
    rerun = sweep_catalog(_catalog(), _probe(["latest", "1.0"]), store_root=tmp_path)
    assert rerun["changes"] == []
    assert rerun["errors"] == []
    from core.observations.chain import order_history

    records = load_all("docker.io", "demo", "app", root=tmp_path)
    ordered, chain_ok = order_history(records)
    assert chain_ok
    assert verify_registry_history(ordered)["status"] == "VALID"


def test_concurrent_writes_all_land(tmp_path):
    import threading

    from core.observations import store

    def write(i):
        store.save_observation(
            {
                "registry": "docker.io",
                "namespace": "demo",
                "repository": "app",
                "observed_at": f"2026-09-01T00:00:{i:02d}+00:00",
                "content_hash": f"sha256:{i}",
            },
            root=tmp_path,
        )

    threads = [threading.Thread(target=write, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    files = store.list_observations("docker.io", "demo", "app", root=tmp_path)
    assert len(files) == 8
    for path in files:
        assert isinstance(store.try_load(path), dict)


def test_unknown_and_distrusted_identity(tmp_path):
    from core.entities.identity import resolution_trust

    assert resolution_trust("some-unknown-thing:1.0")["via"] == "self"
    catalog = [
        {
            "slug": "evil",
            "aliases": ["evil/pkg"],
            "docker_images": [],
            "identity": {"status": "UNVERIFIED", "note": "test only"},
        }
    ]
    trust = resolution_trust("evil/pkg", catalog=catalog)
    assert trust["identity_status"] == "UNVERIFIED"
    assert trust["slug"] == "evil"


def test_unverified_identity_caps_strong_conclusions():
    from core.entities.identity import resolution_trust  # noqa: F401
    from core.risk.check import _combine

    causes = [
        {
            "cause": "upstream_change",
            "relationship": "AFFECTS_VERSION",
            "affected": True,
            "match_method": "event_scope_version",
            "event_id": "e",
            "impact": "ACTION",
            "evidence": ["endoflife.date"],
            "evidence_confidence": "CONFIRMED",
            "identity_status": "UNVERIFIED",
            "identity_via": "catalog",
            "reason": "pin matches scope",
        }
    ]
    verdict = _combine(
        {"kind": "package", "package": "evil", "ecosystem": "PyPI", "version": "1.0"},
        causes,
    )
    assert verdict.affected is True
    assert verdict.confidence == "EMERGING"  # capped, never CONFIRMED/CORROBORATED
    assert "identity" in verdict.reason


def test_invalid_confidence_impact_combos_degrade_safely():
    from core.risk.impact import evaluate_impact

    out = evaluate_impact({"analyst": "change", "impact": "CRITICAL!!!"})
    assert out["eligibility"] == "INFORMATIONAL"
    out = evaluate_impact(
        {"analyst": "change", "event_type": "EOL"},
        dependency_context={
            "verdict": "AFFECTS_VERSION",
            "affected": True,
            "confidence": "BOGUS",
            "reason": "x",
        },
    )
    assert out["assessment"] == "AFFECTS_DEPENDENCY"
    assert out["eligibility"] == "REVIEW"


def test_oversized_webhook_response_rejected():
    import httpx

    from core.notify import WebhookPolicy, post_digest

    def big(request):
        return httpx.Response(200, content=b"x" * (2 * 1024 * 1024), request=request)

    result = post_digest(
        "https://hooks.example/x",
        "md",
        transport=httpx.MockTransport(big),
        resolver=lambda host: ["93.184.216.34"],
        policy=WebhookPolicy(max_response_bytes=1024),
    )
    assert result["ok"] is False
    assert "size limit" in result["error"]


def test_webhook_secrets_never_logged():
    import httpx

    from core.notify import post_digest

    def fail(request):
        raise httpx.ConnectTimeout("down")

    result = post_digest(
        "https://user:s3cret-token@hooks.example:8443/x?api_key=ABC",
        "md",
        transport=httpx.MockTransport(fail),
        resolver=lambda host: ["93.184.216.34"],
    )
    assert result["ok"] is False
    assert "s3cret" not in str(result)
    assert "api_key" not in str(result)


def test_lock_contention_is_an_error_not_corruption(tmp_path):
    import threading

    from core.observations import store

    acquired = threading.Event()

    def holder():
        with store.repo_lock(tmp_path, "docker.io", "demo", "app", wait_seconds=30):
            acquired.set()
            import time

            time.sleep(0.5)

    thread = threading.Thread(target=holder)
    thread.start()
    assert acquired.wait(timeout=5)
    try:
        with pytest.raises(TimeoutError):
            with store.repo_lock(tmp_path, "docker.io", "demo", "app", wait_seconds=0.1):
                pass
    finally:
        thread.join()
    # Lock file is always released.
    assert not (tmp_path / "docker.io" / "demo" / "app" / ".lock").exists()


def test_rollback_missing_newest_file_refuses(tmp_path):
    from core.observations.store import list_observations
    from core.observations.sweep import sweep_catalog

    sweep_catalog(_catalog(), _probe(["latest", "1.0"]), store_root=tmp_path)
    sweep_catalog(_catalog(), _probe(["latest"]), store_root=tmp_path)
    files = list_observations("docker.io", "demo", "app", root=tmp_path)
    assert len(files) == 2
    files[-1].unlink()  # attacker deletes the newest observation
    rerun = sweep_catalog(_catalog(), _probe(["latest"]), store_root=tmp_path)
    assert rerun["changes"] == []
    assert any(e.get("integrity") == "BROKEN" for e in rerun["errors"])


def test_forked_history_refuses(tmp_path):
    import json

    from core.observations.store import list_observations
    from core.observations.sweep import sweep_catalog

    sweep_catalog(_catalog(), _probe(["latest", "1.0"]), store_root=tmp_path)
    files = list_observations("docker.io", "demo", "app", root=tmp_path)
    record = json.loads(files[0].read_text(encoding="utf-8"))
    # Attacker plants a sibling genesis: two records, same predecessor.
    files[0].with_name(files[0].name.replace(".json", "-fork.json")).write_text(
        json.dumps(record), encoding="utf-8"
    )
    rerun = sweep_catalog(_catalog(), _probe(["latest"]), store_root=tmp_path)
    assert rerun["changes"] == []
    assert any(e.get("integrity") == "BROKEN" for e in rerun["errors"])


def test_recomputed_content_hash_still_breaks_chain(tmp_path):
    import json

    from core.evidence.provenance import hash_content
    from core.observations.registry import _raw_body
    from core.observations.store import list_observations
    from core.observations.sweep import sweep_catalog

    sweep_catalog(_catalog(), _probe(["latest", "1.0"]), store_root=tmp_path)
    sweep_catalog(_catalog(), _probe(["latest"]), store_root=tmp_path)
    files = list_observations("docker.io", "demo", "app", root=tmp_path)
    record = json.loads(files[-1].read_text(encoding="utf-8"))
    # Sophisticated tamper: fix the body AND recompute content_hash, but
    # the chain digest (bound to the original observed_at) still breaks.
    record["tags"] = {"latest": ["sha256:EVIL"]}
    record["content_hash"] = hash_content(_raw_body(record))
    files[-1].write_text(json.dumps(record), encoding="utf-8")
    rerun = sweep_catalog(_catalog(), _probe(["latest"]), store_root=tmp_path)
    assert rerun["changes"] == []
    assert any(e.get("integrity") == "BROKEN" for e in rerun["errors"])


def test_oversized_probe_rejected_not_persisted(tmp_path):
    from core.observations.registry import MAX_OBSERVATION_TAGS
    from core.observations.store import list_observations
    from core.observations.sweep import sweep_catalog

    def huge(namespace, repo):
        return {
            "collector": "registries",
            "namespace": namespace,
            "repo": repo,
            "digests": {f"tag-{i}": ["sha256:x"] for i in range(MAX_OBSERVATION_TAGS + 1)},
        }

    result = sweep_catalog(_catalog(), huge, store_root=tmp_path)
    assert result["observations"] == []
    assert result["errors"]
    assert list_observations("docker.io", "demo", "app", root=tmp_path) == []

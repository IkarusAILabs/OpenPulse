"""Security golden suite — end-to-end trust-boundary proofs (A–R).

Every case runs offline. Each one answers: "what malicious or
corrupted input could make OpenPulse claim more than its evidence
supports?" — and proves it cannot.
"""

from datetime import datetime, timezone

import pytest

T1 = datetime(2026, 9, 1, tzinfo=timezone.utc)
T2 = datetime(2026, 9, 2, tzinfo=timezone.utc)
T3 = datetime(2026, 9, 3, tzinfo=timezone.utc)


def _obs(**kw):
    from core.observations.registry import RegistryObservation

    base = {
        "namespace": "bitnami",
        "repository": "redis",
        "observed_at": T1,
        "tags": {"latest": ["sha256:AAA"], "7.2.0": ["sha256:111"]},
    }
    base.update(kw)
    return RegistryObservation(**base).seal()


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


def _catalog():
    return [{"slug": "demo", "docker_images": ["docker.io/demo/app"]}]


def _event(**kw):
    from core.schema.models import OSSEvent

    base = {
        "id": "evt-1",
        "project_slug": "demo",
        "event_type": "DISTRIBUTION_CHANGE",
        "title": "t",
        "summary": "s",
        "confidence": "EMERGING",
        "impact": "REVIEW",
        "evidences": [
            {
                "source": {
                    "name": "docker-hub",
                    "url": "https://hub.docker.com/r/demo/app/tags",
                    "authority": "primary",
                    "fetched_at": "2026-09-02T00:00:00Z",
                },
                "excerpt": "tag disappeared",
                "relation": "supports",
            }
        ],
    }
    base.update(kw)
    return OSSEvent(**base)


# A. Valid registry observation chain ----------------------------------------


def test_a_valid_registry_observation_chain():
    from core.observations.registry import verify_registry_history

    first = _obs().link(None)
    second = _obs(observed_at=T2).link(first.model_dump(mode="json"))
    records = [first.model_dump(mode="json"), second.model_dump(mode="json")]
    assert verify_registry_history(records)["status"] == "VALID"
    assert second.previous_observation_hash == first.chain_hash
    assert second.first_detected_at == first.observed_at


# B. Tampered observation detected --------------------------------------------


def test_b_tampered_observation_detected():
    from core.observations.registry import verify_registry_history

    first = _obs().link(None)
    second = _obs(observed_at=T2).link(first.model_dump(mode="json"))
    tampered = second.model_dump(mode="json")
    tampered["tags"] = {"latest": ["sha256:EVIL"], "7.2.0": ["sha256:111"]}
    result = verify_registry_history([first.model_dump(mode="json"), tampered])
    assert result["status"] == "BROKEN"
    assert result["breaks"] == [1]


def test_b_tampered_timestamp_detected():
    from core.observations.registry import verify_registry_history

    first = _obs().link(None)
    second = _obs(observed_at=T2).link(first.model_dump(mode="json"))
    tampered = second.model_dump(mode="json")
    tampered["observed_at"] = "2026-01-01T00:00:00+00:00"  # backdate, hashes kept
    result = verify_registry_history([first.model_dump(mode="json"), tampered])
    assert result["status"] == "BROKEN"


# C. Missing observation history = baseline ----------------------------------


def test_c_missing_history_is_baseline(tmp_path):
    from core.observations.sweep import sweep_catalog

    result = sweep_catalog(_catalog(), _probe(["latest", "1.0"]), store_root=tmp_path)
    assert result["changes"] == []
    assert result["findings"] == []
    assert result["errors"] == []
    assert result["observations"][0]["previous_observation_hash"] == "genesis"


# D. Tag disappearance produces a candidate change ----------------------------


def test_d_tag_disappearance_produces_candidate_change(tmp_path):
    from core.observations.sweep import sweep_catalog

    sweep_catalog(_catalog(), _probe(["latest", "1.0"]), store_root=tmp_path)
    result = sweep_catalog(_catalog(), _probe(["latest"]), store_root=tmp_path)
    assert [c["type"] for c in result["changes"]] == ["tag_disappeared"]
    finding = result["findings"][0]
    assert finding["event_type"] == "DISTRIBUTION_CHANGE"
    assert finding["evidence_strength"] == "moderate"
    evidence = finding["observation_evidence"]
    assert evidence["fact"]["tag"] == "1.0"
    assert evidence["fact"]["previous_digests"] == ["sha256:1.0"]
    assert evidence["content_hash"] and evidence["chain_hash"]
    assert evidence["previous_content_hash"]
    assert evidence["source_url"].startswith("https://hub.docker.com/r/demo/app/tags")


# E. Candidate change without strong evidence cannot become ACTION_REQUIRED --


def test_e_weak_candidate_never_action_required():
    from core.risk.impact import evaluate_impact

    heuristic = {
        "analyst": "change",
        "event_type": "DISTRIBUTION_CHANGE",
        "signal": "distribution",
        "impact": "ACTION",
        "significance": "high",
        "detection_method": "namespace_heuristic",
        "evidence_strength": "weak",
        "distribution_model_change": True,
        "lifecycle_state": "EFFECTIVE",
        "scope": {"kind": "project", "versions": []},
    }
    context = {
        "verdict": "AFFECTS_VERSION",
        "affected": True,
        "confidence": "CORROBORATED",
        "reason": "pin matches",
    }
    out = evaluate_impact(heuristic, dependency_context=context)
    assert out["assessment"] != "ACTION_REQUIRED"
    assert out["eligibility"] == "REVIEW"


# F. Exact artifact match with weak event evidence remains weak --------------


def test_f_exact_match_weak_evidence_stays_weak():
    from core.risk.check import check_dependency

    event = _event(
        confidence="EMERGING",
        scope={"kind": "artifact", "artifacts": ["docker.io/demo/app:1.0"]},
        affected_artifacts=[{"kind": "docker-image", "ref": "docker.io/demo/app:1.0"}],
    )
    result = check_dependency({"kind": "image", "ref": "docker.io/demo/app:1.0"}, [event])
    assert (result.affected, result.relationship) == (True, "AFFECTS_ARTIFACT")
    assert result.match_strength == "exact"
    assert result.evidence_confidence == "EMERGING"
    assert result.confidence == "EMERGING"  # precise match, weak claim


# G. NOT_AFFECTED is semantically consistent ----------------------------------


def test_g_not_affected_is_consistent():
    from core.risk.check import check_dependency
    from core.risk.impact import evaluate_impact

    event = _event(
        confidence="CORROBORATED",
        scope={"kind": "artifact", "artifacts": ["docker.io/demo/app:1.0"]},
    )
    result = check_dependency({"kind": "image", "ref": "docker.io/demo/other:9.9"}, [event])
    assert result.relationship == "NOT_AFFECTED"
    assert result.affected is False
    out = evaluate_impact(
        {"analyst": "change"},
        dependency_context={
            "verdict": result.relationship,
            "affected": result.affected,
            "confidence": result.confidence,
            "reason": result.reason,
        },
    )
    assert out["assessment"] == "NOT_AFFECTED"
    assert out["eligibility"] == "INFORMATIONAL"


# H. UNKNOWN is not NOT_AFFECTED ----------------------------------------------


def test_h_unknown_is_not_not_affected():
    from core.risk.check import check_dependency

    result = check_dependency({"kind": "image", "ref": "docker.io/stranger/app:1.0"}, [_event()])
    assert result.relationship == "UNKNOWN"
    assert result.relationship != "NOT_AFFECTED"
    assert result.affected is False


# I. RELATED is not AFFECTED --------------------------------------------------


def test_i_related_is_not_affected():
    from core.risk.check import check_dependency

    event = _event(
        scope={"kind": "version", "versions": ["5.0"]},
        affected_versions=["5.0"],
    )
    result = check_dependency({"kind": "image", "ref": "docker.io/demo/app:latest"}, [event])
    assert result.relationship == "RELATED"
    assert result.affected is False


# J. Project match does not become customer impact ----------------------------


def test_j_project_match_never_customer_impact():
    from core.risk.check import check_dependency
    from core.risk.impact import evaluate_impact

    event = _event(confidence="CONFIRMED", scope={"kind": "project"})
    result = check_dependency(
        {"kind": "package", "package": "demo", "ecosystem": "PyPI", "version": "1.0"},
        [event],
    )
    assert result.relationship == "AFFECTS_PROJECT"
    out = evaluate_impact(
        {"analyst": "change"},
        dependency_context={
            "verdict": result.relationship,
            "affected": result.affected,
            "confidence": result.confidence,
            "reason": result.reason,
        },
    )
    assert out["assessment"] not in ("AFFECTS_DEPENDENCY", "ACTION_REQUIRED")


# K. Weak evidence never enters ACTION ----------------------------------------


def test_k_weak_evidence_never_action():
    from core.risk.impact import evaluate_impact

    finding = {
        "analyst": "change",
        "event_type": "DISTRIBUTION_CHANGE",
        "signal": "distribution",
        "impact": "ACTION",
        "significance": "high",
        "distribution_model_change": True,
        "evidence_strength": "weak",
        "lifecycle_state": "EFFECTIVE",
        "scope": {"kind": "project", "versions": []},
    }
    out = evaluate_impact(finding)
    assert out["eligibility"] == "REVIEW"


# L. Public ACTION framing never becomes ACTION_REQUIRED ----------------------


def test_l_public_action_framing_never_action_required():
    from core.risk.impact import evaluate_impact

    out = evaluate_impact(
        {
            "analyst": "change",
            "event_type": "EOL",
            "signal": "lifecycle",
            "impact": "ACTION",
            "lifecycle_state": "EFFECTIVE",
            "effective_at": "2026-09-01",
            "observed_at": "2026-09-26",
            "scope": {"kind": "version", "versions": ["5.0"]},
        }
    )
    assert out["eligibility"] == "ACTION"
    assert out["assessment"] == "PROJECT_CHANGE"
    assert out["assessment"] != "ACTION_REQUIRED"


# M+N. Webhook SSRF -----------------------------------------------------------


def _public_resolver(host):
    return ["93.184.216.34"]


def test_m_webhook_private_and_metadata_rejected():
    from core.notify import validate_webhook_url

    assert validate_webhook_url("https://hooks.example/x", resolver=_public_resolver)[0] is True
    for url in (
        "http://hooks.example/x",  # http needs opt-in
        "ftp://hooks.example/x",
        "https://127.0.0.1/x",
        "https://10.0.0.5/x",
        "https://192.168.1.1/x",
        "https://172.16.9.9/x",
        "https://169.254.169.254/x",
        "https://100.100.100.100/x",
        "https://0.0.0.0/x",
        "https://[::1]/x",
        "https://user:pass@hooks.example/x",
    ):
        ok, reason = validate_webhook_url(url, resolver=_public_resolver)
        assert ok is False, url
        assert reason, url


def test_m_webhook_resolved_private_rejected():
    from core.notify import validate_webhook_url

    ok, reason = validate_webhook_url(
        "https://hooks.example/x", resolver=lambda host: ["93.184.216.34", "10.1.2.3"]
    )
    assert ok is False
    assert "blocked" in reason


def test_n_webhook_redirect_never_followed():
    import httpx

    from core.notify import post_digest

    def redirect(request):
        return httpx.Response(
            302, headers={"location": "https://hooks.example/evil"}, request=request
        )

    result = post_digest(
        "https://hooks.example/x",
        "md",
        transport=httpx.MockTransport(redirect),
        resolver=lambda host: ["93.184.216.34"],
    )
    assert result["ok"] is False
    assert "redirect" in result["error"]


# O. Sealed observation mutation ----------------------------------------------


def test_o_sealed_observation_frozen():
    obs = _obs().link(None)
    with pytest.raises(Exception):
        obs.tags = {"latest": ["sha256:EVIL"]}  # type: ignore[assignment]
    with pytest.raises(Exception):
        obs.content_hash = "sha256:evil"  # type: ignore[assignment]
    # The sealed record still verifies after the failed mutations.
    assert obs.verify_record() == "VALID"


def test_o_mutated_dump_detected():
    from core.observations.registry import verify_registry_observation

    obs = _obs().link(None)
    dumped = obs.model_dump(mode="json")
    dumped["tags"]["latest"] = ["sha256:EVIL"]
    assert verify_registry_observation(dumped, None) == "BROKEN"


# P. Concurrent sweep cannot corrupt history ----------------------------------


def test_p_concurrent_sweeps_keep_valid_chain(tmp_path):
    import threading

    from core.observations.chain import order_history
    from core.observations.registry import verify_registry_history
    from core.observations.store import load_all
    from core.observations.sweep import sweep_catalog

    errors: list = []

    def run():
        try:
            result = sweep_catalog(_catalog(), _probe(["latest", "1.0"]), store_root=tmp_path)
            errors.extend(result["errors"])
        except Exception as exc:  # noqa: BLE001 — the test must see it
            errors.append(exc)

    threads = [threading.Thread(target=run) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    records = load_all("docker.io", "demo", "app", root=tmp_path)
    assert len(records) >= 1
    # Filename order is NOT chain order under concurrency — verify in
    # chain order (the same ordering the sweep itself uses).
    ordered, chain_ok = order_history(records)
    assert chain_ok
    assert verify_registry_history(ordered)["status"] == "VALID"


# Q. First detection stable across later observations -------------------------


def test_q_first_detection_stable(tmp_path):
    from core.observations.sweep import sweep_catalog

    sweep_catalog(_catalog(), _probe(["latest"]), store_root=tmp_path, observed_at=T1)
    run2 = sweep_catalog(
        _catalog(), _probe(["latest", "1.0"]), store_root=tmp_path, observed_at=T2
    )
    run3 = sweep_catalog(
        _catalog(), _probe(["latest", "1.0"]), store_root=tmp_path, observed_at=T3
    )
    # Steady state: no new change, no new finding — but the recorded
    # first detection of the T2 appearance must not drift.
    assert run2["findings"][0]["first_detected_at"] is not None
    assert str(run2["findings"][0]["first_detected_at"])[:10] == "2026-09-02"
    assert run3["changes"] == []


def test_q_reappeared_tag_starts_new_episode(tmp_path):
    from core.observations.sweep import sweep_catalog

    sweep_catalog(_catalog(), _probe(["latest"]), store_root=tmp_path, observed_at=T1)
    run2 = sweep_catalog(
        _catalog(), _probe(["latest", "1.0"]), store_root=tmp_path, observed_at=T2
    )
    run3 = sweep_catalog(_catalog(), _probe(["latest"]), store_root=tmp_path, observed_at=T3)
    assert str(run3["findings"][0]["first_detected_at"])[:10] == "2026-09-03"
    t4 = datetime(2026, 9, 4, tzinfo=timezone.utc)
    run4 = sweep_catalog(
        _catalog(), _probe(["latest", "1.0"]), store_root=tmp_path, observed_at=t4
    )
    # Re-appearance is a NEW episode: first detection is T4, not T2.
    assert str(run4["findings"][0]["first_detected_at"])[:10] == "2026-09-04"
    assert str(run2["findings"][0]["first_detected_at"])[:10] == "2026-09-02"


# S. Deterministic serialization golden ----------------------------------------


def test_s_chain_hash_deterministic_golden():
    """Canonical evidence serialization is byte-stable: the same
    observation always seals to the same hashes (reproducibility
    check for the whole integrity model)."""
    from core.observations.registry import RegistryObservation

    obs = (
        RegistryObservation(
            namespace="demo",
            repository="app",
            observed_at=T1,
            tags={"latest": ["sha256:AAA"]},
        )
        .seal()
        .link(None)
    )
    dumped = obs.model_dump(mode="json")
    assert dumped["content_hash"] == (
        "sha256:b086f50a28f0a03bc3c043203e437da6fc7334bbbeb626a0a16f5e8076185e86"
    )
    assert dumped["chain_hash"] == (
        "sha256:ce055409a073e7e47ab9a6f296e3194d02ae0803053e2159b8563baf4bff2c12"
    )
    assert dumped["observation_id"] == "docker-hub:docker.io/demo/app:b086f50a28f0"


# T. Heuristic identity mappings cap strong conclusions ------------------------


def test_t_namespace_rule_mapping_caps_confidence():
    from core.entities.identity import REVIEW_REQUIRED, resolution_trust
    from core.risk.check import check_dependency

    trust = resolution_trust("bitnami/postgresql")
    assert trust["via"] == "namespace_rule"
    assert trust["identity_status"] == REVIEW_REQUIRED
    event = _event(
        project_slug="bitnami-postgresql",
        confidence="CONFIRMED",
        impact="ACTION",
        scope={"kind": "version", "versions": ["16"]},
        affected_versions=["16"],
    )
    result = check_dependency(
        {"kind": "package", "package": "bitnami/postgresql", "version": "16"},
        [event],
    )
    assert (result.affected, result.relationship) == (True, "AFFECTS_VERSION")
    assert result.confidence == "EMERGING"  # capped: heuristic identity
    assert "identity" in result.reason


def test_t_heuristic_distribution_finding_capped_at_review():
    from analyzers.change_analyst import analyze_registries
    from core.risk.impact import evaluate_impact

    findings = analyze_registries(
        [
            {
                "collector": "registries",
                "repo": "redis",
                "namespace": "bitnami",
                "latest_only": True,
                "has_versioned_tags": False,
            },
            {
                "collector": "registries",
                "repo": "redis",
                "namespace": "bitnamilegacy",
                "latest_only": False,
                "has_versioned_tags": True,
            },
        ]
    )
    heuristic = next(f for f in findings if f.get("distribution_model_change"))
    assert heuristic["impact"] == "ACTION"  # analyst proposal is unchanged
    assert heuristic["evidence_strength"] == "weak"
    out = evaluate_impact(heuristic)
    assert out["eligibility"] == "REVIEW"  # heuristic never action-framed


# R. Independent source families counted correctly ----------------------------


def test_r_source_families_counted_not_labels():
    from core.risk.metrics import finding_source_distribution

    out = finding_source_distribution(
        [
            {"analyst": "security", "sources": ["nvd", "osv"]},  # one family
            {"analyst": "change", "sources": ["endoflife", "github"]},  # two families
            {"analyst": "change", "sources": ["change"]},  # derived only
        ]
    )
    assert out["source_count"] == 5
    assert out["source_family_count"] == 3  # vuln-data, lifecycle-data, upstream-vcs
    assert out["corroborating_family_count"] == 1

"""Catalog sweep tests: fully offline via injected probe functions."""


def _catalog():
    return [
        {"slug": "demo", "docker_images": ["docker.io/demo/app"]},
        {"slug": "bare", "docker_images": ["docker.io/bare"]},
    ]


def _probe(tags):
    def run(namespace, repo):
        assert (namespace, repo) == ("demo", "app")
        return {
            "collector": "registries",
            "registry": "docker.io",
            "namespace": namespace,
            "repo": repo,
            "tags_sample": list(tags),
            "digests": {tag: [f"sha256:{tag}"] for tag in tags},
            "count": len(tags),
            "has_versioned_tags": any(t != "latest" for t in tags),
            "latest_only": bool(tags) and all(t == "latest" for t in tags),
        }

    return run


def test_sweep_targets_skip_bare_namespaces():
    from core.observations.sweep import sweep_targets

    assert sweep_targets(_catalog()) == [("demo", "demo", "app")]


def test_first_run_is_baseline(tmp_path):
    from core.observations.sweep import sweep_catalog

    result = sweep_catalog(_catalog(), _probe(["latest", "1.0"]), store_root=tmp_path)
    assert len(result["observations"]) == 1
    assert result["changes"] == []
    assert result["findings"] == []
    assert result["errors"] == []


def test_second_run_detects_disappearance(tmp_path):
    from core.observations.sweep import sweep_catalog

    sweep_catalog(_catalog(), _probe(["latest", "1.0"]), store_root=tmp_path)
    result = sweep_catalog(_catalog(), _probe(["latest"]), store_root=tmp_path)
    assert [c["type"] for c in result["changes"]] == ["tag_disappeared"]
    assert result["findings"][0]["event_type"] == "DISTRIBUTION_CHANGE"


def test_errors_recorded_not_raised(tmp_path):
    from core.observations.sweep import sweep_catalog

    def boom(namespace, repo):
        raise RuntimeError("network down")

    try:
        result = sweep_catalog(_catalog(), boom, store_root=tmp_path)
    except RuntimeError:
        raise AssertionError("sweep must not raise on probe failure")
    assert len(result["errors"]) == 1
    assert result["errors"][0]["slug"] == "demo"
    assert result["observations"] == []


def test_parser_change_rebaselines_instead_of_diffing(tmp_path):
    """A stored history from older probe semantics is a new baseline,
    not a diff source: windowed tag samples must never diff against
    full tag sets."""
    from core.observations.registry import RegistryObservation
    from core.observations.store import load_all, save_observation
    from core.observations.sweep import observe_repository

    legacy = (
        RegistryObservation(
            namespace="demo",
            repository="app",
            tags={"latest": ["sha256:latest"], "1.0": ["sha256:1.0"]},
            parser_version="openpulse-parsers/0.4.0",
        )
        .seal()
        .link(None)
    )
    save_observation(legacy.model_dump(mode="json"), root=tmp_path)
    probe = {
        "collector": "registries",
        "registry": "docker.io",
        "namespace": "demo",
        "repo": "app",
        "digests": {"latest": ["sha256:latest"], "1.0": ["sha256:1.0"]},
        "count": 2,
    }
    result = observe_repository("docker.io", "demo", "app", probe, store_root=tmp_path)
    assert result["error"] is None
    assert result["history_status"] == "REBASELINED"
    assert result["changes"] == []
    # Chain continues (linked), history stays verifiable.
    from core.observations.registry import verify_registry_history

    history = load_all("docker.io", "demo", "app", root=tmp_path)
    assert verify_registry_history(history)["status"] == "VALID"

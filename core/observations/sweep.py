"""Catalog sweep — distribution discovery across every known image.

`sweep_catalog` takes an injected `probe_fn(namespace, repo)` so the
whole flow is testable offline; the CLI passes the live Docker Hub
probe. Each image: probe → sealed observation → saved → diffed against
history → distribution findings. First sightings are baselines and
produce no findings; errors are recorded per repo, never raised.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from analyzers.change_analyst import analyze_diffs
from core.observations.registry import RegistryObservation, diff_observations, to_observation
from core.observations.store import load_previous, save_observation
from core.risk.match import split_image_ref


def sweep_targets(catalog: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    """(slug, namespace, repo) for every probeable catalog image.

    Only registry/namespace/repo triples probe cleanly; bare namespace
    refs are skipped (they name a catalogue, not an image).
    """
    targets = []
    for entry in catalog:
        for image in entry.get("docker_images") or []:
            registry, namespace, name = split_image_ref(str(image))
            if "/" in str(image) and namespace not in ("docker.io", "") and name:
                targets.append((str(entry.get("slug", "")), namespace, name))
    return targets


def sweep_catalog(
    catalog: list[dict[str, Any]],
    probe_fn: Callable[[str, str], dict[str, Any]],
    store_root: str = ".openpulse/observations",
    slugs: list[str] | None = None,
    observed_at: datetime | None = None,
) -> dict[str, Any]:
    """Probe, persist, diff, and analyse. Returns observations/changes/findings/errors."""
    now = observed_at or datetime.now(timezone.utc)
    observations: list[dict[str, Any]] = []
    changes: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for slug, namespace, repo in sweep_targets(catalog):
        if slugs and slug not in slugs:
            continue
        try:
            probe = probe_fn(namespace, repo)
        except Exception as exc:  # custom probes may raise; record, never crash
            errors.append(
                {
                    "collector": "registries",
                    "namespace": namespace,
                    "repo": repo,
                    "slug": slug,
                    "error": True,
                    "category": "unknown",
                    "retryable": False,
                    "status_code": None,
                    "safe_message": f"{type(exc).__name__}: {str(exc)[:200]}",
                }
            )
            continue
        if probe.get("error"):
            errors.append({**probe, "slug": slug})
            continue
        current = to_observation(probe, observed_at=now)
        previous_raw = load_previous(current.registry, namespace, repo, root=store_root)
        previous = RegistryObservation(**previous_raw) if previous_raw else None
        fresh = diff_observations(previous, current)
        save_observation(current.model_dump(mode="json"), root=store_root)
        observations.append(current.model_dump(mode="json"))
        changes += [c.model_dump(mode="json") for c in fresh]
    findings = analyze_diffs(changes)
    return {
        "observations": observations,
        "changes": changes,
        "findings": findings,
        "errors": errors,
    }

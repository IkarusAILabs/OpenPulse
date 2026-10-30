# ruff: noqa: E501
"""Discovery for the retrospective study (DESIGN.md §8, RQ-R3).

Runs OpenPulse's live collectors and change analyst for every relocation,
archival and distribution event, on one recorded date. It is meant to run
in CI at the freeze tag, with the job's read-only GITHUB_TOKEN:

    python evaluation/retrospective/discovery.py --out discovery.json

Each event is run twice:

- ``as_shipped``: the catalog lookup OpenPulse itself performs
  (``cli.main._live_bundle``). An uncatalogued project yields no input.
- ``supplied``: the affected repository or Docker Hub image is handed to the
  same collectors directly, which measures the analysts apart from catalog
  coverage.

The script records what the analysts return. It does not compare the
constructed scope with the fixture's scope: REPORT.md does that by hand.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from analyzers import change_analyst  # noqa: E402
from collectors.github.collector import GitHubCollector  # noqa: E402
from collectors.registries.docker import RegistryCollector  # noqa: E402
from core.entities.catalog import load_catalog  # noqa: E402

#: event -> (project slug, GitHub repository or None, Docker Hub image or None,
#: or a note when no collector covers the affected thing).
TARGETS = {
    "REL-1": ("moby", "docker/docker", None),
    "REL-3": ("distribution", "docker/distribution", None),
    "REL-4": ("prometheus-operator", "coreos/prometheus-operator", None),
    "DEP-1": ("request", "request/request", None),
    "DEP-2": ("dep", "golang/dep", None),
    "DEP-3": ("tslint", "palantir/tslint", None),
    "DEP-4": ("node-sass", "sass/node-sass", None),
    "DEP-5": ("go-yaml", "go-yaml/yaml", None),
    "DEP-6": ("golint", "golang/lint", None),
    "DIS-1": ("kubernetes", None, "no collector for k8s.gcr.io (Docker Hub only)"),
    "DIS-2": ("openjdk", None, ("library", "openjdk")),
    "DIS-3": ("openjdk", None, ("library", "openjdk")),
    "DIS-4": ("centos", None, ("library", "centos")),
    "DIS-5": ("adoptopenjdk", None, ("library", "adoptopenjdk")),
    "DIS-6": ("java", None, ("library", "java")),
}


def _summary(findings: list[dict]) -> list[dict]:
    keep = ("event_type", "title", "impact", "scope", "affected_versions", "affected_artifacts")
    return [{k: f.get(k) for k in keep} for f in findings]


def _shipped(slug: str) -> dict:
    from cli.main import _live_bundle

    catalogued = any(e.get("slug") == slug for e in load_catalog())
    if not catalogued:
        return {"catalogued": False, "findings": []}
    raw = _live_bundle(slug)
    return {"catalogued": True, "findings": _summary(change_analyst.analyze(raw)), "raw": raw}


def _supplied(slug: str, repo: str | None, image) -> dict:
    raw: dict[str, list] = {}
    if repo:
        gh = GitHubCollector({slug: repo}, token=os.environ.get("GITHUB_TOKEN"))
        raw["github"] = gh.collect(slug)
        raw["github_meta"] = [gh.fetch_repo_meta(slug)]
    if isinstance(image, tuple):
        raw["registries"] = [RegistryCollector().check_image(*image)]
    if not raw:
        return {"input": None, "note": image, "findings": []}
    return {"input": repo or "/".join(image), "findings": _summary(change_analyst.analyze(raw)), "raw": raw}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    results = {}
    for event, (slug, repo, image) in TARGETS.items():
        results[event] = {"project": slug, "as_shipped": _shipped(slug), "supplied": _supplied(slug, repo, image)}
        found = [f["event_type"] for f in results[event]["supplied"]["findings"]]
        print(f"{event}: catalogued={results[event]['as_shipped']['catalogued']} as_shipped={len(results[event]['as_shipped']['findings'])} supplied={found}")
    out = {"recorded_at": started, "token": bool(os.environ.get("GITHUB_TOKEN")), "events": results}
    args.out.write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

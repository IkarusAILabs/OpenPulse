"""Cost measurements for TR-2026-01 (Section 10, "Cost and scale").

Run from the repository root:

    python benchmarks/cost.py            # offline: matching and history growth
    python benchmarks/cost.py --live     # also live acquisition, cold vs warm

Results are written to ``benchmarks/results/cost.json`` with the machine
and Python version. Offline parts use synthetic inventories and events
with the production engine (``check_watchlist``) and the production
observation store (``sweep_catalog``); the live part calls the public
APIs through the agent interface and counts every HTTP request.
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import tempfile
import time
import tracemalloc
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.risk.check import check_watchlist  # noqa: E402
from core.schema.models import Evidence, OSSEvent, Scope, Source  # noqa: E402

FETCHED = datetime(2026, 10, 28, tzinfo=timezone.utc)
SOURCE = Source(
    name="bench/source", url="https://example.org/b", authority="official", fetched_at=FETCHED
)


def _event(i: int, scope_size: int) -> OSSEvent:
    """An artifact-scoped event naming ``scope_size`` repositories."""
    artifacts = [f"docker.io/ns{i}/app{j}" for j in range(scope_size)]
    return OSSEvent(
        id=f"bench-{i}",
        project_slug=f"proj{i}",
        event_type="DISTRIBUTION_CHANGE",
        title="b",
        summary="b",
        confidence="CONFIRMED",
        impact="ACTION",
        evidences=[Evidence(source=SOURCE, excerpt="b")],
        scope=Scope(kind="artifact", artifacts=artifacts, exhaustive=True, basis="announced"),
    )


def _version_event(i: int) -> OSSEvent:
    return OSSEvent(
        id=f"bench-eol-{i}",
        project_slug="redis",
        event_type="EOL",
        title="b",
        summary="b",
        confidence="CONFIRMED",
        impact="ACTION",
        evidences=[Evidence(source=SOURCE, excerpt="b")],
        scope=Scope(kind="version", versions=[f"{i}.0"], exhaustive=True, basis="definitional"),
    )


def _inventory(n: int) -> list[dict]:
    """Half images (some inside event scopes), half packages."""
    deps: list[dict] = []
    for k in range(n):
        if k % 2 == 0:
            deps.append({"kind": "image", "ref": f"docker.io/ns{k % 7}/app{k % 11}:{k % 5}.0"})
        else:
            deps.append(
                {"kind": "package", "package": f"pkg{k}", "ecosystem": "PyPI", "version": "1.0"}
            )
    return deps


def _timed(deps: list[dict], events: list[OSSEvent], repeats: int = 3) -> dict:
    runs = []
    for _ in range(repeats):
        start = time.perf_counter()
        check_watchlist(deps, events)
        runs.append(time.perf_counter() - start)
    seconds = statistics.median(runs)
    pairs = len(deps) * len(events)
    return {
        "dependencies": len(deps),
        "events": len(events),
        "pairs": pairs,
        "seconds": round(seconds, 4),
        "microseconds_per_pair": round(seconds / pairs * 1e6, 1) if pairs else None,
    }


def matching() -> dict:
    scope = 5
    by_inventory = [
        _timed(_inventory(n), [_event(i, scope) for i in range(10)]) for n in (10, 100, 1000, 5000)
    ]
    by_events = [
        _timed(_inventory(1000), [_event(i, scope) for i in range(e)]) for e in (1, 10, 100)
    ]
    by_scope = [
        {"scope_size": k, **_timed(_inventory(1000), [_event(0, k)])} for k in (1, 10, 100, 1000)
    ]
    mixed = _timed(_inventory(1000), [_event(i, scope) for i in range(5)] + [_version_event(7)])
    tracemalloc.start()
    check_watchlist(_inventory(5000), [_event(i, scope) for i in range(10)])
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "by_inventory_size": by_inventory,
        "by_event_count": by_events,
        "by_scope_size": by_scope,
        "mixed_with_version_scope": mixed,
        "peak_memory_mib_5000x10": round(peak / 2**20, 1),
    }


def _probe(tags_by_repo: dict[tuple[str, str], list[str]]):
    def run(namespace: str, repo: str) -> dict:
        tags = tags_by_repo[(namespace, repo)]
        return {
            "collector": "registries",
            "registry": "docker.io",
            "namespace": namespace,
            "repo": repo,
            "tags_sample": list(tags),
            "digests": {t: [f"sha256:{abs(hash((repo, t))):064x}"[-71:]] for t in tags},
            "count": len(tags),
            "has_versioned_tags": any(t != "latest" for t in tags),
            "latest_only": bool(tags) and all(t == "latest" for t in tags),
        }

    return run


def _store_bytes(root: Path) -> int:
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())


def history(repos: int = 50, tags: int = 50, runs: int = 20) -> dict:
    from core.observations.sweep import sweep_catalog

    catalog = [{"slug": f"s{i}", "docker_images": [f"docker.io/ns{i}/app"]} for i in range(repos)]
    out = {}
    for mode in ("steady", "one_new_tag_per_run"):
        tags_by_repo = {
            (f"ns{i}", "app"): ["latest"] + [f"1.{t}" for t in range(tags)] for i in range(repos)
        }
        with tempfile.TemporaryDirectory() as tmp:
            series = []
            for run in range(runs):
                if mode == "one_new_tag_per_run" and run:
                    for key in tags_by_repo:
                        tags_by_repo[key].append(f"2.{run}")
                start = time.perf_counter()
                result = sweep_catalog(
                    catalog,
                    _probe(tags_by_repo),
                    store_root=tmp,
                    observed_at=FETCHED + timedelta(days=run),
                )
                series.append(
                    {
                        "run": run + 1,
                        "seconds": round(time.perf_counter() - start, 3),
                        "store_bytes": _store_bytes(Path(tmp)),
                        "changes": len(result["changes"]),
                        "errors": len(result["errors"]),
                    }
                )
            out[mode] = series
    return {"repositories": repos, "tags_per_repository": tags, "runs": runs, **out}


def live(slugs: list[str]) -> dict:
    import httpx

    from core.agent_tools import Lookups, dependency_status, live_fetcher

    counter = {"requests": 0, "statuses": {}}
    original = httpx.Client.send

    def counting_send(self, request, *args, **kwargs):
        counter["requests"] += 1
        response = original(self, request, *args, **kwargs)
        key = str(response.status_code)
        counter["statuses"][key] = counter["statuses"].get(key, 0) + 1
        return response

    httpx.Client.send = counting_send
    try:
        lookups = Lookups(fetch=live_fetcher())
        rows = []
        for slug in slugs:
            for phase in ("cold", "warm"):
                before = counter["requests"]
                start = time.perf_counter()
                out = dependency_status(package=slug, ecosystem="PyPI", lookups=lookups)
                rows.append(
                    {
                        "package": slug,
                        "phase": phase,
                        "seconds": round(time.perf_counter() - start, 3),
                        "http_requests": counter["requests"] - before,
                        "sources": {s["source"]: s["status"] for s in out.get("sources", [])},
                    }
                )
    finally:
        httpx.Client.send = original
    return {"rows": rows, "http_statuses": counter["statuses"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="also measure live acquisition")
    args = parser.parse_args()
    result = {
        "machine": {
            "python": platform.python_version(),
            "system": platform.platform(),
            "processor": platform.processor(),
        },
        "measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "matching": matching(),
        "history": history(),
    }
    if args.live:
        result["live"] = live(["django", "redis", "flask", "celery", "requests"])
    out = ROOT / "benchmarks" / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "cost.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()

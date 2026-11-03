"""The track T study, Part A: star-history indicators (protocol item TR4 onward).

Run from the repository root, offline:

    python benchmarks/track_t_study.py calibrate

``docs/research/TRACK_T_STUDY_PROTOCOL.md`` defines the indicators (§3), the
split and the calibration (§5). This script implements them:

- **SH1** peak week share, **SH2** four-week concentration and **SH3** daily
  spike, computed from a recorded weekly star history
  (``record_star_history.py``); each needs at least ``MIN_STARS`` stars and a
  complete history (status 200), else the repository is not eligible.
- **Split.** Each organic set is split 50/50 by name with the protocol seed,
  before any value is computed; the split depends on names only.
- **Calibration.** On the calibration half only, each threshold is the
  (k+1)-th largest eligible value, k = floor(1% of eligible), and an
  indicator fires when a value is strictly above it, so at most 1% of the
  calibration half fires.

``calibrate`` never computes a value for a held-out repository or a positive;
it writes the split (names only) and the thresholds to
``benchmarks/fixtures/reputation/star-calibration-<date>.json``.

Two more commands (protocol §4, §6, items TR6):

    python benchmarks/track_t_study.py frame --osv DIR
    GITHUB_TOKEN=... python benchmarks/track_t_study.py run --registered ID

- ``frame`` pins Q-B's sampling frame from every package named by a
  ``MAL-`` record in OSV's ``npm/all.zip`` and ``PyPI/all.zip`` (withdrawn
  records excluded; names only): per ecosystem, a fixed-seed sample of
  ``LOOKALIKE_SAMPLE`` names for ``lookalike`` and one of
  ``MALICIOUS_SAMPLE`` for the registry recording, with the archive's
  SHA-256 and counts. No indicator is computed.
- ``run`` is the study's one run. It refuses until the protocol names the
  registration ``ID`` and no field is left "to fill at archiving", and it
  refuses a second time once results exist (§7). It reads the held-out
  organic half and the positives, runs ``lookalike`` on the frame, records
  registry metadata for the malicious sample and the young set's packages,
  and writes aggregates only: no positive is ever named.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FIXTURES = ROOT / "benchmarks" / "fixtures" / "reputation"
LOCAL = FIXTURES / "local"
PROTOCOL = ROOT / "docs" / "research" / "TRACK_T_STUDY_PROTOCOL.md"
CALIBRATION = "star-calibration-2026-11-03.json"
POSITIVES = "stars-positives-2026-11-03.json"
ORGANIC_PACKAGES = "organic-2026-11-02.json"
RESULTS = ROOT / "benchmarks" / "results" / "track-t-part-a.json"
REPORT = ROOT / "docs" / "research" / "TRACK_T_PART_A_RESULTS.md"
UNFILLED = "**to fill at archiving**"  # the marker in the protocol's table
MALICIOUS_SAMPLE = 500
LOOKALIKE_SAMPLE = 5000  # lookalike takes ~70 ms per npm name; 222k names would take hours
Z95 = 1.959963984540054
SETS = {"organic": "stars-organic-2026-11-03.json", "young": "stars-young-2026-11-03.json"}
SEED = 20261103
MIN_STARS = 50
FALSE_POSITIVE_CAP = 0.01
WEEK = 7 * 86400
DAY = 86400
PRIOR_DAYS = 56  # the 8 weeks before the busiest day
INDICATORS = ("SH1", "SH2", "SH3")


# ---------------------------------------------------------------------------
# Indicators (protocol §3)
# ---------------------------------------------------------------------------


def daily(weeks: list[list[int]]) -> dict[int, int]:
    """{day (epoch seconds): stars} for the days with stars."""
    out: dict[int, int] = {}
    for week, *days in weeks:
        for offset, count in enumerate(days):
            if count:
                out[week + offset * DAY] = out.get(week + offset * DAY, 0) + count
    return out


def indicators(history: dict[str, Any]) -> dict[str, float] | None:
    """SH1-SH3 for an eligible history, else None."""
    if history.get("status") != 200:
        return None
    weeks = sorted(history.get("weeks") or [])
    totals = {w[0]: sum(w[1:]) for w in weeks}
    stars = sum(totals.values())
    if stars < MIN_STARS:
        return None
    sh1 = max(totals.values()) / stars
    sh2 = max(sum(totals.get(start + i * WEEK, 0) for i in range(4)) for start in totals) / stars
    days = daily(weeks)
    busiest = min(days, key=lambda d: (-days[d], d))  # ties: the earliest day
    prior = [days.get(busiest - i * DAY, 0) for i in range(1, PRIOR_DAYS + 1)]
    sh3 = days[busiest] / max(statistics.median(prior), 1)
    return {"SH1": sh1, "SH2": sh2, "SH3": sh3}


# ---------------------------------------------------------------------------
# Split and calibration (protocol §5)
# ---------------------------------------------------------------------------


def split(names: list[str], seed: int = SEED) -> tuple[list[str], list[str]]:
    """(calibration, held-out): half of the names (rounded down) by the seed."""
    ordered = sorted(names, key=str.lower)
    chosen = set(random.Random(seed).sample(ordered, len(ordered) // 2))
    return [n for n in ordered if n in chosen], [n for n in ordered if n not in chosen]


def threshold(values: list[float], cap: float = FALSE_POSITIVE_CAP) -> dict[str, Any]:
    """The smallest observed value that at most ``cap`` of ``values`` exceed."""
    ordered = sorted(values, reverse=True)
    allowed = math.floor(cap * len(ordered))
    value = ordered[allowed]
    return {
        "threshold": value,
        "eligible": len(ordered),
        "allowed_to_fire": allowed,
        "fire": sum(1 for v in ordered if v > value),
    }


def load(filename: str) -> tuple[dict[str, Any], str]:
    path = FIXTURES / filename
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def calibrate(sets: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Split every set, then compute thresholds on the pooled calibration halves."""
    halves: dict[str, dict[str, list[str]]] = {}
    pooled: dict[str, list[float]] = {name: [] for name in INDICATORS}
    ineligible: dict[str, int] = {}
    for label, doc in sets.items():
        calibration, held_out = split(list(doc["repositories"]))
        halves[label] = {"calibration": calibration, "held_out": held_out}
        ineligible[label] = 0
        for repo in calibration:  # never a held-out repository
            values = indicators(doc["repositories"][repo])
            if values is None:
                ineligible[label] += 1
                continue
            for name in INDICATORS:
                pooled[name].append(values[name])
    return {
        "split": halves,
        "calibration_ineligible": ineligible,
        "thresholds": {name: threshold(pooled[name]) for name in INDICATORS},
    }


# ---------------------------------------------------------------------------
# Intervals (protocol §6)
# ---------------------------------------------------------------------------


def wilson(k: int, n: int) -> dict[str, Any]:
    """Rate with its 95% Wilson score interval; None values without data."""
    if not n:
        return {"k": k, "n": n, "rate": None, "low": None, "high": None}
    p = k / n
    centre = (p + Z95**2 / (2 * n)) / (1 + Z95**2 / n)
    half = Z95 * math.sqrt(p * (1 - p) / n + Z95**2 / (4 * n * n)) / (1 + Z95**2 / n)
    return {
        "k": k,
        "n": n,
        "rate": p,
        "low": max(0.0, centre - half),
        "high": min(1.0, centre + half),
    }


def difference(k1: int, n1: int, k2: int, n2: int) -> dict[str, Any]:
    """p1 - p2 with Newcombe's hybrid score 95% interval (method 10)."""
    a, b = wilson(k1, n1), wilson(k2, n2)
    if a["rate"] is None or b["rate"] is None:
        return {"difference": None, "low": None, "high": None}
    d = a["rate"] - b["rate"]
    low = d - math.sqrt((a["rate"] - a["low"]) ** 2 + (b["high"] - b["rate"]) ** 2)
    high = d + math.sqrt((a["high"] - a["rate"]) ** 2 + (b["rate"] - b["low"]) ** 2)
    return {"difference": d, "low": low, "high": high}


# ---------------------------------------------------------------------------
# Q-B's frame (protocol §4)
# ---------------------------------------------------------------------------


def malicious_names(archive: Path, ecosystem: str) -> tuple[list[str], int]:
    """(unique package names, MAL- records read) from one OSV ``all.zip``."""
    names: set[str] = set()
    records = 0
    with zipfile.ZipFile(archive) as z:
        for member in z.namelist():
            if not member.startswith("MAL-") or not member.endswith(".json"):
                continue
            try:
                doc = json.loads(z.read(member))
            except (ValueError, UnicodeDecodeError):
                continue
            if not isinstance(doc, dict) or doc.get("withdrawn"):
                continue
            records += 1
            for affected in doc.get("affected") or []:
                package = affected.get("package") if isinstance(affected, dict) else None
                if isinstance(package, dict) and package.get("ecosystem") == ecosystem:
                    name = package.get("name")
                    if isinstance(name, str) and name:
                        names.add(name)
    return sorted(names), records


def frame(
    archives: dict[str, Path], size: int = MALICIOUS_SAMPLE, lookalike: int = LOOKALIKE_SAMPLE
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for ecosystem, archive in archives.items():
        names, records = malicious_names(archive, ecosystem)

        def pick(n: int, names: list[str] = names) -> list[str]:
            return sorted(random.Random(SEED).sample(names, min(n, len(names))))

        out[ecosystem] = {
            "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "records": records,
            "names": len(names),
            "lookalike_sample": pick(lookalike),
            "sample": pick(size),
        }
    return out


# ---------------------------------------------------------------------------
# The run (protocol §4-§7, item TR6)
# ---------------------------------------------------------------------------


def registered(protocol_text: str, registration: str) -> str | None:
    """Why the run may not start yet, or None when the protocol is archived."""
    if UNFILLED in protocol_text:
        return f"the protocol still has fields marked '{UNFILLED}'"
    if not registration or registration not in protocol_text:
        return "the protocol does not name this registration"
    return None


def _fires(values: dict[str, float] | None, thresholds: dict[str, Any]) -> dict[str, bool] | None:
    if values is None:
        return None
    return {name: values[name] > thresholds[name]["threshold"] for name in INDICATORS}


def _rates(rows: list[dict[str, bool] | None]) -> dict[str, Any]:
    eligible = [r for r in rows if r is not None]
    return {
        "recorded": len(rows),
        "eligible": len(eligible),
        "unresolved": len(rows) - len(eligible),
        **{name: wilson(sum(r[name] for r in eligible), len(eligible)) for name in INDICATORS},
    }


def star_results(
    calibration: dict[str, Any], sets: dict[str, dict[str, Any]], positives: dict[str, Any]
) -> dict[str, Any]:
    """H-A1 and H-A2: held-out organic false positives, and agreement with
    StarScout per method. Aggregates only."""
    thresholds = calibration["thresholds"]
    held: dict[str, list[dict[str, bool] | None]] = {}
    for label, doc in sets.items():
        names = calibration["split"][label]["held_out"]
        held[label] = [_fires(indicators(doc["repositories"][n]), thresholds) for n in names]
    organic = {
        "pooled": _rates([r for rows in held.values() for r in rows]),
        **{label: _rates(rows) for label, rows in held.items()},
    }
    groups: dict[str, list[dict[str, bool] | None]] = {
        "all": [],
        "clustered": [],
        "low_activity": [],
        "low_activity_only": [],
    }
    for history in positives["repositories"].values():
        row = _fires(indicators(history), thresholds)
        methods = history.get("starscout") or []
        groups["all"].append(row)
        for method in ("clustered", "low_activity"):
            if method in methods:
                groups[method].append(row)
        if methods == ["low_activity"]:
            groups["low_activity_only"].append(row)
    flagged = {group: _rates(rows) for group, rows in groups.items()}
    pooled = organic["pooled"]
    hypotheses = {
        name: {
            "H-A1": flagged["all"][name]["rate"] is not None
            and flagged["all"][name]["rate"] >= 0.5,
            "H-A2": pooled[name]["rate"] is not None and pooled[name]["rate"] <= FALSE_POSITIVE_CAP,
        }
        for name in INDICATORS
    }
    return {
        "thresholds": {name: thresholds[name]["threshold"] for name in INDICATORS},
        "organic_held_out": organic,
        "positives": flagged,
        "hypotheses": hypotheses,
        "supported": any(h["H-A1"] and h["H-A2"] for h in hypotheses.values()),
    }


def lookalike_rates(names: list[str], ecosystem: str) -> dict[str, Any]:
    from core import lookalike

    statuses: dict[str, int] = {}
    for name in names:
        status = lookalike.check(ecosystem, name)["status"]
        statuses[status] = statuses.get(status, 0) + 1
    checked = len(names) - statuses.get("NOT_PERFORMED", 0)
    return {
        "names": len(names),
        "statuses": dict(sorted(statuses.items())),
        "flagged": wilson(statuses.get("SUSPICIOUS_INCONCLUSIVE", 0), checked),
        "references": [
            {k: v for k, v in source.items()} for source in lookalike.references(ecosystem)[1]
        ],
    }


def young_packages(young: dict[str, Any]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"npm": [], "PyPI": []}
    for history in young["repositories"].values():
        selection = history.get("selection") or {}
        if selection.get("ecosystem") in out and selection.get("package"):
            out[selection["ecosystem"]].append(selection["package"])
    return {eco: sorted(set(names)) for eco, names in out.items()}


def lookalike_results(
    frame_doc: dict[str, Any], young: dict[str, list[str]], organic: dict[str, list[str]]
) -> dict[str, Any]:
    """H-B1 (npm, where a popular-name reference exists) and the PyPI rates."""
    out: dict[str, Any] = {}
    for ecosystem in ("npm", "PyPI"):
        malicious = lookalike_rates(frame_doc[ecosystem]["lookalike_sample"], ecosystem)
        comparison = lookalike_rates(young[ecosystem], ecosystem)
        popular = lookalike_rates(organic[ecosystem], ecosystem)
        m, c = malicious["flagged"], comparison["flagged"]
        out[ecosystem] = {
            "malicious": malicious,
            "young_organic": comparison,
            "popular_organic": popular,
            "difference": difference(m["k"], m["n"], c["k"], c["n"]),
        }
    d = out["npm"]["difference"]
    out["H-B1"] = d["low"] is not None and d["low"] > 0
    return out


def metadata_results(doc: dict[str, Any]) -> dict[str, Any]:
    """The other package indicators on one recorded set, with availability."""
    from benchmarks import reputation_set

    answered: dict[str, dict[str, int]] = {}
    for p in doc["packages"]:
        counts = answered.setdefault(p["ecosystem"], {"packages": 0, "answered": 0})
        counts["packages"] += 1
        counts["answered"] += p.get("status") == 200
    young = reputation_set.young_popular_repository(doc)
    young.pop("flagged_repositories", None)
    return {
        "registry_answered": answered,
        "publisher_change": reputation_set.publisher_change(doc),
        "repository_moved": reputation_set.repository_moved(doc),
        "young_popular_repository": young,
    }


def provenance_coverage(doc: dict[str, Any]) -> dict[str, Any]:
    """Q-C: whether each package's latest recorded release publishes provenance
    (npm provenance or a PyPI PEP 740 attestation). Presence, not verification."""
    out: dict[str, dict[str, int]] = {}
    for p in doc["packages"]:
        counts = out.setdefault(
            p["ecosystem"],
            {"packages": 0, "published": 0, "none": 0, "unknown": 0, "not_checked": 0},
        )
        counts["packages"] += 1
        releases = p.get("releases") or []
        if p.get("status") != 200 or not releases:
            counts["not_checked"] += 1
            continue
        attested = releases[-1].get("attested")
        counts["published" if attested is True else "none" if attested is False else "unknown"] += 1
    return {
        eco: {**c, "published_rate": wilson(c["published"], c["packages"] - c["not_checked"])}
        for eco, c in out.items()
    }


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{100 * value:.1f}%"


def _interval(w: dict[str, Any]) -> str:
    if w["rate"] is None:
        return "n/a (no eligible data)"
    return f"{w['k']}/{w['n']} = {_pct(w['rate'])} [{_pct(w['low'])}, {_pct(w['high'])}]"


def render(results: dict[str, Any]) -> str:
    """The results page: aggregates only, every hypothesis stated either way."""
    stars, look = results["stars"], results["lookalike"]
    lines = [
        "# Track T study, Part A: results",
        "",
        f"Run {results['run_at']} under the registered protocol "
        f"`{results['registration']}` (`docs/research/TRACK_T_STUDY_PROTOCOL.md`). "
        "Author-run with AI assistance: **not an independent evaluation**. Labels are "
        "StarScout's and OSV's; results are agreement with them, never accuracy.",
        "",
        "## Q-A: star history",
        "",
        "| Indicator | Threshold | Held-out organic flagged (H-A2: ≤ 1%) "
        "| StarScout positives flagged (H-A1: ≥ 50%) | H-A1 | H-A2 |",
        "|---|---|---|---|---|---|",
    ]
    for name in INDICATORS:
        h = stars["hypotheses"][name]
        lines.append(
            f"| {name} | {stars['thresholds'][name]:.4g} "
            f"| {_interval(stars['organic_held_out']['pooled'][name])} "
            f"| {_interval(stars['positives']['all'][name])} "
            f"| {'met' if h['H-A1'] else 'not met'} | {'met' if h['H-A2'] else 'not met'} |"
        )
    lines += [
        "",
        f"**Q-A hypotheses {'supported' if stars['supported'] else 'not supported'}**: "
        "supported only when one indicator meets both H-A1 and H-A2.",
        "",
        "By StarScout method (the `low_activity`-only group is the less circular test):",
        "",
        "| Group | Recorded | Eligible | Unresolved | SH1 | SH2 | SH3 |",
        "|---|---|---|---|---|---|---|",
    ]
    groups = {
        **stars["positives"],
        **{f"organic: {k}": v for k, v in stars["organic_held_out"].items()},
    }
    for group, r in groups.items():
        lines.append(
            f"| {group} | {r['recorded']} | {r['eligible']} | {r['unresolved']} | "
            + " | ".join(_interval(r[n]) for n in INDICATORS)
            + " |"
        )
    lines += [
        "",
        "## Q-B: package indicators on OSV-malicious packages",
        "",
        "| Ecosystem | Set | Names | lookalike flagged |",
        "|---|---|---|---|",
    ]
    for eco in ("npm", "PyPI"):
        for label in ("malicious", "young_organic", "popular_organic"):
            r = look[eco][label]
            lines.append(f"| {eco} | {label} | {r['names']} | {_interval(r['flagged'])} |")
    d = look["npm"]["difference"]
    lines += [
        "",
        f"**H-B1 {'met' if look['H-B1'] else 'not met'}** (npm, malicious minus young organic): "
        + (
            "n/a"
            if d["difference"] is None
            else f"{_pct(d['difference'])} [{_pct(d['low'])}, {_pct(d['high'])}]"
        )
        + ". PyPI is descriptive: OpenPulse has no PyPI popular-name list yet (decision 9).",
        "",
        "Registry metadata still answering, and the other indicators, are in "
        "`benchmarks/results/track-t-part-a.json` (`metadata`).",
        "",
        "## Q-C: published provenance on the latest release",
        "",
        "| Set | Ecosystem | Packages | Published | None | Unknown | Not checked |",
        "|---|---|---|---|---|---|---|",
    ]
    for label, coverage in results["provenance"].items():
        for eco, c in sorted(coverage.items()):
            lines.append(
                f"| {label} | {eco} | {c['packages']} | {_interval(c['published_rate'])} "
                f"| {c['none']} | {c['unknown']} | {c['not_checked']} |"
            )
    lines += [
        "",
        "## Limits",
        "",
        "Every bias in protocol §4 applies: survivorship of the positives, the circularity "
        "of StarScout's `clustered` method, label noise, organic sets that are unlikely but "
        "not proven to be benign, and malicious packages whose registry metadata is gone. "
        "None of this shows that OpenPulse is more accurate than another tool (R-C).",
        "",
    ]
    return "\n".join(lines)


def run(registration: str, fetch: Any = None, log=print) -> dict[str, Any]:
    from benchmarks import record_reputation

    reason = registered(PROTOCOL.read_text(encoding="utf-8"), registration)
    if reason:
        raise SystemExit(f"not run: {reason} (protocol §5: register before reading)")
    if RESULTS.exists():
        raise SystemExit(f"not run: {RESULTS.name} exists; the study runs once (§7)")
    calibration, _ = load(CALIBRATION)
    sets, sources = {}, {}
    for label, filename in SETS.items():
        sets[label], digest = load(filename)
        sources[label] = digest
        if digest != calibration["sources"][label]["sha256"]:
            raise SystemExit(f"not run: {filename} changed since calibration")
    positives = json.loads((LOCAL / POSITIVES).read_text(encoding="utf-8"))
    frame_doc, sources["frame"] = load(
        sorted(p.name for p in FIXTURES.glob("malicious-frame-*.json"))[-1]
    )
    organic, sources["organic_packages"] = load(ORGANIC_PACKAGES)
    organic_names = {
        eco: sorted({p["name"] for p in organic["packages"] if p["ecosystem"] == eco})
        for eco in ("npm", "PyPI")
    }
    young = young_packages(sets["young"])
    fetch = fetch or record_reputation.http_fetch
    recorded = {
        "malicious": record_reputation.record(
            fetch, frame_doc["npm"]["sample"], frame_doc["PyPI"]["sample"], log=log
        ),
        "young": record_reputation.record(fetch, young["npm"], young["PyPI"], log=log),
    }
    when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for label, doc in recorded.items():
        out = FIXTURES / f"packages-{label}-{when[:10]}.json"
        out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8")
    return {
        "run_at": when,
        "registration": registration,
        "script": "benchmarks/track_t_study.py",
        "sources_sha256": sources,
        "stars": star_results(calibration, sets, positives),
        "lookalike": lookalike_results(frame_doc, young, organic_names),
        "metadata": {label: metadata_results(doc) for label, doc in recorded.items()},
        "provenance": {
            "popular_organic": provenance_coverage(organic),
            **{label: provenance_coverage(doc) for label, doc in recorded.items()},
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["calibrate", "frame", "run"])
    parser.add_argument("--osv", type=Path, help="frame: directory with npm-all.zip, PyPI-all.zip")
    parser.add_argument("--registered", default="", help="run: the protocol's registration id")
    args = parser.parse_args(argv)
    if args.command == "frame":
        if args.osv is None:
            parser.error("frame needs --osv")
        doc = {
            "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "script": "benchmarks/track_t_study.py frame",
            "source": "OSV npm/all.zip and PyPI/all.zip, MAL- records, withdrawn excluded",
            "seed": SEED,
            **frame({eco: args.osv / f"{eco}-all.zip" for eco in ("npm", "PyPI")}),
        }
        out = FIXTURES / f"malicious-frame-{doc['recorded_at'][:10]}.json"
        out.write_text(json.dumps(doc, indent=0, sort_keys=True) + "\n", "utf-8")
        print(f"wrote {out.relative_to(ROOT)}")
        for eco in ("npm", "PyPI"):
            print(eco, doc[eco]["records"], "records", doc[eco]["names"], "names")
        return 0
    if args.command == "run":
        results = run(args.registered)
        RESULTS.parent.mkdir(parents=True, exist_ok=True)
        RESULTS.write_text(json.dumps(results, indent=1, sort_keys=True) + "\n", "utf-8")
        REPORT.write_text(render(results), "utf-8")
        print(f"wrote {RESULTS.relative_to(ROOT)} and {REPORT.relative_to(ROOT)}")
        return 0
    sets, sources = {}, {}
    for label, filename in SETS.items():
        sets[label], digest = load(filename)
        sources[label] = {"file": filename, "sha256": digest}
    result = calibrate(sets)
    doc = {
        "computed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "script": "benchmarks/track_t_study.py",
        "protocol": "docs/research/TRACK_T_STUDY_PROTOCOL.md §5",
        "seed": SEED,
        "min_stars": MIN_STARS,
        "false_positive_cap": FALSE_POSITIVE_CAP,
        "rule": "fires when the value is strictly above the threshold",
        "sources": sources,
        **result,
    }
    out = FIXTURES / f"star-calibration-{doc['computed_at'][:10]}.json"
    out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8")
    print(f"wrote {out.relative_to(ROOT)}")
    for name, t in doc["thresholds"].items():
        print(name, json.dumps(t))
    print("calibration ineligible", json.dumps(result["calibration_ineligible"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

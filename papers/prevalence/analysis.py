"""Analysis for the prevalence study (PROTOCOL.md §7).

    python analysis.py data/<run>/measures.jsonl > data/<run>/RESULTS.md

Descriptive only: proportions with Wilson 95% intervals per ecosystem and
stratum, never pooled across strata, and no hypothesis tests. Dependent
counts overlap across packages, so they are reported as medians and
maxima, never summed into a count of affected projects.
"""

import json
import math
import statistics
import sys
from collections import defaultdict

STATES = ("archived", "relocated", "unreachable")


def wilson(k, n, z=1.959964):
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def pct(k, n):
    if n == 0:
        return "n/a"
    lo, hi = wilson(k, n)
    return f"{k}/{n} ({100 * k / n:.1f}%, {100 * lo:.1f}–{100 * hi:.1f})"


def md_row(*values):
    """One Markdown table row."""
    return "| " + " | ".join(str(v) for v in values) + " |"


def header(*columns):
    return [md_row(*columns), md_row(*["---"] * len(columns))]


def in_state(row, state):
    if state == "archived":
        return bool(row.get("archived"))
    return row.get("repo_state") == state


def signals(row):
    return {
        "registry": bool(row.get("deprecated")),
        "advisory": bool(row.get("osv_matched")),
        "lifecycle": bool(row.get("eol_product")),
    }


def main(path):
    rows = [json.loads(line) for line in open(path, encoding="utf-8")]
    groups = defaultdict(list)
    for row in rows:
        groups[(row["ecosystem"], row["stratum"])].append(row)
    out = ["# Results", "", f"Source: `{path}`, {len(rows)} packages.", ""]

    out += [
        "## Coverage of the measure",
        "",
        *header(
            "Ecosystem",
            "Stratum",
            "Sampled",
            "Excluded (no GitHub repository published)",
            "Measured",
            "GitHub error",
        ),
    ]
    for (eco, stratum), rs in sorted(groups.items()):
        excluded = sum(r.get("repo_state") == "excluded" for r in rs)
        errors = sum(r.get("repo_state") == "error" for r in rs)
        out.append(md_row(eco, stratum, len(rs), excluded, len(rs) - excluded - errors, errors))

    out += [
        "",
        "## RQ1: Prevalence (share of measured packages, Wilson 95% interval)",
        "",
        "| Ecosystem | Stratum | Archived | Relocated | Unreachable | Any of the three |",
        "|---|---|---|---|---|---|",
    ]
    for (eco, stratum), rs in sorted(groups.items()):
        measured = [
            r for r in rs if r.get("repo_state") in ("unchanged", "relocated", "unreachable")
        ]
        n = len(measured)
        cells = [pct(sum(in_state(r, s) for r in measured), n) for s in STATES]
        anyk = sum(any(in_state(r, s) for s in STATES) for r in measured)
        out.append(f"| {eco} | {stratum} | " + " | ".join(cells) + f" | {pct(anyk, n)} |")
    out += [
        "",
        "Per distinct repository (packages sharing a repository counted once):",
        "",
        "| Ecosystem | Stratum | Repositories | Archived | Relocated | Unreachable |",
        "|---|---|---|---|---|---|",
    ]
    for (eco, stratum), rs in sorted(groups.items()):
        repos = {}
        for r in rs:
            if r.get("repo_state") in ("unchanged", "relocated", "unreachable"):
                repos.setdefault(r["repository"].lower(), r)
        n = len(repos)
        cells = [pct(sum(in_state(r, s) for r in repos.values()), n) for s in STATES]
        out.append(f"| {eco} | {stratum} | {n} | " + " | ".join(cells) + " |")

    out += [
        "",
        "## RQ2: Exposure of affected packages",
        "",
        "Dependent counts overlap across packages; they are not summed.",
        "",
        *header(
            "Ecosystem",
            "Stratum",
            "State",
            "Packages",
            "Median dependent repos",
            "Max dependent repos",
            "Median dependent packages",
        ),
    ]
    for (eco, stratum), rs in sorted(groups.items()):
        for state in STATES:
            hit = [r for r in rs if in_state(r, state)]
            if not hit:
                out.append(f"| {eco} | {stratum} | {state} | 0 | – | – | – |")
                continue
            repos = [r.get("dependent_repos_count") or 0 for r in hit]
            pkgs = [r.get("dependent_packages_count") or 0 for r in hit]
            out.append(
                f"| {eco} | {stratum} | {state} | {len(hit)} | {statistics.median(repos):,.0f} | "
                f"{max(repos):,} | {statistics.median(pkgs):,.0f} |"
            )

    out += [
        "",
        "## RQ3: Signal coverage of archived or unreachable packages",
        "",
        *header(
            "Ecosystem",
            "Stratum",
            "State",
            "Packages",
            "Registry deprecation",
            "Advisory (OSV)",
            "Lifecycle (endoflife.date)",
            "Any signal",
        ),
    ]
    for (eco, stratum), rs in sorted(groups.items()):
        for state in ("archived", "unreachable"):
            hit = [r for r in rs if in_state(r, state)]
            n = len(hit)
            sig = [signals(r) for r in hit]
            cells = [pct(sum(s[k] for s in sig), n) for k in ("registry", "advisory", "lifecycle")]
            out.append(
                f"| {eco} | {stratum} | {state} | {n} | "
                + " | ".join(cells)
                + f" | {pct(sum(any(s.values()) for s in sig), n)} |"
            )

    out += [
        "",
        "## RQ4: Stale references among renamed repositories",
        "",
        "Denominator: measured packages whose repository has a recorded earlier name",
        "(ecosyste.ms `previous_names`). Numerator: the published repository redirects",
        "(relocated).",
        "",
        *header(
            "Ecosystem",
            "Stratum",
            "Renamed",
            "Published name is stale",
            "Relocated without a recorded rename",
            "Examples (published → current)",
        ),
    ]
    for (eco, stratum), rs in sorted(groups.items()):
        measured = [r for r in rs if r.get("repo_state") in ("unchanged", "relocated")]
        renamed = [r for r in measured if r.get("frame_previous_names")]
        stale = [r for r in renamed if r.get("repo_state") == "relocated"]
        unrecorded = sum(
            1
            for r in measured
            if r.get("repo_state") == "relocated" and not r.get("frame_previous_names")
        )
        examples = "; ".join(f"`{r['repository']}` → `{r['github_full_name']}`" for r in stale[:3])
        out.append(
            md_row(
                eco,
                stratum,
                len(renamed),
                pct(len(stale), len(renamed)),
                unrecorded,
                examples or "–",
            )
        )

    out += [
        "",
        "## Archived packages released after the repository's last push (PROTOCOL.md §5 proxy)",
        "",
        "| Ecosystem | Stratum | Archived | Release after last push | No release time |",
        "|---|---|---|---|---|",
    ]
    for (eco, stratum), rs in sorted(groups.items()):
        hit = [r for r in rs if r.get("archived")]
        later = sum(
            1
            for r in hit
            if r.get("latest_released_at")
            and r.get("pushed_at")
            and r["latest_released_at"] > r["pushed_at"]
        )
        unknown = sum(1 for r in hit if not r.get("latest_released_at") or not r.get("pushed_at"))
        out.append(f"| {eco} | {stratum} | {len(hit)} | {later} | {unknown} |")

    agree = [
        r for r in rows if r.get("frame_archived") is not None and r.get("archived") is not None
    ]
    same = sum(bool(r["frame_archived"]) == bool(r["archived"]) for r in agree)
    out += [
        "",
        "## Validation: frame against source",
        "",
        f"ecosyste.ms `archived` agrees with the GitHub measurement on {pct(same, len(agree))}"
        " packages where both exist.",
        "",
    ]
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1])

"""Lifecycle posture and planning view — planning intelligence, not an EOL export.

`collect_lifecycle_status` turns one raw bundle's endoflife.date
entries into structured posture data (effective EOL, upcoming
deadlines with trustworthy dates, ended support, or explicit
NO-DATA). `build_lifecycle_report` renders the monthly posture:
executive summary, upcoming deadlines, recent ends, coverage gaps,
planning items, and the full matrix as an appendix.

Pure functions (no network). Dates compare against an explicit
`today` (defaults to the current date) so renders are deterministic
for identical inputs. Conditional investigation wording only —
never claims about a customer environment.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from core.leadtime import parse_day

#: Status vocabulary, most severe first for primary-status selection.
STATUS_EOL = "EOL"
STATUS_UPCOMING = "UPCOMING"
STATUS_SUPPORT_ENDED = "SUPPORT-ENDED"
STATUS_OK = "OK"
STATUS_NO_DATA = "NO-DATA"

#: Recent-ends lookback and display caps (deterministic).
RECENT_DAYS = 365
RECENT_CAP = 20
PLANNING_CAP = 10


def collect_lifecycle_status(
    slug: str, raw: dict[str, Any], today: date | None = None
) -> dict[str, Any]:
    """One raw bundle -> structured lifecycle posture for a project."""
    today = today or date.today()
    entries = raw.get("endoflife", []) if isinstance(raw, dict) else []
    usable, skipped, errors = [], [], []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("error"):
            errors.append(str(entry.get("safe_message") or entry.get("category") or "error"))
        elif entry.get("skipped"):
            skipped.append(str(entry["skipped"]))
        elif entry.get("cycle") is not None:
            usable.append(entry)
    if not usable:
        if skipped:
            reason = skipped[0]
        elif errors:
            reason = f"lifecycle collection failed ({errors[0]})"
        else:
            reason = "no lifecycle entries returned"
        return {
            "project": slug,
            "status": STATUS_NO_DATA,
            "no_data_reason": reason,
            "eol": [],
            "upcoming": [],
            "support_ended": [],
            "detail": reason,
        }
    product = str(usable[0].get("product") or slug)
    eol, upcoming, support_ended, details = [], [], [], []
    for entry in usable:
        cycle = str(entry.get("cycle"))
        eol_raw, support_raw = entry.get("eol"), entry.get("support")
        if eol_raw is True:
            eol.append({"version": cycle, "date": None})
            details.append(f"{product} {cycle} is end-of-life (date not published)")
            continue
        eol_day = parse_day(eol_raw)
        if eol_day is not None:
            if eol_day <= today:
                eol.append({"version": cycle, "date": str(eol_day)})
                details.append(f"{product} {cycle} is end-of-life ({eol_day})")
            else:
                upcoming.append(
                    {
                        "version": cycle,
                        "date": str(eol_day),
                        "days_remaining": (eol_day - today).days,
                        "kind": "EOL",
                    }
                )
                details.append(f"{product} {cycle} EOL {eol_day}")
            continue
        support_day = parse_day(support_raw) if support_raw is not True else None
        if support_raw is True or (support_day is not None and support_day <= today):
            support_ended.append(
                {"version": cycle, "date": str(support_day) if support_day else None}
            )
            details.append(f"{product} {cycle} support ended")
        elif support_day is not None and support_day > today:
            upcoming.append(
                {
                    "version": cycle,
                    "date": str(support_day),
                    "days_remaining": (support_day - today).days,
                    "kind": "support",
                }
            )
            details.append(f"{product} {cycle} support ends {support_day}")
    if eol:
        status = STATUS_EOL
    elif upcoming:
        status = STATUS_UPCOMING
    elif support_ended:
        status = STATUS_SUPPORT_ENDED
    else:
        status = STATUS_OK
    return {
        "project": slug,
        "status": status,
        "no_data_reason": None,
        "eol": eol,
        "upcoming": upcoming,
        "support_ended": support_ended,
        "detail": "; ".join(details) if details else "lifecycle data present, nothing actionable",
    }


def build_lifecycle_report(
    month: str,
    statuses: list[dict[str, Any]],
    today: date | None = None,
    notes: list[str] | None = None,
) -> str:
    """Monthly lifecycle posture markdown. Deterministic for identical inputs."""
    today = today or date.today()
    ordered = sorted(statuses, key=lambda s: str(s.get("project", "")))
    concern = [s for s in ordered if s.get("eol")]
    upcoming_projects = [s for s in ordered if s.get("upcoming")]
    support_projects = [s for s in ordered if s.get("support_ended")]
    no_data = [s for s in ordered if s.get("status") == STATUS_NO_DATA]
    upcoming_rows = []
    for status in ordered:
        for item in status.get("upcoming", []) or []:
            eff_day = parse_day(item.get("date"))
            if eff_day is None or eff_day <= today:
                continue
            days = (eff_day - today).days
            upcoming_rows.append(
                (
                    str(item["date"]),
                    str(status.get("project", "")),
                    str(item["version"]),
                    days,
                    str(item.get("kind", "EOL")),
                )
            )
    upcoming_rows.sort()
    recent_rows = []
    for status in ordered:
        for item in status.get("eol", []) or []:
            ended = parse_day(item.get("date")) if item.get("date") else None
            if ended is not None:
                ago = (today - ended).days
                if 0 <= ago <= RECENT_DAYS:
                    recent_rows.append(
                        (ago, str(status.get("project", "")), str(item["version"]), "EOL")
                    )
        for item in status.get("support_ended", []) or []:
            ended = parse_day(item.get("date")) if item.get("date") else None
            if ended is not None:
                ago = (today - ended).days
                if 0 <= ago <= RECENT_DAYS:
                    recent_rows.append(
                        (ago, str(status.get("project", "")), str(item["version"]), "support")
                    )
    recent_rows.sort()

    lines = [
        f"# OpenPulse Lifecycle Posture — {month}",
        "",
        f"Reporting period: {month}.",
        "",
        "Lifecycle data is one source OpenPulse uses. OpenPulse is not an EOL "
        "database. Lifecycle signals are combined with upstream changes, "
        "registry observations, security evidence and dependency identity.",
        "",
        "## Executive Summary",
        "",
        f"- Projects checked: {len(ordered)}",
        f"- Projects with current lifecycle concern (effective EOL): {len(concern)}",
        f"- Projects with an upcoming lifecycle deadline: {len(upcoming_projects)}",
        f"- Projects with ended support: {len(support_projects)}",
        f"- Projects with no lifecycle data: {len(no_data)}",
        "",
        "NO-DATA means OpenPulse has no authoritative lifecycle record from "
        "the currently configured lifecycle source. NO-DATA is a coverage "
        "limitation, not an OK state — never read it as safe.",
        "",
        "## Upcoming Deadlines",
        "",
    ]
    if not upcoming_rows:
        lines.append("No upcoming lifecycle deadlines with trustworthy dates.")
        lines.append("")
    else:
        lines.append(
            "| Project | Version | Effective date | Days remaining | Suggested investigation |"
        )
        lines.append("|---|---|---|---|---|")
        for eff_date, project, version, days, kind in upcoming_rows:
            subject = "active support ends" if kind == "support" else "end-of-life"
            lines.append(
                f"| {project} | {version} | {eff_date} | {days} | "
                f"Check whether you run {project} {version}; plan migration before "
                f"{subject} on {eff_date}. |"
            )
        lines.append("")
    lines.append("## Recently Ended")
    lines.append("")
    if not recent_rows:
        lines.append("No lifecycle endings with trustworthy dates in the last year.")
        lines.append("")
    else:
        shown = recent_rows[:RECENT_CAP]
        for ago, project, version, kind in shown:
            subject = "active support ended" if kind == "support" else "reached end-of-life"
            lines.append(
                f"- **{project}** {version} {subject} {ago} days ago. "
                f"Check whether you still run it; migrate or arrange extended support."
            )
        if len(recent_rows) > RECENT_CAP:
            lines.append(f"- (+{len(recent_rows) - RECENT_CAP} more in the appendix)")
        lines.append("")
    lines.append("## Lifecycle Coverage Gaps")
    lines.append("")
    if not no_data:
        lines.append("Full lifecycle coverage: every checked project returned lifecycle data.")
        lines.append("")
    else:
        lines.append(
            "Absence of lifecycle data is a coverage limitation, not an OK state. "
            "These projects need another source before any lifecycle conclusion:"
        )
        lines.append("")
        by_reason: dict[str, list[str]] = {}
        for status in no_data:
            by_reason.setdefault(str(status.get("no_data_reason") or "unknown"), []).append(
                str(status.get("project", ""))
            )
        for reason in sorted(by_reason):
            lines.append(f"- {reason}: {', '.join(sorted(by_reason[reason]))}")
        lines.append("")
    lines.append("## Top Lifecycle Planning Items")
    lines.append("")
    planning = _planning_items(ordered, today)
    if not planning:
        lines.append("Nothing to plan: no upcoming deadlines, recent ends, or confirmed EOL.")
        lines.append("")
    for rank, line in enumerate(planning[:PLANNING_CAP], 1):
        lines.append(f"{rank}. {line}")
    lines.append("")
    lines.append("## Appendix — Full Lifecycle Coverage Matrix")
    lines.append("")
    lines.append("| project | status | detail |")
    lines.append("|---|---|---|")
    for status in ordered:
        lines.append(
            f"| {status.get('project', '')} | {status.get('status', '')} "
            f"| {status.get('detail', '')} |"
        )
    lines.append("")
    if notes:
        lines.append("### Notes")
        lines.append("")
        lines += [f"- {note}" for note in notes]
        lines.append("")
    return "\n".join(lines).rstrip()


def _planning_items(statuses: list[dict[str, Any]], today: date) -> list[str]:
    """Prioritized planning list: soonest deadlines, then recent ends,
    then confirmed EOL by version count. Conditional wording only —
    never customer impact."""
    upcoming, recent = [], []
    for status in statuses:
        project = str(status.get("project", ""))
        for item in status.get("upcoming", []) or []:
            eff_day = parse_day(item.get("date"))
            if eff_day is None or eff_day <= today:
                continue
            days = (eff_day - today).days
            upcoming.append(
                (
                    days,
                    project,
                    str(item["version"]),
                    f"**{project}** {item['version']} EOL in {days} days "
                    f"({item['date']}) — check inventory and plan migration.",
                )
            )
        for item in status.get("eol", []) or []:
            ended = parse_day(item.get("date")) if item.get("date") else None
            if ended is not None:
                ago = (today - ended).days
                if 0 <= ago <= RECENT_DAYS:
                    recent.append(
                        (
                            ago,
                            project,
                            str(item["version"]),
                            f"**{project}** {item['version']} ended {ago} days ago — "
                            "check whether it remains in your inventory.",
                        )
                    )
    upcoming.sort(key=lambda row: (row[0], row[1], row[2]))
    recent.sort(key=lambda row: (row[0], row[1], row[2]))
    lines = [row[3] for row in upcoming] + [row[3] for row in recent]
    covered = {(row[1], row[2]) for row in recent}
    remaining = sorted(
        (project, v["version"])
        for s in statuses
        for v in (s.get("eol", []) or [])
        if (project := str(s.get("project", "")))
        and (project, str(v["version"])) not in covered
    )
    by_project: dict[str, list[str]] = {}
    for project, version in remaining:
        by_project.setdefault(project, []).append(str(version))
    for project in sorted(by_project, key=lambda p: (-len(by_project[p]), p)):
        versions = ", ".join(by_project[project])
        lines.append(
            f"**{project}** has confirmed end-of-life version(s) ({versions}) — "
            "confirm none remain in your inventory."
        )
    return lines

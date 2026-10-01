"""Event Correlation Agent — many raw signals, one coherent story.

Pure functions. Lifecycle story aggregation groups by project event
semantics — event class + temporal state — so an approaching EOL never
merges with an effective one, while same-state version rows union into
one story carrying affected versions, scope, and the event window.
Distribution story aggregation groups same-repo registry diffs by
direction (disappeared / appeared / changed) so one upstream pruning
event renders as one card, not N near-identical ones. Same event
class + same urgency class merge; everything else passes through
untouched. No information is dropped: versions, scopes, dates, tags,
digests, and evidence links union into the story.
"""

from __future__ import annotations

from typing import Any

_LIFECYCLE = ("EOL", "EOS")

_RANK = {"ACTION": 3, "CRITICAL": 3, "REVIEW": 2, "WATCH": 1, "INFORMATIONAL": 0}

_SIGNIFICANCE_RANK = {"high": 3, "medium": 2, "low": 1}

_STATE = {
    ("EOL", "ACTION"): "reached end-of-life",
    ("EOL", "REVIEW"): "approaching end-of-life",
    ("EOS", "REVIEW"): "ended active support",
    ("EOS", "ACTION"): "ended active support",
}


def _versions(finding: dict[str, Any]) -> list[str]:
    seen = []
    for version in finding.get("affected_versions", []) or []:
        if version not in seen:
            seen.append(str(version))
    return seen


def _links(finding: dict[str, Any]) -> list[str]:
    links = []
    for entry in finding.get("supporting", []) or []:
        if not isinstance(entry, dict):
            continue
        for key in ("link", "url"):
            value = entry.get(key)
            if isinstance(value, str) and value.startswith("http") and value not in links:
                links.append(value)
    return links


def _product(finding: dict[str, Any]) -> str:
    for entry in finding.get("supporting", []) or []:
        if isinstance(entry, dict) and entry.get("product"):
            return str(entry["product"])
    return "project"


def _story_key(finding: dict[str, Any]) -> tuple[str, str]:
    """Grouping key: event class + semantic state.

    Temporal state (EFFECTIVE/UPCOMING) splits stories whose meaning
    differs; findings without a state fall back to impact, preserving
    legacy grouping exactly.
    """
    event_type = str(finding.get("event_type", ""))
    state = str(finding.get("lifecycle_state") or "")
    if state:
        return (event_type, state)
    return (event_type, str(finding.get("impact", "INFORMATIONAL")).upper())


def aggregate_lifecycle(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge same-class lifecycle findings into stories; input order kept."""
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    order: list[tuple[str, str] | int] = []
    for index, finding in enumerate(findings):
        event_type = str(finding.get("event_type", ""))
        if event_type in _LIFECYCLE:
            key = _story_key(finding)
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(finding)
        else:
            order.append(index)
    out = []
    for entry in order:
        if isinstance(entry, int):
            out.append(findings[entry])
            continue
        group = groups[entry]
        if len(group) == 1:
            out.append(group[0])
            continue
        out.append(_story(entry[0], group))
    return out


def _story(event_type: str, group: list[dict[str, Any]]) -> dict[str, Any]:
    product = _product(group[0])
    versions: list[str] = []
    links: list[str] = []
    dates: list[str] = []
    scopes: list[str] = []
    significance = "low"
    observed: list[str] = []
    for finding in group:
        versions += [v for v in _versions(finding) if v not in versions]
        links += [u for u in _links(finding) if u not in links]
        date = finding.get("event_date")
        if date:
            dates.append(str(date))
        scope = finding.get("scope") or {}
        for version in scope.get("versions", []) or []:
            if str(version) not in scopes:
                scopes.append(str(version))
        level = str(finding.get("significance") or "").lower()
        if _SIGNIFICANCE_RANK.get(level, 0) > _SIGNIFICANCE_RANK.get(significance, 0):
            significance = level
        seen = finding.get("observed_at")
        if seen:
            observed.append(str(seen))
    impacts = [_RANK.get(str(f.get("impact", "")).upper(), 0) for f in group]
    impact = next(
        (name for name, rank in sorted(_RANK.items(), key=lambda kv: -kv[1])
         if rank == max(impacts)),
        "INFORMATIONAL",
    )
    state = _STATE.get((event_type, impact), event_type)
    story = {
        "analyst": "event-correlation",
        "event_type": event_type,
        "signal": "lifecycle",
        "title": f"{product} lifecycle: {state} ({', '.join(versions)})",
        "summary": f"{len(group)} cycles share one lifecycle story; "
        f"strongest signal kept at {impact}.",
        "impact": impact,
        "significance": significance,
        "event_date": min(dates) if dates else None,
        "affected_versions": versions,
        "affected_artifacts": [],
        "supporting": [e for f in group for e in (f.get("supporting", []) or [])],
        "evidence_links": links,
        "stories_merged": len(group),
    }
    states = {str(f.get("lifecycle_state") or "") for f in group} - {""}
    if len(states) == 1:
        story["lifecycle_state"] = states.pop()
    if scopes:
        story["scope"] = {"kind": "version", "versions": scopes}
    if dates:
        story["effective_window"] = {
            "earliest": min(dates),
            "latest": max(dates),
        }
    if observed:
        story["observed_at"] = min(observed)
    return story


def lifecycle_first(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Order report items so non-lifecycle stories lead lifecycle tables."""

    def key(item: dict[str, Any]) -> tuple[int, str]:
        findings = item.get("findings", [])
        lifecycle_only = findings and all(
            str(f.get("event_type", "")) in _LIFECYCLE for f in findings
        )
        return (1 if lifecycle_only else 0, str(item.get("project", "")))

    return sorted(items, key=key)


#: Registry diff types grouped by story direction. A repo pruning five
#: tags is one upstream event, not five findings.
_DIRECTION = {
    "tag_disappeared": "disappeared",
    "repo_missing": "disappeared",
    "tag_appeared": "appeared",
    "repo_restored": "appeared",
    "tag_digest_changed": "changed",
    "latest_moved": "changed",
}

_DIRECTION_WORD = {
    "disappeared": "disappeared from",
    "appeared": "appeared in",
    "changed": "changed in",
}


def _distribution_key(finding: dict[str, Any]) -> tuple[str, str, str] | None:
    """(image, direction, method) for diff-derived distribution findings.

    Only registry-observation findings carrying observation evidence
    qualify — heuristic and curated findings pass through untouched.
    """
    if str(finding.get("signal", "")) != "distribution":
        return None
    if str(finding.get("detection_method") or "") != "registry_observation":
        return None
    fact = (finding.get("observation_evidence") or {}).get("fact") or {}
    image = str(fact.get("image") or "")
    direction = _DIRECTION.get(str(fact.get("type") or ""))
    if not image or not direction:
        return None
    return (image, direction, "registry_observation")


def aggregate_distribution(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge same-repo/same-direction registry diffs into stories.

    Singletons and non-diff findings pass through untouched (identity
    for existing consumers). Input order kept: each story takes the
    position of its first member.
    """
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    order: list[tuple[str, str, str] | int] = []
    for index, finding in enumerate(findings):
        key = _distribution_key(finding) if isinstance(finding, dict) else None
        if key is None:
            order.append(index)
            continue
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(finding)
    out = []
    for entry in order:
        if isinstance(entry, int):
            out.append(findings[entry])
            continue
        group = groups[entry]
        if len(group) == 1:
            out.append(group[0])
            continue
        out.append(_distribution_story(entry[0], entry[1], group))
    return out


def _distribution_story(
    image: str, direction: str, group: list[dict[str, Any]]
) -> dict[str, Any]:
    """One card for N same-repo/same-direction diffs. Nothing dropped:
    every tag, digest, scope ref, supporting change, and reference
    unions into the story; observation ids match (one observation pair
    produced the whole group)."""
    first = group[0]
    first_evidence = first.get("observation_evidence") or {}
    first_fact = first_evidence.get("fact") or {}
    tags: list[dict[str, Any]] = []
    refs, artifacts, references, supporting = [], [], [], []
    first_detected: list[str] = []
    for finding in group:
        fact = (finding.get("observation_evidence") or {}).get("fact") or {}
        tag = fact.get("tag")
        if tag is not None and all(t.get("tag") != tag for t in tags):
            tags.append(
                {
                    "tag": tag,
                    "previous_digests": fact.get("previous_digests"),
                    "current_digests": fact.get("current_digests"),
                    "first_detected_at": finding.get("first_detected_at"),
                }
            )
        for ref in ((finding.get("scope") or {}).get("artifacts") or []):
            if str(ref) not in refs:
                refs.append(str(ref))
        for artifact in finding.get("affected_artifacts", []) or []:
            if isinstance(artifact, dict) and artifact.get("ref"):
                if all(a.get("ref") != artifact["ref"] for a in artifacts):
                    artifacts.append(artifact)
        for url in (finding.get("references", []) or []) + _links(finding):
            if url not in references:
                references.append(url)
        supporting += [c for c in (finding.get("supporting", []) or []) if c not in supporting]
        detected = finding.get("first_detected_at")
        if detected:
            first_detected.append(str(detected))
    tags.sort(key=lambda t: str(t.get("tag")))
    impacts = [_RANK.get(str(f.get("impact", "")).upper(), 0) for f in group]
    impact = next(
        (
            name
            for name, rank in sorted(_RANK.items(), key=lambda kv: -kv[1])
            if rank == max(impacts)
        ),
        "INFORMATIONAL",
    )
    significance = "low"
    for finding in group:
        level = str(finding.get("significance") or "").lower()
        if _SIGNIFICANCE_RANK.get(level, 0) > _SIGNIFICANCE_RANK.get(significance, 0):
            significance = level
    word = _DIRECTION_WORD[direction]
    tag_names = ", ".join(f"`{t['tag']}`" for t in tags)
    story = {
        "analyst": "event-correlation",
        "event_type": first.get("event_type", "DISTRIBUTION_CHANGE"),
        "signal": "distribution",
        "title": f"{len(tags)} tags {word} {image.replace('docker.io/', '')}",
        "summary": f"Observed {first_fact.get('type')} for {tag_names}.",
        "impact": impact,
        "significance": significance,
        "detection_method": "registry_observation",
        "evidence_strength": first.get("evidence_strength", "moderate"),
        "observed_at": first.get("observed_at"),
        "first_detected_at": (
            min(first_detected) if first_detected else first.get("first_detected_at")
        ),
        "effective_at": first.get("effective_at"),
        "lifecycle_state": first.get("lifecycle_state"),
        "scope": {"kind": "artifact", "artifacts": refs},
        "affected_versions": ["*"],
        "affected_artifacts": artifacts,
        "references": references,
        "observation_evidence": {
            **first_evidence,
            "fact": {
                **first_fact,
                "tags": tags,
            },
        },
        "supporting": supporting,
        "evidence_links": references,
        "stories_merged": len(group),
    }
    return story

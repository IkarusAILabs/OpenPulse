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
    firsts: list[str] = []
    for finding in group:
        versions += [v for v in _versions(finding) if v not in versions]
        links += [u for u in _links(finding) if u not in links]
        date = finding.get("event_date")
        if date:
            dates.append(str(date))
        # Durable first detections (ledger/observation history) must
        # survive the merge: the story's first detection is the
        # earliest of its members', never dropped back to unknown.
        first = finding.get("first_detected_at")
        if first:
            firsts.append(str(first))
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
        (
            name
            for name, rank in sorted(_RANK.items(), key=lambda kv: -kv[1])
            if rank == max(impacts)
        ),
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
    if firsts:
        story["first_detected_at"] = min(firsts)
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


def _distribution_story(image: str, direction: str, group: list[dict[str, Any]]) -> dict[str, Any]:
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
        for ref in (finding.get("scope") or {}).get("artifacts") or []:
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


def split_moves(
    changes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Namespace moves out of raw diff changes.

    A tag disappearing from namespace A while the same tag appears in
    namespace B (same repository, same sweep) is one migration event,
    not two independent findings: returns (move_findings, remaining).
    Move findings carry both sides' observation identity. Unpaired
    changes pass through untouched. Pure function.
    """
    disappeared: dict[tuple[str, str], dict[str, Any]] = {}
    appeared: dict[tuple[str, str], list[dict[str, Any]]] = {}
    others: list[dict[str, Any]] = []
    for change in changes:
        if not isinstance(change, dict):
            continue
        ctype, repo, tag = (
            str(change.get("type") or ""),
            str(change.get("repository") or ""),
            change.get("tag"),
        )
        if ctype == "tag_disappeared" and repo and tag is not None:
            disappeared[(repo, str(tag))] = change
        elif ctype == "tag_appeared" and repo and tag is not None:
            appeared.setdefault((repo, str(tag)), []).append(change)
        else:
            others.append(change)
    consumed: set[int] = set()
    moves = []
    for key in sorted(set(disappeared) & set(appeared)):
        gone = disappeared[key]
        for seen in appeared[key]:
            if str(seen.get("namespace") or "") == str(gone.get("namespace") or ""):
                continue
            moves.append(_move_finding(gone, seen))
            consumed.add(id(gone))
            consumed.add(id(seen))
            break
    remaining = [c for c in others if id(c) not in consumed]
    for key, change in disappeared.items():
        if id(change) not in consumed:
            remaining.append(change)
    for key, group in appeared.items():
        for change in group:
            if id(change) not in consumed:
                remaining.append(change)
    return moves, remaining


def _move_finding(gone: dict[str, Any], seen: dict[str, Any]) -> dict[str, Any]:
    """One migration story from a disappeared/appeared pair."""
    repo = str(gone.get("repository") or "")
    tag = str(gone.get("tag") or "")
    ns_from, ns_to = str(gone.get("namespace") or ""), str(seen.get("namespace") or "")
    observed = str(seen.get("observed_at") or gone.get("observed_at") or "")
    firsts = [str(v) for v in (gone.get("first_detected_at"), seen.get("first_detected_at")) if v]
    ref_from = f"docker.io/{ns_from}/{repo}:{tag}"
    ref_to = f"docker.io/{ns_to}/{repo}:{tag}"
    return {
        "analyst": "change",
        "event_type": "DISTRIBUTION_CHANGE",
        "signal": "distribution",
        "title": f"`{tag}` moved from {ns_from} to {ns_to} ({repo})",
        "summary": f"Tag `{tag}` disappeared from {ns_from}/{repo} and appeared in "
        f"{ns_to}/{repo} in the same observation window — a distribution move, "
        "not two independent changes.",
        "impact": "REVIEW",
        "significance": "medium",
        "detection_method": "registry_observation",
        "evidence_strength": "moderate",
        "observed_at": observed,
        "first_detected_at": min(firsts) if firsts else None,
        "effective_at": observed,
        "lifecycle_state": "EFFECTIVE",
        "scope": {"kind": "artifact", "artifacts": [ref_from, ref_to]},
        "affected_versions": ["*"],
        "affected_artifacts": [
            {"kind": "docker-image", "ref": ref_from},
            {"kind": "docker-image", "ref": ref_to},
        ],
        "references": [
            f"https://hub.docker.com/r/{ns_from}/{repo}/tags",
            f"https://hub.docker.com/r/{ns_to}/{repo}/tags",
        ],
        "observation_evidence": {
            "observation_id": seen.get("current_observation_id"),
            "source": "docker-hub",
            "source_url": f"https://hub.docker.com/r/{ns_to}/{repo}/tags",
            "observed_at": observed,
            "content_hash": seen.get("current_hash"),
            "chain_hash": seen.get("current_chain"),
            "parser_version": seen.get("parser_version"),
            "previous_observation_id": gone.get("previous_observation_id"),
            "previous_observation_hash": gone.get("previous_chain") or gone.get("previous_hash"),
            "previous_observed_at": gone.get("previous_observed_at"),
            "previous_content_hash": gone.get("previous_hash"),
            "fact": {
                "type": "tag_moved",
                "image": f"docker.io/{repo}",
                "tag": tag,
                "from_namespace": ns_from,
                "to_namespace": ns_to,
                "previous_digests": gone.get("previous"),
                "current_digests": seen.get("current"),
            },
        },
        "supporting": [gone, seen],
    }

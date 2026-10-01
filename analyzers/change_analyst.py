"""Change Analyst — lifecycle/distribution signals from raw collector output.

Pure functions: no network, deterministic. Consumes the raw dicts
produced by collectors (endoflife, registries, github) and emits
finding dicts. Findings are *proposals* — the Evidence Analyst and
the gate in core/evidence/policy.py decide what becomes an OSSEvent.

Every lifecycle finding carries machine-readable scope
(``scope.kind/versions``), a temporal state (``lifecycle_state``:
EFFECTIVE/UPCOMING), and change timestamps (``effective_at``,
``observed_at``). Registry findings additionally carry
``significance`` (low/medium/high) assessed from the observation
itself — never from assumed customer usage. Impact here is the
analyst's proposal; ``core.risk.impact.evaluate_impact`` decides
report eligibility downstream.
"""

from __future__ import annotations

from datetime import date
from typing import Any

EOL_WARN_DAYS = 180

#: How a registry finding was detected. ``namespace_heuristic`` fires on
#: naming patterns (e.g. *-legacy holding versioned tags) — useful for
#: discovery, never authoritative evidence. ``registry_observation``
#: records direct probe/diff facts. ``official_distribution_announcement``
#: is reserved for curated official findings (no producer yet).
DETECTION_REGISTRY_OBSERVATION = "registry_observation"
DETECTION_NAMESPACE_HEURISTIC = "namespace_heuristic"
DETECTION_OFFICIAL_ANNOUNCEMENT = "official_distribution_announcement"

#: Evidence strength carried by registry-diff findings. A directly
#: observed probe/diff fact is ``moderate`` — a real fact from one
#: source, not corroboration and not authority. Heuristic detections
#: (namespace patterns) are ``weak``: discovery leads, never evidence.
#: Only official distribution announcements (no producer yet) may be
#: ``strong``. ``core.risk.impact`` caps weak findings at REVIEW.
EVIDENCE_MODERATE = "moderate"
EVIDENCE_WEAK = "weak"
EVIDENCE_STRONG = "strong"

#: Lifecycle temporal states (P1 §8): announced/upcoming vs effective.
STATE_EFFECTIVE = "EFFECTIVE"
STATE_UPCOMING = "UPCOMING"


def _parse_date(value: Any) -> date | None:
    if value is True:
        return date.min  # endoflife.date uses `true` for "already EOL"
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def analyze_endoflife(
    entries: list[dict[str, Any]], today: date | None = None
) -> list[dict[str, Any]]:
    """Map endoflife.date cycles to EOL/EOS findings."""
    today = today or date.today()
    findings = []
    for e in entries:
        if e.get("error") or e.get("skipped"):
            continue
        cycle, product = e.get("cycle"), e.get("product", "?")
        eol = _parse_date(e.get("eol"))
        if eol is not None and eol <= today:
            findings.append(
                {
                    "analyst": "change",
                    "event_type": "EOL",
                    "signal": "lifecycle",
                    "title": f"{product} {cycle} is end-of-life",
                    "summary": f"Cycle {cycle} reached EOL {_lifecycle_when(e.get('eol'))}; "
                    "no further fixes. Plan upgrade or extended support.",
                    "impact": "ACTION",
                    "event_date": str(e.get("eol")),
                    "effective_at": (None if e.get("eol") is True else str(eol)),
                    "observed_at": str(today),
                    "lifecycle_state": STATE_EFFECTIVE,
                    "scope": {"kind": "version", "versions": [str(cycle)]},
                    "affected_versions": [str(cycle)],
                    "affected_artifacts": [],
                    "supporting": [e],
                }
            )
            continue
        if eol is not None and (eol - today).days <= EOL_WARN_DAYS:
            findings.append(
                {
                    "analyst": "change",
                    "event_type": "EOL",
                    "signal": "lifecycle",
                    "title": f"{product} {cycle} EOL approaching ({e.get('eol')})",
                    "summary": f"Cycle {cycle} ends in {(eol - today).days} days. "
                    "Start migration planning now.",
                    "impact": "REVIEW",
                    "event_date": str(e.get("eol")),
                    "effective_at": (None if e.get("eol") is True else str(eol)),
                    "observed_at": str(today),
                    "lifecycle_state": STATE_UPCOMING,
                    "scope": {"kind": "version", "versions": [str(cycle)]},
                    "affected_versions": [str(cycle)],
                    "affected_artifacts": [],
                    "supporting": [e],
                }
            )
        support = _parse_date(e.get("support"))
        if support is not None and support <= today:
            findings.append(
                {
                    "analyst": "change",
                    "event_type": "EOS",
                    "signal": "support",
                    "title": f"{product} {cycle} ended active support",
                    "summary": f"Active support for cycle {cycle} ended "
                    f"{_lifecycle_when(e.get('support'))}; only security fixes, if any.",
                    "impact": "REVIEW",
                    "event_date": str(e.get("support")),
                    "effective_at": (None if e.get("support") is True else str(support)),
                    "observed_at": str(today),
                    "lifecycle_state": STATE_EFFECTIVE,
                    "scope": {"kind": "version", "versions": [str(cycle)]},
                    "affected_versions": [str(cycle)],
                    "affected_artifacts": [],
                    "supporting": [e],
                }
            )
    return findings


def _lifecycle_when(raw: Any) -> str:
    """Human rendering of an endoflife.date date-or-true field."""
    if raw is True:
        return "(date not published)"
    return f"on {raw}"


def _is_legacy_ns(namespace: str) -> bool:
    """Heuristic marker for a legacy-holding namespace (generic mechanism).

    Matches ``bitnamilegacy``, ``*-legacy``, ``legacy-*``. A naming
    heuristic, not proof — recorded in the finding, never hidden.
    """
    ns = str(namespace or "").lower()
    return "legacy" in ns


def analyze_registries(
    entries: list[dict[str, Any]], today: date | None = None
) -> list[dict[str, Any]]:
    """Map registry probes to distribution findings.

    Generic engine: for one image name held in two namespaces where one
    side is latest-only and the other (legacy-marked) holds versioned
    tags, the versioned distribution moved behind a new model. Bitnami
    remains the golden scenario proving the generic logic — no
    Bitnami-specific branches below.
    """
    today = today or date.today()
    by_image: dict[str, list[dict[str, Any]]] = {}
    for e in entries:
        if e.get("error") or not e.get("repo"):
            continue
        by_image.setdefault(str(e.get("repo")), []).append(e)
    findings = []
    claimed: set[tuple[str | None, str | None]] = set()
    for image, repos in by_image.items():
        mainline = [e for e in repos if e.get("latest_only")]
        legacy = [
            e for e in repos if e.get("has_versioned_tags") and _is_legacy_ns(e.get("namespace"))
        ]
        if mainline and legacy:
            main, old = mainline[0], legacy[0]
            m_ns, o_ns = main.get("namespace"), old.get("namespace")
            findings.append(
                {
                    "analyst": "change",
                    "event_type": "DISTRIBUTION_CHANGE",
                    "signal": "distribution",
                    "title": f"{m_ns} mainline is latest-only; versioned tags live in {o_ns}",
                    "summary": f"docker.io/{m_ns} serves only `latest` while "
                    f"docker.io/{o_ns} holds versioned tags with no updates. "
                    f"Pinned {m_ns}/* references need a migration plan.",
                    "impact": "ACTION",
                    "observed_at": str(today),
                    "effective_at": None,
                    "lifecycle_state": STATE_EFFECTIVE,
                    "significance": "high",
                    "detection_method": DETECTION_NAMESPACE_HEURISTIC,
                    "evidence_strength": EVIDENCE_WEAK,
                    "distribution_model_change": True,
                    "scope": {"kind": "project", "versions": []},
                    "affected_versions": ["*"],
                    "affected_artifacts": [
                        {"kind": "docker-image", "ref": f"docker.io/{m_ns}/{image}:<version>"},
                        {"kind": "docker-image", "ref": f"docker.io/{o_ns}/{image}:<version>"},
                    ],
                    "supporting": [main, old],
                }
            )
            claimed.add((m_ns, image))
            claimed.add((o_ns, image))
    for (ns, repo), e in {
        (e.get("namespace"), e.get("repo")): e
        for e in entries
        if not e.get("error") and e.get("repo")
    }.items():
        if (ns, repo) in claimed:
            continue
        ref = f"docker.io/{ns}/{repo}"
        if e.get("latest_only"):
            findings.append(
                {
                    "analyst": "change",
                    "event_type": "DISTRIBUTION_CHANGE",
                    "signal": "distribution",
                    "title": f"{ns}/{repo} publishes latest-only tags",
                    "summary": "Only the `latest` tag is published; version "
                    "pinning is impossible. Avoid in production.",
                    "impact": "WATCH",
                    "observed_at": str(today),
                    "effective_at": None,
                    "lifecycle_state": STATE_EFFECTIVE,
                    "significance": "medium",
                    "detection_method": DETECTION_REGISTRY_OBSERVATION,
                    "evidence_strength": EVIDENCE_MODERATE,
                    "scope": {"kind": "artifact", "artifacts": [ref]},
                    "affected_versions": ["*"],
                    "affected_artifacts": [{"kind": "docker-image", "ref": f"{ref}:<version>"}],
                    "supporting": [e],
                }
            )
        if e.get("missing"):
            findings.append(
                {
                    "analyst": "change",
                    "event_type": "REGISTRY_CHANGE",
                    "signal": "distribution",
                    "title": f"{ns}/{repo} missing from registry",
                    "summary": "Repository not found — possible removal or rename. "
                    "Verify pulls and mirrors before treating this as removal.",
                    "impact": "REVIEW",
                    "observed_at": str(today),
                    "effective_at": None,
                    "lifecycle_state": STATE_EFFECTIVE,
                    "significance": "high",
                    "detection_method": DETECTION_REGISTRY_OBSERVATION,
                    "evidence_strength": EVIDENCE_MODERATE,
                    "scope": {"kind": "artifact", "artifacts": [ref]},
                    "affected_versions": ["*"],
                    "affected_artifacts": [{"kind": "docker-image", "ref": ref}],
                    "supporting": [e],
                }
            )
    return findings


def analyze_github_meta(
    entries: list[dict[str, Any]], today: date | None = None
) -> list[dict[str, Any]]:
    """Repository metadata rules: archived repos, license visibility."""
    today = today or date.today()
    findings = []
    for e in entries:
        if e.get("error") or e.get("skipped") or e.get("kind") != "repo_meta":
            continue
        if e.get("archived"):
            findings.append(
                {
                    "analyst": "change",
                    "event_type": "PROJECT_ARCHIVED",
                    "signal": "lifecycle",
                    "title": f"{e.get('repo')} is archived on GitHub",
                    "summary": "The repository is read-only; no fixes will "
                    f"land. Last push {e.get('pushed_at')}. Teams depending "
                    "on it may need to migrate.",
                    "impact": "ACTION",
                    "observed_at": str(today),
                    "effective_at": None,
                    "lifecycle_state": STATE_EFFECTIVE,
                    "significance": "high",
                    "scope": {"kind": "project", "versions": []},
                    "affected_versions": ["*"],
                    "affected_artifacts": [],
                    "supporting": [e],
                }
            )
    return findings


#: Diff type -> (event_type, impact, significance, template).
#: Significance is assessed from the observation itself (P1 §12):
#: a moved `latest` digest is routine registry churn (low); a vanished
#: versioned tag needs usage context to matter (medium); a vanished
#: repository is a high-significance candidate that still needs
#: confirmation (impact REVIEW, never automatic ACTION).
DIFF_RULES = {
    "tag_disappeared": (
        "DISTRIBUTION_CHANGE",
        "REVIEW",
        "high",
        "Tag `{tag}` disappeared from {ns}/{repo}",
    ),
    "tag_appeared": (
        "DISTRIBUTION_CHANGE",
        "WATCH",
        "low",
        "Tag `{tag}` appeared in {ns}/{repo}",
    ),
    "tag_digest_changed": (
        "DISTRIBUTION_CHANGE",
        "WATCH",
        "low",
        "Digest behind `{tag}` changed in {ns}/{repo} — republished under the same name",
    ),
    "latest_moved": (
        "DISTRIBUTION_CHANGE",
        "WATCH",
        "low",
        "`latest` in {ns}/{repo} now resolves to a new digest — pin digests in production",
    ),
    "repo_missing": (
        "REGISTRY_CHANGE",
        "REVIEW",
        "high",
        "{ns}/{repo} disappeared from the registry",
    ),
    "repo_restored": (
        "REGISTRY_CHANGE",
        "INFORMATIONAL",
        "low",
        "{ns}/{repo} reappeared in the registry",
    ),
}


def analyze_diffs(changes: list[dict[str, Any]], today: date | None = None) -> list[dict[str, Any]]:
    """Detected observation diffs -> findings (no diff, no finding).

    Every finding retains first-class observation evidence: the exact
    diff fact plus the immutable identity (ids, hashes, timestamps)
    of both observations behind it. The public URL is context for
    readers; the observation identity is the evidence for machines.
    """
    today = today or date.today()
    findings = []
    for c in changes:
        if not isinstance(c, dict):
            continue
        rule = DIFF_RULES.get(str(c.get("type", "")))
        if not rule:
            continue
        event_type, impact, significance, template = rule
        ns, repo = c.get("namespace", "?"), c.get("repository", "?")
        observed = str(c.get("observed_at") or today)
        ref = f"docker.io/{ns}/{repo}:{c.get('tag', '')}".rstrip(":")
        findings.append(
            {
                "analyst": "change",
                "event_type": event_type,
                "signal": "distribution",
                "title": template.format(tag=c.get("tag"), ns=ns, repo=repo),
                "summary": f"Observed {c.get('type')} at {observed}.",
                "impact": impact,
                "significance": significance,
                "detection_method": DETECTION_REGISTRY_OBSERVATION,
                "evidence_strength": EVIDENCE_MODERATE,
                "observed_at": str(today),
                "first_detected_at": c.get("first_detected_at"),
                "effective_at": observed,
                "lifecycle_state": STATE_EFFECTIVE,
                "scope": {"kind": "artifact", "artifacts": [ref]},
                "affected_versions": ["*"],
                "affected_artifacts": [{"kind": "docker-image", "ref": ref}],
                "references": [f"https://hub.docker.com/r/{ns}/{repo}/tags"],
                "observation_evidence": {
                    "observation_id": c.get("current_observation_id"),
                    "source": "docker-hub",
                    "source_url": f"https://hub.docker.com/r/{ns}/{repo}/tags",
                    "observed_at": observed,
                    "content_hash": c.get("current_hash"),
                    "chain_hash": c.get("current_chain"),
                    "parser_version": c.get("parser_version"),
                    "previous_observation_id": c.get("previous_observation_id"),
                    "previous_observation_hash": c.get("previous_chain")
                    or c.get("previous_hash"),
                    "previous_observed_at": c.get("previous_observed_at"),
                    "previous_content_hash": c.get("previous_hash"),
                    "fact": {
                        "type": c.get("type"),
                        "image": f"docker.io/{ns}/{repo}",
                        "tag": c.get("tag"),
                        "previous_digests": c.get("previous"),
                        "current_digests": c.get("current"),
                    },
                },
                "supporting": [c],
            }
        )
    return findings


def analyze(
    raw: dict[str, list[dict[str, Any]]], today: date | None = None
) -> list[dict[str, Any]]:
    """Run all change rules over a raw collector bundle."""
    today = today or date.today()
    findings = analyze_endoflife(raw.get("endoflife", []), today=today)
    findings += analyze_registries(raw.get("registries", []), today=today)
    findings += analyze_github_meta(raw.get("github_meta", []), today=today)
    return findings

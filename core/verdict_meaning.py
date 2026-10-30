"""What a verdict asserts, and what it does not (TR-2026-01 §5.1, §5.2).

A relationship label alone invites over-reading: an agent can take a bare
NOT_AFFECTED as permission to proceed, and an AFFECTS_ARTIFACT as a
finding that the dependency is broken or unsafe. Both are wrong. A
verdict is a statement about *direct scope membership* only. This module
states that, as closed vocabularies a consumer can decide on without
reading any free text:

- ``direct_scope``: member | excluded | undetermined | project_tie |
  no_association, derived from the relationship;
- ``embedded_components``, ``availability``, ``maintenance_or_support``,
  ``security_consequence``: always ``not_evaluated`` today. OpenPulse
  evaluates none of them, and saying so is the point;
- ``statement``: a fixed template per ``direct_scope``. It contains no
  upstream text, so it carries no injected content.

``scope_completeness`` states whether the event's scope was declared
complete, on what basis, and whether that admits a negative. Pure
functions; no I/O.
"""

from __future__ import annotations

from typing import Any

NOT_EVALUATED = "not_evaluated"

DIRECT_SCOPE = {
    "AFFECTS_ARTIFACT": "member",
    "AFFECTS_VERSION": "member",
    "AFFECTS_PACKAGE": "member",
    "NOT_AFFECTED": "excluded",
    "RELATED": "undetermined",
    "AFFECTS_PROJECT": "project_tie",
    "UNKNOWN": "no_association",
}

_STATEMENTS = {
    "member": (
        "In the event's directly named scope. Availability, maintenance or support, "
        "and security consequence were not evaluated: scope membership is not a finding "
        "that the dependency is broken, unsafe or unmaintained."
    ),
    "excluded": (
        "Outside the directly named scope of the cited evidence (an event scope declared "
        "complete, or an advisory's affected ranges). Embedded components, availability, "
        "maintenance or support, and security consequence were not evaluated, and other "
        "events were not considered: this is not a clearance of the dependency."
    ),
    "undetermined": (
        "Scope membership is not established (identity, version, scope completeness or "
        "evidence currency is unresolved). Not a clearance."
    ),
    "project_tie": (
        "Belongs to the event's project, but membership in the event's scope is not "
        "established. Not a clearance."
    ),
    "no_association": (
        "No association with this event was found. Not a clearance: an unknown is not "
        "evidence of safety."
    ),
}


def verdict_meaning(relationship: str) -> dict[str, str]:
    """The closed-vocabulary meaning block for one verdict relationship."""
    direct = DIRECT_SCOPE.get(relationship, "undetermined")
    return {
        "direct_scope": direct,
        "embedded_components": NOT_EVALUATED,
        "availability": NOT_EVALUATED,
        "maintenance_or_support": NOT_EVALUATED,
        "security_consequence": NOT_EVALUATED,
        "statement": _STATEMENTS[direct],
    }


def scope_completeness(scope: Any) -> dict[str, Any]:
    """{state, basis, admits_negative} for an event's scope (or None).

    ``declared`` needs ``exhaustive`` set; ``verified`` is reserved for a
    future verifier and never produced today. A declaration without a
    basis does not admit a negative (N3).
    """
    if scope is None:
        return {"state": "partial", "basis": None, "admits_negative": False}
    declared = bool(getattr(scope, "exhaustive", False))
    basis = getattr(scope, "basis", None)
    return {
        "state": "declared" if declared else "partial",
        "basis": basis if declared else None,
        "admits_negative": bool(declared and basis is not None),
    }

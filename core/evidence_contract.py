"""Evidence contract v1 - standalone schema + builder + validator (issue #67).

The v1 content contract: a JSON document another system can consume
without importing OpenPulse internals. Three layers, each testable
alone:

1. ``schemas/evidence-contract/v1/schema.json`` - the wire shape, JSON
   Schema draft 2020-12, every field carrying a provenance pointer to
   the current OpenPulse surface it copies.
2. ``build_v1_contract`` - (event, verdict[, finding]) -> v1 document.
   The convergence itself lives in ``core.attestation`` (issue #53,
   PR #60): this layer only renames blocks to the v1 outward names
   (event -> event_context, evidence_references -> evidence_refs,
   dates -> temporal) and stamps contract_version 1.0.0. No second
   derivation path exists - v1 is the #60 builder plus names.
3. ``validate_v1_contract`` - standalone validation against the
   schema: no pydantic, no jsonschema dependency. Hand-rolled on
   purpose (the acceptance bars say no new dependencies), and a
   consumer that only needs the schema file can use any
   draft-2020-12 validator instead. The validator supports exactly
   the subset the schema uses: type/enum/const/items/minItems/
   required/additionalProperties/minLength/maxLength/pattern/anyOf/
   $ref/format(date, date-time, uri). Any OTHER keyword is an error,
   never a pass - fail closed.

Integrity: ``provenance.content_hash`` is the #60 body hash recomputed
over the v1 shape (content_hash and generation_timestamp pinned during
hashing), so the same logical document built twice hashes identically
regardless of build time.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from core import attestation
from core.attestation import EvidenceContract
from core.evidence.provenance import hash_content
from core.schema.models import OSSEvent

#: Semver of the v1 contract shape. Bump per the versioning policy in
#: docs/EVIDENCE_CONTRACT.md (patch: wording; minor: additive fields;
#: major: any breaking change to shape or hash semantics).
CONTRACT_VERSION = "1.0.0"

#: The v1 JSON Schema, shipped with the repo. Loaded lazily so that
#: importing this module never touches the filesystem.
SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "schemas" / "evidence-contract" / "v1" / "schema.json"
)

#: v1 outward block names for the #60 inward ones. The builder is a
#: rename layer; every value path is shared with core.attestation.
_V1_RENAME = {
    "contract_schema_version": "contract_version",
    "event": "event_context",
    "evidence_references": "evidence_refs",
    "dates": "temporal",
}


def contract_version() -> str:
    """Semver of the v1 contract shape."""
    return CONTRACT_VERSION


def load_schema() -> dict[str, Any]:
    """The v1 JSON Schema, parsed from the shipped file."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def build_v1_contract(
    event: OSSEvent,
    verdict: Any,
    finding: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """(event, verdict[, finding]) -> one schema-valid v1 document.

    Pure: no I/O, no side effects. The convergence is the #60 builder
    (``attestation.build_contract``); this layer renames blocks to the
    v1 outward names, stamps contract_version 1.0.0 in both places,
    and recomputes the content hash over the v1 shape. Unknown stays
    unknown - nothing is inferred or backfilled.
    """
    base = attestation.build_contract(event, verdict, finding)
    doc = _rename_blocks(base)
    doc["contract_version"] = CONTRACT_VERSION
    _set_content_hash(doc)
    return doc


def _rename_blocks(base: EvidenceContract) -> dict[str, Any]:
    """#60 document -> v1 outward names, values untouched."""
    dumped = base.model_dump(mode="json")
    out: dict[str, Any] = {}
    for name, value in dumped.items():
        out[_V1_RENAME.get(name, name)] = value
    # The provenance block carries the inward #60 name for the same
    # semantic (its own schema-version field); rename inside the
    # block too, so v1 never leaks the inward name anywhere.
    prov = out.get("provenance")
    if isinstance(prov, dict) and "contract_schema_version" in prov:
        prov.pop("contract_schema_version")
        prov["contract_version"] = CONTRACT_VERSION
    return out


#: Fields covered by the v1 content hash: every top-level field except
#: the planned (always-null) signature family, with the two
#: clock/hash-dependent provenance values pinned during hashing so
#: the digest is a function of the evidence content only.
_V1_BODY_FIELDS = (
    "contract_version",
    "event_context",
    "identity",
    "scope",
    "affected_dependency",
    "assessment",
    "evidence_refs",
    "temporal",
    "unknowns",
    "recommendation",
    "provenance",
)


def _hash_body(doc: dict[str, Any]) -> str:
    """Digest over the v1 body with content_hash and the generation
    timestamp pinned: same logical content -> same hash, always."""
    body: dict[str, Any] = {name: doc[name] for name in _V1_BODY_FIELDS}
    body["provenance"] = dict(body["provenance"])
    body["provenance"]["content_hash"] = attestation._HASH_PLACEHOLDER
    body["provenance"]["generation_timestamp"] = attestation._TIMESTAMP_PLACEHOLDER
    return hash_content(body)


def _set_content_hash(doc: dict[str, Any]) -> None:
    doc["provenance"]["content_hash"] = _hash_body(doc)


def verify_v1_content_hash(doc: dict[str, Any]) -> bool:
    """True when provenance.content_hash matches the recomputed v1
    body hash. Clock drift never breaks this: only content matters."""
    try:
        return _hash_body(doc) == doc["provenance"]["content_hash"]
    except (KeyError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Standalone validator (schema-driven, fail-closed)
# ---------------------------------------------------------------------------


def validate_v1_contract(doc: Any, schema: dict[str, Any] | None = None) -> list[str]:
    """Validate a document against the v1 schema. [] means valid.

    Standalone on purpose: no pydantic, no jsonschema. Returns a list
    of human-readable error strings ("$.path: what"). Consumers that
    only ship the schema file can port this function or use any
    draft-2020-12 validator - the subset is pinned below and in
    docs/EVIDENCE_CONTRACT.md.
    """
    if schema is None:
        schema = load_schema()
    errors: list[str] = []
    _validate(doc, schema, schema, "$", errors)
    return errors


#: The exact keyword subset the v1 schema may use. Anything outside
#: this set fails validation with an explicit unsupported-keyword
#: error (fail closed): extending the schema and the validator must
#: happen in the same PR, never one without the other.
_SUPPORTED = frozenset(
    {
        "type",
        "const",
        "enum",
        "anyOf",
        "$ref",
        "items",
        "minItems",
        "required",
        "properties",
        "additionalProperties",
        "minLength",
        "maxLength",
        "pattern",
        "format",
    }
)

#: Annotations the validator walks past without acting on them.
_ANNOTATIONS = frozenset({"title", "description", "deprecated"})


def _validate(
    value: Any,
    node: dict[str, Any],
    root: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    """Subset walker: exactly the keywords the v1 schema uses."""
    for keyword in node:
        if keyword.startswith("$") or keyword in _ANNOTATIONS:
            continue
        if keyword not in _SUPPORTED:
            errors.append(f"{path}: schema uses unsupported keyword `{keyword}`")

    if "const" in node and not _eq(value, node["const"]):
        errors.append(f"{path}: expected const {node['const']!r}, got {value!r}")
    if "enum" in node and not any(_eq(value, item) for item in node["enum"]):
        errors.append(f"{path}: {value!r} is not one of {node['enum']}")

    if "anyOf" in node:
        branch_failures: list[list[str]] = []
        for branch in node["anyOf"]:
            candidate: list[str] = []
            _validate(value, branch, root, path, candidate)
            if not candidate:
                return
            branch_failures.append(candidate)
        errors.append(f"{path}: value {value!r} matches none of the anyOf branches")
        return

    if "$ref" in node:
        _validate(value, _resolve_ref(node["$ref"], root), root, path, errors)
        return

    declared = node.get("type")
    if declared is not None and not _type_ok(value, declared, path, errors):
        return

    if isinstance(value, str):
        if "minLength" in node and len(value) < node["minLength"]:
            errors.append(f"{path}: shorter than minLength {node['minLength']}")
        if "maxLength" in node and len(value) > node["maxLength"]:
            errors.append(f"{path}: longer than maxLength {node['maxLength']}")
        if "pattern" in node and re.search(node["pattern"], value) is None:
            errors.append(f"{path}: {value!r} does not match pattern {node['pattern']!r}")
        fmt = node.get("format")
        if fmt == "date" and not _is_date(value):
            errors.append(f"{path}: {value!r} is not an ISO date (YYYY-MM-DD)")
        elif fmt == "date-time" and not _is_datetime(value):
            errors.append(f"{path}: {value!r} is not an RFC 3339 date-time")
        elif fmt == "uri" and not _is_uri(value):
            errors.append(f"{path}: {value!r} is not an absolute URI")
        elif fmt not in (None, "date", "date-time", "uri"):
            errors.append(f"{path}: schema uses unsupported format `{fmt}`")

    if isinstance(value, list):
        if "minItems" in node and len(value) < node["minItems"]:
            errors.append(f"{path}: fewer than minItems {node['minItems']}")
        items = node.get("items")
        if isinstance(items, dict):
            for i, item in enumerate(value):
                _validate(item, items, root, f"{path}[{i}]", errors)

    if isinstance(value, dict):
        for name in node.get("required", []):
            if name not in value:
                errors.append(f"{path}: missing required property `{name}`")
        properties = node.get("properties", {})
        if node.get("additionalProperties") is False:
            for name in value:
                if name not in properties:
                    errors.append(f"{path}: unexpected property `{name}`")
        for name, sub in properties.items():
            if name in value:
                _validate(value[name], sub, root, f"{path}.{name}", errors)


def _resolve_ref(ref: str, root: dict[str, Any]) -> dict[str, Any]:
    """`#/$defs/name` only - the v1 schema refs nothing else."""
    if not ref.startswith("#/"):
        raise ValueError(f"unsupported $ref {ref!r} (only local #/$defs/ refs)")
    node: Any = root
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def _eq(value: Any, expected: Any) -> bool:
    """JSON equality: bool is never an int, str never a number."""
    if isinstance(value, bool) or isinstance(expected, bool):
        return type(value) is type(expected) and value == expected
    return value == expected


def _type_ok(value: Any, declared: str, path: str, errors: list[str]) -> bool:
    """Type gate. Returns False when the value does not match, after
    appending the error - callers stop walking that subtree."""
    if declared == "object":
        ok = isinstance(value, dict)
    elif declared == "array":
        ok = isinstance(value, list)
    elif declared == "string":
        ok = isinstance(value, str)
    elif declared == "boolean":
        ok = isinstance(value, bool)
    elif declared == "null":
        ok = value is None
    elif declared in ("integer", "number"):
        ok = isinstance(value, (int, float)) and not isinstance(value, bool)
    else:
        errors.append(f"{path}: schema uses unsupported type `{declared}`")
        return False
    if not ok:
        errors.append(f"{path}: expected {declared}, got {_json_type(value)}")
    return ok


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _is_date(value: str) -> bool:
    from datetime import date

    try:
        return date.fromisoformat(value) is not None
    except (ValueError, TypeError):
        return False


def _is_datetime(value: str) -> bool:
    from datetime import datetime

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")) is not None
    except (ValueError, TypeError):
        return False


def _is_uri(value: str) -> bool:
    """Absolute URI: scheme per RFC 3986 (alpha then alnum/+/.-)."""
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", value))

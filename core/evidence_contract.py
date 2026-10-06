"""Evidence contract v1: standalone machine-consumable dependency evidence."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from core import attestation
from core.attestation import EvidenceContract
from core.evidence.provenance import hash_content
from core.schema.models import OSSEvent


CONTRACT_VERSION = "1.0.0"
SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "schemas"
    / "evidence-contract"
    / "v1"
    / "schema.json"
)
_V1_RENAME = {
    "contract_schema_version": "contract_version",
    "event": "event_context",
    "evidence_references": "evidence_refs",
    "dates": "temporal",
}
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


def contract_version() -> str:
    return CONTRACT_VERSION


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def build_v1_contract(
    event: OSSEvent,
    verdict: Any,
    finding: dict[str, Any] | None = None,
) -> dict[str, Any]:
    doc = _rename_blocks(attestation.build_contract(event, verdict, finding))
    doc["contract_version"] = CONTRACT_VERSION
    _set_content_hash(doc)
    return doc


def _rename_blocks(base: EvidenceContract) -> dict[str, Any]:
    out = {
        _V1_RENAME.get(key, key): value
        for key, value in base.model_dump(mode="json").items()
    }
    provenance = out.get("provenance")
    if isinstance(provenance, dict) and "contract_schema_version" in provenance:
        provenance.pop("contract_schema_version")
        provenance["contract_version"] = CONTRACT_VERSION
    return out


def _hash_body(doc: dict[str, Any]) -> str:
    body = {name: doc[name] for name in _V1_BODY_FIELDS}
    body["provenance"] = dict(body["provenance"])
    body["provenance"]["content_hash"] = attestation._HASH_PLACEHOLDER
    body["provenance"]["generation_timestamp"] = attestation._TIMESTAMP_PLACEHOLDER
    return hash_content(body)


def _set_content_hash(doc: dict[str, Any]) -> None:
    doc["provenance"]["content_hash"] = _hash_body(doc)


def verify_v1_content_hash(doc: dict[str, Any]) -> bool:
    try:
        return _hash_body(doc) == doc["provenance"]["content_hash"]
    except (KeyError, TypeError):
        return False


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
_ANNOTATIONS = frozenset({"title", "description", "deprecated"})


def validate_v1_contract(
    doc: dict[str, Any],
    schema: dict[str, Any] | None = None,
) -> list[str]:
    schema = schema or load_schema()
    errors: list[str] = []
    _validate(doc, schema, schema, "$", errors)
    return errors


def _validation_errors(
    value: Any,
    node: dict[str, Any],
    root: dict[str, Any],
    path: str,
) -> list[str]:
    errors: list[str] = []
    _validate(value, node, root, path, errors)
    return errors


def _validate(
    value: Any,
    node: dict[str, Any],
    root: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    for key in node:
        if key.startswith("$") or key in _ANNOTATIONS:
            continue
        if key not in _SUPPORTED:
            errors.append(f"{path}: schema uses unsupported keyword {key}")

    if "const" in node and not _eq(value, node["const"]):
        errors.append(
            f"{path}: expected const {node['const']!r}, got {value!r}"
        )
    if "enum" in node and not any(_eq(value, item) for item in node["enum"]):
        errors.append(f"{path}: {value!r} is not one of {node['enum']}")

    if "anyOf" in node:
        if any(
            not _validation_errors(value, branch, root, path)
            for branch in node["anyOf"]
        ):
            return
        errors.append(f"{path}: value {value!r} matches none of the anyOf branches")
        return

    if "$ref" in node:
        _validate(value, _resolve_ref(node["$ref"], root), root, path, errors)
        return

    value_type = node.get("type")
    if value_type is not None and not _type_ok(
        value, value_type, path, errors
    ):
        return

    if isinstance(value, str):
        if "minLength" in node and len(value) < node["minLength"]:
            errors.append(f"{path}: shorter than minLength")
        if "maxLength" in node and len(value) > node["maxLength"]:
            errors.append(f"{path}: longer than maxLength")
        if "pattern" in node and re.search(node["pattern"], value) is None:
            errors.append(f"{path}: pattern mismatch")

        fmt = node.get("format")
        if fmt == "date" and not _is_date(value):
            errors.append(f"{path}: invalid date")
        elif fmt == "date-time" and not _is_datetime(value):
            errors.append(f"{path}: invalid date-time")
        elif fmt == "uri" and not _is_uri(value):
            errors.append(f"{path}: invalid uri")
        elif fmt not in (None, "date", "date-time", "uri"):
            errors.append(f"{path}: unsupported format {fmt}")

    if isinstance(value, list):
        if "minItems" in node and len(value) < node["minItems"]:
            errors.append(f"{path}: fewer than minItems")
        if isinstance(node.get("items"), dict):
            for index, item in enumerate(value):
                _validate(
                    item,
                    node["items"],
                    root,
                    f"{path}[{index}]",
                    errors,
                )

    if isinstance(value, dict):
        for name in node.get("required", []):
            if name not in value:
                errors.append(f"{path}: missing required property {name}")

        properties = node.get("properties", {})
        if node.get("additionalProperties") is False:
            for name in value:
                if name not in properties:
                    errors.append(f"{path}: unexpected property {name}")

        for name, subschema in properties.items():
            if name in value:
                _validate(
                    value[name],
                    subschema,
                    root,
                    f"{path}.{name}",
                    errors,
                )


def _resolve_ref(ref: str, root: dict[str, Any]) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"unsupported ref {ref!r}")
    node: Any = root
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def _eq(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    return left == right


def _type_ok(
    value: Any,
    value_type: str,
    path: str,
    errors: list[str],
) -> bool:
    checks = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "boolean": isinstance(value, bool),
        "null": value is None,
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
    }
    ok = checks.get(value_type)
    if ok is None:
        errors.append(f"{path}: unsupported type {value_type}")
        return False
    if not ok:
        errors.append(f"{path}: expected {value_type}")
        return False
    return True


def _is_date(value: str) -> bool:
    from datetime import date

    try:
        date.fromisoformat(value)
        return True
    except (ValueError, TypeError):
        return False


def _is_datetime(value: str) -> bool:
    from datetime import datetime

    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except (ValueError, TypeError):
        return False


def _is_uri(value: str) -> bool:
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", value))

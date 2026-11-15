"""Content-hash verification of evidence contracts, 1.x and 2.x (v0.19.0 P3).

Each contract version's rule, as ``docs/EVIDENCE_CONTRACT.md`` states it:

- **2.x** (``content_hash_method: jcs-sha256``): ``"sha256:" + hex(SHA-256(JCS(body)))``
  where the body is the document without ``signature``, ``signing_key_id``
  and ``trust_root``, and without ``provenance.content_hash`` and
  ``provenance.generation_timestamp``. JCS is RFC 8785. The same rule as
  ``conformance/evidence-contract/verify.mjs``.
- **1.x:** ``"sha256:" + hex(SHA-256(json.dumps(body, sort_keys=True,
  separators=(",", ":"))))`` where the body is the version's hashed fields
  (1.0: eleven; 1.1 adds ``inspection_coverage``; 1.2 adds
  ``verdict_meaning`` and ``evaluation_context``) with
  ``provenance.content_hash`` set to ``sha256:pending`` and
  ``provenance.generation_timestamp`` to ``1970-01-01T00:00:00Z``.

Standard library only: an independent reimplementation, not an import.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

# ---------------------------------------------------------------------------
# RFC 8785 JSON Canonicalization Scheme
# ---------------------------------------------------------------------------

_MAX_EXACT_INT = 2**53
_ESCAPES = {
    '"': '\\"',
    "\\": "\\\\",
    "\b": "\\b",
    "\f": "\\f",
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}


class CanonicalizationError(ValueError):
    """A value RFC 8785 cannot represent (NaN, a huge integer, a lone surrogate)."""


def _string(value: str) -> str:
    out = ['"']
    for ch in value:
        if ch in _ESCAPES:
            out.append(_ESCAPES[ch])
        elif ord(ch) < 0x20:
            out.append(f"\\u{ord(ch):04x}")
        elif 0xD800 <= ord(ch) <= 0xDFFF:
            raise CanonicalizationError("lone surrogate in string")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _number(value: float) -> str:
    """ECMAScript Number.prototype.toString for a finite double."""
    if math.isnan(value) or math.isinf(value):
        raise CanonicalizationError("NaN and infinities have no JSON form")
    if value == 0:
        return "0"
    sign = "-" if value < 0 else ""
    mantissa, _, exp = repr(abs(value)).partition("e")
    int_part, _, frac = mantissa.partition(".")
    digits = (int_part + frac).lstrip("0")
    if int_part.strip("0"):
        point = len(int_part.lstrip("0"))
    else:
        point = -(len(frac) - len(frac.lstrip("0")))
    n = point + (int(exp) if exp else 0)  # value = 0.digits x 10**n
    digits = digits.rstrip("0")
    k = len(digits)
    if k <= n <= 21:
        body = digits + "0" * (n - k)
    elif 0 < n <= 21:
        body = digits[:n] + "." + digits[n:]
    elif -6 < n <= 0:
        body = "0." + "0" * (-n) + digits
    else:
        e = n - 1
        fraction = "." + digits[1:] if k > 1 else ""
        body = digits[0] + fraction + "e" + ("+" if e > 0 else "-") + str(abs(e))
    return sign + body


def _write(value: Any, out: list[str]) -> None:
    if value is None:
        out.append("null")
    elif value is True:
        out.append("true")
    elif value is False:
        out.append("false")
    elif isinstance(value, int):
        if abs(value) > _MAX_EXACT_INT:
            raise CanonicalizationError(f"integer {value} is not exact as an IEEE 754 double")
        out.append(_number(float(value)))
    elif isinstance(value, float):
        out.append(_number(value))
    elif isinstance(value, str):
        out.append(_string(value))
    elif isinstance(value, list):
        out.append("[")
        for i, item in enumerate(value):
            if i:
                out.append(",")
            _write(item, out)
        out.append("]")
    elif isinstance(value, dict):
        out.append("{")
        for i, key in enumerate(
            sorted(value, key=lambda k: k.encode("utf-16-be", "surrogatepass"))
        ):
            if i:
                out.append(",")
            out.append(_string(key))
            out.append(":")
            _write(value[key], out)
        out.append("}")
    else:
        raise CanonicalizationError(f"{type(value).__name__} has no JSON form")


def canonicalize(value: Any) -> bytes:
    """The RFC 8785 canonical UTF-8 bytes of a JSON value."""
    out: list[str] = []
    _write(value, out)
    return "".join(out).encode("utf-8")


# ---------------------------------------------------------------------------
# The contract hash rules
# ---------------------------------------------------------------------------

_V2_UNHASHED_TOP = ("signature", "signing_key_id", "trust_root")
_V2_UNHASHED_PROVENANCE = ("content_hash", "generation_timestamp")
_V1_0_FIELDS = (
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
_V1_FIELDS = {
    "1.0.0": _V1_0_FIELDS,
    "1.1.0": (*_V1_0_FIELDS, "inspection_coverage"),
    "1.2.0": (*_V1_0_FIELDS, "inspection_coverage", "verdict_meaning", "evaluation_context"),
}
_V1_HASH_PLACEHOLDER = "sha256:pending"
_V1_TIMESTAMP_PLACEHOLDER = "1970-01-01T00:00:00Z"
CONTENT_HASH_METHOD = "jcs-sha256"


def v2_content_hash(doc: dict[str, Any]) -> str:
    body = {k: v for k, v in doc.items() if k not in _V2_UNHASHED_TOP}
    body["provenance"] = {
        k: v for k, v in doc["provenance"].items() if k not in _V2_UNHASHED_PROVENANCE
    }
    return "sha256:" + hashlib.sha256(canonicalize(body)).hexdigest()


def v1_content_hash(doc: dict[str, Any]) -> str:
    fields = _V1_FIELDS[doc["contract_version"]]
    body = {name: doc[name] for name in fields}
    body["provenance"] = dict(body["provenance"])
    body["provenance"]["content_hash"] = _V1_HASH_PLACEHOLDER
    body["provenance"]["generation_timestamp"] = _V1_TIMESTAMP_PLACEHOLDER
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def hash_problem(doc: dict[str, Any]) -> str | None:
    """Why the document's content hash does not hold, or None when it does.

    Expects a document that already validated against its schema (so the
    fields the rule reads are present and typed).
    """
    version = str(doc.get("contract_version"))
    stated = doc["provenance"].get("content_hash")
    try:
        if version.startswith("2."):
            method = doc["provenance"].get("content_hash_method")
            if method != CONTENT_HASH_METHOD:
                return f"content_hash_method is {method!r}, not {CONTENT_HASH_METHOD!r}"
            computed = v2_content_hash(doc)
        elif version in _V1_FIELDS:
            computed = v1_content_hash(doc)
        else:
            return f"no hash rule for contract {version}"
    except CanonicalizationError as exc:
        return f"cannot canonicalize the document: {exc}"
    if computed != stated:
        return "does not match the document: it was changed after it was hashed"
    return None


__all__ = [
    "CONTENT_HASH_METHOD",
    "CanonicalizationError",
    "canonicalize",
    "hash_problem",
    "v1_content_hash",
    "v2_content_hash",
]

"""RFC 8785 JSON Canonicalization Scheme (JCS), stdlib only.

The evidence contract's 2.0.0 content hash is SHA-256 over the JCS form
of the document (``core.evidence_contract``), so any consumer with a JCS
library recomputes it without OpenPulse's own serializer. JCS fixes what
``json.dumps(sort_keys=True)`` leaves to the implementation:

- object members sorted by their names' UTF-16 code units, not by
  Python's code-point order (they differ above U+FFFF);
- numbers serialized as ECMAScript ``Number.prototype.toString`` does
  (shortest round-trip digits, ``1e+21``, never ``1.0``);
- strings escaped as ECMAScript ``JSON.stringify`` does: only ``"``,
  ``\\`` and control characters, with lowercase ``\\u00xx``.

Rejected, because JCS cannot represent them: NaN and infinities,
integers beyond 2**53 in magnitude (not exact as IEEE 754 doubles), lone
surrogates, non-string object keys, and any other Python type.
"""

from __future__ import annotations

import math
from typing import Any

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


class JCSError(ValueError):
    """A value that RFC 8785 cannot canonicalize."""


def _string(value: str) -> str:
    out = ['"']
    for ch in value:
        if ch in _ESCAPES:
            out.append(_ESCAPES[ch])
        elif ord(ch) < 0x20:
            out.append(f"\\u{ord(ch):04x}")
        elif 0xD800 <= ord(ch) <= 0xDFFF:
            raise JCSError("lone surrogate in string")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _number(value: float) -> str:
    """ECMAScript Number.prototype.toString for a finite double."""
    if math.isnan(value) or math.isinf(value):
        raise JCSError("NaN and infinities have no JSON form")
    if value == 0:
        return "0"  # also -0
    sign = "-" if value < 0 else ""
    # repr gives the shortest round-trip digits; take them apart.
    mantissa, _, exp = repr(abs(value)).partition("e")
    int_part, _, frac = mantissa.partition(".")
    digits = (int_part + frac).lstrip("0")
    point = (
        len(int_part.lstrip("0")) if int_part.strip("0") else -(len(frac) - len(frac.lstrip("0")))
    )
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
        body = (
            digits[0]
            + ("." + digits[1:] if k > 1 else "")
            + "e"
            + ("+" if e > 0 else "-")
            + str(abs(e))
        )
    return sign + body


def _utf16_key(name: str) -> bytes:
    return name.encode("utf-16-be", "surrogatepass")


def _write(value: Any, out: list[str]) -> None:
    if value is None:
        out.append("null")
    elif value is True:
        out.append("true")
    elif value is False:
        out.append("false")
    elif isinstance(value, int):
        if abs(value) > _MAX_EXACT_INT:
            raise JCSError(f"integer {value} is not exact as an IEEE 754 double")
        out.append(_number(float(value)))
    elif isinstance(value, float):
        out.append(_number(value))
    elif isinstance(value, str):
        out.append(_string(value))
    elif isinstance(value, (list, tuple)):
        out.append("[")
        for i, item in enumerate(value):
            if i:
                out.append(",")
            _write(item, out)
        out.append("]")
    elif isinstance(value, dict):
        if any(not isinstance(k, str) for k in value):
            raise JCSError("object keys must be strings")
        out.append("{")
        for i, key in enumerate(sorted(value, key=_utf16_key)):
            if i:
                out.append(",")
            out.append(_string(key))
            out.append(":")
            _write(value[key], out)
        out.append("}")
    else:
        raise JCSError(f"{type(value).__name__} has no JSON form")


def canonicalize(value: Any) -> bytes:
    """The RFC 8785 canonical UTF-8 bytes of a JSON value."""
    out: list[str] = []
    _write(value, out)
    return "".join(out).encode("utf-8")

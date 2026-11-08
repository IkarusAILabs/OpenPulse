"""Schema validation of evidence contract documents.

Every published schema (``schemas/<dir>/schema.json``, copied byte for byte
from OpenPulse's ``schemas/evidence-contract/``) names the one contract
version it describes in ``properties.contract_version.const``. A document is
validated against the schema of the version it declares, and only that one
(v0.19.0 P2):

- a version with no published schema (``2.9.0``, ``2.4``, ``v2.4.0``) is not
  a contract this package can read;
- ``provenance.contract_version`` must be the top-level version;
- where a schema is closed (``additionalProperties: false``), an unknown
  field fails;
- the three formats the schemas use are checked as OpenPulse checks them
  (``date``, ``date-time``: the standard library's ISO 8601 parsers;
  ``uri``: a scheme), with the standard library only, so the result never
  depends on which optional ``jsonschema`` format packages are installed.
"""

from __future__ import annotations

import functools
import json
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date, datetime
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

#: A JSONL file of contracts larger than this is refused, not read.
MAX_DOCUMENTS_BYTES = 64 * 1024 * 1024


@functools.cache
def schemas() -> dict[str, dict[str, Any]]:
    """{contract version: its published schema}, from the bundled files."""
    root = resources.files("openpulse_consumer") / "schemas"
    found: dict[str, dict[str, Any]] = {}
    for directory in sorted(root.iterdir(), key=lambda p: p.name):
        path = directory / "schema.json"
        if not path.is_file():
            continue
        schema = json.loads(path.read_text(encoding="utf-8"))
        version = schema["properties"]["contract_version"]["const"]
        if version in found:
            raise RuntimeError(f"two bundled schemas describe contract {version}")
        found[version] = schema
    return found


def supported_versions() -> list[str]:
    """The contract versions with a published schema, oldest first."""
    return sorted(schemas(), key=lambda v: tuple(int(p) for p in v.split(".")))


#: OpenPulse's own format rules (core.evidence_contract), and no others.
FORMATS = FormatChecker(formats=())


@FORMATS.checks("date")
def _is_date(value: object) -> bool:
    if not isinstance(value, str):
        return True  # format applies to strings; the type keyword judges the rest
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


@FORMATS.checks("date-time")
def _is_datetime(value: object) -> bool:
    if not isinstance(value, str):
        return True
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


@FORMATS.checks("uri")
def _is_uri(value: object) -> bool:
    """An absolute URI: a scheme (RFC 3986: a letter, then letters, digits, + . -)."""
    return not isinstance(value, str) or _SCHEME.match(value) is not None


_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


@functools.cache
def _validator(version: str) -> Draft202012Validator:
    schema = schemas()[version]
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FORMATS)


@dataclass
class Check:
    """One document's result: the version it declares, and why it is invalid."""

    version: str | None
    errors: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors


def _where(path: Any) -> str:
    return "$" + "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in path)


def check(doc: Any) -> Check:
    """Validate one parsed document against the schema of its declared version."""
    if not isinstance(doc, dict):
        return Check(None, ["$: a contract is a JSON object"])
    version = doc.get("contract_version")
    if not isinstance(version, str):
        return Check(None, ["$.contract_version: missing or not a string"])
    if version not in schemas():
        supported = ", ".join(supported_versions())
        return Check(
            version, [f"$.contract_version: no published schema for {version!r} ({supported})"]
        )
    found = sorted(
        _validator(version).iter_errors(doc), key=lambda e: (_where(e.absolute_path), e.message)
    )
    errors = [f"{_where(e.absolute_path)}: {e.message}" for e in found]
    provenance = doc.get("provenance")
    stated = provenance.get("contract_version") if isinstance(provenance, dict) else None
    if stated is not None and stated != version:
        errors.insert(
            0,
            f"$.provenance.contract_version: {stated!r} differs from the top-level "
            f"contract_version {version!r}",
        )
    return Check(version, errors)


def read_jsonl(path: str | Path) -> Iterator[tuple[int, Any]]:
    """(line number, parsed document) for every non-blank line of a JSONL file.

    A line that is not JSON yields ``(line, None)``; the caller reports it.
    ValueError for a file over ``MAX_DOCUMENTS_BYTES`` or not UTF-8.
    """
    target = Path(path)
    if target.stat().st_size > MAX_DOCUMENTS_BYTES:
        raise ValueError(f"{target}: larger than {MAX_DOCUMENTS_BYTES} bytes")
    try:
        text = target.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{target}: not UTF-8") from exc
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            yield number, json.loads(line)
        except ValueError:
            yield number, None

"""Deterministic SBOM of the locked dependency set (CycloneDX 1.5, minimal).

Threat: unlisted transitive dependencies reaching users — the SBOM
enumerates exactly what requirements.lock pins, nothing detected at
runtime. Deterministic by construction: the serial number derives
from the lock content, so identical locks produce identical SBOMs.
The serial is an RFC 4122 UUIDv5 URN, as CycloneDX requires. stdlib only.

Usage: python scripts/gen_sbom.py [LOCK [OUT]]  (defaults: requirements.lock, sbom.json)
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import uuid
from pathlib import Path

_PIN = re.compile(r"^([A-Za-z0-9_.\-]+)==([^\s;#]+)")

#: OpenPulse's own UUIDv5 namespace for SBOM serial numbers, derived once
#: from the project's domain. Hashing the lock digest under it keeps
#: OpenPulse serials disjoint from names hashed under the standard
#: namespaces (NAMESPACE_URL is meant for URLs, not lock digests).
_SERIAL_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "openpulse.ikaruslabs.net")


def serial_number(lock_digest: str) -> str:
    """Deterministic CycloneDX serialNumber (urn:uuid) for one lock digest."""
    return f"urn:uuid:{uuid.uuid5(_SERIAL_NAMESPACE, lock_digest)}"


def build(lock_path: str = "requirements.lock") -> dict:
    text = Path(lock_path).read_text(encoding="utf-8")
    components = []
    for line in text.splitlines():
        match = _PIN.match(line.strip())
        if match:
            components.append(
                {
                    "type": "library",
                    "name": match.group(1),
                    "version": match.group(2),
                    "purl": f"pkg:pypi/{match.group(1).lower()}@{match.group(2)}",
                }
            )
    components.sort(key=lambda c: c["name"].lower())
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": serial_number(digest),
        "version": 1,
        "metadata": {"component": {"type": "application", "name": "openpulse"}},
        "components": components,
    }


def main(argv: list[str] | None = None) -> int:
    # argv[1] is the lock: it used to be ignored, so `gen_sbom.py other.lock
    # out.json` silently described requirements.lock instead.
    args = sys.argv[1:] if argv is None else argv
    lock = args[0] if args else "requirements.lock"
    out = Path(args[1] if len(args) > 1 else "sbom.json")
    sbom = build(lock)
    out.write_text(json.dumps(sbom, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} from {lock} ({len(sbom['components'])} components)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

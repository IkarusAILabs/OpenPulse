"""Deterministic SBOM of the locked dependency set (CycloneDX 1.5, minimal).

Threat: unlisted transitive dependencies reaching users — the SBOM
enumerates exactly what requirements.lock pins, nothing detected at
runtime. Deterministic by construction: the serial number derives
from the lock content, so identical locks produce identical SBOMs.
stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

_PIN = re.compile(r"^([A-Za-z0-9_.\-]+)==([^\s;#]+)")


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
        "serialNumber": f"urn:uuid:openpulse-lock-{digest[:32]}",
        "version": 1,
        "metadata": {"component": {"type": "application", "name": "openpulse"}},
        "components": components,
    }


def main() -> int:
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "sbom.json")
    out.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(build()['components'])} components)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

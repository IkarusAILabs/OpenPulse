"""A stand-in comparator bridge speaking the bridges' JSON-lines protocol.

Used by tests/test_ecosystem_versions.py to exercise the adapter where no
Node, Go or JDK toolchain is installed. It reports the library and version
given in FAKE_LIBRARY / FAKE_VERSION, and parses `[v]N(.N)*[-x]` versions;
FAKE_TRIM=1 drops trailing zero items, as Maven's ComparableVersion does.
"""

import json
import os
import re
import sys

LIBRARY = os.environ.get("FAKE_LIBRARY", "semver")
VERSION = os.environ.get("FAKE_VERSION", "7.8.5")
TRIM = os.environ.get("FAKE_TRIM") == "1"
GRAMMAR = re.compile(r"v?(\d+(?:\.\d+)*)(-[0-9A-Za-z.-]+)?")


def parse(v):
    m = GRAMMAR.fullmatch(v or "")
    if not m:
        return {"valid": False}
    core = [int(n) for n in m.group(1).split(".")]
    while TRIM and len(core) > 1 and core[-1] == 0:
        core.pop()
    return {"valid": True, "core": core, "prerelease": bool(m.group(2)), "canonical": v}


for line in sys.stdin:
    req = json.loads(line)
    if req["op"] == "version":
        body = {"library": LIBRARY, "version": VERSION}
    elif req["op"] == "parse":
        body = parse(req["v"])
    else:
        a, b = parse(req["a"]), parse(req["b"])
        body = {
            "cmp": None
            if not (a["valid"] and b["valid"])
            else (a["core"] > b["core"]) - (a["core"] < b["core"])
        }
    sys.stdout.write(json.dumps({"id": req["id"], **body}) + "\n")
    sys.stdout.flush()

"""Pinned ecosystem version comparators for baseline V (REGISTRATION.md §9).

Baseline V decides release-line membership with each ecosystem's own
reference implementation, not with a re-implementation:

    npm    node-semver      evaluation/comparators/npm/bridge.js
    Go     x/mod/semver     evaluation/comparators/go/main.go
    Maven  ComparableVersion evaluation/comparators/maven/Bridge.java

(PyPI uses ``packaging`` in-process.) Each bridge is a long-running
process that speaks JSON lines; it is started once per run and asked to
parse versions. A bridge must report exactly the pinned library version
(PINS) or it is not used. ``Comparators(required=True)``, which the
registered run uses, refuses to start unless every bridge is present
and pinned; a development run proceeds and records what was missing.

Release-line membership follows the specification's release rule: a
version is in line L when L's numbers are a prefix of the version's
release core, zero-padded. A pre-release belongs to its own core's line
(6.2.0-rc.1 is in 6.2), unlike npm's `satisfies`, which excludes it.
"""

from __future__ import annotations

import atexit
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent / "comparators"

#: The frozen pins (REGISTRATION.md freeze table). A bridge reporting any
#: other version is refused.
PINS = {
    "npm": {"library": "semver", "version": "7.8.5"},
    "go": {"library": "golang.org/x/mod", "version": "v0.42.0"},
    "maven": {"library": "org.apache.maven:maven-artifact", "version": "3.9.16"},
}
MAVEN_JAR = HERE / "maven" / "lib" / "maven-artifact-3.9.16.jar"
_LINE = re.compile(r"\d+(?:\.\d+)*")


class ComparatorUnavailable(RuntimeError):
    """A required pinned comparator is missing or reports another version."""


def default_command(name: str) -> tuple[list[str], Path] | None:
    """(argv, cwd) for one bridge, or None when its toolchain is absent.

    ``OPENPULSE_COMPARATOR_<NAME>`` may hold a JSON argv to override it.
    """
    override = os.environ.get(f"OPENPULSE_COMPARATOR_{name.upper()}")
    if override:
        return json.loads(override), HERE / name
    if name == "npm":
        node = shutil.which("node")
        if node and (HERE / "npm" / "node_modules" / "semver").is_dir():
            return [node, "bridge.js"], HERE / "npm"
    elif name == "go":
        for binary in (HERE / "go" / "bridge", HERE / "go" / "bridge.exe"):
            if binary.is_file():
                return [str(binary)], HERE / "go"
    elif name == "maven":
        java = shutil.which("java")
        if java and MAVEN_JAR.is_file():
            return [java, "-cp", str(MAVEN_JAR), "Bridge.java"], HERE / "maven"
    return None


class Bridge:
    """One running bridge process."""

    def __init__(self, name: str, argv: list[str], cwd: Path):
        self.name = name
        self._next = 0
        self._proc = subprocess.Popen(
            argv,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        self._cache: dict[str, dict[str, Any]] = {}
        self.reported = self.call({"op": "version"})

    def call(self, request: dict[str, Any]) -> dict[str, Any]:
        self._next += 1
        request = {**request, "id": self._next}
        assert self._proc.stdin is not None and self._proc.stdout is not None
        self._proc.stdin.write(json.dumps(request) + "\n")
        self._proc.stdin.flush()
        line = self._proc.stdout.readline()
        if not line:
            raise ComparatorUnavailable(f"{self.name} bridge exited")
        response = json.loads(line)
        if response.get("id") != self._next or "error" in response:
            raise ComparatorUnavailable(f"{self.name} bridge: bad response {response!r}")
        return response

    def parse(self, version: str) -> dict[str, Any]:
        if version not in self._cache:
            self._cache[version] = self.call({"op": "parse", "v": version})
        return self._cache[version]

    def compare(self, a: str, b: str) -> int | None:
        return self.call({"op": "compare", "a": a, "b": b})["cmp"]

    def close(self) -> None:
        if self._proc.poll() is None:
            assert self._proc.stdin is not None
            self._proc.stdin.close()
            try:
                self._proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._proc.kill()


class Comparators:
    """The pinned bridges of one run, with their status recorded."""

    def __init__(self, required: bool = False, names: tuple[str, ...] = tuple(PINS)):
        self.bridges: dict[str, Bridge] = {}
        self.status: dict[str, dict[str, Any]] = {}
        for name in names:
            pin = PINS[name]
            entry: dict[str, Any] = {"pinned": pin, "available": False}
            command = default_command(name)
            if command is None:
                entry["error"] = "toolchain or pinned library not installed"
            else:
                try:
                    bridge = Bridge(name, *command)
                except (OSError, ComparatorUnavailable, json.JSONDecodeError) as exc:
                    entry["error"] = f"bridge failed to start: {exc}"
                else:
                    entry["reported"] = {
                        "library": bridge.reported.get("library"),
                        "version": bridge.reported.get("version"),
                    }
                    if entry["reported"] == pin:
                        entry["available"] = True
                        self.bridges[name] = bridge
                    else:
                        entry["error"] = "reported library or version differs from the pin"
                        bridge.close()
            self.status[name] = entry
        atexit.register(self.close)
        if required and not self.complete:
            missing = {n: s.get("error") for n, s in self.status.items() if not s["available"]}
            self.close()
            raise ComparatorUnavailable(f"pinned comparators required but unavailable: {missing}")

    @property
    def complete(self) -> bool:
        return all(entry["available"] for entry in self.status.values())

    def supports(self, ecosystem: str) -> bool:
        return _bridge_name(ecosystem) in self.bridges

    def release_core(self, ecosystem: str, version: str) -> list[int] | None:
        """The version's release core per the ecosystem's tool, or None."""
        name = _bridge_name(ecosystem)
        bridge = self.bridges.get(name or "")
        if bridge is None:
            return None
        if name == "go" and not version.startswith("v"):
            version = "v" + version  # OSV and some inventories omit Go's prefix
        parsed = bridge.parse(version)
        if not parsed.get("valid"):
            return None
        return [int(n) for n in parsed["core"]]

    def compare(self, ecosystem: str, a: str, b: str) -> int | None:
        """-1, 0 or 1 per the ecosystem's tool; None when either is not a version."""
        name = _bridge_name(ecosystem)
        bridge = self.bridges.get(name or "")
        if bridge is None:
            return None
        if name == "go":
            a, b = (v if v.startswith("v") else "v" + v for v in (a, b))
        return bridge.compare(a, b)

    def in_line(self, ecosystem: str, version: str, line: str) -> bool | None:
        """Is ``version`` in release line ``line``? None when not decidable."""
        if not _LINE.fullmatch(line or ""):
            return None
        core = self.release_core(ecosystem, version)
        if core is None:
            return None
        prefix = [int(n) for n in line.split(".")]
        core = core + [0] * max(0, len(prefix) - len(core))  # Maven trims trailing zeros
        return core[: len(prefix)] == prefix

    def close(self) -> None:
        for bridge in self.bridges.values():
            bridge.close()
        self.bridges = {}


def _bridge_name(ecosystem: str) -> str | None:
    return {"npm": "npm", "go": "go", "golang": "go", "maven": "maven"}.get(
        str(ecosystem or "").strip().lower()
    )

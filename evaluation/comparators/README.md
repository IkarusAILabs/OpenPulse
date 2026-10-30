# Pinned ecosystem comparators for baseline V

Baseline V (`evaluation/strong_baseline.py`) decides release-line membership with each ecosystem's **own reference implementation**, never with a re-implementation. TR-2026-01 §10 requires this, and D8 and D11 are why: re-implementations drift from the ecosystem's ordering.

| Ecosystem | Reference implementation | Pin | Bridge |
|---|---|---|---|
| PyPI | `packaging` | the hash-locked `requirements.lock` | in-process |
| npm | node-semver | `semver` **7.8.5**: `npm/package-lock.json`, sha512 integrity | `npm/bridge.js` (Node **24.22.0**) |
| Go | `golang.org/x/mod/semver` | **v0.42.0**: `go/go.sum` (from sum.golang.org) | `go/main.go` (Go **1.26**, toolchain go1.26.10) |
| Maven | `ComparableVersion` | `org.apache.maven:maven-artifact` **3.9.16**: SHA-256 in `maven/fetch.py` | `maven/Bridge.java` (Temurin **25**, source-file mode) |

Debian (`dpkg`) is **out of scope**. OpenPulse's readers ingest no OS packages (`pkg:deb`), so baseline V never meets a Debian-ecosystem version (REGISTRATION.md §13).

## Install, then run

```bash
npm_config_ignore_scripts=true npm ci --prefix evaluation/comparators/npm
```

```bash
cd evaluation/comparators/go && go build -mod=readonly -trimpath -o bridge .
```

```bash
python evaluation/comparators/maven/fetch.py
```

```bash
python evaluation/run.py --require-comparators
```

`--require-comparators` is the registered run's setting. It refuses to start unless every bridge is present and reports exactly its pinned library version. Without the flag, a development run proceeds. V then falls back to plain dotted numbers, the results file records `comparators.complete: false`, and the registered result is marked invalid.

## Protocol

Each bridge is a long-running process. It reads one JSON request per line and writes one response per line:

| Request | Response |
|---|---|
| `{"id": 1, "op": "version"}` | `{"id": 1, "library": "...", "version": "..."}` |
| `{"id": 2, "op": "parse", "v": "..."}` | `{"id": 2, "valid": true, "core": [1, 2, 3], "prerelease": false, "canonical": "..."}` |
| `{"id": 3, "op": "compare", "a": "...", "b": "..."}` | `{"id": 3, "cmp": -1}` (or 0, 1, `null` when either side is invalid) |

The Python adapter is `evaluation/ecosystem_versions.py`. `OPENPULSE_COMPARATOR_<NAME>` may hold a JSON argv to run a bridge some other way; the tests use this with a stand-in.

## Release-line rule (the specification's, applied to each tool's parse)

A version is in line `L` when `L`'s numbers are a prefix of the version's **release core**, zero-padded. A pre-release belongs to its own core's line.

| Ecosystem | Valid | Release core | Notes |
|---|---|---|---|
| npm | `semver.parse` in strict mode; never `loose` or `coerce` (coerce invents versions) | major, minor, patch | `6.2.0-rc.1` is in line 6.2. npm's own `satisfies("6.2.0-rc.1", "6.2.x")` is false, because ranges exclude pre-releases. V follows the specification instead (a recorded design choice). |
| Go | `semver.IsValid`; the adapter adds a missing `v`, as OSV omits it | from `semver.Canonical`, without pre-release and build | `+incompatible` is build metadata; a pseudo-version sits in its base version's line |
| Maven | ComparableVersion accepts every string, so V's rule is that the canonical form must start with a numeric item | the numeric items before the first sub-list (`-`) | trailing zeros are trimmed (`1.0.0` → `1`), hence the zero-padding; `LATEST`, `RELEASE` and `${…}` are undecidable |

## Tests and the cross-check

- **`tests/test_ecosystem_versions.py`:** tests the adapter with a stand-in bridge on every machine: handshake, refusal of a wrong version, fail-closed required mode, the release-line rule and zero-padding.
- **`tests/test_ecosystem_comparators.py`:** runs the real bridges against documented semantics. It skips without toolchains. In CI's `comparators` job, `OPENPULSE_REQUIRE_COMPARATORS=1` turns every skip into a failure.
- **`crosscheck.py`:** compares OpenPulse's own `core.versions.compare` and `in_release_line` against the reference tools, over a corpus of release cores and pre-release and qualifier forms. Each pair is classified as agree, OpenPulse abstains, OpenPulse decides where the reference rejects, or disagree. It exits non-zero on any disagreement: a candidate defect of the D8 or D11 kind, to be fixed in its own PR. The report is a CI artifact (`ecosystem-comparators`).

# ruff: noqa: E501  (label rules: one rationale per line)
"""Build the retrospective case file with labeller L1's labels (DESIGN.md §5-6).

Run from the repository root:

    python evaluation/retrospective/build_cases.py

Reads the verified references in ``dependents/*.json`` and the fixtures in
``events/``. Writes:

- ``cases/retro-2026-11.draft.json``: every pair with L1's label, rationale
  and source. It becomes the frozen case file only after L2's sample is
  labelled and adjudicated (DESIGN §6-7);
- ``labelling/L2-sample.json``: the seeded 25% sample (seed 20261101, at
  least one pair per event);
- ``labelling/L2-packet.jsonl``: those pairs WITHOUT labels, for L2.

No policy is run (X3): the script only writes labels and validates the
file's format with ``run.validate``.

Dependencies are written as OpenPulse's inventory readers produce them:
container images as image references; npm and Go dependencies as
packages with their ecosystem and resolved version; repository URLs as
source-repository references. Go import paths from Godeps or vendor.json
(for which OpenPulse has no reader) are reduced to their module root.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "evaluation"))

import run  # noqa: E402  (format validation only)

SAMPLE_SEED = 20261101
EVENT_CLASS = {
    "REL": "relocation", "DEP": "deprecation", "DIS": "distribution",
    "LIC": "licence", "EOL": "eol", "CMP": "compromised",
}
DELETED = {
    line.split(":", 1)[1]
    for line in (HERE / "evidence" / "openjdk-2025-deleted-tags.txt").read_text("utf-8").splitlines()
    if line.startswith("openjdk:")
}


def module_root(path: str) -> str:
    """github.com/owner/repo/sub/pkg -> github.com/owner/repo; others unchanged."""
    parts = path.split("/")
    return "/".join(parts[:3]) if parts[0] == "github.com" else path


def host(ref: str) -> str:
    """The first segment of a reference: its registry or code host."""
    return ref.split("/", 1)[0]


def dependency(r: dict) -> dict:
    ref, kind, version = r["reference"], r["kind"], r.get("version")
    if kind == "image":
        return {"kind": "image", "ref": ref}
    if kind == "npm":
        return {"kind": "package", "package": ref, "ecosystem": "npm", "version": version}
    if kind == "go-module":
        return {"kind": "package", "package": module_root(ref), "ecosystem": "Go", "version": version}
    if kind == "repository":
        return {"kind": "image", "ref": ref.removeprefix("https://")}
    if kind == "tool-use":
        # A project's use of a tool has no reference form (SOURCES.md, DEP-2):
        # it is represented by the tool's repository path.
        if host(ref) == "github.com":
            return {"kind": "package", "package": module_root(ref), "ecosystem": "Go", "version": None}
        tool = "github.com/tools/godep" if "godep" in ref else "github.com/golang/dep"
        return {"kind": "image", "ref": tool}
    raise ValueError(kind)


# --- L1's labelling rules, one per event, from the primary source ----------
IN, OUT, UND = "in_scope", "out_of_scope", "undeterminable"


def label(event: str, r: dict) -> tuple[str, str]:
    ref, version = r["reference"], str(r.get("version") or "")
    tag = ref.rsplit(":", 1)[1].split("@")[0] if ":" in ref.split("/")[-1] else ""
    if event in ("REL-1", "REL-3", "REL-4"):
        old = {"REL-1": "github.com/docker/docker", "REL-3": "github.com/docker/distribution", "REL-4": "github.com/coreos/prometheus-operator"}[event]
        if module_root(ref.removeprefix("https://")) == old:
            return IN, f"Names the relocated repository path {old}; it now resolves only through the redirect or the module proxy (relocation scope, TR-2026-01 §1)."
        if host(ref) == "quay.io":
            return OUT, "A container image on quay.io, not the relocated GitHub repository; images kept being pushed to the old organisation."
        return OUT, f"Not a reference to {old}: the new location or a different project."
    if event == "DEP-1":
        if ref == "request":
            return IN, "The npm package request; the README and the registry deprecate every version."
        return OUT, f"{ref} is a different npm package; the deprecation is of request itself."
    if event == "DEP-2":
        if "godep" in ref or "Godeps" in ref:
            return OUT, "godep is a different tool; the deprecation is of golang/dep."
        return IN, "The project uses the dep tool (Gopkg manifest or install), which is deprecated and archived."
    if event == "DEP-3":
        if ref == "tslint":
            return IN, f"tslint {version}: the announcement deprecates the whole project (the registry flags only 6.x; the announcing source defines the scope)."
        return OUT, f"{ref} is a different package."
    if event == "DEP-4":
        if ref == "node-sass":
            return IN, "node-sass: every version is deprecated and the repository archived."
        return OUT, f"{ref} is the recommended replacement, a different package."
    if event == "DEP-5":
        if ref.startswith("gopkg.in/yaml."):
            return IN, f"{ref} is published from go-yaml/yaml, declared unmaintained and archived."
        return OUT, f"{ref} is a different module (a wrapper, fork or other library), not go-yaml/yaml."
    if event == "DEP-6":
        if ref in ("golang.org/x/lint", "github.com/golang/lint/golint") or ref.startswith("golang.org/x/lint"):
            return IN, "golint (golang.org/x/lint, formerly imported as github.com/golang/lint), frozen and deprecated by the accepted proposal."
        return OUT, f"{ref} is a different linter."
    if event == "DIS-1":
        if host(ref) == "k8s.gcr.io":
            return IN, "An image on k8s.gcr.io: 'ALL images on k8s.gcr.io will be impacted' (redirect, then freeze)."
        return OUT, "Not on k8s.gcr.io: the new registry or another host."
    if event == "DIS-2":
        if ref.split(":")[0] in ("openjdk", "docker.io/library/openjdk", "library/openjdk"):
            if "-ea" in tag:
                return OUT, f"openjdk:{tag} is an Early Access tag, which the notice excludes."
            return IN, f"openjdk:{tag}, a non-EA tag of the deprecated official image."
        return OUT, "A different image (another namespace or a successor)."
    if event == "DIS-3":
        if ref.split(":")[0] in ("openjdk", "library/openjdk", "docker.io/library/openjdk"):
            if tag in DELETED:
                return IN, f"openjdk:{tag} is in the published list of 1,051 deleted tags."
            return OUT, f"openjdk:{tag} is not in the deleted-tag list: an explicit version that was kept."
        return OUT, "A different image."
    if event == "DIS-4":
        if ref.split(":")[0] in ("centos", "docker.io/library/centos"):
            return IN, f"centos:{tag}, a tag of the deprecated official image ('All tags of this image are EOL')."
        return OUT, "A different image (quay.io CentOS Stream or another distribution)."
    if event == "DIS-5":
        if ref.split(":")[0] in ("adoptopenjdk", "docker.io/library/adoptopenjdk"):
            return IN, f"adoptopenjdk:{tag}, a tag of the deprecated official image."
        return OUT, "A different image: the non-official adoptopenjdk/* namespace or the successor."
    if event == "DIS-6":
        if ref.split(":")[0] in ("java", "docker.io/library/java"):
            return IN, f"java:{tag}, a tag of the deprecated official image."
        return OUT, "A different image (another namespace)."
    if event == "LIC-1":
        major, minor = (int(x) for x in version.split(".")[:2])
        if (major, minor) >= (7, 11):
            return IN, f"Elasticsearch/Kibana {version} >= 7.11, under the dual SSPL / Elastic License."
        return OUT, f"{version} < 7.11, still Apache-2.0 at the default level."
    if event == "LIC-2":
        if "opentofu" in ref:
            return OUT, "OpenTofu is a different project (the MPL fork)."
        major, minor = (int(x) for x in version.split(".")[:2])
        if (major, minor) >= (1, 6):
            return IN, f"Terraform {version} >= 1.6.0, under BSL 1.1 (tag LICENSE)."
        return OUT, f"Terraform {version} <= 1.5.7, MPL-2.0 (tag LICENSE)."
    if event == "LIC-3":
        if int(version.split(".")[0]) >= 8:
            return IN, f"Grafana {version} >= 8.0.0, AGPLv3 (tag LICENSE)."
        return OUT, f"Grafana {version} < 8.0.0, Apache-2.0 (tag LICENSE)."
    if event == "LIC-4":
        if version == "4.0.4":
            return IN, "MongoDB 4.0.4 was tagged on 2018-11-06, after 2018-10-16, so it is under the SSPL (evidence/mongodb-release-tags.txt)."
        if version != "4.0.2":
            raise ValueError(f"LIC-4: no archived release date for MongoDB {version}")
        return OUT, f"MongoDB {version} was tagged on 2018-08-27, before 2018-10-16, so it stays under the AGPL (evidence/mongodb-release-tags.txt)."
    if event == "EOL-1":
        if ref.startswith("circleci/"):
            return UND, "A CircleCI convenience image that ships Python 2.7: a downstream distribution, whose support the upstream end of life does not settle (TR §5.1)."
        if version.startswith("2.7"):
            return IN, f"python:{tag}, Python 2.7, end of life on 2020-01-01."
        return OUT, f"python:{tag} is Python 3."
    if event == "EOL-2":
        if ref.split(":")[0] in ("centos", "docker.io/library/centos") and (tag == "8" or tag.startswith("8.") or tag.startswith("centos8")):
            return IN, f"centos:{tag}, CentOS Linux 8, end of life on 2021-12-31."
        return OUT, "Not CentOS Linux 8: CentOS Stream 8 or CentOS Linux 7, which the announcement excludes."
    if event == "EOL-3":
        if ref.startswith("circleci/"):
            return UND, "A CircleCI convenience image that ships Node.js 12: a downstream distribution (TR §5.1)."
        if version.split("-")[0] == "12":
            return IN, f"node:{tag}, Node.js 12, end of life on 2022-04-30."
        return OUT, f"node:{tag} is a supported line."
    if event == "CMP-1":
        if ref == "colors" and version in ("1.4.1", "1.4.2", "1.4.44-liberty-2"):
            return IN, f"colors {version} is in both advisories' affected set."
        return OUT, f"{ref} {version} is outside both advisories (1.4.0, or the @colors/colors fork)."
    if event == "CMP-2":
        if ref == "faker" and version == "6.6.6":
            return IN, "faker 6.6.6, the sabotaged version."
        return OUT, f"{ref} {version} is not faker 6.6.6."
    if event == "CMP-3":
        if ref == "node-ipc" and (version in ("10.1.1", "10.1.2", "9.2.2") or version.startswith("11.")):
            return IN, f"node-ipc {version} is in an advisory's affected range."
        return OUT, f"{ref} {version} is outside every advisory's range."
    if event == "CMP-4":
        if ref == "ua-parser-js" and version in ("0.7.29", "0.8.0", "1.0.0"):
            return IN, f"ua-parser-js {version}, a hijacked version."
        return OUT, f"ua-parser-js {version} is not a hijacked version."
    if event == "CMP-5":
        if ref == "event-stream" and version == "3.3.6":
            return IN, "event-stream 3.3.6, which pulled in flatmap-stream 0.1.1."
        return OUT, f"event-stream {version} does not depend on flatmap-stream."
    raise ValueError(event)


def main() -> int:
    groups = [json.loads(p.read_text("utf-8")) for p in sorted((HERE / "dependents").glob("*.json"))]
    events, cases = {}, []
    for group in groups:
        for block in group["events"]:
            eid = block["event"]
            fixture = json.loads((HERE / "events" / eid / "event.json").read_text("utf-8"))
            newest = max(e["source"]["fetched_at"] for e in fixture["evidences"])
            events[eid] = {
                "source": "event",
                "fixture": f"../../evaluation/retrospective/events/{eid}",
                "class": EVENT_CLASS[eid.split("-")[0]],
                "as_of": newest[:10],
            }
            for role, refs in (("in_scope_candidate", block["in_scope"]), ("neighbour", block["neighbours"])):
                for i, r in enumerate(refs, 1):
                    lab, why = label(eid, r)
                    cases.append({
                        "id": f"{eid}-{'s' if role.startswith('in') else 'n'}{i}",
                        "events": [eid],
                        "dependency": dependency(r),
                        "label": lab,
                        "rationale": why,
                        "label_source": f"events/{eid}/SOURCES.md; reference {r['repo']}@{r['commit_sha'][:12]} {r['file']} ({r['commit_date'][:10]})",
                        "labelled_by": "L1",
                        "independent_label": False,
                        "role": role,
                        "template": r.get("template"),
                        "synthetic": False,
                    })
    dataset = {
        "dataset": "openpulse-retro-2026-11",
        "version": "draft-1",
        "status": "draft: L1 labels only; L2 sample pending; not frozen",
        "labelled_by": "L1 (OpenPulse developer)",
        "label_rules": "evaluation/retrospective/build_cases.py label(); DESIGN.md section 6",
        "events": dict(sorted(events.items())),
        "cases": cases,
    }
    run.validate(dataset)  # format only; no policy is run
    (HERE / "cases").mkdir(exist_ok=True)
    (HERE / "cases" / "retro-2026-11.draft.json").write_text(json.dumps(dataset, indent=1) + "\n", encoding="utf-8")

    rng = random.Random(SAMPLE_SEED)
    by_event: dict[str, list[str]] = {}
    for c in cases:
        by_event.setdefault(c["events"][0], []).append(c["id"])
    sample = {rng.choice(sorted(ids)) for _, ids in sorted(by_event.items())}
    target = math.ceil(0.25 * len(cases))
    rest = sorted(c["id"] for c in cases if c["id"] not in sample)
    rng.shuffle(rest)
    sample |= set(rest[: max(0, target - len(sample))])
    (HERE / "labelling").mkdir(exist_ok=True)
    (HERE / "labelling" / "L2-sample.json").write_text(json.dumps({"seed": SAMPLE_SEED, "pairs": sorted(sample)}, indent=1) + "\n", encoding="utf-8")
    # Round 2 (DESIGN §11): each pair carries its event's title and the
    # archived sources' own words, so L2 judges this event and no other.
    statement = {}
    for eid in events:
        fixture = json.loads((HERE / "events" / eid / "event.json").read_text("utf-8"))
        statement[eid] = {
            "event_title": fixture["title"],
            "sources": [
                {"name": e["source"]["name"], "url": e["source"]["url"], "archived": e["source"]["acquisition_method"], "quote": e["excerpt"]}
                for e in fixture["evidences"]
            ],
        }
    with open(HERE / "labelling" / "L2-packet.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for c in cases:
            if c["id"] in sample:
                f.write(json.dumps({"id": c["id"], "event": c["events"][0], **statement[c["events"][0]], "dependency": c["dependency"], "label_source": c["label_source"]}, ensure_ascii=False) + "\n")
    labels = {lab: sum(1 for c in cases if c["label"] == lab) for lab in (IN, OUT, UND)}
    print(f"{len(cases)} pairs over {len(events)} events; L1 labels {labels}; L2 sample {len(sample)} pairs")
    return 0


if __name__ == "__main__":
    sys.exit(main())

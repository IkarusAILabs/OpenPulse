# ruff: noqa: E501  (event specifications: one source per line, verbatim excerpts)
"""Write the retrospective study's 27 event fixtures (DESIGN.md §4).

Run from the repository root:

    python evaluation/retrospective/build_fixtures.py

Every event is specified once, below, from its primary source as archived
(SHORTLIST.md). The script writes ``events/<id>/event.json`` (an OSSEvent,
the input every policy receives) and ``events/<id>/SOURCES.md``. Rules:

- evidence carries the primary URL, the archived snapshot in
  ``acquisition_method`` (``wayback:<timestamp>`` or ``record:<permanent record>``),
  and ``fetched_at`` = the snapshot or record time, so replay sees exactly
  what was archived;
- the scope is the source's, typed; ``exhaustive`` with a basis only where
  the source states the complete extent (or the scope is the event itself);
- where the scope language cannot state the announced extent, the closest
  safe representation is used and the gap is recorded under
  ``representation`` (RQ-R2).

Excerpts are short quotations, at most a sentence, for evidence only.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from core.schema.models import OSSEvent  # noqa: E402

EVENTS = HERE / "events"
EVIDENCE = HERE / "evidence"


def ts(stamp: str) -> datetime:
    """``YYYYMMDDhhmmss`` (Wayback) or ISO 8601 -> aware UTC datetime."""
    if stamp[:8].isdigit() and len(stamp) == 14:
        return datetime.strptime(stamp, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def src(name, url, when, method, excerpt, announced=None, effective=None, relation="supports",
        authority="official", family=None):
    return {
        "name": name,
        "url": url,
        "when": when,
        "method": method,
        "excerpt": excerpt,
        "announced": announced,
        "effective": effective,
        "relation": relation,
        "authority": authority,
        "family": family,
    }


def wb(url: str, stamp: str) -> str:
    return f"wayback:{stamp} http://web.archive.org/web/{stamp}/{url}"


def openjdk_2025_tags() -> list[str]:
    lines = (EVIDENCE / "openjdk-2025-deleted-tags.txt").read_text("utf-8").splitlines()
    return ["docker.io/library/" + line for line in lines if line.startswith("openjdk:")]


CENTOS_8_TAGS = [
    "8", "8.1.1911", "8.2.2004", "8.3.2011", "8.4.2105",
    "centos8", "centos8.1.1911", "centos8.2.2004", "centos8.3.2011", "centos8.4.2105",
]

SPECS = [
    # --- relocation -------------------------------------------------------
    {
        "id": "REL-1", "class": "relocation", "project": "moby", "type": "OWNERSHIP_CHANGE",
        "impact": "REVIEW",
        "title": "docker/docker repository relocated to moby/moby",
        "summary": "Docker's open-source repository github.com/docker/docker became github.com/moby/moby when the Moby Project launched; the old path redirects.",
        "artifacts": [("source-repository", "github.com/docker/docker")],
        "scope": {"kind": "artifact", "artifacts": ["github.com/docker/docker"], "exhaustive": True, "basis": "definitional"},
        "sources": [
            src("moby/moby#32691", "https://github.com/moby/moby/pull/32691", "20170420213705",
                wb("https://github.com/moby/moby/pull/32691", "20170420213705"),
                "If you are a Docker user, nothing changes.", "2017-04-18", "2017-04-18", family="moby"),
        ],
        "representation": "One repository's relocation: an exact repository element, complete by definition. Whether Go import paths that still resolve through the redirect are in scope is not stated by the source.",
    },
    {
        "id": "REL-3", "class": "relocation", "project": "distribution", "type": "OWNERSHIP_CHANGE",
        "impact": "REVIEW",
        "title": "docker/distribution repository relocated to distribution/distribution",
        "summary": "Docker donated Distribution to the CNCF; github.com/docker/distribution was transferred to github.com/distribution/distribution.",
        "artifacts": [("source-repository", "github.com/docker/distribution")],
        "scope": {"kind": "artifact", "artifacts": ["github.com/docker/distribution"], "exhaustive": True, "basis": "definitional"},
        "sources": [
            src("docker/blog-donating-distribution", "https://www.docker.com/blog/donating-docker-distribution-to-the-cncf/", "20210205005303",
                wb("https://www.docker.com/blog/donating-docker-distribution-to-the-cncf/", "20210205005303"),
                "The project is now simply called Distribution, at github.com/distribution/distribution.", "2021-02-04", None, family="docker"),
            src("wayback/github.com-docker-distribution-301", "https://github.com/docker/distribution", "20210129093412",
                wb("https://github.com/docker/distribution", "20210129093412"),
                "First archived HTTP 301 for github.com/docker/distribution.", None, "2021-01-29", relation="context", authority="primary", family="wayback"),
        ],
        "representation": "As REL-1. The v2 Go import path github.com/docker/distribution kept resolving; the source does not address it.",
    },
    {
        "id": "REL-4", "class": "relocation", "project": "prometheus-operator", "type": "OWNERSHIP_CHANGE",
        "impact": "REVIEW",
        "title": "coreos/prometheus-operator relocated to prometheus-operator/prometheus-operator",
        "summary": "The Prometheus Operator moved to its own GitHub organisation; the Go module path changed with release 0.42.0.",
        "artifacts": [("source-repository", "github.com/coreos/prometheus-operator")],
        "scope": {"kind": "artifact", "artifacts": ["github.com/coreos/prometheus-operator"], "exhaustive": True, "basis": "definitional"},
        "sources": [
            src("prometheus-operator#3384", "https://github.com/prometheus-operator/prometheus-operator/pull/3384", "2020-08-05T13:43:00Z",
                "record:github pull request #3384, merged 2020-08-05T13:43Z",
                "Move repository to new organization.", "2020-08-05", "2020-08-05", family="prometheus-operator"),
            src("wayback/github.com-coreos-prometheus-operator", "https://github.com/coreos/prometheus-operator", "20200615012237",
                wb("https://github.com/coreos/prometheus-operator", "20200615012237"),
                "Repository page before the move (HTTP 200).", None, None, relation="context", authority="primary", family="wayback"),
        ],
        "representation": "As REL-1. Container images were pushed to both quay.io organisations for a time; images are not in this event.",
    },
    # --- archival or deprecation ---------------------------------------------
    {
        "id": "DEP-1", "class": "deprecation", "project": "request", "type": "DEPRECATION",
        "impact": "REVIEW",
        "title": "npm package request fully deprecated",
        "summary": "request entered maintenance mode in 2019 and was fully deprecated on 2020-02-11; every published version carries the npm deprecation message.",
        "artifacts": [("npm", "npm:request")],
        "scope": {"kind": "package", "packages": ["pkg:npm/request"], "exhaustive": True, "basis": "definitional"},
        "sources": [
            src("request/request@aded7e4f8e", "https://github.com/request/request/commit/aded7e4f8e", "2020-02-11T16:33:00Z",
                "record:github commit aded7e4f8e (README)",
                "As of Feb 11th 2020, request is fully deprecated. No new changes are expected to land.", "2019-03-30", "2020-02-11", family="request"),
            src("wayback/github.com-request-request", "https://github.com/request/request", "20200211201636",
                wb("https://github.com/request/request", "20200211201636"),
                "Repository README with the deprecation notice.", None, None, relation="context", authority="primary", family="wayback"),
        ],
        "representation": "Every version of one package: a qualified package element, complete by definition. The repository is not archived.",
    },
    {
        "id": "DEP-2", "class": "deprecation", "project": "dep", "type": "PROJECT_ARCHIVED",
        "impact": "REVIEW",
        "title": "golang/dep deprecated and archived",
        "summary": "The Go dependency tool dep was deprecated in favour of Go modules (2020-03-30) and its repository archived (2020-09-08).",
        "artifacts": [("source-repository", "github.com/golang/dep")],
        "scope": {"kind": "artifact", "artifacts": ["github.com/golang/dep"], "exhaustive": True, "basis": "definitional"},
        "sources": [
            src("golang/go#38158", "https://github.com/golang/go/issues/38158", "20200808211416",
                wb("https://github.com/golang/go/issues/38158", "20200808211416"),
                "Proposal to add deprecation language to the README and archive the repository.", "2020-03-30", None, family="golang"),
            src("wayback/github.com-golang-dep", "https://github.com/golang/dep", "20200917033647",
                wb("https://github.com/golang/dep", "20200917033647"),
                "As of 2020, Dep is deprecated and archived in favor of Go modules.", None, "2020-09-08", family="golang"),
        ],
        "representation": "GAP: a project's use of a tool (Gopkg.toml / Gopkg.lock, an install script) has no reference form in the scope language or the inventory readers; only references to the repository path can be expressed.",
    },
    {
        "id": "DEP-3", "class": "deprecation", "project": "tslint", "type": "DEPRECATION",
        "impact": "REVIEW",
        "title": "TSLint deprecated in favour of ESLint",
        "summary": "Palantir deprecated TSLint on a phased roadmap (announced 2019-02-19; no PRs accepted from 2020-12-01); the repository was later archived.",
        "artifacts": [("npm", "npm:tslint")],
        "scope": {"kind": "package", "packages": ["pkg:npm/tslint"], "exhaustive": True, "basis": "definitional"},
        "sources": [
            src("palantir/tslint-in-2019", "https://medium.com/palantir/tslint-in-2019-1a144c2317a9", "20190219201734",
                wb("https://medium.com/palantir/tslint-in-2019-1a144c2317a9", "20190219201734"),
                "TSLint will be deprecated in favor of supporting typescript-eslint.", "2019-02-19", None, family="palantir"),
            src("palantir/tslint#4534", "https://github.com/palantir/tslint/issues/4534", "20190508120833",
                wb("https://github.com/palantir/tslint/issues/4534", "20190508120833"),
                "Roadmap: stop accepting any PRs on 2020-12-01.", None, "2020-12-01", family="palantir"),
        ],
        "representation": "The announcement deprecates the whole project; the npm registry flags only 6.0.0-6.1.3. The announcing source defines the scope (REGISTRATION §8 precedence), so every version is in it.",
    },
    {
        "id": "DEP-4", "class": "deprecation", "project": "node-sass", "type": "PROJECT_ARCHIVED",
        "impact": "REVIEW",
        "title": "Node Sass end of life",
        "summary": "Node Sass was declared end-of-life: the npm package deprecated and the repository archived on 2024-07-24.",
        "artifacts": [("npm", "npm:node-sass")],
        "scope": {"kind": "package", "packages": ["pkg:npm/node-sass"], "exhaustive": True, "basis": "definitional"},
        "sources": [
            src("sass-lang/node-sass-is-end-of-life", "https://sass-lang.com/blog/node-sass-is-end-of-life/", "20240812011239",
                wb("https://sass-lang.com/blog/node-sass-is-end-of-life/", "20240812011239"),
                "The npm package has been marked as deprecated, and the GitHub repository has been archived.", "2024-07-24", "2024-07-24", family="sass"),
        ],
        "representation": "Every version of one package: complete by definition.",
    },
    {
        "id": "DEP-5", "class": "deprecation", "project": "go-yaml", "type": "PROJECT_ARCHIVED",
        "impact": "REVIEW",
        "title": "go-yaml/yaml unmaintained and archived",
        "summary": "The author labelled go-yaml/yaml (gopkg.in/yaml.v2 and v3) unmaintained on 2025-04-01; the repository was then archived.",
        "artifacts": [("source-repository", "github.com/go-yaml/yaml")],
        "scope": {"kind": "package", "packages": ["pkg:golang/gopkg.in/yaml.v3", "pkg:golang/gopkg.in/yaml.v2"], "exhaustive": False, "basis": None},
        "sources": [
            src("go-yaml/yaml@944c86a", "https://github.com/go-yaml/yaml/commit/944c86a7d29391925ed6ac33bee98a0516f1287a", "2025-04-01T17:00:11Z",
                "record:github commit 944c86a (README)",
                "THIS PROJECT IS UNMAINTAINED.", "2025-04-01", None, family="go-yaml"),
            src("wayback/github.com-go-yaml-yaml", "https://github.com/go-yaml/yaml", "20250401151649",
                wb("https://github.com/go-yaml/yaml", "20250401151649"),
                "README with the unmaintained notice.", None, "2025-04-25", relation="context", authority="primary", family="wayback"),
        ],
        "representation": "The source names the repository, not the modules it publishes; the modules are listed as qualified package values and the scope is left partial, since the source does not enumerate them.",
    },
    {
        "id": "DEP-6", "class": "deprecation", "project": "golint", "type": "DEPRECATION",
        "impact": "REVIEW",
        "title": "golint frozen and deprecated",
        "summary": "A Go proposal to freeze and deprecate golang.org/x/lint was accepted (2020-06-03); the GitHub mirror was archived on 2021-05-08.",
        "artifacts": [("source-repository", "github.com/golang/lint")],
        "scope": {"kind": "package", "packages": ["pkg:golang/golang.org/x/lint"], "exhaustive": True, "basis": "definitional"},
        "sources": [
            src("golang/go#38968", "https://github.com/golang/go/issues/38968", "20210511082834",
                wb("https://github.com/golang/go/issues/38968", "20210511082834"),
                "This proposal - to freeze and deprecate x/lint - is accepted.", "2020-06-03", "2021-05-08", family="golang"),
        ],
        "representation": "One module, complete by definition. The canonical googlesource repository received a commit in 2024 although the GitHub mirror is archived.",
    },
    # --- distribution ------------------------------------------------------------
    {
        "id": "DIS-1", "class": "distribution", "project": "kubernetes", "type": "REGISTRY_CHANGE",
        "impact": "ACTION",
        "title": "k8s.gcr.io redirected to registry.k8s.io and frozen",
        "summary": "Kubernetes moved image publishing to registry.k8s.io; k8s.gcr.io traffic was redirected from 2023-03-20 and the registry frozen on 2023-04-03.",
        "artifacts": [],
        "scope": {"kind": "registry", "registries": ["k8s.gcr.io"], "exhaustive": True, "basis": "announced"},
        "sources": [
            src("kubernetes.io/registry-k8s-io-ga", "https://kubernetes.io/blog/2022/11/28/registry-k8s-io-faster-cheaper-ga/", "20221129154618",
                wb("https://kubernetes.io/blog/2022/11/28/registry-k8s-io-faster-cheaper-ga/", "20221129154618"),
                "registry.k8s.io is generally available; new images will stop being published to k8s.gcr.io.", "2022-11-28", None, family="kubernetes"),
            src("kubernetes.io/k8s-gcr-io-freeze", "https://kubernetes.io/blog/2023/02/06/k8s-gcr-io-freeze-announcement/", "20230213025122",
                wb("https://kubernetes.io/blog/2023/02/06/k8s-gcr-io-freeze-announcement/", "20230213025122"),
                "No further images for Kubernetes and related subprojects will be pushed to the old registry.", "2023-02-06", "2023-04-03", family="kubernetes"),
            src("kubernetes.io/image-registry-redirect", "https://kubernetes.io/blog/2023/03/10/image-registry-redirect/", "20230315231813",
                wb("https://kubernetes.io/blog/2023/03/10/image-registry-redirect/", "20230315231813"),
                "ALL images on k8s.gcr.io will be impacted by this change.", "2023-03-10", "2023-03-20", family="kubernetes"),
        ],
        "representation": "GAP: 'every image on registry k8s.gcr.io' can only be stated as a registry element, which is always an envelope (it can exclude, never give a positive). The exact namespace form cannot cover nested repositories (k8s.gcr.io/ingress-nginx/controller).",
    },
    {
        "id": "DIS-2", "class": "distribution", "project": "openjdk", "type": "DEPRECATION",
        "impact": "REVIEW",
        "title": "Official openjdk image deprecated (no non-EA updates after July 2022)",
        "summary": "The Docker Official Image openjdk was marked officially deprecated; only Early Access tags keep receiving updates after July 2022.",
        "artifacts": [],
        "scope": {"kind": "artifact", "artifacts": ["docker.io/library/openjdk"], "exhaustive": True, "basis": "announced"},
        "sources": [
            src("docker-library/docs@326814f", "https://github.com/docker-library/docs/commit/326814f7acbd", "2022-06-10T00:00:00Z",
                "record:github commit 326814f7acbd (openjdk deprecation notice)",
                "This image is officially deprecated and all users are recommended to find and use suitable replacements ASAP.", "2022-06-10", "2022-08-01", family="docker-library"),
            src("docker-library/openjdk#505", "https://github.com/docker-library/openjdk/issues/505", "20220718201219",
                wb("https://github.com/docker-library/openjdk/issues/505", "20220718201219"),
                "Upstream retirement notice for the OpenJDK builds the image is sourced from.", "2022-06-09", None, relation="context", family="docker-library"),
        ],
        "representation": "GAP: 'all tags except Early Access' cannot be stated: the <version> predicate also matches EA tags (19-ea-5-jdk) and misses non-version tags (latest, jre). The repository element (every tag) is used, so EA tags will be positives by construction.",
    },
    {
        "id": "DIS-3", "class": "distribution", "project": "openjdk", "type": "DISTRIBUTION_CHANGE",
        "impact": "ACTION",
        "title": "1,051 floating openjdk tags deleted from Docker Hub",
        "summary": "docker-library deleted 1,051 'bare' openjdk tags from Docker Hub on 2025-11-03, keeping explicit historical versions and EA/RC tags.",
        "artifacts": [],
        "scope": {"kind": "artifact", "artifacts": "OPENJDK_2025", "exhaustive": True, "basis": "announced"},
        "sources": [
            src("docker-library/official-images#20210", "https://github.com/docker-library/official-images/pull/20210", "20251105030321",
                wb("https://github.com/docker-library/official-images/pull/20210", "20251105030321"),
                "Deletes are now complete.", "2025-10-31", "2025-11-03", family="docker-library"),
        ],
        "representation": "Exact: one tag element per deleted tag (evidence/openjdk-2025-deleted-tags.txt), complete as announced. A digest-pinned reference is undetermined (its tag is unknown).",
    },
    {
        "id": "DIS-4", "class": "distribution", "project": "centos", "type": "DEPRECATION",
        "impact": "REVIEW",
        "title": "Official centos image deprecated and removed from the library",
        "summary": "The centos Official Image was deprecated (2022-09-22) and all its tags removed from the official-images library after CentOS 7 end of life (2024-07-02).",
        "artifacts": [],
        "scope": {"kind": "artifact", "artifacts": ["docker.io/library/centos"], "exhaustive": True, "basis": "announced"},
        "sources": [
            src("docker-library/docs#2205", "https://github.com/docker-library/docs/pull/2205", "20221014104857",
                wb("http://hub.docker.com/_/centos", "20221014104857"),
                "This image is no longer supported/maintained.", "2022-09-22", None, family="docker-library"),
            src("docker-library/official-images#17094", "https://github.com/docker-library/official-images/pull/17094", "20241212144136",
                wb("https://github.com/docker-library/official-images/pull/17094", "20241212144136"),
                "All tags of this image are EOL.", None, "2024-07-02", family="docker-library"),
        ],
        "representation": "Every tag, as the notice says. 'Removed from the library' is not deletion from Docker Hub: most tags still pull.",
    },
    {
        "id": "DIS-5", "class": "distribution", "project": "adoptopenjdk", "type": "DEPRECATION",
        "impact": "REVIEW",
        "title": "Official adoptopenjdk image deprecated in favour of eclipse-temurin",
        "summary": "The adoptopenjdk Official Image was deprecated in favour of eclipse-temurin, with no further updates after 2021-08-01.",
        "artifacts": [],
        "scope": {"kind": "artifact", "artifacts": ["docker.io/library/adoptopenjdk"], "exhaustive": True, "basis": "announced"},
        "sources": [
            src("docker-library/docs@4baab4b", "https://github.com/docker-library/docs/commit/4baab4b75b58", "20210825110321",
                wb("https://hub.docker.com/_/adoptopenjdk", "20210825110321"),
                "This image is officially deprecated in favor of the eclipse-temurin image, and will receive no further updates after 2021-08-01.", "2021-08-13", "2021-08-01", family="docker-library"),
        ],
        "representation": "Every tag of one repository. The non-official adoptopenjdk/* namespace is a different repository.",
    },
    {
        "id": "DIS-6", "class": "distribution", "project": "java", "type": "DEPRECATION",
        "impact": "REVIEW",
        "title": "Official java image deprecated in favour of openjdk",
        "summary": "The java Official Image was deprecated in favour of openjdk on 2016-08-11, with no updates after 2016-12-31.",
        "artifacts": [],
        "scope": {"kind": "artifact", "artifacts": ["docker.io/library/java"], "exhaustive": True, "basis": "announced"},
        "sources": [
            src("docker-library/docs@a3439b6", "https://github.com/docker-library/docs/commit/a3439b66b798", "20161027201850",
                wb("https://hub.docker.com/_/java/", "20161027201850"),
                "This image is officially deprecated in favor of the openjdk image, and will receive no further updates after 2016-12-31.", "2016-08-11", "2016-12-31", family="docker-library"),
        ],
        "representation": "Every tag of one repository.",
    },
    # --- licence ---------------------------------------------------------------
    {
        "id": "LIC-1", "class": "licence", "project": "elasticsearch", "type": "LICENSE_CHANGE",
        "impact": "REVIEW",
        "title": "Elasticsearch and Kibana relicensed from Apache-2.0 from 7.11",
        "summary": "Starting with 7.11, Elasticsearch and Kibana source moved from Apache-2.0 to a dual SSPL / Elastic License; clients, Beats and Logstash stay Apache-2.0.",
        "artifacts": [("docker-image", "docker.elastic.co/elasticsearch/elasticsearch:7.11.0")],
        "scope": {"kind": "version", "versions": ["7.11"], "exhaustive": False, "basis": None},
        "sources": [
            src("elastic/licensing-change", "https://www.elastic.co/blog/licensing-change", "20210115230839",
                wb("https://www.elastic.co/blog/licensing-change", "20210115230839"),
                "Starting with the upcoming Elastic 7.11 release, we will be moving the Apache 2.0-licensed code to dual license.", "2021-01-14", "2021-02-10", family="elastic"),
        ],
        "representation": "GAP: an open-ended boundary (every release >= 7.11) cannot be stated; only release lines can, and at the announcement only 7.11 was known. The scope is the 7.11 line, partial. Kibana is a separate project in the catalog's terms, so Kibana references reach this event with unresolved identity.",
    },
    {
        "id": "LIC-2", "class": "licence", "project": "terraform", "type": "LICENSE_CHANGE",
        "impact": "REVIEW",
        "title": "Terraform relicensed from MPL-2.0 to BSL 1.1 from 1.6",
        "summary": "HashiCorp moved future releases, including Terraform from 1.6.0, to the Business Source License 1.1; APIs and SDKs stay MPL-2.0.",
        "artifacts": [],
        "scope": {"kind": "version", "versions": ["1.6"], "exhaustive": False, "basis": None},
        "sources": [
            src("hashicorp/adopts-bsl", "https://www.hashicorp.com/blog/hashicorp-adopts-business-source-license", "20230811223350",
                wb("https://www.hashicorp.com/blog/hashicorp-adopts-business-source-license", "20230811223350"),
                "BSL v1.1 on all future releases of HashiCorp products.", "2023-08-10", "2023-08-16", family="hashicorp"),
            src("hashicorp/terraform@v1.6.0/LICENSE", "https://github.com/hashicorp/terraform/blob/v1.6.0/LICENSE", "2023-10-04T00:00:00Z",
                "record:git tag v1.6.0 LICENSE (BUSL 1.1); tag v1.5.7 LICENSE (MPL 2.0)",
                "Licensed Work: Terraform 1.6.0.", None, None, relation="context", authority="primary", family="hashicorp"),
        ],
        "representation": "GAP as LIC-1: 'every release from 1.6.0' cannot be stated; the 1.6 line, partial. The blog names no version; the boundary is from the tag LICENSE files.",
    },
    {
        "id": "LIC-3", "class": "licence", "project": "grafana", "type": "LICENSE_CHANGE",
        "impact": "REVIEW",
        "title": "Grafana relicensed from Apache-2.0 to AGPLv3 from 8.0",
        "summary": "Grafana Labs relicensed Grafana (with Loki and Tempo) from Apache-2.0 to AGPLv3; Grafana 8.0.0 is the first AGPL release. Plugins and some libraries stay Apache-2.0.",
        "artifacts": [],
        "scope": {"kind": "version", "versions": ["8"], "exhaustive": False, "basis": None},
        "sources": [
            src("grafana/relicensing-to-agplv3", "https://grafana.com/blog/2021/04/20/grafana-loki-tempo-relicensing-to-agplv3/", "20210421230514",
                wb("https://grafana.com/blog/2021/04/20/grafana-loki-tempo-relicensing-to-agplv3/", "20210421230514"),
                "We are relicensing our core open source projects from Apache 2.0 to AGPLv3.", "2021-04-20", "2021-06-08", family="grafana"),
        ],
        "representation": "GAP as LIC-1: the 8 line, partial. The version boundary is derived from tag LICENSE files, not stated by the blog.",
    },
    {
        "id": "LIC-4", "class": "licence", "project": "mongodb", "type": "LICENSE_CHANGE",
        "impact": "REVIEW",
        "title": "MongoDB Community Server relicensed to SSPL for releases on or after 2018-10-16",
        "summary": "All MongoDB Community Server patch releases and versions released on or after 2018-10-16, on every branch, are under the SSPL.",
        "artifacts": [],
        "scope": None,
        "sources": [
            src("mongodb/sspl-faq", "https://www.mongodb.com/licensing/server-side-public-license/faq", "20181023161242",
                wb("https://www.mongodb.com/licensing/server-side-public-license/faq", "20181023161242"),
                "All MongoDB Community Server patch releases and versions released on or after October 16, 2018, will be subject to this new license.", "2018-10-16", "2018-10-16", family="mongodb"),
        ],
        "representation": "GAP: a date-based boundary across every branch has no form in the scope language (versions are release lines). The event is project-wide, which can tie a dependency to the project but never decide membership.",
    },
    # --- end of life -----------------------------------------------------------
    {
        "id": "EOL-1", "class": "eol", "project": "cpython", "type": "EOL",
        "impact": "ACTION",
        "title": "Python 2.7 end of life",
        "summary": "Python 2.7 reached end of life on 2020-01-01; the final release, 2.7.18, contains fixes up to that date only.",
        "artifacts": [],
        "scope": {"kind": "version", "versions": ["2.7"], "exhaustive": True, "basis": "definitional"},
        "sources": [
            src("python.org/sunset-python-2", "https://www.python.org/doc/sunset-python-2/", "20200102202103",
                wb("https://www.python.org/doc/sunset-python-2/", "20200102202103"),
                "We have decided that January 1, 2020, was the day that we sunset Python 2.", "2014-04-13", "2020-01-01", family="python"),
        ],
        "representation": "One release line, complete by definition.",
    },
    {
        "id": "EOL-2", "class": "eol", "project": "centos", "type": "EOL",
        "impact": "ACTION",
        "title": "CentOS Linux 8 end of life",
        "summary": "CentOS Linux 8 ended on 2021-12-31 in favour of CentOS Stream 8; CentOS Linux 7 continued separately.",
        "artifacts": [],
        "scope": {"kind": "artifact", "artifacts": [f"docker.io/library/centos:{t}" for t in CENTOS_8_TAGS], "exhaustive": False, "basis": None},
        "sources": [
            src("centos/future-is-centos-stream", "https://blog.centos.org/2020/12/future-is-centos-stream/", "20201211014354",
                wb("https://blog.centos.org/2020/12/future-is-centos-stream/", "20201211014354"),
                "CentOS Linux 8, as a rebuild of RHEL 8, will end at the end of 2021.", "2020-12-08", "2021-12-31", family="centos"),
        ],
        "representation": "GAP: CentOS is not a curated project, so a release-line scope could not resolve identity; the CentOS 8 image tags are enumerated instead (as listed on Docker Hub on 2026-10-30) and the scope is left partial so that a missed tag can never be cleared.",
    },
    {
        "id": "EOL-3", "class": "eol", "project": "nodejs", "type": "EOL",
        "impact": "ACTION",
        "title": "Node.js 12 end of life",
        "summary": "The Node.js 12.x (Erbium) release line reached end of life on 2022-04-30; the final release is v12.22.12.",
        "artifacts": [],
        "scope": {"kind": "version", "versions": ["12"], "exhaustive": True, "basis": "definitional"},
        "sources": [
            src("nodejs/Release", "https://github.com/nodejs/Release", "20220430045420",
                wb("https://github.com/nodejs/Release", "20220430045420"),
                "12.x Erbium: end-of-life 2022-04-30.", None, "2022-04-30", family="nodejs"),
        ],
        "representation": "One release line, complete by definition.",
    },
    # --- compromised versions ------------------------------------------------------
    {
        "id": "CMP-1", "class": "compromised", "project": "colors", "type": "SECURITY",
        "impact": "CRITICAL",
        "title": "Sabotaged colors versions",
        "summary": "The maintainer published colors versions that print garbage and loop forever.",
        "artifacts": [],
        "scope": {"kind": "version", "versions": ["1.4.1", "1.4.2", "1.4.44"], "exhaustive": False, "basis": None},
        "sources": [
            src("GHSA-5rqg-jm4f-cqx7", "https://github.com/advisories/GHSA-5rqg-jm4f-cqx7", "20220115123912",
                wb("https://github.com/advisories/GHSA-5rqg-jm4f-cqx7", "20220115123912"),
                "colors versions 1.4.1, 1.4.2, and 1.4.44-liberty-2 were published including malicious code.", "2022-01-10", "2022-01-08", family="github-advisories"),
            src("GHSA-gh88-3pxp-6fm8", "https://github.com/advisories/GHSA-gh88-3pxp-6fm8", "2022-01-21T00:00:00Z",
                "record:github advisory GHSA-gh88-3pxp-6fm8 (affected >= 1.4.1)",
                "Affected versions: >= 1.4.1.", "2022-01-21", None, relation="context", family="github-advisories"),
        ],
        "representation": "The two advisories disagree on the extent (an enumerated set vs >= 1.4.1), so the scope is partial (TR Table 7). The version element 1.4.44 covers 1.4.44-liberty-2. The package is not curated, so the version scope resolves no identity.",
    },
    {
        "id": "CMP-2", "class": "compromised", "project": "faker", "type": "SECURITY",
        "impact": "CRITICAL",
        "title": "Sabotaged faker 6.6.6",
        "summary": "The maintainer published faker 6.6.6 with the functional code removed.",
        "artifacts": [],
        "scope": {"kind": "version", "versions": ["6.6.6"], "exhaustive": True, "basis": "announced"},
        "sources": [
            src("GHSA-5w9c-rv96-fr7g", "https://github.com/advisories/GHSA-5w9c-rv96-fr7g", "2022-03-22T00:00:00Z",
                "record:github advisory GHSA-5w9c-rv96-fr7g (faker = 6.6.6)",
                "The maintainer deliberately removed the functional code from this package.", "2022-03-22", "2022-01-05", family="github-advisories"),
            src("wayback/github.com-Marak-faker.js", "https://github.com/Marak/faker.js", "20220106193513",
                wb("https://github.com/Marak/faker.js", "20220106193513"),
                "Repository page after the 6.6.6 release.", None, None, relation="context", authority="primary", family="wayback"),
        ],
        "representation": "One version, as announced. The package is not curated (see CMP-1).",
    },
    {
        "id": "CMP-3", "class": "compromised", "project": "node-ipc", "type": "SECURITY",
        "impact": "CRITICAL",
        "title": "Protestware in node-ipc",
        "summary": "node-ipc 10.1.1-10.1.2 overwrote files on geolocated hosts; 9.2.2 and 11.x shipped the peacenotwar payload.",
        "artifacts": [],
        "scope": {"kind": "version", "versions": ["10.1.1", "10.1.2", "9.2.2", "11"], "exhaustive": True, "basis": "announced"},
        "sources": [
            src("GHSA-97m3-w2cp-4xx6", "https://github.com/advisories/GHSA-97m3-w2cp-4xx6", "20220321003825",
                wb("https://github.com/advisories/GHSA-97m3-w2cp-4xx6", "20220321003825"),
                "Versions 10.1.1 and 10.1.2 are vulnerable to embedded malicious code, removed in version 10.1.3.", "2022-03-16", "2022-03-07", family="github-advisories"),
            src("GHSA-8gr3-2gjw-jj7g+GHSA-3mpp-xfvh-qh37", "https://github.com/advisories/GHSA-3mpp-xfvh-qh37", "2022-03-16T00:00:00Z",
                "record:github advisories GHSA-8gr3-2gjw-jj7g (= 9.2.2) and GHSA-3mpp-xfvh-qh37 (>= 11.0.0, < 12.0.0)",
                "Hidden functionality in 9.2.2; desktop message in 11.x.", "2022-03-16", None, family="github-advisories"),
        ],
        "representation": "Three advisory ranges as versions and one release line (11). The package is not curated (see CMP-1).",
    },
    {
        "id": "CMP-4", "class": "compromised", "project": "ua-parser-js", "type": "SECURITY",
        "impact": "CRITICAL",
        "title": "Hijacked ua-parser-js versions",
        "summary": "The maintainer's npm account was hijacked and ua-parser-js 0.7.29, 0.8.0 and 1.0.0 published with malware.",
        "artifacts": [],
        "scope": {"kind": "version", "versions": ["0.7.29", "0.8.0", "1.0.0"], "exhaustive": True, "basis": "announced"},
        "sources": [
            src("faisalman/ua-parser-js#536", "https://github.com/faisalman/ua-parser-js/issues/536", "20211023193659",
                wb("https://github.com/faisalman/ua-parser-js/issues/536", "20211023193659"),
                "Published some compromised packages (0.7.29, 0.8.0, 1.0.0).", "2021-10-22", "2021-10-22", family="ua-parser-js"),
        ],
        "representation": "One bad version per release line, as announced. The package is not curated (see CMP-1).",
    },
    {
        "id": "CMP-5", "class": "compromised", "project": "event-stream", "type": "SECURITY",
        "impact": "CRITICAL",
        "title": "Malicious flatmap-stream dependency in event-stream 3.3.6",
        "summary": "event-stream 3.3.6 depended on the malicious flatmap-stream 0.1.1, which targeted the Copay wallet.",
        "artifacts": [],
        "scope": {"kind": "version", "versions": ["3.3.6"], "exhaustive": True, "basis": "announced"},
        "sources": [
            src("npm-blog/event-stream-incident", "https://blog.npmjs.org/post/180565383195/details-about-the-event-stream-incident", "20181129013028",
                wb("https://blog.npmjs.org/post/180565383195/details-about-the-event-stream-incident", "20181129013028"),
                "The malicious package was version 0.1.1 of flatmap-stream.", "2018-11-27", "2018-09-09", family="npm"),
        ],
        "representation": "One version of event-stream. flatmap-stream itself is a separate package and not in this event; the advisories disagree on its extent. The package is not curated (see CMP-1).",
    },
]


def build(spec: dict) -> tuple[dict, str]:
    scope = spec["scope"]
    if scope is not None and scope.get("artifacts") == "OPENJDK_2025":
        scope = {**scope, "artifacts": openjdk_2025_tags()}
    evidences = []
    for s in spec["sources"]:
        source = {
            "name": s["name"],
            "url": s["url"],
            "authority": s["authority"],
            "fetched_at": ts(s["when"]).isoformat().replace("+00:00", "Z"),
            "acquisition_method": s["method"],
        }
        if s["family"]:
            source["family"] = s["family"]
        evidence = {"source": source, "excerpt": s["excerpt"], "relation": s["relation"]}
        if s["announced"]:
            evidence["announcement_date"] = s["announced"]
        if s["effective"]:
            evidence["effective_date"] = s["effective"]
        evidences.append(evidence)
    newest = max(ts(s["when"]) for s in spec["sources"])
    event = {
        "id": f"retro-{spec['id'].lower()}",
        "project_slug": spec["project"],
        "event_type": spec["type"],
        "title": spec["title"],
        "summary": spec["summary"],
        "confidence": "CONFIRMED",
        "impact": spec["impact"],
        "affected_artifacts": [{"kind": k, "ref": r} for k, r in spec["artifacts"]],
        "evidences": evidences,
        "created_at": newest.isoformat().replace("+00:00", "Z"),
    }
    if scope is not None:
        event["scope"] = scope
    OSSEvent(**event)  # validates against the frozen schema
    lines = [f"# {spec['id']}: {spec['title']}", "", f"Class: {spec['class']}. Project slug: `{spec['project']}`.", ""]
    lines.append("| Source | Primary URL | Archived as | Fetched at |")
    lines.append("|---|---|---|---|")
    for s in spec["sources"]:
        lines.append(f"| {s['name']} | {s['url']} | {s['method']} | {ts(s['when']).isoformat()} |")
    lines += ["", "## Representation (RQ-R2)", "", spec["representation"], ""]
    return event, "\n".join(lines)


def main() -> int:
    for spec in SPECS:
        event, sources = build(spec)
        folder = EVENTS / spec["id"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "event.json").write_text(json.dumps(event, indent=1) + "\n", encoding="utf-8")
        (folder / "SOURCES.md").write_text(sources, encoding="utf-8")
    print(f"wrote {len(SPECS)} event fixtures under {EVENTS.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

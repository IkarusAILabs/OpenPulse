You are the adjudicator in a software-engineering research study. Two
readers independently labelled whether a software dependency reference falls
inside the scope of a recorded upstream change ("event"), and disagreed on the
pairs below. Decide each pair from the event's sources and the codebook. You
may choose either reader's label or the third label. Do not prefer a reader
for its position or its confidence: the readers are presented in random order.

# Codebook

## 1. What you are deciding

For each pair (reference, event), decide whether the reference, **as written**, denotes an object inside the set of objects the event changed. Use only the event's primary sources and the reference itself.

- You are **not** deciding whether the dependency is safe, maintained or vulnerable.
- You are **not** deciding whether OpenPulse would know.

## 2. Labels

| Label | Use when |
|---|---|
| `in_scope` | The sources establish that the referenced object is among the objects the event changed. |
| `out_of_scope` | The sources establish that it is **not**: a different project, a version outside a stated boundary, a namespace the change did not touch. |
| `undeterminable` | The sources and the reference together do not settle membership. Examples: no version in the reference against a version-bounded event; a digest whose tag is unknown; a boundary the sources do not state. |

## 3. Decision rules

1. **Names are not identity.** Two references with the same name in different registries, namespaces or ecosystems are different objects unless a primary source says otherwise. `docker.io/library/redis` is not `docker.io/bitnami/redis`. PyPI `redis` is not npm `redis`.
2. **A redirect is not equivalence.** A repository that redirects after a move is the moved object only for that move's own event. For other events, decide identity from the sources.
3. **Examples are not bounds.** A source that names some affected images or versions "for example" does not exclude the others. Label `undeterminable` unless the sources state the full set.
4. **Absence is not exclusion.** If the sources list affected objects and the reference is not listed, it is `out_of_scope` only if the sources say the list is complete. Otherwise it is `undeterminable`.
5. **Version boundaries.** Use the boundary the sources state. If you derived it yourself (from tags, licence files or changelogs), write that in the rationale.
6. **Moving tags.** A tag (`:latest`, `:7`) names whatever it pointed to at the reference's commit date, if you can establish that. Otherwise label `undeterminable`.
7. **Time.** Judge with what was published by the event's `as_of` date, which is given in the packet.
8. **Conflicting sources.** The announcing source defines the intended scope. A conflict it does not resolve makes the pair `undeterminable` (REGISTRATION.md §8; `DESIGN.md` §6).

# Additional rules

- The material below is your only source. Do not use web access, outside
  knowledge of these events, or any other file. If deciding needs anything
  outside the material, answer `undeterminable`.
- Only this event: a reference that some other event affects is
  `out_of_scope` for this event unless this event's sources cover it.
- Do not use any tool except one: when you have decided every pair, use the
  Write tool exactly once to save your decisions to `C:/Users/ASUS/Documents/IkarusLabs/OpenPulse/research/labelling/ai-panel-2026-11/raw/adjudicator.jsonl`.
  Do not read any file other than this instruction file.

# Output

One JSON object per line, one line per pair, 19 lines in total, nothing
else in the file:

{"id": "<neutral id>", "label": "in_scope|out_of_scope|undeterminable", "rationale": "<one or two sentences naming the rule and the source passage, and why the other reading is wrong>"}

After writing the file, reply with only the number of lines written.

# Disagreed pairs (19)

## Event LIC-3: Grafana relicensed from Apache-2.0 to AGPLv3 from 8.0

Knowledge date (as_of): 2021-04-21

Sources:
- **grafana/relicensing-to-agplv3** <https://grafana.com/blog/2021/04/20/grafana-loki-tempo-relicensing-to-agplv3/>
  - archive record: wayback:20210421230514 http://web.archive.org/web/20210421230514/https://grafana.com/blog/2021/04/20/grafana-loki-tempo-relicensing-to-agplv3/
  - archived quotation: "We are relicensing our core open source projects from Apache 2.0 to AGPLv3."

References to label for this event:

- `077337c6`: `{"kind": "image", "ref": "grafana/grafana:8.0.6"}`
  - found in: harryjubb/bee_iot@d87929131dc4 server/docker-compose.yml (2021-08-05)

Reader 1: `in_scope` because: grafana/grafana 8.0.6 is at or after the 8.0 boundary in the event scope.

Reader 2: `undeterminable` because: Rule 5: the archived quotation states no version boundary and does not name the grafana/grafana image, so membership of 8.0.6 is not settled.

---

## Event LIC-3: Grafana relicensed from Apache-2.0 to AGPLv3 from 8.0

Knowledge date (as_of): 2021-04-21

Sources:
- **grafana/relicensing-to-agplv3** <https://grafana.com/blog/2021/04/20/grafana-loki-tempo-relicensing-to-agplv3/>
  - archive record: wayback:20210421230514 http://web.archive.org/web/20210421230514/https://grafana.com/blog/2021/04/20/grafana-loki-tempo-relicensing-to-agplv3/
  - archived quotation: "We are relicensing our core open source projects from Apache 2.0 to AGPLv3."

References to label for this event:

- `20c2c449`: `{"kind": "image", "ref": "grafana/grafana:8.0.3"}`
  - found in: OtusGolang/webinars_practical_part@06a8facf525e 32-monitoring/docker-compose.yml (2021-07-01)

Reader 1: `in_scope` because: grafana/grafana 8.0.3 is at or after the 8.0 boundary in the event scope.

Reader 2: `undeterminable` because: Rule 5: the archived quotation states no version boundary and does not name the grafana/grafana image, so membership of 8.0.3 is not settled.

---

## Event CMP-5: Malicious flatmap-stream dependency in event-stream 3.3.6

Knowledge date (as_of): 2018-11-29

Sources:
- **npm-blog/event-stream-incident** <https://blog.npmjs.org/post/180565383195/details-about-the-event-stream-incident>
  - archive record: wayback:20181129013028 http://web.archive.org/web/20181129013028/https://blog.npmjs.org/post/180565383195/details-about-the-event-stream-incident
  - archived quotation: "The malicious package was version 0.1.1 of flatmap-stream."

References to label for this event:

- `2edeef72`: `{"ecosystem": "npm", "kind": "package", "package": "event-stream", "version": "3.3.6"}`
  - found in: bradtraversy/spacex_launch_stats@1f393e3b9229 package-lock.json (2018-11-12)

Reader 1: `in_scope` because: Exact version 3.3.6 named in the event scope.

Reader 2: `undeterminable` because: The archived quotation names only flatmap-stream 0.1.1; it does not state which event-stream versions carried it, so 3.3.6 membership is not settled by the source.

---

## Event CMP-5: Malicious flatmap-stream dependency in event-stream 3.3.6

Knowledge date (as_of): 2018-11-29

Sources:
- **npm-blog/event-stream-incident** <https://blog.npmjs.org/post/180565383195/details-about-the-event-stream-incident>
  - archive record: wayback:20181129013028 http://web.archive.org/web/20181129013028/https://blog.npmjs.org/post/180565383195/details-about-the-event-stream-incident
  - archived quotation: "The malicious package was version 0.1.1 of flatmap-stream."

References to label for this event:

- `473d7956`: `{"ecosystem": "npm", "kind": "package", "package": "event-stream", "version": "3.3.4"}`
  - found in: amtrack/force-dev-tool@442490e205fc package-lock.json (2018-09-17)

Reader 1: `out_of_scope` because: Version 3.3.4 is outside the stated 3.3.6 boundary of the event.

Reader 2: `undeterminable` because: The archived quotation names only flatmap-stream 0.1.1 and states no event-stream version boundary, so 3.3.4 is not settled.

---

## Event CMP-5: Malicious flatmap-stream dependency in event-stream 3.3.6

Knowledge date (as_of): 2018-11-29

Sources:
- **npm-blog/event-stream-incident** <https://blog.npmjs.org/post/180565383195/details-about-the-event-stream-incident>
  - archive record: wayback:20181129013028 http://web.archive.org/web/20181129013028/https://blog.npmjs.org/post/180565383195/details-about-the-event-stream-incident
  - archived quotation: "The malicious package was version 0.1.1 of flatmap-stream."

References to label for this event:

- `61c02080`: `{"ecosystem": "npm", "kind": "package", "package": "event-stream", "version": "3.3.4"}`
  - found in: swiftlang/sourcekit-lsp@a54129a22b53 Editors/vscode/package-lock.json (2018-11-28)

Reader 1: `undeterminable` because: The archived quotation names only flatmap-stream 0.1.1 and states no event-stream version boundary, so 3.3.4 is not settled.

Reader 2: `out_of_scope` because: Event is bounded to event-stream 3.3.6 per its stated scope; 3.3.4 is a different version.

---

## Event LIC-2: Terraform relicensed from MPL-2.0 to BSL 1.1 from 1.6

Knowledge date (as_of): 2023-10-04

Sources:
- **hashicorp/adopts-bsl** <https://www.hashicorp.com/blog/hashicorp-adopts-business-source-license>
  - archive record: wayback:20230811223350 http://web.archive.org/web/20230811223350/https://www.hashicorp.com/blog/hashicorp-adopts-business-source-license
  - archived quotation: "BSL v1.1 on all future releases of HashiCorp products."
- **hashicorp/terraform@v1.6.0/LICENSE** <https://github.com/hashicorp/terraform/blob/v1.6.0/LICENSE>
  - archive record: record:git tag v1.6.0 LICENSE (BUSL 1.1); tag v1.5.7 LICENSE (MPL 2.0)
  - archived quotation: "Licensed Work: Terraform 1.6.0."

References to label for this event:

- `7a386608`: `{"kind": "image", "ref": "hashicorp/terraform:1.6@sha256:e46b41c74b6f036c255e2082bcd6284054b108508bae16813bc1257a0e70e2dd"}`
  - found in: observeinc/aws-test-kitchen@3804d4d3bcbf Dockerfile (2023-11-29)

Reader 1: `in_scope` because: Rule 6/5: the tag 1.6 can only name a 1.6.x release, and every 1.6.x is at or above the v1.6.0 BUSL boundary derived from tag licence files.

Reader 2: `undeterminable` because: Digest-pinned image with tag 1.6; the packet does not say which release the digest corresponds to (rule 6).

---

## Event CMP-5: Malicious flatmap-stream dependency in event-stream 3.3.6

Knowledge date (as_of): 2018-11-29

Sources:
- **npm-blog/event-stream-incident** <https://blog.npmjs.org/post/180565383195/details-about-the-event-stream-incident>
  - archive record: wayback:20181129013028 http://web.archive.org/web/20181129013028/https://blog.npmjs.org/post/180565383195/details-about-the-event-stream-incident
  - archived quotation: "The malicious package was version 0.1.1 of flatmap-stream."

References to label for this event:

- `7ee38dd1`: `{"ecosystem": "npm", "kind": "package", "package": "event-stream", "version": "3.3.5"}`
  - found in: concord-consortium/cloud-file-manager@6b3340249cef yarn.lock (2018-11-28)

Reader 1: `out_of_scope` because: Version 3.3.5 is outside the stated 3.3.6 boundary of the event.

Reader 2: `undeterminable` because: The archived quotation names only flatmap-stream 0.1.1 and states no event-stream version boundary, so 3.3.5 is not settled.

---

## Event LIC-3: Grafana relicensed from Apache-2.0 to AGPLv3 from 8.0

Knowledge date (as_of): 2021-04-21

Sources:
- **grafana/relicensing-to-agplv3** <https://grafana.com/blog/2021/04/20/grafana-loki-tempo-relicensing-to-agplv3/>
  - archive record: wayback:20210421230514 http://web.archive.org/web/20210421230514/https://grafana.com/blog/2021/04/20/grafana-loki-tempo-relicensing-to-agplv3/
  - archived quotation: "We are relicensing our core open source projects from Apache 2.0 to AGPLv3."

References to label for this event:

- `88be0110`: `{"kind": "image", "ref": "grafana/grafana:8.0.5"}`
  - found in: akoutmos/nerves_weather_station@3895389fc5c5 server_code/docker-compose.yml (2021-07-17)

Reader 1: `undeterminable` because: Rule 5: the archived quotation states no version boundary and does not name the grafana/grafana image, so membership of 8.0.5 is not settled.

Reader 2: `in_scope` because: grafana/grafana 8.0.5 is at or after the 8.0 boundary in the event scope.

---

## Event CMP-5: Malicious flatmap-stream dependency in event-stream 3.3.6

Knowledge date (as_of): 2018-11-29

Sources:
- **npm-blog/event-stream-incident** <https://blog.npmjs.org/post/180565383195/details-about-the-event-stream-incident>
  - archive record: wayback:20181129013028 http://web.archive.org/web/20181129013028/https://blog.npmjs.org/post/180565383195/details-about-the-event-stream-incident
  - archived quotation: "The malicious package was version 0.1.1 of flatmap-stream."

References to label for this event:

- `8aea7783`: `{"ecosystem": "npm", "kind": "package", "package": "event-stream", "version": "3.3.6"}`
  - found in: sxei/vscode-plugin-demo@978fa184dc83 package-lock.json (2018-10-15)

Reader 1: `undeterminable` because: The archived quotation names only flatmap-stream 0.1.1; it does not state which event-stream versions carried it, so 3.3.6 membership is not settled by the source.

Reader 2: `in_scope` because: Event title names event-stream 3.3.6 as the version carrying the malicious flatmap-stream dependency; reference is that exact version.

---

## Event LIC-3: Grafana relicensed from Apache-2.0 to AGPLv3 from 8.0

Knowledge date (as_of): 2021-04-21

Sources:
- **grafana/relicensing-to-agplv3** <https://grafana.com/blog/2021/04/20/grafana-loki-tempo-relicensing-to-agplv3/>
  - archive record: wayback:20210421230514 http://web.archive.org/web/20210421230514/https://grafana.com/blog/2021/04/20/grafana-loki-tempo-relicensing-to-agplv3/
  - archived quotation: "We are relicensing our core open source projects from Apache 2.0 to AGPLv3."

References to label for this event:

- `90a2b443`: `{"kind": "image", "ref": "grafana/grafana:8.0.2"}`
  - found in: bcremer/docker-telegraf-influx-grafana-stack@70b806c2b8c0 docker-compose.yml (2021-06-15)

Reader 1: `in_scope` because: grafana/grafana 8.0.2 is at or after the 8.0 boundary in the event scope.

Reader 2: `undeterminable` because: Rule 5: the archived quotation states no version boundary and does not name the grafana/grafana image, so membership of 8.0.2 is not settled.

---

## Event DEP-5: go-yaml/yaml unmaintained and archived

Knowledge date (as_of): 2025-04-01

Sources:
- **go-yaml/yaml@944c86a** <https://github.com/go-yaml/yaml/commit/944c86a7d29391925ed6ac33bee98a0516f1287a>
  - archive record: record:github commit 944c86a (README)
  - archived quotation: "THIS PROJECT IS UNMAINTAINED."
- **wayback/github.com-go-yaml-yaml** <https://github.com/go-yaml/yaml>
  - archive record: wayback:20250401151649 http://web.archive.org/web/20250401151649/https://github.com/go-yaml/yaml
  - archived quotation: "README with the unmaintained notice."

References to label for this event:

- `9581a58f`: `{"ecosystem": "Go", "kind": "package", "package": "sigs.k8s.io/yaml", "version": "v1.4.0"}`
  - found in: kubernetes/kubernetes@0d3d2733f609 go.mod (2025-04-24)

Reader 1: `undeterminable` because: Rule 1: sigs.k8s.io/yaml is a different module path; the packet does not state its relation to github.com/go-yaml/yaml.

Reader 2: `out_of_scope` because: sigs.k8s.io/yaml is a different module path and project from go-yaml/yaml (rule 1).

---

## Event DIS-3: 1,051 floating openjdk tags deleted from Docker Hub

Knowledge date (as_of): 2025-11-05

Sources:
- **docker-library/official-images#20210** <https://github.com/docker-library/official-images/pull/20210>
  - archive record: wayback:20251105030321 http://web.archive.org/web/20251105030321/https://github.com/docker-library/official-images/pull/20210
  - archived quotation: "Deletes are now complete."

Archived evidence file `openjdk-2025-deleted-tags.txt`:
```
# openjdk tags deleted from Docker Hub on 2025-11-03
# Source: https://github.com/docker-library/official-images/pull/20210#issuecomment-3482847877 (tianon, 2025-11-03T22:24:16Z)
# Archived: http://web.archive.org/web/20251105030321/https://github.com/docker-library/official-images/pull/20210
# Retrieved 2026-10-30 through the GitHub API. One tag per line, exactly as listed in the comment.
openjdk:10
openjdk:10.0
openjdk:10.0-jdk
openjdk:10.0-jdk-nanoserver
openjdk:10.0-jdk-nanoserver-sac2016
openjdk:10.0-jdk-oracle
openjdk:10.0-jdk-oraclelinux7
openjdk:10.0-jdk-sid
openjdk:10.0-jdk-slim
openjdk:10.0-jdk-slim-sid
openjdk:10.0-jdk-windowsservercore
openjdk:10.0-jdk-windowsservercore-1709
openjdk:10.0-jdk-windowsservercore-ltsc2016
openjdk:10.0-jre
openjdk:10.0-jre-sid
openjdk:10.0-jre-slim
openjdk:10.0-jre-slim-sid
openjdk:10.0-nanoserver
openjdk:10.0-nanoserver-sac2016
openjdk:10.0-oracle
openjdk:10.0-oraclelinux7
openjdk:10.0-sid
openjdk:10.0-slim
openjdk:10.0-slim-sid
openjdk:10.0-windowsservercore
openjdk:10.0-windowsservercore-1709
openjdk:10.0-windowsservercore-ltsc2016
openjdk:10-jdk
openjdk:10-jdk-experimental
openjdk:10-jdk-nanoserver
openjdk:10-jdk-nanoserver-sac2016
openjdk:10-jdk-oracle
openjdk:10-jdk-oraclelinux7
openjdk:10-jdk-sid
openjdk:10-jdk-slim
openjdk:10-jdk-slim-experimental
openjdk:10-jdk-slim-sid
openjdk:10-jdk-windowsservercore
openjdk:10-jdk-windowsservercore-1709
openjdk:10-jdk-windowsservercore-ltsc2016
openjdk:10-jre
openjdk:10-jre-experimental
openjdk:10-jre-sid
openjdk:10-jre-slim
openjdk:10-jre-slim-experimental
openjdk:10-jre-slim-sid
openjdk:10-nanoserver
openjdk:10-nanoserver-sac2016
openjdk:10-oracle
openjdk:10-oraclelinux7
openjdk:10-sid
openjdk:10-slim
openjdk:10-slim-experimental
openjdk:10-slim-sid
openjdk:10-windowsservercore
openjdk:10-windowsservercore-1709
openjdk:10-windowsservercore-ltsc2016
openjdk:11
openjdk:11.0
openjdk:11.0-bullseye
openjdk:11.0-buster
openjdk:11.0-jdk
openjdk:11.0-jdk-bullseye
openjdk:11.0-jdk-buster
openjdk:11.0-jdk-nanoserver
openjdk:11.0-jdk-nanoserver-1803
openjdk:11.0-jdk-nanoserver-1809
openjdk:11.0-jdk-nanoserver-sac2016
openjdk:11.0-jdk-oracle
openjdk:11.0-jdk-oraclelinux7
openjdk:11.0-jdk-oraclelinux8
openjdk:11.0-jdk-sid
openjdk:11.0-jdk-slim
openjdk:11.0-jdk-slim-bullseye
openjdk:11.0-jdk-slim-buster
openjdk:11.0-jdk-slim-sid
openjdk:11.0-jdk-slim-stretch
openjdk:11.0-jdk-stretch
openjdk:11.0-jdk-windowsservercore
openjdk:11.0-jdk-windowsservercore-1709
openjdk:11.0-jdk-windowsservercore-1803
openjdk:11.0-jdk-windowsservercore-1809
openjdk:11.0-jdk-windowsservercore-ltsc2016
openjdk:11.0-jdk-windowsservercore-ltsc2022
openjdk:11.0-jre
openjdk:11.0-jre-bullseye
openjdk:11.0-jre-buster
openjdk:11.0-jre-nanoserver
openjdk:11.0-jre-nanoserver-1803
openjdk:11.0-jre-nanoserver-1809
openjdk:11.0-jre-sid
openjdk:11.0-jre-slim
openjdk:11.0-jre-slim-bullseye
openjdk:11.0-jre-slim-buster
openjdk:11.0-jre-slim-sid
openjdk:11.0-jre-slim-stretch
openjdk:11.0-jre-stretch
openjdk:11.0-jre-windowsservercore
openjdk:11.0-jre-windowsservercore-1803
openjdk:11.0-jre-windowsservercore-1809
openjdk:11.0-jre-windowsservercore-ltsc2016
openjdk:11.0-jre-windowsservercore-ltsc2022
openjdk:11.0-nanoserver
openjdk:11.0-nanoserver-1803
openjdk:11.0-nanoserver-1809
openjdk:11.0-nanoserver-sac2016
openjdk:11.0-oracle
openjdk:11.0-oraclelinux7
openjdk:11.0-oraclelinux8
openjdk:11.0-sid
openjdk:11.0-slim
openjdk:11.0-slim-bullseye
openjdk:11.0-slim-buster
openjdk:11.0-slim-sid
openjdk:11.0-slim-stretch
openjdk:11.0-stretch
openjdk:11.0-windowsservercore
openjdk:11.0-windowsservercore-1709
openjdk:11.0-windowsservercore-1803
openjdk:11.0-windowsservercore-1809
openjdk:11.0-windowsservercore-ltsc2016
openjdk:11.0-windowsservercore-ltsc2022
openjdk:11-bullseye
openjdk:11-buster
openjdk:11-jdk
openjdk:11-jdk-bullseye
openjdk:11-jdk-buster
openjdk:11-jdk-nanoserver
openjdk:11-jdk-nanoserver-1803
openjdk:11-jdk-nanoserver-1809
openjdk:11-jdk-nanoserver-sac2016
openjdk:11-jdk-oracle
openjdk:11-jdk-oraclelinux7
openjdk:11-jdk-oraclelinux8
openjdk:11-jdk-sid
openjdk:11-jdk-slim
openjdk:11-jdk-slim-bullseye
openjdk:11-jdk-slim-buster
openjdk:11-jdk-slim-sid
openjdk:11-jdk-slim-stretch
openjdk:11-jdk-stretch
openjdk:11-jdk-windowsservercore
openjdk:11-jdk-windowsservercore-1709
openjdk:11-jdk-windowsservercore-1803
openjdk:11-jdk-windowsservercore-1809
openjdk:11-jdk-windowsservercore-ltsc2016
openjdk:11-jdk-windowsservercore-ltsc2022
openjdk:11-jre
openjdk:11-jre-bullseye
openjdk:11-jre-buster
openjdk:11-jre-nanoserver
openjdk:11-jre-nanoserver-1803
openjdk:11-jre-nanoserver-1809
openjdk:11-jre-sid
openjdk:11-jre-slim
openjdk:11-jre-slim-bullseye
openjdk:11-jre-slim-buster
openjdk:11-jre-slim-sid
openjdk:11-jre-slim-stretch
openjdk:11-jre-stretch
openjdk:11-jre-windowsservercore
openjdk:11-jre-windowsservercore-1803
openjdk:11-jre-windowsservercore-1809
openjdk:11-jre-windowsservercore-ltsc2016
openjdk:11-jre-windowsservercore-ltsc2022
openjdk:11-nanoserver
openjdk:11-nanoserver-1803
openjdk:11-nanoserver-1809
openjdk:11-nanoserver-sac2016
openjdk:11-oracle
openjdk:11-oraclelinux7
openjdk:11-oraclelinux8
openjdk:11-sid
openjdk:11-slim
openjdk:11-slim-bullseye
openjdk:11-slim-buster
openjdk:11-slim-sid
openjdk:11-slim-stretch
openjdk:11-stretch
openjdk:11-windowsservercore
openjdk:11-windowsservercore-1709
openjdk:11-windowsservercore-1803
openjdk:11-windowsservercore-1809
openjdk:11-windowsservercore-ltsc2016
openjdk:11-windowsservercore-ltsc2022
openjdk:12
openjdk:12.0
openjdk:12.0-jdk
openjdk:12.0-jdk-oracle
openjdk:12.0-jdk-oraclelinux7
openjdk:12.0-jdk-windowsservercore
openjdk:12.0-jdk-windowsservercore-1803
openjdk:12.0-jdk-windowsservercore-1809
openjdk:12.0-jdk-windowsservercore-ltsc2016
openjdk:12.0-oracle
openjdk:12.0-oraclelinux7
openjdk:12.0-windowsservercore
openjdk:12.0-windowsservercore-1803
openjdk:12.0-windowsservercore-1809
openjdk:12.0-windowsservercore-ltsc2016
openjdk:12-alpine
openjdk:12-alpine3.8
openjdk:12-alpine3.9
openjdk:12-jdk
openjdk:12-jdk-alpine
openjdk:12-jdk-alpine3.8
openjdk:12-jdk-alpine3.9
openjdk:12-jdk-nanoserver
openjdk:12-jdk-nanoserver-sac2016
openjdk:12-jdk-oracle
openjdk:12-jdk-oraclelinux7
openjdk:12-jdk-windowsservercore
openjdk:12-jdk-windowsservercore-1709
openjdk:12-jdk-windowsservercore-1803
openjdk:12-jdk-windowsservercore-1809
openjdk:12-jdk-windowsservercore-ltsc2016
openjdk:12-nanoserver
openjdk:12-nanoserver-sac2016
openjdk:12-oracle
openjdk:12-oraclelinux7
openjdk:12-windowsservercore
openjdk:12-windowsservercore-1709
openjdk:12-windowsservercore-1803
openjdk:12-windowsservercore-1809
openjdk:12-windowsservercore-ltsc2016
openjdk:13
openjdk:13.0
openjdk:13.0-buster
openjdk:13.0-jdk
openjdk:13.0-jdk-buster
openjdk:13.0-jdk-nanoserver
openjdk:13.0-jdk-nanoserver-1803
openjdk:13.0-jdk-nanoserver-1809
openjdk:13.0-jdk-oracle
openjdk:13.0-jdk-oraclelinux7
openjdk:13.0-jdk-slim
openjdk:13.0-jdk-slim-buster
openjdk:13.0-jdk-windowsservercore
openjdk:13.0-jdk-windowsservercore-1803
openjdk:13.0-jdk-windowsservercore-1809
openjdk:13.0-jdk-windowsservercore-ltsc2016
openjdk:13.0-nanoserver
openjdk:13.0-nanoserver-1803
openjdk:13.0-nanoserver-1809
openjdk:13.0-oracle
openjdk:13.0-oraclelinux7
openjdk:13.0-slim
openjdk:13.0-slim-buster
openjdk:13.0-windowsservercore
openjdk:13.0-windowsservercore-1803
openjdk:13.0-windowsservercore-1809
openjdk:13.0-windowsservercore-ltsc2016
openjdk:13-alpine
openjdk:13-alpine3.10
openjdk:13-alpine3.8
openjdk:13-alpine3.9
openjdk:13-buster
openjdk:13-jdk
openjdk:13-jdk-alpine
openjdk:13-jdk-alpine3.10
openjdk:13-jdk-alpine3.8
openjdk:13-jdk-alpine3.9
openjdk:13-jdk-buster
openjdk:13-jdk-nanoserver
openjdk:13-jdk-nanoserver-1803
openjdk:13-jdk-nanoserver-1809
openjdk:13-jdk-nanoserver-sac2016
openjdk:13-jdk-oracle
openjdk:13-jdk-oraclelinux7
openjdk:13-jdk-slim
openjdk:13-jdk-slim-buster
openjdk:13-jdk-windowsservercore
openjdk:13-jdk-windowsservercore-1709
openjdk:13-jdk-windowsservercore-1803
openjdk:13-jdk-windowsservercore-1809
openjdk:13-jdk-windowsservercore-ltsc2016
openjdk:13-nanoserver
openjdk:13-nanoserver-1803
openjdk:13-nanoserver-1809
openjdk:13-nanoserver-sac2016
openjdk:13-oracle
openjdk:13-oraclelinux7
openjdk:13-slim
openjdk:13-slim-buster
openjdk:13-windowsservercore
openjdk:13-windowsservercore-1709
openjdk:13-windowsservercore-1803
openjdk:13-windowsservercore-1809
openjdk:13-windowsservercore-ltsc2016
openjdk:14
openjdk:14.0
openjdk:14.0-buster
openjdk:14.0-jdk
openjdk:14.0-jdk-buster
openjdk:14.0-jdk-nanoserver
openjdk:14.0-jdk-nanoserver-1809
openjdk:14.0-jdk-oracle
openjdk:14.0-jdk-oraclelinux7
openjdk:14.0-jdk-oraclelinux8
openjdk:14.0-jdk-slim
openjdk:14.0-jdk-slim-buster
openjdk:14.0-jdk-windowsservercore
openjdk:14.0-jdk-windowsservercore-1809
openjdk:14.0-jdk-windowsservercore-ltsc2016
openjdk:14.0-nanoserver
openjdk:14.0-nanoserver-1809
openjdk:14.0-oracle
openjdk:14.0-oraclelinux7
openjdk:14.0-oraclelinux8
openjdk:14.0-slim
openjdk:14.0-slim-buster
openjdk:14.0-windowsservercore
openjdk:14.0-windowsservercore-1809
openjdk:14.0-windowsservercore-ltsc2016
openjdk:14-alpine
openjdk:14-alpine3.10
openjdk:14-buster
openjdk:14-jdk
openjdk:14-jdk-alpine
openjdk:14-jdk-alpine3.10
openjdk:14-jdk-buster
openjdk:14-jdk-nanoserver
openjdk:14-jdk-nanoserver-1803
openjdk:14-jdk-nanoserver-1809
openjdk:14-jdk-oracle
openjdk:14-jdk-oraclelinux7
openjdk:14-jdk-oraclelinux8
openjdk:14-jdk-slim
openjdk:14-jdk-slim-buster
openjdk:14-jdk-windowsservercore
openjdk:14-jdk-windowsservercore-1803
openjdk:14-jdk-windowsservercore-1809
openjdk:14-jdk-windowsservercore-ltsc2016
openjdk:14-nanoserver
openjdk:14-nanoserver-1803
openjdk:14-nanoserver-1809
openjdk:14-oracle
openjdk:14-oraclelinux7
openjdk:14-oraclelinux8
openjdk:14-slim
openjdk:14-slim-buster
openjdk:14-windowsservercore
openjdk:14-windowsservercore-1803
openjdk:14-windowsservercore-1809
openjdk:14-windowsservercore-ltsc2016
openjdk:15
openjdk:15.0
openjdk:15.0-buster
openjdk:15.0-jdk
openjdk:15.0-jdk-buster
openjdk:15.0-jdk-nanoserver
openjdk:15.0-jdk-nanoserver-1809
openjdk:15.0-jdk-oracle
openjdk:15.0-jdk-oraclelinux7
openjdk:15.0-jdk-oraclelinux8
openjdk:15.0-jdk-slim
openjdk:15.0-jdk-slim-buster
openjdk:15.0-jdk-windowsservercore
openjdk:15.0-jdk-windowsservercore-1809
openjdk:15.0-jdk-windowsservercore-ltsc2016
openjdk:15.0-nanoserver
openjdk:15.0-nanoserver-1809
openjdk:15.0-oracle
openjdk:15.0-oraclelinux7
openjdk:15.0-oraclelinux8
openjdk:15.0-slim
openjdk:15.0-slim-buster
openjdk:15.0-windowsservercore
openjdk:15.0-windowsservercore-1809
openjdk:15.0-windowsservercore-ltsc2016
openjdk:15-alpine
openjdk:15-alpine3.11
openjdk:15-alpine3.12
openjdk:15-buster
openjdk:15-jdk
openjdk:15-jdk-alpine
openjdk:15-jdk-alpine3.11
openjdk:15-jdk-alpine3.12
openjdk:15-jdk-buster
openjdk:15-jdk-nanoserver
openjdk:15-jdk-nanoserver-1809
openjdk:15-jdk-oracle
openjdk:15-jdk-oraclelinux7
openjdk:15-jdk-oraclelinux8
openjdk:15-jdk-slim
openjdk:15-jdk-slim-buster
openjdk:15-jdk-windowsservercore
openjdk:15-jdk-windowsservercore-1809
openjdk:15-jdk-windowsservercore-ltsc2016
openjdk:15-nanoserver
openjdk:15-nanoserver-1809
openjdk:15-oracle
openjdk:15-oraclelinux7
openjdk:15-oraclelinux8
openjdk:15-slim
openjdk:15-slim-buster
openjdk:15-windowsservercore
openjdk:15-windowsservercore-1809
openjdk:15-windowsservercore-ltsc2016
openjdk:16
openjdk:16.0
openjdk:16.0-bullseye
openjdk:16.0-buster
openjdk:16.0-jdk
openjdk:16.0-jdk-bullseye
openjdk:16.0-jdk-buster
openjdk:16.0-jdk-nanoserver
openjdk:16.0-jdk-nanoserver-1809
openjdk:16.0-jdk-oracle
openjdk:16.0-jdk-oraclelinux7
openjdk:16.0-jdk-oraclelinux8
openjdk:16.0-jdk-slim
openjdk:16.0-jdk-slim-bullseye
openjdk:16.0-jdk-slim-buster
openjdk:16.0-jdk-windowsservercore
openjdk:16.0-jdk-windowsservercore-1809
openjdk:16.0-jdk-windowsservercore-ltsc2016
openjdk:16.0-nanoserver
openjdk:16.0-nanoserver-1809
openjdk:16.0-oracle
openjdk:16.0-oraclelinux7
openjdk:16.0-oraclelinux8
openjdk:16.0-slim
openjdk:16.0-slim-bullseye
openjdk:16.0-slim-buster
openjdk:16.0-windowsservercore
openjdk:16.0-windowsservercore-1809
openjdk:16.0-windowsservercore-ltsc2016
openjdk:16-alpine
openjdk:16-alpine3.12
openjdk:16-alpine3.13
openjdk:16-bullseye
openjdk:16-buster
openjdk:16-jdk
openjdk:16-jdk-alpine
openjdk:16-jdk-alpine3.12
openjdk:16-jdk-alpine3.13
openjdk:16-jdk-bullseye
openjdk:16-jdk-buster
openjdk:16-jdk-nanoserver
openjdk:16-jdk-nanoserver-1809
openjdk:16-jdk-oracle
openjdk:16-jdk-oraclelinux7
openjdk:16-jdk-oraclelinux8
openjdk:16-jdk-slim
openjdk:16-jdk-slim-bullseye
openjdk:16-jdk-slim-buster
openjdk:16-jdk-windowsservercore
openjdk:16-jdk-windowsservercore-1809
openjdk:16-jdk-windowsservercore-ltsc2016
openjdk:16-nanoserver
openjdk:16-nanoserver-1809
openjdk:16-oracle
openjdk:16-oraclelinux7
openjdk:16-oraclelinux8
openjdk:16-slim
openjdk:16-slim-bullseye
openjdk:16-slim-buster
openjdk:16-windowsservercore
openjdk:16-windowsservercore-1809
openjdk:16-windowsservercore-ltsc2016
openjdk:17
openjdk:17.0
openjdk:17.0-bullseye
openjdk:17.0-buster
openjdk:17.0-jdk
openjdk:17.0-jdk-bullseye
openjdk:17.0-jdk-buster
openjdk:17.0-jdk-nanoserver
openjdk:17.0-jdk-nanoserver-1809
openjdk:17.0-jdk-oracle
openjdk:17.0-jdk-oraclelinux7
openjdk:17.0-jdk-oraclelinux8
openjdk:17.0-jdk-slim
openjdk:17.0-jdk-slim-bullseye
openjdk:17.0-jdk-slim-buster
openjdk:17.0-jdk-windowsservercore
openjdk:17.0-jdk-windowsservercore-1809
openjdk:17.0-jdk-windowsservercore-ltsc2016
openjdk:17.0-jdk-windowsservercore-ltsc2022
openjdk:17.0-nanoserver
openjdk:17.0-nanoserver-1809
openjdk:17.0-oracle
openjdk:17.0-oraclelinux7
openjdk:17.0-oraclelinux8
openjdk:17.0-slim
openjdk:17.0-slim-bullseye
openjdk:17.0-slim-buster
openjdk:17.0-windowsservercore
openjdk:17.0-windowsservercore-1809
openjdk:17.0-windowsservercore-ltsc2016
openjdk:17.0-windowsservercore-ltsc2022
openjdk:17-alpine
openjdk:17-alpine3.12
openjdk:17-alpine3.13
openjdk:17-alpine3.14
openjdk:17-bullseye
openjdk:17-buster
openjdk:17-jdk
openjdk:17-jdk-alpine
openjdk:17-jdk-alpine3.12
openjdk:17-jdk-alpine3.13
openjdk:17-jdk-alpine3.14
openjdk:17-jdk-bullseye
openjdk:17-jdk-buster
openjdk:17-jdk-nanoserver
openjdk:17-jdk-nanoserver-1809
openjdk:17-jdk-oracle
openjdk:17-jdk-oraclelinux7
openjdk:17-jdk-oraclelinux8
openjdk:17-jdk-slim
openjdk:17-jdk-slim-bullseye
openjdk:17-jdk-slim-buster
openjdk:17-jdk-windowsservercore
openjdk:17-jdk-windowsservercore-1809
openjdk:17-jdk-windowsservercore-ltsc2016
openjdk:17-jdk-windowsservercore-ltsc2022
openjdk:17-nanoserver
openjdk:17-nanoserver-1809
openjdk:17-oracle
openjdk:17-oraclelinux7
openjdk:17-oraclelinux8
openjdk:17-slim
openjdk:17-slim-bullseye
openjdk:17-slim-buster
openjdk:17-windowsservercore
openjdk:17-windowsservercore-1809
openjdk:17-windowsservercore-ltsc2016
openjdk:17-windowsservercore-ltsc2022
openjdk:18
openjdk:18.0
openjdk:18.0-bullseye
openjdk:18.0-buster
openjdk:18.0-jdk
openjdk:18.0-jdk-bullseye
openjdk:18.0-jdk-buster
openjdk:18.0-jdk-nanoserver
openjdk:18.0-jdk-nanoserver-1809
openjdk:18.0-jdk-oracle
openjdk:18.0-jdk-oraclelinux7
openjdk:18.0-jdk-oraclelinux8
openjdk:18.0-jdk-slim
openjdk:18.0-jdk-slim-bullseye
openjdk:18.0-jdk-slim-buster
openjdk:18.0-jdk-windowsservercore
openjdk:18.0-jdk-windowsservercore-1809
openjdk:18.0-jdk-windowsservercore-ltsc2022
openjdk:18.0-nanoserver
openjdk:18.0-nanoserver-1809
openjdk:18.0-oracle
openjdk:18.0-oraclelinux7
openjdk:18.0-oraclelinux8
openjdk:18.0-slim
openjdk:18.0-slim-bullseye
openjdk:18.0-slim-buster
openjdk:18.0-windowsservercore
openjdk:18.0-windowsservercore-1809
openjdk:18.0-windowsservercore-ltsc2022
openjdk:18-alpine
openjdk:18-alpine3.13
openjdk:18-alpine3.14
openjdk:18-alpine3.15
openjdk:18-bullseye
openjdk:18-buster
openjdk:18-jdk
openjdk:18-jdk-alpine
openjdk:18-jdk-alpine3.13
openjdk:18-jdk-alpine3.14
openjdk:18-jdk-alpine3.15
openjdk:18-jdk-bullseye
openjdk:18-jdk-buster
openjdk:18-jdk-nanoserver
openjdk:18-jdk-nanoserver-1809
openjdk:18-jdk-oracle
openjdk:18-jdk-oraclelinux7
openjdk:18-jdk-oraclelinux8
openjdk:18-jdk-slim
openjdk:18-jdk-slim-bullseye
openjdk:18-jdk-slim-buster
openjdk:18-jdk-windowsservercore
openjdk:18-jdk-windowsservercore-1809
openjdk:18-jdk-windowsservercore-ltsc2016
openjdk:18-jdk-windowsservercore-ltsc2022
openjdk:18-nanoserver
openjdk:18-nanoserver-1809
openjdk:18-oracle
openjdk:18-oraclelinux7
openjdk:18-oraclelinux8
openjdk:18-slim
openjdk:18-slim-bullseye
openjdk:18-slim-buster
openjdk:18-windowsservercore
openjdk:18-windowsservercore-1809
openjdk:18-windowsservercore-ltsc2016
openjdk:18-windowsservercore-ltsc2022
openjdk:19
openjdk:19-alpine
openjdk:19-alpine3.14
openjdk:19-alpine3.15
openjdk:19-alpine3.16
openjdk:19-bullseye
openjdk:19-buster
openjdk:19-jdk
openjdk:19-jdk-alpine
openjdk:19-jdk-alpine3.14
openjdk:19-jdk-alpine3.15
openjdk:19-jdk-alpine3.16
openjdk:19-jdk-bullseye
openjdk:19-jdk-buster
openjdk:19-jdk-nanoserver
openjdk:19-jdk-nanoserver-1809
openjdk:19-jdk-oracle
openjdk:19-jdk-oraclelinux7
openjdk:19-jdk-oraclelinux8
openjdk:19-jdk-slim
openjdk:19-jdk-slim-bullseye
openjdk:19-jdk-slim-buster
openjdk:19-jdk-windowsservercore
openjdk:19-jdk-windowsservercore-1809
openjdk:19-jdk-windowsservercore-ltsc2016
openjdk:19-jdk-windowsservercore-ltsc2022
openjdk:19-nanoserver
openjdk:19-nanoserver-1809
openjdk:19-oracle
openjdk:19-oraclelinux7
openjdk:19-oraclelinux8
openjdk:19-slim
openjdk:19-slim-bullseye
openjdk:19-slim-buster
openjdk:19-windowsservercore
openjdk:19-windowsservercore-1809
openjdk:19-windowsservercore-ltsc2016
openjdk:19-windowsservercore-ltsc2022
openjdk:20
openjdk:20-bullseye
openjdk:20-buster
openjdk:20-jdk
openjdk:20-jdk-bullseye
openjdk:20-jdk-buster
openjdk:20-jdk-nanoserver
openjdk:20-jdk-nanoserver-1809
openjdk:20-jdk-oracle
openjdk:20-jdk-oraclelinux7
openjdk:20-jdk-oraclelinux8
openjdk:20-jdk-slim
openjdk:20-jdk-slim-bullseye
openjdk:20-jdk-slim-buster
openjdk:20-jdk-windowsservercore
openjdk:20-jdk-windowsservercore-1809
openjdk:20-jdk-windowsservercore-ltsc2022
openjdk:20-nanoserver
openjdk:20-nanoserver-1809
openjdk:20-oracle
openjdk:20-oraclelinux7
openjdk:20-oraclelinux8
openjdk:20-slim
openjdk:20-slim-bullseye
openjdk:20-slim-buster
openjdk:20-windowsservercore
openjdk:20-windowsservercore-1809
openjdk:20-windowsservercore-ltsc2022
openjdk:21
openjdk:21-bookworm
openjdk:21-bullseye
openjdk:21-buster
openjdk:21-jdk
openjdk:21-jdk-bookworm
openjdk:21-jdk-bullseye
openjdk:21-jdk-buster
openjdk:21-jdk-nanoserver
openjdk:21-jdk-nanoserver-1809
openjdk:21-jdk-oracle
openjdk:21-jdk-oraclelinux7
openjdk:21-jdk-oraclelinux8
openjdk:21-jdk-slim
openjdk:21-jdk-slim-bookworm
openjdk:21-jdk-slim-bullseye
openjdk:21-jdk-slim-buster
openjdk:21-jdk-windowsservercore
openjdk:21-jdk-windowsservercore-1809
openjdk:21-jdk-windowsservercore-ltsc2022
openjdk:21-nanoserver
openjdk:21-nanoserver-1809
openjdk:21-oracle
openjdk:21-oraclelinux7
openjdk:21-oraclelinux8
openjdk:21-slim
openjdk:21-slim-bookworm
openjdk:21-slim-bullseye
openjdk:21-slim-buster
openjdk:21-windowsservercore
openjdk:21-windowsservercore-1809
openjdk:21-windowsservercore-ltsc2022
openjdk:22
openjdk:22-bookworm
openjdk:22-bullseye
openjdk:22-buster
openjdk:22-slim
openjdk:22-slim-bookworm
openjdk:22-slim-bullseye
openjdk:22-slim-buster
openjdk:22-windowsservercore
openjdk:22-windowsservercore-1809
openjdk:22-windowsservercore-ltsc2022
openjdk:23
openjdk:23-bookworm
openjdk:23-bullseye
openjdk:23-jdk
openjdk:23-jdk-bookworm
openjdk:23-jdk-bullseye
openjdk:23-jdk-nanoserver
openjdk:23-jdk-nanoserver-1809
openjdk:23-jdk-oracle
openjdk:23-jdk-oraclelinux7
openjdk:23-jdk-oraclelinux8
openjdk:23-jdk-oraclelinux9
openjdk:23-jdk-slim
openjdk:23-jdk-slim-bookworm
openjdk:23-jdk-slim-bullseye
openjdk:23-jdk-windowsservercore
openjdk:23-jdk-windowsservercore-1809
openjdk:23-jdk-windowsservercore-ltsc2022
openjdk:23-nanoserver
openjdk:23-nanoserver-1809
openjdk:23-oracle
openjdk:23-oraclelinux7
openjdk:23-oraclelinux8
openjdk:23-oraclelinux9
openjdk:23-slim
openjdk:23-slim-bookworm
openjdk:23-slim-bullseye
openjdk:23-windowsservercore
openjdk:23-windowsservercore-1809
openjdk:23-windowsservercore-ltsc2022
openjdk:24
openjdk:24-bookworm
openjdk:24-bullseye
openjdk:24-jdk
openjdk:24-jdk-bookworm
openjdk:24-jdk-bullseye
openjdk:24-jdk-nanoserver
openjdk:24-jdk-nanoserver-1809
openjdk:24-jdk-nanoserver-ltsc2022
openjdk:24-jdk-nanoserver-ltsc2025
openjdk:24-jdk-oracle
openjdk:24-jdk-oraclelinux8
openjdk:24-jdk-oraclelinux9
openjdk:24-jdk-slim
openjdk:24-jdk-slim-bookworm
openjdk:24-jdk-slim-bullseye
openjdk:24-jdk-windowsservercore
openjdk:24-jdk-windowsservercore-1809
openjdk:24-jdk-windowsservercore-ltsc2022
openjdk:24-jdk-windowsservercore-ltsc2025
openjdk:24-nanoserver
openjdk:24-nanoserver-1809
openjdk:24-nanoserver-ltsc2022
openjdk:24-nanoserver-ltsc2025
openjdk:24-oracle
openjdk:24-oraclelinux8
openjdk:24-oraclelinux9
openjdk:24-slim
openjdk:24-slim-bookworm
openjdk:24-slim-bullseye
openjdk:24-windowsservercore
openjdk:24-windowsservercore-1809
openjdk:24-windowsservercore-ltsc2022
openjdk:24-windowsservercore-ltsc2025
openjdk:25
openjdk:25-bookworm
openjdk:25-bullseye
openjdk:25-jdk
openjdk:25-jdk-bookworm
openjdk:25-jdk-bullseye
openjdk:25-jdk-nanoserver
openjdk:25-jdk-nanoserver-1809
openjdk:25-jdk-nanoserver-ltsc2022
openjdk:25-jdk-nanoserver-ltsc2025
openjdk:25-jdk-oracle
openjdk:25-jdk-oraclelinux8
openjdk:25-jdk-oraclelinux9
openjdk:25-jdk-slim
openjdk:25-jdk-slim-bookworm
openjdk:25-jdk-slim-bullseye
openjdk:25-jdk-slim-trixie
openjdk:25-jdk-trixie
openjdk:25-jdk-windowsservercore
openjdk:25-jdk-windowsservercore-1809
openjdk:25-jdk-windowsservercore-ltsc2022
openjdk:25-jdk-windowsservercore-ltsc2025
openjdk:25-nanoserver
openjdk:25-nanoserver-1809
openjdk:25-nanoserver-ltsc2022
openjdk:25-nanoserver-ltsc2025
openjdk:25-oracle
openjdk:25-oraclelinux8
openjdk:25-oraclelinux9
openjdk:25-slim
openjdk:25-slim-bookworm
openjdk:25-slim-bullseye
openjdk:25-slim-trixie
openjdk:25-trixie
openjdk:25-windowsservercore
openjdk:25-windowsservercore-1809
openjdk:25-windowsservercore-ltsc2022
openjdk:25-windowsservercore-ltsc2025
openjdk:26
openjdk:26-bookworm
openjdk:26-bullseye
openjdk:26-jdk
openjdk:26-jdk-bookworm
openjdk:26-jdk-bullseye
openjdk:26-jdk-nanoserver
openjdk:26-jdk-nanoserver-ltsc2022
openjdk:26-jdk-nanoserver-ltsc2025
openjdk:26-jdk-oracle
openjdk:26-jdk-oraclelinux8
openjdk:26-jdk-oraclelinux9
openjdk:26-jdk-slim
openjdk:26-jdk-slim-bookworm
openjdk:26-jdk-slim-bullseye
openjdk:26-jdk-slim-trixie
openjdk:26-jdk-trixie
openjdk:26-jdk-windowsservercore
openjdk:26-jdk-windowsservercore-ltsc2022
openjdk:26-jdk-windowsservercore-ltsc2025
openjdk:26-nanoserver
openjdk:26-nanoserver-ltsc2022
openjdk:26-nanoserver-ltsc2025
openjdk:26-oracle
openjdk:26-oraclelinux8
openjdk:26-oraclelinux9
openjdk:26-slim
openjdk:26-slim-bookworm
openjdk:26-slim-bullseye
openjdk:26-slim-trixie
openjdk:26-trixie
openjdk:26-windowsservercore
openjdk:26-windowsservercore-ltsc2022
openjdk:26-windowsservercore-ltsc2025
openjdk:6
openjdk:6-jdk
openjdk:6-jdk-slim
openjdk:6-jdk-slim-wheezy
openjdk:6-jdk-wheezy
openjdk:6-jre
openjdk:6-jre-slim
openjdk:6-jre-slim-wheezy
openjdk:6-jre-wheezy
openjdk:6-slim
openjdk:6-slim-wheezy
openjdk:6-wheezy
openjdk:7
openjdk:7-alpine
openjdk:7-alpine3.7
openjdk:7-alpine3.8
openjdk:7-alpine3.9
openjdk:7-jdk
openjdk:7-jdk-alpine
openjdk:7-jdk-alpine3.7
openjdk:7-jdk-alpine3.8
openjdk:7-jdk-alpine3.9
openjdk:7-jdk-jessie
openjdk:7-jdk-slim
openjdk:7-jdk-slim-jessie
openjdk:7-jessie
openjdk:7-jre
openjdk:7-jre-alpine
openjdk:7-jre-alpine3.7
openjdk:7-jre-alpine3.8
openjdk:7-jre-alpine3.9
openjdk:7-jre-jessie
openjdk:7-jre-slim
openjdk:7-jre-slim-jessie
openjdk:7-slim
openjdk:7-slim-jessie
openjdk:8
openjdk:8-alpine
openjdk:8-alpine3.7
openjdk:8-alpine3.8
openjdk:8-alpine3.9
openjdk:8-bullseye
openjdk:8-buster
openjdk:8-jdk
openjdk:8-jdk-alpine
openjdk:8-jdk-alpine3.7
openjdk:8-jdk-alpine3.8
openjdk:8-jdk-alpine3.9
openjdk:8-jdk-bullseye
openjdk:8-jdk-buster
openjdk:8-jdk-nanoserver
openjdk:8-jdk-nanoserver-1803
openjdk:8-jdk-nanoserver-1809
openjdk:8-jdk-nanoserver-sac2016
openjdk:8-jdk-oracle
openjdk:8-jdk-oraclelinux7
openjdk:8-jdk-oraclelinux8
openjdk:8-jdk-slim
openjdk:8-jdk-slim-bullseye
openjdk:8-jdk-slim-buster
openjdk:8-jdk-slim-stretch
openjdk:8-jdk-stretch
openjdk:8-jdk-windowsservercore
openjdk:8-jdk-windowsservercore-1709
openjdk:8-jdk-windowsservercore-1803
openjdk:8-jdk-windowsservercore-1809
openjdk:8-jdk-windowsservercore-ltsc2016
openjdk:8-jdk-windowsservercore-ltsc2022
openjdk:8-jre
openjdk:8-jre-alpine
openjdk:8-jre-alpine3.7
openjdk:8-jre-alpine3.8
openjdk:8-jre-alpine3.9
openjdk:8-jre-bullseye
openjdk:8-jre-buster
openjdk:8-jre-nanoserver
openjdk:8-jre-nanoserver-1803
openjdk:8-jre-nanoserver-1809
openjdk:8-jre-slim
openjdk:8-jre-slim-bullseye
openjdk:8-jre-slim-buster
openjdk:8-jre-slim-stretch
openjdk:8-jre-stretch
openjdk:8-jre-windowsservercore
openjdk:8-jre-windowsservercore-1803
openjdk:8-jre-windowsservercore-1809
openjdk:8-jre-windowsservercore-ltsc2016
openjdk:8-jre-windowsservercore-ltsc2022
openjdk:8-nanoserver
openjdk:8-nanoserver-1803
openjdk:8-nanoserver-1809
openjdk:8-nanoserver-sac2016
openjdk:8-oracle
openjdk:8-oraclelinux7
openjdk:8-oraclelinux8
openjdk:8-slim
openjdk:8-slim-bullseye
openjdk:8-slim-buster
openjdk:8-slim-stretch
openjdk:8-stretch
openjdk:8-windowsservercore
openjdk:8-windowsservercore-1709
openjdk:8-windowsservercore-1803
openjdk:8-windowsservercore-1809
openjdk:8-windowsservercore-ltsc2016
openjdk:8-windowsservercore-ltsc2022
openjdk:9
openjdk:9.0
openjdk:9.0-jdk
openjdk:9.0-jdk-nanoserver
openjdk:9.0-jdk-nanoserver-sac2016
openjdk:9.0-jdk-sid
openjdk:9.0-jdk-slim
openjdk:9.0-jdk-slim-sid
openjdk:9.0-jdk-windowsservercore
openjdk:9.0-jdk-windowsservercore-1709
openjdk:9.0-jdk-windowsservercore-ltsc2016
openjdk:9.0-jre
openjdk:9.0-jre-sid
openjdk:9.0-jre-slim
openjdk:9.0-jre-slim-sid
openjdk:9.0-nanoserver
openjdk:9.0-nanoserver-sac2016
openjdk:9.0-sid
openjdk:9.0-slim
openjdk:9.0-slim-sid
openjdk:9.0-windowsservercore
openjdk:9.0-windowsservercore-1709
openjdk:9.0-windowsservercore-ltsc2016
openjdk:9-jdk
openjdk:9-jdk-nanoserver
openjdk:9-jdk-nanoserver-sac2016
openjdk:9-jdk-sid
openjdk:9-jdk-slim
openjdk:9-jdk-slim-sid
openjdk:9-jdk-windowsservercore
openjdk:9-jdk-windowsservercore-1709
openjdk:9-jdk-windowsservercore-ltsc2016
openjdk:9-jre
openjdk:9-jre-sid
openjdk:9-jre-slim
openjdk:9-jre-slim-sid
openjdk:9-nanoserver
openjdk:9-nanoserver-sac2016
openjdk:9-sid
openjdk:9-slim
openjdk:9-slim-sid
openjdk:9-windowsservercore
openjdk:9-windowsservercore-1709
openjdk:9-windowsservercore-ltsc2016
openjdk:alpine
openjdk:alpine3.7
openjdk:alpine3.8
openjdk:bullseye
openjdk:buster
openjdk:jdk
openjdk:jdk-alpine
openjdk:jdk-alpine3.7
openjdk:jdk-alpine3.8
openjdk:jdk-bullseye
openjdk:jdk-buster
openjdk:jdk-nanoserver
openjdk:jdk-nanoserver-1803
openjdk:jdk-nanoserver-1809
openjdk:jdk-nanoserver-sac2016
openjdk:jdk-oracle
openjdk:jdk-oraclelinux7
openjdk:jdk-oraclelinux8
openjdk:jdk-sid
openjdk:jdk-slim
openjdk:jdk-slim-bullseye
openjdk:jdk-slim-buster
openjdk:jdk-slim-sid
openjdk:jdk-slim-stretch
openjdk:jdk-stretch
openjdk:jdk-windowsservercore
openjdk:jdk-windowsservercore-1709
openjdk:jdk-windowsservercore-1803
openjdk:jdk-windowsservercore-1809
openjdk:jdk-windowsservercore-ltsc2016
openjdk:jdk-windowsservercore-ltsc2022
openjdk:jre
openjdk:jre-alpine
openjdk:jre-alpine3.7
openjdk:jre-alpine3.8
openjdk:jre-sid
openjdk:jre-slim
openjdk:jre-slim-sid
openjdk:jre-slim-stretch
openjdk:jre-stretch
openjdk:latest
openjdk:nanoserver
openjdk:nanoserver-1803
openjdk:nanoserver-1809
openjdk:nanoserver-sac2016
openjdk:oracle
openjdk:oraclelinux7
openjdk:oraclelinux8
openjdk:sid
openjdk:slim
openjdk:slim-bullseye
openjdk:slim-buster
openjdk:slim-sid
openjdk:slim-stretch
openjdk:stretch
openjdk:windowsservercore
openjdk:windowsservercore-1709
openjdk:windowsservercore-1803
openjdk:windowsservercore-1809
openjdk:windowsservercore-ltsc2016
openjdk:windowsservercore-ltsc2022
```

References to label for this event:

- `a25fa6b2`: `{"kind": "image", "ref": "openjdk:8u342-jre"}`
  - found in: arempter/hive-metastore-docker@e15fc5116d10 Dockerfile (2023-01-31)

Reader 1: `out_of_scope` because: openjdk:8u342-jre is not in the complete deleted tag list.

Reader 2: `undeterminable` because: Rule 4: openjdk:8u342-jre is not in the deleted-tags list, and the sources do not state the list covers every changed tag.

---

## Event LIC-3: Grafana relicensed from Apache-2.0 to AGPLv3 from 8.0

Knowledge date (as_of): 2021-04-21

Sources:
- **grafana/relicensing-to-agplv3** <https://grafana.com/blog/2021/04/20/grafana-loki-tempo-relicensing-to-agplv3/>
  - archive record: wayback:20210421230514 http://web.archive.org/web/20210421230514/https://grafana.com/blog/2021/04/20/grafana-loki-tempo-relicensing-to-agplv3/
  - archived quotation: "We are relicensing our core open source projects from Apache 2.0 to AGPLv3."

References to label for this event:

- `a63f07a0`: `{"kind": "image", "ref": "grafana/grafana:7.5.5"}`
  - found in: warriorBrian/nuxt-blog@ee3d8b87420b prometheus/docker-compose.yml (2021-05-24)

Reader 1: `out_of_scope` because: 7.5.5 is before the 8.0 boundary in the event scope.

Reader 2: `undeterminable` because: Rule 5: the archived quotation says core projects are relicensed but states no version boundary; the 8.0 boundary appears only in the event title, not in a source.

---

## Event LIC-3: Grafana relicensed from Apache-2.0 to AGPLv3 from 8.0

Knowledge date (as_of): 2021-04-21

Sources:
- **grafana/relicensing-to-agplv3** <https://grafana.com/blog/2021/04/20/grafana-loki-tempo-relicensing-to-agplv3/>
  - archive record: wayback:20210421230514 http://web.archive.org/web/20210421230514/https://grafana.com/blog/2021/04/20/grafana-loki-tempo-relicensing-to-agplv3/
  - archived quotation: "We are relicensing our core open source projects from Apache 2.0 to AGPLv3."

References to label for this event:

- `aa979c36`: `{"kind": "image", "ref": "grafana/grafana:7.5.2"}`
  - found in: testinggospels/camouflage@7599ad9f269c docker-compose.yml (2021-05-19)

Reader 1: `undeterminable` because: Rule 5: the archived quotation states no version boundary, so whether 7.5.2 is relicensed is not settled by the source.

Reader 2: `out_of_scope` because: 7.5.2 is before the 8.0 boundary in the event scope.

---

## Event LIC-3: Grafana relicensed from Apache-2.0 to AGPLv3 from 8.0

Knowledge date (as_of): 2021-04-21

Sources:
- **grafana/relicensing-to-agplv3** <https://grafana.com/blog/2021/04/20/grafana-loki-tempo-relicensing-to-agplv3/>
  - archive record: wayback:20210421230514 http://web.archive.org/web/20210421230514/https://grafana.com/blog/2021/04/20/grafana-loki-tempo-relicensing-to-agplv3/
  - archived quotation: "We are relicensing our core open source projects from Apache 2.0 to AGPLv3."

References to label for this event:

- `c32b29d7`: `{"kind": "image", "ref": "grafana/grafana:7.5.5"}`
  - found in: orb-community/orb@d69b91f3ed6c docker/docker-compose.yml (2021-05-21)

Reader 1: `out_of_scope` because: 7.5.5 is before the 8.0 boundary in the event scope.

Reader 2: `undeterminable` because: Rule 5: the archived quotation states no version boundary, so whether 7.5.5 is relicensed is not settled by the source.

---

## Event CMP-5: Malicious flatmap-stream dependency in event-stream 3.3.6

Knowledge date (as_of): 2018-11-29

Sources:
- **npm-blog/event-stream-incident** <https://blog.npmjs.org/post/180565383195/details-about-the-event-stream-incident>
  - archive record: wayback:20181129013028 http://web.archive.org/web/20181129013028/https://blog.npmjs.org/post/180565383195/details-about-the-event-stream-incident
  - archived quotation: "The malicious package was version 0.1.1 of flatmap-stream."

References to label for this event:

- `d61560e7`: `{"ecosystem": "npm", "kind": "package", "package": "event-stream", "version": "3.3.6"}`
  - found in: swiftlang/sourcekit-lsp@7b8e325f8f6e Editors/vscode/package-lock.json (2018-11-26)

Reader 1: `undeterminable` because: The archived quotation names only flatmap-stream 0.1.1; it does not state which event-stream versions carried it, so 3.3.6 membership is not settled by the source.

Reader 2: `in_scope` because: Exact version 3.3.6 named in the event scope.

---

## Event DIS-3: 1,051 floating openjdk tags deleted from Docker Hub

Knowledge date (as_of): 2025-11-05

Sources:
- **docker-library/official-images#20210** <https://github.com/docker-library/official-images/pull/20210>
  - archive record: wayback:20251105030321 http://web.archive.org/web/20251105030321/https://github.com/docker-library/official-images/pull/20210
  - archived quotation: "Deletes are now complete."

Archived evidence file `openjdk-2025-deleted-tags.txt`:
```
# openjdk tags deleted from Docker Hub on 2025-11-03
# Source: https://github.com/docker-library/official-images/pull/20210#issuecomment-3482847877 (tianon, 2025-11-03T22:24:16Z)
# Archived: http://web.archive.org/web/20251105030321/https://github.com/docker-library/official-images/pull/20210
# Retrieved 2026-10-30 through the GitHub API. One tag per line, exactly as listed in the comment.
openjdk:10
openjdk:10.0
openjdk:10.0-jdk
openjdk:10.0-jdk-nanoserver
openjdk:10.0-jdk-nanoserver-sac2016
openjdk:10.0-jdk-oracle
openjdk:10.0-jdk-oraclelinux7
openjdk:10.0-jdk-sid
openjdk:10.0-jdk-slim
openjdk:10.0-jdk-slim-sid
openjdk:10.0-jdk-windowsservercore
openjdk:10.0-jdk-windowsservercore-1709
openjdk:10.0-jdk-windowsservercore-ltsc2016
openjdk:10.0-jre
openjdk:10.0-jre-sid
openjdk:10.0-jre-slim
openjdk:10.0-jre-slim-sid
openjdk:10.0-nanoserver
openjdk:10.0-nanoserver-sac2016
openjdk:10.0-oracle
openjdk:10.0-oraclelinux7
openjdk:10.0-sid
openjdk:10.0-slim
openjdk:10.0-slim-sid
openjdk:10.0-windowsservercore
openjdk:10.0-windowsservercore-1709
openjdk:10.0-windowsservercore-ltsc2016
openjdk:10-jdk
openjdk:10-jdk-experimental
openjdk:10-jdk-nanoserver
openjdk:10-jdk-nanoserver-sac2016
openjdk:10-jdk-oracle
openjdk:10-jdk-oraclelinux7
openjdk:10-jdk-sid
openjdk:10-jdk-slim
openjdk:10-jdk-slim-experimental
openjdk:10-jdk-slim-sid
openjdk:10-jdk-windowsservercore
openjdk:10-jdk-windowsservercore-1709
openjdk:10-jdk-windowsservercore-ltsc2016
openjdk:10-jre
openjdk:10-jre-experimental
openjdk:10-jre-sid
openjdk:10-jre-slim
openjdk:10-jre-slim-experimental
openjdk:10-jre-slim-sid
openjdk:10-nanoserver
openjdk:10-nanoserver-sac2016
openjdk:10-oracle
openjdk:10-oraclelinux7
openjdk:10-sid
openjdk:10-slim
openjdk:10-slim-experimental
openjdk:10-slim-sid
openjdk:10-windowsservercore
openjdk:10-windowsservercore-1709
openjdk:10-windowsservercore-ltsc2016
openjdk:11
openjdk:11.0
openjdk:11.0-bullseye
openjdk:11.0-buster
openjdk:11.0-jdk
openjdk:11.0-jdk-bullseye
openjdk:11.0-jdk-buster
openjdk:11.0-jdk-nanoserver
openjdk:11.0-jdk-nanoserver-1803
openjdk:11.0-jdk-nanoserver-1809
openjdk:11.0-jdk-nanoserver-sac2016
openjdk:11.0-jdk-oracle
openjdk:11.0-jdk-oraclelinux7
openjdk:11.0-jdk-oraclelinux8
openjdk:11.0-jdk-sid
openjdk:11.0-jdk-slim
openjdk:11.0-jdk-slim-bullseye
openjdk:11.0-jdk-slim-buster
openjdk:11.0-jdk-slim-sid
openjdk:11.0-jdk-slim-stretch
openjdk:11.0-jdk-stretch
openjdk:11.0-jdk-windowsservercore
openjdk:11.0-jdk-windowsservercore-1709
openjdk:11.0-jdk-windowsservercore-1803
openjdk:11.0-jdk-windowsservercore-1809
openjdk:11.0-jdk-windowsservercore-ltsc2016
openjdk:11.0-jdk-windowsservercore-ltsc2022
openjdk:11.0-jre
openjdk:11.0-jre-bullseye
openjdk:11.0-jre-buster
openjdk:11.0-jre-nanoserver
openjdk:11.0-jre-nanoserver-1803
openjdk:11.0-jre-nanoserver-1809
openjdk:11.0-jre-sid
openjdk:11.0-jre-slim
openjdk:11.0-jre-slim-bullseye
openjdk:11.0-jre-slim-buster
openjdk:11.0-jre-slim-sid
openjdk:11.0-jre-slim-stretch
openjdk:11.0-jre-stretch
openjdk:11.0-jre-windowsservercore
openjdk:11.0-jre-windowsservercore-1803
openjdk:11.0-jre-windowsservercore-1809
openjdk:11.0-jre-windowsservercore-ltsc2016
openjdk:11.0-jre-windowsservercore-ltsc2022
openjdk:11.0-nanoserver
openjdk:11.0-nanoserver-1803
openjdk:11.0-nanoserver-1809
openjdk:11.0-nanoserver-sac2016
openjdk:11.0-oracle
openjdk:11.0-oraclelinux7
openjdk:11.0-oraclelinux8
openjdk:11.0-sid
openjdk:11.0-slim
openjdk:11.0-slim-bullseye
openjdk:11.0-slim-buster
openjdk:11.0-slim-sid
openjdk:11.0-slim-stretch
openjdk:11.0-stretch
openjdk:11.0-windowsservercore
openjdk:11.0-windowsservercore-1709
openjdk:11.0-windowsservercore-1803
openjdk:11.0-windowsservercore-1809
openjdk:11.0-windowsservercore-ltsc2016
openjdk:11.0-windowsservercore-ltsc2022
openjdk:11-bullseye
openjdk:11-buster
openjdk:11-jdk
openjdk:11-jdk-bullseye
openjdk:11-jdk-buster
openjdk:11-jdk-nanoserver
openjdk:11-jdk-nanoserver-1803
openjdk:11-jdk-nanoserver-1809
openjdk:11-jdk-nanoserver-sac2016
openjdk:11-jdk-oracle
openjdk:11-jdk-oraclelinux7
openjdk:11-jdk-oraclelinux8
openjdk:11-jdk-sid
openjdk:11-jdk-slim
openjdk:11-jdk-slim-bullseye
openjdk:11-jdk-slim-buster
openjdk:11-jdk-slim-sid
openjdk:11-jdk-slim-stretch
openjdk:11-jdk-stretch
openjdk:11-jdk-windowsservercore
openjdk:11-jdk-windowsservercore-1709
openjdk:11-jdk-windowsservercore-1803
openjdk:11-jdk-windowsservercore-1809
openjdk:11-jdk-windowsservercore-ltsc2016
openjdk:11-jdk-windowsservercore-ltsc2022
openjdk:11-jre
openjdk:11-jre-bullseye
openjdk:11-jre-buster
openjdk:11-jre-nanoserver
openjdk:11-jre-nanoserver-1803
openjdk:11-jre-nanoserver-1809
openjdk:11-jre-sid
openjdk:11-jre-slim
openjdk:11-jre-slim-bullseye
openjdk:11-jre-slim-buster
openjdk:11-jre-slim-sid
openjdk:11-jre-slim-stretch
openjdk:11-jre-stretch
openjdk:11-jre-windowsservercore
openjdk:11-jre-windowsservercore-1803
openjdk:11-jre-windowsservercore-1809
openjdk:11-jre-windowsservercore-ltsc2016
openjdk:11-jre-windowsservercore-ltsc2022
openjdk:11-nanoserver
openjdk:11-nanoserver-1803
openjdk:11-nanoserver-1809
openjdk:11-nanoserver-sac2016
openjdk:11-oracle
openjdk:11-oraclelinux7
openjdk:11-oraclelinux8
openjdk:11-sid
openjdk:11-slim
openjdk:11-slim-bullseye
openjdk:11-slim-buster
openjdk:11-slim-sid
openjdk:11-slim-stretch
openjdk:11-stretch
openjdk:11-windowsservercore
openjdk:11-windowsservercore-1709
openjdk:11-windowsservercore-1803
openjdk:11-windowsservercore-1809
openjdk:11-windowsservercore-ltsc2016
openjdk:11-windowsservercore-ltsc2022
openjdk:12
openjdk:12.0
openjdk:12.0-jdk
openjdk:12.0-jdk-oracle
openjdk:12.0-jdk-oraclelinux7
openjdk:12.0-jdk-windowsservercore
openjdk:12.0-jdk-windowsservercore-1803
openjdk:12.0-jdk-windowsservercore-1809
openjdk:12.0-jdk-windowsservercore-ltsc2016
openjdk:12.0-oracle
openjdk:12.0-oraclelinux7
openjdk:12.0-windowsservercore
openjdk:12.0-windowsservercore-1803
openjdk:12.0-windowsservercore-1809
openjdk:12.0-windowsservercore-ltsc2016
openjdk:12-alpine
openjdk:12-alpine3.8
openjdk:12-alpine3.9
openjdk:12-jdk
openjdk:12-jdk-alpine
openjdk:12-jdk-alpine3.8
openjdk:12-jdk-alpine3.9
openjdk:12-jdk-nanoserver
openjdk:12-jdk-nanoserver-sac2016
openjdk:12-jdk-oracle
openjdk:12-jdk-oraclelinux7
openjdk:12-jdk-windowsservercore
openjdk:12-jdk-windowsservercore-1709
openjdk:12-jdk-windowsservercore-1803
openjdk:12-jdk-windowsservercore-1809
openjdk:12-jdk-windowsservercore-ltsc2016
openjdk:12-nanoserver
openjdk:12-nanoserver-sac2016
openjdk:12-oracle
openjdk:12-oraclelinux7
openjdk:12-windowsservercore
openjdk:12-windowsservercore-1709
openjdk:12-windowsservercore-1803
openjdk:12-windowsservercore-1809
openjdk:12-windowsservercore-ltsc2016
openjdk:13
openjdk:13.0
openjdk:13.0-buster
openjdk:13.0-jdk
openjdk:13.0-jdk-buster
openjdk:13.0-jdk-nanoserver
openjdk:13.0-jdk-nanoserver-1803
openjdk:13.0-jdk-nanoserver-1809
openjdk:13.0-jdk-oracle
openjdk:13.0-jdk-oraclelinux7
openjdk:13.0-jdk-slim
openjdk:13.0-jdk-slim-buster
openjdk:13.0-jdk-windowsservercore
openjdk:13.0-jdk-windowsservercore-1803
openjdk:13.0-jdk-windowsservercore-1809
openjdk:13.0-jdk-windowsservercore-ltsc2016
openjdk:13.0-nanoserver
openjdk:13.0-nanoserver-1803
openjdk:13.0-nanoserver-1809
openjdk:13.0-oracle
openjdk:13.0-oraclelinux7
openjdk:13.0-slim
openjdk:13.0-slim-buster
openjdk:13.0-windowsservercore
openjdk:13.0-windowsservercore-1803
openjdk:13.0-windowsservercore-1809
openjdk:13.0-windowsservercore-ltsc2016
openjdk:13-alpine
openjdk:13-alpine3.10
openjdk:13-alpine3.8
openjdk:13-alpine3.9
openjdk:13-buster
openjdk:13-jdk
openjdk:13-jdk-alpine
openjdk:13-jdk-alpine3.10
openjdk:13-jdk-alpine3.8
openjdk:13-jdk-alpine3.9
openjdk:13-jdk-buster
openjdk:13-jdk-nanoserver
openjdk:13-jdk-nanoserver-1803
openjdk:13-jdk-nanoserver-1809
openjdk:13-jdk-nanoserver-sac2016
openjdk:13-jdk-oracle
openjdk:13-jdk-oraclelinux7
openjdk:13-jdk-slim
openjdk:13-jdk-slim-buster
openjdk:13-jdk-windowsservercore
openjdk:13-jdk-windowsservercore-1709
openjdk:13-jdk-windowsservercore-1803
openjdk:13-jdk-windowsservercore-1809
openjdk:13-jdk-windowsservercore-ltsc2016
openjdk:13-nanoserver
openjdk:13-nanoserver-1803
openjdk:13-nanoserver-1809
openjdk:13-nanoserver-sac2016
openjdk:13-oracle
openjdk:13-oraclelinux7
openjdk:13-slim
openjdk:13-slim-buster
openjdk:13-windowsservercore
openjdk:13-windowsservercore-1709
openjdk:13-windowsservercore-1803
openjdk:13-windowsservercore-1809
openjdk:13-windowsservercore-ltsc2016
openjdk:14
openjdk:14.0
openjdk:14.0-buster
openjdk:14.0-jdk
openjdk:14.0-jdk-buster
openjdk:14.0-jdk-nanoserver
openjdk:14.0-jdk-nanoserver-1809
openjdk:14.0-jdk-oracle
openjdk:14.0-jdk-oraclelinux7
openjdk:14.0-jdk-oraclelinux8
openjdk:14.0-jdk-slim
openjdk:14.0-jdk-slim-buster
openjdk:14.0-jdk-windowsservercore
openjdk:14.0-jdk-windowsservercore-1809
openjdk:14.0-jdk-windowsservercore-ltsc2016
openjdk:14.0-nanoserver
openjdk:14.0-nanoserver-1809
openjdk:14.0-oracle
openjdk:14.0-oraclelinux7
openjdk:14.0-oraclelinux8
openjdk:14.0-slim
openjdk:14.0-slim-buster
openjdk:14.0-windowsservercore
openjdk:14.0-windowsservercore-1809
openjdk:14.0-windowsservercore-ltsc2016
openjdk:14-alpine
openjdk:14-alpine3.10
openjdk:14-buster
openjdk:14-jdk
openjdk:14-jdk-alpine
openjdk:14-jdk-alpine3.10
openjdk:14-jdk-buster
openjdk:14-jdk-nanoserver
openjdk:14-jdk-nanoserver-1803
openjdk:14-jdk-nanoserver-1809
openjdk:14-jdk-oracle
openjdk:14-jdk-oraclelinux7
openjdk:14-jdk-oraclelinux8
openjdk:14-jdk-slim
openjdk:14-jdk-slim-buster
openjdk:14-jdk-windowsservercore
openjdk:14-jdk-windowsservercore-1803
openjdk:14-jdk-windowsservercore-1809
openjdk:14-jdk-windowsservercore-ltsc2016
openjdk:14-nanoserver
openjdk:14-nanoserver-1803
openjdk:14-nanoserver-1809
openjdk:14-oracle
openjdk:14-oraclelinux7
openjdk:14-oraclelinux8
openjdk:14-slim
openjdk:14-slim-buster
openjdk:14-windowsservercore
openjdk:14-windowsservercore-1803
openjdk:14-windowsservercore-1809
openjdk:14-windowsservercore-ltsc2016
openjdk:15
openjdk:15.0
openjdk:15.0-buster
openjdk:15.0-jdk
openjdk:15.0-jdk-buster
openjdk:15.0-jdk-nanoserver
openjdk:15.0-jdk-nanoserver-1809
openjdk:15.0-jdk-oracle
openjdk:15.0-jdk-oraclelinux7
openjdk:15.0-jdk-oraclelinux8
openjdk:15.0-jdk-slim
openjdk:15.0-jdk-slim-buster
openjdk:15.0-jdk-windowsservercore
openjdk:15.0-jdk-windowsservercore-1809
openjdk:15.0-jdk-windowsservercore-ltsc2016
openjdk:15.0-nanoserver
openjdk:15.0-nanoserver-1809
openjdk:15.0-oracle
openjdk:15.0-oraclelinux7
openjdk:15.0-oraclelinux8
openjdk:15.0-slim
openjdk:15.0-slim-buster
openjdk:15.0-windowsservercore
openjdk:15.0-windowsservercore-1809
openjdk:15.0-windowsservercore-ltsc2016
openjdk:15-alpine
openjdk:15-alpine3.11
openjdk:15-alpine3.12
openjdk:15-buster
openjdk:15-jdk
openjdk:15-jdk-alpine
openjdk:15-jdk-alpine3.11
openjdk:15-jdk-alpine3.12
openjdk:15-jdk-buster
openjdk:15-jdk-nanoserver
openjdk:15-jdk-nanoserver-1809
openjdk:15-jdk-oracle
openjdk:15-jdk-oraclelinux7
openjdk:15-jdk-oraclelinux8
openjdk:15-jdk-slim
openjdk:15-jdk-slim-buster
openjdk:15-jdk-windowsservercore
openjdk:15-jdk-windowsservercore-1809
openjdk:15-jdk-windowsservercore-ltsc2016
openjdk:15-nanoserver
openjdk:15-nanoserver-1809
openjdk:15-oracle
openjdk:15-oraclelinux7
openjdk:15-oraclelinux8
openjdk:15-slim
openjdk:15-slim-buster
openjdk:15-windowsservercore
openjdk:15-windowsservercore-1809
openjdk:15-windowsservercore-ltsc2016
openjdk:16
openjdk:16.0
openjdk:16.0-bullseye
openjdk:16.0-buster
openjdk:16.0-jdk
openjdk:16.0-jdk-bullseye
openjdk:16.0-jdk-buster
openjdk:16.0-jdk-nanoserver
openjdk:16.0-jdk-nanoserver-1809
openjdk:16.0-jdk-oracle
openjdk:16.0-jdk-oraclelinux7
openjdk:16.0-jdk-oraclelinux8
openjdk:16.0-jdk-slim
openjdk:16.0-jdk-slim-bullseye
openjdk:16.0-jdk-slim-buster
openjdk:16.0-jdk-windowsservercore
openjdk:16.0-jdk-windowsservercore-1809
openjdk:16.0-jdk-windowsservercore-ltsc2016
openjdk:16.0-nanoserver
openjdk:16.0-nanoserver-1809
openjdk:16.0-oracle
openjdk:16.0-oraclelinux7
openjdk:16.0-oraclelinux8
openjdk:16.0-slim
openjdk:16.0-slim-bullseye
openjdk:16.0-slim-buster
openjdk:16.0-windowsservercore
openjdk:16.0-windowsservercore-1809
openjdk:16.0-windowsservercore-ltsc2016
openjdk:16-alpine
openjdk:16-alpine3.12
openjdk:16-alpine3.13
openjdk:16-bullseye
openjdk:16-buster
openjdk:16-jdk
openjdk:16-jdk-alpine
openjdk:16-jdk-alpine3.12
openjdk:16-jdk-alpine3.13
openjdk:16-jdk-bullseye
openjdk:16-jdk-buster
openjdk:16-jdk-nanoserver
openjdk:16-jdk-nanoserver-1809
openjdk:16-jdk-oracle
openjdk:16-jdk-oraclelinux7
openjdk:16-jdk-oraclelinux8
openjdk:16-jdk-slim
openjdk:16-jdk-slim-bullseye
openjdk:16-jdk-slim-buster
openjdk:16-jdk-windowsservercore
openjdk:16-jdk-windowsservercore-1809
openjdk:16-jdk-windowsservercore-ltsc2016
openjdk:16-nanoserver
openjdk:16-nanoserver-1809
openjdk:16-oracle
openjdk:16-oraclelinux7
openjdk:16-oraclelinux8
openjdk:16-slim
openjdk:16-slim-bullseye
openjdk:16-slim-buster
openjdk:16-windowsservercore
openjdk:16-windowsservercore-1809
openjdk:16-windowsservercore-ltsc2016
openjdk:17
openjdk:17.0
openjdk:17.0-bullseye
openjdk:17.0-buster
openjdk:17.0-jdk
openjdk:17.0-jdk-bullseye
openjdk:17.0-jdk-buster
openjdk:17.0-jdk-nanoserver
openjdk:17.0-jdk-nanoserver-1809
openjdk:17.0-jdk-oracle
openjdk:17.0-jdk-oraclelinux7
openjdk:17.0-jdk-oraclelinux8
openjdk:17.0-jdk-slim
openjdk:17.0-jdk-slim-bullseye
openjdk:17.0-jdk-slim-buster
openjdk:17.0-jdk-windowsservercore
openjdk:17.0-jdk-windowsservercore-1809
openjdk:17.0-jdk-windowsservercore-ltsc2016
openjdk:17.0-jdk-windowsservercore-ltsc2022
openjdk:17.0-nanoserver
openjdk:17.0-nanoserver-1809
openjdk:17.0-oracle
openjdk:17.0-oraclelinux7
openjdk:17.0-oraclelinux8
openjdk:17.0-slim
openjdk:17.0-slim-bullseye
openjdk:17.0-slim-buster
openjdk:17.0-windowsservercore
openjdk:17.0-windowsservercore-1809
openjdk:17.0-windowsservercore-ltsc2016
openjdk:17.0-windowsservercore-ltsc2022
openjdk:17-alpine
openjdk:17-alpine3.12
openjdk:17-alpine3.13
openjdk:17-alpine3.14
openjdk:17-bullseye
openjdk:17-buster
openjdk:17-jdk
openjdk:17-jdk-alpine
openjdk:17-jdk-alpine3.12
openjdk:17-jdk-alpine3.13
openjdk:17-jdk-alpine3.14
openjdk:17-jdk-bullseye
openjdk:17-jdk-buster
openjdk:17-jdk-nanoserver
openjdk:17-jdk-nanoserver-1809
openjdk:17-jdk-oracle
openjdk:17-jdk-oraclelinux7
openjdk:17-jdk-oraclelinux8
openjdk:17-jdk-slim
openjdk:17-jdk-slim-bullseye
openjdk:17-jdk-slim-buster
openjdk:17-jdk-windowsservercore
openjdk:17-jdk-windowsservercore-1809
openjdk:17-jdk-windowsservercore-ltsc2016
openjdk:17-jdk-windowsservercore-ltsc2022
openjdk:17-nanoserver
openjdk:17-nanoserver-1809
openjdk:17-oracle
openjdk:17-oraclelinux7
openjdk:17-oraclelinux8
openjdk:17-slim
openjdk:17-slim-bullseye
openjdk:17-slim-buster
openjdk:17-windowsservercore
openjdk:17-windowsservercore-1809
openjdk:17-windowsservercore-ltsc2016
openjdk:17-windowsservercore-ltsc2022
openjdk:18
openjdk:18.0
openjdk:18.0-bullseye
openjdk:18.0-buster
openjdk:18.0-jdk
openjdk:18.0-jdk-bullseye
openjdk:18.0-jdk-buster
openjdk:18.0-jdk-nanoserver
openjdk:18.0-jdk-nanoserver-1809
openjdk:18.0-jdk-oracle
openjdk:18.0-jdk-oraclelinux7
openjdk:18.0-jdk-oraclelinux8
openjdk:18.0-jdk-slim
openjdk:18.0-jdk-slim-bullseye
openjdk:18.0-jdk-slim-buster
openjdk:18.0-jdk-windowsservercore
openjdk:18.0-jdk-windowsservercore-1809
openjdk:18.0-jdk-windowsservercore-ltsc2022
openjdk:18.0-nanoserver
openjdk:18.0-nanoserver-1809
openjdk:18.0-oracle
openjdk:18.0-oraclelinux7
openjdk:18.0-oraclelinux8
openjdk:18.0-slim
openjdk:18.0-slim-bullseye
openjdk:18.0-slim-buster
openjdk:18.0-windowsservercore
openjdk:18.0-windowsservercore-1809
openjdk:18.0-windowsservercore-ltsc2022
openjdk:18-alpine
openjdk:18-alpine3.13
openjdk:18-alpine3.14
openjdk:18-alpine3.15
openjdk:18-bullseye
openjdk:18-buster
openjdk:18-jdk
openjdk:18-jdk-alpine
openjdk:18-jdk-alpine3.13
openjdk:18-jdk-alpine3.14
openjdk:18-jdk-alpine3.15
openjdk:18-jdk-bullseye
openjdk:18-jdk-buster
openjdk:18-jdk-nanoserver
openjdk:18-jdk-nanoserver-1809
openjdk:18-jdk-oracle
openjdk:18-jdk-oraclelinux7
openjdk:18-jdk-oraclelinux8
openjdk:18-jdk-slim
openjdk:18-jdk-slim-bullseye
openjdk:18-jdk-slim-buster
openjdk:18-jdk-windowsservercore
openjdk:18-jdk-windowsservercore-1809
openjdk:18-jdk-windowsservercore-ltsc2016
openjdk:18-jdk-windowsservercore-ltsc2022
openjdk:18-nanoserver
openjdk:18-nanoserver-1809
openjdk:18-oracle
openjdk:18-oraclelinux7
openjdk:18-oraclelinux8
openjdk:18-slim
openjdk:18-slim-bullseye
openjdk:18-slim-buster
openjdk:18-windowsservercore
openjdk:18-windowsservercore-1809
openjdk:18-windowsservercore-ltsc2016
openjdk:18-windowsservercore-ltsc2022
openjdk:19
openjdk:19-alpine
openjdk:19-alpine3.14
openjdk:19-alpine3.15
openjdk:19-alpine3.16
openjdk:19-bullseye
openjdk:19-buster
openjdk:19-jdk
openjdk:19-jdk-alpine
openjdk:19-jdk-alpine3.14
openjdk:19-jdk-alpine3.15
openjdk:19-jdk-alpine3.16
openjdk:19-jdk-bullseye
openjdk:19-jdk-buster
openjdk:19-jdk-nanoserver
openjdk:19-jdk-nanoserver-1809
openjdk:19-jdk-oracle
openjdk:19-jdk-oraclelinux7
openjdk:19-jdk-oraclelinux8
openjdk:19-jdk-slim
openjdk:19-jdk-slim-bullseye
openjdk:19-jdk-slim-buster
openjdk:19-jdk-windowsservercore
openjdk:19-jdk-windowsservercore-1809
openjdk:19-jdk-windowsservercore-ltsc2016
openjdk:19-jdk-windowsservercore-ltsc2022
openjdk:19-nanoserver
openjdk:19-nanoserver-1809
openjdk:19-oracle
openjdk:19-oraclelinux7
openjdk:19-oraclelinux8
openjdk:19-slim
openjdk:19-slim-bullseye
openjdk:19-slim-buster
openjdk:19-windowsservercore
openjdk:19-windowsservercore-1809
openjdk:19-windowsservercore-ltsc2016
openjdk:19-windowsservercore-ltsc2022
openjdk:20
openjdk:20-bullseye
openjdk:20-buster
openjdk:20-jdk
openjdk:20-jdk-bullseye
openjdk:20-jdk-buster
openjdk:20-jdk-nanoserver
openjdk:20-jdk-nanoserver-1809
openjdk:20-jdk-oracle
openjdk:20-jdk-oraclelinux7
openjdk:20-jdk-oraclelinux8
openjdk:20-jdk-slim
openjdk:20-jdk-slim-bullseye
openjdk:20-jdk-slim-buster
openjdk:20-jdk-windowsservercore
openjdk:20-jdk-windowsservercore-1809
openjdk:20-jdk-windowsservercore-ltsc2022
openjdk:20-nanoserver
openjdk:20-nanoserver-1809
openjdk:20-oracle
openjdk:20-oraclelinux7
openjdk:20-oraclelinux8
openjdk:20-slim
openjdk:20-slim-bullseye
openjdk:20-slim-buster
openjdk:20-windowsservercore
openjdk:20-windowsservercore-1809
openjdk:20-windowsservercore-ltsc2022
openjdk:21
openjdk:21-bookworm
openjdk:21-bullseye
openjdk:21-buster
openjdk:21-jdk
openjdk:21-jdk-bookworm
openjdk:21-jdk-bullseye
openjdk:21-jdk-buster
openjdk:21-jdk-nanoserver
openjdk:21-jdk-nanoserver-1809
openjdk:21-jdk-oracle
openjdk:21-jdk-oraclelinux7
openjdk:21-jdk-oraclelinux8
openjdk:21-jdk-slim
openjdk:21-jdk-slim-bookworm
openjdk:21-jdk-slim-bullseye
openjdk:21-jdk-slim-buster
openjdk:21-jdk-windowsservercore
openjdk:21-jdk-windowsservercore-1809
openjdk:21-jdk-windowsservercore-ltsc2022
openjdk:21-nanoserver
openjdk:21-nanoserver-1809
openjdk:21-oracle
openjdk:21-oraclelinux7
openjdk:21-oraclelinux8
openjdk:21-slim
openjdk:21-slim-bookworm
openjdk:21-slim-bullseye
openjdk:21-slim-buster
openjdk:21-windowsservercore
openjdk:21-windowsservercore-1809
openjdk:21-windowsservercore-ltsc2022
openjdk:22
openjdk:22-bookworm
openjdk:22-bullseye
openjdk:22-buster
openjdk:22-slim
openjdk:22-slim-bookworm
openjdk:22-slim-bullseye
openjdk:22-slim-buster
openjdk:22-windowsservercore
openjdk:22-windowsservercore-1809
openjdk:22-windowsservercore-ltsc2022
openjdk:23
openjdk:23-bookworm
openjdk:23-bullseye
openjdk:23-jdk
openjdk:23-jdk-bookworm
openjdk:23-jdk-bullseye
openjdk:23-jdk-nanoserver
openjdk:23-jdk-nanoserver-1809
openjdk:23-jdk-oracle
openjdk:23-jdk-oraclelinux7
openjdk:23-jdk-oraclelinux8
openjdk:23-jdk-oraclelinux9
openjdk:23-jdk-slim
openjdk:23-jdk-slim-bookworm
openjdk:23-jdk-slim-bullseye
openjdk:23-jdk-windowsservercore
openjdk:23-jdk-windowsservercore-1809
openjdk:23-jdk-windowsservercore-ltsc2022
openjdk:23-nanoserver
openjdk:23-nanoserver-1809
openjdk:23-oracle
openjdk:23-oraclelinux7
openjdk:23-oraclelinux8
openjdk:23-oraclelinux9
openjdk:23-slim
openjdk:23-slim-bookworm
openjdk:23-slim-bullseye
openjdk:23-windowsservercore
openjdk:23-windowsservercore-1809
openjdk:23-windowsservercore-ltsc2022
openjdk:24
openjdk:24-bookworm
openjdk:24-bullseye
openjdk:24-jdk
openjdk:24-jdk-bookworm
openjdk:24-jdk-bullseye
openjdk:24-jdk-nanoserver
openjdk:24-jdk-nanoserver-1809
openjdk:24-jdk-nanoserver-ltsc2022
openjdk:24-jdk-nanoserver-ltsc2025
openjdk:24-jdk-oracle
openjdk:24-jdk-oraclelinux8
openjdk:24-jdk-oraclelinux9
openjdk:24-jdk-slim
openjdk:24-jdk-slim-bookworm
openjdk:24-jdk-slim-bullseye
openjdk:24-jdk-windowsservercore
openjdk:24-jdk-windowsservercore-1809
openjdk:24-jdk-windowsservercore-ltsc2022
openjdk:24-jdk-windowsservercore-ltsc2025
openjdk:24-nanoserver
openjdk:24-nanoserver-1809
openjdk:24-nanoserver-ltsc2022
openjdk:24-nanoserver-ltsc2025
openjdk:24-oracle
openjdk:24-oraclelinux8
openjdk:24-oraclelinux9
openjdk:24-slim
openjdk:24-slim-bookworm
openjdk:24-slim-bullseye
openjdk:24-windowsservercore
openjdk:24-windowsservercore-1809
openjdk:24-windowsservercore-ltsc2022
openjdk:24-windowsservercore-ltsc2025
openjdk:25
openjdk:25-bookworm
openjdk:25-bullseye
openjdk:25-jdk
openjdk:25-jdk-bookworm
openjdk:25-jdk-bullseye
openjdk:25-jdk-nanoserver
openjdk:25-jdk-nanoserver-1809
openjdk:25-jdk-nanoserver-ltsc2022
openjdk:25-jdk-nanoserver-ltsc2025
openjdk:25-jdk-oracle
openjdk:25-jdk-oraclelinux8
openjdk:25-jdk-oraclelinux9
openjdk:25-jdk-slim
openjdk:25-jdk-slim-bookworm
openjdk:25-jdk-slim-bullseye
openjdk:25-jdk-slim-trixie
openjdk:25-jdk-trixie
openjdk:25-jdk-windowsservercore
openjdk:25-jdk-windowsservercore-1809
openjdk:25-jdk-windowsservercore-ltsc2022
openjdk:25-jdk-windowsservercore-ltsc2025
openjdk:25-nanoserver
openjdk:25-nanoserver-1809
openjdk:25-nanoserver-ltsc2022
openjdk:25-nanoserver-ltsc2025
openjdk:25-oracle
openjdk:25-oraclelinux8
openjdk:25-oraclelinux9
openjdk:25-slim
openjdk:25-slim-bookworm
openjdk:25-slim-bullseye
openjdk:25-slim-trixie
openjdk:25-trixie
openjdk:25-windowsservercore
openjdk:25-windowsservercore-1809
openjdk:25-windowsservercore-ltsc2022
openjdk:25-windowsservercore-ltsc2025
openjdk:26
openjdk:26-bookworm
openjdk:26-bullseye
openjdk:26-jdk
openjdk:26-jdk-bookworm
openjdk:26-jdk-bullseye
openjdk:26-jdk-nanoserver
openjdk:26-jdk-nanoserver-ltsc2022
openjdk:26-jdk-nanoserver-ltsc2025
openjdk:26-jdk-oracle
openjdk:26-jdk-oraclelinux8
openjdk:26-jdk-oraclelinux9
openjdk:26-jdk-slim
openjdk:26-jdk-slim-bookworm
openjdk:26-jdk-slim-bullseye
openjdk:26-jdk-slim-trixie
openjdk:26-jdk-trixie
openjdk:26-jdk-windowsservercore
openjdk:26-jdk-windowsservercore-ltsc2022
openjdk:26-jdk-windowsservercore-ltsc2025
openjdk:26-nanoserver
openjdk:26-nanoserver-ltsc2022
openjdk:26-nanoserver-ltsc2025
openjdk:26-oracle
openjdk:26-oraclelinux8
openjdk:26-oraclelinux9
openjdk:26-slim
openjdk:26-slim-bookworm
openjdk:26-slim-bullseye
openjdk:26-slim-trixie
openjdk:26-trixie
openjdk:26-windowsservercore
openjdk:26-windowsservercore-ltsc2022
openjdk:26-windowsservercore-ltsc2025
openjdk:6
openjdk:6-jdk
openjdk:6-jdk-slim
openjdk:6-jdk-slim-wheezy
openjdk:6-jdk-wheezy
openjdk:6-jre
openjdk:6-jre-slim
openjdk:6-jre-slim-wheezy
openjdk:6-jre-wheezy
openjdk:6-slim
openjdk:6-slim-wheezy
openjdk:6-wheezy
openjdk:7
openjdk:7-alpine
openjdk:7-alpine3.7
openjdk:7-alpine3.8
openjdk:7-alpine3.9
openjdk:7-jdk
openjdk:7-jdk-alpine
openjdk:7-jdk-alpine3.7
openjdk:7-jdk-alpine3.8
openjdk:7-jdk-alpine3.9
openjdk:7-jdk-jessie
openjdk:7-jdk-slim
openjdk:7-jdk-slim-jessie
openjdk:7-jessie
openjdk:7-jre
openjdk:7-jre-alpine
openjdk:7-jre-alpine3.7
openjdk:7-jre-alpine3.8
openjdk:7-jre-alpine3.9
openjdk:7-jre-jessie
openjdk:7-jre-slim
openjdk:7-jre-slim-jessie
openjdk:7-slim
openjdk:7-slim-jessie
openjdk:8
openjdk:8-alpine
openjdk:8-alpine3.7
openjdk:8-alpine3.8
openjdk:8-alpine3.9
openjdk:8-bullseye
openjdk:8-buster
openjdk:8-jdk
openjdk:8-jdk-alpine
openjdk:8-jdk-alpine3.7
openjdk:8-jdk-alpine3.8
openjdk:8-jdk-alpine3.9
openjdk:8-jdk-bullseye
openjdk:8-jdk-buster
openjdk:8-jdk-nanoserver
openjdk:8-jdk-nanoserver-1803
openjdk:8-jdk-nanoserver-1809
openjdk:8-jdk-nanoserver-sac2016
openjdk:8-jdk-oracle
openjdk:8-jdk-oraclelinux7
openjdk:8-jdk-oraclelinux8
openjdk:8-jdk-slim
openjdk:8-jdk-slim-bullseye
openjdk:8-jdk-slim-buster
openjdk:8-jdk-slim-stretch
openjdk:8-jdk-stretch
openjdk:8-jdk-windowsservercore
openjdk:8-jdk-windowsservercore-1709
openjdk:8-jdk-windowsservercore-1803
openjdk:8-jdk-windowsservercore-1809
openjdk:8-jdk-windowsservercore-ltsc2016
openjdk:8-jdk-windowsservercore-ltsc2022
openjdk:8-jre
openjdk:8-jre-alpine
openjdk:8-jre-alpine3.7
openjdk:8-jre-alpine3.8
openjdk:8-jre-alpine3.9
openjdk:8-jre-bullseye
openjdk:8-jre-buster
openjdk:8-jre-nanoserver
openjdk:8-jre-nanoserver-1803
openjdk:8-jre-nanoserver-1809
openjdk:8-jre-slim
openjdk:8-jre-slim-bullseye
openjdk:8-jre-slim-buster
openjdk:8-jre-slim-stretch
openjdk:8-jre-stretch
openjdk:8-jre-windowsservercore
openjdk:8-jre-windowsservercore-1803
openjdk:8-jre-windowsservercore-1809
openjdk:8-jre-windowsservercore-ltsc2016
openjdk:8-jre-windowsservercore-ltsc2022
openjdk:8-nanoserver
openjdk:8-nanoserver-1803
openjdk:8-nanoserver-1809
openjdk:8-nanoserver-sac2016
openjdk:8-oracle
openjdk:8-oraclelinux7
openjdk:8-oraclelinux8
openjdk:8-slim
openjdk:8-slim-bullseye
openjdk:8-slim-buster
openjdk:8-slim-stretch
openjdk:8-stretch
openjdk:8-windowsservercore
openjdk:8-windowsservercore-1709
openjdk:8-windowsservercore-1803
openjdk:8-windowsservercore-1809
openjdk:8-windowsservercore-ltsc2016
openjdk:8-windowsservercore-ltsc2022
openjdk:9
openjdk:9.0
openjdk:9.0-jdk
openjdk:9.0-jdk-nanoserver
openjdk:9.0-jdk-nanoserver-sac2016
openjdk:9.0-jdk-sid
openjdk:9.0-jdk-slim
openjdk:9.0-jdk-slim-sid
openjdk:9.0-jdk-windowsservercore
openjdk:9.0-jdk-windowsservercore-1709
openjdk:9.0-jdk-windowsservercore-ltsc2016
openjdk:9.0-jre
openjdk:9.0-jre-sid
openjdk:9.0-jre-slim
openjdk:9.0-jre-slim-sid
openjdk:9.0-nanoserver
openjdk:9.0-nanoserver-sac2016
openjdk:9.0-sid
openjdk:9.0-slim
openjdk:9.0-slim-sid
openjdk:9.0-windowsservercore
openjdk:9.0-windowsservercore-1709
openjdk:9.0-windowsservercore-ltsc2016
openjdk:9-jdk
openjdk:9-jdk-nanoserver
openjdk:9-jdk-nanoserver-sac2016
openjdk:9-jdk-sid
openjdk:9-jdk-slim
openjdk:9-jdk-slim-sid
openjdk:9-jdk-windowsservercore
openjdk:9-jdk-windowsservercore-1709
openjdk:9-jdk-windowsservercore-ltsc2016
openjdk:9-jre
openjdk:9-jre-sid
openjdk:9-jre-slim
openjdk:9-jre-slim-sid
openjdk:9-nanoserver
openjdk:9-nanoserver-sac2016
openjdk:9-sid
openjdk:9-slim
openjdk:9-slim-sid
openjdk:9-windowsservercore
openjdk:9-windowsservercore-1709
openjdk:9-windowsservercore-ltsc2016
openjdk:alpine
openjdk:alpine3.7
openjdk:alpine3.8
openjdk:bullseye
openjdk:buster
openjdk:jdk
openjdk:jdk-alpine
openjdk:jdk-alpine3.7
openjdk:jdk-alpine3.8
openjdk:jdk-bullseye
openjdk:jdk-buster
openjdk:jdk-nanoserver
openjdk:jdk-nanoserver-1803
openjdk:jdk-nanoserver-1809
openjdk:jdk-nanoserver-sac2016
openjdk:jdk-oracle
openjdk:jdk-oraclelinux7
openjdk:jdk-oraclelinux8
openjdk:jdk-sid
openjdk:jdk-slim
openjdk:jdk-slim-bullseye
openjdk:jdk-slim-buster
openjdk:jdk-slim-sid
openjdk:jdk-slim-stretch
openjdk:jdk-stretch
openjdk:jdk-windowsservercore
openjdk:jdk-windowsservercore-1709
openjdk:jdk-windowsservercore-1803
openjdk:jdk-windowsservercore-1809
openjdk:jdk-windowsservercore-ltsc2016
openjdk:jdk-windowsservercore-ltsc2022
openjdk:jre
openjdk:jre-alpine
openjdk:jre-alpine3.7
openjdk:jre-alpine3.8
openjdk:jre-sid
openjdk:jre-slim
openjdk:jre-slim-sid
openjdk:jre-slim-stretch
openjdk:jre-stretch
openjdk:latest
openjdk:nanoserver
openjdk:nanoserver-1803
openjdk:nanoserver-1809
openjdk:nanoserver-sac2016
openjdk:oracle
openjdk:oraclelinux7
openjdk:oraclelinux8
openjdk:sid
openjdk:slim
openjdk:slim-bullseye
openjdk:slim-buster
openjdk:slim-sid
openjdk:slim-stretch
openjdk:stretch
openjdk:windowsservercore
openjdk:windowsservercore-1709
openjdk:windowsservercore-1803
openjdk:windowsservercore-1809
openjdk:windowsservercore-ltsc2016
openjdk:windowsservercore-ltsc2022
```

References to label for this event:

- `ebe72d72`: `{"kind": "image", "ref": "openjdk:11.0.16-jdk-slim"}`
  - found in: adyach/nakadi-docker@cac260904ea4 Dockerfile (2022-09-13)

Reader 1: `undeterminable` because: Rule 4: openjdk:11.0.16-jdk-slim is not in the deleted-tags list, and the sources do not state the list covers every changed tag.

Reader 2: `out_of_scope` because: openjdk:11.0.16-jdk-slim is not in the complete 1,051-tag deleted list (file has 1,051 lines).

---

## Event EOL-3: Node.js 12 end of life

Knowledge date (as_of): 2022-04-30

Sources:
- **nodejs/Release** <https://github.com/nodejs/Release>
  - archive record: wayback:20220430045420 http://web.archive.org/web/20220430045420/https://github.com/nodejs/Release
  - archived quotation: "12.x Erbium: end-of-life 2022-04-30."

References to label for this event:

- `f632b9cc`: `{"kind": "image", "ref": "circleci/node:12"}`
  - found in: alibaba/butterfly@d26f5e78dfa0 .circleci/config.yml (2021-05-18)

Reader 1: `out_of_scope` because: circleci/node:12 is a different image in a different namespace (rule 1); the source covers the Node.js 12.x release line, not third-party images.

Reader 2: `undeterminable` because: Rule 1: circleci/node is a third-party image; the source covers the Node.js 12.x line and does not establish what this image contains.

---

## Event EOL-1: Python 2.7 end of life

Knowledge date (as_of): 2020-01-02

Sources:
- **python.org/sunset-python-2** <https://www.python.org/doc/sunset-python-2/>
  - archive record: wayback:20200102202103 http://web.archive.org/web/20200102202103/https://www.python.org/doc/sunset-python-2/
  - archived quotation: "We have decided that January 1, 2020, was the day that we sunset Python 2."

References to label for this event:

- `f7412141`: `{"kind": "image", "ref": "circleci/python:2.7"}`
  - found in: remind101/empire@775178497a2c .circleci/config.yml (2019-03-30)

Reader 1: `undeterminable` because: Rule 1: circleci/python is a third-party image; the source covers Python 2 and does not establish what this image contains.

Reader 2: `out_of_scope` because: circleci/python:2.7 is a different image in a different namespace (rule 1); the source concerns the Python 2 language sunset.

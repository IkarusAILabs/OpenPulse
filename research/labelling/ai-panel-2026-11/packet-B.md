## Event CMP-5: Malicious flatmap-stream dependency in event-stream 3.3.6

Knowledge date (as_of): 2018-11-29

Sources:
- **npm-blog/event-stream-incident** <https://blog.npmjs.org/post/180565383195/details-about-the-event-stream-incident>
  - archive record: wayback:20181129013028 http://web.archive.org/web/20181129013028/https://blog.npmjs.org/post/180565383195/details-about-the-event-stream-incident
  - archived quotation: "The malicious package was version 0.1.1 of flatmap-stream."

References to label for this event:

- `8aea7783`: `{"ecosystem": "npm", "kind": "package", "package": "event-stream", "version": "3.3.6"}`
  - found in: sxei/vscode-plugin-demo@978fa184dc83 package-lock.json (2018-10-15)
- `61c02080`: `{"ecosystem": "npm", "kind": "package", "package": "event-stream", "version": "3.3.4"}`
  - found in: swiftlang/sourcekit-lsp@a54129a22b53 Editors/vscode/package-lock.json (2018-11-28)
- `d61560e7`: `{"ecosystem": "npm", "kind": "package", "package": "event-stream", "version": "3.3.6"}`
  - found in: swiftlang/sourcekit-lsp@7b8e325f8f6e Editors/vscode/package-lock.json (2018-11-26)
- `473d7956`: `{"ecosystem": "npm", "kind": "package", "package": "event-stream", "version": "3.3.4"}`
  - found in: amtrack/force-dev-tool@442490e205fc package-lock.json (2018-09-17)
- `2edeef72`: `{"ecosystem": "npm", "kind": "package", "package": "event-stream", "version": "3.3.6"}`
  - found in: bradtraversy/spacex_launch_stats@1f393e3b9229 package-lock.json (2018-11-12)
- `7ee38dd1`: `{"ecosystem": "npm", "kind": "package", "package": "event-stream", "version": "3.3.5"}`
  - found in: concord-consortium/cloud-file-manager@6b3340249cef yarn.lock (2018-11-28)

## Event EOL-2: CentOS Linux 8 end of life

Knowledge date (as_of): 2020-12-11

Sources:
- **centos/future-is-centos-stream** <https://blog.centos.org/2020/12/future-is-centos-stream/>
  - archive record: wayback:20201211014354 http://web.archive.org/web/20201211014354/https://blog.centos.org/2020/12/future-is-centos-stream/
  - archived quotation: "CentOS Linux 8, as a rebuild of RHEL 8, will end at the end of 2021."

References to label for this event:

- `0fd7f57c`: `{"kind": "image", "ref": "centos:8"}`
  - found in: wxWidgets/Phoenix@07a1e9ea96ed docker/build/centos-8/Dockerfile (2020-07-31)
- `9ddd6e73`: `{"kind": "image", "ref": "centos:8"}`
  - found in: Tencent/plato@e8c8aa52f028 docker/Dockerfile.centos.8 (2019-11-26)
- `0b05f344`: `{"kind": "image", "ref": "quay.io/centos/centos:stream8"}`
  - found in: nmstate/nmstate@f7cae5584451 packaging/Dockerfile.c8s-nmstate-dev (2021-12-01)
- `8232508e`: `{"kind": "image", "ref": "centos:8"}`
  - found in: bbc/audiowaveform@4548d9cd33a1 rpm/Dockerfile-centos8 (2021-08-07)
- `a997381a`: `{"kind": "image", "ref": "centos:8"}`
  - found in: mhallsmoore/qstrader@ce38e604777e dockerfiles/centos8/Dockerfile (2021-01-06)
- `89bcae50`: `{"kind": "image", "ref": "centos:7"}`
  - found in: aliyun/rds_dbsync@35bb00a26273 Dockerfile (2018-12-22)

## Event LIC-4: MongoDB Community Server relicensed to SSPL for releases on or after 2018-10-16

Knowledge date (as_of): 2018-10-23

Sources:
- **mongodb/sspl-faq** <https://www.mongodb.com/licensing/server-side-public-license/faq>
  - archive record: wayback:20181023161242 http://web.archive.org/web/20181023161242/https://www.mongodb.com/licensing/server-side-public-license/faq
  - archived quotation: "All MongoDB Community Server patch releases and versions released on or after October 16, 2018, will be subject to this new license."

Archived evidence file `mongodb-release-tags.txt`:
```
# MongoDB release tags: label basis for LIC-4 (SSPL applies to releases on or after 2018-10-16).
# Source: GitHub git tag objects in mongodb/mongo, read 2026-10-30 via the REST API
#   GET /repos/mongodb/mongo/git/tags/<tag object sha>
# tag	tagger date (UTC)	tag object	commit
r4.0.2	2018-08-27T22:58:10Z	77fd882e6837795736455c113ce815acfe6ea640	fc1573ba18aee42f97a3bb13b67af7d837826b47
r4.0.4	2018-11-06T19:45:45Z	502ddb1538e64dd5e0ccf933894d17a81fa50464	f288a3bdf201007f3693c58e140056adf8b04839
```

References to label for this event:

- `8d94cd3e`: `{"kind": "image", "ref": "mongo:4.0.4"}`
  - found in: Den1al/JSShell@89800add6bc6 docker-compose.yml (2018-12-17)
- `7c043791`: `{"kind": "image", "ref": "mongo:4.0.2"}`
  - found in: NCBI-Hackathons/CTEligible@4182f482417b ct-eligible-flask/docker-compose.yml (2018-09-11)
- `ec27bddf`: `{"kind": "image", "ref": "mongo:4.0.2"}`
  - found in: oktadev/okta-jhipster-microservices-oauth-example@70d4f0a65faa docker-compose/docker-compose.yml (2018-10-12)
- `68514ef5`: `{"kind": "image", "ref": "mongo:4.0.4"}`
  - found in: mydeveloperplanet/mydockercomposeplanet@5111bd128a6e docker-compose.yml (2018-11-25)

## Event EOL-3: Node.js 12 end of life

Knowledge date (as_of): 2022-04-30

Sources:
- **nodejs/Release** <https://github.com/nodejs/Release>
  - archive record: wayback:20220430045420 http://web.archive.org/web/20220430045420/https://github.com/nodejs/Release
  - archived quotation: "12.x Erbium: end-of-life 2022-04-30."

References to label for this event:

- `b4d71fe4`: `{"kind": "image", "ref": "node:12-alpine"}`
  - found in: adtac/commento@84bfd64e3297 Dockerfile (2021-02-02)
- `f9332e9b`: `{"kind": "image", "ref": "node:16-alpine"}`
  - found in: nolanlawson/pinafore@05a3b2d31f47 Dockerfile (2022-04-19)
- `f632b9cc`: `{"kind": "image", "ref": "circleci/node:12"}`
  - found in: alibaba/butterfly@d26f5e78dfa0 .circleci/config.yml (2021-05-18)
- `ca53d779`: `{"kind": "image", "ref": "node:14"}`
  - found in: nteract/commuter@ea2f3d9878d9 Dockerfile (2020-07-21)
- `9b372f76`: `{"kind": "image", "ref": "node:12-alpine"}`
  - found in: taniarascia/takenote@1ba749d1690f Dockerfile (2020-12-11)
- `664fbb27`: `{"kind": "image", "ref": "node:12-alpine"}`
  - found in: excalidraw/excalidraw-room@a0b69ee474b5 Dockerfile (2020-10-21)
- `adb4ac0d`: `{"kind": "image", "ref": "node:12"}`
  - found in: jmcdo29/testing-nestjs@fa73e575a145 Dockerfile (2020-05-25)

## Event CMP-3: Protestware in node-ipc

Knowledge date (as_of): 2022-03-21

Sources:
- **GHSA-97m3-w2cp-4xx6** <https://github.com/advisories/GHSA-97m3-w2cp-4xx6>
  - archive record: wayback:20220321003825 http://web.archive.org/web/20220321003825/https://github.com/advisories/GHSA-97m3-w2cp-4xx6
  - archived quotation: "Versions 10.1.1 and 10.1.2 are vulnerable to embedded malicious code, removed in version 10.1.3."
- **GHSA-8gr3-2gjw-jj7g+GHSA-3mpp-xfvh-qh37** <https://github.com/advisories/GHSA-3mpp-xfvh-qh37>
  - archive record: record:github advisories GHSA-8gr3-2gjw-jj7g (= 9.2.2) and GHSA-3mpp-xfvh-qh37 (>= 11.0.0, < 12.0.0)
  - archived quotation: "Hidden functionality in 9.2.2; desktop message in 11.x."

References to label for this event:

- `de1cfbc4`: `{"ecosystem": "npm", "kind": "package", "package": "node-ipc", "version": "9.2.2"}`
  - found in: vuejs/vue-cli@37ef809c873f yarn.lock (2022-03-15)
- `077e33de`: `{"ecosystem": "npm", "kind": "package", "package": "@achrinza/node-ipc", "version": "9.2.5"}`
  - found in: vuejs/vue-cli@b2b07a569375 yarn.lock (2022-06-15)
- `b0993611`: `{"ecosystem": "npm", "kind": "package", "package": "node-ipc", "version": "9.2.1"}`
  - found in: vuejs/vue-cli@4c679ec525b4 yarn.lock (2022-03-14)
- `d13ccabb`: `{"ecosystem": "npm", "kind": "package", "package": "node-ipc", "version": "9.2.2"}`
  - found in: kodadot/nft-gallery@500e4d4ef970 yarn.lock (2022-03-17)
- `d69dcf94`: `{"ecosystem": "npm", "kind": "package", "package": "node-ipc", "version": "10.1.0"}`
  - found in: MillenniumEarl/recaptcha-harvester@8a34196cc09c package-lock.json (2022-03-17)
- `32552f7e`: `{"ecosystem": "npm", "kind": "package", "package": "node-ipc", "version": "9.2.1"}`
  - found in: saproto/ProTube@3aa4c8fb798e vue-remote/package-lock.json (2022-03-18)
- `5c5272c1`: `{"ecosystem": "npm", "kind": "package", "package": "node-ipc", "version": "9.1.1"}`
  - found in: ca-risken/web@d55f1a08bae1 yarn.lock (2022-03-17)

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

- `1061be5a`: `{"ecosystem": "Go", "kind": "package", "package": "gopkg.in/yaml.v3", "version": "v3.0.1"}`
  - found in: helm/helm@ef64468187f9 go.mod (2025-04-24)
- `a7e7ab76`: `{"ecosystem": "Go", "kind": "package", "package": "gopkg.in/yaml.v3", "version": "v3.0.1"}`
  - found in: docker/compose@955e4ed94ec8 go.mod (2025-04-24)
- `9581a58f`: `{"ecosystem": "Go", "kind": "package", "package": "sigs.k8s.io/yaml", "version": "v1.4.0"}`
  - found in: kubernetes/kubernetes@0d3d2733f609 go.mod (2025-04-24)
- `43805957`: `{"ecosystem": "Go", "kind": "package", "package": "gopkg.in/yaml.v2", "version": "v2.4.0"}`
  - found in: argoproj/argo-cd@0be041a83474 go.mod (2025-04-23)
- `d1a2d7f9`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/goccy/go-yaml", "version": "v1.10.0"}`
  - found in: gobitfly/eth2-beaconchain-explorer@5a5a65bd4a64 go.mod (2025-04-23)
- `c5707a52`: `{"ecosystem": "Go", "kind": "package", "package": "gopkg.in/yaml.v2", "version": "v2.4.0"}`
  - found in: prometheus/prometheus@f82e8433361a go.mod (2025-04-17)
- `872fb31f`: `{"ecosystem": "Go", "kind": "package", "package": "go.yaml.in/yaml/v3", "version": "v3.0.5"}`
  - found in: prometheus/prometheus@a87694bbef54 go.mod (2026-10-29)

## Event REL-4: coreos/prometheus-operator relocated to prometheus-operator/prometheus-operator

Knowledge date (as_of): 2020-08-05

Sources:
- **prometheus-operator#3384** <https://github.com/prometheus-operator/prometheus-operator/pull/3384>
  - archive record: record:github pull request #3384, merged 2020-08-05T13:43Z
  - archived quotation: "Move repository to new organization."
- **wayback/github.com-coreos-prometheus-operator** <https://github.com/coreos/prometheus-operator>
  - archive record: wayback:20200615012237 http://web.archive.org/web/20200615012237/https://github.com/coreos/prometheus-operator
  - archived quotation: "Repository page before the move (HTTP 200)."

References to label for this event:

- `c17a1655`: `{"kind": "image", "ref": "github.com/coreos/prometheus-operator"}`
  - found in: prometheus-operator/kube-prometheus@2326773ee1c4 jsonnet/kube-prometheus/jsonnetfile.json (2020-07-31)
- `2ce3e98a`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/coreos/prometheus-operator", "version": "v0.40.0"}`
  - found in: openshift/cluster-monitoring-operator@9bbab32f5adf go.mod (2020-08-04)
- `9fce18ee`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/coreos/prometheus-operator", "version": "v0.38.1-0.20200506070354-4231c1d4b313"}`
  - found in: tkestack/tke@1b39f9d9dd9c go.mod (2020-07-28)
- `707df66a`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/prometheus-operator/prometheus-operator", "version": "v0.94.1"}`
  - found in: openshift/cluster-monitoring-operator@8be14a1b0cc1 go.mod (2026-09-24)
- `86bafcbf`: `{"kind": "image", "ref": "quay.io/coreos/prometheus-operator:v0.40.0"}`
  - found in: prometheus-operator/kube-prometheus@63ad66e3f31e manifests/setup/prometheus-operator-deployment.yaml (2020-07-28)
- `80560426`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/coreos/prometheus-operator", "version": "v0.38.0"}`
  - found in: open-cluster-management/multicluster-observability-operator@958fa688022d go.mod (2020-06-18)

## Event DEP-6: golint frozen and deprecated

Knowledge date (as_of): 2021-05-11

Sources:
- **golang/go#38968** <https://github.com/golang/go/issues/38968>
  - archive record: wayback:20210511082834 http://web.archive.org/web/20210511082834/https://github.com/golang/go/issues/38968
  - archived quotation: "This proposal - to freeze and deprecate x/lint - is accepted."

References to label for this event:

- `1bcccfe5`: `{"ecosystem": "Go", "kind": "package", "package": "golang.org/x/lint", "version": "v0.0.0-20200302205851-738671d3881b"}`
  - found in: jaegertracing/jaeger@56af6b4d3bdb go.mod (2021-03-30)
- `a4e73f35`: `{"ecosystem": "Go", "kind": "package", "package": "golang.org/x/lint", "version": "v0.0.0-20200302205851-738671d3881b"}`
  - found in: kubernetes/kubernetes@185f65fbddb5 go.mod (2021-05-06)
- `54438d65`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/mgechev/revive", "version": "v1.0.2"}`
  - found in: etcd-io/etcd@3423a949c0fc tools/mod/go.mod (2021-04-19)
- `c04a67b5`: `{"ecosystem": "Go", "kind": "package", "package": "golang.org/x/lint", "version": "v0.0.0-20190313153728-d0100b6bd8b3"}`
  - found in: grpc/grpc-go@4e8458e5c638 test/tools/go.mod (2020-10-21)
- `641c886d`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/golang/lint", "version": null}`
  - found in: bitrise-io/bitrise@ebc001294738 Dockerfile (2018-11-30)
- `46baf50a`: `{"ecosystem": "Go", "kind": "package", "package": "golang.org/x/lint", "version": "v0.0.0-20200302205851-738671d3881b"}`
  - found in: cockroachdb/cockroach@1d45c87e4702 go.mod (2021-05-05)
- `8e128618`: `{"ecosystem": "Go", "kind": "package", "package": "honnef.co/go/tools", "version": "v0.0.1-2020.1.6"}`
  - found in: cockroachdb/cockroach@1d45c87e4702 go.mod (2021-05-05)

## Event EOL-1: Python 2.7 end of life

Knowledge date (as_of): 2020-01-02

Sources:
- **python.org/sunset-python-2** <https://www.python.org/doc/sunset-python-2/>
  - archive record: wayback:20200102202103 http://web.archive.org/web/20200102202103/https://www.python.org/doc/sunset-python-2/
  - archived quotation: "We have decided that January 1, 2020, was the day that we sunset Python 2."

References to label for this event:

- `f7412141`: `{"kind": "image", "ref": "circleci/python:2.7"}`
  - found in: remind101/empire@775178497a2c .circleci/config.yml (2019-03-30)
- `f1d4f314`: `{"kind": "image", "ref": "python:2.7.10"}`
  - found in: cloudtools/stacker@49a5fa71dc07 Dockerfile (2016-11-24)
- `5772b21b`: `{"kind": "image", "ref": "python:3.7-slim"}`
  - found in: duo-labs/cloudmapper@2cafc9c10397 Dockerfile (2019-07-25)
- `60fdd13d`: `{"kind": "image", "ref": "python:2.7"}`
  - found in: globocom/database-as-a-service@2f55198bcc3d Dockerfile (2019-08-30)
- `d83a7add`: `{"kind": "image", "ref": "python:2.7"}`
  - found in: openshift/openshift-restclient-python@a0313b721d73 Dockerfile (2017-11-02)
- `ab4aef32`: `{"kind": "image", "ref": "python:2.7"}`
  - found in: Netflix-Skunkworks/stethoscope@b9f3a74a1f3f Dockerfile (2018-03-13)

## Event DEP-3: TSLint deprecated in favour of ESLint

Knowledge date (as_of): 2019-05-08

Sources:
- **palantir/tslint-in-2019** <https://medium.com/palantir/tslint-in-2019-1a144c2317a9>
  - archive record: wayback:20190219201734 http://web.archive.org/web/20190219201734/https://medium.com/palantir/tslint-in-2019-1a144c2317a9
  - archived quotation: "TSLint will be deprecated in favor of supporting typescript-eslint."
- **palantir/tslint#4534** <https://github.com/palantir/tslint/issues/4534>
  - archive record: wayback:20190508120833 http://web.archive.org/web/20190508120833/https://github.com/palantir/tslint/issues/4534
  - archived quotation: "Roadmap: stop accepting any PRs on 2020-12-01."

References to label for this event:

- `e65c8b48`: `{"ecosystem": "npm", "kind": "package", "package": "tslint", "version": "5.20.1"}`
  - found in: ReactiveX/rxjs@7a11ad2c71f6 package-lock.json (2020-11-23)
- `60cb7fbf`: `{"ecosystem": "npm", "kind": "package", "package": "@typescript-eslint/eslint-plugin", "version": "3.2.0"}`
  - found in: microsoft/vscode@5e7cd9987627 yarn.lock (2021-05-28)
- `f622d1bf`: `{"ecosystem": "npm", "kind": "package", "package": "tslint-config-prettier", "version": "1.18.0"}`
  - found in: ReactiveX/rxjs@7a11ad2c71f6 package-lock.json (2020-11-23)
- `3f25d87d`: `{"ecosystem": "npm", "kind": "package", "package": "tslint", "version": "6.1.3"}`
  - found in: palantir/blueprint@6c8d1912891a yarn.lock (2020-10-05)
- `2866e41c`: `{"ecosystem": "npm", "kind": "package", "package": "tslint", "version": "5.11.0"}`
  - found in: Microsoft/vscode@ac8fd91011cf yarn.lock (2019-02-19)
- `4f8c8b55`: `{"ecosystem": "npm", "kind": "package", "package": "tslint", "version": "6.1.3"}`
  - found in: angular/angular@318255a5f872 yarn.lock (2020-11-25)

## Event DIS-1: k8s.gcr.io redirected to registry.k8s.io and frozen

Knowledge date (as_of): 2023-03-15

Sources:
- **kubernetes.io/registry-k8s-io-ga** <https://kubernetes.io/blog/2022/11/28/registry-k8s-io-faster-cheaper-ga/>
  - archive record: wayback:20221129154618 http://web.archive.org/web/20221129154618/https://kubernetes.io/blog/2022/11/28/registry-k8s-io-faster-cheaper-ga/
  - archived quotation: "registry.k8s.io is generally available; new images will stop being published to k8s.gcr.io."
- **kubernetes.io/k8s-gcr-io-freeze** <https://kubernetes.io/blog/2023/02/06/k8s-gcr-io-freeze-announcement/>
  - archive record: wayback:20230213025122 http://web.archive.org/web/20230213025122/https://kubernetes.io/blog/2023/02/06/k8s-gcr-io-freeze-announcement/
  - archived quotation: "No further images for Kubernetes and related subprojects will be pushed to the old registry."
- **kubernetes.io/image-registry-redirect** <https://kubernetes.io/blog/2023/03/10/image-registry-redirect/>
  - archive record: wayback:20230315231813 http://web.archive.org/web/20230315231813/https://kubernetes.io/blog/2023/03/10/image-registry-redirect/
  - archived quotation: "ALL images on k8s.gcr.io will be impacted by this change."

References to label for this event:

- `6a288c15`: `{"kind": "image", "ref": "k8s.gcr.io/pause"}`
  - found in: jpetazzo/obs-docker@605d8163db53 docker-compose.yml (2021-05-07)
- `2b774735`: `{"kind": "image", "ref": "gcr.io/cadvisor/cadvisor:v0.37.0"}`
  - found in: mbugeia/srt2hls@fe87a0f8fa2d docker-compose.yml (2021-10-04)
- `41f69e82`: `{"kind": "image", "ref": "k8s.gcr.io/echoserver:1.10"}`
  - found in: pjoe/loadem@367ddb4a764f docker-compose.yml (2020-10-14)
- `5e105297`: `{"kind": "image", "ref": "k8s.gcr.io/etcd-amd64:3.1.12"}`
  - found in: deitch/kubesync@235189b7d317 test/docker-compose.yml (2018-07-20)
- `67172da3`: `{"kind": "image", "ref": "registry.k8s.io/metrics-server/metrics-server"}`
  - found in: kubernetes-sigs/metrics-server@e86a9f02b73a charts/metrics-server/values.yaml (2022-12-22)
- `9275c434`: `{"kind": "image", "ref": "registry.k8s.io/pause:3.8"}`
  - found in: sergelogvinov/devops-examples@8cd3b1473506 python/docker-compose.yml (2024-09-05)
- `1d141517`: `{"kind": "image", "ref": "k8s.gcr.io/ingress-gce-glbc-amd64:v1.8.0"}`
  - found in: kubernetes/ingress-gce@75f14a06c244 docs/deploy/gke/non-gcp/glbc.yaml (2023-03-06)

## Event CMP-4: Hijacked ua-parser-js versions

Knowledge date (as_of): 2021-10-23

Sources:
- **faisalman/ua-parser-js#536** <https://github.com/faisalman/ua-parser-js/issues/536>
  - archive record: wayback:20211023193659 http://web.archive.org/web/20211023193659/https://github.com/faisalman/ua-parser-js/issues/536
  - archived quotation: "Published some compromised packages (0.7.29, 0.8.0, 1.0.0)."

References to label for this event:

- `55927023`: `{"ecosystem": "npm", "kind": "package", "package": "ua-parser-js", "version": "0.7.28"}`
  - found in: openwebdocs/mdn-bcd-collector@a16a4f8a7565 package-lock.json (2021-10-25)
- `fc9df59a`: `{"ecosystem": "npm", "kind": "package", "package": "ua-parser-js", "version": "0.7.29"}`
  - found in: smartcoder0777/nebula.gl@65812697f946 examples/sf/yarn.lock (2021-10-22)
- `e5b6814b`: `{"ecosystem": "npm", "kind": "package", "package": "ua-parser-js", "version": "0.7.29"}`
  - found in: Esger/Pentominos2@86c582c0f7fe package-lock.json (2021-10-22)
- `9fd11ca8`: `{"ecosystem": "npm", "kind": "package", "package": "ua-parser-js", "version": "0.7.30"}`
  - found in: navikt/aksel-website@09036ceeae44 yarn.lock (2021-10-22)
- `371f542c`: `{"ecosystem": "npm", "kind": "package", "package": "ua-parser-js", "version": "0.7.29"}`
  - found in: navikt/aksel-website@3354bfa68750 yarn.lock (2021-10-22)

## Event DEP-1: npm package request fully deprecated

Knowledge date (as_of): 2020-02-11

Sources:
- **request/request@aded7e4f8e** <https://github.com/request/request/commit/aded7e4f8e>
  - archive record: record:github commit aded7e4f8e (README)
  - archived quotation: "As of Feb 11th 2020, request is fully deprecated. No new changes are expected to land."
- **wayback/github.com-request-request** <https://github.com/request/request>
  - archive record: wayback:20200211201636 http://web.archive.org/web/20200211201636/https://github.com/request/request
  - archived quotation: "Repository README with the deprecation notice."

References to label for this event:

- `11442ccc`: `{"ecosystem": "npm", "kind": "package", "package": "request", "version": "^2.88.0"}`
  - found in: nodejs/node-gyp@a79d866ac3bf package.json (2020-01-08)
- `3f623f49`: `{"ecosystem": "npm", "kind": "package", "package": "request-promise", "version": "4.2.4"}`
  - found in: PolymathNetwork/polymath-core@d7f1102f9c83 yarn.lock (2019-12-27)
- `c17fe886`: `{"ecosystem": "npm", "kind": "package", "package": "request", "version": "2.88.0"}`
  - found in: electron/electron@fcee7212ce19 yarn.lock (2019-11-05)
- `43eaefa5`: `{"ecosystem": "npm", "kind": "package", "package": "@cypress/request", "version": "2.88.10"}`
  - found in: cypress-io/cypress@c4ad4253ef96 yarn.lock (2023-05-25)
- `a5e74f11`: `{"ecosystem": "npm", "kind": "package", "package": "request", "version": "2.88.0"}`
  - found in: Microsoft/vscode@99cce92f4220 yarn.lock (2020-02-10)
- `416346e2`: `{"ecosystem": "npm", "kind": "package", "package": "request", "version": "2.88.0"}`
  - found in: npm/cli@f533d61eb27c package-lock.json (2020-01-28)

## Event DEP-4: Node Sass end of life

Knowledge date (as_of): 2024-08-12

Sources:
- **sass-lang/node-sass-is-end-of-life** <https://sass-lang.com/blog/node-sass-is-end-of-life/>
  - archive record: wayback:20240812011239 http://web.archive.org/web/20240812011239/https://sass-lang.com/blog/node-sass-is-end-of-life/
  - archived quotation: "The npm package has been marked as deprecated, and the GitHub repository has been archived."

References to label for this event:

- `7bda0f4f`: `{"ecosystem": "npm", "kind": "package", "package": "node-sass", "version": "4.14.1"}`
  - found in: akveo/ngx-admin@651dadee3384 package-lock.json (2023-10-29)
- `a5a3c682`: `{"ecosystem": "npm", "kind": "package", "package": "sass-embedded", "version": "1.78.0"}`
  - found in: engineervix/cv@cdb5d7f471b6 package-lock.json (2025-01-25)
- `9df3b3e2`: `{"ecosystem": "npm", "kind": "package", "package": "node-sass", "version": "8.0.0"}`
  - found in: naver/typedoc-to-mdx@bd7a09c18947 package-lock.json (2023-03-10)
- `c49e4a28`: `{"ecosystem": "npm", "kind": "package", "package": "node-sass", "version": "7.0.1"}`
  - found in: openSUSE/fuel-ignition@d0aeecf9a8e7 package-lock.json (2023-08-09)
- `97e90d74`: `{"ecosystem": "npm", "kind": "package", "package": "node-sass", "version": "9.0.0"}`
  - found in: btcpayserver/btcpayserver-design@8bbb8d4bf955 package-lock.json (2024-06-27)
- `f2dbcfa1`: `{"ecosystem": "npm", "kind": "package", "package": "sass", "version": "1.77.8"}`
  - found in: twbs/bootstrap@f406388c1ba3 package-lock.json (2024-07-15)

## Event CMP-1: Sabotaged colors versions

Knowledge date (as_of): 2022-01-21

Sources:
- **GHSA-5rqg-jm4f-cqx7** <https://github.com/advisories/GHSA-5rqg-jm4f-cqx7>
  - archive record: wayback:20220115123912 http://web.archive.org/web/20220115123912/https://github.com/advisories/GHSA-5rqg-jm4f-cqx7
  - archived quotation: "colors versions 1.4.1, 1.4.2, and 1.4.44-liberty-2 were published including malicious code."
- **GHSA-gh88-3pxp-6fm8** <https://github.com/advisories/GHSA-gh88-3pxp-6fm8>
  - archive record: record:github advisory GHSA-gh88-3pxp-6fm8 (affected >= 1.4.1)
  - archived quotation: "Affected versions: >= 1.4.1."

References to label for this event:

- `6c06dd73`: `{"ecosystem": "npm", "kind": "package", "package": "colors", "version": "1.4.2"}`
  - found in: CaoMeiYouRen/koa2-template@21798a4e3b24 yarn.lock (2022-01-10)
- `bab10f52`: `{"ecosystem": "npm", "kind": "package", "package": "colors", "version": "1.4.2"}`
  - found in: ingio/console-app@b4a79c89d938 package-lock.json (2022-01-10)
- `af82b0f2`: `{"ecosystem": "npm", "kind": "package", "package": "colors", "version": "1.4.2"}`
  - found in: zulybot/zuly@d5350e2a47e5 yarn.lock (2022-01-10)
- `7fefde73`: `{"ecosystem": "npm", "kind": "package", "package": "colors", "version": "1.4.1"}`
  - found in: karrot-dev/karrot-frontend@5a65b679e2ce yarn.lock (2022-01-10)
- `08f47657`: `{"ecosystem": "npm", "kind": "package", "package": "colors", "version": "1.4.0"}`
  - found in: winstonjs/winston@d18198d14935 package-lock.json (2022-01-25)
- `6e01dfc9`: `{"ecosystem": "npm", "kind": "package", "package": "@colors/colors", "version": "1.5.0"}`
  - found in: winstonjs/winston@70fc03d046ee package-lock.json (2022-03-11)
- `432be208`: `{"ecosystem": "npm", "kind": "package", "package": "colors", "version": "1.4.0"}`
  - found in: aws/aws-cdk@455147a5c3ed yarn.lock (2022-01-09)

## Event DIS-6: Official java image deprecated in favour of openjdk

Knowledge date (as_of): 2016-10-27

Sources:
- **docker-library/docs@a3439b6** <https://github.com/docker-library/docs/commit/a3439b66b798>
  - archive record: wayback:20161027201850 http://web.archive.org/web/20161027201850/https://hub.docker.com/_/java/
  - archived quotation: "This image is officially deprecated in favor of the openjdk image, and will receive no further updates after 2016-12-31."

References to label for this event:

- `1c66c45c`: `{"kind": "image", "ref": "dockerfile/java:oracle-java8"}`
  - found in: baasbox/baasbox@313f7dea3d06 Dockerfile (2015-03-20)
- `04aeb634`: `{"kind": "image", "ref": "java:8"}`
  - found in: cer/event-sourcing-examples@bbea6d9d2f8f scala-spring/docker-compose.yml (2015-12-21)
- `ad03e156`: `{"kind": "image", "ref": "java:8-jre"}`
  - found in: mesos/chronos@35ca3295ed7e Dockerfile (2016-12-03)
- `cbb13cd5`: `{"kind": "image", "ref": "java:8"}`
  - found in: cptactionhank/docker-atlassian-jira-software@557212a6a112 Dockerfile (2016-12-29)
- `ca5176e8`: `{"kind": "image", "ref": "java:8"}`
  - found in: SwellRT/swellrt@ddf7a8361fa9 Dockerfile (2016-12-05)

## Event DIS-4: Official centos image deprecated and removed from the library

Knowledge date (as_of): 2024-12-12

Sources:
- **docker-library/docs#2205** <https://github.com/docker-library/docs/pull/2205>
  - archive record: wayback:20221014104857 http://web.archive.org/web/20221014104857/http://hub.docker.com/_/centos
  - archived quotation: "This image is no longer supported/maintained."
- **docker-library/official-images#17094** <https://github.com/docker-library/official-images/pull/17094>
  - archive record: wayback:20241212144136 http://web.archive.org/web/20241212144136/https://github.com/docker-library/official-images/pull/17094
  - archived quotation: "All tags of this image are EOL."

References to label for this event:

- `a0488b06`: `{"kind": "image", "ref": "quay.io/centos/centos:stream9"}`
  - found in: theforeman/foreman@a88d8d36b233 Dockerfile (2024-04-10)
- `950c5fe3`: `{"kind": "image", "ref": "centos:7"}`
  - found in: naver/arcus-memcached@f29fde9df908 Dockerfile (2024-06-11)
- `4cca3cb9`: `{"kind": "image", "ref": "rockylinux:8"}`
  - found in: harvard-nrg/anatqc@16889526c983 Dockerfile (2023-06-06)
- `42ebab65`: `{"kind": "image", "ref": "centos:8"}`
  - found in: harvard-nrg/anatqc@28b27180651e Dockerfile (2022-06-24)
- `e653742c`: `{"kind": "image", "ref": "centos:7"}`
  - found in: orlabs/orange@285e4f4a195f Dockerfile (2022-08-01)
- `7edb79a4`: `{"kind": "image", "ref": "quay.io/centos/centos:stream8"}`
  - found in: firewalld/firewalld@c7370b4238da Dockerfile (2022-03-10)
- `15e76a55`: `{"kind": "image", "ref": "centos:7"}`
  - found in: aliyun/rds_dbsync@35bb00a26273 Dockerfile (2018-12-22)

## Event LIC-3: Grafana relicensed from Apache-2.0 to AGPLv3 from 8.0

Knowledge date (as_of): 2021-04-21

Sources:
- **grafana/relicensing-to-agplv3** <https://grafana.com/blog/2021/04/20/grafana-loki-tempo-relicensing-to-agplv3/>
  - archive record: wayback:20210421230514 http://web.archive.org/web/20210421230514/https://grafana.com/blog/2021/04/20/grafana-loki-tempo-relicensing-to-agplv3/
  - archived quotation: "We are relicensing our core open source projects from Apache 2.0 to AGPLv3."

References to label for this event:

- `90a2b443`: `{"kind": "image", "ref": "grafana/grafana:8.0.2"}`
  - found in: bcremer/docker-telegraf-influx-grafana-stack@70b806c2b8c0 docker-compose.yml (2021-06-15)
- `88be0110`: `{"kind": "image", "ref": "grafana/grafana:8.0.5"}`
  - found in: akoutmos/nerves_weather_station@3895389fc5c5 server_code/docker-compose.yml (2021-07-17)
- `20c2c449`: `{"kind": "image", "ref": "grafana/grafana:8.0.3"}`
  - found in: OtusGolang/webinars_practical_part@06a8facf525e 32-monitoring/docker-compose.yml (2021-07-01)
- `a63f07a0`: `{"kind": "image", "ref": "grafana/grafana:7.5.5"}`
  - found in: warriorBrian/nuxt-blog@ee3d8b87420b prometheus/docker-compose.yml (2021-05-24)
- `c32b29d7`: `{"kind": "image", "ref": "grafana/grafana:7.5.5"}`
  - found in: orb-community/orb@d69b91f3ed6c docker/docker-compose.yml (2021-05-21)
- `077337c6`: `{"kind": "image", "ref": "grafana/grafana:8.0.6"}`
  - found in: harryjubb/bee_iot@d87929131dc4 server/docker-compose.yml (2021-08-05)
- `aa979c36`: `{"kind": "image", "ref": "grafana/grafana:7.5.2"}`
  - found in: testinggospels/camouflage@7599ad9f269c docker-compose.yml (2021-05-19)

## Event CMP-2: Sabotaged faker 6.6.6

Knowledge date (as_of): 2022-03-22

Sources:
- **GHSA-5w9c-rv96-fr7g** <https://github.com/advisories/GHSA-5w9c-rv96-fr7g>
  - archive record: record:github advisory GHSA-5w9c-rv96-fr7g (faker = 6.6.6)
  - archived quotation: "The maintainer deliberately removed the functional code from this package."
- **wayback/github.com-Marak-faker.js** <https://github.com/Marak/faker.js>
  - archive record: wayback:20220106193513 http://web.archive.org/web/20220106193513/https://github.com/Marak/faker.js
  - archived quotation: "Repository page after the 6.6.6 release."

References to label for this event:

- `5c97f1aa`: `{"ecosystem": "npm", "kind": "package", "package": "faker", "version": "6.6.6"}`
  - found in: pieforproviders/pieforproviders@450b63596f3f yarn.lock (2022-01-10)
- `9e252af0`: `{"ecosystem": "npm", "kind": "package", "package": "faker", "version": "6.6.6"}`
  - found in: pulumi/actions@9e2ba1369a13 yarn.lock (2022-01-18)
- `930fc502`: `{"ecosystem": "npm", "kind": "package", "package": "@faker-js/faker", "version": "6.0.0"}`
  - found in: forem/forem@91e3b5e2cb79 yarn.lock (2022-03-21)
- `12d45b9c`: `{"ecosystem": "npm", "kind": "package", "package": "faker", "version": "6.6.6"}`
  - found in: dipjyotimetia/CypressTestFramework@166c247b8b94 package-lock.json (2022-01-05)
- `1933a4fa`: `{"ecosystem": "npm", "kind": "package", "package": "faker", "version": "6.6.6"}`
  - found in: rubyforgood/casa@47e3af39d1fe yarn.lock (2022-01-10)
- `10e6e13a`: `{"ecosystem": "npm", "kind": "package", "package": "faker", "version": "5.5.3"}`
  - found in: pulumi/actions@15a649aa40e1 yarn.lock (2022-01-18)

## Event REL-3: docker/distribution repository relocated to distribution/distribution

Knowledge date (as_of): 2021-02-05

Sources:
- **docker/blog-donating-distribution** <https://www.docker.com/blog/donating-docker-distribution-to-the-cncf/>
  - archive record: wayback:20210205005303 http://web.archive.org/web/20210205005303/https://www.docker.com/blog/donating-docker-distribution-to-the-cncf/
  - archived quotation: "The project is now simply called Distribution, at github.com/distribution/distribution."
- **wayback/github.com-docker-distribution-301** <https://github.com/docker/distribution>
  - archive record: wayback:20210129093412 http://web.archive.org/web/20210129093412/https://github.com/docker/distribution
  - archived quotation: "First archived HTTP 301 for github.com/docker/distribution."

References to label for this event:

- `879f9c60`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/docker/distribution", "version": "v2.7.1+incompatible"}`
  - found in: kubernetes/kubernetes@562a39a2e1e2 go.mod (2021-01-28)
- `fcf9b3dc`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/distribution/distribution", "version": "v3.1.2"}`
  - found in: goreleaser/goreleaser@9adc473ee22f go.mod (2026-10-26)
- `4129aead`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/docker/distribution", "version": "v2.7.1+incompatible"}`
  - found in: helm/helm@e8817d7a1867 go.mod (2021-01-27)
- `baef36b3`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/docker/distribution", "version": "v2.7.1+incompatible"}`
  - found in: goharbor/harbor@e6b53593ee5b src/go.mod (2020-12-09)
- `aa4e11a2`: `{"ecosystem": "Go", "kind": "package", "package": "cosmossdk.io/x/distribution", "version": "v0.2.0-rc.1"}`
  - found in: cordialsys/crosschain@ca7c798d38d2 go.mod (2026-10-15)
- `5d5105d9`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/docker/distribution", "version": "v2.7.1+incompatible"}`
  - found in: containers/image@88cc8ef4bda7 go.mod (2021-01-15)

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

- `6c31e152`: `{"kind": "image", "ref": "hashicorp/terraform:1.6.4"}`
  - found in: TelkomIndonesia/terraq@aabe715f5be5 Dockerfile (2023-11-20)
- `043706f8`: `{"kind": "image", "ref": "hashicorp/terraform:1.5.4"}`
  - found in: cmdlabs/terraform-aws-gitlab-runner-scale@c3c8e7b3dbe4 Dockerfile-terraform (2023-08-02)
- `35a01765`: `{"kind": "image", "ref": "ghcr.io/opentofu/opentofu:1.12.1-minimal"}`
  - found in: flux-iac/tofu-controller@c2c83130c236 runner.Dockerfile (2026-05-28)
- `06e17978`: `{"kind": "image", "ref": "hashicorp/terraform:1.5.7"}`
  - found in: KazanExpress/ke-infra-docker@1f7fca9bb1ca images/terragrunt/v0.51.3-tfv1.5.7-tools/Dockerfile (2023-09-20)
- `7a386608`: `{"kind": "image", "ref": "hashicorp/terraform:1.6@sha256:e46b41c74b6f036c255e2082bcd6284054b108508bae16813bc1257a0e70e2dd"}`
  - found in: observeinc/aws-test-kitchen@3804d4d3bcbf Dockerfile (2023-11-29)
- `6140f3b6`: `{"kind": "image", "ref": "hashicorp/terraform:1.6.5"}`
  - found in: KazanExpress/ke-infra-docker@25e3d7148dfb images/terragrunt/v0.53.8-tfv1.6.5-tools/Dockerfile (2023-12-06)
- `7e2cba82`: `{"kind": "image", "ref": "hashicorp/terraform:1.6.2"}`
  - found in: thedatafoundation/gha-iac@de9e61bd1c17 Dockerfile (2023-12-11)

## Event DEP-2: golang/dep deprecated and archived

Knowledge date (as_of): 2020-09-17

Sources:
- **golang/go#38158** <https://github.com/golang/go/issues/38158>
  - archive record: wayback:20200808211416 http://web.archive.org/web/20200808211416/https://github.com/golang/go/issues/38158
  - archived quotation: "Proposal to add deprecation language to the README and archive the repository."
- **wayback/github.com-golang-dep** <https://github.com/golang/dep>
  - archive record: wayback:20200917033647 http://web.archive.org/web/20200917033647/https://github.com/golang/dep
  - archived quotation: "As of 2020, Dep is deprecated and archived in favor of Go modules."

References to label for this event:

- `611ec3d3`: `{"kind": "image", "ref": "github.com/golang/dep"}`
  - found in: jaegertracing/jaeger@043b1ae85662 Gopkg.toml (2020-02-19)
- `12f20c83`: `{"kind": "image", "ref": "github.com/tools/godep"}`
  - found in: kubernetes/kubernetes@85bd96521932 Godeps/Godeps.json (2017-04-17)
- `075b1e05`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/golang/dep", "version": null}`
  - found in: istio/istio@da7ef3fb9655 Makefile (2018-05-25)
- `0ef37ab8`: `{"kind": "image", "ref": "github.com/golang/dep"}`
  - found in: knative/serving@06d5f04a0fb5 Gopkg.toml (2020-04-21)
- `41f9a581`: `{"kind": "image", "ref": "github.com/golang/dep"}`
  - found in: vmware-tanzu/velero@b2acd3b683c5 Gopkg.toml (2020-01-14)

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
- `a27216a0`: `{"kind": "image", "ref": "library/openjdk:21"}`
  - found in: navikt/statusplattform@a3f0baef4057 Dockerfile (2025-03-07)
- `56525d5b`: `{"kind": "image", "ref": "openjdk:jre"}`
  - found in: fabric8io/docker-maven-plugin@d36d5c70e7b6 samples/run-java/Dockerfile (2018-05-16)
- `a25fa6b2`: `{"kind": "image", "ref": "openjdk:8u342-jre"}`
  - found in: arempter/hive-metastore-docker@e15fc5116d10 Dockerfile (2023-01-31)
- `aab49605`: `{"kind": "image", "ref": "openjdk:21-slim"}`
  - found in: tencentmusic/supersonic@614917ba7648 docker/Dockerfile (2025-04-02)
- `f2999c16`: `{"kind": "image", "ref": "eclipse-temurin:21"}`
  - found in: genome-nexus/genome-nexus@e7d088c16528 Dockerfile (2025-08-04)
- `a4947bca`: `{"kind": "image", "ref": "openjdk:17-jdk-slim"}`
  - found in: melonlee/LazyAdmin@07e4969e9cdf Dockerfile (2025-07-13)

## Event DIS-5: Official adoptopenjdk image deprecated in favour of eclipse-temurin

Knowledge date (as_of): 2021-08-25

Sources:
- **docker-library/docs@4baab4b** <https://github.com/docker-library/docs/commit/4baab4b75b58>
  - archive record: wayback:20210825110321 http://web.archive.org/web/20210825110321/https://hub.docker.com/_/adoptopenjdk
  - archived quotation: "This image is officially deprecated in favor of the eclipse-temurin image, and will receive no further updates after 2021-08-01."

References to label for this event:

- `705d8826`: `{"kind": "image", "ref": "adoptopenjdk/openjdk11:alpine"}`
  - found in: gomint/gomint@eb083dd0ba6b Dockerfile (2020-07-10)
- `2c46edb5`: `{"kind": "image", "ref": "adoptopenjdk:11"}`
  - found in: metriql/metriql@3752b9643984 Dockerfile (2021-07-31)
- `a5c6b04a`: `{"kind": "image", "ref": "adoptopenjdk:11-jre-openj9"}`
  - found in: adevinta/zoe@a84a8e01bf07 zoe-cli/Dockerfile (2021-04-15)
- `a1df2acd`: `{"kind": "image", "ref": "eclipse-temurin:17"}`
  - found in: gaia-app/gaia@619bf1e92922 Dockerfile (2021-10-08)
- `a67bfe74`: `{"kind": "image", "ref": "adoptopenjdk:11-jre"}`
  - found in: box/mojito@fc9501edbcd8 docker/Dockerfile-bk11 (2021-06-11)
- `018563e8`: `{"kind": "image", "ref": "adoptopenjdk:11-jre-hotspot"}`
  - found in: thombergs/code-examples@029a5f03fb19 spring-boot/spring-boot-health-check/Dockerfile (2020-09-19)

## Event LIC-1: Elasticsearch and Kibana relicensed from Apache-2.0 from 7.11

Knowledge date (as_of): 2021-01-15

Sources:
- **elastic/licensing-change** <https://www.elastic.co/blog/licensing-change>
  - archive record: wayback:20210115230839 http://web.archive.org/web/20210115230839/https://www.elastic.co/blog/licensing-change
  - archived quotation: "Starting with the upcoming Elastic 7.11 release, we will be moving the Apache 2.0-licensed code to dual license."

References to label for this event:

- `3a7bc541`: `{"kind": "image", "ref": "docker.elastic.co/elasticsearch/elasticsearch:7.13.4"}`
  - found in: reelyactive/pareto-anywhere@4827d9f3e515 docker-compose.yml (2021-08-02)
- `a3822fcc`: `{"kind": "image", "ref": "docker.elastic.co/elasticsearch/elasticsearch:7.10.2"}`
  - found in: deric/es-dedupe@04fdb3701b4c docker-compose.yml (2021-02-03)
- `8dd7e794`: `{"kind": "image", "ref": "docker.elastic.co/elasticsearch/elasticsearch:7.12.0"}`
  - found in: dineshsonachalam/tech-courses-search-engine@137f0cb3fcf6 docker-compose.yml (2021-05-08)
- `bf4cf069`: `{"kind": "image", "ref": "docker.elastic.co/elasticsearch/elasticsearch:7.13.0"}`
  - found in: netsampler/goflow2@80ef166b84b9 compose/elk/docker-compose.yml (2021-06-01)
- `e0324104`: `{"kind": "image", "ref": "docker.elastic.co/kibana/kibana:7.12.0"}`
  - found in: mooreniemi/Transbucket_Rails@25287a3c7be8 docker-compose.yml (2021-04-04)

## Event DIS-2: Official openjdk image deprecated (no non-EA updates after July 2022)

Knowledge date (as_of): 2022-07-18

Sources:
- **docker-library/docs@326814f** <https://github.com/docker-library/docs/commit/326814f7acbd>
  - archive record: record:github commit 326814f7acbd (openjdk deprecation notice)
  - archived quotation: "This image is officially deprecated and all users are recommended to find and use suitable replacements ASAP."
- **docker-library/openjdk#505** <https://github.com/docker-library/openjdk/issues/505>
  - archive record: wayback:20220718201219 http://web.archive.org/web/20220718201219/https://github.com/docker-library/openjdk/issues/505
  - archived quotation: "Upstream retirement notice for the OpenJDK builds the image is sourced from."

References to label for this event:

- `7afaf0ed`: `{"kind": "image", "ref": "openjdk:19-ea-16-slim"}`
  - found in: ttrzcinski/RestJ12@4d7fcd824583 Dockerfile (2022-05-02)
- `cbed9502`: `{"kind": "image", "ref": "eclipse-temurin:17"}`
  - found in: gaia-app/gaia@619bf1e92922 Dockerfile (2021-10-08)
- `0a896452`: `{"kind": "image", "ref": "adoptopenjdk/openjdk11:alpine-slim"}`
  - found in: virtualansoftware/service-virtualization-openapi@290daa4adfb2 Dockerfile (2022-03-11)
- `a46b5ec7`: `{"kind": "image", "ref": "openjdk:8-jdk-alpine"}`
  - found in: confluentinc/kafka-connect-http-demo@35af36e97cc5 Dockerfile (2019-05-09)
- `2cfa1ca5`: `{"kind": "image", "ref": "openjdk:8-jdk-alpine"}`
  - found in: dsyer/kubernetes-intro@c3ea9a8c5cfe Dockerfile (2020-03-23)
- `d041bd8d`: `{"kind": "image", "ref": "openjdk:8-jre-slim-bullseye"}`
  - found in: Graylog2/graylog-docker@47ec065f1814 docker/oss/Dockerfile (2021-12-15)
- `617b7e97`: `{"kind": "image", "ref": "openjdk:8-jdk-alpine"}`
  - found in: shzlw/poli@75137ec7abc1 Dockerfile (2020-05-22)

## Event REL-1: docker/docker repository relocated to moby/moby

Knowledge date (as_of): 2017-04-20

Sources:
- **moby/moby#32691** <https://github.com/moby/moby/pull/32691>
  - archive record: wayback:20170420213705 http://web.archive.org/web/20170420213705/https://github.com/moby/moby/pull/32691
  - archived quotation: "If you are a Docker user, nothing changes."

References to label for this event:

- `1d9aae6d`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/docker/docker", "version": null}`
  - found in: hashicorp/terraform@b8b896e11b5a vendor/vendor.json (2017-04-16)
- `7b63da6f`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/docker/docker", "version": null}`
  - found in: hashicorp/nomad@4e61de3e5754 vendor/vendor.json (2017-04-12)
- `2f0d4f33`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/docker/engine-api", "version": null}`
  - found in: kubernetes/kubernetes@85bd96521932 Godeps/Godeps.json (2017-04-17)
- `9c0bca09`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/docker/docker", "version": null}`
  - found in: kubernetes/kubernetes@85bd96521932 Godeps/Godeps.json (2017-04-17)
- `deba6fde`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/docker/docker", "version": null}`
  - found in: openshift/origin@cc467d40b3a1 Godeps/Godeps.json (2017-04-05)
- `b10f36e3`: `{"ecosystem": "Go", "kind": "package", "package": "github.com/moby/moby", "version": "v1.54.1"}`
  - found in: google/cadvisor@f00f449b15bb go.mod (2026-10-02)

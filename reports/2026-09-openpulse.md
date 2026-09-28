# OpenPulse — 2026-09

100 projects monitored

58 significant events

_158 related-but-unconfirmed records held back (see `openpulse analyze` for the full stream)._

## 🔴 Action-worthy changes (28)

### cert-manager

Pulse: lifecycle action

🔴 **[EOL]** cert-manager 1.19 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 1.19 reached EOL on 2026-07-08; no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/cert-manager

🟠 **[SECURITY]** CVE-2026-62290 [AFFECTS_PACKAGE] tracked by nvd (_analyst=security, suggested impact=REVIEW_)
cert-manager adds certificates and certificate issuers as resource types in Kubernetes clusters, and simplifies the process of obtaining, renewing and using those certificates. From 1.18.0 until 1.19.6 and 1.20.3, Challenge resources under acme.cert-manager.io can be created directly by namespace us

Evidence: security, nvd
- https://github.com/cert-manager/cert-manager/commit/6bda47297c8fbc6b121b8b76624b668d26f1a155
- https://github.com/cert-manager/cert-manager/commit/b37dbf01ecea50a0b3a19df0a7fe4c5ad6803f16
- https://github.com/cert-manager/cert-manager/pull/8940
- https://github.com/cert-manager/cert-manager/pull/8941
- https://github.com/cert-manager/cert-manager/releases/tag/v1.19.6
- https://github.com/cert-manager/cert-manager/releases/tag/v1.20.3
- https://github.com/cert-manager/cert-manager/security/advisories/GHSA-8rvj-mm4h-c258

### minio

Pulse: activity action, lifecycle action

🔴 **[PROJECT_ARCHIVED]** minio/minio is archived on GitHub (_analyst=change, suggested impact=ACTION_)
The repository is read-only; no fixes will land. Last push 2026-04-24T17:54:39Z. Migrate off it.

Evidence: change
- https://github.com/minio/minio

### airflow

Pulse: lifecycle action

🟠 **[EOS]** apache-airflow 3.3 ended active support (_analyst=change, suggested impact=REVIEW_)
Active support for cycle 3.3 ended (date not published); only security fixes, if any.

Evidence: change
- https://endoflife.date/apache-airflow

🔴 **[EOL]** apache-airflow 3.2 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 3.2 reached EOL on 2026-07-06; no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/apache-airflow

### argocd

Pulse: lifecycle action

🔴 **[EOL]** argo-cd 3.2 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 3.2 reached EOL on 2026-08-04; no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/argo-cd

### cilium

Pulse: lifecycle action

🔴 **[EOL]** cilium 1.17 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 1.17 reached EOL on 2026-07-29; no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/cilium

### clickhouse

Pulse: lifecycle action

🔴 **[EOL]** clickhouse lifecycle: reached end-of-life (26.6, 26.5, 26.4, 25.8) (_analyst=event-correlation, suggested impact=ACTION_)
4 cycles share one lifecycle story; strongest signal kept at ACTION.

Evidence: event-correlation
- https://endoflife.date/clickhouse

🟠 **[EOL]** clickhouse 26.3 EOL approaching (2027-03-26) (_analyst=change, suggested impact=REVIEW_)
Cycle 26.3 ends in 179 days. Start migration planning now.

Evidence: change
- https://endoflife.date/clickhouse

### containerd

Pulse: lifecycle action

🟠 **[EOL]** containerd lifecycle: approaching end-of-life (2.2, 2.0) (_analyst=event-correlation, suggested impact=REVIEW_)
2 cycles share one lifecycle story; strongest signal kept at REVIEW.

Evidence: event-correlation
- https://endoflife.date/containerd

🔴 **[EOL]** containerd lifecycle: reached end-of-life (2.1, 1.7) (_analyst=event-correlation, suggested impact=ACTION_)
2 cycles share one lifecycle story; strongest signal kept at ACTION.

Evidence: event-correlation
- https://endoflife.date/containerd

### elasticsearch

Pulse: lifecycle action

🔴 **[EOL]** elasticsearch 9.3 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 9.3 reached EOL on 2026-08-04; no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/elasticsearch

### envoy

Pulse: lifecycle action

🟠 **[EOL]** envoy lifecycle: approaching end-of-life (1.37, 1.36) (_analyst=event-correlation, suggested impact=REVIEW_)
2 cycles share one lifecycle story; strongest signal kept at REVIEW.

Evidence: event-correlation
- https://endoflife.date/envoy

🔴 **[EOL]** envoy 1.35 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 1.35 reached EOL on 2026-07-23; no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/envoy

### go

Pulse: lifecycle action

🔴 **[EOL]** go 1.25 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 1.25 reached EOL on 2026-08-19; no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/go

### grafana

Pulse: lifecycle action

🟠 **[EOS]** grafana lifecycle: ended active support (13.2, 13.1) (_analyst=event-correlation, suggested impact=REVIEW_)
2 cycles share one lifecycle story; strongest signal kept at REVIEW.

Evidence: event-correlation
- https://endoflife.date/grafana

🟠 **[EOL]** grafana lifecycle: approaching end-of-life (13.1, 13.0) (_analyst=event-correlation, suggested impact=REVIEW_)
2 cycles share one lifecycle story; strongest signal kept at REVIEW.

Evidence: event-correlation
- https://endoflife.date/grafana

🔴 **[EOL]** grafana 12.3 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 12.3 reached EOL on 2026-08-19; no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/grafana

### influxdb

Pulse: lifecycle action

🔴 **[EOL]** influxdb 3.9 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 3.9 reached EOL on 2026-07-30; no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/influxdb

### istio

Pulse: lifecycle action

🟠 **[EOL]** istio lifecycle: approaching end-of-life (1.31, 1.30, 1.29) (_analyst=event-correlation, suggested impact=REVIEW_)
3 cycles share one lifecycle story; strongest signal kept at REVIEW.

Evidence: event-correlation
- https://endoflife.date/istio

🔴 **[EOL]** istio 1.28 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 1.28 reached EOL on 2026-07-01; no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/istio

### keycloak

Pulse: lifecycle action

🔴 **[EOL]** keycloak 26.6 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 26.6 reached EOL on 2026-07-09; no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/keycloak

### kyverno

Pulse: lifecycle action

🔴 **[EOL]** kyverno 1.16 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 1.16 reached EOL on 2026-08-20; no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/kyverno

### mariadb

Pulse: lifecycle action

🟠 **[EOL]** mariadb 13.0 EOL approaching (2026-12-31) (_analyst=change, suggested impact=REVIEW_)
Cycle 13.0 ends in 94 days. Start migration planning now.

Evidence: change
- https://endoflife.date/mariadb

🔴 **[EOL]** mariadb 10.6 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 10.6 reached EOL on 2026-07-06; no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/mariadb

### mongodb

Pulse: lifecycle action

🔴 **[EOL]** mongodb 8.2 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 8.2 reached EOL on 2026-07-31; no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/mongodb

### neo4j

Pulse: activity review, lifecycle action

🔴 **[EOL]** neo4j lifecycle: reached end-of-life (2026.08, 2026.07, 2026.06, 2026.05) (_analyst=event-correlation, suggested impact=ACTION_)
4 cycles share one lifecycle story; strongest signal kept at ACTION.

Evidence: event-correlation
- https://endoflife.date/neo4j

### nodejs

Pulse: lifecycle action

🔴 **[EOL]** nodejs lifecycle: reached end-of-life (3, 2, 1) (_analyst=event-correlation, suggested impact=ACTION_)
3 cycles share one lifecycle story; strongest signal kept at ACTION.

Evidence: event-correlation
- https://endoflife.date/nodejs

### numpy

Pulse: lifecycle action

🟠 **[EOL]** numpy 2.2 EOL approaching (2026-12-09) (_analyst=change, suggested impact=REVIEW_)
Cycle 2.2 ends in 72 days. Start migration planning now.

Evidence: change
- https://endoflife.date/numpy

🔴 **[EOL]** numpy 2.1 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 2.1 reached EOL on 2026-08-19; no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/numpy

### openssl

Pulse: lifecycle action

🟠 **[EOL]** openssl lifecycle: approaching end-of-life (3.6, 3.4) (_analyst=event-correlation, suggested impact=REVIEW_)
2 cycles share one lifecycle story; strongest signal kept at REVIEW.

Evidence: event-correlation
- https://endoflife.date/openssl

🔴 **[EOL]** openssl 3.0 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 3.0 reached EOL on 2026-09-07; no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/openssl

### prometheus

Pulse: lifecycle action

🟠 **[EOL]** prometheus lifecycle: approaching end-of-life (3.15, 3.14) (_analyst=event-correlation, suggested impact=REVIEW_)
2 cycles share one lifecycle story; strongest signal kept at REVIEW.

Evidence: event-correlation
- https://endoflife.date/prometheus

🔴 **[EOL]** prometheus lifecycle: reached end-of-life (3.12, 3.5) (_analyst=event-correlation, suggested impact=ACTION_)
2 cycles share one lifecycle story; strongest signal kept at ACTION.

Evidence: event-correlation
- https://endoflife.date/prometheus

### rabbitmq

Pulse: lifecycle action

🔴 **[EOL]** rabbitmq 4.2 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 4.2 reached EOL on 2026-07-31; no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/rabbitmq

### rust

Pulse: lifecycle action

🔴 **[EOL]** rust lifecycle: reached end-of-life (1.97, 1.96) (_analyst=event-correlation, suggested impact=ACTION_)
2 cycles share one lifecycle story; strongest signal kept at ACTION.

Evidence: event-correlation
- https://endoflife.date/rust

### solr

Pulse: lifecycle action

🔴 **[EOL]** solr lifecycle: reached end-of-life (4, 3, 1) (_analyst=event-correlation, suggested impact=ACTION_)
3 cycles share one lifecycle story; strongest signal kept at ACTION.

Evidence: event-correlation
- https://endoflife.date/solr

### terraform

Pulse: lifecycle action

🔴 **[EOL]** terraform 1.14 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 1.14 reached EOL on 2026-08-26; no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/terraform

### traefik

Pulse: lifecycle action

🟠 **[EOS]** traefik 3.7 ended active support (_analyst=change, suggested impact=REVIEW_)
Active support for cycle 3.7 ended (date not published); only security fixes, if any.

Evidence: change
- https://endoflife.date/traefik

🔴 **[EOL]** traefik lifecycle: reached end-of-life (3.6, 2.11) (_analyst=event-correlation, suggested impact=ACTION_)
2 cycles share one lifecycle story; strongest signal kept at ACTION.

Evidence: event-correlation
- https://endoflife.date/traefik

### vue

Pulse: lifecycle action

🟠 **[EOS]** vue 3.5 ended active support (_analyst=change, suggested impact=REVIEW_)
Active support for cycle 3.5 ended (date not published); only security fixes, if any.

Evidence: change
- https://endoflife.date/vue

🔴 **[EOL]** vue 1 is end-of-life (_analyst=change, suggested impact=ACTION_)
Cycle 1 reached EOL (date not published); no further fixes. Plan upgrade or extended support.

Evidence: change
- https://endoflife.date/vue

## 🟠 Changes to watch (14)

### angular

Pulse: lifecycle action

🟠 **[EOL]** angular 20 EOL approaching (2026-11-28) (_analyst=change, suggested impact=REVIEW_)
Cycle 20 ends in 61 days. Start migration planning now.

Evidence: change
- https://endoflife.date/angular

### consul

Pulse: lifecycle action

🟠 **[EOL]** consul 1.22 EOL approaching (2026-10-31) (_analyst=change, suggested impact=REVIEW_)
Cycle 1.22 ends in 33 days. Start migration planning now.

Evidence: change
- https://endoflife.date/consul

### django

Pulse: lifecycle action

🟠 **[EOS]** django 6.0 ended active support (_analyst=change, suggested impact=REVIEW_)
Active support for cycle 6.0 ended on 2026-08-04; only security fixes, if any.

Evidence: change
- https://endoflife.date/django

### gradle

Pulse: lifecycle action

🟠 **[EOS]** gradle 9 ended active support (_analyst=change, suggested impact=REVIEW_)
Active support for cycle 9 ended (date not published); only security fixes, if any.

Evidence: change
- https://endoflife.date/gradle

### haproxy

Pulse: lifecycle action

🟠 **[EOL]** haproxy 3.3 EOL approaching (2027-01-01) (_analyst=change, suggested impact=REVIEW_)
Cycle 3.3 ends in 95 days. Start migration planning now.

Evidence: change
- https://endoflife.date/haproxy

### kubernetes

Pulse: lifecycle action

🟠 **[EOL]** kubernetes lifecycle: approaching end-of-life (1.35, 1.34) (_analyst=event-correlation, suggested impact=REVIEW_)
2 cycles share one lifecycle story; strongest signal kept at REVIEW.

Evidence: event-correlation
- https://endoflife.date/kubernetes

🟠 **[EOS]** kubernetes 1.34 ended active support (_analyst=change, suggested impact=REVIEW_)
Active support for cycle 1.34 ended on 2026-08-27; only security fixes, if any.

Evidence: change
- https://endoflife.date/kubernetes

### php

Pulse: lifecycle action

🟠 **[EOL]** php 8.2 EOL approaching (2026-12-31) (_analyst=change, suggested impact=REVIEW_)
Cycle 8.2 ends in 94 days. Start migration planning now.

Evidence: change
- https://endoflife.date/php

### postgresql

Pulse: lifecycle action

🟠 **[EOL]** postgresql 14 EOL approaching (2026-11-12) (_analyst=change, suggested impact=REVIEW_)
Cycle 14 ends in 45 days. Start migration planning now.

Evidence: change
- https://endoflife.date/postgresql

### react

Pulse: lifecycle review

🟠 **[EOS]** react 19 ended active support (_analyst=change, suggested impact=REVIEW_)
Active support for cycle 19 ended (date not published); only security fixes, if any.

Evidence: change
- https://endoflife.date/react

### redis

Pulse: lifecycle action

🟠 **[EOS]** redis lifecycle: ended active support (8.10, 8.8) (_analyst=event-correlation, suggested impact=REVIEW_)
2 cycles share one lifecycle story; strongest signal kept at REVIEW.

Evidence: event-correlation
- https://endoflife.date/redis

🟠 **[EOL]** redis 8.0 EOL approaching (2026-12-01) (_analyst=change, suggested impact=REVIEW_)
Cycle 8.0 ends in 64 days. Start migration planning now.

Evidence: change
- https://endoflife.date/redis

### spark

Pulse: lifecycle action

🟠 **[EOL]** apache-spark 4.0 EOL approaching (2026-11-23) (_analyst=change, suggested impact=REVIEW_)
Cycle 4.0 ends in 56 days. Start migration planning now.

Evidence: change
- https://endoflife.date/apache-spark

### spring-boot

Pulse: lifecycle action

🟠 **[EOL]** spring-boot 4.0 EOL approaching (2026-12-31) (_analyst=change, suggested impact=REVIEW_)
Cycle 4.0 ends in 94 days. Start migration planning now.

Evidence: change
- https://endoflife.date/spring-boot

### vitess

Pulse: lifecycle action

🟠 **[EOL]** vitess 23 EOL approaching (2026-11-04) (_analyst=change, suggested impact=REVIEW_)
Cycle 23 ends in 37 days. Start migration planning now.

Evidence: change
- https://endoflife.date/vitess

### zookeeper

Pulse: lifecycle action

🟠 **[EOS]** zookeeper lifecycle: ended active support (3.9, 3.8) (_analyst=event-correlation, suggested impact=REVIEW_)
2 cycles share one lifecycle story; strongest signal kept at REVIEW.

Evidence: event-correlation
- https://endoflife.date/zookeeper

## Notes

- Collectors: endoflife.date, GitHub releases + repo metadata, NVD, CISA KEV, Docker Hub.
- GitHub calls authenticated (5000 req/hr budget).
- NVD queried without API key (5 req/30s); misses degrade to gaps, not findings.
- Keyword-associated CVE records without identity evidence are held back, not narrated.

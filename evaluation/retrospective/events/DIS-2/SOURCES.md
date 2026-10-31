# DIS-2: Official openjdk image deprecated (no non-EA updates after July 2022)

Class: distribution. Project slug: `openjdk`.

| Source | Primary URL | Archived as | Fetched at |
|---|---|---|---|
| docker-library/docs@326814f | https://github.com/docker-library/docs/commit/326814f7acbd | record:github commit 326814f7acbd (openjdk deprecation notice) | 2022-06-10T00:00:00+00:00 |
| docker-library/openjdk#505 | https://github.com/docker-library/openjdk/issues/505 | wayback:20220718201219 http://web.archive.org/web/20220718201219/https://github.com/docker-library/openjdk/issues/505 | 2022-07-18T20:12:19+00:00 |

## Representation (RQ-R2)

GAP: 'all tags except Early Access' cannot be stated: the <version> predicate also matches EA tags (19-ea-5-jdk) and misses non-version tags (latest, jre). The repository element (every tag) is used, so EA tags will be positives by construction.

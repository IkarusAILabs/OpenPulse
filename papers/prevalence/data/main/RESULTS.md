# Results

Source: `data/main/measures.jsonl`, 6000 packages.

## Coverage of the measure

| Ecosystem | Stratum | Sampled | Excluded (no GitHub repository published) | Measured | GitHub error |
| --- | --- | --- | --- | --- | --- |
| go | tail | 1000 | 37 | 963 | 0 |
| go | top | 1000 | 35 | 965 | 0 |
| npm | tail | 1000 | 26 | 974 | 0 |
| npm | top | 1000 | 7 | 993 | 0 |
| pypi | tail | 1000 | 160 | 840 | 0 |
| pypi | top | 1000 | 113 | 887 | 0 |

## RQ1: Prevalence (share of measured packages, Wilson 95% interval)

| Ecosystem | Stratum | Archived | Relocated | Unreachable | Any of the three |
|---|---|---|---|---|---|
| go | tail | 113/963 (11.7%, 9.9–13.9) | 91/963 (9.4%, 7.8–11.5) | 24/963 (2.5%, 1.7–3.7) | 207/963 (21.5%, 19.0–24.2) |
| go | top | 106/965 (11.0%, 9.2–13.1) | 40/965 (4.1%, 3.1–5.6) | 4/965 (0.4%, 0.2–1.1) | 140/965 (14.5%, 12.4–16.9) |
| npm | tail | 96/974 (9.9%, 8.1–11.9) | 81/974 (8.3%, 6.7–10.2) | 20/974 (2.1%, 1.3–3.2) | 175/974 (18.0%, 15.7–20.5) |
| npm | top | 47/993 (4.7%, 3.6–6.2) | 40/993 (4.0%, 3.0–5.4) | 4/993 (0.4%, 0.2–1.0) | 86/993 (8.7%, 7.1–10.6) |
| pypi | tail | 77/840 (9.2%, 7.4–11.3) | 66/840 (7.9%, 6.2–9.9) | 19/840 (2.3%, 1.5–3.5) | 144/840 (17.1%, 14.7–19.8) |
| pypi | top | 55/887 (6.2%, 4.8–8.0) | 31/887 (3.5%, 2.5–4.9) | 1/887 (0.1%, 0.0–0.6) | 78/887 (8.8%, 7.1–10.8) |

Per distinct repository (packages sharing a repository counted once):

| Ecosystem | Stratum | Repositories | Archived | Relocated | Unreachable |
|---|---|---|---|---|---|
| go | tail | 922 | 112/922 (12.1%, 10.2–14.4) | 90/922 (9.8%, 8.0–11.8) | 24/922 (2.6%, 1.8–3.8) |
| go | top | 856 | 93/856 (10.9%, 9.0–13.1) | 39/856 (4.6%, 3.4–6.2) | 4/856 (0.5%, 0.2–1.2) |
| npm | tail | 841 | 93/841 (11.1%, 9.1–13.4) | 72/841 (8.6%, 6.9–10.6) | 20/841 (2.4%, 1.5–3.6) |
| npm | top | 662 | 46/662 (6.9%, 5.2–9.1) | 32/662 (4.8%, 3.4–6.7) | 4/662 (0.6%, 0.2–1.5) |
| pypi | tail | 807 | 77/807 (9.5%, 7.7–11.8) | 66/807 (8.2%, 6.5–10.3) | 19/807 (2.4%, 1.5–3.6) |
| pypi | top | 855 | 53/855 (6.2%, 4.8–8.0) | 31/855 (3.6%, 2.6–5.1) | 1/855 (0.1%, 0.0–0.7) |

## RQ2: Exposure of affected packages

Dependent counts overlap across packages; they are not summed.

| Ecosystem | Stratum | State | Packages | Median dependent repos | Max dependent repos | Median dependent packages |
| --- | --- | --- | --- | --- | --- | --- |
| go | tail | archived | 113 | 43 | 5,697 | 31 |
| go | tail | relocated | 91 | 28 | 2,527 | 24 |
| go | tail | unreachable | 24 | 16 | 364 | 12 |
| go | top | archived | 106 | 20,469 | 247,600 | 3,606 |
| go | top | relocated | 40 | 18,829 | 123,694 | 3,315 |
| go | top | unreachable | 4 | 10,897 | 20,257 | 2,662 |
| npm | tail | archived | 96 | 7,036 | 810,914 | 73 |
| npm | tail | relocated | 81 | 5,106 | 968,234 | 53 |
| npm | tail | unreachable | 20 | 5,260 | 140,228 | 25 |
| npm | top | archived | 47 | 2,132,693 | 4,404,245 | 955 |
| npm | top | relocated | 40 | 1,901,495 | 4,404,245 | 1,200 |
| npm | top | unreachable | 4 | 2,237,260 | 2,311,479 | 1,238 |
| pypi | tail | archived | 77 | 49 | 2,240 | 2 |
| pypi | tail | relocated | 66 | 44 | 1,658 | 2 |
| pypi | tail | unreachable | 19 | 92 | 662 | 0 |
| pypi | top | archived | 55 | 9,394 | 75,321 | 92 |
| pypi | top | relocated | 31 | 7,185 | 96,320 | 99 |
| pypi | top | unreachable | 1 | 34,507 | 34,507 | 59 |

## RQ3: Signal coverage of archived or unreachable packages

| Ecosystem | Stratum | State | Packages | Registry deprecation | Advisory (OSV) | Lifecycle (endoflife.date) | Any signal |
| --- | --- | --- | --- | --- | --- | --- | --- |
| go | tail | archived | 113 | 3/113 (2.7%, 0.9–7.5) | 0/113 (0.0%, 0.0–3.3) | 1/113 (0.9%, 0.2–4.8) | 4/113 (3.5%, 1.4–8.7) |
| go | tail | unreachable | 24 | 0/24 (0.0%, 0.0–13.8) | 0/24 (0.0%, 0.0–13.8) | 1/24 (4.2%, 0.7–20.2) | 1/24 (4.2%, 0.7–20.2) |
| go | top | archived | 106 | 13/106 (12.3%, 7.3–19.9) | 1/106 (0.9%, 0.2–5.2) | 1/106 (0.9%, 0.2–5.2) | 15/106 (14.2%, 8.8–22.0) |
| go | top | unreachable | 4 | 0/4 (0.0%, 0.0–49.0) | 0/4 (0.0%, 0.0–49.0) | 0/4 (0.0%, 0.0–49.0) | 0/4 (0.0%, 0.0–49.0) |
| npm | tail | archived | 96 | 27/96 (28.1%, 20.1–37.8) | 0/96 (0.0%, 0.0–3.8) | 0/96 (0.0%, 0.0–3.8) | 27/96 (28.1%, 20.1–37.8) |
| npm | tail | unreachable | 20 | 4/20 (20.0%, 8.1–41.6) | 0/20 (0.0%, 0.0–16.1) | 0/20 (0.0%, 0.0–16.1) | 4/20 (20.0%, 8.1–41.6) |
| npm | top | archived | 47 | 22/47 (46.8%, 33.3–60.8) | 0/47 (0.0%, 0.0–7.6) | 0/47 (0.0%, 0.0–7.6) | 22/47 (46.8%, 33.3–60.8) |
| npm | top | unreachable | 4 | 0/4 (0.0%, 0.0–49.0) | 0/4 (0.0%, 0.0–49.0) | 0/4 (0.0%, 0.0–49.0) | 0/4 (0.0%, 0.0–49.0) |
| pypi | tail | archived | 77 | 5/77 (6.5%, 2.8–14.3) | 0/77 (0.0%, 0.0–4.8) | 0/77 (0.0%, 0.0–4.8) | 5/77 (6.5%, 2.8–14.3) |
| pypi | tail | unreachable | 19 | 0/19 (0.0%, 0.0–16.8) | 0/19 (0.0%, 0.0–16.8) | 0/19 (0.0%, 0.0–16.8) | 0/19 (0.0%, 0.0–16.8) |
| pypi | top | archived | 55 | 4/55 (7.3%, 2.9–17.3) | 1/55 (1.8%, 0.3–9.6) | 1/55 (1.8%, 0.3–9.6) | 5/55 (9.1%, 3.9–19.6) |
| pypi | top | unreachable | 1 | 0/1 (0.0%, 0.0–79.3) | 0/1 (0.0%, 0.0–79.3) | 0/1 (0.0%, 0.0–79.3) | 0/1 (0.0%, 0.0–79.3) |

## RQ4: Stale references among renamed repositories

Denominator: measured packages whose repository has a recorded earlier name
(ecosyste.ms `previous_names`). Numerator: the published repository redirects
(relocated).

| Ecosystem | Stratum | Renamed | Published name is stale | Relocated without a recorded rename | Examples (published → current) |
| --- | --- | --- | --- | --- | --- |
| go | tail | 232 | 74/232 (31.9%, 26.2–38.1) | 17 | `kubernetes/heapster` → `kubernetes-retired/heapster`; `coreos/prometheus-operator` → `prometheus-operator/prometheus-operator`; `hajimehoshi/oto` → `ebitengine/oto` |
| go | top | 196 | 35/196 (17.9%, 13.1–23.8) | 5 | `envoyproxy/protoc-gen-validate` → `bufbuild/protoc-gen-validate`; `smartystreets/assertions` → `smarty/assertions`; `jtolds/gls` → `jtolio/gls` |
| npm | tail | 364 | 75/364 (20.6%, 16.8–25.1) | 6 | `jonschlinkert/posix-character-classes` → `micromatch/posix-character-classes`; `sindresorhus/pkg-up` → `sindresorhus/package-up`; `crypto-browserify/browserify-cipher` → `browserify/browserify-cipher` |
| npm | top | 498 | 39/498 (7.8%, 5.8–10.5) | 1 | `facebook/regenerator` → `meta/regenerator`; `visionmedia/node-cookie-signature` → `tj/node-cookie-signature`; `TrySound/postcss-value-parser` → `postcss/postcss-value-parser` |
| pypi | tail | 176 | 59/176 (33.5%, 27.0–40.8) | 7 | `williamFalcon/test_tube` → `williamFalcon/test-tube`; `technige/py2neo` → `neo4j-contrib/py2neo`; `pytorch/fairseq` → `facebookresearch/fairseq` |
| pypi | top | 291 | 31/291 (10.7%, 7.6–14.7) | 0 | `pickleshare/pickleshare` → `ipython/pickleshare`; `jazzband/dj-database-url` → `django-commons/dj-database-url`; `aio-libs/async-timeout` → `aio-libs-abandoned/async-timeout` |

## Archived packages released after the repository's last push (PROTOCOL.md §5 proxy)

| Ecosystem | Stratum | Archived | Release after last push | No release time |
|---|---|---|---|---|
| go | tail | 113 | 1 | 0 |
| go | top | 106 | 0 | 0 |
| npm | tail | 96 | 13 | 0 |
| npm | top | 47 | 7 | 0 |
| pypi | tail | 77 | 10 | 0 |
| pypi | top | 55 | 4 | 0 |

## Validation: frame against source

ecosyste.ms `archived` agrees with the GitHub measurement on 5509/5531 (99.6%, 99.4–99.7) packages where both exist.


# Applicability specification: the independent-oracle edition

This is the decision model of TR-2026-01 (§5.2–5.4, Tables 6 and 8, conditions N1–N5), restated so that it can be implemented without reading any OpenPulse code. It covers exactly the cases the kit's case format can express (README, "Case format"). Where the report is informal, this text gives the definition that the team's oracle and the implementation both use. **Say so if you think a definition is wrong**: that is half of the job.

Section numbers in brackets point to TR-2026-01.

## 1. Inputs

A **case** is one dependency `d` and a list of one or more **events**.

**Dependency `d`:** either

- an **image reference** (`ref`): a container image, or a source-repository location such as `github.com/owner/repo`; or
- a **package** (`package` name, optional `version`).

It also carries `belongs_to`: the project that a *curated, reviewed* mapping assigns it to, or `null` when no curated mapping exists. Identity is an input, not something you resolve. Relative to an event of project `p`, the identity of `d` is:

| `belongs_to` | identity relative to `p` |
|---|---|
| `p` | **project** |
| another project | **other** |
| `null` | **unresolved** |

**Event `e`:**

- `project`: the project the event is about;
- `scope`: either `null` (a project-wide event) or one **scope kind** with a list of values. The kinds are `artifact`, `release_line`, `package` and `registry`;
- `named`: references the event names as affected examples. These illustrate the change; they never bound it;
- `completeness`: `partial` or `declared`, and `basis`: `null` or one of `definitional`, `announced`, `corroborated`, `verified`;
- `admissibility`: `current`, `withdrawn`, `superseded`, `contested` (the event's own evidence contradicts it) or `stale` (its newest evidence is older than the consumer's freshness bound).

## 2. Elements

An event's element set `E` is:

- one `artifact` element per `named` reference, marked **example**;
- if `scope` is `null`: one `project` element for `e.project`;
- otherwise one element of the scope kind per value.

`E` can be empty only if `scope` is non-null with no values. This does not occur in kit cases.

Each element has a **role** [§5.2]:

- an `artifact` element whose name is `*` (a namespace) and that has no tag is an **envelope**;
- a `registry` element is always an **envelope**;
- every other element is **exact**.

An envelope may justify an exclusion but never a positive.

## 3. Reference canonical form [§6, D9, D12]

Parse a reference string as follows. Identity parts are canonicalised; the tag and digest keep their exact spelling.

1. Strip one leading scheme, if present: `oci://`, `docker://`, `https://`, `http://` (case-insensitive).
2. If the string contains `@`, split at the first `@`. The right side is the **digest**, kept verbatim.
3. Split the rest at its last `/`. In the last segment, a `:` separates the name from the **tag**, kept verbatim. A colon in an earlier segment is never a tag: it is a registry port.
4. Split the path into segments. If there is more than one segment, and the first contains `.` or `:` or equals `localhost`, the first segment is the **registry**. Otherwise the registry is `docker.io`, and all segments are the repository path.
5. `index.docker.io` and `registry-1.docker.io` are `docker.io`.
6. If one repository segment remains, the namespace is `library` on `docker.io` and empty elsewhere. Otherwise the namespace is every segment but the last (joined by `/`), and the name is the last segment.
7. Lowercase the registry, namespace and name.

So `redis`, `docker.io/redis` and `index.docker.io/library/redis` are the same repository: `docker.io/library/redis`. `docker.io/bitnami/*` is a namespace element (its name is `*`).

A reference with neither tag nor digest has the **effective tag** `latest`. A reference that pins only a digest has no effective tag: its tag is unknown.

**Tag predicates** [§5.2]: an element may carry the tag `<version>` (every version-like tag) or `*` (every tag) in place of a literal tag.

A tag is **version-like** when the whole tag matches this grammar (case-insensitive):

- an optional `v`;
- one or more dot-separated runs of digits;
- optionally one pre-release marker, optionally preceded by `-`, `.` or `_`. The markers are `dev`, `alpha`, `a`, `beta`, `b`, `rc`, `c`, `preview` and `pre`, each optionally followed by digits;
- optionally a variant suffix: `-`, then a letter, then any letters, digits, `.`, `_` or `-`.

`1.25`, `7.2.4-debian-12-r3`, `v3.5.0` and `1.0rc1` are version-like. `latest` and `alpine` are not.

The **release** of a version is its leading dotted-digit run, after an optional `v`. The rest is ignored: `13.16-alpine` has release `13.16`. Version `v` is **in** release line `l` when the release of `l` is a prefix of the release of `v`, compared numerically component by component. So `4.2` covers `4.2.11` but not `4.20.1`. If either release cannot be read, the comparison is undetermined.

## 4. Membership tests [§5.3]

Each test `t(d, x)` returns one of:

| Result | Meaning |
|---|---|
| **M** | member |
| **N** | decisively excluded |
| **?** | undetermined |
| **P** | project tie |
| **0** | no association |

### 4.1 Across reference kinds (S2, S3)

When `d` and an element are of different kinds, the element-specific rules below do not apply. The result is:

- **0** if `d`'s identity is *other*: a curated mapping to another project is positive evidence of no association;
- **0** if `d` is a package whose identity is *unresolved*, and the element cannot name the same object. A package is never a container image, an image object, or a registry location;
- **?** otherwise.

A package *may* be the same object as a source-repository element (one on `github.com`, `gitlab.com` or `bitbucket.org`): a Go module path names its repository.

### 4.2 `artifact` element `x`

**If `d` is a package:**

- if `x` is an example, the result is **0** (an example illustrates an image event, never a package's);
- otherwise apply §4.1, where "may be the same object" means `x`'s registry is a source host.

**If `d` is an image reference**, let `D` and `X` be the parsed references.

- **Namespace element** (`X` has name `*`):
  - **N** if `D`'s (registry, namespace) differs from `X`'s;
  - else **?** if `x` is an envelope (no tag);
  - else apply the tag test below.
- **Different repository** (registry, namespace or name differ): **0** if `x` is an example (S4: an example never bounds), else **N**.
- **Object element** (`X` has a digest):
  - **?** if `D` pins no digest (a tag can move onto the digest);
  - **M** if the digests are equal;
  - **?** otherwise (object levels are not compared, so unequal digests are undetermined).
- **Repository element** (`X` has no tag): **M**, whatever `D`'s tag or digest.
- **Otherwise**, the tag test:
  - predicate `*`: **M**;
  - if `D` has no effective tag (digest only): **?**;
  - predicate `<version>`: **M** if `D`'s effective tag is version-like, else **N**;
  - literal tag: **M** if equal (exact spelling), else **N**;
  - an **N** from the tag test on an *example* becomes **?**: a named tag establishes that tag, not the repository's others.

### 4.3 `release_line` element `x` (value: a release line)

- **0** if identity is *other*.
- **?** if identity is *unresolved*.
- If `d` is an image: **?** unless its effective tag is version-like. Otherwise the version is that tag.
- If `d` is a package: **?** if it has no version.
- Then **M** if the version is in the line, **N** if not, and **?** if the comparison is undetermined.

### 4.4 `package` element `x` (value: a package name)

- If `d` is an image: apply §4.1. A package element cannot name the same object as an image.
- If `d`'s package name equals `x` (case-insensitive): **M**.
- Otherwise **0** if identity is *other*, else **?**. Names are not canonicalised per ecosystem, so inequality alone never excludes.

### 4.5 `registry` element `x` (value: a registry host)

- If `d` is a package: apply §4.1. It can never be the same object.
- If `d`'s registry equals `x`: **?**, since a registry element is an envelope.
- Otherwise **N**.

### 4.6 `project` element

**P** if identity is *project*, **0** if *other*, **?** if *unresolved*. Failure to establish identity is never evidence of non-identity (N2).

## 5. Per-event decision [Algorithm 1]

Layer 1 decides whether the event is evaluated at all:

- a `withdrawn` or `superseded` event is not evaluated. Its result is **UNLOADED**;
- a `contested` or `stale` event *is* evaluated, but it may never clear (S1). Layer 1 restricts negatives only; it never changes a positive.

Layer 2 evaluates **every** element, with no early return: `T = { t(d, x) : x ∈ E }`.

Layer 3 takes the first rule that applies:

1. **M** ∈ T → **AFFECTS**.
2. **?** ∈ T → **RELATED**.
3. **N** ∈ T →
   - **NOT_AFFECTED** only if T ⊆ {N, 0}, completeness is `declared` with a non-null basis, and the event is neither contested nor stale;
   - otherwise **RELATED**. Exclusion from a scope not known to be complete is never a clearance.
4. **P** ∈ T → **AFFECTS_PROJECT**.
5. Otherwise (T ⊆ {0}) → **UNKNOWN**.

## 6. Cross-event summary [Table 8]

Ignore UNLOADED results. Then the summary is:

1. **affected** if any event gives AFFECTS;
2. otherwise **unresolved** if any gives RELATED or AFFECTS_PROJECT;
3. otherwise **cleared** if any gives NOT_AFFECTED;
4. otherwise **no association**, including when no event remains.

A clearance never headlines over an unresolved association, whatever the order or number of events.

## 7. What a result means [Table 6]

| Result | Means | Does not mean |
|---|---|---|
| AFFECTS | `d` is in the event's directly named scope | broken, unsafe, unmaintained |
| NOT_AFFECTED | `d` is outside the directly named scope, which is declared complete | safe; unaffected by embedded components, other events, or consequences |
| RELATED | an association exists but is not established | either of the above |
| AFFECTS_PROJECT | `d` belongs to the event's project; scope membership is not established | |
| UNKNOWN | no association was found | safe |

## 8. Known open points

These are recorded, not hidden. Challenge any of them:

- Elements of more than one kind in one event's scope are specified [§5.2], but the case format and the implementation carry one kind per event.
- OCI object levels (index, manifest, layer) are not compared. Unequal digests are therefore **?**.
- The version-like grammar and the release-prefix rule are generic. They are not any ecosystem's own ordering.
- Package names are not canonicalised (PEP 503, Maven group/artifact, npm scopes), hence §4.4's **?** on inequality.
- A `verified` completeness state is defined, but nothing produces it. A `declared` scope is a producer's assertion, admitted here when it has a basis.

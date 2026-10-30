# Encoding rules for policy R (OSV and OpenVEX)

**Status: drafted 2026-10-30 with the registration amendments; frozen when [`REGISTRATION.md`](../REGISTRATION.md) is archived.** After archiving, any change to these rules is a registration amendment (REGISTRATION §11).

Policy R (REGISTRATION §2) asks what TR-2026-01's model adds over formats that already exist, read with care. Each held-out event is re-encoded **from its primary sources alone** as an OSV record or as OpenVEX statements. A careful conservative consumer, `evaluation/existing_representation.py`, then reads the encoding. These rules fix how an event becomes an encoding, so that R depends on the formats and on the rules, and not on the encoder's judgement.

## 1. The encoder

- The encoder is a person, not an annotator for the same events. The encoder sees no label and no policy's output, and finishes every encoding before any policy runs (REGISTRATION §10).
- The encoder works from this document and the event's primary sources. Nothing else is used:
  - not OpenPulse's typed scope, its curated catalogue, or its affected-artefact list;
  - not another event's encoding;
  - not a search for products the sources do not name.
- Budget: 15–25 minutes per event (REGISTRATION §6). An event the encoder cannot finish in 45 minutes is encoded as far as possible, and the gap is recorded as loss (§7, code L7).

## 2. Inputs

The event's **primary sources** are the sources its fixture cites as evidence, as acquired on or before the event's first-observation date:
- the vendor's, maintainer's or registry's own statement;
- recorded registry or repository observations (repository metadata, registry listings);
- a release-cycle feed (such as endoflife.date) only where the fixture cites it.

The encoder reads each source's recorded excerpt and, where the excerpt is not enough, the archived source at its acquisition date. Nothing published after the first-observation date is read.

## 3. Which format

### 3.1 By subject

| What the source says changed | Encoding |
|---|---|
| Versions, or all versions, of a **package in an OSV ecosystem**: PyPI, npm, Go, Maven | an **OSV record** (§5) |
| **Container images** (a repository, a tag, a digest) | **OpenVEX statements** (§6) |
| **Source repositories** (relocation, archival) | **OpenVEX statements** |
| **Distributions** (charts, images or tags withdrawn or moved) | **OpenVEX statements** |
| Anything else (a server's release line with no named package or image, a product by name) | nothing expressible: an empty encoding, with its loss recorded (§7) |

One event may need both: an OSV record for its packages and OpenVEX statements for its images. A subject that fits neither format is never forced into one.

### 3.2 What may be encoded

- Encode **only the products the sources name**: a package by its ecosystem and name, an image by its reference, a repository by its path. Never add a product because it seems related, because it belongs to the same project, or because it is a well-known alias.
- A product named only by a class or a prefix ("every image under `docker.io/bitnami`", "all `com.itextpdf` modules") is not a named product. Record it as loss (L1, L4), and encode nothing for it.
- A status needs the source's own words:
  - **`affected`**: the source puts the product within the change;
  - **`not_affected`**: the source puts the product outside the change, explicitly: an exclusion, a relocation's destination, or a replacement the source says continues unchanged;
  - **`under_investigation`**: the source names the product but leaves its status open.
- The source's silence is never a status. A product the sources do not mention gets no statement.

## 4. Purls (shared with the consumer)

The consumer compares purls by **exact string equality**. The encoder and the consumer build them by the same rule (`existing_representation.dependency_purl` and `_package_key`):

| Product | purl |
|---|---|
| PyPI package | `pkg:pypi/<name>@<version>`, name normalised per PEP 503 (lowercase, runs of `-_.` become `-`) |
| npm package | `pkg:npm/<name>@<version>`, lowercase; a scope's `@` is written `%40` |
| Maven artifact | `pkg:maven/<groupId>/<artifactId>@<version>`, lowercase |
| Go module | `pkg:golang/<module path>@<version>`, lowercase |
| Container image | `pkg:docker/<namespace>/<name>@<tag or digest>`, after the specification's canonicalisation: Docker Hub hosts fold to `docker.io`, a single name gets the namespace `library`, and an untagged reference is `latest`. A registry other than `docker.io` is the qualifier `?repository_url=<registry>`. A digest's `:` is written `%3A`. |
| Repository on github.com, gitlab.com, bitbucket.org | `pkg:github/<owner>/<repo>` (or `gitlab`, `bitbucket`), lowercase, no version |

OSV identifies a package by `ecosystem` and `name`. The consumer turns that pair into the versionless purl above, and ignores the record's own `purl` field, so a record cannot match by a purl that disagrees with its name.

A statement's product purl must carry the version or tag the source names. A versionless image purl matches only a dependency that has no tag, which does not occur after canonicalisation, so an image without a named tag cannot be stated: record L2.

## 5. OSV records

### 5.1 Record

- `schema_version` `1.6.0`; `id` `OPENPULSE-EVAL-<event name>`; `modified` the first-observation date; `summary` one line in the encoder's words.
- One `affected` entry per named package, with `package.ecosystem` (`PyPI`, `npm`, `Go`, `Maven`) and `package.name` as the source writes it.
- `database_specific` and `ecosystem_specific` may carry notes. The consumer never reads them, so nothing that decides membership may live there.

### 5.2 Ranges

- **Type.** `ECOSYSTEM` for PyPI and Maven; `SEMVER` for npm and Go. `GIT` ranges are never written: the consumer cannot evaluate them against a released version.
- **Order.** Events are listed in ascending version order, as `introduced` / `fixed` pairs, or with a final `last_affected` when the source names the last affected version.
- **All versions.** `introduced: "0"` and no upper bound.
- **Exact versions** the source lists, and nothing else: the `versions` array.

### 5.3 Release lines

A source that names a release line ("Django 4.2", "React 18") covers every version in that line, pre-releases included: the specification's rule, which V and C also apply. The line becomes one range from the lowest version in the line to the lowest version in the next line:

| Ecosystem | Line `X.Y` (or `X`) | Range |
|---|---|---|
| PyPI | `4.2` | `introduced: "4.2.dev0"`, `fixed: "4.3.dev0"` |
| npm, Go | `18` | `introduced: "18.0.0-0"`, `fixed: "19.0.0-0"` |
| Maven | `8.0` | `introduced: "8.0-alpha"`, `fixed: "8.1-alpha"`, and record L5 (no qualifier is lower than every other) |

The next line is the next number at the line's last position (`4.2` → `4.3`, `18` → `19`), even when that line was never released.

## 6. OpenVEX statements

- One OpenVEX v0.2.0 document per event: `@context` `https://openvex.dev/ns/v0.2.0`, an `@id`, `author` (the encoder), `timestamp` (the first-observation date), `version` 1.
- The `vulnerability` of each statement is the change event: `name` the event's name, and `description` the change in one line. OpenVEX was designed for vulnerabilities; using it for other changes is part of what R tests.
- `products` is a list of `{"@id": <purl>}` built per §4. Subcomponents are not used.
- `status` is one of `affected`, `not_affected`, `under_investigation`, chosen per §3.2.
  - `affected` carries an `action_statement` where the source gives one.
  - `not_affected` carries an `impact_statement` quoting or paraphrasing the source's reason. OpenVEX's `justification` labels are written for vulnerable code, and are used only when one fits literally.
- An event with nothing to state still gets a document with an empty `statements` list, and its loss recorded.

## 7. Encoding loss

For each event, the encoder records what the formats could not express, as a list of entries: `code`, `what` (one sentence), `source` (the URL that states it). An event's loss is empty only if the encoding carries everything the sources say about who is affected and who is not.

| Code | Loss |
|---|---|
| **L1** | A **namespace or prefix** scope: every image under a namespace, every package under a group. |
| **L2** | A **tag or version class** that is not a range in an OSV ecosystem: "every versioned tag", "latest only", an image tag line. |
| **L3** | **Completeness**: the source states that its list is closed, or that its scope is definitional, and the encoding cannot carry that (OpenVEX statements cannot say that unlisted products are unaffected). An OSV range is closed for its own package, so L3 never applies to it. |
| **L4** | **Identity**: the source names a product or project, not a package, image or repository that has a purl. |
| **L5** | **Version semantics**: a boundary the ecosystem's comparator cannot place exactly (Maven qualifiers, variant tag suffixes). |
| **L6** | **No format**: the subject has no OSV ecosystem and no product purl at all (a server's release line distributed as images the source does not name). |
| **L7** | **Other**, described in full, including an encoding left unfinished (§1). |

Loss is recorded per event in the encoding, and reported per event and per event class. R's results are also reported on the events with no loss (REGISTRATION §4).

## 8. File format

One JSON file per event, `representations/<dataset>/<event name>.json`:

```json
{
  "event": "<event name in the case set>",
  "encoder": "<name or pseudonymous ID>",
  "encoded_on": "YYYY-MM-DD",
  "sources": ["<primary source URL>", "..."],
  "osv": [ <OSV record>, ... ],
  "openvex": <OpenVEX document or null>,
  "loss": [ {"code": "L1", "what": "...", "source": "<URL>"} ],
  "notes": "<optional free text, never read by the consumer>"
}
```

`existing_representation.validate_encoding` enforces the structure: a primary source, supported OSV ecosystems and range types, OpenVEX statuses from §3.2, purl products, a reason on every `not_affected`, and a code and description on every loss entry.

## 9. Freezing

- In the case set, each event names its encoding and the file's SHA-256:

  ```json
  "encoding": {"file": "representations/<dataset>/<event>.json", "sha256": "<hex>"}
  ```

- `run.py` verifies the hash before any policy runs, and refuses a mismatch or a malformed encoding. The registered run (`--require-encodings`) also refuses an event with no encoding.
- The files are stored byte for byte (`.gitattributes`: `-text`), so the hash holds on every platform.
- Encodings are frozen before any policy runs on the held-out set, and never revised after a result is seen. A correction found later is reported as a separate run, as for implementation defects (REGISTRATION §10).

## 10. What the consumer does

For reference; `evaluation/existing_representation.py` is authoritative.

- **Identity:** the dependency's purl (§4), compared exactly.
- **OSV:** for an `affected` entry whose package equals the dependency's, the version is affected if it is in `versions` or inside a range under the pinned comparator. It is not affected if every range decides it outside. A range the comparator cannot decide, or a dependency without a version, is unresolved. Withdrawn records are ignored.
- **OpenVEX:** a statement naming the dependency's exact purl gives its status: `affected` is affected, `not_affected` is not affected, anything else is unresolved.
- **Per event:** affected over unresolved over not affected; an event whose encoding says nothing about the dependency, or that has no encoding, is unresolved.
- **Across events:** as V and C (TR-2026-01 Table 8): affected, then unresolved, then not affected; no current event is no association.

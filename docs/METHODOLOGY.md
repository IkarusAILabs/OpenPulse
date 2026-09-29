# Methodology — how OpenPulse knows what it claims (schema v0.4.0)

## Sources

Upstream: GitHub releases + repo metadata, official blogs/changelogs.
Security: OSV.dev, NVD, MITRE CVE, CISA KEV, GitHub Advisories,
Exploit-DB (link only). Lifecycle: endoflife.date. Ecosystems: Maven,
npm, PyPI, Docker/OCI (initial).

## Source authority tiers

Sources are not equal. Tiers, strongest first:

- **official** — the vendor/project itself (announcement, changelog,
  advisory, repo). Alone sufficient for CONFIRMED.
- **primary** — lifecycle databases (endoflife.date), registries
  serving protocol truth (tag lists, digests). Strong but narrow:
  endoflife.date proves dates, never distribution intent.
- **secondary** — reputable press, mirrors, aggregators. Corroborates;
  never confirms alone.
- **tertiary** — rumors, single discussions. Context at most.

endoflife.date is a primary lifecycle source — one input among many,
not the definition of OpenPulse. A lifecycle database answers "when
does software reach EOL"; OpenPulse answers "what is changing upstream,
and does it affect what I depend on".

## Identity hierarchy

`docker.io/redis` ≠ `docker.io/bitnami/redis`, always. Resolution
order: curated overrides → catalog aliases → Bitnami-namespace rule →
normalized fallback (`core/entities/resolve.py`). Typed identity refs
(`core/entities/identity.py`: project, package, artifact, repository,
registry_artifact, purl, cpe) record *why* two names were treated as
the same thing. Same identity evidence = same thing; same name is
never enough.

## Vulnerability correlation methodology

NVD `keywordSearch` is **discovery**, never applicability. Findings
carry `relationship` + `match_method` + `identity_evidence`:

- `osv_package` — OSV query scope (package/ecosystem identity).
- `osv_package+version_range` / `cpe_version_range` — plus an evaluated
  version range → `AFFECTS_VERSION`.
- `cpe_vendor_product` — normalized exact product equality only.
  Token overlap (`spring` vs `spring-shell`) is NOT identity.
- `keyword_only` — capped at `REVIEW`, never `AFFECTS_VERSION/_ARTIFACT`.
- KEV `exact`/`strong` sets `in_kev`; `weak` never does. KEV +
  uncertain applicability → `REVIEW`, never `CRITICAL`.

## Version applicability

`core/versions.py` evaluates OSV events
(introduced/fixed/last_affected) and NVD CPE range attributes
(versionStart/EndIncluding/Excluding) plus exact versions. Result is
`True`/`False`/`None` — `None` (unknown version, exotic scheme) keeps
the ceiling at `AFFECTS_PACKAGE` or `RELATED`. Uncertainty never
strengthens a conclusion.

## Evidence, claims, independence

Every claim names supporting evidence (`Claim.evidence_refs`); an
official-but-unrelated source never satisfies a claim. Corroboration
counts independent families, folding `derived_from` chains.
Contradicting evidence stays visible (`⚠️ CONTRADICTS`); unresolved
conflict blocks `ACTION`/`CRITICAL`. High-impact conclusions require
official/primary authority or hashed provenance.

## Confidence

- CONFIRMED: official announcement (vendor blog, repo release, EOL page).
- CORROBORATED: 2+ independent sources.
- EMERGING: single credible secondary.
- UNVERIFIED: weak/rumor — never triggers ACTION alone.

Official evidence proves the statement *from that source*; it does not
automatically prove the user's dependency is affected. Impact coupling
is enforced by the gate.

## Popularity

GitHub stars inform reach, never risk: ≥50k very high, ≥10k high,
≥1k medium, else low, unknown → unranked. The facet stays
informational (always 🟢) — popularity never promotes an impact.

## Impact

INFORMATIONAL < WATCH < REVIEW < ACTION < CRITICAL. Findings also
carry severity (CVSS band), urgency, and recommended_action. No opaque
single score — facets stay separate.

## Intelligence semantics

An analyst `impact` is a proposal, not a conclusion. Reports place
findings through impact eligibility (`core/risk/impact.py`):

- `PROJECT_SIGNAL` — something exists (unscoped, unconfirmed).
- `PROJECT_CHANGE` — scoped ecosystem change (what changed, with
  versions/artifacts/dates). Never customer impact.
- `AFFECTS_DEPENDENCY` — a linked inventory entry matches.
- `ACTION_REQUIRED` — affected + effective + strong confidence. Only
  here does EOL (or any change) become action for *your* software.

Eligibility ladder for public reports: scoped effective EOL and
distribution model changes may be ACTION-framed (with disclaimer);
archived upstreams, vanished repositories/tags, and support ends are
REVIEW at most; upcoming EOL and routine registry churn are WATCH.
EOL detected never equals ACTION_REQUIRED — that needs inventory.

## Registry observations

What the registry exposed at time T: repository state, tag→digest
map, content hash (`core/observations/`). Tags are mutable pointers,
never identities. First sighting is a baseline; changes derive only
from observation diffs. History lives in git-ignored local JSON —
portable, no server.

## Uncertainty handling

Unknown version → no version claim. Unknown identity → RELATED, not
AFFECTS. Unknown applicability + KEV → REVIEW, not CRITICAL.
Conflicting evidence → visible + blocking for strong actions.

## Limitations — what OpenPulse does not know

- No auto-remediation; not a SAST/SCA replacement.
- English sources first; no private-registry visibility.
- Version comparison is best-effort numeric (exotic schemes → unknown).
- CPE data depends on NVD configuration quality.
- Popularity informs reach, never risk (stars bands, always 🟢).
- `latest` moves constantly — pin digests in production.
- License/support-model changes are curated events for now (Bitnami,
  iText fixtures): no automated license collector exists yet, so the
  pipeline cannot *discover* them — only validate, gate, and match
  them once recorded with evidence.

## Core distinctions (design principles)

- RELATED ≠ AFFECTED — association is not impact.
- AFFECTS_PROJECT ≠ AFFECTS_VERSION — project ties are contextual.
- UNKNOWN ≠ NOT_AFFECTED — unevaluated is not cleared.
- OBSERVATION ≠ CLAIM ≠ EVENT — facts, assertions, and gated
  intelligence are separate layers.
- Detection (what was observed) ≠ assessment (what evidence
  establishes) ≠ recommendation (what to investigate). Recommendations
  never feed back into impact calculations.
- SOURCE SIGNAL ≠ CHANGE ≠ AFFECTED DEPENDENCY ≠ ACTIONABLE
  INTELLIGENCE. A lifecycle date is a signal; a scoped, dated change
  is intelligence; impact requires a dependency.
- Public intelligence (what changed in OSS) ≠ customer intelligence
  (does it affect my software). Public reports never assert the second.

## Verdict decision matrix (`core/risk/check.py`)

AFFECTS_ARTIFACT > AFFECTS_VERSION > AFFECTS_PACKAGE >
NOT_AFFECTED > RELATED > AFFECTS_PROJECT > UNKNOWN.
`affected` is True only for ARTIFACT/VERSION/PACKAGE. A stronger
negative (evaluated version outside the range) beats RELATED/UNKNOWN;
no weaker match overrides it. Verdict confidence: ARTIFACT →
CONFIRMED, VERSION/NOT_AFFECTED → CORROBORATED, PACKAGE →
EMERGING, project/related → EMERGING/UNVERIFIED, unknown →
UNVERIFIED.

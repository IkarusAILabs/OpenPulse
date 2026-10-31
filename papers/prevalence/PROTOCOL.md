# Study protocol: upstream source changes among widely used packages

Status: **draft v0.1, 2026-10-31.** Frozen (tagged, SHA-256 of this file
recorded in `data/FREEZE.md`) before the main collection runs. Every later
change is appended to the amendment log at the end, with its date and
reason, and is never edited into the text above it.

## 1. Purpose

TR-2026-01 asks what upstream change evidence is missing from a
dependency decision (its Q1), and answers with examples. This study
measures it. It is independent of OpenPulse: it uses no OpenPulse code,
catalogue, fixture or verdict, so its results are not evidence for or
against OpenPulse's engine.

## 2. Research questions

- **RQ1 (prevalence).** Among the most depended-upon packages of npm,
  PyPI and Go, what share have a source repository that is archived,
  relocated, or no longer reachable?
- **RQ2 (exposure).** How many dependent packages and repositories do
  those packages have?
- **RQ3 (signal coverage).** For packages whose source repository is
  archived or unreachable, what share carry a machine-readable signal a
  dependency tool could act on: a registry deprecation flag, an advisory
  in OSV, or an entry in endoflife.date?
- **RQ4 (stale references).** Among packages whose source repository
  has a recorded earlier name, what share of registry metadata still
  publishes an earlier name, so that consumers reach the code only
  through a platform redirect? The denominator comes from ecosyste.ms's
  `previous_names`, because GitHub's API exposes no rename history; the
  numerator is the GitHub measurement (state *relocated*). Without an
  independent denominator the question would be true by construction: a
  package is *relocated* precisely when its published URL redirects.

RQ1–RQ4 are descriptive. The study tests no hypothesis and makes no
causal claim.

## 3. Sampling frame and sample

- **Frame.** Packages listed by ecosyste.ms (`packages.ecosyste.ms`) for
  the registries `npmjs.org`, `pypi.org` and `proxy.golang.org`, ranked by
  `dependent_repos_count`.
- **Sample.** For each ecosystem, the top 1,000 packages by that count
  (stratum *Top*) and a simple random sample of 1,000 packages from ranks
  1,001–20,000 (stratum *Tail*), drawn with a seed fixed in
  `data/FREEZE.md`. Results are reported per ecosystem and per stratum,
  never pooled across strata.
- **Unit.** A package. Packages that share a source repository are kept,
  and are also reported once per distinct repository.
- **Exclusion.** Packages whose registry metadata names no repository, or
  a repository on a host other than github.com, are counted and reported,
  and are excluded from RQ1–RQ4 (GitHub is the only host whose state is
  measured). The repository is always the one the registry publishes, not
  ecosyste.ms's normalised `repository_url`, because RQ4 asks whether that
  published reference is stale.

## 4. Measures

Every observation records the source, the request URL and the UTC time.
Primary sources decide every measure; ecosyste.ms is used only for the
frame, the ranking and the dependent counts.

| Measure | Source (primary) | Definition |
|---|---|---|
| Repository URL | The registry's own metadata, as published | npm: `repository` of the latest version's manifest (string or `.url`). PyPI: the first github.com URL among `project_urls` values under the keys Source, Sources, Source Code, Repository, Code, GitHub, Homepage (in that order, case-insensitive); else the first `project_urls` value, in published order, that names a github.com repository; else `home_page`. Go: the module path when it starts with `github.com/`; for `gopkg.in/` the mapping gopkg.in documents (`gopkg.in/user/pkg.vN` → `github.com/user/pkg`, `gopkg.in/pkg.vN` → `github.com/go-pkg/pkg`); otherwise the repository in the module's `go-import` meta tag (`https://<module>?go-get=1`), which is what the `go` command follows. A reference counts only if its host is exactly `github.com` (or `www.github.com`), in any of the forms registries publish: `https://`, `git+https://`, `git://`, `git@github.com:owner/repo`, a bare `github.com/owner/repo`, and for npm its documented shorthands `github:owner/repo` and `owner/repo`. The first two path segments name the repository; `.git` and trailing slashes are removed. |
| Repository state | GitHub REST API, `GET /repos/{owner}/{repo}` for that repository | **unchanged**: 200, and the returned `full_name` equals the requested one (case-insensitive); **relocated**: 200 after a redirect, and `full_name` differs; **unreachable**: 404 or 451; plus the `archived` flag on any 200 |
| Registry deprecation | npm: `deprecated` on the latest version's manifest; PyPI: `Development Status :: 7 - Inactive` classifier, or the latest release yanked; Go: the `go.mod` of the latest version carries a `// Deprecated:` comment (retraction is not measured: the Go proxy's `@latest` never returns a retracted version) | Present / absent, for the latest version |
| Advisory signal | OSV `querybatch` by ecosystem and name | Any OSV record whose summary or details matches the pre-registered terms `unmaintained`, `deprecated`, `archived`, `abandoned`, `no longer maintained`, `end of life`, `end-of-life` (case-insensitive) |
| Lifecycle signal | endoflife.date `api/all.json` | The package name, or its repository name, equals a product identifier |
| Exposure | ecosyste.ms | `dependent_packages_count` and `dependent_repos_count` at collection time |
| Rename history | ecosyste.ms `repo_metadata.previous_names` (secondary; GitHub exposes none) | The repository has at least one recorded earlier name |
| Stale reference | registry metadata vs the measured repository state | Among packages with a rename history: the published repository is in state *relocated* |

A package can be in more than one state (for example relocated and
archived). Each state is reported separately; no state is inferred from
another.

## 5. What these measures cannot show

Stated before collection, so they are not post-hoc excuses:

- **Archived is not abandoned.** A repository can be archived because
  development moved (into a monorepo, to a fork), while the package is
  still released. The study therefore also records whether the package
  had a release after the repository's last push (`pushed_at`). That is a
  proxy, not a determination, and is reported as such.
- **No dates of change.** GitHub exposes no archive date or transfer date
  through its API, so the study is cross-sectional: it measures state at
  collection time, not when changes happened or how long dependents took
  to react.
- **Signal matching is lexical.** The advisory and lifecycle measures can
  miss a signal phrased differently, and can match an unrelated mention.
  A validation sample (§6) estimates both errors.
- **Top-ranked packages are not typical packages.** The *Top* stratum
  describes the packages most depended on, which matter most for
  exposure; the *Tail* stratum is there so the results aren't read as
  ecosystem-wide.

## 6. Validation

- **Frame against source.** For a random 10% of sampled packages, the
  ecosyste.ms `archived` flag and `full_name` are compared with the GitHub
  measurement, and agreement is reported. Disagreement does not change any
  result, because GitHub decides.
- **Signal matching.** A random sample of 100 packages (or all, if fewer)
  with a matched advisory or lifecycle signal, and 100 without, is read by
  a human rater, who records whether the signal concerns the package's
  maintenance or location. **At least one rater must not be the author**;
  the author's ratings alone are reported only as a consistency check, and
  the paper says which raters were independent.
- **Archived packages.** Every archived repository in the *Top* stratum
  is classified by a rater as *moved* (the README or description names a
  successor location), *deprecated* (it says it is no longer maintained),
  or *unstated*, using a written guide (`RATING_GUIDE.md`, written before
  rating).

## 7. Analysis

- Proportions per ecosystem and stratum, with Wilson 95% intervals.
- Exposure as medians and totals, with the caveat that dependent counts
  overlap across packages and must not be summed into a count of affected
  projects.
- Signal coverage (RQ3) as a 2×3 table: archived / unreachable × registry
  / advisory / lifecycle, plus *any signal*.
- No hypothesis tests. Differences between ecosystems are described, not
  tested.

## 8. Pilot

A pilot of the top 100 packages per ecosystem tests the instrument only:
request handling, rate limits, parsing and the definitions above. Pilot
data are kept in `data/pilot/`, marked as pilot, and are not reported as
results.

Before this protocol was written, the author viewed summary counts from
the ecosyste.ms frame for the top 100 packages per ecosystem (counts of
`archived`, `previous_names` and registry `status`). The paper discloses
this.

The pilot changed this draft in three places, before it was frozen:

1. **PyPI repository URL.** Pilot v1 excluded 10 of 100 PyPI packages; 4
   of them published a GitHub repository under keys the rule didn't list
   (`Sources`) or only under other keys (`Bug`, `Download`). The rule
   gained `Sources` and a fallback to any `project_urls` value naming a
   GitHub repository. Pilot v2: 6 excluded, none of which publishes a
   GitHub URL.
2. **Go repository URL.** Pilot v1 excluded 31 of 100 Go modules because
   their paths are not on github.com. The rule now follows `gopkg.in`'s
   documented mapping and the `go-import` meta tag. Pilot v2: 17
   excluded, all `golang.org/x/…` and similar modules hosted on Google's
   own git, which this study does not measure.
3. **RQ4 denominator.** As first written, RQ4 was true by construction
   (a package is *relocated* exactly when its published URL redirects).
   It now uses repositories with a recorded earlier name as the
   denominator.

A fourth change came from code review (CodeQL), not from pilot data: the
first parser accepted any URL that merely contained `github.com`, such as
`mygithub.com/…`. It now requires that exact host. Re-applied to the
pilot v2 references, it changed no package's repository.

No pilot result is reported, and these changes were made for coverage
and validity of the measures, not in response to any prevalence figure.

## 9. Ethics and data

Only public package and repository metadata is collected; no personal
data beyond public account and organisation names in repository paths.
Requests stay within each service's documented rate limits. The raw
responses, the frozen sample and the analysis code are published with the
paper.

## Amendment log

_None yet._

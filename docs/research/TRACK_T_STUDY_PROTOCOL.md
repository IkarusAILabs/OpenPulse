# Track T study protocol: do the trust indicators separate what they claim to? (DRAFT)

**Status: a draft protocol (written 2026-11-03), not registered.** It becomes a registered protocol only when a named, accountable author archives it on OSF Registries or Zenodo **before** the held-out data in §4 is read. Until then it may change. After archiving, every change is an amendment (§10).

**Who runs it, and what that means.** This study is **author-run with AI assistance**. An AI assistant wrote this draft, the recorders and the analysis code, and will run them; the owner reviews and registers. It is therefore **not an independent evaluation**, and no result from it may be described as one. It follows the R-C rule in `docs/NEXT_PHASES.md`: no document claims that OpenPulse is more accurate than an alternative until an independent evaluation is complete. What makes the results worth having anyway:
- **external labels** (§4): which repositories ran fake-star campaigns and which packages were malicious comes from published third-party records, never from the authors or an AI;
- **thresholds frozen before the positives are read** (§5), on organic data only;
- **one pre-registered run**, with every deviation reported (§10).

It is separate from TR-2026-01 and its registration (`evaluation/REGISTRATION.md`), and never pooled with it. It answers parts of RQ2 and RQ3 from `docs/ROADMAP.md`, "Track T", "Evaluation plan". Agent studies (RQ1, RQ4) and enforcement (RQ5) are Part B, outlined in §11 and registered separately.

| Field | Value |
|---|---|
| Title | Do transparent package-trust indicators separate flagged from organic projects? |
| Responsible author | **to fill at archiving** (a person; an AI cannot be the accountable author) |
| Registry and identifier | **to fill at archiving** (OSF Registries or Zenodo DOI) |
| Archive date | **to fill at archiving** |
| Implementation freeze | **to fill at archiving**: tag and full commit of the OpenPulse measured |
| Analysis code | `benchmarks/record_star_history.py`, `benchmarks/record_young_set.py`, `benchmarks/record_reputation.py`, and the study script `benchmarks/track_t_study.py` |

## 1. Questions

- **Q-A (RQ3, star history).** Can a weekly star-history indicator flag repositories that StarScout identified as running fake-star campaigns, at a false-positive rate on organic projects of at most 1%?
- **Q-B (RQ3, package metadata).** How often do OpenPulse's existing package-level indicators (lookalike name, publisher change, moved repository, young popular repository, registry existence) fire on packages that OSV lists as malicious, compared with organic packages?
- **Q-C (RQ2).** For what share of a realistic dependency set can provenance be verified today, and how often does the check end in missing evidence?

## 2. Hypotheses

Set before any held-out data is read. Each is tested once.

- **H-A1.** At the threshold calibrated in §5, at least one of SH1–SH3 (§3) flags ≥ 50% of the StarScout sample whose history is available, with the lower 95% Wilson bound reported.
- **H-A2.** The same indicator flags ≤ 1% of the held-out organic repositories (upper 95% Wilson bound reported).
- **H-B1.** On OSV-malicious packages, the share flagged by `lookalike` is higher than on organic packages (difference with a 95% interval).
- **Q-C** is descriptive and has no hypothesis.

A hypothesis that fails is reported as failed, with the same prominence.

## 3. Indicators under test

**Star history (new, T-C2), defined here before any positive is read.** From GitHub's weekly star-history buckets (§4), over a repository's whole recorded history:

| Id | Name | Definition |
|---|---|---|
| SH1 | Peak week share | stars in the busiest week ÷ all stars; only for repositories with ≥ 50 stars |
| SH2 | Four-week concentration | stars in the busiest 4 consecutive weeks ÷ all stars; ≥ 50 stars |
| SH3 | Daily spike | the busiest day's stars ÷ the median daily stars of the 56 days before it (with the median floored at 1); ≥ 50 stars |

A repository is eligible only with at least 50 stars and a complete history (recorder status 200; a capped, incomplete or invalid series is not eligible). Weeks and days missing from the recorded series have no stars. SH2's four weeks are consecutive calendar weeks. When several days tie for busiest, SH3 uses the earliest.

Each fires when its value is **strictly above** its threshold (§5). No indicator is combined with another into a score; each is reported on its own (track T rule).

**Package metadata (existing, shipped in v0.12–v0.16):** `lookalike`, `publisher_change`, `repository_moved`, `young_popular_repository`, `registry_existence`, each with its production rule unchanged.

## 4. Data

All sources are pinned by date and SHA-256 at the freeze. **No package contents or malware are ever downloaded**: only names, versions and registry or GitHub metadata.

| Set | Source | Labels from | Committed? |
|---|---|---|---|
| Organic repositories | The repositories of the organic reputation set (`benchmarks/fixtures/reputation/organic-*.json`), star histories recorded by `record_star_history.py` | Their selection: popular, curated or depended-on projects (Q1) | Yes |
| Organic young repositories | `benchmarks/record_young_set.py`: GitHub repositories created in the 12 calendar months ending 30 days before recording, with ≥ 50 stars (Python, JavaScript, TypeScript; not forks, not archived), kept only when the PyPI or npm package of the same name claims exactly that repository, has no OSV `MAL-` record, and StarScout did not flag it; a fixed-seed sample of 500 | Two-way registry linkage, no malicious record, not flagged (residual risk stated) | Yes |
| Fake-star positives | StarScout (He et al., "Six Million (Suspected) Fake Stars in GitHub", ICSE 2026), `data/250101/fake_stars_{clustered,low_activity}_repos.csv` at commit `7994d8e4cd3bd6e724e513c14e9d696ded23048f` (SHA-256 clustered `02aeaf16bb1d4bef1069717dd50bc6595055d124d5573436d60b3aaaeddb52d4`, low activity `bd9d12344d205d27fd933070e98a3db2101b3678ae602974350eabe4656debee`); a fixed-seed sample of 1000 (seed `20261103`) | StarScout's detection (heuristic, per method) | **No**: local only (§8) |
| Malicious packages | OSV `PyPI/all.zip` and `npm/all.zip`, `MAL-` records only, snapshot at the freeze; the Datadog malicious-software-packages dataset's **manifest** (names only) as a second source | OSV / OpenSSF malicious-packages and Datadog | Names and versions only |

**Star history.** Third-party stargazer listings (`/stargazers`, and GraphQL `starredAt`) return nothing since GitHub's 2026 restriction (verified 2026-11-03: 404 with a token, 401 without, empty GraphQL edges). The study uses the star-history endpoint (`GET /repos/{owner}/{repo}/stargazers/history`, API 2026-03-10): weekly counts with a per-day breakdown, newest first, no stargazer.

**Known biases, reported with the results:**
- **Survivorship.** Many flagged repositories are deleted (StarScout reports most promote short-lived malware). The positive set is the flagged repositories whose history still answers; the share that does is reported.
- **Circularity.** StarScout's "clustered" method looks for stars clustered in time, which SH1–SH3 also measure. Results are reported per StarScout method; the `low_activity`-only subset (accounts with little other activity) is the less circular test.
- **Label noise.** StarScout's authors say flagged repositories may be false positives. Results are stated as agreement with StarScout, never as accuracy.
- **Organic is not proven benign.** It is popular or depended-on, which makes a fake-star campaign unlikely, not impossible.

### What has been read so far (2026-11-03)

The three sets are recorded. Before archiving, indicator values have been computed **only for the organic calibration half** (§5); for the held-out half and the positives only **availability** has been looked at:

| Set | Recorded | Histories read | Not available |
|---|---|---|---|
| Organic (`stars-organic-2026-11-03.json`) | 123 | 123 | 0 |
| Organic young (`stars-young-2026-11-03.json`) | 500 of 706 kept from 6,976 candidates (6,267 not linked both ways, 3 with an OSV `MAL-` record) | 500 | 0 |
| StarScout positives (local) | 1,000 (668 flagged by `clustered`, 353 by `low_activity`, 21 by both) | 366 (96 `clustered`, 290 `low_activity`) | 634: 627 deleted (404), 7 blocked (403) |

History totals match GitHub's star counts (organic median ratio 1.000; young within 1%). Survival among the positives differs by StarScout method (82% of `low_activity` repositories still answer, 14% of `clustered` ones), so the surviving positive set leans to the less circular method (§4): of the 366, 270 were flagged by `low_activity` alone. Rate-limited answers were waited out and retried, so no repository is unavailable because of the rate limit.

## 5. Calibration and freezing

1. The organic repositories (both organic sets, pooled) are split 50/50 with seed `20261103`, within each set, into **calibration** and **held-out** halves. False-positive rates are reported for the pooled held-out half and for the young held-out half on its own.
2. On the pooled calibration half only, each SH threshold is the (k+1)-th largest eligible value, k = ⌊1% × eligible⌋: the smallest observed value that at most 1% of eligible calibration repositories exceed. The split is made from names before any value is computed.
3. The thresholds are computed **before archiving** and archived with the protocol. The positives and the held-out half are read only after the archive date.
4. The frozen thresholds are applied once to the held-out organic half (H-A2) and the positives (H-A1).

The package-metadata indicators keep their production thresholds; nothing is tuned.

### Calibration result (computed 2026-11-03, before archiving)

`python benchmarks/track_t_study.py calibrate`, written to `benchmarks/fixtures/reputation/star-calibration-2026-11-03.json` with the split (names only) and the SHA-256 of both organic fixtures. Calibration half: 61 of 123 organic and 250 of 500 young repositories; 300 eligible (11 organic repositories have fewer than 50 stars). k = 3.

| Indicator | Threshold (fires when strictly above) | Calibration repositories above it |
|---|---|---|
| SH1 peak week share | 0.7956 | 3 of 300 |
| SH2 four-week concentration | 0.9921 | 3 of 300 |
| SH3 daily spike | 2581 | 3 of 300 |

These are strict: organic young projects often gain most of their stars in a launch week, so a 1% false-positive cap leaves only extreme bursts flagged. That makes H-A1 harder to meet; the thresholds stand as computed, and the result is reported whichever way it goes. No held-out organic repository and no positive was read to compute them (the script reads only calibration-half histories; `tests/test_track_t_study.py` checks this).

## 6. Metrics

- Firing rate per indicator on each set, with 95% Wilson intervals.
- For positives: recall against StarScout, per StarScout method and overall.
- Unresolved rate: repositories or packages whose evidence could not be read (deleted, 404, rate-limited, invalid series), per set.
- Q-C: share of a dependency set with verified provenance, missing provenance, and not checked, per ecosystem.

## 7. Stopping rule

One run on the frozen data. If GitHub's rate limit interrupts recording, recording resumes until the sample is complete or 7 days pass; the remainder is reported as unresolved. No resampling to improve a result.

## 8. Ethics and data handling

- StarScout's authors ask that the data be used for statistical analysis, not to name individual repositories. Positive histories are stored only under `benchmarks/fixtures/reputation/local/` (git-ignored), and only aggregate results are published.
- No artifact is downloaded or executed; no package is published; no live attack is run.
- GitHub is read within its rate limits, with a token passed through the environment only.

## 9. Who does what

| Step | Who |
|---|---|
| Draft the protocol, write the recorders and analysis code, run them, write the report | AI assistant, reviewed by the owner |
| Approve the protocol, archive it under their name, tag the freeze | The responsible author (the owner) |
| Labels | Third parties only: StarScout, OSV / OpenSSF, Datadog |
| Independent replication | Invited; anyone can rerun from the archived protocol and the committed data |

## 10. Deviations

Any change after archiving is an amendment: dated, with its reason, reported with the results. A deviation found after the run is reported, never silently fixed.

## 11. Part B (outline, registered separately)

- **RQ1 and RQ4 (agents).** Coding agents given realistic tasks against a local stub registry in a reserved namespace, with and without OpenPulse's trust block: selection of non-existent or lookalike packages, and whether warnings are acted on. The agent's behaviour is what is measured; no AI labels anything.
- **RQ5 (enforcement).** The gate, receipts (v0.17) and bypass routes on synthetic changes: prohibited installs prevented, false blocks, latency.

## 12. What this study cannot show

- That OpenPulse is more accurate than any other tool (no independent evaluation; R-C).
- That an indicator detects fake stars in general: it shows agreement with one published detector, on the repositories that still exist.
- That an unflagged project is trustworthy: absence of an indicator is never evidence of authenticity.

# Registering the track T study (Part A): the owner's steps

This is item TR5 in `docs/NEXT_PHASES.md`. The protocol (`docs/research/TRACK_T_STUDY_PROTOCOL.md`) becomes a registered protocol only when a named person archives it **before** the held-out data is read. An AI assistant prepared everything below. The archiving itself, and the name on it, must be yours: an AI cannot be the accountable author.

Nothing in the held-out half, the StarScout positives or the malicious-package sample has been read. `track_t_study.py run` refuses to run until the steps below are done.

## Before you start: two decisions

| # | Decision | If yes | If no |
|---|---|---|---|
| 17 | Register Part A under your name | Follow the steps below | The study stays a draft; nothing runs |
| 18 | Use StarScout's flagged-repository lists as fake-star labels, kept local and published only as aggregates | Q-A runs as written | Q-A has no positives: amend §1, §2 and §4 to drop Q-A (Q-B and Q-C still run) before archiving |

Read the protocol in full. Every choice in it is fixed once you archive: the questions, hypotheses, thresholds, samples, metrics and stopping rule. A later change is an amendment, reported with the results (§10).

## Steps

Zenodo is suggested because it can reserve a DOI before publishing, so the archived protocol can name its own identifier. OSF Registries works too: use the registration's identifier in the same places.

1. **Merge #318** (the protocol, data, calibration and analysis code) into `main`.
2. **Reserve a DOI.** On Zenodo, start a new upload and reserve a DOI (the upload form offers this before publishing). Do not publish yet.
3. **Fill the protocol's header** in a small pull request against `main`. Replace each "to fill at archiving" field (including its bold marker):
   - Responsible author: your name and affiliation (and ORCID if you have one).
   - Registry and identifier: `Zenodo, <the reserved DOI>`.
   - Archive date: the date you will publish.
   - Implementation freeze: the tag `track-t-part-a-freeze`.

   Merge it.
4. **Tag the freeze** on that merge commit and push the tag:

   ```bash
   git tag -a track-t-part-a-freeze -m "Track T study Part A: implementation freeze"
   ```

   ```bash
   git push origin track-t-part-a-freeze
   ```

5. **Build the archive** from a clean checkout of that tag. It refuses if a protocol field is unfilled, a file differs from the commit, or the commit has no tag:

   ```bash
   python benchmarks/track_t_study.py package
   ```

   It writes `dist/track-t-part-a-<commit>.zip` and prints its SHA-256. The zip holds the protocol, the analysis code, the production rules it applies, every committed input and a `MANIFEST.json`. That manifest has the commit, the tag and each file's SHA-256. It also pins, by hash only, the inputs that are not archived: StarScout's files and the local positives (kept private, as StarScout's authors ask), and OSV's archives.
6. **Publish on Zenodo.** Upload the zip, and the protocol file on its own so it can be read without unzipping. Suggested metadata:
   - **Title:** Do transparent package-trust indicators separate flagged from organic projects? (Track T study, Part A: registered protocol)
   - **Creators:** you. The AI assistance is disclosed in the description, not as a creator.
   - **Description:** "Pre-registered protocol, analysis code and inputs for OpenPulse's track T study, Part A: star-history indicators against StarScout's fake-star labels (Q-A), package indicators on OSV-malicious packages (Q-B), and provenance coverage (Q-C). Thresholds were calibrated on organic data before archiving; held-out and labelled data are read only after. Author-run with AI assistance; not an independent evaluation."
   - **License:** Apache-2.0, as the repository.
   - **Related identifiers:** the repository (`https://github.com/IkarusAILabs/OpenPulse`) and the tag's tree URL.
   - **Keywords:** software supply chain, open source, package registries, fake stars, malicious packages, preregistration.
7. **Tell the AI assistant the DOI.** The run is one command, on the tagged code:

   ```bash
   python benchmarks/track_t_study.py run --registered <the DOI>
   ```

   It writes `benchmarks/results/track-t-part-a.json` and `docs/research/TRACK_T_PART_A_RESULTS.md`, and refuses to run a second time.

## Review copy

To see exactly what will be archived before you decide, build a draft bundle (marked DRAFT, listing what is still missing):

```bash
python benchmarks/track_t_study.py package --draft
```

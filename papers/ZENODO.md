# Archiving OpenPulse on Zenodo

Zenodo gives each archived release a DOI, which the arXiv comments field,
`CITATION.cff` and later journal papers can cite. Both steps need the
author's Zenodo account, so they are yours.

## 1. Future releases: switch on the GitHub integration

1. Log in to <https://zenodo.org> with GitHub.
2. Open <https://zenodo.org/account/settings/github/> and switch
   **IkarusAILabs/OpenPulse** on. If the organisation doesn't appear,
   grant Zenodo access to IkarusAILabs in GitHub's OAuth settings first.

From then on, every *published* GitHub release is archived automatically,
using `.zenodo.json` in the repository root for its metadata.

## 2. v0.8.0: upload it once by hand

The integration only reacts to releases published after it is switched
on, and v0.8.0 (the release TR-2026-01 describes) was published on
2026-10-31, before that. Don't cut a new release just to trigger it: the
report cites v0.8.0 exactly. Upload it manually instead.

1. Build the archive from the tag. The tag is fixed, so the archive is
   reproducible:

   ```bash
   git archive --format=tar.gz --prefix=OpenPulse-0.8.0/ -o OpenPulse-v0.8.0.tar.gz v0.8.0
   ```
2. On Zenodo, choose **New upload** and add `OpenPulse-v0.8.0.tar.gz`.
3. Fill in the form:

   | Field | Value |
   |---|---|
   | Resource type | Software |
   | Title | OpenPulse: upstream change evidence for dependency decisions |
   | Creators | Kış, Mehmet (Ikarus AI Labs, Cambridge, United Kingdom); add your ORCID if you have one |
   | Version | v0.8.0 |
   | Publication date | 2026-10-31 |
   | Licence | Apache License 2.0 |
   | Description | copy from `.zenodo.json` |
   | Keywords | copy from `.zenodo.json` |
   | Related works | `https://github.com/IkarusAILabs/OpenPulse/tree/v0.8.0`, *is supplement to*; the TR-2026-01 PDF (and the arXiv identifier once posted), *is documented by* |
4. Publish, and note the version DOI.

## 3. After the DOI exists

- Add it to `CITATION.cff` under `identifiers` (type `doi`), and to the
  README citation.
- Put it in the arXiv comments field (`papers/tr-2026-01/ARXIV.md`).
- When the next release is archived by the integration, Zenodo also
  creates a *concept DOI* that always resolves to the latest version.
  Cite the version DOI in papers, so readers get exactly v0.8.0.

# Literature review protocol

**Status:** prepared, not yet executed. No new search was run for this draft, and no reference was verified in this session.

The draft cites only entries of the technical report's bibliography:
- 25 of them are among the 47 verified on 2026-10-28 (`papers/tr-2026-01/related_notes.md`: Crossref, usenix.org, arXiv, official pages);
- 4 were entered from memory and are marked with a dagger in the text (`\citeUNV`) and `% UNVERIFIED` in `references.bib`.

## 1. Questions the review must answer

1. Does an existing format, standard or tool already represent **whether a listed affected set is complete**, and decide applicability from it?
   - **Read first:** the SPDX 3.0 `Relationship.completeness` property (complete / incomplete / noAssertion); CycloneDX `compositions[].aggregate`; the CSAF product-status semantics; the VEX `under_investigation` status.
   - **Answer before writing any novelty sentence.**
2. How do SCA tools and vulnerability databases decide "not affected", and what do they do when identity is uncertain (purl/CPE matching, ecosystem aliases)?
3. What is known about package identity, namespace and confusion (dependency confusion, typosquatting, mirrors, renamed repositories)?
4. What empirical work measures lifecycle events: deprecation, archival, licence change, registry moves?
5. Three-valued and multi-valued decision models; the closed-world assumption and query completeness in databases.
6. AI coding agents: package hallucination, dependency selection, tool-output injection, and assurance for AI-mediated change.

## 2. Search

- **Sources:**
  - ACM DL, IEEE Xplore, Springer Link, USENIX, arXiv (cs.SE, cs.CR);
  - specification sites: SPDX, CycloneDX/ECMA, OASIS CSAF, OpenVEX, OSV, CISA.
- **Strings** (record each run with its date and hit count):
  - `("software composition analysis" OR "vulnerable dependenc*") AND (applicab* OR "not affected" OR reachab*)`
  - `("VEX" OR "vulnerability exploitability exchange")`
  - `("closed world assumption" OR "incomplete information") AND (completeness)`
  - `("dependency confusion" OR typosquat* OR "package identity" OR purl)`
  - `("deprecat*" OR "archiv*" OR "end of life" OR "license change") AND (dependenc* OR ecosystem)`
  - `("coding agent" OR "LLM") AND (package OR dependency) AND (hallucinat* OR select*)`
- **Window:** 2015–2026 for empirical work; no limit for foundations.
- **Snowballing:** one round backward and forward from the 10 closest papers.

## 3. Inclusion and exclusion

- **Include:** peer-reviewed papers, standards and specifications, and primary vendor documentation for facts about a format.
- **Grey literature:** blogs, only for facts no primary source states, marked as such.
- **Exclude:** secondary summaries where the primary is available.

## 4. What to record per included work

A table with these columns:
- key and full citation, with a DOI or stable URL;
- how it was verified, and the date;
- research question;
- method;
- evaluation design;
- main findings;
- limitations;
- relation to OpenPulse;
- the specific distinction, if any, **supported by evidence from the source**.

## 5. Must-verify list (before submission)

| Key | Problem |
|---|---|
| `oasis2022csaf` | No DOI or URL in the entry |
| `reiter1978closed` | Entered from memory; check the venue (a 1978 *Logic and Data Bases* chapter) and pages |
| `razniewski2011completeness` | Entered from memory; check the venue and year |
| `kleene1952introduction` | Entered from memory; check the edition and publisher |
| SPDX 3.0, CycloneDX compositions | Not cited yet; read and position (question 1) |
| `krishna2025phantoms`, `debenedetti2024agentdojo` | arXiv versions cited; check for peer-reviewed versions (AgentDojo appeared at NeurIPS 2024) |
| `nistnvd` (TR only) | The 2026 status page claim needs a dated archive |

The other 11 unverified entries of the TR bibliography are not cited in this draft.

## 6. Claims the manuscript must not make until §1–5 are done

- that the model is novel, or that it is the first;
- that existing formats cannot express completeness;
- any comparison of effectiveness with a named tool.

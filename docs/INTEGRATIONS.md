# Integrations: SARIF, DefectDojo and Dependency-Track

Every OpenPulse output is built from the same evidence contracts (`openpulse attest`, [`docs/EVIDENCE_CONTRACT.md`](EVIDENCE_CONTRACT.md)), so the JSONL, SARIF, DefectDojo and Dependency-Track views never disagree. For GitHub Code Scanning (SARIF) in CI, see [`docs/GITHUB_ACTION.md`](GITHUB_ACTION.md).

## DefectDojo

Security teams already triage in DefectDojo, so OpenPulse findings can go there directly. `attest --defectdojo` writes DefectDojo's **Generic Findings Import** format.

```bash
openpulse attest --lockfile poetry.lock --event data/fixtures/django-eol/event.json --defectdojo openpulse-defectdojo.json
```

```bash
curl -sS -X POST "$DEFECTDOJO_URL/api/v2/import-scan/" -H "Authorization: Token $DEFECTDOJO_TOKEN" -F scan_type="Generic Findings Import" -F engagement="$ENGAGEMENT_ID" -F file=@openpulse-defectdojo.json
```

In the UI, open the engagement and choose **Import Scan Results** with scan type *Generic Findings Import*.

| Contract | DefectDojo severity |
|---|---|
| Affected, CRITICAL impact | Critical |
| Affected, ACTION impact | High |
| Affected, REVIEW impact | Medium |
| Affected, WATCH or INFORMATIONAL impact | Low |
| RELATED, or a dependency no event applies to | Info |
| NOT_AFFECTED | not exported |

Each finding includes:

- the evidence URLs, the recommendation, and what could not be established;
- the hash of the evidence contract it came from;
- a stable `unique_id_from_tool`, so re-imports deduplicate instead of piling up.

Trust results (`attest --trust`) are separate findings tagged `trust`. Their severity reflects your trust policy, never a risk score: High only when the policy prohibits the condition ([`docs/TRUST_POLICY.md`](TRUST_POLICY.md)).

## Dependency-Track

Dependency-Track only tracks vulnerabilities, so OpenPulse findings go in as **INTERNAL vulnerabilities**, one per OpenPulse event (`OPENPULSE-<event id>`), assigned to the affected components of your DT project:

```bash
openpulse attest --sbom bom.json --event data/fixtures/django-eol/event.json --output contracts.jsonl
openpulse dependency-track --contracts contracts.jsonl --dry-run
```

```bash
OPENPULSE_DTRACK_API_KEY=... openpulse dependency-track --contracts contracts.jsonl --url https://dtrack.example --project-name my-app --project-version 1.4.0
```

- **What is pushed:** only *affected* pairs. RELATED and UNKNOWN pairs stay in the JSONL, SARIF and DefectDojo outputs, because DT treats anything assigned as vulnerable.
- **Matching:** components are matched by group, name and version inside the project. Dependencies that aren't components of the project are reported, never guessed onto a different component.
- **Re-runs:** pushing again reuses existing vulnerabilities, so nothing duplicates.
- **Credentials:** the API key is read only from `OPENPULSE_DTRACK_API_KEY`, never from the command line. It needs the `VULNERABILITY_MANAGEMENT` and `PORTFOLIO_MANAGEMENT` permissions.
- **Transport:** HTTPS is required unless you pass `--allow-http`, and redirects are never followed.

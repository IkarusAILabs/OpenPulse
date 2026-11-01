# Scheduled watchlist checks

`openpulse check` is built for unattended runs: bounded input, no
network except live collectors, and `--strict` (exit 1 when anything
is affected) as the CI-gate primitive. `--digest` prints the grouped
summary instead of per-dependency lines — the shape to archive or post.

## Cron (weekly Monday 06:00 UTC)

```cron
0 6 * * 1 cd /opt/OpenPulse && openpulse check --watchlist watchlists/prod.yaml --event events/current.json --digest >> var/checks/$(date +\%F).md
```

Use `--raw-bundle-dir` with checked-in offline bundles when the
schedule must not depend on upstream APIs that day.

Recording is on by default: every scheduled run persists durable
first detections to `.openpulse/detections/` (the detection ledger),
so a warning window survives across cron runs — a re-detected
lifecycle or security fact reports its original first-seen date,
never "today". Pass `--ledger ''` to disable recording for a run
(no claims are made, nothing is written). Point two schedules at
different roots with `--ledger <path>` to keep their histories
independent.

## GitHub Actions (weekly + CI gate)

```yaml
name: watchlist
on:
  schedule: [{cron: "0 6 * * 1"}]
  workflow_dispatch:
permissions:
  contents: read
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5
        with: {python-version: "3.11"}
      - run: pip install -U pip "setuptools>=83" && pip install -e .
      - run: openpulse check --watchlist watchlists/prod.yaml --event events/current.json --strict
```

`--strict` fails the workflow exactly when a dependency is affected;
`RELATED`/`UNKNOWN` never fail a gate. Keep the watchlist and the
event files committed next to this recipe so every run is reproducible.

### Keyed history across runs (lead times in CI)

A fresh runner starts with an empty `.openpulse/`, so the recipe above
records every detection as new and publishes no lead time. Lead times
need two things: the detection ledger carried from run to run, and a
history key, because `check`, `digest`, `warnings` and `report` publish
first detections only from keyed history (`docs/KEYED_INTEGRITY.md`).

1. Make a key once, on your own machine: `openpulse history-key generate`.
   It prints the key on stdout and its `key_id` on stderr, and writes
   nothing. Store the key as an Actions secret, for example
   `OPENPULSE_HISTORY_KEY`. Never commit it, and never put it under
   `.openpulse/` (OpenPulse refuses a key file there).
2. Pass the secret as an environment variable and carry the ledger in
   the Actions cache:

```yaml
    steps:
      # ...checkout, setup-python and install as above...
      # Pin actions/cache to the commit SHA you have reviewed, like the steps above.
      - uses: actions/cache@v4
        with:
          path: .openpulse/detections
          key: openpulse-ledger-${{ github.run_id }}
          restore-keys: openpulse-ledger-
      - run: openpulse digest --watchlist watchlists/prod.yaml --event events/current.json
        env:
          OPENPULSE_HISTORY_KEY: ${{ secrets.OPENPULSE_HISTORY_KEY }}
      - run: openpulse check --watchlist watchlists/prod.yaml --event events/current.json --strict
        env:
          OPENPULSE_HISTORY_KEY: ${{ secrets.OPENPULSE_HISTORY_KEY }}
```

Each run restores the newest saved ledger and saves its own under a
new key. Run `digest` before `check`: `digest` reads the ledger and
`check` records today's detections. The cache is scoped by branch, so
run the schedule on the default branch; a pull request's cache can
never reach it. A cache GitHub has evicted (unused for 7 days) starts
the ledger again: detections are new, never backdated. Anyone who can
edit the cache but lacks the key can delete entries, but cannot forge
one: an edited entry fails its MAC and publishes no lead time.

**Rotating the key:** make a new key, set it as
`OPENPULSE_HISTORY_KEY`, and move the old one to
`OPENPULSE_HISTORY_KEYS_PREVIOUS` (also a secret). The next run
re-keys the ledger and logs the handover; drop the old key once every
entry has been rewritten.

## Posting digests (Slack)

```bash
openpulse check --watchlist watchlists/prod.yaml --event events/current.json \
  --digest --webhook "$SLACK_WEBHOOK_URL" --strict
```

Posts the grouped digest to any JSON-text webhook (Slack incoming
webhook contract: `{"text": "..."}`). Delivery failures warn but never
mask the check result — `--strict` still reflects affected state only.
Store the URL as an Actions secret, never in the repo.

## Watchlist format

See `data/fixtures/watchlist_sample.yaml`. Optional per-dependency
`source`, `environment`, `owner` fields pass through untouched for
future hosted ingestion.

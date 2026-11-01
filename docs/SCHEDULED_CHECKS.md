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

To fail on **deadlines** instead (v0.11.0), gate on `warnings`:

```yaml
      - run: openpulse warnings --watchlist watchlists/prod.yaml --event events/current.json --fail-on critical
```

`--fail-on SEVERITY` exits 1 when a warning at or above that severity
is in the window. The order is OVERDUE > CRITICAL (7 days or less) >
HIGH (30) > MEDIUM (90) > LOW, so `critical` also fails on a deadline
that has already passed. The reason goes to stderr, so `--output json`
stays parseable. As with every gate, FAILED repository coverage fails
it too. Without `--fail-on`, `warnings` only reports.

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

**Anchoring the ledger:** the cache is writable by anything that runs
in the repository's workflows, so keep a checkpoint where it is not.
After `check`, write an anchor and keep it as an artifact or commit it
to a dedicated branch; at the start of the next run, verify the restored
ledger against the previous anchor:

```yaml
      - run: openpulse verify --anchor anchors/latest.json --require-signed
        env:
          OPENPULSE_HISTORY_KEY: ${{ secrets.OPENPULSE_HISTORY_KEY }}
      # ...digest and check as above...
      - run: openpulse anchor --out anchors/latest.json
        env:
          OPENPULSE_HISTORY_KEY: ${{ secrets.OPENPULSE_HISTORY_KEY }}
```

`verify` exits 1 when anything the anchor saw is gone or changed (a
deleted or backdated ledger entry, a dropped rotation-log entry), and
`--require-signed` refuses an anchor the key did not sign. On the very
first run there is no anchor yet: skip `verify` until one exists.

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

Posts to any JSON-text webhook (Slack incoming webhook contract:
`{"text": "..."}`). Delivery failures warn but never mask the check
result — `--strict` still reflects affected state only. Store the URL as
an Actions secret, never in the repo.

**Each alert is posted once (v0.11.0).** An alert is one affected cause
of a verdict, or a repository that was not fully read. OpenPulse records
what it delivered in `.openpulse/deliveries/alerts.json`
(`--delivery-state` or `OPENPULSE_DELIVERY_STATE` to move it):

- A run posts only alerts not delivered before, and nothing when there
  are none. The terminal output still shows the full digest.
- A revised event or a raised impact is a new alert.
- A failed post is retried once in the run, then on later runs with a
  backoff (5 minutes, doubling, at most 6 hours). After 5 failed runs
  the alert is dead-lettered: kept in `alerts.json` with its last error
  and never posted again.
- The webhook URL is never stored.

In GitHub Actions, carry the state in the cache like the ledger, or
every run starts empty and posts everything again:

```yaml
      - uses: actions/cache@v4   # pin to a reviewed commit SHA
        with:
          path: .openpulse/deliveries
          key: openpulse-deliveries-${{ github.run_id }}
          restore-keys: openpulse-deliveries-
```

`--delivery-state ''` restores the old behaviour: the whole digest on
every run.

**Signed posts (v0.11.0).** Set `OPENPULSE_WEBHOOK_SECRET` (an Actions
secret; `openssl rand -hex 32` makes one, at least 32 characters) or
pass `--webhook-secret-file`. Every post then carries
`X-OpenPulse-Timestamp` and `X-OpenPulse-Signature: v1=<hex>`. A
receiver that holds the same secret checks them over the **raw** request
body:

```python
from core.webhook_signing import verify_webhook_signature  # stdlib only; copy the file

ok = verify_webhook_signature(
    secret, raw_body,
    headers.get("X-OpenPulse-Timestamp"), headers.get("X-OpenPulse-Signature"),
)  # False for a wrong signature, or a timestamp more than 300 s off (a replay)
```

Slack and Teams incoming webhooks ignore the headers, so signing is
harmless there; it matters for a receiver you run yourself.

## Watchlist format

See `data/fixtures/watchlist_sample.yaml`. Optional per-dependency
`source`, `environment`, `owner` fields pass through untouched for
future hosted ingestion.

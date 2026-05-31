# Global Macro Panel Continuation Mission

Date: 2026-05-31

Status: complete

## Goal

Build the next useful Marco data foundation by turning the current FRED, ECB,
and World Bank source hauls into a documented global macro panel artifact,
without coupling source ingestion to hosted uploads, MikeOSS, FinRobot,
Sourcecycled, or `vmctl`.

## MissionGradient

Value criterion:

```text
Maximize reusable official macro data coverage while preserving provenance,
latest-revised/vintage labeling, source-adapter independence, and a single
agent-readable artifact surface.
```

Quality target: solid.

Homotopy:

```text
configured source haul
-> cached raw official observations
-> normalized source observations
-> narrow annual panel summary
-> model-ready global macro panel with explicit frequency joins
-> cross-country backtests
```

The narrow annual panel is valid only if it preserves the same source,
provenance, artifact, CLI, and API shape required by the fuller panel.

## Invariants

- Keep generated raw data under ignored `data/`.
- Commit compact shareable summaries only.
- Label all current public-source data as latest-revised snapshots.
- Keep source adapters independent from the experiment runner.
- Use official APIs first.
- Preserve source URLs, hashes, provider IDs, frequency, period, and country.

## Essential Work

1. Define a reusable configured source haul.
2. Keep fetch commands reproducible.
3. Build a normalized global macro panel from current source observations.
4. Export a compact shareable panel summary.
5. Expose the summary through CLI/API and the static frontend.
6. Update docs with exactly what data exists and what remains unproven.

## Stopping Condition

The mission is complete when CI passes and the repo exposes a committed
shareable global macro panel summary built from the current FRED/ECB/World Bank
foundation.

## Run Checkpoint & Resumption State

status: complete

last checkpoint: configured source haul, global panel builder, CLI/API endpoint,
frontend artifact load, docs, local CI verification, GitHub CI verification,
and live static preview verification are complete.

current artifact state: the committed target artifact should be
`artifacts/global-macro-panel/global_macro_starter_20260531/summary.json`.

what shipped: commit `7ddf4a7`, followed by a documentation evidence commit.

what was proven: targeted tests for global panel, agent API, ECB, and World Bank
passed locally; full `make ci` also passed with 34 Python tests and a Svelte
production build; GitHub CI passed; live `choir-ip.com` served the global panel
JSON as `application/json`; browser verification found the new Global Macro
Data Haul panel.

unproven or partial claims: GitHub Actions deploy secrets are still absent, so
the deploy workflow currently skips remote deploy and local `node-a` deployment
is still required.

belief-state changes: the immediate highest-value expansion is a small
official-source annual global panel, not another frontend feature or hosted
upload path.

remaining error field: source coverage is still annual and latest-revised;
cross-frequency joins are explicitly not proven.

highest-impact remaining uncertainty: how much monthly/quarterly official data
can be added through ECB, IMF, OECD, BIS, and RBI before the backtest runner
needs new missing-data/frequency semantics.

next executable probe:

```sh
gh secret set NODE_A_HOST --body '51.81.93.94'
gh secret set NODE_A_USER --body 'root'
gh secret set NODE_A_SSH_PRIVATE_KEY < ~/.ssh/id_ed25519_ovh
```

suggested resume goal string:

```text
/goal In /Users/wiz/emf, turn the global_macro_starter_20260531 annual source-haul artifact into the next model-ready global macro panel by adding one monthly or quarterly official source family with explicit frequency/missingness policy, preserving source hashes and vintage labels, and proving the resulting panel can feed a small cross-country FX/rate backtest without leaking latest-revised assumptions into vintage-safe claims.
```

evidence artifact refs:

```text
artifacts/global-macro-panel/global_macro_starter_20260531/summary.json
docs/runs/20260531-global-macro-panel-checkpoint.md
```

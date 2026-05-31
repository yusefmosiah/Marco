# Marco Agent API Reference

## CLI Commands

Use from the repo without installing the package:

```sh
PYTHONPATH=src python3 -m emf_macro.cli <command> --root .
```

Commands:

```text
list-runs
show-run --run-id latest
metrics --run-id latest --pair USD_CAD --horizon 6
best --run-id latest --pair USD_CAD --horizon 6
agent-context --run-id latest
report --run-id latest
serve-agent-api --host 127.0.0.1 --port 8765
list-datasets
dataset-add path/to/data.csv --name "My Dataset"
dataset-fetch-url https://example.com/data.csv --name "External Dataset"
models
suggest-hypotheses
plan-experiments --pair USD_CAD --horizon 6
```

Installed command equivalent:

```sh
emf-macro <command>
```

## HTTP Endpoints

Default local API base:

```text
http://127.0.0.1:8765
```

Endpoints:

```text
GET /health
GET /v1/runs
GET /v1/runs/latest
GET /v1/runs/latest/metrics?pair=USD_CAD&horizon_months=6
GET /v1/runs/latest/best?pair=USD_CAD&horizon_months=6
GET /v1/runs/latest/report
GET /v1/datasets
GET /v1/models
GET /v1/hypotheses
GET /v1/experiment-plan?pair=USD_CAD&horizon_months=6
GET /v1/agent-context
```

The API also supports `HEAD` for endpoint checks.

## Public Static Artifact

Node A static preview:

```text
https://choir-ip.com/marco/
https://choir-ip.com/marco/artifacts/fred-fx-rate-lab-summary.json
```

This is not the dynamic API. It is enough for agents to inspect the current
shareable run summary.

## Important Fields

Run identity:

```text
run_id
created_at
vintage_policy
lookahead_status
headline.status
```

Metric rows:

```text
pair
horizon_months
model_id
mae
rmse
directional_accuracy
n
target
```

Best rows:

```text
pair
horizon_months
best_model
best_rmse
random_walk_rmse
rmse_improvement_vs_random_walk
n
target
```

## Current Public Run

As of 2026-05-31, the public static artifact reports:

```text
run_id=20260531-161930-fx-rate-diff
pairs=EUR_USD, GBP_USD, USD_CAD, USD_JPY, USD_MXN
horizons=1, 3, 6
vintage_policy=latest_revised_snapshot
lookahead_status=not_real_time_vintage_safe
```

Random-walk/no-change baselines won nearly everywhere on RMSE in this snapshot;
ridge only slightly improved `USD_CAD` at `6M`.

## Deployment Notes

- `https://choir-ip.com/marco/` is live on Node A as a static Caddy route.
- The dynamic Python API is not yet deployed as a Node A service.
- GitHub Actions CI is enabled on push to `main`.
- Node A static deploy workflow exists but requires repo secrets:
  `NODE_A_HOST`, `NODE_A_USER`, `NODE_A_SSH_PRIVATE_KEY`.

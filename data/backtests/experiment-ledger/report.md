# Marco Experiment Ledger Report

Run ID: `ledger-77c68467739a7088`

Vintage policy: `latest_revised_snapshot`

Lookahead status: `not_real_time_vintage_safe`

Completed jobs: `3`

Failed jobs: `0`

Skipped jobs: `0`

Baseline gate status: `passed`

## Metrics

| Dataset | Pair | Target | Horizon | Model | N | RMSE | MAE | Directional Accuracy |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| current_fred_fx_rate_panel | USD_CAD | fx_return_6m | 6 | no_change | 231 | 0.059150 | 0.043340 | 0.000 |
| current_fred_fx_rate_panel | USD_CAD | fx_return_6m | 6 | random_walk | 231 | 0.059150 | 0.043340 | 0.000 |
| current_fred_fx_rate_panel | USD_CAD | fx_return_6m | 6 | ridge | 231 | 0.058701 | 0.043031 | 0.610 |

## Baseline Gates

```json
{
  "gates": [
    {
      "best_model": "ridge",
      "best_rmse": 0.05870072749649144,
      "dataset_id": "current_fred_fx_rate_panel",
      "horizon_months": 6,
      "missing_baselines": [],
      "no_change_rmse": 0.05915017088445292,
      "pair": "USD_CAD",
      "random_walk_rmse": 0.05915017088445292,
      "required_baselines": [
        "random_walk",
        "no_change"
      ],
      "status": "passed",
      "target": "fx_return_6m"
    }
  ],
  "plan_id": "plan-77c68467739a7088",
  "schema_version": "marco.baseline_gates.v1",
  "status": "passed"
}
```

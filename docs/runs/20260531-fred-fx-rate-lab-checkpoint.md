# FRED FX/Rate Lab Checkpoint

Date: 2026-05-31

Run ID: `20260531-161930-fx-rate-diff`

Status: foundation checkpoint complete

## What Shipped

- Python package `emf_macro`.
- CLI command `emf-macro run-fx-rate-lab`.
- Public FRED/FRED-MD source downloader with source hashing.
- Series catalog emission.
- Normalized macro fact emission.
- Monthly rates/FX panel emission as CSV and Parquet.
- Feature engine for nominal-rate differentials, inflation differentials,
  real-rate differentials, yield differentials, lagged FX returns, realized
  volatility, and FX-return targets.
- Walk-forward backtest runner.
- Baselines: random walk, no-change, rolling mean, carry differential,
  real-rate differential.
- First regularized model: ridge regression.
- Unit tests for parsing, FX direction signs, target construction, and
  walk-forward behavior.

## Commands Run

```sh
uv pip install --python .venv/bin/python pandas numpy scikit-learn pyarrow pytest
PYTHONPATH=src .venv/bin/python -m pytest
PYTHONPATH=src .venv/bin/python -m emf_macro.cli run-fx-rate-lab --root . --evaluation-start 2006-01 --horizons 1,3,6
uv pip install --python .venv/bin/python -e '.[dev]'
.venv/bin/emf-macro --help
.venv/bin/python -m pytest
```

## Verification

Tests:

```text
4 passed
```

Live validation:

```json
{
  "status": "passed",
  "panel_rows": 1349,
  "panel_columns": 23,
  "features_rows": 6745,
  "catalog_rows": 149,
  "prediction_rows": 17394,
  "pairs": ["EUR_USD", "GBP_USD", "USD_CAD", "USD_JPY", "USD_MXN"],
  "models": [
    "carry_diff",
    "no_change",
    "random_walk",
    "real_rate_diff",
    "ridge",
    "rolling_mean_36m"
  ],
  "required_baselines_present": true,
  "vintage_policy": "latest_revised_snapshot",
  "lookahead_status": "not_real_time_vintage_safe"
}
```

## Generated Artifacts

Generated files are intentionally ignored by git.

```text
data/derived/fred_fx_rates/source_manifest.json
data/derived/fred_fx_rates/series_catalog.jsonl
data/derived/fred_fx_rates/macro_facts.jsonl
data/derived/fred_fx_rates/panel_monthly.csv
data/derived/fred_fx_rates/panel_monthly.parquet
data/derived/fred_fx_rates/features_monthly.csv
data/derived/fred_fx_rates/features_monthly.parquet
data/derived/fred_fx_rates/feature_manifest.jsonl
data/derived/fred_fx_rates/validation_report.json
backtests/runs/20260531-161930-fx-rate-diff/config.json
backtests/runs/20260531-161930-fx-rate-diff/metrics.json
backtests/runs/20260531-161930-fx-rate-diff/predictions.jsonl
backtests/runs/20260531-161930-fx-rate-diff/report.md
```

## Model Result

The first result is intentionally not overclaimed.

Random-walk/no-change baselines won almost everywhere on RMSE. The only slight
RMSE improvement in this run was ridge on `USD_CAD:fx_return_6m`:

```text
USD_CAD:fx_return_6m
random_walk RMSE: 0.059150
ridge RMSE:       0.058701
```

Carry and real-rate differential baselines did not generally beat no-change on
RMSE. That is a useful platform result: the harness compared against hard
baselines and did not manufacture a false signal.

## Limitations

- This is a latest-revised-snapshot run, not a real-time vintage-safe backtest.
- Ordinary FRED pulls and FRED-MD current data may include revisions unavailable
  at the simulated forecast origin.
- Transaction costs, carry mechanics, and trading P&L are not modeled.
- FX direction conventions are recorded, but the first model family still needs
  deeper review before any economic interpretation.
- India/EM source availability remains untested.

## Next Path

1. Add ALFRED/vintage-aware pulls for a small subset of series.
2. Re-run one pair and horizon with strict `as_of` data cuts.
3. Add release-calendar metadata for CPI, policy rates, yields, and FX.
4. Add transaction-cost and carry-return accounting before any trading-style
   claims.
5. Map India/EM sources for policy rates, short rates, CPI, yields, FX,
   reserves, current account, external debt, and risk controls.

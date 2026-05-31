# FX/Rate Differential Backtest Report

Run ID: `20260531-161930-fx-rate-diff`

Vintage policy: `latest_revised_snapshot`

Lookahead status: `not_real_time_vintage_safe`

This run uses public FRED/FRED-MD latest snapshots. Walk-forward splits prevent target-period leakage inside the panel, but this is not a true real-time ALFRED/vintage backtest.

## Validation

```json
{
  "catalog_rows": 149,
  "features_rows": 6745,
  "lookahead_status": "not_real_time_vintage_safe",
  "models": [
    "carry_diff",
    "no_change",
    "random_walk",
    "real_rate_diff",
    "ridge",
    "rolling_mean_36m"
  ],
  "notes": [
    "FRED-MD current and ordinary FRED pulls are latest/revised snapshots.",
    "Backtests enforce walk-forward train windows, but are not ALFRED real-time vintage safe.",
    "Every FX target keeps explicit quote convention metadata in feature_manifest.jsonl."
  ],
  "pairs": [
    "EUR_USD",
    "GBP_USD",
    "USD_CAD",
    "USD_JPY",
    "USD_MXN"
  ],
  "panel_columns": 23,
  "panel_rows": 1349,
  "prediction_rows": 17394,
  "required_baselines_present": true,
  "status": "passed",
  "vintage_policy": "latest_revised_snapshot"
}
```

## Model Metrics

### EUR_USD:fx_return_1m

| Model | N | MAE | RMSE | Directional Accuracy |
| --- | ---: | ---: | ---: | ---: |
| carry_diff | 228 | 0.020030 | 0.026688 | 0.513 |
| no_change | 228 | 0.019966 | 0.026573 | 0.000 |
| random_walk | 228 | 0.019966 | 0.026573 | 0.000 |
| real_rate_diff | 228 | 0.020198 | 0.026872 | 0.439 |
| ridge | 228 | 0.020152 | 0.027526 | 0.583 |
| rolling_mean_36m | 228 | 0.020347 | 0.027094 | 0.465 |

### EUR_USD:fx_return_3m

| Model | N | MAE | RMSE | Directional Accuracy |
| --- | ---: | ---: | ---: | ---: |
| carry_diff | 228 | 0.034951 | 0.046323 | 0.491 |
| no_change | 228 | 0.034578 | 0.045708 | 0.000 |
| random_walk | 228 | 0.034578 | 0.045708 | 0.000 |
| real_rate_diff | 228 | 0.035751 | 0.047227 | 0.408 |
| ridge | 228 | 0.035631 | 0.046600 | 0.654 |
| rolling_mean_36m | 228 | 0.035402 | 0.047124 | 0.469 |

### EUR_USD:fx_return_6m

| Model | N | MAE | RMSE | Directional Accuracy |
| --- | ---: | ---: | ---: | ---: |
| carry_diff | 226 | 0.053712 | 0.068801 | 0.491 |
| no_change | 226 | 0.052950 | 0.067165 | 0.000 |
| random_walk | 226 | 0.052950 | 0.067165 | 0.000 |
| real_rate_diff | 226 | 0.055212 | 0.070871 | 0.416 |
| ridge | 226 | 0.050821 | 0.067623 | 0.650 |
| rolling_mean_36m | 226 | 0.054163 | 0.069843 | 0.522 |

### USD_JPY:fx_return_1m

| Model | N | MAE | RMSE | Directional Accuracy |
| --- | ---: | ---: | ---: | ---: |
| carry_diff | 147 | 0.018676 | 0.025129 | 0.479 |
| no_change | 147 | 0.018609 | 0.025099 | 0.000 |
| random_walk | 147 | 0.018609 | 0.025099 | 0.000 |
| real_rate_diff | 147 | 0.018511 | 0.025131 | 0.575 |
| ridge | 147 | 0.019532 | 0.025869 | 0.534 |
| rolling_mean_36m | 147 | 0.018541 | 0.025264 | 0.568 |

### USD_JPY:fx_return_3m

| Model | N | MAE | RMSE | Directional Accuracy |
| --- | ---: | ---: | ---: | ---: |
| carry_diff | 147 | 0.033438 | 0.045668 | 0.476 |
| no_change | 147 | 0.033320 | 0.045530 | 0.000 |
| random_walk | 147 | 0.033320 | 0.045530 | 0.000 |
| real_rate_diff | 147 | 0.033584 | 0.045819 | 0.551 |
| ridge | 147 | 0.035799 | 0.046409 | 0.565 |
| rolling_mean_36m | 147 | 0.034402 | 0.045637 | 0.544 |

### USD_JPY:fx_return_6m

| Model | N | MAE | RMSE | Directional Accuracy |
| --- | ---: | ---: | ---: | ---: |
| carry_diff | 147 | 0.051599 | 0.068093 | 0.449 |
| no_change | 147 | 0.050638 | 0.067707 | 0.000 |
| random_walk | 147 | 0.050638 | 0.067707 | 0.000 |
| real_rate_diff | 147 | 0.051432 | 0.068822 | 0.510 |
| ridge | 147 | 0.051360 | 0.068275 | 0.565 |
| rolling_mean_36m | 147 | 0.048713 | 0.068444 | 0.612 |

### GBP_USD:fx_return_1m

| Model | N | MAE | RMSE | Directional Accuracy |
| --- | ---: | ---: | ---: | ---: |
| carry_diff | 231 | 0.019806 | 0.025872 | 0.463 |
| no_change | 231 | 0.019675 | 0.025675 | 0.000 |
| random_walk | 231 | 0.019675 | 0.025675 | 0.000 |
| real_rate_diff | 231 | 0.019953 | 0.026056 | 0.424 |
| ridge | 231 | 0.020275 | 0.026316 | 0.467 |
| rolling_mean_36m | 231 | 0.019959 | 0.026159 | 0.476 |

### GBP_USD:fx_return_3m

| Model | N | MAE | RMSE | Directional Accuracy |
| --- | ---: | ---: | ---: | ---: |
| carry_diff | 231 | 0.036190 | 0.048643 | 0.450 |
| no_change | 231 | 0.035769 | 0.047732 | 0.000 |
| random_walk | 231 | 0.035769 | 0.047732 | 0.000 |
| real_rate_diff | 231 | 0.037052 | 0.049543 | 0.398 |
| ridge | 231 | 0.037915 | 0.050018 | 0.424 |
| rolling_mean_36m | 231 | 0.036340 | 0.048891 | 0.545 |

### GBP_USD:fx_return_6m

| Model | N | MAE | RMSE | Directional Accuracy |
| --- | ---: | ---: | ---: | ---: |
| carry_diff | 231 | 0.053105 | 0.072763 | 0.433 |
| no_change | 231 | 0.052268 | 0.070595 | 0.000 |
| random_walk | 231 | 0.052268 | 0.070595 | 0.000 |
| real_rate_diff | 231 | 0.055299 | 0.075094 | 0.338 |
| ridge | 231 | 0.057164 | 0.074893 | 0.429 |
| rolling_mean_36m | 231 | 0.054260 | 0.072925 | 0.511 |

### USD_CAD:fx_return_1m

| Model | N | MAE | RMSE | Directional Accuracy |
| --- | ---: | ---: | ---: | ---: |
| carry_diff | 231 | 0.018913 | 0.025710 | 0.506 |
| no_change | 231 | 0.018917 | 0.025636 | 0.000 |
| random_walk | 231 | 0.018917 | 0.025636 | 0.000 |
| real_rate_diff | 231 | 0.018912 | 0.025805 | 0.532 |
| ridge | 231 | 0.018840 | 0.025859 | 0.541 |
| rolling_mean_36m | 231 | 0.019047 | 0.026039 | 0.498 |

### USD_CAD:fx_return_3m

| Model | N | MAE | RMSE | Directional Accuracy |
| --- | ---: | ---: | ---: | ---: |
| carry_diff | 231 | 0.031388 | 0.042895 | 0.472 |
| no_change | 231 | 0.031098 | 0.042530 | 0.000 |
| random_walk | 231 | 0.031098 | 0.042530 | 0.000 |
| real_rate_diff | 231 | 0.031679 | 0.043332 | 0.446 |
| ridge | 231 | 0.031163 | 0.042579 | 0.554 |
| rolling_mean_36m | 231 | 0.031759 | 0.043385 | 0.489 |

### USD_CAD:fx_return_6m

| Model | N | MAE | RMSE | Directional Accuracy |
| --- | ---: | ---: | ---: | ---: |
| carry_diff | 231 | 0.044029 | 0.060028 | 0.450 |
| no_change | 231 | 0.043340 | 0.059150 | 0.000 |
| random_walk | 231 | 0.043340 | 0.059150 | 0.000 |
| real_rate_diff | 231 | 0.045037 | 0.061429 | 0.411 |
| ridge | 231 | 0.043031 | 0.058701 | 0.610 |
| rolling_mean_36m | 231 | 0.045582 | 0.060918 | 0.476 |

### USD_MXN:fx_return_1m

| Model | N | MAE | RMSE | Directional Accuracy |
| --- | ---: | ---: | ---: | ---: |
| carry_diff | 130 | 0.026000 | 0.035410 | 0.500 |
| no_change | 130 | 0.025899 | 0.034900 | 0.000 |
| random_walk | 130 | 0.025899 | 0.034900 | 0.000 |
| real_rate_diff | 130 | 0.025936 | 0.035261 | 0.508 |
| ridge | 130 | 0.026580 | 0.035957 | 0.485 |
| rolling_mean_36m | 130 | 0.026198 | 0.035416 | 0.477 |

### USD_MXN:fx_return_3m

| Model | N | MAE | RMSE | Directional Accuracy |
| --- | ---: | ---: | ---: | ---: |
| carry_diff | 130 | 0.046715 | 0.063094 | 0.500 |
| no_change | 130 | 0.046161 | 0.060645 | 0.000 |
| random_walk | 130 | 0.046161 | 0.060645 | 0.000 |
| real_rate_diff | 130 | 0.045974 | 0.062151 | 0.508 |
| ridge | 130 | 0.045754 | 0.061080 | 0.531 |
| rolling_mean_36m | 130 | 0.047707 | 0.062229 | 0.508 |

### USD_MXN:fx_return_6m

| Model | N | MAE | RMSE | Directional Accuracy |
| --- | ---: | ---: | ---: | ---: |
| carry_diff | 130 | 0.063901 | 0.084376 | 0.477 |
| no_change | 130 | 0.058707 | 0.077457 | 0.000 |
| random_walk | 130 | 0.058707 | 0.077457 | 0.000 |
| real_rate_diff | 130 | 0.061157 | 0.081431 | 0.454 |
| ridge | 130 | 0.060171 | 0.077600 | 0.538 |
| rolling_mean_36m | 130 | 0.062365 | 0.080082 | 0.500 |

## Next Vintage-Safe Path

- Replace selected FRED latest pulls with ALFRED vintages where available.
- Add release-date calendars for CPI, policy rates, yields, and FX observations.
- Re-run the same configs with an `as_of` data cut for each forecast origin.
- Build India/EM panels only after the vintage-safe protocol is explicit.

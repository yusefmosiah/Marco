# Macro Forecast Lab

FRED-MD path: `/Users/macbox/Library/CloudStorage/Dropbox/PhD/Research/code/Marco/data/fred-fx-rate-lab/raw/5d1b4008d3b4d5cb14883c395e8d1d80750b8b0a4f301e24c91f3f6710621663.csv`

Horizon: `6M`

Targets:

- `interest_rate`: FEDFUNDS level
- `inflation_yoy`: CPIAUCSL year-over-year log inflation
- `growth_proxy_yoy`: INDPRO year-over-year growth proxy, not true quarterly GDP

## Metrics

| Target | Model | N | MAE | RMSE | R-squared | Directional Accuracy |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| growth_proxy_yoy | linear_top5 | 232 | 3.342542 | 5.582424 | -0.537 | 0.517 |
| growth_proxy_yoy | no_change | 236 | 2.895239 | 4.823538 | -0.018 | 0.000 |
| growth_proxy_yoy | rolling_mean_12 | 236 | 3.806263 | 6.104677 | -0.631 | 0.419 |
| growth_proxy_yoy | var | 236 | 2.902502 | 4.666061 | 0.047 | 0.581 |
| growth_proxy_yoy | xgboost_top5 | 232 | 2.994023 | 4.321857 | 0.079 | 0.569 |
| inflation_yoy | linear_top5 | 232 | 1.569080 | 2.178159 | -0.369 | 0.629 |
| inflation_yoy | no_change | 236 | 1.093582 | 1.533581 | 0.319 | 0.000 |
| inflation_yoy | rolling_mean_12 | 236 | 1.413157 | 1.925997 | -0.075 | 0.538 |
| inflation_yoy | var | 236 | 1.136982 | 1.634396 | 0.226 | 0.475 |
| inflation_yoy | xgboost_top5 | 232 | 1.394895 | 2.005018 | -0.160 | 0.608 |
| interest_rate | linear_top5 | 232 | 0.473169 | 0.712539 | 0.867 | 0.607 |
| interest_rate | no_change | 236 | 0.445720 | 0.795910 | 0.834 | 0.000 |
| interest_rate | rolling_mean_12 | 236 | 0.838778 | 1.314795 | 0.547 | 0.305 |
| interest_rate | var | 236 | 0.753831 | 1.005646 | 0.735 | 0.633 |
| interest_rate | xgboost_top5 | 232 | 0.574618 | 0.752810 | 0.852 | 0.646 |

## Forecast Plots

- `interest_rate`: `/Users/macbox/Library/CloudStorage/Dropbox/PhD/Research/code/Marco/data/backtests/macro-forecast-lab/plots/interest_rate.svg`
- `inflation_yoy`: `/Users/macbox/Library/CloudStorage/Dropbox/PhD/Research/code/Marco/data/backtests/macro-forecast-lab/plots/inflation_yoy.svg`
- `growth_proxy_yoy`: `/Users/macbox/Library/CloudStorage/Dropbox/PhD/Research/code/Marco/data/backtests/macro-forecast-lab/plots/growth_proxy_yoy.svg`

## Chronos-2 Zero-Shot

```json
{
  "model_id": "chronos2_zero_shot",
  "status": "not_requested"
}
```

This run uses latest-revised FRED-MD data, not real-time vintage-safe data.

from __future__ import annotations

import numpy as np
import pandas as pd

from emf_macro.backtest import BacktestConfig, walk_forward_pair


def test_walk_forward_never_trains_on_current_target() -> None:
    periods = pd.date_range("2000-01-31", periods=140, freq="ME")
    rows = []
    for i, period in enumerate(periods):
        row = {
            "period": period,
            "pair": "TEST",
            "fx_return_1m": i / 1000.0,
            "carry_pred_1m": 0.0,
            "real_rate_pred_1m": 0.0,
            "nominal_rate_diff": float(i),
            "inflation_diff": 0.1,
            "real_rate_diff": float(i) - 0.1,
            "yield_10y_diff": 0.2,
            "yield_curve_slope_local": 0.3,
            "yield_curve_slope_us": 0.4,
            "fx_return_1m_lag": 0.01,
            "fx_return_3m_lag": 0.02,
            "fx_vol_12m": 0.03,
        }
        rows.append(row)
    features = pd.DataFrame(rows)
    predictions, summary = walk_forward_pair(
        features,
        BacktestConfig(
            pair="TEST",
            target="fx_return_1m",
            horizon_months=1,
            evaluation_start="2008-01",
            train_min_months=84,
        ),
    )
    assert not predictions.empty
    first_origin = predictions["forecast_origin"].min()
    assert first_origin >= "2008-01"
    assert {"random_walk", "no_change", "carry_diff", "real_rate_diff", "ridge"}.issubset(
        set(predictions["model_id"])
    )
    assert summary["metrics"]["random_walk"]["n"] > 0

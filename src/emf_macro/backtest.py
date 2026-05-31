from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


FEATURE_COLUMNS = [
    "nominal_rate_diff",
    "inflation_diff",
    "real_rate_diff",
    "yield_10y_diff",
    "yield_curve_slope_local",
    "yield_curve_slope_us",
    "fx_return_1m_lag",
    "fx_return_3m_lag",
    "fx_vol_12m",
]


@dataclass(frozen=True)
class BacktestConfig:
    pair: str
    target: str
    horizon_months: int
    evaluation_start: str
    train_min_months: int = 84
    train_window: str = "expanding"
    vintage_policy: str = "latest_revised_snapshot"
    lookahead_status: str = "not_real_time_vintage_safe"


def metrics(actual: Iterable[float], predicted: Iterable[float]) -> dict:
    a = np.asarray(list(actual), dtype=float)
    p = np.asarray(list(predicted), dtype=float)
    err = p - a
    nonzero = a != 0
    direction = np.sign(a[nonzero]) == np.sign(p[nonzero])
    return {
        "n": int(len(a)),
        "mae": float(np.mean(np.abs(err))) if len(a) else math.nan,
        "rmse": float(np.sqrt(np.mean(err * err))) if len(a) else math.nan,
        "directional_accuracy": float(np.mean(direction)) if len(direction) else math.nan,
    }


def walk_forward_pair(features: pd.DataFrame, config: BacktestConfig) -> tuple[pd.DataFrame, dict]:
    pair_df = features[features["pair"] == config.pair].copy()
    pair_df["period"] = pd.to_datetime(pair_df["period"])
    pair_df = pair_df.sort_values("period")
    cols = ["period", config.target, f"carry_pred_{config.horizon_months}m", f"real_rate_pred_{config.horizon_months}m", *FEATURE_COLUMNS]
    pair_df = pair_df[cols].dropna().reset_index(drop=True)
    eval_start = pd.Timestamp(config.evaluation_start)

    rows: list[dict] = []
    for idx, row in pair_df.iterrows():
        origin = row["period"]
        if origin < eval_start or idx < config.train_min_months:
            continue
        train = pair_df.iloc[:idx].dropna()
        if train.empty:
            continue
        y_train = train[config.target]
        x_train = train[FEATURE_COLUMNS]
        x_now = row[FEATURE_COLUMNS].to_frame().T

        rolling_mean = float(y_train.tail(36).mean())
        ridge = make_pipeline(StandardScaler(), Ridge(alpha=10.0))
        ridge.fit(x_train, y_train)
        ridge_pred = float(ridge.predict(x_now)[0])

        actual = float(row[config.target])
        rows.extend(
            [
                _prediction_row(config, origin, "random_walk", actual, 0.0),
                _prediction_row(config, origin, "no_change", actual, 0.0),
                _prediction_row(config, origin, "rolling_mean_36m", actual, rolling_mean),
                _prediction_row(config, origin, "carry_diff", actual, float(row[f"carry_pred_{config.horizon_months}m"])),
                _prediction_row(config, origin, "real_rate_diff", actual, float(row[f"real_rate_pred_{config.horizon_months}m"])),
                _prediction_row(config, origin, "ridge", actual, ridge_pred),
            ]
        )

    predictions = pd.DataFrame(rows)
    metric_rows = {
        model: metrics(group["actual"], group["prediction"])
        for model, group in predictions.groupby("model_id")
    }
    return predictions, {
        "config": asdict(config),
        "metrics": metric_rows,
        "baselines": ["random_walk", "no_change", "rolling_mean_36m", "carry_diff", "real_rate_diff"],
        "advanced_models": ["ridge"],
    }


def _prediction_row(config: BacktestConfig, origin: pd.Timestamp, model: str, actual: float, prediction: float) -> dict:
    return {
        "pair": config.pair,
        "target": config.target,
        "horizon_months": config.horizon_months,
        "forecast_origin": origin.strftime("%Y-%m"),
        "target_period": (origin + pd.offsets.MonthEnd(config.horizon_months)).strftime("%Y-%m"),
        "model_id": model,
        "actual": actual,
        "prediction": prediction,
        "error": prediction - actual,
        "vintage_policy": config.vintage_policy,
        "lookahead_status": config.lookahead_status,
    }

from __future__ import annotations

import numpy as np
import pandas as pd

from .catalog import PAIR_SPECS, US_CPI, US_RATE, US_YIELD_10Y, PairSpec


def cpi_yoy(series: pd.Series) -> pd.Series:
    return 100.0 * np.log(series / series.shift(12))


def annualized_vol(series: pd.Series, window: int = 12) -> pd.Series:
    return series.rolling(window).std() * np.sqrt(12)


def quote_sign(pair: PairSpec) -> int:
    return 1 if pair.quote_convention == "USD_PER_FOREIGN" else -1


def build_pair_features(panel: pd.DataFrame, horizons: tuple[int, ...] = (1, 3, 6)) -> tuple[pd.DataFrame, list[dict]]:
    frames: list[pd.DataFrame] = []
    manifest: list[dict] = []

    us_rate = panel[US_RATE.series_id]
    us_inflation = cpi_yoy(panel[US_CPI.series_id])
    us_yield = panel[US_YIELD_10Y.series_id]

    for pair in PAIR_SPECS:
        fx = panel[pair.fx.series_id]
        local_rate = panel[pair.local_rate.series_id]
        local_inflation = cpi_yoy(panel[pair.local_cpi.series_id])
        local_yield = panel[pair.local_yield_10y.series_id]
        sign = quote_sign(pair)

        df = pd.DataFrame(index=panel.index)
        df["pair"] = pair.pair
        df["country"] = pair.country
        df["spot_fx"] = fx
        df["local_rate"] = local_rate
        df["us_rate"] = us_rate
        df["nominal_rate_diff"] = local_rate - us_rate
        df["local_cpi_yoy"] = local_inflation
        df["us_cpi_yoy"] = us_inflation
        df["inflation_diff"] = local_inflation - us_inflation
        df["real_rate_diff"] = df["nominal_rate_diff"] - df["inflation_diff"]
        df["local_yield_10y"] = local_yield
        df["us_yield_10y"] = us_yield
        df["yield_10y_diff"] = local_yield - us_yield
        df["yield_curve_slope_local"] = local_yield - local_rate
        df["yield_curve_slope_us"] = us_yield - us_rate
        df["fx_return_1m_lag"] = np.log(fx / fx.shift(1))
        df["fx_return_3m_lag"] = np.log(fx / fx.shift(3))
        df["fx_vol_12m"] = annualized_vol(df["fx_return_1m_lag"], 12)
        df["carry_signal_annual"] = sign * df["nominal_rate_diff"] / 100.0
        df["real_rate_signal_annual"] = sign * df["real_rate_diff"] / 100.0
        df["next_rate_change_1m"] = local_rate.shift(-1) - local_rate
        df["next_rate_change_direction_1m"] = np.sign(df["next_rate_change_1m"])

        for horizon in horizons:
            target = np.log(fx.shift(-horizon) / fx)
            df[f"fx_return_{horizon}m"] = target
            df[f"random_walk_pred_{horizon}m"] = 0.0
            df[f"carry_pred_{horizon}m"] = df["carry_signal_annual"] * horizon / 12.0
            df[f"real_rate_pred_{horizon}m"] = df["real_rate_signal_annual"] * horizon / 12.0
            manifest.extend(
                [
                    {
                        "pair": pair.pair,
                        "feature": f"fx_return_{horizon}m",
                        "kind": "target",
                        "formula": f"log(spot_fx[t+{horizon}] / spot_fx[t])",
                        "positive_return_means": pair.positive_return_means,
                        "quote_convention": pair.quote_convention,
                        "vintage_policy": "latest_revised_snapshot",
                    },
                    {
                        "pair": pair.pair,
                        "feature": f"carry_pred_{horizon}m",
                        "kind": "baseline_prediction",
                        "formula": f"quote_sign * nominal_rate_diff / 100 * {horizon}/12",
                        "quote_sign": sign,
                        "vintage_policy": "latest_revised_snapshot",
                    },
                ]
            )

        frames.append(df.reset_index(names="period"))

    return pd.concat(frames, ignore_index=True), manifest

from __future__ import annotations

import numpy as np
import pandas as pd

from emf_macro.catalog import PAIR_SPECS
from emf_macro.features import build_pair_features, quote_sign


def test_quote_sign_preserves_fx_direction_convention() -> None:
    signs = {pair.pair: quote_sign(pair) for pair in PAIR_SPECS}
    assert signs["EUR_USD"] == 1
    assert signs["GBP_USD"] == 1
    assert signs["USD_JPY"] == -1
    assert signs["USD_CAD"] == -1
    assert signs["USD_MXN"] == -1


def test_target_uses_future_spot_without_feature_leakage() -> None:
    idx = pd.date_range("2020-01-31", periods=30, freq="ME")
    data = {}
    for pair in PAIR_SPECS:
        data[pair.fx.series_id] = np.linspace(1.0, 2.0, len(idx))
        data[pair.local_rate.series_id] = np.full(len(idx), 5.0)
        data[pair.local_cpi.series_id] = np.linspace(100.0, 112.0, len(idx))
        data[pair.local_yield_10y.series_id] = np.full(len(idx), 6.0)
    data["FEDFUNDS"] = np.full(len(idx), 2.0)
    data["CPIAUCSL"] = np.linspace(100.0, 106.0, len(idx))
    data["DGS10"] = np.full(len(idx), 3.0)
    features, manifest = build_pair_features(pd.DataFrame(data, index=idx), horizons=(3,))
    eur = features[features["pair"] == "EUR_USD"].set_index("period")
    expected = np.log(eur["spot_fx"].shift(-3) / eur["spot_fx"])
    pd.testing.assert_series_equal(eur["fx_return_3m"], expected, check_names=False)
    assert any(row["feature"] == "fx_return_3m" and row["kind"] == "target" for row in manifest)

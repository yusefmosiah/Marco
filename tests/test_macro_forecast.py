from __future__ import annotations

from pathlib import Path

import pandas as pd

from emf_macro.macro_forecast import (
    MacroForecastConfig,
    build_macro_target_panel,
    load_fred_md,
    run_macro_forecast_lab,
    walk_forward_var_comparison,
)


def test_build_macro_target_panel_creates_interest_inflation_and_growth_targets(tmp_path: Path) -> None:
    path = write_fred_md(tmp_path)
    fred_md = load_fred_md(path)

    panel = build_macro_target_panel(fred_md)

    assert list(panel.columns) == ["interest_rate", "inflation_yoy", "growth_proxy_yoy"]
    assert panel.index.min() == pd.Timestamp("2001-01-31")
    assert panel["interest_rate"].notna().all()


def test_walk_forward_var_comparison_emits_baselines_and_var(tmp_path: Path) -> None:
    panel = build_macro_target_panel(load_fred_md(write_fred_md(tmp_path)))

    predictions = walk_forward_var_comparison(
        panel,
        horizon_months=3,
        evaluation_start="2008-01",
        train_min_months=84,
        var_lags=3,
    )

    assert sorted(predictions["model_id"].unique().tolist()) == ["no_change", "rolling_mean_12", "var"]
    assert sorted(predictions["target"].unique().tolist()) == ["growth_proxy_yoy", "inflation_yoy", "interest_rate"]
    assert {"actual", "prediction", "error", "actual_change", "predicted_change"}.issubset(predictions.columns)


def test_run_macro_forecast_lab_writes_artifacts(tmp_path: Path) -> None:
    fred_md_path = write_fred_md(tmp_path)

    summary = run_macro_forecast_lab(
        MacroForecastConfig(
            root=tmp_path,
            fred_md_path=fred_md_path,
            output_dir=tmp_path / "macro-run",
            evaluation_start="2008-01",
            horizon_months=3,
            train_min_months=84,
            var_lags=3,
        )
    )

    assert summary["schema_version"] == "marco.macro_forecast_lab.v1"
    assert "linear_top5" in summary["models"]
    assert {"no_change", "rolling_mean_12", "var"}.issubset(set(summary["models"]))
    assert all("r_squared" in row for row in summary["metrics"])
    assert summary["chronos2_zero_shot"]["status"] == "not_requested"
    assert (tmp_path / "macro-run" / "macro_targets_monthly.csv").exists()
    assert (tmp_path / "macro-run" / "predictions.jsonl").exists()
    assert (tmp_path / "macro-run" / "metrics.json").exists()
    assert (tmp_path / "macro-run" / "summary.json").exists()
    assert (tmp_path / "macro-run" / "report.md").exists()
    assert (tmp_path / "macro-run" / "plots" / "interest_rate.svg").exists()
    assert (tmp_path / "macro-run" / "plots" / "inflation_yoy.svg").exists()
    assert (tmp_path / "macro-run" / "plots" / "growth_proxy_yoy.svg").exists()


def write_fred_md(root: Path) -> Path:
    periods = pd.date_range("2000-01-31", periods=180, freq="ME")
    rows = [
        {
            "sasdate": "Transform:",
            "FEDFUNDS": 2,
            "CPIAUCSL": 6,
            "INDPRO": 5,
            "PAYEMS": 5,
            "UNRATE": 2,
            "GS10": 2,
            "M2SL": 6,
            "PCEPI": 6,
            "RETAILx": 5,
        }
    ]
    for idx, period in enumerate(periods):
        rows.append(
            {
                "sasdate": period.strftime("%-m/%-d/%Y"),
                "FEDFUNDS": 2.0 + 0.01 * idx,
                "CPIAUCSL": 100.0 + idx,
                "INDPRO": 80.0 + 0.5 * idx,
                "PAYEMS": 1000.0 + 2.0 * idx,
                "UNRATE": 5.0 + 0.01 * ((idx % 24) - 12),
                "GS10": 3.0 + 0.005 * idx,
                "M2SL": 500.0 + 1.5 * idx,
                "PCEPI": 95.0 + 0.8 * idx,
                "RETAILx": 200.0 + 1.1 * idx,
            }
        )
    path = root / "fred_md.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path

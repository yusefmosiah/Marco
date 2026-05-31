from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from emf_macro.economic_model_agent import run_economic_model_agent


def test_economic_model_agent_returns_filtered_metrics_and_latest_forecasts(tmp_path: Path) -> None:
    write_macro_forecast_artifacts(tmp_path)

    payload = run_economic_model_agent(tmp_path, target="interest_rate", model_id="xgboost_top5")

    assert payload["schema_version"] == "marco.economic_model_agent.v1"
    assert payload["agent_id"] == "economic_modeling_agent"
    assert payload["metrics"] == [
        {
            "target": "interest_rate",
            "model_id": "xgboost_top5",
            "n": 2,
            "rmse": 0.2,
            "r_squared": 0.9,
        }
    ]
    assert payload["latest_forecasts"][0]["forecast_origin"] == "2026-02"
    assert payload["latest_forecasts"][0]["prediction"] == 4.2
    latest = tmp_path / "data" / "agents" / "latest" / "economic_modeling_agent.md"
    assert latest.exists()
    assert "schema_version: marco.agent_handoff.v1" in latest.read_text(encoding="utf-8")
    assert payload["handoff"]["latest_path"] == "data/agents/latest/economic_modeling_agent.md"


def write_macro_forecast_artifacts(root: Path) -> None:
    output_dir = root / "data" / "backtests" / "macro-forecast-lab"
    output_dir.mkdir(parents=True)
    summary = {
        "schema_version": "marco.macro_forecast_lab.v1",
        "horizon_months": 6,
        "vintage_policy": "latest_revised_snapshot",
        "lookahead_status": "not_real_time_vintage_safe",
        "targets": {"interest_rate": "FEDFUNDS level"},
        "models": ["xgboost_top5"],
        "output_dir": str(output_dir),
        "plots": {"interest_rate": str(output_dir / "plots" / "interest_rate.svg")},
        "metrics": [
            {
                "target": "interest_rate",
                "model_id": "xgboost_top5",
                "n": 2,
                "rmse": 0.2,
                "r_squared": 0.9,
            },
            {
                "target": "inflation_yoy",
                "model_id": "xgboost_top5",
                "n": 2,
                "rmse": 1.0,
                "r_squared": 0.1,
            },
        ],
    }
    (output_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    pd.DataFrame(
        [
            {
                "target": "interest_rate",
                "model_id": "xgboost_top5",
                "forecast_origin": "2026-01",
                "target_period": "2026-07",
                "actual": 4.0,
                "prediction": 4.1,
                "error": 0.1,
                "selected_factors": ["FEDFUNDS"],
            },
            {
                "target": "interest_rate",
                "model_id": "xgboost_top5",
                "forecast_origin": "2026-02",
                "target_period": "2026-08",
                "actual": 4.0,
                "prediction": 4.2,
                "error": 0.2,
                "selected_factors": ["FEDFUNDS"],
            },
        ]
    ).to_json(output_dir / "predictions.jsonl", orient="records", lines=True)

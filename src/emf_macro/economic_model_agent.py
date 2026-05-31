from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .macro_forecast import MacroForecastConfig, run_macro_forecast_lab


AGENT_SCHEMA = "marco.economic_model_agent.v1"


def run_economic_model_agent(
    root: Path,
    *,
    horizon_months: int = 6,
    target: str | None = None,
    model_id: str | None = None,
    refresh: bool = False,
) -> dict[str, Any]:
    summary_path = root / "data" / "backtests" / "macro-forecast-lab" / "summary.json"
    if refresh or not summary_path.exists():
        summary = run_macro_forecast_lab(
            MacroForecastConfig(
                root=root,
                horizon_months=horizon_months,
            )
        )
    else:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))

    metrics = filter_rows(summary.get("metrics", []), target=target, model_id=model_id)
    predictions = load_latest_predictions(Path(summary["output_dir"]) / "predictions.jsonl", target=target, model_id=model_id)
    return {
        "schema_version": AGENT_SCHEMA,
        "agent_id": "economic_model_agent",
        "name": "Marco Economic Model Agent",
        "purpose": "Provide structured macro forecasts for downstream research and news agents.",
        "inputs": {
            "source_data": "FRED-MD latest-revised snapshot",
            "horizon_months": summary["horizon_months"],
            "target_filter": target,
            "model_filter": model_id,
        },
        "caveats": [
            "Uses latest-revised FRED-MD data, not real-time ALFRED vintages.",
            "growth_proxy_yoy is industrial-production YoY, not true quarterly GDP.",
            "Forecasts must be interpreted against baseline metrics.",
        ],
        "summary": {
            "vintage_policy": summary["vintage_policy"],
            "lookahead_status": summary["lookahead_status"],
            "targets": summary["targets"],
            "models": summary["models"],
            "output_dir": summary["output_dir"],
            "plots": summary.get("plots", {}),
        },
        "metrics": metrics,
        "latest_forecasts": predictions,
    }


def filter_rows(rows: list[dict[str, Any]], *, target: str | None, model_id: str | None) -> list[dict[str, Any]]:
    filtered = rows
    if target:
        filtered = [row for row in filtered if row.get("target") == target]
    if model_id:
        filtered = [row for row in filtered if row.get("model_id") == model_id]
    return filtered


def load_latest_predictions(path: Path, *, target: str | None, model_id: str | None) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    df = pd.read_json(path, lines=True)
    if target:
        df = df[df["target"] == target]
    if model_id:
        df = df[df["model_id"] == model_id]
    if df.empty:
        return []
    latest = df.sort_values(["target", "model_id", "forecast_origin"]).groupby(["target", "model_id"], as_index=False).tail(1)
    columns = [
        "target",
        "model_id",
        "forecast_origin",
        "target_period",
        "actual",
        "prediction",
        "error",
        "selected_factors",
    ]
    available_columns = [column for column in columns if column in latest.columns]
    return latest[available_columns].sort_values(["target", "model_id"]).to_dict(orient="records")

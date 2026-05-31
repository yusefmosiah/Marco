from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from .backtest import BacktestConfig, walk_forward_pair
from .catalog import PAIR_SPECS, selected_series
from .features import build_pair_features
from .fred import (
    catalog_row,
    fetch_fred_md,
    fetch_fred_series,
    fred_md_catalog_rows,
    parse_fred_md,
    parse_fred_series,
)
from .io import ensure_dir, write_json, write_jsonl, write_manifest
from .normalize import facts_from_frame, fred_md_facts


def run_fx_rate_lab(root: Path, evaluation_start: str = "2006-01", horizons: tuple[int, ...] = (1, 3, 6)) -> dict:
    raw_dir = root / "data" / "raw" / "fred_fx_rates"
    derived_dir = root / "data" / "derived" / "fred_fx_rates"
    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-fx-rate-diff")
    run_dir = root / "backtests" / "runs" / run_id
    ensure_dir(derived_dir)
    ensure_dir(run_dir)

    records = []
    fred_md_record = fetch_fred_md(raw_dir)
    records.append(fred_md_record)
    fred_md, tcodes = parse_fred_md(fred_md_record)

    series_frames = []
    catalog_rows = fred_md_catalog_rows(tcodes, fred_md_record)
    specs = selected_series()
    spec_by_id = {spec.series_id: spec for spec in specs}
    source_snapshots = {}
    for spec in specs:
        record = fetch_fred_series(spec, raw_dir)
        records.append(record)
        source_snapshots[spec.series_id] = record.sha256
        catalog_rows.append(catalog_row(spec, record))
        series_frames.append(parse_fred_series(record, spec))

    write_manifest(derived_dir / "source_manifest.json", records)
    write_jsonl(derived_dir / "series_catalog.jsonl", catalog_rows)

    selected_panel = pd.concat(series_frames, axis=1).sort_index()
    selected_panel = selected_panel.loc[:, ~selected_panel.columns.duplicated()]
    features, feature_manifest = build_pair_features(selected_panel, horizons=horizons)

    facts = fred_md_facts(fred_md, fred_md_record.sha256)
    facts.extend(facts_from_frame(selected_panel, spec_by_id, source_snapshots))
    write_jsonl(derived_dir / "macro_facts.jsonl", facts)
    write_jsonl(derived_dir / "feature_manifest.jsonl", feature_manifest)

    selected_panel.to_csv(derived_dir / "panel_monthly.csv", index_label="period")
    selected_panel.to_parquet(derived_dir / "panel_monthly.parquet")
    features.to_csv(derived_dir / "features_monthly.csv", index=False)
    features.to_parquet(derived_dir / "features_monthly.parquet")

    all_predictions = []
    summaries = {}
    for pair in PAIR_SPECS:
        for horizon in horizons:
            target = f"fx_return_{horizon}m"
            config = BacktestConfig(
                pair=pair.pair,
                target=target,
                horizon_months=horizon,
                evaluation_start=evaluation_start,
            )
            predictions, summary = walk_forward_pair(features, config)
            if predictions.empty:
                continue
            all_predictions.append(predictions)
            summaries[f"{pair.pair}:{target}"] = summary

    predictions_df = pd.concat(all_predictions, ignore_index=True)
    predictions_df.to_json(run_dir / "predictions.jsonl", orient="records", lines=True)
    metrics_payload = {
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "vintage_policy": "latest_revised_snapshot",
        "lookahead_status": "not_real_time_vintage_safe",
        "summaries": summaries,
    }
    write_json(run_dir / "metrics.json", metrics_payload)
    write_json(run_dir / "config.json", {"evaluation_start": evaluation_start, "horizons": list(horizons)})
    write_json(run_dir / "feature_manifest.json", feature_manifest)

    validation = validate_outputs(selected_panel, features, predictions_df, catalog_rows)
    write_json(derived_dir / "validation_report.json", validation)
    report = render_report(run_id, validation, metrics_payload)
    (run_dir / "report.md").write_text(report, encoding="utf-8")
    write_json(derived_dir / "latest_run.json", {"run_id": run_id, "run_dir": str(run_dir)})
    return {"run_id": run_id, "derived_dir": str(derived_dir), "run_dir": str(run_dir), "validation": validation}


def validate_outputs(panel: pd.DataFrame, features: pd.DataFrame, predictions: pd.DataFrame, catalog_rows: list[dict]) -> dict:
    required_models = {"random_walk", "no_change", "rolling_mean_36m", "carry_diff", "real_rate_diff"}
    model_ids = set(predictions["model_id"].unique())
    return {
        "status": "passed" if required_models.issubset(model_ids) else "failed",
        "panel_rows": int(len(panel)),
        "panel_columns": int(len(panel.columns)),
        "features_rows": int(len(features)),
        "catalog_rows": int(len(catalog_rows)),
        "prediction_rows": int(len(predictions)),
        "pairs": sorted(features["pair"].dropna().unique().tolist()),
        "models": sorted(model_ids),
        "required_baselines_present": sorted(required_models.issubset(model_ids) for _ in [0])[0],
        "vintage_policy": "latest_revised_snapshot",
        "lookahead_status": "not_real_time_vintage_safe",
        "notes": [
            "FRED-MD current and ordinary FRED pulls are latest/revised snapshots.",
            "Backtests enforce walk-forward train windows, but are not ALFRED real-time vintage safe.",
            "Every FX target keeps explicit quote convention metadata in feature_manifest.jsonl.",
        ],
    }


def render_report(run_id: str, validation: dict, metrics_payload: dict) -> str:
    lines = [
        f"# FX/Rate Differential Backtest Report",
        "",
        f"Run ID: `{run_id}`",
        "",
        "Vintage policy: `latest_revised_snapshot`",
        "",
        "Lookahead status: `not_real_time_vintage_safe`",
        "",
        "This run uses public FRED/FRED-MD latest snapshots. Walk-forward splits prevent target-period leakage inside the panel, but this is not a true real-time ALFRED/vintage backtest.",
        "",
        "## Validation",
        "",
        "```json",
        json.dumps(validation, indent=2, sort_keys=True),
        "```",
        "",
        "## Model Metrics",
        "",
    ]
    for key, summary in metrics_payload["summaries"].items():
        lines.append(f"### {key}")
        lines.append("")
        lines.append("| Model | N | MAE | RMSE | Directional Accuracy |")
        lines.append("| --- | ---: | ---: | ---: | ---: |")
        for model, metric in sorted(summary["metrics"].items()):
            lines.append(
                f"| {model} | {metric['n']} | {metric['mae']:.6f} | {metric['rmse']:.6f} | {metric['directional_accuracy']:.3f} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Next Vintage-Safe Path",
            "",
            "- Replace selected FRED latest pulls with ALFRED vintages where available.",
            "- Add release-date calendars for CPI, policy rates, yields, and FX observations.",
            "- Re-run the same configs with an `as_of` data cut for each forecast origin.",
            "- Build India/EM panels only after the vintage-safe protocol is explicit.",
        ]
    )
    return "\n".join(lines) + "\n"

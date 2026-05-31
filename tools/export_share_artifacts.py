#!/usr/bin/env python3
"""Export small shareable artifacts from a generated FX/rate lab run."""

from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path


MODELS_ORDER = [
    "random_walk",
    "no_change",
    "rolling_mean_36m",
    "carry_diff",
    "real_rate_diff",
    "ridge",
]


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "usage: export_share_artifacts.py RUN_DIR DERIVED_DIR OUTPUT_DIR",
            file=sys.stderr,
        )
        return 2

    run_dir = Path(sys.argv[1])
    derived_dir = Path(sys.argv[2])
    out_dir = Path(sys.argv[3])
    out_dir.mkdir(parents=True, exist_ok=True)

    metrics = load_json(run_dir / "metrics.json")
    validation = load_json(derived_dir / "validation_report.json")
    config = load_json(run_dir / "config.json")

    rows: list[dict] = []
    best_by_rmse: list[dict] = []
    for target_key, summary in sorted(metrics["summaries"].items()):
        pair, target = target_key.split(":")
        horizon = int(target.removeprefix("fx_return_").removesuffix("m"))
        metric_rows = []
        for model_id, model_metrics in summary["metrics"].items():
            row = {
                "pair": pair,
                "target": target,
                "horizon_months": horizon,
                "model_id": model_id,
                "n": model_metrics["n"],
                "mae": model_metrics["mae"],
                "rmse": model_metrics["rmse"],
                "directional_accuracy": model_metrics["directional_accuracy"],
            }
            rows.append(row)
            metric_rows.append(row)
        best = min(metric_rows, key=lambda r: r["rmse"])
        random_walk = next(r for r in metric_rows if r["model_id"] == "random_walk")
        best_by_rmse.append(
            {
                "pair": pair,
                "target": target,
                "horizon_months": horizon,
                "best_model": best["model_id"],
                "best_rmse": best["rmse"],
                "random_walk_rmse": random_walk["rmse"],
                "rmse_improvement_vs_random_walk": random_walk["rmse"] - best["rmse"],
                "n": best["n"],
            }
        )

    pairs = sorted({row["pair"] for row in rows})
    horizons = sorted({row["horizon_months"] for row in rows})
    models = [model for model in MODELS_ORDER if any(row["model_id"] == model for row in rows)]

    summary_payload = {
        "run_id": metrics["run_id"],
        "created_at": metrics["created_at"],
        "vintage_policy": metrics["vintage_policy"],
        "lookahead_status": metrics["lookahead_status"],
        "config": config,
        "validation": validation,
        "pairs": pairs,
        "horizons": horizons,
        "models": models,
        "metrics": rows,
        "best_by_rmse": best_by_rmse,
        "headline": {
            "status": validation["status"],
            "panel_rows": validation["panel_rows"],
            "panel_columns": validation["panel_columns"],
            "features_rows": validation["features_rows"],
            "prediction_rows": validation["prediction_rows"],
            "model_result": (
                "Random-walk/no-change baselines won almost everywhere on RMSE; "
                "ridge only slightly improved USD_CAD at 6M in this snapshot run."
            ),
        },
    }

    (out_dir / "summary.json").write_text(
        json.dumps(summary_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "validation.json").write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    shutil.copyfile(run_dir / "report.md", out_dir / "report.md")

    with (out_dir / "model_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with (out_dir / "best_by_rmse.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(best_by_rmse[0].keys()))
        writer.writeheader()
        writer.writerows(best_by_rmse)

    print(json.dumps({"output_dir": str(out_dir), "rows": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

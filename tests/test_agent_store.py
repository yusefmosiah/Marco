from __future__ import annotations

import json
from pathlib import Path

from emf_macro.agent_store import ArtifactStore


def write_summary(root: Path, run_id: str) -> None:
    run_dir = root / "artifacts" / "fred-fx-rate-lab" / run_id
    run_dir.mkdir(parents=True)
    summary = {
        "run_id": run_id,
        "created_at": "2026-05-31T00:00:00+00:00",
        "vintage_policy": "latest_revised_snapshot",
        "lookahead_status": "not_real_time_vintage_safe",
        "config": {"horizons": [1, 6]},
        "headline": {"status": "passed", "prediction_rows": 2},
        "pairs": ["USD_CAD"],
        "horizons": [1, 6],
        "models": ["random_walk", "ridge"],
        "metrics": [
            {
                "pair": "USD_CAD",
                "horizon_months": 6,
                "model_id": "ridge",
                "rmse": 0.4,
                "mae": 0.3,
                "directional_accuracy": 0.55,
                "n": 10,
                "target": "fx_return_6m",
            },
            {
                "pair": "USD_CAD",
                "horizon_months": 1,
                "model_id": "random_walk",
                "rmse": 0.2,
                "mae": 0.1,
                "directional_accuracy": 0.5,
                "n": 10,
                "target": "fx_return_1m",
            },
        ],
        "best_by_rmse": [
            {
                "pair": "USD_CAD",
                "horizon_months": 6,
                "best_model": "ridge",
                "best_rmse": 0.4,
                "random_walk_rmse": 0.42,
                "rmse_improvement_vs_random_walk": 0.02,
                "n": 10,
                "target": "fx_return_6m",
            }
        ],
    }
    (run_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (run_dir / "report.md").write_text("# Report\n", encoding="utf-8")


def test_artifact_store_lists_and_filters_runs(tmp_path: Path) -> None:
    write_summary(tmp_path, "20260101-000000-fx-rate-diff")
    store = ArtifactStore(tmp_path)

    runs = store.list_runs()
    assert runs[0]["run_id"] == "20260101-000000-fx-rate-diff"
    assert len(runs[0]["summary_sha256"]) == 64

    metrics = store.filter_metrics("latest", pair="USD_CAD", horizon_months=6)
    assert [row["model_id"] for row in metrics] == ["ridge"]

    best = store.filter_best("latest", pair="USD_CAD", horizon_months=6)
    assert best[0]["best_model"] == "ridge"

    context = store.agent_context("latest", public_base_url="https://example.test/marco")
    assert context["schema_version"] == "marco.agent_context.v1"
    assert context["active_run_id"] == "20260101-000000-fx-rate-diff"
    assert context["public_urls"]["active_run"].endswith("/v1/runs/20260101-000000-fx-rate-diff")

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from emf_macro.experiments import stable_job_id, stable_plan_id
from emf_macro.runner import RunnerConfig, run_experiment_plan


def test_runner_writes_atomic_job_artifacts_and_baseline_gates(tmp_path: Path) -> None:
    features_path = write_features(tmp_path, ["USD_CAD"])
    plan = make_plan(["USD_CAD"], ["random_walk", "no_change", "ridge"])

    result = run_experiment_plan(
        RunnerConfig(
            root=tmp_path,
            plan=plan,
            features_path=features_path,
            output_dir=tmp_path / "run",
            evaluation_start="2008-01",
            train_min_months=84,
        )
    )

    assert result["completed_job_count"] == 3
    assert result["failed_job_count"] == 0
    assert result["baseline_gate_status"] == "passed"

    run_dir = tmp_path / "run"
    aggregate = load_json(run_dir / "aggregate_metrics.json")
    gates = load_json(run_dir / "baseline_gates.json")
    assert aggregate["schema_version"] == "marco.aggregate_metrics.v1"
    assert [row["model_id"] for row in aggregate["metrics"]] == ["no_change", "random_walk", "ridge"]
    assert gates["status"] == "passed"

    for job in plan["jobs"]:
        job_dir = run_dir / "jobs" / job["job_id"]
        assert (job_dir / "config.json").exists()
        assert load_json(job_dir / "status.json")["status"] == "completed"
        assert (job_dir / "metrics.json").exists()
        assert (job_dir / "predictions.jsonl").exists()


def test_runner_rerun_is_idempotent(tmp_path: Path) -> None:
    features_path = write_features(tmp_path, ["USD_CAD"])
    plan = make_plan(["USD_CAD"], ["random_walk", "no_change", "ridge"])
    config = RunnerConfig(
        root=tmp_path,
        plan=plan,
        features_path=features_path,
        output_dir=tmp_path / "run",
        evaluation_start="2008-01",
        train_min_months=84,
    )

    first = run_experiment_plan(config)
    first_aggregate = (tmp_path / "run" / "aggregate_metrics.json").read_text(encoding="utf-8")
    second = run_experiment_plan(config)
    second_aggregate = (tmp_path / "run" / "aggregate_metrics.json").read_text(encoding="utf-8")

    assert first["run_id"] == second["run_id"]
    assert first_aggregate == second_aggregate


def test_runner_rejects_model_claims_when_baselines_are_missing(tmp_path: Path) -> None:
    features_path = write_features(tmp_path, ["USD_CAD"])
    plan = make_plan(["USD_CAD"], ["ridge"])

    run_experiment_plan(
        RunnerConfig(
            root=tmp_path,
            plan=plan,
            features_path=features_path,
            output_dir=tmp_path / "run",
            evaluation_start="2008-01",
            train_min_months=84,
        )
    )

    gates = load_json(tmp_path / "run" / "baseline_gates.json")
    assert gates["status"] == "failed"
    assert gates["gates"][0]["missing_baselines"] == ["random_walk", "no_change"]


def test_runner_preserves_partial_failure_artifacts(tmp_path: Path) -> None:
    features_path = write_features(tmp_path, ["USD_CAD"])
    plan = make_plan(["USD_CAD", "MISSING_PAIR"], ["random_walk", "no_change"])

    result = run_experiment_plan(
        RunnerConfig(
            root=tmp_path,
            plan=plan,
            features_path=features_path,
            output_dir=tmp_path / "run",
            evaluation_start="2008-01",
            train_min_months=84,
        )
    )

    assert result["completed_job_count"] == 2
    assert result["failed_job_count"] == 2
    aggregate = load_json(tmp_path / "run" / "aggregate_metrics.json")
    assert len(aggregate["failures"]) == 2
    for failure in aggregate["failures"]:
        assert (tmp_path / "run" / "jobs" / failure["job_id"] / "failure.json").exists()


def test_runner_skips_non_executable_jobs_explicitly(tmp_path: Path) -> None:
    features_path = write_features(tmp_path, ["USD_CAD"])
    plan = make_plan(["USD_CAD"], ["random_walk", "gradient_boosted_trees"])
    plan["jobs"][1]["executable_now"] = False
    plan["jobs"][1]["status"] = "planned"

    result = run_experiment_plan(
        RunnerConfig(
            root=tmp_path,
            plan=plan,
            features_path=features_path,
            output_dir=tmp_path / "run",
            evaluation_start="2008-01",
            train_min_months=84,
        )
    )

    assert result["completed_job_count"] == 1
    assert result["skipped_job_count"] == 1
    skipped = load_json(tmp_path / "run" / "aggregate_metrics.json")["skipped"]
    assert skipped[0]["status"] == "skipped"


def test_runner_parallel_matches_serial_aggregate(tmp_path: Path) -> None:
    features_path = write_features(tmp_path, ["USD_CAD", "USD_MXN"])
    plan = make_plan(["USD_CAD", "USD_MXN"], ["random_walk", "no_change", "ridge"])

    run_experiment_plan(
        RunnerConfig(
            root=tmp_path,
            plan=plan,
            features_path=features_path,
            output_dir=tmp_path / "serial",
            evaluation_start="2008-01",
            train_min_months=84,
            max_parallelism=1,
        )
    )
    run_experiment_plan(
        RunnerConfig(
            root=tmp_path,
            plan=plan,
            features_path=features_path,
            output_dir=tmp_path / "parallel",
            evaluation_start="2008-01",
            train_min_months=84,
            max_parallelism=2,
        )
    )

    serial = load_json(tmp_path / "serial" / "aggregate_metrics.json")
    parallel = load_json(tmp_path / "parallel" / "aggregate_metrics.json")
    assert serial == parallel


def write_features(root: Path, pairs: list[str]) -> Path:
    periods = pd.date_range("2000-01-31", periods=150, freq="ME")
    rows = []
    for pair_index, pair in enumerate(pairs):
        for idx, period in enumerate(periods):
            rows.append(
                {
                    "period": period.strftime("%Y-%m-%d"),
                    "pair": pair,
                    "fx_return_6m": (idx + pair_index) / 1000.0,
                    "carry_pred_6m": 0.001 * pair_index,
                    "real_rate_pred_6m": 0.002 * pair_index,
                    "nominal_rate_diff": float(idx + pair_index),
                    "inflation_diff": 0.1 + pair_index,
                    "real_rate_diff": float(idx) - 0.1,
                    "yield_10y_diff": 0.2,
                    "yield_curve_slope_local": 0.3,
                    "yield_curve_slope_us": 0.4,
                    "fx_return_1m_lag": 0.01,
                    "fx_return_3m_lag": 0.02,
                    "fx_vol_12m": 0.03,
                }
            )
    path = root / "features.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def make_plan(pairs: list[str], models: list[str]) -> dict:
    jobs = []
    for pair in pairs:
        for model_id in models:
            jobs.append(
                {
                    "job_id": stable_job_id("current_fred_fx_rate_panel", pair, 6, model_id),
                    "dataset_id": "current_fred_fx_rate_panel",
                    "pair": pair,
                    "target": "fx_return_6m",
                    "horizon_months": 6,
                    "model_id": model_id,
                    "executable_now": True,
                    "complexity_tier": 0 if model_id in {"random_walk", "no_change"} else 2,
                    "status": "ready",
                }
            )
    return {
        "schema_version": "marco.experiment_plan.v1",
        "plan_id": stable_plan_id("test-run", jobs),
        "source_run_id": "test-run",
        "vintage_policy": "latest_revised_snapshot",
        "lookahead_status": "not_real_time_vintage_safe",
        "max_parallelism": 2,
        "dataset_ids": ["current_fred_fx_rate_panel"],
        "pairs": pairs,
        "horizons": [6],
        "model_ids": models,
        "job_count": len(jobs),
        "jobs": jobs,
    }


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

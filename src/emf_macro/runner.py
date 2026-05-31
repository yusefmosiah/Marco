from __future__ import annotations

import json
import math
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .backtest import BacktestConfig, walk_forward_pair
from .datasets import build_dataset_mapping_spec, validate_dataset_mapping_spec
from .experiments import build_hypothesis_spec, validate_hypothesis_spec


RUN_SCHEMA = "marco.experiment_run.v1"
JOB_STATUS_SCHEMA = "marco.experiment_job_status.v1"
JOB_METRICS_SCHEMA = "marco.experiment_job_metrics.v1"
AGGREGATE_SCHEMA = "marco.aggregate_metrics.v1"
BASELINE_GATES_SCHEMA = "marco.baseline_gates.v1"

REQUIRED_BASELINES = ["random_walk", "no_change"]


@dataclass(frozen=True)
class RunnerConfig:
    root: Path
    plan: dict[str, Any]
    features_path: Path | None = None
    output_dir: Path | None = None
    evaluation_start: str = "2006-01"
    train_min_months: int = 84
    max_parallelism: int = 1
    mapping_spec: dict[str, Any] | None = None
    hypothesis_spec: dict[str, Any] | None = None


def run_experiment_plan(config: RunnerConfig) -> dict[str, Any]:
    validate_experiment_plan(config.plan)
    features_path = config.features_path or default_features_path(config.root)
    features = load_features(features_path)
    run_id = run_id_for_plan(config.plan)
    run_dir = config.output_dir or (config.root / "backtests" / "runs" / run_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    mapping_spec = config.mapping_spec or default_mapping_spec_for_plan(config.plan)
    hypothesis_spec = config.hypothesis_spec or default_hypothesis_spec_for_plan(config.plan)
    validate_default_specs(mapping_spec, hypothesis_spec)

    write_json_atomic(run_dir / "experiment_plan.json", config.plan)
    write_json_atomic(run_dir / "dataset_mapping.json", mapping_spec)
    write_json_atomic(run_dir / "hypothesis_spec.json", hypothesis_spec)
    write_json_atomic(
        run_dir / "run_manifest.json",
        {
            "schema_version": RUN_SCHEMA,
            "run_id": run_id,
            "plan_id": config.plan["plan_id"],
            "source_run_id": config.plan.get("source_run_id"),
            "features_path": str(features_path),
            "dataset_mapping_id": mapping_spec["mapping_id"],
            "hypothesis_id": hypothesis_spec["hypothesis_id"],
            "vintage_policy": config.plan.get("vintage_policy", "latest_revised_snapshot"),
            "lookahead_status": config.plan.get("lookahead_status", "not_real_time_vintage_safe"),
            "evaluation_start": config.evaluation_start,
            "train_min_months": config.train_min_months,
            "max_parallelism": config.max_parallelism,
        },
    )

    jobs = list(config.plan["jobs"])
    skipped = [job for job in jobs if job.get("status") != "ready" or not job.get("executable_now", False)]
    ready = [job for job in jobs if job.get("status") == "ready" and job.get("executable_now", False)]

    completed_jobs: list[dict[str, Any]] = []
    failed_jobs: list[dict[str, Any]] = []
    skipped_jobs: list[dict[str, Any]] = []
    for job in skipped:
        skipped_jobs.append(write_skipped_job(run_dir, job, "job is not executable now"))

    groups = group_ready_jobs(ready)
    if config.max_parallelism <= 1 or len(groups) <= 1:
        results = [
            execute_job_group(group, features, run_dir, config.evaluation_start, config.train_min_months, config.plan)
            for group in groups
        ]
    else:
        with ThreadPoolExecutor(max_workers=config.max_parallelism) as executor:
            futures = [
                executor.submit(
                    execute_job_group,
                    group,
                    features,
                    run_dir,
                    config.evaluation_start,
                    config.train_min_months,
                    config.plan,
                )
                for group in groups
            ]
            results = [future.result() for future in futures]

    for result in results:
        completed_jobs.extend(result["completed"])
        failed_jobs.extend(result["failed"])

    aggregate = aggregate_metrics(config.plan, completed_jobs, failed_jobs, skipped_jobs)
    gates = baseline_gates(config.plan, completed_jobs)
    write_json_atomic(run_dir / "aggregate_metrics.json", aggregate)
    write_json_atomic(run_dir / "baseline_gates.json", gates)
    (run_dir / "report.md").write_text(render_runner_report(run_id, aggregate, gates), encoding="utf-8")

    return {
        "schema_version": RUN_SCHEMA,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "completed_job_count": len(completed_jobs),
        "failed_job_count": len(failed_jobs),
        "skipped_job_count": len(skipped_jobs),
        "baseline_gate_status": gates["status"],
    }


def validate_experiment_plan(plan: dict[str, Any]) -> None:
    if plan.get("schema_version") != "marco.experiment_plan.v1":
        raise ValueError("unsupported experiment plan schema")
    if not plan.get("plan_id"):
        raise ValueError("experiment plan is missing plan_id")
    if not plan.get("jobs"):
        raise ValueError("experiment plan has no jobs")


def load_features(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def default_features_path(root: Path) -> Path:
    parquet = root / "data" / "derived" / "fred_fx_rates" / "features_monthly.parquet"
    if parquet.exists():
        return parquet
    return root / "data" / "derived" / "fred_fx_rates" / "features_monthly.csv"


def run_id_for_plan(plan: dict[str, Any]) -> str:
    return f"ledger-{plan['plan_id'].removeprefix('plan-')}"


def default_mapping_spec_for_plan(plan: dict[str, Any]) -> dict[str, Any]:
    value_columns = sorted({job["target"] for job in plan["jobs"]})
    record = {
        "dataset_id": plan.get("dataset_ids", ["current_fred_fx_rate_panel"])[0],
        "schema": {
            "columns": [
                "period",
                "pair",
                "fx_return_1m",
                "fx_return_3m",
                "fx_return_6m",
                "nominal_rate_diff",
                "inflation_diff",
                "real_rate_diff",
                "yield_10y_diff",
                "yield_curve_slope_local",
                "yield_curve_slope_us",
                "fx_return_1m_lag",
                "fx_return_3m_lag",
                "fx_vol_12m",
                *value_columns,
            ]
        },
    }
    return build_dataset_mapping_spec(
        record,
        date_column="period",
        value_columns=value_columns,
        frequency="M",
        indicators={column: "fx_return" for column in value_columns},
        vintage_policy=plan.get("vintage_policy", "latest_revised_snapshot"),
    )


def default_hypothesis_spec_for_plan(plan: dict[str, Any]) -> dict[str, Any]:
    models = sorted({job["model_id"] for job in plan["jobs"] if job.get("executable_now")})
    for baseline in REQUIRED_BASELINES:
        if baseline not in models:
            models.append(baseline)
    return build_hypothesis_spec(
        hypothesis_id=f"hyp-{plan['plan_id'].removeprefix('plan-')}",
        title="Rate and inflation differentials should earn their place against hard FX baselines.",
        claim="Candidate FX/rate models should only be promoted when they beat random-walk and no-change baselines under the same split.",
        target="fx_return",
        feature_families=["rate_diff", "real_rate_diff", "inflation_diff", "yield_diff"],
        required_datasets=plan.get("dataset_ids", ["current_fred_fx_rate_panel"]),
        candidate_models=models,
        baseline_models=REQUIRED_BASELINES,
        horizon_months=sorted({int(job["horizon_months"]) for job in plan["jobs"]}),
        falsification_rule="Reject any promoted model claim when random_walk or no_change is missing for the same dataset, pair, target, horizon, and split.",
    )


def validate_default_specs(mapping_spec: dict[str, Any], hypothesis_spec: dict[str, Any]) -> None:
    record = {
        "dataset_id": mapping_spec["dataset_id"],
        "schema": {"columns": [mapping_spec["date_column"], *mapping_spec["value_columns"]]},
    }
    validate_dataset_mapping_spec(record, mapping_spec)
    validate_hypothesis_spec(hypothesis_spec)


def group_ready_jobs(jobs: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, int, str], list[dict[str, Any]]] = {}
    for job in jobs:
        key = (job["dataset_id"], job["pair"], int(job["horizon_months"]), job["target"])
        grouped.setdefault(key, []).append(job)
    return [sorted(group, key=lambda job: job["job_id"]) for _, group in sorted(grouped.items())]


def execute_job_group(
    group: list[dict[str, Any]],
    features: pd.DataFrame,
    run_dir: Path,
    evaluation_start: str,
    train_min_months: int,
    plan: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    first = group[0]
    config = BacktestConfig(
        pair=first["pair"],
        target=first["target"],
        horizon_months=int(first["horizon_months"]),
        evaluation_start=evaluation_start,
        train_min_months=train_min_months,
        vintage_policy=plan.get("vintage_policy", "latest_revised_snapshot"),
        lookahead_status=plan.get("lookahead_status", "not_real_time_vintage_safe"),
    )

    try:
        predictions, summary = walk_forward_pair(features, config)
    except Exception as exc:
        return {"completed": [], "failed": [write_failed_job(run_dir, job, exc) for job in group]}

    completed = []
    failed = []
    for job in group:
        model_id = job["model_id"]
        model_predictions = predictions[predictions["model_id"] == model_id].copy()
        model_metrics = summary["metrics"].get(model_id)
        if model_predictions.empty or model_metrics is None:
            failed.append(write_failed_job(run_dir, job, ValueError(f"model {model_id} did not produce predictions")))
            continue
        completed.append(write_completed_job(run_dir, job, model_predictions, model_metrics, asdict(config)))
    return {"completed": completed, "failed": failed}


def write_completed_job(
    run_dir: Path,
    job: dict[str, Any],
    predictions: pd.DataFrame,
    model_metrics: dict[str, Any],
    backtest_config: dict[str, Any],
) -> dict[str, Any]:
    job_dir = run_dir / "jobs" / job["job_id"]
    tmp_dir = temp_job_dir(job_dir)
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=False)
    config_payload = {"schema_version": "marco.experiment_job_config.v1", "job": job, "backtest_config": backtest_config}
    status_payload = {"schema_version": JOB_STATUS_SCHEMA, "job_id": job["job_id"], "status": "completed"}
    metrics_payload = {
        "schema_version": JOB_METRICS_SCHEMA,
        "job_id": job["job_id"],
        "dataset_id": job["dataset_id"],
        "pair": job["pair"],
        "target": job["target"],
        "horizon_months": int(job["horizon_months"]),
        "model_id": job["model_id"],
        **normalize_numbers(model_metrics),
    }
    write_json_atomic(tmp_dir / "config.json", config_payload)
    write_json_atomic(tmp_dir / "status.json", status_payload)
    write_json_atomic(tmp_dir / "metrics.json", metrics_payload)
    predictions.to_json(tmp_dir / "predictions.jsonl", orient="records", lines=True)
    replace_dir_atomic(tmp_dir, job_dir)
    return metrics_payload


def write_failed_job(run_dir: Path, job: dict[str, Any], exc: Exception) -> dict[str, Any]:
    job_dir = run_dir / "jobs" / job["job_id"]
    tmp_dir = temp_job_dir(job_dir)
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=False)
    failure_payload = {
        "schema_version": "marco.experiment_job_failure.v1",
        "job_id": job["job_id"],
        "status": "failed",
        "error_type": type(exc).__name__,
        "error_message": str(exc),
    }
    write_json_atomic(tmp_dir / "config.json", {"schema_version": "marco.experiment_job_config.v1", "job": job})
    write_json_atomic(tmp_dir / "status.json", {"schema_version": JOB_STATUS_SCHEMA, "job_id": job["job_id"], "status": "failed"})
    write_json_atomic(tmp_dir / "failure.json", failure_payload)
    replace_dir_atomic(tmp_dir, job_dir)
    return failure_payload


def write_skipped_job(run_dir: Path, job: dict[str, Any], reason: str) -> dict[str, Any]:
    job_dir = run_dir / "jobs" / job["job_id"]
    tmp_dir = temp_job_dir(job_dir)
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=False)
    payload = {"schema_version": JOB_STATUS_SCHEMA, "job_id": job["job_id"], "status": "skipped", "reason": reason}
    write_json_atomic(tmp_dir / "config.json", {"schema_version": "marco.experiment_job_config.v1", "job": job})
    write_json_atomic(tmp_dir / "status.json", payload)
    replace_dir_atomic(tmp_dir, job_dir)
    return payload


def aggregate_metrics(
    plan: dict[str, Any],
    completed_jobs: list[dict[str, Any]],
    failed_jobs: list[dict[str, Any]],
    skipped_jobs: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = sorted(completed_jobs, key=metric_sort_key)
    return {
        "schema_version": AGGREGATE_SCHEMA,
        "plan_id": plan["plan_id"],
        "source_run_id": plan.get("source_run_id"),
        "vintage_policy": plan.get("vintage_policy", "latest_revised_snapshot"),
        "lookahead_status": plan.get("lookahead_status", "not_real_time_vintage_safe"),
        "completed_job_count": len(completed_jobs),
        "failed_job_count": len(failed_jobs),
        "skipped_job_count": len(skipped_jobs),
        "metrics": rows,
        "failures": sorted(failed_jobs, key=lambda row: row["job_id"]),
        "skipped": sorted(skipped_jobs, key=lambda row: row["job_id"]),
    }


def baseline_gates(plan: dict[str, Any], completed_jobs: list[dict[str, Any]]) -> dict[str, Any]:
    metrics_by_key = {}
    for row in completed_jobs:
        key = (row["dataset_id"], row["pair"], row["target"], int(row["horizon_months"]))
        metrics_by_key.setdefault(key, {})[row["model_id"]] = row

    gate_rows = []
    for key, models in sorted(metrics_by_key.items()):
        missing = [baseline for baseline in REQUIRED_BASELINES if baseline not in models]
        best = None
        if not missing:
            best = min(models.values(), key=lambda row: row["rmse"])
        gate_rows.append(
            {
                "dataset_id": key[0],
                "pair": key[1],
                "target": key[2],
                "horizon_months": key[3],
                "status": "passed" if not missing else "failed",
                "required_baselines": REQUIRED_BASELINES,
                "missing_baselines": missing,
                "best_model": best["model_id"] if best else None,
                "best_rmse": best["rmse"] if best else None,
                "random_walk_rmse": models.get("random_walk", {}).get("rmse"),
                "no_change_rmse": models.get("no_change", {}).get("rmse"),
            }
        )
    return {
        "schema_version": BASELINE_GATES_SCHEMA,
        "plan_id": plan["plan_id"],
        "status": "passed" if gate_rows and all(row["status"] == "passed" for row in gate_rows) else "failed",
        "gates": gate_rows,
    }


def render_runner_report(run_id: str, aggregate: dict[str, Any], gates: dict[str, Any]) -> str:
    lines = [
        "# Marco Experiment Ledger Report",
        "",
        f"Run ID: `{run_id}`",
        "",
        f"Vintage policy: `{aggregate['vintage_policy']}`",
        "",
        f"Lookahead status: `{aggregate['lookahead_status']}`",
        "",
        f"Completed jobs: `{aggregate['completed_job_count']}`",
        "",
        f"Failed jobs: `{aggregate['failed_job_count']}`",
        "",
        f"Skipped jobs: `{aggregate['skipped_job_count']}`",
        "",
        f"Baseline gate status: `{gates['status']}`",
        "",
        "## Metrics",
        "",
        "| Dataset | Pair | Target | Horizon | Model | N | RMSE | MAE | Directional Accuracy |",
        "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in aggregate["metrics"]:
        lines.append(
            f"| {row['dataset_id']} | {row['pair']} | {row['target']} | {row['horizon_months']} | {row['model_id']} | "
            f"{row['n']} | {format_metric(row['rmse'], 6)} | {format_metric(row['mae'], 6)} | "
            f"{format_metric(row['directional_accuracy'], 3)} |"
        )
    lines.extend(["", "## Baseline Gates", ""])
    lines.append("```json")
    lines.append(json.dumps(gates, indent=2, sort_keys=True))
    lines.append("```")
    return "\n".join(lines) + "\n"


def temp_job_dir(job_dir: Path) -> Path:
    return job_dir.with_name(f".{job_dir.name}.tmp-{os.getpid()}")


def replace_dir_atomic(tmp_dir: Path, final_dir: Path) -> None:
    backup = final_dir.with_name(f".{final_dir.name}.old-{os.getpid()}")
    if backup.exists():
        shutil.rmtree(backup)
    if final_dir.exists():
        final_dir.rename(backup)
    tmp_dir.rename(final_dir)
    if backup.exists():
        shutil.rmtree(backup)


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def normalize_numbers(payload: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for key, value in payload.items():
        if isinstance(value, float) and math.isnan(value):
            result[key] = None
        else:
            result[key] = value
    return result


def format_metric(value: Any, digits: int) -> str:
    if value is None:
        return "null"
    return f"{float(value):.{digits}f}"


def metric_sort_key(row: dict[str, Any]) -> tuple[str, str, str, int, str]:
    return (row["dataset_id"], row["pair"], row["target"], int(row["horizon_months"]), row["model_id"])

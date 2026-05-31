from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .agent_store import ArtifactStore
from .datasets import DatasetRegistry
from .model_registry import list_model_specs


@dataclass(frozen=True)
class HypothesisSpec:
    schema_version: str
    hypothesis_id: str
    title: str
    claim: str
    target: str
    feature_families: list[str]
    required_datasets: list[str]
    candidate_models: list[str]
    baseline_models: list[str]
    metric: str
    horizon_months: list[int]
    split_policy: str
    falsification_rule: str


def suggest_hypotheses(root: Path, run_id: str = "latest") -> dict[str, Any]:
    store = ArtifactStore(root)
    datasets = DatasetRegistry(root).list()
    summary = store.load_summary(run_id)
    resolved = store.resolve_run_id(run_id)
    best_rows = summary.get("best_by_rmse", [])
    model_rows = summary.get("metrics", [])
    active_models = [row for row in list_model_specs(include_planned=False)]

    suggestions = [
        {
            "hypothesis_id": "baseline-dominance-check",
            "title": "Most FX/rate signals do not beat no-change after walk-forward costs of estimation.",
            "why": "The current run shows random-walk/no-change baselines winning nearly everywhere on RMSE.",
            "next_test": "Repeat at 12M/24M horizons and across rolling 120-month windows before adding complexity.",
            "required_data": ["current_fred_fx_rate_panel"],
            "candidate_models": ["random_walk", "no_change", "rolling_mean_36m", "ridge"],
        },
        {
            "hypothesis_id": "carry-real-rate-regime",
            "title": "Carry and real-rate differentials may work only in selected inflation/rate regimes.",
            "why": "Simple carry and real-rate rules underperform broadly in the current aggregate snapshot.",
            "next_test": "Slice by 2006-2012, 2013-2019, and 2020-present; compare RMSE and directional accuracy.",
            "required_data": ["current_fred_fx_rate_panel"],
            "candidate_models": ["carry_diff", "real_rate_diff", "ridge"],
        },
        {
            "hypothesis_id": "feature-panel-width",
            "title": "Wider macro panels may help only if model complexity is staged against hard baselines.",
            "why": "Ridge only slightly improves USD_CAD 6M, suggesting any edge is weak and needs more evidence.",
            "next_test": "Add more countries/indicators, then compare regularized linear models before nonlinear models.",
            "required_data": ["fred_md", "country_macro_panels"],
            "candidate_models": [model["model_id"] for model in active_models],
        },
    ]

    if datasets:
        suggestions.append(
            {
                "hypothesis_id": "uploaded-dataset-augmentation",
                "title": "User-provided time-series data can be mapped into Marco panels and tested against the same baselines.",
                "why": f"{len(datasets)} local dataset(s) are registered and can seed dataset-specific experiment plans.",
                "next_test": "Infer date/frequency/target columns, build a normalized panel, and run the baseline ladder first.",
                "required_data": [row["dataset_id"] for row in datasets],
                "candidate_models": ["random_walk", "no_change", "rolling_mean_36m", "ridge"],
            }
        )

    return {
        "schema_version": "marco.hypotheses.v1",
        "run_id": resolved,
        "vintage_policy": summary.get("vintage_policy"),
        "lookahead_status": summary.get("lookahead_status"),
        "dataset_count": len(datasets),
        "metric_rows": len(model_rows),
        "best_rows": best_rows,
        "hypotheses": suggestions,
    }


def build_hypothesis_spec(
    *,
    hypothesis_id: str,
    title: str,
    claim: str,
    target: str,
    feature_families: list[str],
    required_datasets: list[str],
    candidate_models: list[str],
    falsification_rule: str,
    baseline_models: list[str] | None = None,
    metric: str = "rmse",
    horizon_months: list[int] | None = None,
    split_policy: str = "walk_forward_expanding",
) -> dict[str, Any]:
    spec = HypothesisSpec(
        schema_version="marco.hypothesis_spec.v1",
        hypothesis_id=hypothesis_id,
        title=title,
        claim=claim,
        target=target,
        feature_families=feature_families,
        required_datasets=required_datasets,
        candidate_models=candidate_models,
        baseline_models=baseline_models or ["random_walk", "no_change"],
        metric=metric,
        horizon_months=horizon_months or [1, 3, 6],
        split_policy=split_policy,
        falsification_rule=falsification_rule,
    )
    payload = asdict(spec)
    validate_hypothesis_spec(payload)
    return payload


def validate_hypothesis_spec(spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != "marco.hypothesis_spec.v1":
        raise ValueError("unsupported hypothesis spec schema")
    required_text = ["hypothesis_id", "title", "claim", "target", "metric", "split_policy", "falsification_rule"]
    missing_text = [field for field in required_text if not str(spec.get(field, "")).strip()]
    if missing_text:
        raise ValueError(f"missing required hypothesis fields: {', '.join(missing_text)}")
    for field in ["feature_families", "required_datasets", "candidate_models", "baseline_models", "horizon_months"]:
        if not spec.get(field):
            raise ValueError(f"{field} must not be empty")
    if not set(spec["baseline_models"]) <= set(spec["candidate_models"]):
        raise ValueError("baseline_models must be included in candidate_models")
    if any(int(horizon) <= 0 for horizon in spec["horizon_months"]):
        raise ValueError("horizon_months must be positive")


def build_experiment_plan(
    root: Path,
    run_id: str = "latest",
    *,
    pairs: list[str] | None = None,
    horizons: list[int] | None = None,
    model_ids: list[str] | None = None,
    dataset_ids: list[str] | None = None,
    max_parallelism: int = 4,
) -> dict[str, Any]:
    store = ArtifactStore(root)
    summary = store.load_summary(run_id)
    resolved = store.resolve_run_id(run_id)
    available_models = {row["model_id"]: row for row in list_model_specs(include_planned=True)}
    executable_models = [row["model_id"] for row in available_models.values() if row["executable_now"]]
    selected_pairs = pairs or summary.get("pairs", [])
    selected_horizons = horizons or summary.get("horizons", [])
    selected_models = model_ids or executable_models
    selected_datasets = dataset_ids or ["current_fred_fx_rate_panel"]

    jobs = []
    for dataset_id in selected_datasets:
        for pair in selected_pairs:
            for horizon in selected_horizons:
                for model_id in selected_models:
                    spec = available_models.get(model_id)
                    jobs.append(
                        {
                            "job_id": stable_job_id(dataset_id, pair, horizon, model_id),
                            "dataset_id": dataset_id,
                            "pair": pair,
                            "target": f"fx_return_{horizon}m",
                            "horizon_months": horizon,
                            "model_id": model_id,
                            "executable_now": bool(spec and spec["executable_now"]),
                            "complexity_tier": spec["complexity_tier"] if spec else None,
                            "status": "ready" if spec and spec["executable_now"] else "planned",
                        }
                    )

    return {
        "schema_version": "marco.experiment_plan.v1",
        "plan_id": stable_plan_id(resolved, jobs),
        "source_run_id": resolved,
        "vintage_policy": summary.get("vintage_policy"),
        "lookahead_status": summary.get("lookahead_status"),
        "max_parallelism": max_parallelism,
        "dataset_ids": selected_datasets,
        "pairs": selected_pairs,
        "horizons": selected_horizons,
        "model_ids": selected_models,
        "job_count": len(jobs),
        "jobs": jobs,
        "next_runner_contract": {
            "parallel_axis": "independent dataset/pair/horizon/model jobs",
            "required_artifacts": ["predictions", "metrics", "config", "source_hashes"],
            "promotion_gate": "compare every model against random_walk and no_change before claiming improvement",
        },
    }


def stable_job_id(dataset_id: str, pair: str, horizon: int, model_id: str) -> str:
    digest = hashlib.sha256(f"{dataset_id}|{pair}|{horizon}|{model_id}".encode("utf-8")).hexdigest()
    return f"job-{digest[:16]}"


def stable_plan_id(run_id: str, jobs: list[dict[str, Any]]) -> str:
    payload = json.dumps([job["job_id"] for job in jobs], sort_keys=True)
    digest = hashlib.sha256(f"{run_id}|{payload}".encode("utf-8")).hexdigest()
    return f"plan-{digest[:16]}"

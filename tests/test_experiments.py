from __future__ import annotations

from pathlib import Path

import pytest

from emf_macro.experiments import build_experiment_plan, build_hypothesis_spec, suggest_hypotheses

from test_agent_store import write_summary


def test_suggest_hypotheses_uses_run_artifacts(tmp_path: Path) -> None:
    write_summary(tmp_path, "20260101-000000-fx-rate-diff")

    payload = suggest_hypotheses(tmp_path)

    assert payload["schema_version"] == "marco.hypotheses.v1"
    assert payload["run_id"] == "20260101-000000-fx-rate-diff"
    assert payload["hypotheses"]
    assert payload["vintage_policy"] == "latest_revised_snapshot"


def test_build_experiment_plan_crosses_dataset_pair_horizon_model(tmp_path: Path) -> None:
    write_summary(tmp_path, "20260101-000000-fx-rate-diff")

    plan = build_experiment_plan(
        tmp_path,
        pairs=["USD_CAD"],
        horizons=[6],
        model_ids=["random_walk", "ridge", "gradient_boosted_trees"],
        dataset_ids=["current_fred_fx_rate_panel", "uploaded-demo"],
        max_parallelism=2,
    )

    assert plan["schema_version"] == "marco.experiment_plan.v1"
    assert plan["job_count"] == 6
    assert plan["max_parallelism"] == 2
    statuses = {job["model_id"]: job["status"] for job in plan["jobs"]}
    assert statuses["random_walk"] == "ready"
    assert statuses["ridge"] == "ready"
    assert statuses["gradient_boosted_trees"] == "planned"


def test_build_hypothesis_spec_requires_baseline_models() -> None:
    spec = build_hypothesis_spec(
        hypothesis_id="real-rate-diff-fx",
        title="Real-rate differentials predict FX returns after baseline gates.",
        claim="Higher real-rate differentials should improve 6M FX return forecasts versus no-change.",
        target="fx_return_6m",
        feature_families=["real_rate_diff", "inflation_diff"],
        required_datasets=["current_fred_fx_rate_panel"],
        candidate_models=["random_walk", "no_change", "ridge"],
        horizon_months=[6],
        falsification_rule="Reject if ridge does not beat both random_walk and no_change on walk-forward RMSE.",
    )

    assert spec["schema_version"] == "marco.hypothesis_spec.v1"
    assert spec["baseline_models"] == ["random_walk", "no_change"]


def test_build_hypothesis_spec_rejects_baseline_outside_candidates() -> None:
    with pytest.raises(ValueError, match="baseline_models"):
        build_hypothesis_spec(
            hypothesis_id="bad",
            title="Bad baseline",
            claim="Bad baseline setup",
            target="fx_return_6m",
            feature_families=["rate_diff"],
            required_datasets=["current_fred_fx_rate_panel"],
            candidate_models=["ridge"],
            falsification_rule="Reject when setup is invalid.",
        )

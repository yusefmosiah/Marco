from __future__ import annotations

from pathlib import Path

from emf_macro.experiments import build_experiment_plan, suggest_hypotheses

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

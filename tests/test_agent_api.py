from __future__ import annotations

from http import HTTPStatus
from pathlib import Path

from emf_macro.agent_api import route_get
from emf_macro.agent_store import ArtifactStore

from test_agent_store import write_summary


def test_agent_api_routes_metrics_and_report(tmp_path: Path) -> None:
    write_summary(tmp_path, "20260101-000000-fx-rate-diff")
    store = ArtifactStore(tmp_path)

    health, status, content_type = route_get(store, "/health", {}, public_base_url=None)
    assert status == HTTPStatus.OK
    assert content_type == "application/json"
    assert health["runs"] == 1

    payload, status, _ = route_get(
        store,
        "/v1/runs/latest/metrics",
        {"pair": ["USD_CAD"], "horizon_months": ["6"]},
        public_base_url=None,
    )
    assert status == HTTPStatus.OK
    assert [row["model_id"] for row in payload["metrics"]] == ["ridge"]

    report, status, content_type = route_get(store, "/v1/runs/latest/report", {}, public_base_url=None)
    assert status == HTTPStatus.OK
    assert content_type == "text/markdown"
    assert report == "# Report\n"


def test_agent_api_routes_experiment_foundation(tmp_path: Path) -> None:
    write_summary(tmp_path, "20260101-000000-fx-rate-diff")
    store = ArtifactStore(tmp_path)

    models, status, _ = route_get(store, "/v1/models", {"active_only": ["true"]}, public_base_url=None)
    assert status == HTTPStatus.OK
    assert all(row["executable_now"] for row in models["models"])

    hypotheses, status, _ = route_get(store, "/v1/hypotheses", {}, public_base_url=None)
    assert status == HTTPStatus.OK
    assert hypotheses["hypotheses"]

    plan, status, _ = route_get(
        store,
        "/v1/experiment-plan",
        {"pair": ["USD_CAD"], "horizon_months": ["6"], "model_id": ["ridge"]},
        public_base_url=None,
    )
    assert status == HTTPStatus.OK
    assert plan["job_count"] == 1

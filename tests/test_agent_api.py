from __future__ import annotations

from http import HTTPStatus
from pathlib import Path

from emf_macro.agent_api import route_get
from emf_macro.agent_store import ArtifactStore
from test_analyst_agent import write_analyst_payload
from test_news import write_registry
from test_news_agent import write_news_bundle

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


def test_agent_api_route_global_panel(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    artifact_dir = tmp_path / "artifacts" / "global-macro-panel" / "global_macro_starter_20260531"
    artifact_dir.mkdir(parents=True)
    (artifact_dir / "summary.json").write_text(
        '{"schema_version":"marco.global_macro_panel.v1","panel_rows":4}\n',
        encoding="utf-8",
    )

    payload, status, content_type = route_get(store, "/v1/global-panel", {}, public_base_url=None)

    assert status == HTTPStatus.OK
    assert content_type == "application/json"
    assert payload["panel_rows"] == 4


def test_agent_api_route_news_ledger(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    write_registry(tmp_path)
    bundle = tmp_path / "data" / "macro-news"
    bundle.mkdir(parents=True)
    (bundle / "summary.json").write_text(
        '{"schema_version":"marco.news_summary.v1","item_count":1}\n',
        encoding="utf-8",
    )
    (bundle / "news_items.jsonl").write_text(
        '{"id":"news-1","source_id":"example_central_bank","title":"Policy rate held steady"}\n',
        encoding="utf-8",
    )
    (bundle / "fetches.jsonl").write_text(
        '{"id":"fetch-1","source_id":"example_central_bank","status_code":200}\n',
        encoding="utf-8",
    )

    summary, status, content_type = route_get(store, "/v1/news", {}, public_base_url=None)
    assert status == HTTPStatus.OK
    assert content_type == "application/json"
    assert summary["item_count"] == 1

    sources, status, _ = route_get(store, "/v1/news/sources", {}, public_base_url=None)
    assert status == HTTPStatus.OK
    assert sources["sources"][0]["id"] == "example_central_bank"

    items, status, _ = route_get(store, "/v1/news/items", {"source_id": ["example_central_bank"]}, public_base_url=None)
    assert status == HTTPStatus.OK
    assert items["items"][0]["id"] == "news-1"

    fetches, status, _ = route_get(store, "/v1/news/fetches", {}, public_base_url=None)
    assert status == HTTPStatus.OK
    assert fetches["fetches"][0]["id"] == "fetch-1"


def test_agent_api_route_news_agent(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    write_news_bundle(tmp_path)

    payload, status, content_type = route_get(store, "/v1/agents/news-agent", {}, public_base_url=None)

    assert status == HTTPStatus.OK
    assert content_type == "application/json"
    assert payload["schema_version"] == "marco.news_agent.v1"
    assert payload["agent_id"] == "news_agent"
    assert payload["summary"]["item_count"] == 3
    assert not (tmp_path / "data" / "agents" / "latest" / "news_agent.md").exists()


def test_agent_api_route_analyst_agent(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    write_analyst_payload(tmp_path)

    payload, status, content_type = route_get(store, "/v1/agents/analyst-agent", {}, public_base_url=None)

    assert status == HTTPStatus.OK
    assert content_type == "application/json"
    assert payload["schema_version"] == "marco.analyst_agent.v1"
    assert payload["agent_id"] == "analyst_agent"
    assert payload["summary"]["article_count"] == 1
    assert "handoff" not in payload


def test_agent_api_route_economic_model_agent(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    output_dir = tmp_path / "data" / "backtests" / "macro-forecast-lab"
    output_dir.mkdir(parents=True)
    (output_dir / "summary.json").write_text(
        """
        {
          "schema_version": "marco.macro_forecast_lab.v1",
          "horizon_months": 6,
          "vintage_policy": "latest_revised_snapshot",
          "lookahead_status": "not_real_time_vintage_safe",
          "targets": {"interest_rate": "FEDFUNDS level"},
          "models": ["xgboost_top5"],
          "output_dir": "__OUTPUT_DIR__",
          "plots": {},
          "metrics": [{"target":"interest_rate","model_id":"xgboost_top5","n":2,"rmse":0.2,"r_squared":0.9}]
        }
        """.replace("__OUTPUT_DIR__", str(output_dir)),
        encoding="utf-8",
    )
    (output_dir / "predictions.jsonl").write_text(
        '{"target":"interest_rate","model_id":"xgboost_top5","forecast_origin":"2026-02","target_period":"2026-08","actual":4.0,"prediction":4.2,"error":0.2}\n',
        encoding="utf-8",
    )

    payload, status, content_type = route_get(
        store,
        "/v1/economic-model-agent",
        {"target": ["interest_rate"], "model_id": ["xgboost_top5"]},
        public_base_url=None,
    )

    assert status == HTTPStatus.OK
    assert content_type == "application/json"
    assert payload["schema_version"] == "marco.economic_model_agent.v1"
    assert payload["agent_id"] == "economic_modeling_agent"
    assert payload["metrics"][0]["model_id"] == "xgboost_top5"
    assert "handoff" not in payload
    assert not (tmp_path / "data" / "agents" / "latest" / "economic_modeling_agent.md").exists()

    alias, alias_status, _ = route_get(
        store,
        "/v1/agents/economic-modeling-agent",
        {"target": ["interest_rate"], "model_id": ["xgboost_top5"]},
        public_base_url=None,
    )
    assert alias_status == HTTPStatus.OK
    assert alias["agent_id"] == "economic_modeling_agent"

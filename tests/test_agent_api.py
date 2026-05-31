from __future__ import annotations

from http import HTTPStatus
from pathlib import Path

from emf_macro.agent_api import route_get
from emf_macro.agent_store import ArtifactStore
from test_news import write_registry

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

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .agent_store import ArtifactNotFoundError, ArtifactStore
from .datasets import DatasetRegistry
from .experiments import build_experiment_plan, suggest_hypotheses
from .global_panel import load_global_macro_summary
from .model_registry import list_model_specs


def run_server(root: Path, host: str, port: int, public_base_url: str | None = None) -> None:
    store = ArtifactStore(root=root)
    handler = make_handler(store, public_base_url=public_base_url)
    server = ThreadingHTTPServer((host, port), handler)
    print(json.dumps({"status": "listening", "host": host, "port": port, "root": str(root)}), flush=True)
    server.serve_forever()


def make_handler(store: ArtifactStore, public_base_url: str | None = None) -> type[BaseHTTPRequestHandler]:
    class AgentApiHandler(BaseHTTPRequestHandler):
        server_version = "MarcoAgentAPI/0.1"

        def do_GET(self) -> None:
            self.write_route(include_body=True)

        def do_HEAD(self) -> None:
            self.write_route(include_body=False)

        def write_route(self, include_body: bool) -> None:
            try:
                parsed = urlparse(self.path)
                path = parsed.path.rstrip("/") or "/"
                query = parse_qs(parsed.query)
                payload, status, content_type = route_get(store, path, query, public_base_url=public_base_url)
                if content_type == "application/json":
                    body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"
                else:
                    body = str(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", f"{content_type}; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if include_body:
                    self.wfile.write(body)
            except ArtifactNotFoundError as error:
                self.write_error(HTTPStatus.NOT_FOUND, str(error), include_body=include_body)
            except ValueError as error:
                self.write_error(HTTPStatus.BAD_REQUEST, str(error), include_body=include_body)
            except Exception as error:  # pragma: no cover - defensive boundary for HTTP callers.
                self.write_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(error), include_body=include_body)

        def log_message(self, format: str, *args: Any) -> None:
            return

        def write_error(self, status: HTTPStatus, message: str, include_body: bool = True) -> None:
            body = json.dumps({"error": message, "status": status.value}, indent=2).encode("utf-8") + b"\n"
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if include_body:
                self.wfile.write(body)

    return AgentApiHandler


def route_get(
    store: ArtifactStore,
    path: str,
    query: dict[str, list[str]],
    *,
    public_base_url: str | None = None,
) -> tuple[Any, HTTPStatus, str]:
    if path == "/health":
        return {"status": "ok", "service": "marco-agent-api", "runs": len(store.list_runs())}, HTTPStatus.OK, "application/json"

    if path == "/v1/runs":
        return {"runs": store.list_runs()}, HTTPStatus.OK, "application/json"

    if path == "/v1/agent-context":
        run_id = first(query, "run_id", "latest")
        return store.agent_context(run_id, public_base_url=public_base_url), HTTPStatus.OK, "application/json"

    if path == "/v1/datasets":
        return {"datasets": DatasetRegistry(store.root).list()}, HTTPStatus.OK, "application/json"

    if path == "/v1/models":
        active_only = first(query, "active_only", "false").lower() in {"1", "true", "yes"}
        return {"models": list_model_specs(include_planned=not active_only)}, HTTPStatus.OK, "application/json"

    if path == "/v1/hypotheses":
        run_id = first(query, "run_id", "latest")
        return suggest_hypotheses(store.root, run_id), HTTPStatus.OK, "application/json"

    if path == "/v1/experiment-plan":
        run_id = first(query, "run_id", "latest")
        return build_experiment_plan(
            store.root,
            run_id,
            pairs=query.get("pair"),
            horizons=optional_int_list(query.get("horizon_months") or query.get("horizon")),
            model_ids=query.get("model_id"),
            dataset_ids=query.get("dataset_id"),
            max_parallelism=optional_int(first(query, "max_parallelism")) or 4,
        ), HTTPStatus.OK, "application/json"

    if path == "/v1/global-panel":
        haul_id = first(query, "haul_id", "global_macro_starter_20260531")
        return load_global_macro_summary(store.root, haul_id=haul_id), HTTPStatus.OK, "application/json"

    parts = path.strip("/").split("/")
    if len(parts) >= 3 and parts[0] == "v1" and parts[1] == "runs":
        run_id = parts[2]
        if len(parts) == 3:
            return store.load_summary(run_id), HTTPStatus.OK, "application/json"
        if len(parts) == 4 and parts[3] == "metrics":
            return {
                "run_id": store.resolve_run_id(run_id),
                "metrics": store.filter_metrics(
                    run_id,
                    pair=first(query, "pair"),
                    horizon_months=optional_int(first(query, "horizon_months") or first(query, "horizon")),
                    model_id=first(query, "model_id"),
                ),
            }, HTTPStatus.OK, "application/json"
        if len(parts) == 4 and parts[3] == "best":
            return {
                "run_id": store.resolve_run_id(run_id),
                "best_by_rmse": store.filter_best(
                    run_id,
                    pair=first(query, "pair"),
                    horizon_months=optional_int(first(query, "horizon_months") or first(query, "horizon")),
                ),
            }, HTTPStatus.OK, "application/json"
        if len(parts) == 4 and parts[3] == "report":
            return store.load_report(run_id), HTTPStatus.OK, "text/markdown"

    raise ArtifactNotFoundError(f"route not found: {path}")


def first(query: dict[str, list[str]], key: str, default: str | None = None) -> str | None:
    values = query.get(key)
    if not values:
        return default
    return values[0]


def optional_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def optional_int_list(values: list[str] | None) -> list[int] | None:
    if not values:
        return None
    return [int(value) for value in values if value != ""]

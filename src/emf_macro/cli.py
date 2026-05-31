from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agent_api import run_server
from .agent_store import ArtifactStore
from .datasets import DatasetRegistry
from .experiments import build_experiment_plan, suggest_hypotheses
from .model_registry import list_model_specs
from .sources import MacroSourceCatalog


def main() -> None:
    parser = argparse.ArgumentParser(prog="emf-macro")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run-fx-rate-lab", help="run the FRED FX/rate differential foundation pipeline")
    run.add_argument("--root", default=".", help="repo root")
    run.add_argument("--evaluation-start", default="2006-01")
    run.add_argument("--horizons", default="1,3,6", help="comma-separated month horizons")

    list_runs = sub.add_parser("list-runs", help="list committed shareable artifact runs")
    list_runs.add_argument("--root", default=".", help="repo root")
    list_runs.add_argument("--compact", action="store_true", help="emit compact JSON")

    show_run = sub.add_parser("show-run", help="show a run summary artifact")
    show_run.add_argument("--root", default=".", help="repo root")
    show_run.add_argument("--run-id", default="latest")
    show_run.add_argument("--compact", action="store_true", help="emit compact JSON")

    metrics = sub.add_parser("metrics", help="query model metrics for a run")
    metrics.add_argument("--root", default=".", help="repo root")
    metrics.add_argument("--run-id", default="latest")
    metrics.add_argument("--pair")
    metrics.add_argument("--horizon", type=int)
    metrics.add_argument("--model-id")
    metrics.add_argument("--compact", action="store_true", help="emit compact JSON")

    best = sub.add_parser("best", help="query best model rows by pair/horizon")
    best.add_argument("--root", default=".", help="repo root")
    best.add_argument("--run-id", default="latest")
    best.add_argument("--pair")
    best.add_argument("--horizon", type=int)
    best.add_argument("--compact", action="store_true", help="emit compact JSON")

    context = sub.add_parser("agent-context", help="emit an agent-readable context packet")
    context.add_argument("--root", default=".", help="repo root")
    context.add_argument("--run-id", default="latest")
    context.add_argument("--public-base-url")
    context.add_argument("--compact", action="store_true", help="emit compact JSON")

    report = sub.add_parser("report", help="print a run report.md artifact")
    report.add_argument("--root", default=".", help="repo root")
    report.add_argument("--run-id", default="latest")

    serve = sub.add_parser("serve-agent-api", help="serve a read-only JSON API over artifact runs")
    serve.add_argument("--root", default=".", help="repo root")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--public-base-url")

    datasets = sub.add_parser("list-datasets", help="list locally registered uploaded/fetched datasets")
    datasets.add_argument("--root", default=".", help="repo root")
    datasets.add_argument("--compact", action="store_true", help="emit compact JSON")

    dataset_add = sub.add_parser("dataset-add", help="register a local dataset file under data/uploads")
    dataset_add.add_argument("path")
    dataset_add.add_argument("--root", default=".", help="repo root")
    dataset_add.add_argument("--name")
    dataset_add.add_argument("--kind", default="time_series")
    dataset_add.add_argument("--tag", action="append", default=[])
    dataset_add.add_argument("--compact", action="store_true", help="emit compact JSON")

    dataset_fetch = sub.add_parser("dataset-fetch-url", help="fetch and register a dataset URL under data/uploads")
    dataset_fetch.add_argument("url")
    dataset_fetch.add_argument("--root", default=".", help="repo root")
    dataset_fetch.add_argument("--name")
    dataset_fetch.add_argument("--kind", default="time_series")
    dataset_fetch.add_argument("--tag", action="append", default=[])
    dataset_fetch.add_argument("--compact", action="store_true", help="emit compact JSON")

    models = sub.add_parser("models", help="list model ladder specs")
    models.add_argument("--active-only", action="store_true")
    models.add_argument("--compact", action="store_true", help="emit compact JSON")

    sources = sub.add_parser("sources", help="list or inspect official macro source candidates")
    sources_sub = sources.add_subparsers(dest="sources_command", required=True)
    sources_list = sources_sub.add_parser("list", help="list official macro source candidates")
    sources_list.add_argument("--root", default=".", help="repo root")
    sources_list.add_argument("--priority", choices=["p0", "p1", "p2"])
    sources_list.add_argument("--status", choices=["active", "planned", "candidate"])
    sources_list.add_argument("--region", help="filter by region code, e.g. IN, BR, global")
    sources_list.add_argument("--compact", action="store_true", help="emit compact JSON")
    sources_inspect = sources_sub.add_parser("inspect", help="inspect one official macro source candidate")
    sources_inspect.add_argument("source_id")
    sources_inspect.add_argument("--root", default=".", help="repo root")
    sources_inspect.add_argument("--compact", action="store_true", help="emit compact JSON")

    hypotheses = sub.add_parser("suggest-hypotheses", help="suggest next testable macro/backtest hypotheses")
    hypotheses.add_argument("--root", default=".", help="repo root")
    hypotheses.add_argument("--run-id", default="latest")
    hypotheses.add_argument("--compact", action="store_true", help="emit compact JSON")

    plan = sub.add_parser("plan-experiments", help="emit a parallel backtest experiment plan")
    plan.add_argument("--root", default=".", help="repo root")
    plan.add_argument("--run-id", default="latest")
    plan.add_argument("--pair", action="append", dest="pairs")
    plan.add_argument("--horizon", action="append", type=int, dest="horizons")
    plan.add_argument("--model-id", action="append", dest="model_ids")
    plan.add_argument("--dataset-id", action="append", dest="dataset_ids")
    plan.add_argument("--max-parallelism", type=int, default=4)
    plan.add_argument("--output", help="optional path to write the plan JSON")
    plan.add_argument("--compact", action="store_true", help="emit compact JSON")

    args = parser.parse_args()

    if args.command == "run-fx-rate-lab":
        from .pipeline import run_fx_rate_lab

        horizons = tuple(int(part) for part in args.horizons.split(",") if part.strip())
        result = run_fx_rate_lab(Path(args.root).resolve(), args.evaluation_start, horizons)
        print_json(result)
    elif args.command == "list-runs":
        store = ArtifactStore(Path(args.root).resolve())
        print_json({"runs": store.list_runs()}, compact=args.compact)
    elif args.command == "show-run":
        store = ArtifactStore(Path(args.root).resolve())
        print_json(store.load_summary(args.run_id), compact=args.compact)
    elif args.command == "metrics":
        store = ArtifactStore(Path(args.root).resolve())
        print_json(
            {
                "run_id": store.resolve_run_id(args.run_id),
                "metrics": store.filter_metrics(
                    args.run_id,
                    pair=args.pair,
                    horizon_months=args.horizon,
                    model_id=args.model_id,
                ),
            },
            compact=args.compact,
        )
    elif args.command == "best":
        store = ArtifactStore(Path(args.root).resolve())
        print_json(
            {
                "run_id": store.resolve_run_id(args.run_id),
                "best_by_rmse": store.filter_best(args.run_id, pair=args.pair, horizon_months=args.horizon),
            },
            compact=args.compact,
        )
    elif args.command == "agent-context":
        store = ArtifactStore(Path(args.root).resolve())
        print_json(store.agent_context(args.run_id, public_base_url=args.public_base_url), compact=args.compact)
    elif args.command == "report":
        store = ArtifactStore(Path(args.root).resolve())
        print(store.load_report(args.run_id), end="")
    elif args.command == "serve-agent-api":
        run_server(Path(args.root).resolve(), args.host, args.port, public_base_url=args.public_base_url)
    elif args.command == "list-datasets":
        registry = DatasetRegistry(Path(args.root).resolve())
        print_json({"datasets": registry.list()}, compact=args.compact)
    elif args.command == "dataset-add":
        registry = DatasetRegistry(Path(args.root).resolve())
        print_json(
            registry.add_file(Path(args.path).resolve(), name=args.name, kind=args.kind, tags=args.tag),
            compact=args.compact,
        )
    elif args.command == "dataset-fetch-url":
        registry = DatasetRegistry(Path(args.root).resolve())
        print_json(registry.fetch_url(args.url, name=args.name, kind=args.kind, tags=args.tag), compact=args.compact)
    elif args.command == "models":
        print_json({"models": list_model_specs(include_planned=not args.active_only)}, compact=args.compact)
    elif args.command == "sources":
        catalog = MacroSourceCatalog(Path(args.root).resolve())
        if args.sources_command == "list":
            print_json(
                {
                    "schema_version": "marco.macro_sources.list.v1",
                    "sources": catalog.list(priority=args.priority, status=args.status, region=args.region),
                },
                compact=args.compact,
            )
        elif args.sources_command == "inspect":
            print_json(catalog.inspect(args.source_id), compact=args.compact)
    elif args.command == "suggest-hypotheses":
        print_json(suggest_hypotheses(Path(args.root).resolve(), args.run_id), compact=args.compact)
    elif args.command == "plan-experiments":
        payload = build_experiment_plan(
            Path(args.root).resolve(),
            args.run_id,
            pairs=args.pairs,
            horizons=args.horizons,
            model_ids=args.model_ids,
            dataset_ids=args.dataset_ids,
            max_parallelism=args.max_parallelism,
        )
        if args.output:
            Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print_json(payload, compact=args.compact)


def print_json(payload: object, compact: bool = False) -> None:
    if compact:
        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

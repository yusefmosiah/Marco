from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agent_api import run_server
from .agent_store import ArtifactStore


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


def print_json(payload: object, compact: bool = False) -> None:
    if compact:
        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

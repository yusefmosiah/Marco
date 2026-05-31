#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_API_BASE = "http://127.0.0.1:8765"
PUBLIC_SUMMARY_URL = "https://choir-ip.com/marco/artifacts/fred-fx-rate-lab-summary.json"


def main() -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--api-base", default=DEFAULT_API_BASE)
    common.add_argument("--repo-root", default=".")
    common.add_argument("--pretty", action="store_true")

    parser = argparse.ArgumentParser(description="Query Marco agent artifacts.")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--pretty", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("context", parents=[common], help="get agent context; API first, CLI fallback")
    sub.add_parser("runs", parents=[common], help="list runs; API first, CLI fallback")
    sub.add_parser("datasets", parents=[common], help="list local datasets; API first, CLI fallback")
    sub.add_parser("models", parents=[common], help="list model ladder specs; API first, CLI fallback")
    sub.add_parser("hypotheses", parents=[common], help="suggest hypotheses; API first, CLI fallback")
    run = sub.add_parser("run", parents=[common], help="show run summary")
    run.add_argument("--run-id", default="latest")

    metrics = sub.add_parser("metrics", parents=[common], help="query model metrics")
    metrics.add_argument("--run-id", default="latest")
    metrics.add_argument("--pair")
    metrics.add_argument("--horizon", type=int)
    metrics.add_argument("--model-id")

    best = sub.add_parser("best", parents=[common], help="query best model rows")
    best.add_argument("--run-id", default="latest")
    best.add_argument("--pair")
    best.add_argument("--horizon", type=int)

    plan = sub.add_parser("plan", parents=[common], help="build an experiment plan; API first, CLI fallback")
    plan.add_argument("--run-id", default="latest")
    plan.add_argument("--pair", action="append", dest="pairs")
    plan.add_argument("--horizon", action="append", type=int, dest="horizons")
    plan.add_argument("--model-id", action="append", dest="model_ids")
    plan.add_argument("--dataset-id", action="append", dest="dataset_ids")

    sub.add_parser("public-summary", parents=[common], help="fetch the live static summary from choir-ip.com")

    args = parser.parse_args()
    try:
        payload = dispatch(args)
    except Exception as error:
        print(f"marco_client error: {error}", file=sys.stderr)
        return 1
    print_json(payload, pretty=args.pretty)
    return 0


def dispatch(args: argparse.Namespace) -> Any:
    if args.command == "public-summary":
        return http_json(PUBLIC_SUMMARY_URL)

    if args.command == "context":
        return api_or_cli(args, "/v1/agent-context", ["agent-context", "--run-id", "latest", "--compact"])
    if args.command == "runs":
        return api_or_cli(args, "/v1/runs", ["list-runs", "--compact"])
    if args.command == "datasets":
        return api_or_cli(args, "/v1/datasets", ["list-datasets", "--compact"])
    if args.command == "models":
        return api_or_cli(args, "/v1/models", ["models", "--compact"])
    if args.command == "hypotheses":
        return api_or_cli(args, "/v1/hypotheses", ["suggest-hypotheses", "--compact"])
    if args.command == "run":
        return api_or_cli(args, f"/v1/runs/{args.run_id}", ["show-run", "--run-id", args.run_id, "--compact"])
    if args.command == "metrics":
        query = clean_query({"pair": args.pair, "horizon_months": args.horizon, "model_id": args.model_id})
        cli = ["metrics", "--run-id", args.run_id, "--compact"]
        if args.pair:
            cli.extend(["--pair", args.pair])
        if args.horizon is not None:
            cli.extend(["--horizon", str(args.horizon)])
        if args.model_id:
            cli.extend(["--model-id", args.model_id])
        return api_or_cli(args, f"/v1/runs/{args.run_id}/metrics?{query}", cli)
    if args.command == "best":
        query = clean_query({"pair": args.pair, "horizon_months": args.horizon})
        cli = ["best", "--run-id", args.run_id, "--compact"]
        if args.pair:
            cli.extend(["--pair", args.pair])
        if args.horizon is not None:
            cli.extend(["--horizon", str(args.horizon)])
        return api_or_cli(args, f"/v1/runs/{args.run_id}/best?{query}", cli)
    if args.command == "plan":
        query = multi_query(
            {
                "run_id": [args.run_id],
                "pair": args.pairs,
                "horizon_months": [str(value) for value in args.horizons] if args.horizons else None,
                "model_id": args.model_ids,
                "dataset_id": args.dataset_ids,
            }
        )
        cli = ["plan-experiments", "--run-id", args.run_id, "--compact"]
        for pair in args.pairs or []:
            cli.extend(["--pair", pair])
        for horizon in args.horizons or []:
            cli.extend(["--horizon", str(horizon)])
        for model_id in args.model_ids or []:
            cli.extend(["--model-id", model_id])
        for dataset_id in args.dataset_ids or []:
            cli.extend(["--dataset-id", dataset_id])
        return api_or_cli(args, f"/v1/experiment-plan?{query}", cli)
    raise ValueError(f"unknown command: {args.command}")


def api_or_cli(args: argparse.Namespace, path: str, cli_args: list[str]) -> Any:
    url = args.api_base.rstrip("/") + path
    try:
        return http_json(url)
    except Exception:
        return cli_json(Path(args.repo_root), cli_args)


def http_json(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def cli_json(repo_root: Path, args: list[str]) -> Any:
    command = [sys.executable, "-m", "emf_macro.cli", *args]
    env = os.environ.copy()
    src = repo_root.resolve() / "src"
    if src.exists():
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(src) if not existing else f"{src}{os.pathsep}{existing}"
    result = subprocess.run(
        command,
        cwd=repo_root,
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def clean_query(values: dict[str, object]) -> str:
    clean = {key: value for key, value in values.items() if value is not None}
    return urllib.parse.urlencode(clean)


def multi_query(values: dict[str, list[str] | None]) -> str:
    clean: list[tuple[str, str]] = []
    for key, items in values.items():
        for item in items or []:
            clean.append((key, item))
    return urllib.parse.urlencode(clean)


def print_json(payload: Any, pretty: bool = False) -> None:
    if pretty:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())

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
    parser = argparse.ArgumentParser(description="Query Marco agent artifacts.")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--pretty", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("context", help="get agent context; API first, CLI fallback")
    sub.add_parser("runs", help="list runs; API first, CLI fallback")
    run = sub.add_parser("run", help="show run summary")
    run.add_argument("--run-id", default="latest")

    metrics = sub.add_parser("metrics", help="query model metrics")
    metrics.add_argument("--run-id", default="latest")
    metrics.add_argument("--pair")
    metrics.add_argument("--horizon", type=int)
    metrics.add_argument("--model-id")

    best = sub.add_parser("best", help="query best model rows")
    best.add_argument("--run-id", default="latest")
    best.add_argument("--pair")
    best.add_argument("--horizon", type=int)

    sub.add_parser("public-summary", help="fetch the live static summary from choir-ip.com")

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


def print_json(payload: Any, pretty: bool = False) -> None:
    if pretty:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())

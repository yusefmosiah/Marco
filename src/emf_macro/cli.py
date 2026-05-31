from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import run_fx_rate_lab


def main() -> None:
    parser = argparse.ArgumentParser(prog="emf-macro")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run-fx-rate-lab", help="run the FRED FX/rate differential foundation pipeline")
    run.add_argument("--root", default=".", help="repo root")
    run.add_argument("--evaluation-start", default="2006-01")
    run.add_argument("--horizons", default="1,3,6", help="comma-separated month horizons")
    args = parser.parse_args()

    if args.command == "run-fx-rate-lab":
        horizons = tuple(int(part) for part in args.horizons.split(",") if part.strip())
        result = run_fx_rate_lab(Path(args.root).resolve(), args.evaluation_start, horizons)
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

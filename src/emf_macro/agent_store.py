from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_LAB = "fred-fx-rate-lab"


class ArtifactNotFoundError(FileNotFoundError):
    pass


@dataclass(frozen=True)
class ArtifactStore:
    root: Path
    lab: str = DEFAULT_LAB

    @property
    def artifact_root(self) -> Path:
        return self.root / "artifacts" / self.lab

    def run_dirs(self) -> list[Path]:
        if not self.artifact_root.exists():
            return []
        return sorted(
            path
            for path in self.artifact_root.iterdir()
            if path.is_dir() and (path / "summary.json").exists()
        )

    def resolve_run_id(self, run_id: str = "latest") -> str:
        runs = self.list_runs()
        if not runs:
            raise ArtifactNotFoundError(f"no artifact runs found under {self.artifact_root}")
        if run_id == "latest":
            return runs[-1]["run_id"]
        if any(run["run_id"] == run_id for run in runs):
            return run_id
        raise ArtifactNotFoundError(f"run not found: {run_id}")

    def run_dir(self, run_id: str = "latest") -> Path:
        resolved = self.resolve_run_id(run_id)
        return self.artifact_root / resolved

    def load_summary(self, run_id: str = "latest") -> dict[str, Any]:
        path = self.run_dir(run_id) / "summary.json"
        return load_json(path)

    def load_report(self, run_id: str = "latest") -> str:
        path = self.run_dir(run_id) / "report.md"
        if not path.exists():
            raise ArtifactNotFoundError(f"report not found: {path}")
        return path.read_text(encoding="utf-8")

    def list_runs(self) -> list[dict[str, Any]]:
        rows = []
        for run_dir in self.run_dirs():
            summary = load_json(run_dir / "summary.json")
            rows.append(
                {
                    "run_id": summary["run_id"],
                    "created_at": summary.get("created_at"),
                    "status": summary.get("headline", {}).get("status"),
                    "vintage_policy": summary.get("vintage_policy"),
                    "lookahead_status": summary.get("lookahead_status"),
                    "pairs": summary.get("pairs", []),
                    "horizons": summary.get("horizons", []),
                    "models": summary.get("models", []),
                    "artifact_dir": str(run_dir),
                    "summary_sha256": sha256_file(run_dir / "summary.json"),
                }
            )
        return sorted(rows, key=lambda row: row["run_id"])

    def filter_metrics(
        self,
        run_id: str = "latest",
        *,
        pair: str | None = None,
        horizon_months: int | None = None,
        model_id: str | None = None,
    ) -> list[dict[str, Any]]:
        summary = self.load_summary(run_id)
        rows = summary.get("metrics", [])
        if pair is not None:
            rows = [row for row in rows if row.get("pair") == pair]
        if horizon_months is not None:
            rows = [row for row in rows if row.get("horizon_months") == horizon_months]
        if model_id is not None:
            rows = [row for row in rows if row.get("model_id") == model_id]
        return sorted(rows, key=lambda row: (row.get("pair", ""), row.get("horizon_months", 0), row.get("rmse", 0)))

    def filter_best(
        self,
        run_id: str = "latest",
        *,
        pair: str | None = None,
        horizon_months: int | None = None,
    ) -> list[dict[str, Any]]:
        summary = self.load_summary(run_id)
        rows = summary.get("best_by_rmse", [])
        if pair is not None:
            rows = [row for row in rows if row.get("pair") == pair]
        if horizon_months is not None:
            rows = [row for row in rows if row.get("horizon_months") == horizon_months]
        return sorted(rows, key=lambda row: (row.get("pair", ""), row.get("horizon_months", 0)))

    def agent_context(self, run_id: str = "latest", public_base_url: str | None = None) -> dict[str, Any]:
        resolved = self.resolve_run_id(run_id)
        summary = self.load_summary(resolved)
        runs = self.list_runs()
        context = {
            "schema_version": "marco.agent_context.v1",
            "name": "Marco FRED FX/Rate Macro Lab",
            "description": "Agent-readable access to Marco macro backtest artifacts.",
            "active_run_id": resolved,
            "available_runs": runs,
            "active_run": {
                "run_id": summary["run_id"],
                "created_at": summary.get("created_at"),
                "headline": summary.get("headline", {}),
                "vintage_policy": summary.get("vintage_policy"),
                "lookahead_status": summary.get("lookahead_status"),
                "config": summary.get("config", {}),
                "pairs": summary.get("pairs", []),
                "horizons": summary.get("horizons", []),
                "models": summary.get("models", []),
                "best_by_rmse": summary.get("best_by_rmse", []),
            },
            "constraints": [
                "Current artifacts are latest-revised snapshots, not ALFRED real-time vintages.",
                "Random-walk/no-change baselines must remain explicit comparison points.",
                "The current API is read-only over committed artifacts.",
            ],
            "cli_examples": [
                "emf-macro list-runs --root .",
                "emf-macro show-run --root . --run-id latest",
                "emf-macro metrics --root . --run-id latest --pair USD_CAD --horizon 6",
                "emf-macro agent-context --root . --run-id latest",
                "emf-macro serve-agent-api --root . --host 127.0.0.1 --port 8765",
            ],
            "api_endpoints": [
                "GET /health",
                "GET /v1/runs",
                "GET /v1/runs/latest",
                "GET /v1/runs/latest/metrics?pair=USD_CAD&horizon_months=6",
                "GET /v1/runs/latest/best",
                "GET /v1/runs/latest/report",
                "GET /v1/agent-context",
            ],
        }
        if public_base_url:
            base = public_base_url.rstrip("/")
            context["public_urls"] = {
                "app": base + "/",
                "agent_context": base + "/api/v1/agent-context",
                "runs": base + "/api/v1/runs",
                "active_run": base + f"/api/v1/runs/{resolved}",
            }
        return context


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ArtifactNotFoundError(f"artifact not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

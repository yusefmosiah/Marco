from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .macro_forecast import MacroForecastConfig, run_macro_forecast_lab


AGENT_SCHEMA = "marco.economic_model_agent.v1"
HANDOFF_SCHEMA = "marco.agent_handoff.v1"
AGENT_ID = "economic_modeling_agent"


def run_economic_model_agent(
    root: Path,
    *,
    horizon_months: int = 6,
    target: str | None = None,
    model_id: str | None = None,
    refresh: bool = False,
    write_handoff: bool = True,
) -> dict[str, Any]:
    generated_at = utc_now_iso()
    run_id = f"{AGENT_ID}-{generated_at.replace('-', '').replace(':', '').replace('T', '-').replace('Z', '')}"
    summary_path = root / "data" / "backtests" / "macro-forecast-lab" / "summary.json"
    if refresh or not summary_path.exists():
        summary = run_macro_forecast_lab(
            MacroForecastConfig(
                root=root,
                horizon_months=horizon_months,
            )
        )
    else:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))

    output_dir = resolve_summary_path(root, summary["output_dir"])
    metrics = filter_rows(summary.get("metrics", []), target=target, model_id=model_id)
    predictions = load_latest_predictions(output_dir / "predictions.jsonl", target=target, model_id=model_id)
    payload = {
        "schema_version": AGENT_SCHEMA,
        "agent_id": AGENT_ID,
        "run_id": run_id,
        "generated_at": generated_at,
        "name": "Marco Economic Model Agent",
        "purpose": "Provide structured macro forecasts for downstream research and news agents.",
        "inputs": {
            "source_data": "FRED-MD latest-revised snapshot",
            "horizon_months": summary["horizon_months"],
            "target_filter": target,
            "model_filter": model_id,
        },
        "caveats": [
            "Uses latest-revised FRED-MD data, not real-time ALFRED vintages.",
            "growth_proxy_yoy is industrial-production YoY, not true quarterly GDP.",
            "Forecasts must be interpreted against baseline metrics.",
        ],
        "summary": {
            "vintage_policy": summary["vintage_policy"],
            "lookahead_status": summary["lookahead_status"],
            "horizon_months": summary["horizon_months"],
            "targets": summary["targets"],
            "models": summary["models"],
            "output_dir": summary["output_dir"],
            "plots": summary.get("plots", {}),
        },
        "metrics": metrics,
        "latest_forecasts": predictions,
    }
    if write_handoff:
        payload["handoff"] = write_agent_handoff(root, payload)
    return payload


def filter_rows(rows: list[dict[str, Any]], *, target: str | None, model_id: str | None) -> list[dict[str, Any]]:
    filtered = rows
    if target:
        filtered = [row for row in filtered if row.get("target") == target]
    if model_id:
        filtered = [row for row in filtered if row.get("model_id") == model_id]
    return filtered


def load_latest_predictions(path: Path, *, target: str | None, model_id: str | None) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    df = pd.read_json(path, lines=True)
    if target:
        df = df[df["target"] == target]
    if model_id:
        df = df[df["model_id"] == model_id]
    if df.empty:
        return []
    latest = df.sort_values(["target", "model_id", "forecast_origin"]).groupby(["target", "model_id"], as_index=False).tail(1)
    columns = [
        "target",
        "model_id",
        "forecast_origin",
        "target_period",
        "actual",
        "prediction",
        "error",
        "selected_factors",
    ]
    available_columns = [column for column in columns if column in latest.columns]
    return latest[available_columns].sort_values(["target", "model_id"]).to_dict(orient="records")


def write_agent_handoff(root: Path, payload: dict[str, Any]) -> dict[str, str]:
    run_dir = root / "data" / "agents" / "runs" / AGENT_ID / payload["run_id"]
    latest_path = root / "data" / "agents" / "latest" / f"{AGENT_ID}.md"
    state_path = root / "data" / "agents" / "state" / f"{AGENT_ID}.json"
    run_dir.mkdir(parents=True, exist_ok=True)
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    output_md = render_handoff_markdown(payload, output_path=(run_dir / "output.md").relative_to(root))
    write_text_atomic(run_dir / "input.md", render_input_markdown(payload))
    write_text_atomic(run_dir / "output.md", output_md)
    write_json_atomic(
        run_dir / "status.json",
        {
            "schema_version": "marco.agent_run_status.v1",
            "agent_id": AGENT_ID,
            "run_id": payload["run_id"],
            "status": "succeeded",
            "generated_at": payload["generated_at"],
        },
    )
    write_json_atomic(
        run_dir / "artifacts.json",
        {
            "schema_version": "marco.agent_run_artifacts.v1",
            "agent_id": AGENT_ID,
            "run_id": payload["run_id"],
            "refs": [
                payload["summary"]["output_dir"],
                f"{payload['summary']['output_dir']}/summary.json",
                f"{payload['summary']['output_dir']}/metrics.json",
                f"{payload['summary']['output_dir']}/predictions.jsonl",
            ],
        },
    )
    write_text_atomic(run_dir / "logs.jsonl", json.dumps({"event": "completed", "run_id": payload["run_id"]}, sort_keys=True) + "\n")
    write_text_atomic(latest_path, output_md)
    write_json_atomic(
        state_path,
        {
            "schema_version": "marco.agent_state.v1",
            "agent_id": AGENT_ID,
            "last_run_id": payload["run_id"],
            "updated_at": payload["generated_at"],
            "latest_path": str(latest_path.relative_to(root)),
        },
    )
    return {
        "run_dir": str(run_dir.relative_to(root)),
        "latest_path": str(latest_path.relative_to(root)),
        "state_path": str(state_path.relative_to(root)),
    }


def render_input_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {payload['name']} Input",
            "",
            "```json",
            json.dumps(payload["inputs"], indent=2, sort_keys=True),
            "```",
            "",
        ]
    )


def render_handoff_markdown(payload: dict[str, Any], *, output_path: Path) -> str:
    metric_lines = [format_metric(row) for row in payload["metrics"][:12]]
    forecast_lines = [format_forecast(row) for row in payload["latest_forecasts"][:12]]
    summary = payload["summary"]
    output_dir = summary["output_dir"]
    return "\n".join(
        [
            "---",
            f"schema_version: {HANDOFF_SCHEMA}",
            f"agent_id: {AGENT_ID}",
            f"run_id: {payload['run_id']}",
            f"generated_at: {payload['generated_at']}",
            "status: succeeded",
            "input_refs:",
            "  - data/fred-fx-rate-lab/source_manifest.json",
            "output_refs:",
            f"  - {output_path}",
            f"  - {output_dir}/summary.json",
            f"  - {output_dir}/metrics.json",
            f"  - {output_dir}/predictions.jsonl",
            "evidence_refs:",
            f"  - {output_dir}",
            "next_run_requests: []",
            "---",
            "",
            "# Economic Modeling Agent Handoff",
            "",
            "## Current Answer",
            "",
            f"Marco has a latest-revised FRED-MD macro forecast lab for a `{summary['horizon_months']}M` horizon. "
            f"It compares `{', '.join(summary['models'])}` on interest-rate, inflation, and industrial-production growth-proxy targets.",
            "",
            "## Evidence",
            "",
            f"- Vintage policy: `{summary['vintage_policy']}`",
            f"- Lookahead status: `{summary['lookahead_status']}`",
            f"- Artifact directory: `{output_dir}`",
            f"- Targets: `{', '.join(summary['targets'].keys())}`",
            "",
            "Metric sample:",
            *(metric_lines or ["- No metric rows matched the current filters."]),
            "",
            "Latest forecast sample:",
            *(forecast_lines or ["- No forecast rows matched the current filters."]),
            "",
            "## Changes Since Previous Run",
            "",
            "- Integrated macro forecast artifacts into the Marco multiagent handoff surface.",
            "",
            "## Caveats",
            "",
            *[f"- {caveat}" for caveat in payload["caveats"]],
            "",
            "## Open Questions",
            "",
            "- Which targets should move from latest-revised FRED-MD snapshots to real-time vintage-safe evaluation first?",
            "- Which external central-bank and global macro sources should be joined before testing richer rate/FX hypotheses?",
            "",
            "## Suggested Next Runs",
            "",
            "- Re-run with real-time ALFRED vintages for policy-rate and inflation targets.",
            "- Join ECB, World Bank, and Fed communications features to test whether text/event features improve baselines.",
            "",
        ]
    )


def format_metric(row: dict[str, Any]) -> str:
    parts = [
        f"`{row.get('target')}`",
        f"`{row.get('model_id')}`",
        f"n={row.get('n')}",
    ]
    for key in ["mae", "rmse", "r_squared", "directional_accuracy"]:
        if key in row:
            parts.append(f"{key}={format_number(row[key])}")
    return f"- {'; '.join(parts)}"


def format_forecast(row: dict[str, Any]) -> str:
    return (
        f"- `{row.get('target')}` `{row.get('model_id')}`: "
        f"{row.get('forecast_origin')} -> {row.get('target_period')}, "
        f"prediction={format_number(row.get('prediction'))}, actual={format_number(row.get('actual'))}"
    )


def format_number(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_text_atomic(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def write_json_atomic(path: Path, payload: Any) -> None:
    write_text_atomic(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def resolve_summary_path(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path

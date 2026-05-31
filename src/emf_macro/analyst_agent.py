from __future__ import annotations

import json
import os
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


AGENT_ID = "analyst_agent"
AGENT_SCHEMA = "marco.analyst_agent.v1"
HANDOFF_SCHEMA = "marco.agent_handoff.v1"
DEFAULT_OUTPUT = Path("output/analyst/financial-news-ingestion-latest.json")


def run_analyst_agent(
    root: Path,
    *,
    run_codex: bool = False,
    prompt: str | None = None,
    model: str | None = None,
    model_reasoning_effort: str = "medium",
    write_handoff: bool = False,
    timeout_seconds: int = 900,
) -> dict[str, Any]:
    root = root.resolve()
    command_result: dict[str, Any] | None = None
    if run_codex:
        command_result = run_codex_ingestion(
            root,
            prompt=prompt,
            model=model,
            model_reasoning_effort=model_reasoning_effort,
            timeout_seconds=timeout_seconds,
        )

    payload_path = latest_payload_path(root)
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    report_path = latest_report_path(payload_path)
    generated_at = utc_now_iso()
    run_id = f"{AGENT_ID}-{generated_at.replace('-', '').replace(':', '').replace('T', '-').replace('Z', '')}"
    articles = payload.get("articles", [])
    packet: dict[str, Any] = {
        "schema_version": AGENT_SCHEMA,
        "agent_id": AGENT_ID,
        "run_id": run_id,
        "generated_at": generated_at,
        "name": "Marco Analyst Agent",
        "purpose": "Collect, structure, and audit financial news ingestion outputs for downstream synthesis.",
        "inputs": {
            "payload_path": str(payload_path.relative_to(root)),
            "report_path": str(report_path.relative_to(root)) if report_path else None,
            "codex_invoked": run_codex,
            "model": model,
            "model_reasoning_effort": model_reasoning_effort,
        },
        "summary": {
            "source_payload_schema": payload.get("agent_id"),
            "article_count": payload.get("article_count", len(articles)),
            "window_start": payload.get("window_start"),
            "window_end": payload.get("window_end"),
            "retrieval_error_count": len(payload.get("retrieval_errors", [])),
            "domain_counts": dict(sorted(Counter(article.get("domain", "unknown") for article in articles).items())),
            "source_counts": dict(sorted(Counter(article.get("source_name", "unknown") for article in articles).items())),
        },
        "latest_articles": articles[:12],
        "retrieval_errors": payload.get("retrieval_errors", []),
        "caveats": [
            "This is an analyst/news-ingestion specialist packet, not a final investment recommendation.",
            "The Codex SDK run path requires local Codex auth and installed analyst CLI dependencies.",
            "Source text fidelity should be spot-checked before any downstream sentiment or synthesis claim.",
        ],
    }
    if command_result is not None:
        packet["codex_run"] = command_result
    if write_handoff:
        packet["handoff"] = write_analyst_handoff(root, packet)
    return packet


def run_codex_ingestion(
    root: Path,
    *,
    prompt: str | None,
    model: str | None,
    model_reasoning_effort: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    script = root / "apps" / "analyst-cli" / "bin" / "analyst-rag.js"
    package_dir = root / "apps" / "analyst-cli"
    if not script.exists():
        raise FileNotFoundError(f"analyst CLI script not found: {script}")
    if not (package_dir / "node_modules").exists():
        raise FileNotFoundError("apps/analyst-cli/node_modules is missing; run `npm ci` in apps/analyst-cli")

    output = DEFAULT_OUTPUT
    report_output = output.with_suffix(".summary.md")
    cmd = [
        "node",
        str(script),
        "run-ingestion",
        "--root",
        str(root),
        "--output",
        str(output),
        "--report-output",
        str(report_output),
        "--model-reasoning-effort",
        model_reasoning_effort,
    ]
    if model:
        cmd.extend(["--model", model])
    if prompt:
        cmd.extend(["--prompt", prompt])

    env = os.environ.copy()
    env.setdefault("MARCO_CODEX_REASONING_EFFORT", model_reasoning_effort)
    if model:
        env.setdefault("MARCO_CODEX_MODEL", model)
    completed = subprocess.run(
        cmd,
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"analyst Codex CLI failed with exit {completed.returncode}: {completed.stderr.strip()}")
    return {
        "command": " ".join(cmd),
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
        "output_path": str(output),
        "report_output": str(report_output),
    }


def latest_payload_path(root: Path) -> Path:
    preferred = root / DEFAULT_OUTPUT
    if preferred.exists():
        return preferred
    candidates = sorted((root / "output" / "analyst").glob("financial-news-ingestion-*.json"))
    if not candidates:
        raise FileNotFoundError("no analyst JSON payloads found under output/analyst")
    return candidates[-1]


def latest_report_path(payload_path: Path) -> Path | None:
    candidates = [
        payload_path.with_suffix(".summary.md"),
        payload_path.with_suffix(".validation.md"),
        payload_path.with_name(f"{payload_path.stem}.validation.md"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def write_analyst_handoff(root: Path, packet: dict[str, Any]) -> dict[str, str]:
    run_dir = root / "data" / "agents" / "runs" / AGENT_ID / packet["run_id"]
    latest_path = root / "data" / "agents" / "latest" / f"{AGENT_ID}.md"
    state_path = root / "data" / "agents" / "state" / f"{AGENT_ID}.json"
    run_dir.mkdir(parents=True, exist_ok=True)
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    output_md = render_analyst_handoff(packet, output_path=(run_dir / "output.md").relative_to(root))
    write_text_atomic(run_dir / "input.md", render_input_markdown(packet))
    write_text_atomic(run_dir / "output.md", output_md)
    write_json_atomic(run_dir / "status.json", {"schema_version": "marco.agent_run_status.v1", "agent_id": AGENT_ID, "run_id": packet["run_id"], "status": "succeeded", "generated_at": packet["generated_at"]})
    write_json_atomic(run_dir / "artifacts.json", {"schema_version": "marco.agent_run_artifacts.v1", "agent_id": AGENT_ID, "run_id": packet["run_id"], "refs": [packet["inputs"]["payload_path"], packet["inputs"]["report_path"]]})
    write_text_atomic(run_dir / "logs.jsonl", json.dumps({"event": "completed", "run_id": packet["run_id"]}, sort_keys=True) + "\n")
    write_text_atomic(latest_path, output_md)
    write_json_atomic(state_path, {"schema_version": "marco.agent_state.v1", "agent_id": AGENT_ID, "last_run_id": packet["run_id"], "updated_at": packet["generated_at"], "latest_path": str(latest_path.relative_to(root))})
    return {"run_dir": str(run_dir.relative_to(root)), "latest_path": str(latest_path.relative_to(root)), "state_path": str(state_path.relative_to(root))}


def render_input_markdown(packet: dict[str, Any]) -> str:
    return "# Analyst Agent Input\n\n```json\n" + json.dumps(packet["inputs"], indent=2, sort_keys=True) + "\n```\n"


def render_analyst_handoff(packet: dict[str, Any], *, output_path: Path) -> str:
    summary = packet["summary"]
    articles = packet["latest_articles"][:8]
    return "\n".join(
        [
            "---",
            f"schema_version: {HANDOFF_SCHEMA}",
            f"agent_id: {AGENT_ID}",
            f"run_id: {packet['run_id']}",
            f"generated_at: {packet['generated_at']}",
            "status: succeeded",
            "input_refs:",
            f"  - {packet['inputs']['payload_path']}",
            "output_refs:",
            f"  - {output_path}",
            "evidence_refs:",
            f"  - {packet['inputs']['payload_path']}",
            "next_run_requests: []",
            "---",
            "",
            "# Analyst Agent Handoff",
            "",
            "## Current Answer",
            "",
            f"The analyst ingestion packet covers {summary['article_count']} articles from {summary['window_start']} through {summary['window_end']}.",
            "",
            "## Evidence",
            "",
            f"- Payload: `{packet['inputs']['payload_path']}`",
            f"- Report: `{packet['inputs'].get('report_path')}`",
            f"- Domain counts: `{summary['domain_counts']}`",
            f"- Source counts: `{summary['source_counts']}`",
            f"- Retrieval errors: `{summary['retrieval_error_count']}`",
            "",
            "Latest article sample:",
            *[format_article(article) for article in articles],
            "",
            "## Changes Since Previous Run",
            "",
            "- Promoted the analyst ingestion output into the shared Marco agent handoff surface.",
            "",
            "## Caveats",
            "",
            *[f"- {caveat}" for caveat in packet["caveats"]],
            "",
            "## Open Questions",
            "",
            "- Which downstream sentiment or synthesis agent should consume this ingestion payload first?",
            "- Which sources should move from Codex-led retrieval to deterministic fetch adapters?",
            "",
            "## Suggested Next Runs",
            "",
            "- Run Codex ingestion with an explicit model and medium reasoning effort after confirming local Codex auth.",
            "- Convert recurring analyst sources into deterministic source-ledger feeds where possible.",
            "",
        ]
    )


def format_article(article: dict[str, Any]) -> str:
    return f"- `{article.get('article_id')}` `{article.get('domain')}` {article.get('source_name')}: {article.get('headline')}"


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_text_atomic(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def write_json_atomic(path: Path, payload: Any) -> None:
    write_text_atomic(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")

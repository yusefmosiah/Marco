# Marco Agent API And CLI

Date: 2026-05-31

Status: initial read-only agent surface

## Goal

Agents should not have to scrape the Svelte UI or guess file paths. Marco now
has two stable machine surfaces over committed artifacts:

- CLI commands through `emf-macro`;
- a dependency-free local HTTP JSON API.

The first surface is read-only over committed artifact bundles. Running new
backtests remains an explicit CLI operation until there is authentication, job
isolation, and a run queue.

## Install

From the repo:

```sh
uv venv .venv
uv pip install --python .venv/bin/python -e '.[dev]'
```

For lightweight read-only use, the agent commands do not import pandas or
scikit-learn. A Python process with `PYTHONPATH=src` can call them directly:

```sh
PYTHONPATH=src python3 -m emf_macro.cli list-runs --root .
```

## CLI

List artifact runs:

```sh
emf-macro list-runs --root .
```

Show the latest run summary:

```sh
emf-macro show-run --root . --run-id latest
```

Query model metrics:

```sh
emf-macro metrics --root . --run-id latest --pair USD_CAD --horizon 6
```

Query best model rows:

```sh
emf-macro best --root . --run-id latest --pair USD_CAD --horizon 6
```

Emit the agent context packet:

```sh
emf-macro agent-context --root . --run-id latest
```

Print the Markdown report:

```sh
emf-macro report --root . --run-id latest
```

Use `--compact` on JSON commands when another agent or shell pipeline will parse
the output.

## HTTP API

Start the local read-only API:

```sh
emf-macro serve-agent-api --root . --host 127.0.0.1 --port 8765 \
  --public-base-url https://choir-ip.com/marco
```

Endpoints:

```text
GET /health
GET /v1/runs
GET /v1/runs/latest
GET /v1/runs/latest/metrics?pair=USD_CAD&horizon_months=6
GET /v1/runs/latest/best
GET /v1/runs/latest/report
GET /v1/agent-context
```

Example:

```sh
curl -s 'http://127.0.0.1:8765/v1/runs/latest/metrics?pair=USD_CAD&horizon_months=6' | jq
```

## Agent Context Shape

`GET /v1/agent-context` and `emf-macro agent-context` return:

```text
schema_version
name
description
active_run_id
available_runs
active_run
constraints
cli_examples
api_endpoints
public_urls, when --public-base-url is provided
```

The packet is intended to be the first thing an external coding or research
agent reads before deciding which specific endpoint or CLI command to call.

## Current Guardrails

- The API is read-only.
- The current artifact is `latest_revised_snapshot`, not vintage-safe ALFRED
  evidence.
- Baselines remain first-class outputs; agents should not summarize model
  results without comparing against random-walk/no-change rows.
- The HTTP server is intentionally dependency-free and local-first. Put it
  behind Caddy/auth before exposing mutating routes.

## Live Static Artifact

The current public preview is still static:

```text
https://choir-ip.com/marco/
https://choir-ip.com/marco/artifacts/fred-fx-rate-lab-summary.json
```

The dynamic local API can be mounted under `/marco/api/` later once Node A has a
durable service definition for it.

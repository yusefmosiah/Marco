# Marco Agent API And CLI

Date: 2026-05-31

Status: initial read-only agent surface

## Goal

Agents should not have to scrape the Svelte UI or guess file paths. Marco now
has two stable machine surfaces over committed artifacts:

- CLI commands through `emf-macro`;
- a dependency-free local HTTP JSON API.

The planned multiagent runtime contract is documented in
`docs/agents/multiagent-runtime-harness.md`.

The intended public shape is not one giant agent endpoint. Marco should expose
three specialist agent APIs plus a chatbot API/GUI:

```text
economic_modeling_agent API
news_agent API
analyst_agent API
ui_chatbot_agent API + website chat interface
```

The chatbot reads the latest markdown reports from the three specialist agents
by default. When a user asks for a custom answer, the chatbot may call a
specialist API to create a bounded run request, then consume that agent's next
report.

The first surface is read-only over committed artifact bundles. Running new
backtests remains an explicit CLI operation until there is authentication, job
isolation, and a run queue.

Implemented specialist endpoints:

```text
GET /v1/agents/economic-modeling-agent
GET /v1/agents/news-agent
GET /v1/agents/analyst-agent
```

All three return a JSON packet on their own. By default these endpoints are
read-only and do not replace `data/agents/latest/*.md`. Pass
`write_handoff=true` only for controlled local runs that should update the
shared markdown handoff files. For `news-agent`, pass `run=true` to run the
deterministic news model wrapper and `fetch=true` to fetch feeds. For
`analyst-agent`, pass `run=true` to invoke the Codex SDK CLI.

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

## Analyst Agentic RAG CLI

The Analyst agent can also run as a Codex SDK-powered CLI under
`apps/analyst-cli`. This is the portable path for a personal server.

```sh
cd apps/analyst-cli
npm install
node ./bin/analyst-rag.js retrieve "financial news ingestion macro fed"
node ./bin/analyst-rag.js run-ingestion \
  --root ../.. \
  --output output/analyst/financial-news-ingestion-latest.json
```

What this wrapper does:

- loads `OPENAI_API_KEY` from the environment or repo root `.env.local`;
- retrieves local context from `agents/analyst.toml`, Marco docs, artifacts, and
  previous Analyst outputs;
- starts a Codex SDK thread in the repo root;
- passes the Analyst JSON schema for `run-ingestion`;
- validates approved source domains, stable IDs, and excerpt length before
  writing output;
- writes a one-page Markdown summary report with an audit section next to the
  JSON output, or at `--report-output` when supplied.

The Codex SDK package wraps the `codex` CLI and exchanges JSONL events with it,
so the server needs Node 18+ and the SDK installed with
`npm install @openai/codex-sdk`, following
<https://developers.openai.com/codex/sdk>. The Codex CLI also needs a writable
home directory for local state.

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
GET /v1/datasets
GET /v1/models
GET /v1/hypotheses
GET /v1/experiment-plan?pair=USD_CAD&horizon_months=6
GET /v1/global-panel
GET /v1/news
GET /v1/news/sources
GET /v1/news/items?source_id=ecb_press&limit=10
GET /v1/news/fetches?limit=10
GET /v1/economic-model-agent?target=interest_rate&model_id=var
GET /v1/agent-context
```

Example:

```sh
curl -s 'http://127.0.0.1:8765/v1/runs/latest/metrics?pair=USD_CAD&horizon_months=6' | jq
```

Global macro panel summary:

```sh
emf-macro global-panel-summary --root . --haul-id global_macro_starter_20260531
curl -s 'http://127.0.0.1:8765/v1/global-panel?haul_id=global_macro_starter_20260531' | jq
```

Source-haul commands:

```sh
emf-macro source-hauls --root .
emf-macro run-source-haul global_macro_starter_20260531 --root .
emf-macro build-global-panel --root . --haul-id global_macro_starter_20260531
```

Macro news source-ledger commands:

```sh
emf-macro news-sources --root .
emf-macro news-fetch --root .
emf-macro news-summary --root .
emf-macro news-items --root . --limit 10
emf-macro news-fetches --root . --limit 10
emf-macro news-agent-run --root .
```

The news CLI is the first interface for the future news agent. It should cite
exact `news_item.id` values from `news-items`, not inferred recent feed rows.
`news-agent-run` maintains `data/macro-news/model.md`, `model_state.json`, and
per-fetch journals under `data/macro-news/fetch-journal/`.

Economic modeling commands:

```sh
emf-macro run-macro-forecast-lab --root .
emf-macro economic-model-agent --root .
emf-macro economic-model-agent --root . --target interest_rate --model-id var
```

`run-macro-forecast-lab` writes forecast artifacts under
`data/backtests/macro-forecast-lab/`. `economic-model-agent` reads those
artifacts and writes the shared multiagent handoff at
`data/agents/latest/economic_modeling_agent.md`, plus immutable run files under
`data/agents/runs/economic_modeling_agent/`.

Analyst agent commands:

```sh
emf-macro analyst-agent --root .
emf-macro analyst-agent --root . --write-handoff
emf-macro analyst-agent --root . --run-codex --model "$MARCO_CODEX_MODEL" --model-reasoning-effort medium --write-handoff
```

The Analyst agent is the Codex SDK-backed specialist. The Python command reads
the latest Analyst JSON artifact by default, and can invoke
`apps/analyst-cli/bin/analyst-rag.js` when `--run-codex` is passed. Configure
the live Codex run with `MARCO_CODEX_MODEL` and
`MARCO_CODEX_REASONING_EFFORT=medium`, or with the CLI flags shown above.

Macro news API:

```sh
curl -s 'http://127.0.0.1:8765/v1/news' | jq
curl -s 'http://127.0.0.1:8765/v1/news/items?limit=5' | jq
```

Economic modeling API:

```sh
curl -s 'http://127.0.0.1:8765/v1/economic-model-agent?target=interest_rate&model_id=var' | jq
curl -s 'http://127.0.0.1:8765/v1/agents/economic-modeling-agent?target=interest_rate&model_id=var' | jq
curl -s 'http://127.0.0.1:8765/v1/agents/news-agent' | jq
curl -s 'http://127.0.0.1:8765/v1/agents/analyst-agent' | jq
```

The API is read-only by default. Use the CLI when updating committed handoff
files; pass `write_handoff=true` only for controlled local runs that should
replace `data/agents/latest/*.md`.

## LLM Gateway

Marco's committed news model agent is deterministic today. The next synthesis
agent should use the go-choir gateway instead of storing provider credentials in
this repo or in the Marco web app.

Current preferred synthesis model:

```text
provider = fireworks
model = accounts/fireworks/models/deepseek-v4-flash
reasoning_effort = medium
```

Node A has the go-choir gateway on `127.0.0.1:8084`. Provider credentials are
deployed from `/Users/wiz/go-choir/.env` with:

```sh
cd /Users/wiz/go-choir
./nix/deploy-provider-creds.sh node-a
```

Gateway calls should explicitly set `provider`, `model`, and
`reasoning_effort`; do not rely on the gateway's provider default model. The
gateway keeps Fireworks, search, and other provider keys host-side and issues
short caller credentials for authenticated runtime clients.

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
- Dataset upload/fetch mutation is local CLI-only for now:
  `dataset-add` and `dataset-fetch-url`.
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
https://choir-ip.com/marco/artifacts/global-macro-panel-summary.json
https://choir-ip.com/marco/artifacts/macro-news-summary.json
```

The dynamic local API can be mounted under `/marco/api/` later once Node A has a
durable service definition for it.

## Dataset And Experiment Planning

Local dataset registry:

```sh
emf-macro dataset-add sample.csv --root . --name "Sample Dataset"
emf-macro dataset-fetch-url https://example.com/data.csv --root . --name "External Dataset"
emf-macro list-datasets --root .
```

Model ladder and hypotheses:

```sh
emf-macro models
emf-macro suggest-hypotheses --root . --run-id latest
```

Parallel experiment plan:

```sh
emf-macro plan-experiments --root . --pair USD_CAD --horizon 6 --max-parallelism 4
```

# Setup

Date: 2026-05-31

## Required Tools

Core:

```text
uv
Python 3.11+
Node.js 22+
npm
git
curl
```

Useful but optional:

```text
jq      inspect JSON artifacts and API responses
gh      GitHub Actions/secrets/repo operations
rsync   Node A static deploy
ssh     Node A static deploy
```

## Recommended Setup

Use `uv`. It is the default for this repo because it is fast, simple, and keeps
the Python environment local to `.venv`.

```sh
tools/bootstrap.sh
```

Equivalent manual setup:

```sh
uv sync --extra dev

cd apps/web
npm ci
```

## Common Commands

Run tests:

```sh
make test
```

Build the frontend:

```sh
make web-build
```

Check runtime dependency audit for the static frontend:

```sh
cd apps/web
npm audit --omit=dev
```

`npm ci` may report dev-toolchain audit findings from Vite/Svelte transitive
dependencies. The runtime dependency audit above is the relevant check for the
deployed static artifact.

Run the same local checks as CI:

```sh
make ci
```

Inspect the latest artifact for agents:

```sh
make agent-context
```

Create a local dataset registry entry:

```sh
.venv/bin/emf-macro dataset-add path/to/data.csv --root . --name "My Dataset"
```

Plan a parallel backtest matrix:

```sh
.venv/bin/emf-macro plan-experiments --root . --pair USD_CAD --horizon 6
```

Run the macro forecast lab and update the economic modeling agent handoff:

```sh
.venv/bin/emf-macro run-macro-forecast-lab --root .
.venv/bin/emf-macro economic-model-agent --root .
```

Serve the read-only local agent API:

```sh
make serve-agent-api
```

Then query:

```sh
curl -s http://127.0.0.1:8765/v1/agent-context | jq
curl -s 'http://127.0.0.1:8765/v1/runs/latest/metrics?pair=USD_CAD&horizon_months=6' | jq
```

## Public Preview

Current Node A static preview:

```text
https://choir-ip.com/marco/
```

Current public JSON artifact:

```text
https://choir-ip.com/marco/artifacts/fred-fx-rate-lab-summary.json
```

## Notes For Agents

If package install has not happened, read-only commands can still run from the
repo with:

```sh
PYTHONPATH=src python3 -m emf_macro.cli list-runs --root .
PYTHONPATH=src python3 -m emf_macro.cli agent-context --root . --compact
```

The repo-local skill for this workflow is:

```text
skills/marco-agent-api/SKILL.md
```

The skill helper can query local API, CLI fallback, or the public static
artifact:

```sh
python3 skills/marco-agent-api/scripts/marco_client.py context --repo-root .
python3 skills/marco-agent-api/scripts/marco_client.py public-summary
```

## CI

GitHub Actions runs on push to `main`:

- Python install and tests;
- CLI smoke commands;
- Svelte frontend build.

Node A auto-deploy exists but waits for SSH secrets. See
[GitHub Actions CI and Node A deploy](deployment/github-actions.md).

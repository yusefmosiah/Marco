---
name: marco-agent-api
description: Use when an agent needs to inspect or consume Marco macro/backtest artifacts, query the Marco agent CLI or HTTP API, summarize model metrics, compare FX/rate baselines, fetch the public static artifact at choir-ip.com/marco, or start a local read-only Marco artifact API. This skill is for agent-facing data access, not for changing models or running undocumented finance analysis.
---

# Marco Agent API

## Start Here

Use the highest-fidelity available surface:

1. If inside the Marco repo, prefer the CLI:
   `PYTHONPATH=src python3 -m emf_macro.cli agent-context --root . --compact`
2. If a local API is running, call:
   `GET http://127.0.0.1:8765/v1/agent-context`
3. If neither exists, use the public static artifact:
   `https://choir-ip.com/marco/artifacts/fred-fx-rate-lab-summary.json`

Always preserve these constraints in summaries:

- Current public artifacts are `latest_revised_snapshot`, not ALFRED/vintage-safe evidence.
- Random-walk/no-change baselines are first-class comparison points.
- The API is read-only over committed artifacts.
- Do not imply live trading suitability or finance-professional validation.

## Common Tasks

List runs:

```sh
PYTHONPATH=src python3 -m emf_macro.cli list-runs --root . --compact
```

Get the active agent packet:

```sh
PYTHONPATH=src python3 -m emf_macro.cli agent-context --root . --run-id latest --compact
```

Get metrics for one pair/horizon:

```sh
PYTHONPATH=src python3 -m emf_macro.cli metrics --root . --run-id latest --pair USD_CAD --horizon 6 --compact
```

Start the local API:

```sh
PYTHONPATH=src python3 -m emf_macro.cli serve-agent-api \
  --root . \
  --host 127.0.0.1 \
  --port 8765 \
  --public-base-url https://choir-ip.com/marco
```

Query with the bundled helper script:

```sh
python skills/marco-agent-api/scripts/marco_client.py context --repo-root .
python skills/marco-agent-api/scripts/marco_client.py metrics --repo-root . --pair USD_CAD --horizon 6
python skills/marco-agent-api/scripts/marco_client.py public-summary
```

## Decision Rules

- Use CLI when working from a checked-out repo and no persistent service is needed.
- Use HTTP API when another process, browser, or agent needs repeated structured reads.
- Use the static public artifact only for share/read-only checks, because it exposes summary data but not the full dynamic API.
- Start no long-running API server unless the user asked for a service or a deploy task; if started for smoke testing, stop it before finishing.
- For Node A deployment questions, read `docs/deployment/github-actions.md` and `docs/deployment/node-a-static-preview.md`.

## Output Guidance

When answering from Marco artifacts, include:

- run id;
- snapshot/vintage policy;
- pair/horizon/model filters used;
- whether the baseline or a model won;
- the exact metric field being compared, usually RMSE.

Do not overstate small RMSE deltas. For example, if ridge beats random walk on
`USD_CAD` at `6M`, say it is a slight improvement in this latest-revised
snapshot, not a proven forecasting edge.

## References

Read `references/endpoints.md` when you need exact endpoint shapes, response
fields, or Caddy/API deployment notes.

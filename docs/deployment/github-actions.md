# GitHub Actions CI And Node A Deploy

Date: 2026-05-31

Status: CI enabled; Node A deploy workflow manages the live agent system when
secrets are present

## CI

Workflow:

```text
.github/workflows/ci.yml
```

Triggers:

```text
push to main
pull_request
workflow_dispatch
```

Jobs:

- Python tests: installs `.[dev]`, runs `pytest -q`, and smokes agent CLI
  commands.
- Web build: runs `npm ci` and `npm run build` under `apps/web`, then uploads
  the built `dist` as a workflow artifact.

## Node A Live Deploy

Workflow:

```text
.github/workflows/deploy-node-a.yml
```

Triggers:

```text
workflow_dispatch
push to main when web, API, data, runtime, or deploy files change
```

This workflow calls:

```text
tools/deploy_node_a_live.sh
```

It deploys:

- Svelte workbench assets to `/var/www/marco/current`
- repo/runtime files to `/opt/marco`
- Python CLI in `/opt/marco/.venv`
- Go API binary at `/usr/local/bin/marco-agentd`
- systemd service `marco-agentd.service`
- Caddy routes for `/marco/` and `/marco-api/`

Public routes:

```text
https://choir-ip.com/marco/
https://choir-ip.com/marco-api/health
```

## Required Secrets

The deploy workflow intentionally does nothing until these repository secrets
exist:

```text
NODE_A_HOST
NODE_A_USER
NODE_A_SSH_PRIVATE_KEY
```

Expected values:

```text
NODE_A_HOST=51.81.93.94
NODE_A_USER=root
NODE_A_SSH_PRIVATE_KEY=<private deploy key allowed by node-a>
```

Do not commit the key. Add it as a GitHub repo secret.

Using GitHub CLI:

```sh
gh secret set NODE_A_HOST --body '51.81.93.94'
gh secret set NODE_A_USER --body 'root'
gh secret set NODE_A_SSH_PRIVATE_KEY < ~/.ssh/id_ed25519_ovh
```

Only run the last command if you are comfortable letting this GitHub repo use
that SSH key for Node A deploys. A narrower dedicated deploy key is better.

## Runtime Notes

The UI does not provide local browser-side chat answers. Prompt submission calls
the live `marco-agentd` API through `/marco-api`.

The service uses:

```text
ZOT_HOME=/var/lib/marco/zot
MARCO_AGENT_MODEL=accounts/fireworks/models/deepseek-v4-flash
MARCO_AGENT_REASONING=medium
EnvironmentFile=-/var/lib/go-choir/gateway-provider.env
```

Agents can still use artifact URLs directly for evidence:

```text
https://choir-ip.com/marco/artifacts/fred-fx-rate-lab-summary.json
https://choir-ip.com/marco/artifacts/global-macro-panel-summary.json
```

or call the live agent API:

```sh
curl https://choir-ip.com/marco-api/health
curl -X POST https://choir-ip.com/marco-api/v1/chat \
  -H 'content-type: application/json' \
  -d '{"prompt":"Summarize Marco status."}'
```

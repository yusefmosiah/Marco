# GitHub Actions CI And Node A Deploy

Date: 2026-05-31

Status: CI enabled; Node A deploy workflow added but waits for secrets

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

## Node A Static Deploy

Workflow:

```text
.github/workflows/deploy-node-a.yml
```

Triggers:

```text
workflow_dispatch
push to main when apps/web, artifacts, deploy script, or deploy workflow changes
```

This workflow calls:

```text
tools/deploy_node_a_static.sh
```

It deploys the static Svelte preview to:

```text
https://choir-ip.com/marco/
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

## What Is Not Deployed Yet

The current Node A preview is still static. The new Marco agent API and CLI are
in the repo, but the dynamic HTTP API is not yet running as a Node A systemd
service.

To expose the dynamic API publicly, we still need:

1. a durable Python runtime or packaged service on Node A;
2. a systemd service for `emf-macro serve-agent-api`;
3. a Caddy route such as `/marco/api/*` to proxy to the local service;
4. an auth decision before adding mutating endpoints.

For now, agents can use:

```text
https://choir-ip.com/marco/artifacts/fred-fx-rate-lab-summary.json
https://choir-ip.com/marco/artifacts/global-macro-panel-summary.json
```

or clone the repo and use:

```sh
emf-macro agent-context --root .
emf-macro serve-agent-api --root . --host 127.0.0.1 --port 8765
```

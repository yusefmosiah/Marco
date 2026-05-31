# Marco Agent Workbench Web

Svelte/Vite frontend for the Marco hackathon demo. The app is a three-panel
live agent workbench:

- left: chat threads and worker-agent status
- center: open chat session with agent routing
- right: rendered report summaries and committed artifact links

Prompts are sent to the deployed Marco agent API. The committed artifact JSON is
used for the right-side evidence/report panel, not as a chat fallback.

The app reads:

```text
apps/web/public/artifacts/fred-fx-rate-lab-summary.json
apps/web/public/artifacts/global-macro-panel-summary.json
apps/web/public/artifacts/macro-news-summary.json
```

## Run

```sh
npm install
npm run dev -- --port 5177
```

Open:

```text
http://127.0.0.1:5177/
```

To run locally against a local `marco-agentd`:

```sh
VITE_MARCO_AGENT_API=http://127.0.0.1:8080 npm run dev -- --port 5177
```

The Node A deployment builds with:

```sh
VITE_MARCO_AGENT_API=/marco-api npm run build
```

## Build

```sh
npm run build
```

The app intentionally uses Svelte with plain CSS and committed JSON evidence
artifacts instead of a heavy charting stack. The data contract is JSON/CSV-first
so finance and data engineering users can inspect the source artifacts directly.

## Agent API Contract

When `VITE_MARCO_AGENT_API` is set, prompts use:

```text
POST /v1/chat
POST /v1/agents/economic-modeling-agent/prompt
POST /v1/agents/news-agent/prompt
POST /v1/agents/analyst-agent/prompt
```

See `../../docs/agents/chat-and-agent-interface-strategy.md` for the current
agent/chat diagram and `../../docs/agents/api-and-cli.md` for the API/CLI
contract.

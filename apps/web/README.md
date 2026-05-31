# Marco FX/Rate Lab Web

Svelte/Vite static frontend for the committed FRED FX/rate lab artifacts.

The app reads:

```text
apps/web/public/artifacts/fred-fx-rate-lab-summary.json
```

That file is copied from:

```text
artifacts/fred-fx-rate-lab/20260531-161930-fx-rate-diff/summary.json
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

## Build

```sh
npm run build
```

The app intentionally uses Svelte with plain SVG/CSS/table rendering instead of
a heavy charting stack. The data contract is JSON/CSV-first so finance and data
engineering users can work from the artifacts directly.

## Next Interface

The next Svelte pass is a Marco workbench rather than a static dashboard:

```text
left: chat threads, specialist runs, queued requests
center: conversation stream backed by POST /v1/chat
right: rendered markdown handoffs and raw artifact links
```

See `../../docs/agents/chat-and-agent-interface-strategy.md` for the current
agent/chat diagram and UI contract.

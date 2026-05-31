#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing required tool: $1" >&2
    return 1
  fi
}

need uv
need node
need npm
need go

cd "$ROOT"

uv sync --extra dev

cd "$ROOT/apps/web"
npm ci

cd "$ROOT/apps/analyst-cli"
npm ci

echo "Marco setup complete."
echo "Python CLI: .venv/bin/emf-macro list-runs --root ."
echo "Web build:  cd apps/web && npm run build"
echo "Analyst CLI: cd apps/analyst-cli && node ./bin/analyst-rag.js retrieve macro"
echo "Agent runtime: go run ./cmd/marco-agentd --root . --host 127.0.0.1 --port 8787"
echo "Zot install if needed: go install github.com/patriceckhart/zot/cmd/zot@latest"

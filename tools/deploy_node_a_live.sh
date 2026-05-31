#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SSH_ALIAS="${SSH_ALIAS:-node-a}"
REMOTE_APP_ROOT="${REMOTE_APP_ROOT:-/opt/marco}"
REMOTE_WEB_ROOT="${REMOTE_WEB_ROOT:-/var/www/marco/current}"
REMOTE_CADDY_CONFIG="${REMOTE_CADDY_CONFIG:-/var/lib/caddy/marco_caddy_config}"
CADDY_BIN="${CADDY_BIN:-/nix/store/nyijib6swbd9a6644g7ccaxbd51nq4ib-caddy-2.11.2/bin/caddy}"
MARCO_AGENT_API="${MARCO_AGENT_API:-/marco-api}"
MARCO_AGENT_PORT="${MARCO_AGENT_PORT:-8787}"

cd "$ROOT/apps/web"
VITE_MARCO_AGENT_API="$MARCO_AGENT_API" npm run build

ssh "$SSH_ALIAS" "install -d -m 0755 '$REMOTE_APP_ROOT' '$REMOTE_WEB_ROOT' /var/lib/marco"
rsync -az --delete \
  --exclude '.git/' \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude '.pytest_cache/' \
  --exclude 'apps/web/node_modules/' \
  --exclude 'apps/web/dist/' \
  "$ROOT/" "$SSH_ALIAS:$REMOTE_APP_ROOT/"
rsync -az --delete "$ROOT/apps/web/dist/" "$SSH_ALIAS:$REMOTE_WEB_ROOT/"

ssh "$SSH_ALIAS" "REMOTE_APP_ROOT='$REMOTE_APP_ROOT' REMOTE_WEB_ROOT='$REMOTE_WEB_ROOT' REMOTE_CADDY_CONFIG='$REMOTE_CADDY_CONFIG' CADDY_BIN='$CADDY_BIN' MARCO_AGENT_PORT='$MARCO_AGENT_PORT' bash -s" <<'SCRIPT'
set -euo pipefail

cd "$REMOTE_APP_ROOT"

PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python3 || true)"
fi
if [ -z "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(find /nix/store -maxdepth 4 -path '*/bin/python3' 2>/dev/null | sort | head -1)"
fi
if [ -z "$PYTHON_BIN" ]; then
  echo "python3 is required on Node A" >&2
  exit 127
fi
GCC_LIB_DIR="$(dirname "$(find /nix/store -path '*/lib/libstdc++.so.6' 2>/dev/null | sort | head -1)")"
if [ -z "$GCC_LIB_DIR" ]; then
  echo "libstdc++.so.6 is required on Node A" >&2
  exit 127
fi

"$PYTHON_BIN" -m venv .venv
.venv/bin/python -m ensurepip --upgrade >/dev/null
.venv/bin/python -m pip install --upgrade pip >/dev/null
.venv/bin/python -m pip install -e . >/dev/null

go build -o /usr/local/bin/marco-agentd ./cmd/marco-agentd

cat > /run/systemd/system/marco-agentd.service <<UNIT
[Unit]
Description=Marco live multiagent API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$REMOTE_APP_ROOT
Environment=ZOT_HOME=/var/lib/marco/zot
Environment=MARCO_PYTHON_CLI=$REMOTE_APP_ROOT/.venv/bin/emf-macro
Environment=MARCO_ZOT_BIN=/usr/local/bin/zot
Environment=MARCO_AGENT_PROVIDER=fireworks
Environment=MARCO_AGENT_MODEL=accounts/fireworks/models/deepseek-v4-flash
Environment=MARCO_AGENT_REASONING=medium
Environment=LD_LIBRARY_PATH=$GCC_LIB_DIR
EnvironmentFile=-/var/lib/go-choir/gateway-provider.env
ExecStart=/usr/local/bin/marco-agentd --root $REMOTE_APP_ROOT --host 127.0.0.1 --port $MARCO_AGENT_PORT
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl start marco-agentd.service
systemctl restart marco-agentd.service

for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:$MARCO_AGENT_PORT/health" >/dev/null; then
    break
  fi
  sleep 1
done
curl -fsS "http://127.0.0.1:$MARCO_AGENT_PORT/health" >/dev/null

awk -v web_root="$REMOTE_WEB_ROOT" -v agent_port="$MARCO_AGENT_PORT" '
  /handle \/assets\/\*/ && !inserted {
    print "\thandle /marco {"
    print "\t\tredir /marco/ permanent"
    print "\t}"
    print "\thandle_path /marco-api/* {"
    print "\t\treverse_proxy 127.0.0.1:" agent_port " {"
    print "\t\t\ttransport http {"
    print "\t\t\t\tresponse_header_timeout 5m"
    print "\t\t\t\tread_timeout 5m"
    print "\t\t\t\twrite_timeout 5m"
    print "\t\t\t}"
    print "\t\t}"
    print "\t}"
    print "\thandle_path /marco/* {"
    print "\t\troot * " web_root
    print "\t\theader Cache-Control \"no-store\""
    print "\t\ttry_files {path} /index.html"
    print "\t\tfile_server"
    print "\t}"
    inserted=1
  }
  { print }
' /etc/caddy/caddy_config > "$REMOTE_CADDY_CONFIG"

"$CADDY_BIN" adapt --config "$REMOTE_CADDY_CONFIG" --adapter caddyfile >/tmp/marco-caddy-adapt.json
"$CADDY_BIN" reload --config "$REMOTE_CADDY_CONFIG" --adapter caddyfile --force
SCRIPT

curl -fsS https://choir-ip.com/marco-api/health >/dev/null
curl -fsS -I https://choir-ip.com/marco/ >/dev/null

echo "Marco live UI: https://choir-ip.com/marco/"
echo "Marco live API: https://choir-ip.com/marco-api/health"

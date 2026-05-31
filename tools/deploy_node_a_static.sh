#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SSH_ALIAS="${SSH_ALIAS:-node-a}"
REMOTE_ROOT="${REMOTE_ROOT:-/var/www/marco/current}"
REMOTE_CADDY_CONFIG="${REMOTE_CADDY_CONFIG:-/var/lib/caddy/marco_caddy_config}"
CADDY_BIN="${CADDY_BIN:-/nix/store/nyijib6swbd9a6644g7ccaxbd51nq4ib-caddy-2.11.2/bin/caddy}"

cd "$ROOT/apps/web"
npm run build

ssh "$SSH_ALIAS" "install -d -m 0755 '$REMOTE_ROOT'"
rsync -az --delete "$ROOT/apps/web/dist/" "$SSH_ALIAS:$REMOTE_ROOT/"
ssh "$SSH_ALIAS" "chown -R root:root '$REMOTE_ROOT'"

ssh "$SSH_ALIAS" "cat > /tmp/marco-caddy-update.sh <<'SCRIPT'
set -euo pipefail
awk '
  /handle \\/assets\\/\\*/ && !inserted {
    print \"\\thandle /marco {\"
    print \"\\t\\tredir /marco/ permanent\"
    print \"\\t}\"
    print \"\\thandle_path /marco/* {\"
    print \"\\t\\troot * $REMOTE_ROOT\"
    print \"\\t\\theader Cache-Control \\\"no-store\\\"\"
    print \"\\t\\ttry_files {path} /index.html\"
    print \"\\t\\tfile_server\"
    print \"\\t}\"
    inserted=1
  }
  { print }
' /etc/caddy/caddy_config > '$REMOTE_CADDY_CONFIG'
'$CADDY_BIN' adapt --config '$REMOTE_CADDY_CONFIG' --adapter caddyfile >/tmp/marco-caddy-adapt.json
'$CADDY_BIN' reload --config '$REMOTE_CADDY_CONFIG' --adapter caddyfile --force
SCRIPT
bash /tmp/marco-caddy-update.sh"

curl -fsS -I https://choir-ip.com/marco/ >/dev/null
curl -fsS -I https://choir-ip.com/marco/artifacts/fred-fx-rate-lab-summary.json >/dev/null

echo "Marco deployed: https://choir-ip.com/marco/"

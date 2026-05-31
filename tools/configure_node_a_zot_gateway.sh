#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-node-a}"
SANDBOX_ID="${MARCO_ZOT_SANDBOX_ID:-marco-zot}"
MODEL="${MARCO_AGENT_MODEL:-accounts/fireworks/models/deepseek-v4-flash}"
REASONING="${MARCO_AGENT_REASONING:-medium}"
ZOT_HOME_REMOTE="${MARCO_ZOT_HOME_REMOTE:-/var/lib/marco/zot}"
GATEWAY_URL="${MARCO_GATEWAY_URL:-http://127.0.0.1:8084}"
GATEWAY_PROVIDER_ENV="${MARCO_GATEWAY_PROVIDER_ENV:-/var/lib/go-choir/gateway-provider.env}"

ssh "$HOST" \
  "SANDBOX_ID='${SANDBOX_ID}' MODEL='${MODEL}' REASONING='${REASONING}' ZOT_HOME_REMOTE='${ZOT_HOME_REMOTE}' GATEWAY_URL='${GATEWAY_URL}' GATEWAY_PROVIDER_ENV='${GATEWAY_PROVIDER_ENV}' bash -s" <<'REMOTE'
set -euo pipefail

ZOT_BIN="${ZOT_BIN:-$(command -v zot 2>/dev/null || true)}"
if [ -z "$ZOT_BIN" ] && [ -x /usr/local/bin/zot ]; then
  ZOT_BIN=/usr/local/bin/zot
fi
if [ -z "$ZOT_BIN" ]; then
  echo "zot is not installed on this host" >&2
  exit 1
fi

if [ ! -f "$GATEWAY_PROVIDER_ENV" ]; then
  echo "gateway provider env not found: $GATEWAY_PROVIDER_ENV" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$GATEWAY_PROVIDER_ENV"
set +a

if [ -z "${FIREWORKS_API_KEY:-}" ]; then
  echo "FIREWORKS_API_KEY is missing from $GATEWAY_PROVIDER_ENV" >&2
  exit 1
fi

install -d -m 700 "$ZOT_HOME_REMOTE"

BASE_URL="${FIREWORKS_BASE_URL:-https://api.fireworks.ai/inference}"
jq -n --arg model "$MODEL" --arg reasoning "$REASONING" \
  '{provider:"fireworks", model:$model, reasoning:$reasoning, theme:""}' \
  > "${ZOT_HOME_REMOTE}/config.json.tmp"
mv "${ZOT_HOME_REMOTE}/config.json.tmp" "${ZOT_HOME_REMOTE}/config.json"
chmod 644 "${ZOT_HOME_REMOTE}/config.json"

jq -n --arg model "$MODEL" --arg base_url "$BASE_URL" \
  '{providers:{fireworks:{models:[{id:$model,name:"Choir Gateway Fireworks DeepSeek V4 Flash",reasoning:true,contextWindow:1000000,maxTokens:384000,priceInput:0.14,priceOutput:0.28,priceCacheRead:0.03,baseUrl:$base_url,api:"anthropic-messages",input:["text"]}]}}}' \
  > "${ZOT_HOME_REMOTE}/models.json.tmp"
mv "${ZOT_HOME_REMOTE}/models.json.tmp" "${ZOT_HOME_REMOTE}/models.json"
chmod 644 "${ZOT_HOME_REMOTE}/models.json"

jq -n --arg token "$FIREWORKS_API_KEY" \
  '{additional_api_key_creds:{fireworks:{api_key:$token}}}' \
  > "${ZOT_HOME_REMOTE}/auth.json.tmp"
mv "${ZOT_HOME_REMOTE}/auth.json.tmp" "${ZOT_HOME_REMOTE}/auth.json"
chmod 600 "${ZOT_HOME_REMOTE}/auth.json"

echo "Configured Zot at ${ZOT_HOME_REMOTE}"
echo "provider=fireworks"
echo "model=${MODEL}"
echo "reasoning=${REASONING}"
echo "base_url=${BASE_URL}"

ZOT_HOME="$ZOT_HOME_REMOTE" "$ZOT_BIN" --list-models | grep -F "$MODEL" | head -n 1
ZOT_HOME="$ZOT_HOME_REMOTE" "$ZOT_BIN" --provider fireworks --model "$MODEL" --base-url "$BASE_URL" --reasoning "$REASONING" --no-tools --no-session --no-skill --no-ext --max-steps 3 -p 'Reply exactly: marco-node-a-zot-ok'
REMOTE

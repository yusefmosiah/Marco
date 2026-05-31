# Node A Static Preview Deployment

Date: 2026-05-31

Status: live preview on Node A

Public URL:

```text
https://choir-ip.com/marco/
```

## What Is Running

The current Marco Svelte/Vite frontend is deployed as static files on Node A:

```text
/var/www/marco/current
```

Caddy serves the app under the existing `choir-ip.com` host with:

```text
/marco/ -> /var/www/marco/current
```

The deployed app reads the committed shareable artifact:

```text
/marco/artifacts/fred-fx-rate-lab-summary.json
```

## Verification

Verified from outside the host:

```sh
curl -I https://choir-ip.com/marco/
curl -I https://choir-ip.com/marco/assets/index-2a7030bd.js
curl -I https://choir-ip.com/marco/assets/index-d21007fa.css
curl https://choir-ip.com/marco/artifacts/fred-fx-rate-lab-summary.json \
  | jq '{run_id, pair_count: (.pairs | length), metric_rows: (.metrics | length), best_rows: (.best_by_rmse | length), headline: .headline}'
```

Observed artifact summary:

```json
{
  "run_id": "20260531-161930-fx-rate-diff",
  "pair_count": 5,
  "metric_rows": 90,
  "best_rows": 15,
  "headline": {
    "features_rows": 6745,
    "model_result": "Random-walk/no-change baselines won almost everywhere on RMSE; ridge only slightly improved USD_CAD at 6M in this snapshot run.",
    "panel_columns": 23,
    "panel_rows": 1349,
    "prediction_rows": 17394,
    "status": "passed"
  }
}
```

## Redeploy

From the Marco repo:

```sh
tools/deploy_node_a_static.sh
```

The script:

1. Builds `apps/web`.
2. Syncs `apps/web/dist/` to `node-a:/var/www/marco/current/`.
3. Reloads Caddy with a `/marco/` route.
4. Checks the public page and artifact endpoints.

## Caveat

This is a runtime Caddy reload based on Node A's generated Caddy config:

```text
/etc/caddy/caddy_config -> /etc/static/caddy/caddy_config
runtime copy: /var/lib/caddy/marco_caddy_config
```

It is suitable for the hackathon preview, but a Caddy restart or NixOS rebuild
may revert the route unless the same route is added to the Node A Nix config in
`go-choir`.

Port `9090` was also tested and served correctly on localhost, but external
traffic to `51.81.93.94:9090` timed out. The working public route uses standard
HTTPS on `choir-ip.com`.

## Next Persistent Step

Make the route durable by adding an equivalent `handle /marco` and
`handle_path /marco/*` block to `go-choir`'s Node A Nix configuration, or switch
to a dedicated subdomain such as:

```text
marco.choir-ip.com
```

That subdomain still needs DNS/TLS wiring.

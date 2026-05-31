---
schema_version: marco.agent_handoff.v1
agent_id: economic_modeling_agent
run_id: economic_modeling_agent-20260531-220316
generated_at: 2026-05-31T22:03:16Z
status: succeeded
input_refs:
  - data/fred-fx-rate-lab/source_manifest.json
output_refs:
  - data/agents/runs/economic_modeling_agent/economic_modeling_agent-20260531-220316/output.md
  - data/backtests/macro-forecast-lab/summary.json
  - data/backtests/macro-forecast-lab/metrics.json
  - data/backtests/macro-forecast-lab/predictions.jsonl
evidence_refs:
  - data/backtests/macro-forecast-lab
next_run_requests: []
---

# Economic Modeling Agent Handoff

## Current Answer

Marco has a latest-revised FRED-MD macro forecast lab for a `6M` horizon. It compares `linear_top5, no_change, rolling_mean_12, var` on interest-rate, inflation, and industrial-production growth-proxy targets.

## Evidence

- Vintage policy: `latest_revised_snapshot`
- Lookahead status: `not_real_time_vintage_safe`
- Artifact directory: `data/backtests/macro-forecast-lab`
- Targets: `growth_proxy_yoy, inflation_yoy, interest_rate`

Metric sample:
- `growth_proxy_yoy`; `linear_top5`; n=232; mae=3.343; rmse=5.582; r_squared=-0.5371; directional_accuracy=0.5172
- `growth_proxy_yoy`; `no_change`; n=236; mae=2.895; rmse=4.824; r_squared=-0.01817; directional_accuracy=0
- `growth_proxy_yoy`; `rolling_mean_12`; n=236; mae=3.806; rmse=6.105; r_squared=-0.6308; directional_accuracy=0.4195
- `growth_proxy_yoy`; `var`; n=236; mae=2.903; rmse=4.666; r_squared=0.04723; directional_accuracy=0.5805
- `inflation_yoy`; `linear_top5`; n=232; mae=1.569; rmse=2.178; r_squared=-0.3688; directional_accuracy=0.6293
- `inflation_yoy`; `no_change`; n=236; mae=1.094; rmse=1.534; r_squared=0.3187; directional_accuracy=0
- `inflation_yoy`; `rolling_mean_12`; n=236; mae=1.413; rmse=1.926; r_squared=-0.07463; directional_accuracy=0.5381
- `inflation_yoy`; `var`; n=236; mae=1.137; rmse=1.634; r_squared=0.2261; directional_accuracy=0.4746
- `interest_rate`; `linear_top5`; n=232; mae=0.4732; rmse=0.7125; r_squared=0.867; directional_accuracy=0.6068
- `interest_rate`; `no_change`; n=236; mae=0.4457; rmse=0.7959; r_squared=0.8338; directional_accuracy=0
- `interest_rate`; `rolling_mean_12`; n=236; mae=0.8388; rmse=1.315; r_squared=0.5466; directional_accuracy=0.3048
- `interest_rate`; `var`; n=236; mae=0.7538; rmse=1.006; r_squared=0.7347; directional_accuracy=0.6333

Latest forecast sample:
- `growth_proxy_yoy` `linear_top5`: 2025-06 -> 2026-02, prediction=0.2845, actual=1.224
- `growth_proxy_yoy` `no_change`: 2025-08 -> 2026-03, prediction=1.182, actual=0.7389
- `growth_proxy_yoy` `rolling_mean_12`: 2025-08 -> 2026-03, prediction=0.235, actual=0.7389
- `growth_proxy_yoy` `var`: 2025-08 -> 2026-03, prediction=1.726, actual=0.7389
- `inflation_yoy` `linear_top5`: 2025-06 -> 2026-02, prediction=2.479, actual=2.405
- `inflation_yoy` `no_change`: 2025-08 -> 2026-03, prediction=2.896, actual=3.233
- `inflation_yoy` `rolling_mean_12`: 2025-08 -> 2026-03, prediction=2.618, actual=3.233
- `inflation_yoy` `var`: 2025-08 -> 2026-03, prediction=3.048, actual=3.233
- `interest_rate` `linear_top5`: 2025-06 -> 2026-02, prediction=4.345, actual=3.64
- `interest_rate` `no_change`: 2025-08 -> 2026-03, prediction=4.33, actual=3.64
- `interest_rate` `rolling_mean_12`: 2025-08 -> 2026-03, prediction=4.477, actual=3.64
- `interest_rate` `var`: 2025-08 -> 2026-03, prediction=4.037, actual=3.64

## Changes Since Previous Run

- Integrated macro forecast artifacts into the Marco multiagent handoff surface.

## Caveats

- Uses latest-revised FRED-MD data, not real-time ALFRED vintages.
- growth_proxy_yoy is industrial-production YoY, not true quarterly GDP.
- Forecasts must be interpreted against baseline metrics.

## Open Questions

- Which targets should move from latest-revised FRED-MD snapshots to real-time vintage-safe evaluation first?
- Which external central-bank and global macro sources should be joined before testing richer rate/FX hypotheses?

## Suggested Next Runs

- Re-run with real-time ALFRED vintages for policy-rate and inflation targets.
- Join ECB, World Bank, and Fed communications features to test whether text/event features improve baselines.

# Global Macro Panel Checkpoint

Date: 2026-05-31

Status: local CI passed; GitHub Actions pending after push

## What Changed

Marco now has a configured source-haul layer and a normalized global macro
panel summary that can be consumed by humans, the static frontend, the CLI, and
agents.

The first haul is:

```text
global_macro_starter_20260531
```

It is defined in:

```text
configs/source_hauls.json
```

## Current Data Haul

World Bank Indicators:

| Indicator | Feature | Countries | Years | Observations |
| --- | --- | ---: | --- | ---: |
| `NY.GDP.MKTP.CD` | `gdp_current_usd` | 8 | 2000-2024 | 200 |
| `FP.CPI.TOTL.ZG` | `inflation_cpi_annual_pct` | 8 | 2000-2024 | 200 |
| `BN.CAB.XOKA.CD` | `current_account_usd` | 8 | 2000-2024 | 200 |
| `SP.POP.TOTL` | `population_total` | 8 | 2000-2024 | 200 |

ECB SDMX:

| Flow | Series | Window | Observations | Join Status |
| --- | --- | --- | ---: | --- |
| `EXR` | `M.USD.EUR.SP00.A` | 2024-01 to 2024-03 | 3 | retained as source observations |

## Panel Artifact

The generated annual panel has:

| Item | Value |
| --- | ---: |
| Countries | 8 |
| Years | 25 |
| Country-year rows | 200 |
| Features | 4 |
| World Bank observations | 800 |
| ECB observations | 3 |

Committed summary:

```text
artifacts/global-macro-panel/global_macro_starter_20260531/summary.json
apps/web/public/artifacts/global-macro-panel-summary.json
```

Ignored generated panel:

```text
data/derived/global_macro_panel/panel_annual.csv
data/derived/global_macro_panel/panel_annual.jsonl
data/derived/global_macro_panel/summary.json
```

## Commands

```sh
emf-macro source-hauls --root .
emf-macro run-source-haul global_macro_starter_20260531 --root .
emf-macro build-global-panel --root . --haul-id global_macro_starter_20260531
emf-macro global-panel-summary --root . --haul-id global_macro_starter_20260531
```

## Evidence

Targeted local tests passed:

```text
pytest -q tests/test_global_panel.py tests/test_agent_api.py tests/test_world_bank.py tests/test_ecb.py
10 passed
```

Full local CI passed:

```text
make ci
34 passed
vite build completed
```

GitHub Actions evidence should be checked after push.

## Limits

- This is latest-revised snapshot data, not vintage-safe data.
- ECB observations are not joined into the annual panel yet.
- The panel is not yet a backtest input contract for global FX/rate models.
- Missing values and cross-frequency joins still need explicit policy before
  model training.

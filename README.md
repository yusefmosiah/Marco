# Marco

Macro research and backtesting lab.

This repo is currently focused on macro data ingestion and backtesting.

The active priority is:

```text
pull FRED/FRED-MD data
-> normalize into model-ready macro panels
-> engineer FX/rate features
-> run honest backtests against hard baselines
```

The earlier MikeOSS/table-extraction work is deferred. It remains useful
context for a later document-processing lane, but it is not the current build
priority.

Current artifact:

- [Setup](docs/setup.md)
- [Current focus](docs/strategy/current-focus.md)
- [Coherent platform plan](docs/strategy/coherent-platform-plan.md)
- [Global macro data expansion](docs/strategy/global-macro-data-expansion.md)
- [ECB SDMX source adapter](docs/sources/ecb-sdmx.md)
- [World Bank Indicators source adapter](docs/sources/world-bank-indicators.md)
- [Fed FOMC communications source adapter](docs/sources/fed-fomc-communications.md)
- [Macro news source ledger](docs/strategy/macro-news-source-ledger.md)
- [Dataset, hypothesis, and parallel backtesting foundation](docs/strategy/datasets-hypotheses-parallel-backtesting.md)
- [Agent API and CLI](docs/agents/api-and-cli.md)
- [Repo-local Marco agent API skill](skills/marco-agent-api/SKILL.md)
- [FRED-MD Macro Lab foundation mission](docs/missions/fred-md-macro-lab-foundation.md)
- [Experiment ledger continuation mission](docs/missions/marco-experiment-ledger-continuation.md)
- [FRED FX/rate lab checkpoint](docs/runs/20260531-fred-fx-rate-lab-checkpoint.md)
- [ECB SDMX smoke checkpoint](docs/runs/20260531-ecb-sdmx-smoke-checkpoint.md)
- [World Bank Indicators haul checkpoint](docs/runs/20260531-world-bank-indicators-haul.md)
- [Fed FOMC communications haul checkpoint](docs/runs/20260531-fed-fomc-communications-haul.md)
- [Macro news source ledger checkpoint](docs/runs/20260531-macro-news-source-ledger-checkpoint.md)
- [Global macro panel continuation mission](docs/missions/global-macro-panel-continuation.md)
- [Global macro panel checkpoint](docs/runs/20260531-global-macro-panel-checkpoint.md)
- [FinRobot/MikeOSS platform evaluation](docs/strategy/finrobot-mikeoss-platform-evaluation.md)
- [Node A static preview deployment](docs/deployment/node-a-static-preview.md)
- [GitHub Actions CI and Node A deploy](docs/deployment/github-actions.md)
- [Shareable FRED FX/rate artifacts](artifacts/fred-fx-rate-lab/20260531-161930-fx-rate-diff/)
- [Shareable Fed FOMC communications summary](artifacts/fed-fomc-communications/)
- [Shareable macro news summary](artifacts/macro-news/)
- [Shareable global macro panel summary](artifacts/global-macro-panel/global_macro_starter_20260531/)
- [Repo-root data bundles](data/)
- [Svelte visualization app](apps/web/)
- [Historical MikeOSS proposal](docs/proposals/mission-proposal.md)
- [Mobile-friendly PDF](output/pdf/emf-mission-proposal.pdf)

The custom frontend, MikeOSS integration, EM financial-statement extraction, and
deployment are intentionally out of scope until the FRED/backtesting foundation
is stronger.

## Quickstart

Install everything needed for local tests, CLI, API, and frontend work:

```sh
tools/bootstrap.sh
make ci
```

See [Setup](docs/setup.md) for required tools and manual installation.

## Data Haul

Marco currently has six concrete data surfaces.

The repo-root shareable data bundles live under:

```text
data/fred-fx-rate-lab/
data/world-bank-indicators/
data/ecb-sdmx/
data/global-macro-panel/
data/fed-fomc-communications/
data/macro-news/
data/backtests/
```

The ignored `data/raw/`, `data/derived/`, and `backtests/runs/` paths are still
working caches, but the current local contents have been promoted into the
shareable bundles above.

### Committed Shareable Artifacts

The repo commits compact FRED FX/rate lab artifacts under:

```text
artifacts/fred-fx-rate-lab/20260531-161930-fx-rate-diff/
```

That checkpoint contains:

| Item | Value |
| --- | ---: |
| Run ID | `20260531-161930-fx-rate-diff` |
| FX pairs | `EUR_USD`, `GBP_USD`, `USD_CAD`, `USD_JPY`, `USD_MXN` |
| Horizons | 1M, 3M, 6M |
| Models | `random_walk`, `no_change`, `rolling_mean_36m`, `carry_diff`, `real_rate_diff`, `ridge` |
| Monthly panel rows | 1,349 |
| Monthly panel columns | 23 |
| Feature rows | 6,745 |
| Prediction rows | 17,394 |
| Metric rows | 90 |
| Best-by-RMSE rows | 15 |

Files:

```text
summary.json
metrics.json
validation.json
model_metrics.csv
best_by_rmse.csv
report.md
```

### Generated Local FRED Data

Running `emf-macro run-fx-rate-lab` creates ignored local source and derived
data under:

```text
data/raw/fred_fx_rates/
data/derived/fred_fx_rates/
backtests/runs/
```

The local derived FRED feature panel currently includes:

```text
data/derived/fred_fx_rates/panel_monthly.csv
data/derived/fred_fx_rates/panel_monthly.parquet
data/derived/fred_fx_rates/features_monthly.csv
data/derived/fred_fx_rates/features_monthly.parquet
data/derived/fred_fx_rates/macro_facts.jsonl
data/derived/fred_fx_rates/feature_manifest.jsonl
data/derived/fred_fx_rates/source_manifest.json
data/derived/fred_fx_rates/series_catalog.jsonl
```

These are latest-revised FRED/FRED-MD snapshots, not ALFRED vintage-safe data.

### Live Source Adapter Hauls

Generated adapter hauls are ignored under `data/`.

ECB SDMX:

| Source | Series | Window | Observations |
| --- | --- | --- | ---: |
| ECB `EXR` | `M.USD.EUR.SP00.A` | 2024-01 to 2024-03 | 3 |

World Bank Indicators:

| Indicator | Countries | Years | Observations |
| --- | --- | --- | ---: |
| `NY.GDP.MKTP.CD` | USA, IND, BRA, MEX, ZAF, IDN, TUR, CHN | 2000-2024 | 200 |
| `FP.CPI.TOTL.ZG` | USA, IND, BRA, MEX, ZAF, IDN, TUR, CHN | 2000-2024 | 200 |
| `BN.CAB.XOKA.CD` | USA, IND, BRA, MEX, ZAF, IDN, TUR, CHN | 2000-2024 | 200 |
| `SP.POP.TOTL` | USA, IND, BRA, MEX, ZAF, IDN, TUR, CHN | 2000-2024 | 200 |

Total current World Bank haul: 800 normalized annual observations.

Fed FOMC communications:

| Source | Rows | Minutes | Statements | Window |
| --- | ---: | ---: | ---: | --- |
| `vtasca/fed-statement-scraping` `communications.csv` | 464 | 241 | 223 | 2000-02-02 to 2026-05-20 |

The Fed corpus is text-event data, not a numeric macro time series. It is
committed as a shareable repo-root data bundle under:

```text
data/fed-fomc-communications/communications.csv
data/fed-fomc-communications/observations.jsonl
data/fed-fomc-communications/dataset_record.json
data/fed-fomc-communications/dataset_mapping.json
data/fed-fomc-communications/source_manifest.json
data/fed-fomc-communications/summary.json
```

The hash-addressed raw cache and generated derived cache still live under
ignored `data/raw/` and `data/derived/`.

The compact committed summary lives at:

```text
artifacts/fed-fomc-communications/summary.json
```

Macro news source ledger:

| Source | Provider | Observations |
| --- | --- | ---: |
| `bank_of_england_news` | Bank of England | 50 |
| `bank_of_england_publications` | Bank of England | 50 |
| `bank_of_england_speeches` | Bank of England | 50 |
| `bank_of_japan_statistics_en` | Bank of Japan | 60 |
| `bank_of_japan_whats_new_en` | Bank of Japan | 53 |
| `bea_news_releases` | U.S. Bureau of Economic Analysis | 45 |
| `bis_central_bank_speeches` | Bank for International Settlements | 25 |
| `bis_press_releases` | Bank for International Settlements | 25 |
| `ecb_press` | European Central Bank | 15 |
| `federal_reserve_banking_reg_policy` | Federal Reserve Board | 15 |
| `federal_reserve_monetary_policy` | Federal Reserve Board | 15 |
| `federal_reserve_press_all` | Federal Reserve Board | 20 |
| `federal_reserve_speeches` | Federal Reserve Board | 15 |
| `rbi_notifications` | Reserve Bank of India | 10 |
| `rbi_press_releases` | Reserve Bank of India | 10 |
| `rbi_speeches` | Reserve Bank of India | 10 |
| `sec_press_releases` | U.S. Securities and Exchange Commission | 25 |

Total current macro news haul: 493 normalized official-feed items from 17
feeds. Configured intervals range from 5 to 30 minutes; there is no persistent
scheduler yet, so `news-fetch` runs the haul on demand.

The news ledger is event/publication data, not numeric macro time series. It is
committed as a shareable repo-root data bundle under:

```text
data/macro-news/source_registry.json
data/macro-news/source_manifest.json
data/macro-news/fetches.jsonl
data/macro-news/news_items.jsonl
data/macro-news/dataset_record.json
data/macro-news/summary.json
```

The compact committed summary lives at:

```text
artifacts/macro-news/summary.json
apps/web/public/artifacts/macro-news-summary.json
```

The source catalog currently tracks 16 official/source-linked candidates. Active
fetch adapters exist for `fred`, `ecb_sdmx`, `world_bank_indicators`,
`fed_fomc_communications`, and the separate `macro_news` source ledger.

### Normalized Global Macro Panel

The first configured source haul is:

```text
configs/source_hauls.json
global_macro_starter_20260531
```

It currently builds a latest-revised annual panel with:

| Item | Value |
| --- | ---: |
| Countries | 8 |
| Years | 2000-2024 |
| Country-year rows | 200 |
| World Bank observations | 800 |
| ECB source observations | 3 |
| Features | 4 |

Countries: `BRA`, `CHN`, `IDN`, `IND`, `MEX`, `TUR`, `USA`, `ZAF`.

Features:

```text
current_account_usd
gdp_current_usd
inflation_cpi_annual_pct
population_total
```

The committed compact summary lives at:

```text
artifacts/global-macro-panel/global_macro_starter_20260531/summary.json
apps/web/public/artifacts/global-macro-panel-summary.json
```

Generated local panel files are ignored:

```text
data/derived/global_macro_panel/panel_annual.csv
data/derived/global_macro_panel/panel_annual.jsonl
data/derived/global_macro_panel/summary.json
```

List and run configured source hauls:

```sh
emf-macro source-hauls --root .
emf-macro run-source-haul global_macro_starter_20260531 --root .
```

Build and inspect the normalized panel:

```sh
emf-macro build-global-panel --root . --haul-id global_macro_starter_20260531
emf-macro global-panel-summary --root . --haul-id global_macro_starter_20260531
```

## Macro Lab

Run the FRED FX/rate differential lab:

```sh
.venv/bin/emf-macro run-fx-rate-lab --root . --evaluation-start 2006-01 --horizons 1,3,6
```

Generated source data and backtest runs live under ignored `data/` and
`backtests/runs/` paths. Commit checkpoint summaries under `docs/runs/`, not
large generated data files.

Export compact GitHub-shareable artifacts from a generated run:

```sh
python3 tools/export_share_artifacts.py \
  backtests/runs/20260531-161930-fx-rate-diff \
  data/derived/fred_fx_rates \
  artifacts/fred-fx-rate-lab/20260531-161930-fx-rate-diff
```

## Visualization

The visualization app is a small Svelte/Vite static frontend over committed
artifact JSON:

```sh
cd apps/web
npm ci
npm run dev -- --port 5177
```

Open `http://127.0.0.1:5177/`.

Build:

```sh
npm run build
```

Why Svelte: it keeps the frontend source small and reviewable while still
producing a standard static web app. Finance/data-engineering users can ignore
the frontend and consume the committed JSON/CSV artifacts directly.

## Agent API And CLI

Agents can use the read-only artifact surface instead of scraping the UI:

```sh
emf-macro list-runs --root .
emf-macro metrics --root . --run-id latest --pair USD_CAD --horizon 6
emf-macro agent-context --root . --run-id latest
emf-macro serve-agent-api --root . --host 127.0.0.1 --port 8765
```

See [Agent API and CLI](docs/agents/api-and-cli.md).

Dataset and experiment-planning foundation:

```sh
emf-macro dataset-add path/to/data.csv --root . --name "My Dataset"
emf-macro suggest-hypotheses --root . --run-id latest
emf-macro plan-experiments --root . --pair USD_CAD --horizon 6
emf-macro sources list --root . --priority p0
emf-macro sources inspect rbi_dbie --root .
emf-macro sources inspect fed_fomc_communications --root .
emf-macro source-hauls --root .
emf-macro global-panel-summary --root .
```

Fetch the first non-FRED official central-bank source:

```sh
emf-macro source-fetch ecb_sdmx \
  --root . \
  --flow EXR \
  --series M.USD.EUR.SP00.A \
  --start-period 2024-01 \
  --end-period 2024-03

emf-macro source-observations ecb_sdmx --root . --series M.USD.EUR.SP00.A --limit 5
```

Fetch World Bank annual macro controls:

```sh
emf-macro source-fetch world_bank_indicators \
  --root . \
  --country 'USA;IND;BRA;MEX;ZAF;IDN;TUR;CHN' \
  --indicator NY.GDP.MKTP.CD \
  --start-year 2000 \
  --end-year 2024

emf-macro source-observations world_bank_indicators --root . --indicator NY.GDP.MKTP.CD --limit 5
```

Fetch Fed FOMC statements and minutes text:

```sh
emf-macro source-fetch fed_fomc_communications --root .
emf-macro source-observations fed_fomc_communications --root . --communication-type Minute --limit 2
```

Execute a bounded experiment plan into an ignored local run ledger:

```sh
emf-macro plan-experiments \
  --root . \
  --pair USD_CAD \
  --horizon 6 \
  --model-id random_walk \
  --model-id no_change \
  --model-id ridge \
  --output tmp/usd-cad-6m-plan.json

emf-macro run-experiment-plan \
  --root . \
  --plan tmp/usd-cad-6m-plan.json \
  --features data/derived/fred_fx_rates/features_monthly.parquet \
  --evaluation-start 2006-01 \
  --max-parallelism 1
```

Runner outputs live under ignored `backtests/runs/ledger-*/`.

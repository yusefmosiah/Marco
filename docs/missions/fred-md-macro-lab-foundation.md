# FRED-MD FX/Rate Macro Lab Mission

Date: 2026-05-31

Repo: `/Users/wiz/emf`

Mission name: `fred-md-fx-rate-macro-lab`

Status: foundation checkpoint executed

## Scope Boundary

This is the active mission lane.

MikeOSS, tabular document extraction, financial-statement parsing, custom UI,
and deployment are explicitly out of scope for the current implementation pass.
They are deferred until the FRED/backtesting substrate is stronger.

Current priority:

```text
pull FRED data
-> build model-ready panels
-> engineer FX/rate features
-> run backtests
-> document evidence and limitations
```

## Goal String

```text
/goal In /Users/wiz/emf, build the FRED-MD FX/Rate Macro Lab foundation:
ingest and hash public FRED-MD/FRED source data, create a normalized
macro panel for rates, inflation, yields, and FX, engineer nominal and real
interest-rate differentials, implement random-walk/no-change and carry-style
baselines, run walk-forward backtests for FX returns and rate-policy targets
with explicit latest-revised-snapshot vs real-time-vintage labeling, and
checkpoint with tests, metrics, model artifacts, reports, and the next path
toward vintage-safe India/EM expansion.
```

## Mission Thesis

Build the first Marco macro modeling foundation around a concrete economic
hypothesis:

```text
interest-rate differentials and real-rate differentials contain information
about FX returns, FX pressure, and future rate-policy moves.
```

The mission is not "predict FX with AI." FX is hard, noisy, and hostile to
overfit models. The mission is to build a backtesting substrate that can test
whether rate differentials, inflation differentials, yield spreads, and simple
macro controls beat naive baselines under walk-forward evaluation.

FRED-MD remains useful as the macro-panel reference shape, but this mission
should not stop at reproducing FRED-MD. It should build a model-ready panel for
rates and FX, run baseline models, and produce an honest report.

The long-term Marco macro product is:

```text
official macro sources
-> normalized vintage-aware macro panel
-> economic feature engineering
-> reproducible backtests
-> model outputs with evidence, baselines, and error metrics
```

## Cognitive Transforms

Current uncertainty or obstacle:

The easy but weak route is to ingest a broad macro dataset and produce generic
forecast charts. That would be too diffuse. The stronger route is to choose one
economic mechanism, build the substrate needed to test it, and make every model
fight a baseline.

Selected transforms:

1. Depth extraction - "interest-rate differential predicts FX" is not a magic
   formula. The deeper object is a testable carry/UIP/real-rate pressure model
   with regimes, crashes, and baseline comparisons.
2. Failure-mode inversion - assume every FX model is overfit until it beats a
   random walk or no-change baseline out of sample.
3. Homotopy preservation - start with US/FRED-accessible series and major FX
   pairs, but preserve the same artifact topology needed for India/EM: source
   manifests, normalized facts, panel features, model configs, predictions,
   metrics, and reports.
4. Audience translation - for hackathon presentation, say "we built a
   source-linked macro backtesting lab for testing rate-differential FX/rate
   models," not "we built an AI that predicts currencies."
5. Anti-Goodhart transform - the first valuable outcome may be "carry baseline
   does not beat random walk on this setup." Honest negative results validate
   the platform more than a cherry-picked chart.

Route-changing insights:

- Model target selection must drive data ingestion. Pull rates, inflation,
  yields, FX, and risk controls before broad generic indicators.
- FRED-MD `current.csv` is useful for macro context, but FX/rate modeling may
  require direct FRED series pulls beyond FRED-MD.
- The first report should compare naive, carry, real-rate, and simple
  regularized models on the same walk-forward split.
- Real-time/vintage-safe backtesting is a realism upgrade. The first checkpoint
  may use revised snapshots, but it must label that limitation.

Changed plan:

- Implementation: build a rates/FX panel and feature engine before broad
  FRED-MD factor models.
- Verifier/evidence: prove train/test separation, target horizon alignment,
  exchange-rate direction convention, rate differential signs, and baseline
  metrics.
- Scope: first checkpoint targets a small set of FRED-available currencies or
  proxies, plus a clean path to India/EM data.
- Stopping condition: a checkpoint is valid only when model outputs include
  metrics against random-walk/no-change baselines and a report explicitly states
  whether results are vintage-safe.

Next high-information action:

Identify FRED-accessible series for policy/short rates, inflation, yields, and
FX rates; inspect availability and date ranges; then lock a minimal target
basket before coding model complexity.

## Real Artifact

A working repo foundation that can:

1. Download and cache FRED-MD plus selected FRED rate, inflation, yield, and FX
   series.
2. Preserve source manifests and file hashes.
3. Normalize observations into macro facts.
4. Build a monthly model-ready panel.
5. Engineer nominal-rate differential, inflation differential,
   real-rate differential, yield-spread, and FX-return targets.
6. Run walk-forward backtests for FX-return and rate-policy targets.
7. Compare every nontrivial model against random-walk/no-change and simple
   historical baselines.
8. Emit predictions, metrics, feature manifests, and report artifacts.

## Value Criterion

Maximize honest out-of-sample economic signal discovery while minimizing
lookahead bias, target leakage, revised-data overclaims, sign-convention
mistakes, cherry-picked pairs, missing source lineage, and model complexity that
does not beat baselines.

## Hard Invariants

- Preserve raw downloaded source files by content hash.
- Do not commit downloaded raw datasets unless intentionally small and licensed
  for repo storage.
- Do not commit secrets. Initial FRED public CSV/API work should not require
  secrets unless an optional FRED API key is later used.
- Every normalized series/fact must retain source dataset, source series ID,
  frequency, period, source snapshot, and unit metadata when available.
- Every FX series must record direction convention, for example `USD_PER_EUR` or
  `INR_PER_USD`.
- Every target must record forecast horizon and target construction.
- Do not call a backtest "no-lookahead" unless the run uses only data available
  as of each simulated date.
- Treat FRED-MD `current.csv` and ordinary FRED latest pulls as
  latest-revised-snapshot data unless ALFRED/vintage sources are used.
- Every model must compare against a random-walk/no-change baseline.
- No EM expansion until the FRED/rates/FX panel and baseline backtest report
  work end to end.

## Initial Model Targets

Primary target:

```text
h-month log FX return
```

Example:

```text
fx_return_h = log(spot_fx_{t+h} / spot_fx_t)
```

The sign convention must be explicit. If `spot_fx` is local currency per USD,
positive return means local currency depreciation against USD. If `spot_fx` is
USD per foreign currency, positive return means foreign currency appreciation.

Secondary targets:

- next policy-rate change direction;
- next short-rate change;
- FX pressure score;
- carry return proxy if spot and rate data permit.

## Initial Feature Families

Core:

- local short/policy rate;
- US short/policy rate;
- nominal-rate differential;
- local CPI inflation;
- US CPI inflation;
- inflation differential;
- real-rate differential;
- local and US 10-year yield;
- yield differential;
- yield-curve slope;
- lagged FX returns;
- realized FX volatility.

Optional risk controls:

- equity drawdown / VIX proxy;
- commodity price proxy;
- credit spread proxy;
- current account / external balance proxy;
- FX reserves for EM expansion.

## Initial Currency/Pairs Basket

Start with FRED-accessible, liquid pairs and rate series where possible:

- EUR/USD or USD/EUR;
- JPY/USD or USD/JPY;
- GBP/USD or USD/GBP;
- CAD/USD or USD/CAD;
- MXN/USD or USD/MXN if data coverage is good.

India/EM expansion comes after the foundation:

- USD/INR;
- USD/BRL;
- USD/MXN;
- USD/ZAR;
- USD/IDR;
- USD/TRY.

## Initial Output Format

```text
data/
  raw/                         # ignored; source downloads by hash
  derived/
    fred_fx_rates/
      source_manifest.json
      series_catalog.jsonl
      macro_facts.jsonl
      panel_monthly.parquet
      panel_monthly.csv
      feature_manifest.jsonl
      validation_report.json
models/
  baselines/
    random_walk/
    no_change/
    rolling_mean/
    carry_diff/
  linear/
    ridge/
backtests/
  configs/
  runs/
    YYYYMMDD-HHMMSS-fx-rate-diff/
      config.json
      metrics.json
      predictions.jsonl
      feature_manifest.json
      report.md
```

The central durable objects are:

- `series_catalog.jsonl`: source series metadata.
- `macro_facts.jsonl`: long-format observations.
- `panel_monthly.parquet`: model-ready matrix.
- `feature_manifest.jsonl`: feature and target derivations.
- `backtests/runs/...`: model run evidence.

## Fact Shape

```json
{
  "geo_id": "US",
  "dataset": "FRED",
  "source_series_id": "FEDFUNDS",
  "indicator": "rates.policy.fed_funds",
  "period": "2025-04",
  "frequency": "monthly",
  "value_raw": 4.33,
  "unit": "percent",
  "source_snapshot": "sha256:...",
  "vintage_policy": "latest_revised_snapshot",
  "evidence_id": "fred:FEDFUNDS:2025-04"
}
```

## Feature Shape

```json
{
  "feature_id": "feature:MX:2025-04:real_rate_diff_us",
  "country": "MX",
  "period": "2025-04",
  "name": "real_rate_diff_vs_us",
  "value": 2.15,
  "inputs": [
    "rates.short.mx",
    "rates.short.us",
    "inflation.cpi_yoy.mx",
    "inflation.cpi_yoy.us"
  ],
  "formula": "(mx_rate - us_rate) - (mx_cpi_yoy - us_cpi_yoy)",
  "vintage_policy": "latest_revised_snapshot"
}
```

## Backtest Shape

```json
{
  "run_id": "20260531-fx-rate-diff-v0",
  "model_id": "carry_diff_baseline_v0",
  "target": "fx_return_3m",
  "pair": "USD_MXN",
  "forecast_horizon": "3M",
  "train_window": "expanding",
  "evaluation_start": "2005-01",
  "evaluation_end": "2024-12",
  "vintage_policy": "latest_revised_snapshot",
  "lookahead_status": "not_real_time_vintage_safe",
  "baselines": ["random_walk", "rolling_mean"],
  "metrics": {
    "mae": 0.0,
    "rmse": 0.0,
    "directional_accuracy": 0.0,
    "hit_rate_vs_random_walk": 0.0
  }
}
```

## Receding-Horizon Plan

### Pass 1: Target Basket And Source Discovery

- Identify FRED series IDs for selected FX pairs.
- Identify US and foreign short-rate/policy-rate proxies.
- Identify CPI/inflation proxies.
- Identify 10-year yield or yield-spread proxies where available.
- Record date ranges and missingness before locking model targets.

### Pass 2: Data Foundation

- Create package skeleton.
- Add FRED/FRED-MD downloader with source manifest and hash storage.
- Parse selected series into normalized macro facts.
- Emit `series_catalog.jsonl` and `macro_facts.jsonl`.
- Add tests for date parsing, frequency normalization, source hashing, and
  direction convention metadata.

### Pass 3: Feature And Target Engine

- Build monthly panel.
- Align mixed-frequency or missing series with explicit policy.
- Compute FX returns for 1M, 3M, and 6M horizons.
- Compute nominal and real interest-rate differentials.
- Compute inflation differentials, yield differentials, lagged returns, and
  volatility features.
- Add tests that target horizons do not leak future values into features.

### Pass 4: Baseline Backtesting Harness

- Add walk-forward runner.
- Add random-walk/no-change, rolling-mean, and carry-differential baselines.
- Require explicit pair, target, horizon, train window, and evaluation window.
- Emit predictions, metrics, and Markdown report.
- Mark latest-pull/revised-snapshot backtests clearly as not real-time-vintage
  safe.

### Pass 5: First Regularized Model

- Add ridge or lasso regression.
- Compare against baselines on identical splits.
- Report whether the model improves MAE/RMSE/directional accuracy.
- Preserve negative results honestly.

### Pass 6: Realism Upgrade Plan

- Identify smallest path to vintage-safe runs:
  - ALFRED vintages for selected FRED series;
  - release-date calendars;
  - archived FRED-MD/FRED snapshots if available;
  - source-specific release timestamps for EM data.
- Produce India/EM data source map for rates, inflation, FX, reserves, current
  account, debt, and risk controls.

## Agent/Module Roles

- Source Loader: downloads public files and writes source manifests.
- Catalog Builder: normalizes series metadata, units, frequencies, and FX
  direction conventions.
- Feature Engineer: owns rate differentials, real-rate differentials, and target
  construction.
- Panel Builder: produces model-ready matrices.
- Backtest Runner: runs walk-forward evaluations.
- Model Runner: owns baselines and first regularized models.
- Verifier: checks leakage policy, target alignment, metrics, and report
  consistency.

These should be ordinary modules first. Agents come later for source discovery,
EM document ingestion, and model-selection loops.

## Evaluation

Data tests:

- Source files exist and hashes are recorded.
- Dates parse into monthly periods.
- Series IDs align with catalog.
- FX direction convention is recorded for every FX series.
- Panel columns match catalog and feature manifest.

Feature tests:

- Nominal-rate differential sign is deterministic.
- Real-rate differential formula is deterministic.
- FX return target sign is deterministic.
- Forecast target at `t+h` is never used in features at `t`.
- Missing-value behavior is explicit and reported.

Backtest tests:

- Train windows never include rows after the forecast origin.
- Prediction timestamps and target timestamps are separated by horizon.
- Baselines run before advanced models.
- Reports state whether the run is real-time-vintage safe.

Model tests:

- Random-walk/no-change baseline is always present.
- Carry/real-rate models beat or fail baselines honestly.
- Metrics are written even when performance is poor.
- Feature coefficients or contribution summaries are reported when available.

## Anti-Goodhart Constraints

- Do not optimize for a pretty chart.
- Do not hide baseline failures.
- Do not cherry-pick one currency pair without showing the basket.
- Do not claim "predicts FX" unless out-of-sample metrics beat baseline.
- Do not claim trading profitability without transaction costs, carry mechanics,
  and risk controls.
- Do not use revised/latest snapshots to claim real-time nowcast or trading
  performance.
- Do not add complex agent orchestration before the panel/backtest artifact
  works.

## Rollback And Safety

- Keep generated data under ignored `data/` and `backtests/runs/` unless a
  small fixture is intentionally committed.
- Keep source code and docs separate from generated data artifacts.
- Every run report must include enough config to reproduce the run.
- If a model or transform bug is found, preserve the failing config and output
  as evidence before replacing it.

## Stopping Condition For First Implementation Run

The first implementation mission can stop at a valid checkpoint when:

- Selected FRED/FRED-MD sources download and hash successfully.
- Series catalog and macro facts are emitted.
- Monthly rates/FX panel is built.
- Nominal and real rate differentials plus FX-return targets are generated.
- At least random-walk/no-change and carry-differential baselines run in
  walk-forward mode for at least one pair and horizon.
- A backtest report exists and clearly labels the vintage limitation.
- Tests or verification scripts prove parser, feature, target, and backtest
  invariants.

Do not require India-MD, Mike integration, UI, deployment, true vintage-safe
ALFRED runs, or advanced models in the first foundation mission.

## Run Checkpoint & Resumption State

```text
status: complete
last checkpoint: 2026-05-31 foundation run `20260531-161930-fx-rate-diff`
  completed with validation status `passed`
current artifact state: /Users/wiz/emf contains proposal artifacts and this
  FX/rate macro mission, plus a Python package and CLI for the first FRED
  FX/rate lab
what shipped: FRED/FRED-MD downloader, source hashing, normalized macro facts,
  monthly panel builder, feature engineering, baseline/ridge walk-forward
  backtests, tests, generated run artifacts, checkpoint report
what was proven: selected FRED/FRED-MD sources downloaded and hashed; panel and
  features built; five FX pairs evaluated; required baselines present; unit
  tests passed; generated validation report passed
unproven or partial claims: real-time vintage safety, trading profitability,
  transaction costs, robustness beyond selected pairs, India/EM data availability
belief-state changes: macro value is source-linked panels plus backtested
  economic models; first concrete wedge is interest-rate differential / FX-rate
  pressure, not broad generic macro dashboards; first run shows random-walk /
  no-change baselines remain hard to beat on RMSE
remaining error field: vintage-safe backtesting, FX direction conventions,
  target leakage, baseline integrity, overfit risk
highest-impact remaining uncertainty: whether a simple carry/real-rate model
  beats random-walk/no-change baselines under vintage-safe evaluation and richer
  risk controls
next executable probe: add ALFRED/vintage-aware pulls for selected series and
  re-run one pair/horizon with true as-of data cuts
suggested resume goal string: use the Goal String at top of document
evidence artifact refs: docs/runs/20260531-fred-fx-rate-lab-checkpoint.md;
  generated run dir backtests/runs/20260531-161930-fx-rate-diff;
  generated derived dir data/derived/fred_fx_rates
rollback refs: git history
```

## Sources

- FRED-MD and FRED-QD database page:
  https://www.stlouisfed.org/research/economists/mccracken/fred-databases
- FRED-MD paper/appendix:
  https://files.stlouisfed.org/files/htdocs/fred-databases/fredmd.pdf
- FRED-QD article:
  https://www.stlouisfed.org/publications/review/2021/01/14/fred-qd-a-quarterly-database-for-macroeconomic-research
- FRED API documentation:
  https://fred.stlouisfed.org/docs/api/fred/
- FRED series search:
  https://fred.stlouisfed.org/search
- KRED weak signal for FRED-MD-style country datasets:
  https://arxiv.org/abs/2509.16115

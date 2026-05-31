# FRED-MD Macro Lab Foundation Mission

Date: 2026-05-31

Repo: `/Users/wiz/emf`

Mission name: `fred-md-macro-lab-foundation`

Status: planned checkpoint, not executed

## Goal String

```text
/goal In /Users/wiz/emf, build the FRED-MD Macro Lab foundation as a durable
macro-modeling substrate: ingest and hash public FRED-MD source data, parse
series metadata and transformation codes, emit normalized macro facts plus a
model-ready monthly panel, implement baseline walk-forward backtests with clear
latest-revised-snapshot vs real-time-vintage labeling, and checkpoint with
tests, metrics, report artifacts, and the next path toward vintage-safe
backtesting and India-MD.
```

## Mission Thesis

Build the macro foundation of EMF around FRED-MD before expanding to India and
other emerging markets.

The goal is not to make a dashboard first. The goal is to create a reproducible
macro modeling substrate:

```text
FRED-MD / FRED-QD source data
-> normalized macro fact graph
-> model-ready monthly and quarterly panels
-> transformation engine
-> backtesting harness
-> baseline economic model runs
-> evidence and no-lookahead checks
```

FRED-MD is the right first substrate because it is already a curated monthly
macroeconomic database designed for research and factor modeling. FRED-QD is
the quarterly companion. These datasets give EMF a clean reference shape before
we build noisier India-MD / EM-MD panels from RBI, MoSPI, IMF, World Bank,
central banks, finance ministries, and other sources.

## Cognitive Transforms

Current uncertainty or obstacle:

It is tempting to treat the task as "download FRED-MD and run models." That
would produce charts quickly but would not create the durable foundation we need
for emerging-market macro work. The real object is a source-linked,
transformation-aware, vintage-aware modeling substrate.

Selected transforms:

1. Depth extraction - "normalized macro data" is not the value. The value is
   reproducible economic model runs on model-ready panels, with enough source
   lineage to trust or falsify each result.
2. Failure-mode inversion - assume every attractive backtest is fake until it
   proves no lookahead, no revised-data leakage, and no target-period leakage.
3. Homotopy preservation - build the FRED-MD foundation using the same artifact
   topology we will need for India-MD: source manifest, series catalog, facts,
   transformations, panels, model configs, run outputs, and reports.
4. Audience translation - the hackathon-visible claim should not be
   "macroeconomic AI." It should be "we can reproduce a standard macro panel,
   run transparent backtests, and then apply the same machinery to EM data."
5. Anti-Goodhart transform - baseline models are not a warm-up; they are the
   guardrail. Complex models only matter if they beat simple baselines under the
   same protocol.

Route-changing insights:

- The first shipped artifact should be a backtestable panel and run report, not
  an agent or UI.
- `current.csv` should be accepted for foundation plumbing but explicitly
  labeled as latest-revised-snapshot data.
- True vintage-safe backtesting is a separate realism axis and must become the
  next executable probe after the foundation works.
- The pipeline should store run configs and outputs as first-class artifacts so
  model failures are inspectable, not overwritten.

Changed plan:

- Implementation: build ingestion, transformation, panel, and backtest modules
  before adding agents, Mike, UI, or India-specific source complexity.
- Verifier/evidence: test source hashes, tcode parsing, transformation math,
  panel shape, walk-forward train/test separation, and report consistency.
- Scope: stop first foundation run after FRED-MD baseline backtests and report;
  defer FRED-QD, India-MD, UI, deployment, and advanced models unless the core
  loop is already proven.
- Stopping condition: a checkpoint is valid only when a user can inspect
  `series_catalog.jsonl`, `macro_facts.jsonl`, `panel_monthly.*`, and a
  baseline backtest report with explicit vintage limitations.

Next high-information action:

Download FRED-MD `current.csv`, inspect the exact header/tcode/date layout, and
write parser tests before implementing model code.

## Real Artifact

A working repo foundation that can:

1. Download and cache FRED-MD `current.csv` plus the appendix/metadata.
2. Parse series IDs, categories, transformation codes, dates, and raw values.
3. Emit a normalized macro fact graph.
4. Emit model-ready panel files.
5. Apply McCracken-Ng/FRED-MD transformations reproducibly.
6. Run first walk-forward backtests without lookahead against simple baselines.
7. Produce a run report showing data coverage, transformations, model outputs,
   errors, and known realism gaps.

## Value Criterion

Maximize reproducible macro-model usefulness while minimizing lookahead bias,
silent transformation errors, missing source lineage, fake precision, and model
performance claims that only work because revised/future data leaked into the
past.

This mission is successful only if the foundation makes later economic models
easier to run and harder to overclaim.

## Hard Invariants

- Preserve raw downloaded source files by content hash.
- Do not commit downloaded raw datasets unless intentionally small and licensed
  for repo storage.
- Do not commit secrets. FRED-MD public CSV work should not require secrets.
- Every normalized series/fact must retain source dataset, source series ID,
  frequency, period, vintage or source snapshot, transformation code, and unit
  metadata when available.
- Do not call a backtest "no-lookahead" unless the run uses only data available
  as of each simulated date.
- Treat FRED-MD `current.csv` as a latest/revised snapshot. It is fine for
  parser, transform, panel, and model-plumbing work. It is not sufficient for
  production-grade real-time vintage backtesting by itself.
- Baselines must be present before complex models.
- Model outputs must include uncertainty/residuals or at least explicit error
  metrics; no chart-only claims.
- No EM expansion until FRED-MD ingestion, transformation, and a baseline
  backtest report work end to end.

## Initial Output Format

```text
data/
  raw/                         # ignored; source downloads by hash
  derived/
    fred_md/
      source_manifest.json
      series_catalog.jsonl
      macro_facts.jsonl
      panel_monthly.parquet
      panel_monthly.csv
      transformations.jsonl
      validation_report.json
    fred_qd/
      ...
models/
  baselines/
    last_value/
    ar1/
  factor_model/
backtests/
  configs/
  runs/
    YYYYMMDD-HHMMSS-fred-md-baseline/
      config.json
      metrics.json
      predictions.jsonl
      feature_manifest.json
      report.md
```

The central durable objects are:

- `series_catalog.jsonl`: one row per source series with category, source ID,
  frequency, transformation code, units, and notes.
- `macro_facts.jsonl`: long-format facts, one row per series-period-snapshot.
- `panel_monthly.parquet`: wide matrix for modeling.
- `transformations.jsonl`: raw -> transformed derivation records.
- `backtests/runs/...`: model run evidence.

## Fact Shape

```json
{
  "geo_id": "US",
  "dataset": "FRED-MD",
  "source_series_id": "INDPRO",
  "indicator": "production.industrial.total",
  "period": "2025-04",
  "frequency": "monthly",
  "value_raw": 102.4,
  "value_transformed": 0.0031,
  "unit": "index",
  "transformation_code": 5,
  "source_snapshot": "sha256:...",
  "vintage_policy": "latest_revised_snapshot",
  "evidence_id": "fred-md:INDPRO:2025-04"
}
```

## Backtest Shape

```json
{
  "run_id": "20260531-fred-md-ar1-industrial-production",
  "model_id": "baseline_ar1_v0",
  "target": "INDPRO",
  "forecast_horizon": "1M",
  "train_window": "expanding",
  "evaluation_start": "1985-01",
  "evaluation_end": "2024-12",
  "vintage_policy": "latest_revised_snapshot",
  "lookahead_status": "not_real_time_vintage_safe",
  "baselines": ["last_value", "rolling_mean"],
  "metrics": {
    "mae": 0.0,
    "rmse": 0.0,
    "directional_accuracy": 0.0
  }
}
```

## Receding-Horizon Plan

### Pass 1: Data Foundation

- Create package skeleton.
- Add a FRED-MD downloader with source manifest and hash storage.
- Parse `current.csv` into raw metadata and observations.
- Parse transformation-code rows correctly.
- Emit `series_catalog.jsonl` and `macro_facts.jsonl`.
- Add tests for date parsing, tcode parsing, series count, and hash manifest.

### Pass 2: Transform And Panel Builder

- Implement FRED-MD transformation codes.
- Emit raw and transformed long-format facts.
- Build a wide monthly panel.
- Add missing-value handling policy.
- Validate that transformed panel has expected shape and no accidental date
  leakage from future periods.

### Pass 3: Baseline Backtesting Harness

- Add walk-forward backtest runner.
- Add last-value, rolling-mean, and AR(1) baselines.
- Require explicit target, horizon, train window, and evaluation window.
- Emit predictions, metrics, and a Markdown report.
- Mark `current.csv` backtests as latest-revised snapshot backtests, not true
  real-time vintage backtests.

### Pass 4: First Model Layer

- Add a simple factor model or PCA factor extractor.
- Forecast one or two targets:
  - industrial production growth
  - CPI inflation or unemployment
- Compare to baselines.
- Report whether the factor model actually improves out-of-sample metrics.

### Pass 5: Realism Upgrade Plan

- Identify the smallest route to real-time vintage backtesting:
  - archived FRED-MD vintages if available;
  - ALFRED release/vintage data for selected series;
  - source release calendars;
  - synthetic release-date policy only as clearly labeled approximation.
- Produce the India-MD source map:
  - RBI;
  - MoSPI;
  - Ministry of Finance;
  - IMF;
  - World Bank;
  - BIS;
  - market rates/FX sources.

## Agent/Module Roles

- Source Loader: downloads public files and writes source manifests.
- Catalog Builder: normalizes series metadata and transformation codes.
- Transformation Engine: applies raw -> transformed series rules.
- Panel Builder: produces model-ready matrices.
- Backtest Runner: runs walk-forward evaluations.
- Model Runner: owns baseline and first factor models.
- Verifier: checks shape, leakage policy, metrics, and report consistency.

These can be ordinary modules first. Agents come later if document ingestion or
model-selection loops become complex.

## Evaluation

Data tests:

- Source file exists and hash is recorded.
- Date columns parse into monthly periods.
- Series IDs and transformation codes align.
- Long facts count equals non-empty source observations after expected filtering.
- Panel columns match catalog.

Transformation tests:

- Each transformation code has a deterministic implementation.
- Log/difference transformations handle non-positive values explicitly.
- Missing-value behavior is explicit and reported.

Backtest tests:

- Train windows never include rows after the forecast origin.
- Prediction timestamps and target timestamps are separated by horizon.
- Baselines run before advanced models.
- Reports state whether the run is real-time-vintage safe.

Model tests:

- Model beats or fails baselines honestly.
- Metrics are written even when performance is poor.
- Top contributing factors/features are reported when available.

## Anti-Goodhart Constraints

- Do not optimize for a pretty chart.
- Do not hide baseline failures.
- Do not claim factor-model value unless it beats simple baselines under the
  same backtest protocol.
- Do not use revised FRED-MD snapshots to make claims about real-time trading or
  nowcasting performance.
- Do not introduce India/EM source complexity until the FRED-MD foundation is
  reproducible.

## Rollback And Safety

- Keep all generated data under ignored `data/` and `backtests/runs/` unless a
  small fixture is intentionally committed.
- Keep source code and docs separate from generated data artifacts.
- Every run report must include enough config to reproduce the run.
- If a model or transform bug is found, preserve the failing config and output
  as evidence before replacing it.

## Stopping Condition For First Implementation Run

The first implementation mission can stop at a valid checkpoint when:

- FRED-MD downloads and hashes successfully.
- Series catalog and macro facts are emitted.
- Transformed monthly panel is built.
- At least two baseline models run in walk-forward mode for one target.
- A backtest report exists and clearly labels the vintage limitation.
- Tests or verification scripts prove parser, transform, and backtest invariants.

Do not require India-MD, Mike integration, UI, deployment, or advanced models in
the first foundation mission.

## Suggested Resume Goal

```text
/goal In /Users/wiz/emf, build the FRED-MD Macro Lab foundation: implement
public FRED-MD ingestion with source hashing, parse the catalog and
transformation codes, emit normalized macro facts and a model-ready monthly
panel, implement baseline walk-forward backtests, and checkpoint with tests,
metrics, and a report that clearly labels the vintage/no-lookahead limitations.
```

## Run Checkpoint & Resumption State

```text
status: checkpoint_incomplete
last checkpoint: mission document prepared; no implementation run started
current artifact state: /Users/wiz/emf contains proposal artifacts and this
  FRED-MD macro foundation mission
what shipped: docs only
what was proven: FRED-MD/FRED-QD source path and mission shape researched
unproven or partial claims: exact CSV format, current row/column counts,
  transformation parsing, panel builder, and backtest harness
belief-state changes: macro value is model-ready panels and backtests, not data
  normalization alone
remaining error field: vintage-safe backtesting, transformation correctness,
  model baseline integrity
highest-impact remaining uncertainty: whether we can obtain enough historical
  vintages/release dates for credible no-lookahead claims beyond revised-snapshot
  plumbing
next executable probe: download current FRED-MD CSV, inspect format, and build
  source manifest + parser tests
suggested resume goal string: see Suggested Resume Goal
evidence artifact refs: this mission doc
rollback refs: git history once committed
```

## Sources

- FRED-MD and FRED-QD database page:
  https://www.stlouisfed.org/research/economists/mccracken/fred-databases
- FRED-MD paper/appendix:
  https://files.stlouisfed.org/files/htdocs/fred-databases/fredmd.pdf
- FRED-QD article:
  https://www.stlouisfed.org/publications/review/2021/01/14/fred-qd-a-quarterly-database-for-macroeconomic-research
- FRED-MD paper listing:
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2646151
- KRED weak signal for FRED-MD-style country datasets:
  https://arxiv.org/abs/2509.16115

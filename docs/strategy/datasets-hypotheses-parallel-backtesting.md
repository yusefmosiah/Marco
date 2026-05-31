# Dataset, Hypothesis, And Parallel Backtesting Foundation

Date: 2026-05-31

Status: initial foundation

## Direction

Marco should become an artifact-first macro modeling lab:

```text
datasets
-> normalized panels
-> hypotheses
-> experiment plans
-> parallel backtest jobs
-> model artifacts and reports
-> better hypotheses
```

The next product value is not just uploading files. It is letting users and
agents bring or fetch datasets, map them into a normalized time-series panel,
and then run many honest backtests across models, horizons, regimes, countries,
and feature sets.

## What Exists Now

This commit adds the first local foundations:

- dataset registry under ignored `data/registry/datasets.jsonl`;
- uploaded/fetched dataset storage under ignored `data/uploads/`;
- model ladder specs from hard baselines to planned sequence models;
- hypothesis suggestions based on current run artifacts and registered datasets;
- experiment-plan JSON that fans out dataset/pair/horizon/model jobs.
- official macro source catalog access;
- dataset mapping specs for date/frequency/value/vintage contracts;
- hypothesis specs with explicit baselines, metrics, horizons, split policy, and
  falsification rules.

The dynamic API exposes read-only planning surfaces:

```text
GET /v1/datasets
GET /v1/models
GET /v1/hypotheses
GET /v1/experiment-plan?pair=USD_CAD&horizon_months=6
```

The CLI adds local mutation for datasets:

```sh
emf-macro dataset-add sample.csv --root . --name "My Macro Dataset"
emf-macro dataset-fetch-url https://example.com/data.csv --root . --name "External Dataset"
emf-macro list-datasets --root .
emf-macro models
emf-macro suggest-hypotheses --root .
emf-macro plan-experiments --root . --pair USD_CAD --horizon 6
emf-macro sources list --root . --priority p0
```

## Why Local Mutation First

Public upload endpoints need authentication, quotas, file-size limits, content
inspection, storage retention, and provenance policy. Until those exist, dataset
mutation should stay local or behind a trusted operator path.

The read-only API can be safely exposed sooner because it only reports committed
or locally registered artifact metadata.

## Model Ladder

Use a staged ladder rather than jumping directly to complex models:

```text
tier 0: random_walk, no_change
tier 1: rolling_mean_36m, carry_diff, real_rate_diff
tier 2: ridge
tier 3: elastic_net
tier 4: gradient_boosted_trees
tier 5: temporal_foundation_model
```

Every experiment plan must keep random-walk/no-change baselines. Later model
families should earn their place by beating hard baselines under the same
walk-forward and vintage rules.

## Parallel Backtesting Contract

The experiment plan is designed to be embarrassingly parallel:

```text
dataset_id x pair x horizon x model_id -> independent backtest job
```

Each job should eventually emit:

- config;
- source dataset hashes;
- feature manifest;
- predictions;
- metrics;
- model artifact, when applicable;
- report fragment;
- failure reason, if the job fails.

The runner should aggregate jobs into a run bundle and only report a model
"win" after comparing against random-walk and no-change for the same dataset,
target, horizon, and split.

## Next Implementation Step

Build a job runner that consumes:

```text
marco.dataset_mapping.v1
marco.hypothesis_spec.v1
marco.experiment_plan.v1
```

and writes:

```text
backtests/runs/<run_id>/
  experiment_plan.json
  jobs/<job_id>/config.json
  jobs/<job_id>/predictions.jsonl
  jobs/<job_id>/metrics.json
  aggregate_metrics.json
  report.md
```

Then add panel-mapping for registered datasets:

```text
dataset columns
-> date/frequency/unit/country/indicator mapping
-> normalized panel
-> feature set
-> experiment plan
```

Only after that should the hosted app add user uploads.

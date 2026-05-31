# Marco Experiment Ledger Continuation Mission

Date: 2026-05-31

Repo: `/Users/wiz/emf`

Mission name: `marco-experiment-ledger-continuation`

Status: implementation checkpoint executed

## One-Line Goal String

```text
/goal In /Users/wiz/emf, continue Marco from the proven FRED/FX/rate foundation by building the experiment ledger and runner: consume marco.dataset_mapping.v1, marco.hypothesis_spec.v1, and marco.experiment_plan.v1; execute ready baseline and ridge jobs with atomic per-job artifacts; aggregate only when required baselines exist; prove deterministic reruns, partial-failure behavior, and serial/parallel equivalence in CI; preserve latest-revised vs vintage labeling; keep Node A as static preview; and checkpoint the next clean path toward ECB/IMF/World Bank/RBI global macro source ingestion without coupling the runner to hosted uploads, MikeOSS, FinRobot, Sourcecycled, or vmctl.
```

## Thesis

Marco’s next durable object is not a bigger model list or a broader data scrape.
It is the experiment ledger:

```text
source snapshot
-> dataset mapping
-> hypothesis spec
-> experiment plan
-> job artifacts
-> baseline-gated aggregate metrics
-> report and shareable summaries
```

The foundation now has FRED artifacts, model specs, source catalog access,
dataset mapping specs, hypothesis specs, experiment-plan generation, a read-only
agent API, a Svelte preview, and CI. The missing load-bearing piece is a runner
that turns plans into durable, comparable job evidence.

## Real Artifact

A local runner and artifact contract that can execute a small Marco experiment
from a fresh checkout and leave a durable run bundle:

```text
backtests/runs/<run_id>/
  experiment_plan.json
  run_manifest.json
  jobs/<job_id>/
    config.json
    status.json
    predictions.jsonl
    metrics.json
    failure.json              # only on failed jobs
  aggregate_metrics.json
  baseline_gates.json
  report.md
```

The first successful run should use the current committed FRED FX/rate panel
shape and execute a bounded plan such as:

```text
dataset: current_fred_fx_rate_panel
pairs: USD_CAD
horizons: 6
models: random_walk, no_change, ridge
```

## Current Belief State

- The repo is green on GitHub Actions as of commit `df90722`.
- The current source catalog and schema contracts are tested.
- The existing `run-fx-rate-lab` pipeline already knows how to produce metrics,
  predictions, and reports for the FRED FX/rate lab.
- The existing experiment plan is a contract, not an executor.
- The highest-impact uncertainty is how cleanly the existing backtest code can
  be reused by a per-job runner without duplicating pipeline logic.

## Value Criterion

Maximize reproducible learning per backtest while minimizing lookahead leakage,
baseline omission, partial-run ambiguity, duplicate artifact paths, and model
complexity that cannot be compared against hard baselines.

The system moves uphill when:

- every job has a deterministic ID and isolated artifact directory;
- rerunning the same plan does not create conflicting canonical results;
- a failed job is visible and does not poison successful jobs;
- aggregate metrics refuse to promote model claims without matching baselines;
- serial and parallel execution produce equivalent aggregate results;
- fresh checkout CI can prove the runner contract without live secrets;
- the next source adapter can feed the same ledger without changing its shape.

## Quality Gradient

Expected quality level: **solid**.

Solid means:

- no new parallel implementation of the whole FRED pipeline;
- concise runner code with clear artifact schemas;
- deterministic IDs and stable JSON output ordering;
- focused unit tests plus one CLI smoke path;
- docs updated with exact commands and artifact paths;
- generated large data remains ignored unless exported as compact shareable
  summaries.

Excellent is not required yet:

- no hosted mutable upload API;
- no vmctl execution backend;
- no custom model training platform;
- no polished UI for runner internals;
- no full SDMX adapter implementation inside this mission.

## Hard Invariants

- Do not commit secrets or raw bulk data.
- Preserve latest-revised-snapshot vs real-time-vintage labels.
- Do not call a run vintage-safe unless it uses vintage data.
- Every promoted model comparison must include `random_walk` and `no_change`
  for the same dataset, target, horizon, pair, and split.
- Every job writes either metrics and predictions or a failure artifact.
- Aggregation must not silently drop failed or missing required jobs.
- Public/hosted mutation remains deferred.
- Node A remains a static preview unless a separate deployment mission changes
  that boundary.
- `vmctl` is an optional later execution backend, not a requirement for this
  runner.

## Receding-Horizon Control

### Control Interval 1: Runner Contract

- Define artifact schemas for run manifest, job config, job status, job metrics,
  and baseline gates.
- Add tests for deterministic job/run paths.
- Add CLI shape, likely:

  ```sh
  emf-macro run-experiment-plan --root . --plan path/to/plan.json
  ```

### Control Interval 2: Serial Execution

- Execute only `ready` jobs.
- Start with current FRED panel runs for `random_walk`, `no_change`, and
  `ridge`.
- Reuse existing backtest/model logic where possible.
- Write atomic per-job artifacts.

### Control Interval 3: Aggregation And Gates

- Aggregate completed job metrics.
- Refuse "best model" claims where required baselines are missing.
- Emit `baseline_gates.json` and `aggregate_metrics.json`.
- Generate a short `report.md`.

### Control Interval 4: Failure And Idempotence

- Test partial failure without corrupting completed jobs.
- Test rerun idempotence.
- Test missing-baseline rejection.
- Test stable output order.

### Control Interval 5: Parallelism

- Add bounded local parallel execution only after serial behavior is stable.
- Prove serial/parallel aggregate equivalence.
- Keep `vmctl` as a documented future backend.

### Control Interval 6: Docs And Next Source Adapter

- Update CLI/API/strategy docs with the runner command and artifact layout.
- Add the next mission note for ECB SDMX smoke fetch after the runner lands.

## Dense Feedback And Evidence Ledger

Record evidence for:

- `pytest -q`;
- `make ci`;
- CLI plan generation;
- runner execution on a tiny bounded plan;
- artifact tree listing;
- deterministic rerun proof;
- partial failure test;
- baseline gate rejection test;
- serial/parallel equivalence test, if parallelism lands;
- GitHub Actions run ID after push.

## Acceptance Criteria

1. Runner consumes `marco.experiment_plan.v1`.
2. Runner records or validates associated `marco.dataset_mapping.v1` and
   `marco.hypothesis_spec.v1` references, even if the first run uses the
   built-in current FRED panel.
3. Ready jobs execute and write atomic artifacts.
4. Planned/non-executable jobs are skipped with explicit status.
5. Failed jobs write failure artifacts.
6. Aggregate metrics include only valid completed jobs and expose failures.
7. Baseline gates require `random_walk` and `no_change`.
8. Rerunning the same bounded plan is deterministic and does not create
   conflicting canonical artifacts.
9. Local CI passes.
10. GitHub Actions CI passes after push.
11. Docs explain the command, output contract, and residual limits.

## Anti-Goodhart Constraints

- Do not optimize for job count.
- Do not add model families before baseline-gated aggregation works.
- Do not claim parallel backtesting because a plan can be generated.
- Do not claim hosted platform progress from a local mutable registry.
- Do not bury negative results; a baseline win is useful evidence.
- Do not use latest-revised FRED data to imply live trading performance.

## Rollback Policy

- Keep all generated run artifacts under ignored `backtests/runs/`.
- Commit only source, tests, docs, compact exported summaries, and small fixture
  artifacts.
- If runner design duplicates too much of the current pipeline, stop and
  refactor around the existing backtest boundary instead of adding a second
  system.
- If live source/API work becomes tempting, defer it to the ECB/IMF adapter
  mission after runner proof.

## Later Integration Seams

| Future lane | Integration seam |
| --- | --- |
| ECB/IMF/World Bank/RBI data | source adapter emits mapped dataset records and panel inputs |
| Sourcecycled | source manifest import into dataset records |
| MikeOSS/FinRobot | extracted tabular facts become mapped datasets or graph facts |
| Hosted uploads | authenticated dataset registry plus mapping validation |
| Choir | agent orchestration over CLI/API surfaces |
| `vmctl` | optional worker backend for job shards after local runner proof |
| Frontend | reads aggregate run artifacts and reports |

## Run Checkpoint And Resumption State

```text
status: checkpoint_incomplete
last checkpoint: local implementation of runner and ledger contract before
  GitHub promotion
current artifact state: source catalog, dataset mapping specs, hypothesis specs,
  experiment plans, read-only API, skill, Svelte preview, CI, and a local
  experiment runner are present
what shipped: source runner module, run-experiment-plan CLI, per-job artifact
  writing, aggregate metrics, baseline gates, focused tests, and docs
what was proven: local make ci passed with runner tests covering completed
  artifacts, deterministic reruns, missing-baseline rejection, skipped jobs,
  partial failure artifacts, and serial/parallel aggregate equivalence; CLI
  help and bounded USD_CAD 6M plan generation smoke commands ran successfully;
  local generated FRED features executed USD_CAD 6M random_walk/no_change/ridge
  into ledger-77c68467739a7088 with 3 completed jobs, 0 failures, and passed
  baseline gates
unproven or partial claims: no hosted API mutation; no ECB/IMF/RBI source
  adapter; no ALFRED real-time vintage-safe runner path yet
belief-state changes: existing walk_forward_pair is a workable per-group
  execution boundary, so the runner can stay a ledger layer
remaining error field: fresh clones still need either generated FRED features or
  a committed compact fixture before run-experiment-plan can execute real
  USD_CAD jobs without first running run-fx-rate-lab
highest-impact remaining uncertainty: whether the next source adapter should
  start with ECB SDMX smoke fetch or ALFRED vintage-safe replacement for the
  current FRED pull path
next executable probe: add a small committed runner fixture or implement the
  first ECB SDMX smoke fetch behind the same dataset mapping contract
suggested resume goal string: /goal Run docs/missions/marco-experiment-ledger-continuation.md
  to build and verify the Marco experiment runner and artifact ledger
evidence artifact refs: tests/test_runner.py, local make ci run, CLI smoke
  output for run-experiment-plan plus USD_CAD 6M plan generation, local ignored
  run backtests/runs/ledger-77c68467739a7088
rollback refs: revert the runner/CLI/doc commit before any live deployment
```

# Marco Coherent Platform Plan

Date: 2026-05-31

Status: planning spine

## Thesis

Marco should stay coherent by treating every ambition as one of four layers:

```text
source/provenance
-> normalized macro panels
-> experiment ledger and backtests
-> agent/API/frontend consumption
```

The active product object is the experiment ledger: a durable record tying source
snapshots, mapping specs, hypothesis specs, jobs, metrics, artifacts, reports,
and deployment state together.

This keeps the current FRED/FRED-MD backtesting work compatible with later
Sourcecycled ingestion, MikeOSS/FinRobot table workflows, Choir agents, and
Node A worker VMs without collapsing all of them into one immediate mission.

## Layer Map

| Layer | Current Marco role | Later expansion | Current rule |
| --- | --- | --- | --- |
| Source/provenance | FRED/FRED-MD pulls, hashes, artifact summaries | Sourcecycled, EM central banks, filings, PDFs, event feeds | Add provenance fields now, do not build a general source platform yet |
| Normalization | Macro panels for FX/rates/inflation/yields | EM panels, company fundamentals, multi-country macro | Require explicit mapping specs before user uploads become model inputs |
| Experiments | Baselines, model registry, hypothesis suggestions, plans | Parallel model sweeps, richer ML, vintage-safe EM expansion | Build the runner/ledger before adding many models |
| Consumption | CLI, read-only API, repo-local skill, Svelte preview | Hosted uploads, agent workflows, custom frontend | Keep public mutation deferred until auth/storage/job isolation exist |
| Execution substrate | Local CLI and GitHub Actions CI | Node A service, `vmctl` worker VMs, Choir orchestration | CI is the verifier; VMs are a scale/isolation backend after the ledger exists |

The global source expansion lane is tracked in
[Global Macro Data Expansion](global-macro-data-expansion.md), with a
machine-readable catalog at `configs/macro_sources.json`.

## What Belongs Now

The next implementation work should strengthen the path from data to credible
backtest evidence:

1. Dataset mapping specs.
2. Hypothesis specs.
3. A durable experiment runner for `marco.experiment_plan.v1`.
4. Atomic per-job artifacts.
5. Aggregation with required baseline gates.
6. CI tests for determinism, partial failures, reruns, and artifact schemas.
7. Documentation that lets another agent or human rerun the lab from checkout.

This is the shortest path from "we have macro data" to "we can evaluate ideas
about rates and FX without fooling ourselves."

## What Stays Deferred

These are valuable, but they should not drive the immediate architecture:

- MikeOSS/FinRobot table extraction over financial statements.
- Full Sourcecycled standalone source-ingestion platform.
- Public hosted user uploads.
- Arbitrary custom agent workflows against mutable hosted state.
- Training custom models on user-provided time-series corpora.
- Dedicated Cloudflare subdomain wiring.
- VM-scale parallel execution.

Each deferred lane should integrate through explicit contracts instead of
private coupling.

## Sourcecycled Fit

Sourcecycled is the eventual source/provenance platform:

```text
sources -> fetches -> items -> manifests -> Marco dataset imports
```

Marco should prepare for it by storing optional source manifest references on
dataset records and by accepting future JSON/JSONL manifests. Marco should not
depend on Sourcecycled for FRED/FRED-MD v0 because FRED is already structured
and the current bottleneck is backtest credibility, not source discovery.

## MikeOSS And FinRobot Fit

MikeOSS and FinRobot belong to a later document/table agent lane:

```text
financial filings / PDFs / tables
-> extraction workflows
-> normalized company facts
-> Marco-compatible panels or graph facts
-> experiments and comparisons
```

They should be evaluated as extraction harnesses after the experiment ledger can
prove whether extracted data improves forecasts or analysis.

## CI Unroll

Every phase should land with a CI-visible acceptance gate:

| Phase | Deliverable | CI gate |
| --- | --- | --- |
| Foundation | Existing FRED lab, API, skill, web build | `pytest -q`, CLI smoke, Svelte build |
| Mapping | `DatasetMappingSpec` and schema validation | mapping unit tests and invalid-input tests |
| Hypotheses | `HypothesisSpec` with falsification fields | schema tests and plan generation tests |
| Runner | local experiment runner with atomic job artifacts | deterministic IDs, rerun idempotence, partial-failure tests |
| Aggregation | baseline-gated metrics and report bundles | missing-baseline rejection and report schema tests |
| Parallelism | bounded local parallel job execution | serial/parallel equivalence tests |
| Deployment | Node A static preview plus optional API/service | deploy workflow smoke and public endpoint verification |
| VM backend | optional `vmctl` job workers | documented manual/staging proof before relying on it |

The rule is simple: no new layer counts as real until a fresh checkout can prove
it through CI or a documented deployed smoke test.

## Node A And `vmctl`

Node A is already useful as the public preview host. The current live surface is
static:

```text
https://choir-ip.com/marco/
```

`go-choir` also has a `vmctl` service for worker VM ownership and lifecycle.
That can become useful when Marco jobs need isolation or more parallelism than a
single host process should provide. Treat it as a later backend with this shape:

```text
Marco experiment plan
-> job queue
-> local runner or GitHub CI for default execution
-> optional Node A runner
-> optional vmctl worker VM per shard/model family
-> artifact upload/merge
```

Important constraints:

- Do not require `vmctl` for local development or GitHub CI.
- Do not use worker VMs before the experiment artifact contract is stable.
- Prefer `worker-medium` for ordinary repo/build jobs and `worker-large` only
  for bounded heavier model sweeps.
- Use objective fingerprints and run IDs so duplicate worker leases do not
  create duplicate canonical artifacts.
- Keep generated data and run artifacts outside git unless explicitly exported
  as compact shareable summaries.

## Deployment Shape

Near term deployment remains:

```text
GitHub main
-> CI
-> static web build
-> Node A /marco preview
```

The dynamic agent API can run locally now. A hosted API should wait until it has
read-only production posture, auth decisions, logging, storage paths, and a
clear separation between public artifacts and private mutable state.

## Next Mission String

```text
/goal In /Users/wiz/emf, build the Marco experiment-ledger foundation: define
dataset mapping and hypothesis specs, implement a local runner for
marco.experiment_plan.v1 with atomic per-job artifacts and baseline-gated
aggregation, prove rerun determinism and partial-failure behavior in CI, keep
Node A as static preview only, and document the later Sourcecycled, MikeOSS,
FinRobot, Choir, and vmctl integration seams without coupling the current FRED
backtesting mission to them.
```

## Current Stopping Rule

Proceed only with work that improves one of:

- FRED/FRED-MD ingestion and snapshot labeling;
- normalized macro panels;
- dataset mapping specs;
- falsifiable hypothesis specs;
- experiment execution, artifacts, metrics, or reports;
- CI/deployed proof;
- agent/API/frontend consumption of proven artifacts.

Everything else is a named future integration seam.

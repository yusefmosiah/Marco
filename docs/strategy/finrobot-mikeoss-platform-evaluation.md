# FinRobot, MikeOSS, and the Marco Platform Path

Date: 2026-05-31

Status: strategy note for the next product turn

## Question

Should Marco become a fork of FinRobot or MikeOSS, or should Marco stay its own
macro/backtesting core and borrow platform patterns from both?

The product target is no longer just a data visualization website. The stronger
target is an interactive macro research agent:

```text
hosted public app
-> published macro datasets and workflows
-> agentic interaction over those artifacts
-> user uploads of time-series data
-> reusable custom workflows
-> model and backtest registry
-> eventual custom model training
```

That framing changes the architecture. The durable product object is not a
chatbot and not a dashboard. It is a system where datasets, transformations,
features, models, backtests, reports, and agent decisions are all inspectable
artifacts.

## Recommendation

Keep Marco as the core repo and product spine.

Do not fork MikeOSS into the Marco core right now. It is a strong reference for
project workspaces, document upload, tabular review, workflow templates, and
citation UX, but its legal-document architecture and AGPL-3.0 license make it a
poor default foundation for a finance/macro platform.

Do not hard-fork all of FinRobot right now either. FinRobot is the better fork
candidate because it is finance-native and Apache-2.0, but Marco already has the
cleaner macro data and backtesting substrate. Treat FinRobot as an Apache-licensed
source of patterns and possible modules: agent report generation, finance data
adapters, task logging, report rendering, and FastAPI web-app structure.

If we later must choose one codebase to fork for speed, fork FinRobot, not
MikeOSS. But the better near-term path is:

```text
Marco core
+ selected FinRobot-inspired finance-agent/reporting pieces
+ selected MikeOSS-inspired workflow/document/citation UX concepts
```

## Comparison

| Axis | FinRobot | MikeOSS | Marco implication |
| --- | --- | --- | --- |
| Primary domain | Financial AI agents, equity research, trading/risk workflows | Legal document assistant, workflows, tabular review, citations | FinRobot is closer to finance; MikeOSS is closer to workflow/document UX |
| License | Apache-2.0 | AGPL-3.0 | FinRobot is safer to borrow/fork for a product core |
| Current app shape | Python package plus FinRobot Equity FastAPI app | Next.js frontend, Express backend, Supabase, R2/S3 storage | Marco can stay Python-first for data/backtests and add a thin app/API |
| Strongest asset | Finance-specific agents, data adapters, report generation | Uploads, projects, reusable workflows, parallel tabular reviews, cited cells | Borrow different ideas from each |
| Weakest fit | Equity/FMP/report oriented, not vintage-safe macro backtesting | Legal-domain prompts and document-first storage model | Neither should replace Marco's macro kernel |
| Fork risk | Medium: useful but broad and possibly not clean enough as platform core | High: license and domain mismatch | Avoid full fork until a module-level spike proves value |

## What FinRobot Gives Us

FinRobot presents itself as an open-source financial AI agent platform. The
current public repo includes a general `finrobot` package plus a `finrobot_equity`
application that can run a local web interface, fetch data through Financial
Modeling Prep, generate projections and peer comparisons, run LLM-based report
section agents, and render HTML/PDF equity research reports.

Useful ideas for Marco:

- Specialized finance agents for separate report sections.
- A task-oriented web app rather than a pure chat UI.
- Report artifacts as durable HTML/PDF outputs.
- Data adapter organization for external finance APIs.
- Background task logs and output-serving patterns.
- A finance audience vocabulary: thesis, risk, valuation, catalysts, peer
  comparisons, forecasts.

Risks:

- It is built around equity research and FMP data, while Marco's immediate
  foundation is public macro data, vintage labeling, feature engineering, and
  walk-forward backtests.
- It can generate persuasive reports, but Marco needs explicit evidence,
  leakage checks, baselines, and reproducible run artifacts before persuasion.
- A full fork may import product surface area that does not help the first
  macro/FX/rate wedge.

## What MikeOSS Gives Us

MikeOSS is a legal-document assistant positioned as an open-source alternative
to Harvey and Legora. Its repo describes a Next.js frontend, Express backend,
Supabase Auth/Postgres, and Cloudflare R2-compatible storage. Its public site
emphasizes assistant chat over documents, project workspaces, spreadsheet-style
parallel extraction across documents, verifiable citations back to page/quote,
and reusable workflows.

Useful ideas for Marco:

- Project-scoped workspaces.
- User uploads with durable document/data objects.
- Reusable workflow templates users can run repeatedly.
- Tabular review as an interface for agent-produced structured outputs.
- Every extracted or generated claim linked back to source evidence.
- User-provided model keys and self-hosting story.

Risks:

- The repo is AGPL-3.0, which is a major product architecture constraint if its
  code becomes the hosted Marco core.
- Its prompts and core objects are legal-document-first, not macro time-series
  modeling-first.
- Its infrastructure footprint is heavier than needed for the next Marco step.

## The Shipped Agent

The hackathon-grade version should not be "a chatbot next to charts." It should
ship an agent with tools that operate over real artifacts.

First useful tool set:

```text
list_datasets
list_runs
inspect_run_metrics
compare_baselines
explain_feature_set
open_report_artifact
run_backtest_from_template
export_share_package
```

The agent must answer from the run registry and artifacts. It should be able to
say which model won, which baseline won, what data snapshot was used, what target
was predicted, and whether the run is latest-revised or vintage-safe.

Second useful tool set:

```text
upload_timeseries_file
infer_schema
map_columns_to_macro_concepts
validate_frequency_and_units
build_panel
run_template_workflow
save_workflow
publish_artifacts
```

That is where the platform starts to become more than a static report.

## Marco Platform Architecture

The platform should be artifact-first:

```text
source_data
  -> source_hashes
  -> normalized_series
  -> model_ready_panels
  -> feature_sets
  -> targets
  -> backtest_runs
  -> metrics
  -> model_artifacts
  -> reports
  -> agent_events
```

Core services:

- Data registry: catalogs raw sources, hashes, licenses, vintages, frequencies,
  countries, units, and transformations.
- Panel builder: converts source series into aligned monthly/quarterly panels.
- Feature engine: creates nominal/real interest differentials, inflation
  differentials, yield slopes, FX returns, lags, and rolling windows.
- Backtest runner: executes walk-forward baselines and models.
- Evaluation store: records metrics, split definitions, snapshots, and model
  artifacts.
- Agent runtime: exposes safe tools over the registry and runner.
- Workflow registry: stores reusable data/model/report recipes.
- Frontend: shows run comparisons, lets the agent operate, and eventually lets
  users upload data and launch workflows.

## Product Flywheel

The flywheel is not "more charts." It is:

```text
more public datasets
-> better normalized macro catalog
-> more reusable workflow templates
-> more backtest and model artifacts
-> better agent answers and recommendations
-> user-uploaded datasets mapped into the same structure
-> more evaluated examples for future model training
```

Custom model training only makes sense after the artifact layer is strong enough
to provide clean examples:

- Inputs: normalized panels, feature sets, vintage labels, split definitions.
- Outputs: predictions, explanations, portfolio/rate decisions, errors.
- Metadata: horizon, country pair, regime, model config, source snapshot.

## Near-Term Build Plan

1. Keep the current Marco FRED/FX/rate lab as the kernel.
2. Add a run registry API over committed and generated artifacts.
3. Add an agent endpoint with read-only tools over datasets, metrics, reports,
   and feature definitions.
4. Extend the Svelte frontend from static visualization to an agent workspace.
5. Add workflow templates for FRED FX/rate backtests.
6. Add user upload for CSV/Parquet time-series data with schema inference and
   manual column mapping.
7. Add saved custom workflows.
8. Add a model registry and background job runner.
9. Only then revisit MikeOSS-style document/table extraction for filings and EM
   financial statements.

## Fork Decision Rules

Fork FinRobot if:

- we need a finance-agent report generator faster than building our own;
- its FastAPI task/report app can be trimmed without importing too much equity
  baggage;
- we can keep Marco's data/backtest artifacts as the source of truth.

Fork or embed MikeOSS only if:

- document/table extraction becomes the active product center again;
- AGPL-3.0 obligations are acceptable for the hosted service;
- we want a separate, clearly licensed document-processing service rather than
  mixing it into Marco core.

Do neither if:

- the next milestone is still FRED ingestion, vintage-safe macro panels, FX/rate
  backtests, and an agent over those artifacts.

That is the current case.

## Sources Checked

- FinRobot repo: https://github.com/AI4Finance-Foundation/FinRobot
- FinRobot Equity README in the repo, including local web interface, FMP/OpenAI
  key requirements, multi-agent report pipeline, and Apache-2.0 license.
- MikeOSS repo: https://github.com/willchen96/mike
- MikeOSS site: https://mikeoss.com
- MikeOSS repo README and LICENSE, including Next.js/Express/Supabase/R2
  architecture and AGPL-3.0 license.

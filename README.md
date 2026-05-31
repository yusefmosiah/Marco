# emf

Emerging Markets Financials.

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

- [Current focus](docs/strategy/current-focus.md)
- [FRED-MD Macro Lab foundation mission](docs/missions/fred-md-macro-lab-foundation.md)
- [FRED FX/rate lab checkpoint](docs/runs/20260531-fred-fx-rate-lab-checkpoint.md)
- [Historical MikeOSS proposal](docs/proposals/mission-proposal.md)
- [Mobile-friendly PDF](output/pdf/emf-mission-proposal.pdf)

The custom frontend, MikeOSS integration, EM financial-statement extraction, and
deployment are intentionally out of scope until the FRED/backtesting foundation
is stronger.

## Macro Lab Quickstart

Install locally:

```sh
uv venv .venv
uv pip install --python .venv/bin/python -e '.[dev]'
```

Run the FRED FX/rate differential lab:

```sh
.venv/bin/emf-macro run-fx-rate-lab --root . --evaluation-start 2006-01 --horizons 1,3,6
```

Generated source data and backtest runs live under ignored `data/` and
`backtests/runs/` paths. Commit checkpoint summaries under `docs/runs/`, not
large generated data files.

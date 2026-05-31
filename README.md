# emf

Emerging Markets Financials.

This repo is the working home for the MikeOSS-backed workflow to pull emerging
markets financial statements, starting with India, and normalize them into a
cited JSON graph for cross-company and cross-market comparison.

Current artifact:

- [Mission proposal](docs/proposals/mission-proposal.md)
- [FRED-MD Macro Lab foundation mission](docs/missions/fred-md-macro-lab-foundation.md)
- [FRED FX/rate lab checkpoint](docs/runs/20260531-fred-fx-rate-lab-checkpoint.md)
- [Mobile-friendly PDF](output/pdf/emf-mission-proposal.pdf)

The initial mission is workflow-first. The custom frontend and production
deployment are intentionally deferred until the extraction and verification
pipeline works on real filings.

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

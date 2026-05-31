# Current Focus

Date: 2026-05-31

Status: active direction

## Active Priority

Focus on backtesting and FRED data.

The current product object is not MikeOSS, a legal-document workflow, or a UI.
It is a reproducible macro backtesting substrate:

```text
FRED / FRED-MD source data
-> hashed source cache
-> normalized macro facts
-> model-ready panels
-> feature engineering
-> walk-forward backtests
-> baseline comparisons
-> checkpoint reports
```

The first economic wedge is FX and rates:

```text
interest-rate differentials
real-rate differentials
inflation differentials
yield differentials
FX returns
policy-rate movement targets
```

## Deferred Lane

MikeOSS/table extraction is tabled for now.

That lane may return later for:

- tabular parallel extraction over filings;
- source-linked evidence review;
- human audit surfaces;
- financial-statement normalization.

But it should not drive current implementation decisions.

## Why This Separation Matters

The repo was mixing two different products:

- document/table extraction over financial filings;
- macro data panels and economic-model backtesting.

Both can eventually belong under EMF, but the near-term work needs one center of
gravity. The active center is:

```text
pull FRED data and backtest models honestly
```

## Near-Term Backtesting Roadmap

1. Keep the current FRED FX/rate lab working.
2. Add 12M and 24M forecast horizons.
3. Add rolling 120-month windows alongside expanding windows.
4. Add regime slices:
   - 2006-2012;
   - 2013-2019;
   - 2020-present.
5. Add spaced-origin robustness for 12M/24M targets.
6. Add ALFRED/vintage-aware pulls for one pair and one target.
7. Only after that, map India/EM macro sources.

## Current Rule

If a task does not improve FRED ingestion, panel construction, feature
engineering, leakage control, baseline comparison, or backtest reporting, it is
probably not part of the active mission.

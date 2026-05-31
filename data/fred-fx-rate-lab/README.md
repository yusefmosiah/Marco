# FRED FX/Rate Lab Data

This bundle publishes the local FRED/FRED-MD data used by Marco's current
FX/rate differential backtest.

Key files:

```text
panel_monthly.csv
panel_monthly.parquet
features_monthly.csv
features_monthly.parquet
macro_facts.jsonl
feature_manifest.jsonl
series_catalog.jsonl
source_manifest.json
validation_report.json
raw/
```

Coverage:

```text
126 FRED-MD monthly series
23 selected FRED FX/rate/CPI/yield series
1,349 monthly panel rows
6,745 engineered feature rows
latest_revised_snapshot vintage policy
```

`raw/` contains the hash-addressed source CSV snapshots used to build the
derived panel.

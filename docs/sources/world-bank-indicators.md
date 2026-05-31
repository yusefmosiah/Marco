# World Bank Indicators Source Adapter

Date: 2026-05-31

Status: smoke adapter implemented

## Purpose

World Bank Indicators gives Marco broad annual country coverage for global and
EM macro controls. It complements higher-frequency central-bank data:

```text
country annual controls
-> mapped macro observations
-> panel features and hypothesis context
```

## Official API Shape

World Bank documents indicator calls under:

```text
https://api.worldbank.org/v2/country/{countries}/indicator/{indicator}
```

Marco uses JSON responses:

```text
format=json
per_page=20000
date=YYYY:YYYY
```

Example:

```text
https://api.worldbank.org/v2/country/USA;IND;BRA;MEX;ZAF;IDN;TUR;CHN/indicator/NY.GDP.MKTP.CD?format=json&per_page=20000&date=2000%3A2024
```

## CLI

Fetch GDP for the current starter country basket:

```sh
emf-macro source-fetch world_bank_indicators \
  --root . \
  --country 'USA;IND;BRA;MEX;ZAF;IDN;TUR;CHN' \
  --indicator NY.GDP.MKTP.CD \
  --start-year 2000 \
  --end-year 2024
```

Inspect normalized observations:

```sh
emf-macro source-observations world_bank_indicators \
  --root . \
  --indicator NY.GDP.MKTP.CD \
  --limit 5
```

## Artifacts

Generated artifacts are ignored by git:

```text
data/raw/world_bank_indicators/<sha256>.json
data/derived/world_bank_indicators/<indicator_slug>/source_manifest.json
data/derived/world_bank_indicators/<indicator_slug>/observations.jsonl
data/derived/world_bank_indicators/<indicator_slug>/dataset_record.json
data/derived/world_bank_indicators/<indicator_slug>/dataset_mapping.json
```

## Current Local Haul

Fetched locally on 2026-05-31:

| Indicator | Meaning | Countries | Years | Observations |
| --- | --- | --- | --- | ---: |
| `NY.GDP.MKTP.CD` | GDP, current US dollars | USA, IND, BRA, MEX, ZAF, IDN, TUR, CHN | 2000-2024 | 200 |
| `FP.CPI.TOTL.ZG` | Inflation, consumer prices annual % | USA, IND, BRA, MEX, ZAF, IDN, TUR, CHN | 2000-2024 | 200 |
| `BN.CAB.XOKA.CD` | Current account balance, current US dollars | USA, IND, BRA, MEX, ZAF, IDN, TUR, CHN | 2000-2024 | 200 |
| `SP.POP.TOTL` | Population, total | USA, IND, BRA, MEX, ZAF, IDN, TUR, CHN | 2000-2024 | 200 |

Total: 800 normalized annual observations.

## Current Limits

- CI uses an offline fixture, not live World Bank access.
- The adapter stores one derived folder per indicator.
- The data is latest-revised annual data, not real-time vintage data.
- These controls are not yet joined into the FRED/ECB backtest panel.

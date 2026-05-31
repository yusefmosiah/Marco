# ECB SDMX Source Adapter

Date: 2026-05-31

Status: smoke adapter implemented

## Purpose

ECB is Marco's first non-FRED official central-bank source adapter. It proves
the source-ingestion shape needed for later IMF, OECD, BIS, RBI, and other
central-bank data:

```text
official API URL
-> raw response cached by sha256
-> normalized macro observations
-> dataset record
-> dataset mapping spec
```

The adapter is intentionally separate from the experiment runner. Source
ingestion emits mapped data artifacts; runner integration comes after panel
construction.

## Official API Shape

ECB documents the SDMX 2.1 REST endpoint as:

```text
https://data-api.ecb.europa.eu/service/data/{flowRef}/{seriesKey}
```

For exchange rates:

```text
flowRef: EXR
seriesKey: M.USD.EUR.SP00.A
format: csvdata
```

Example:

```text
https://data-api.ecb.europa.eu/service/data/EXR/M.USD.EUR.SP00.A?startPeriod=2024-01&endPeriod=2024-03&format=csvdata
```

## CLI

Fetch and cache a monthly USD/EUR exchange-rate series:

```sh
emf-macro source-fetch ecb_sdmx \
  --root . \
  --flow EXR \
  --series M.USD.EUR.SP00.A \
  --start-period 2024-01 \
  --end-period 2024-03
```

Inspect normalized observations:

```sh
emf-macro source-observations ecb_sdmx \
  --root . \
  --series M.USD.EUR.SP00.A \
  --limit 5
```

Inspect the catalog entry:

```sh
emf-macro sources inspect ecb_sdmx --root .
```

## Artifacts

Generated artifacts are ignored by git:

```text
data/raw/ecb_sdmx/<sha256>.csv
data/derived/ecb_sdmx/source_manifest.json
data/derived/ecb_sdmx/observations.jsonl
data/derived/ecb_sdmx/dataset_record.json
data/derived/ecb_sdmx/dataset_mapping.json
```

Normalized observations use:

```text
marco.macro_observation.v1
```

The mapping file uses:

```text
marco.dataset_mapping.v1
```

## Current Limits

- The adapter currently targets ECB CSV responses.
- CI uses an offline fixture, not the live ECB API.
- The first supported fixture is the ECB `EXR` exchange-rate flow.
- The adapter labels data as `latest_revised_snapshot`.
- No ALFRED-style real-time vintage safety is implied.
- No direct experiment-runner coupling exists yet.

## Next Adapter Path

Reuse this shape for:

1. IMF SDMX: global and EM macro bridge.
2. OECD SDMX: standardized cross-country macro datasets.
3. BIS SDMX: banking, credit, debt, property, and financial-cycle data.
4. RBI DBIE: India-specific macro data, likely with source-specific download
   discovery before SDMX-like normalization.

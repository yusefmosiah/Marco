# ECB SDMX Smoke Checkpoint

Date: 2026-05-31

Status: live smoke succeeded locally; CI remains fixture-only

## Command

```sh
emf-macro source-fetch ecb_sdmx \
  --root . \
  --flow EXR \
  --series M.USD.EUR.SP00.A \
  --start-period 2024-01 \
  --end-period 2024-03 \
  --compact
```

Then:

```sh
emf-macro source-observations ecb_sdmx \
  --root . \
  --series M.USD.EUR.SP00.A \
  --limit 2 \
  --compact
```

## Evidence

The fetch returned:

```json
{
  "schema_version": "marco.ecb_fetch.v1",
  "source_id": "ecb_sdmx",
  "flow": "EXR",
  "series_key": "M.USD.EUR.SP00.A",
  "observation_count": 3,
  "raw_sha256": "6ca199a1728f7fba60327d21d8d6f068d52c3ea615deec4569fb08e520385278",
  "raw_path": "data/raw/ecb_sdmx/6ca199a1728f7fba60327d21d8d6f068d52c3ea615deec4569fb08e520385278.csv",
  "observations_path": "data/derived/ecb_sdmx/observations.jsonl",
  "dataset_mapping_path": "data/derived/ecb_sdmx/dataset_mapping.json"
}
```

The generated dataset mapping used:

```json
{
  "schema_version": "marco.dataset_mapping.v1",
  "frequency": "M",
  "indicators": {
    "value": "exchange_rate"
  },
  "units": {
    "value": "USD"
  },
  "vintage_policy": "latest_revised_snapshot"
}
```

## Notes

- Generated ECB raw and derived artifacts remain ignored under `data/`.
- CI uses `tests/fixtures/ecb_exr_usd_eur.csv` and does not require live ECB
  network access.
- This proves the first official non-FRED central-bank adapter path.
- This does not yet build an ECB panel for backtesting.
- This does not imply real-time vintage safety.

## Next Path

1. Generalize shared SDMX utilities.
2. Add ECB panel construction for EUR/USD and euro-area rates.
3. Add IMF SDMX or ALFRED vintage-safe ingestion next, depending on whether
   breadth or backtest scientific validity is higher priority.

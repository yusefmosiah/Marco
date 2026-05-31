# World Bank Indicators Haul Checkpoint

Date: 2026-05-31

Status: live local fetch succeeded; CI remains fixture-only

## Country Basket

```text
USA;IND;BRA;MEX;ZAF;IDN;TUR;CHN
```

## Indicators

| Indicator | Meaning | Years | Observations |
| --- | --- | --- | ---: |
| `NY.GDP.MKTP.CD` | GDP, current US dollars | 2000-2024 | 200 |
| `FP.CPI.TOTL.ZG` | Inflation, consumer prices annual % | 2000-2024 | 200 |
| `BN.CAB.XOKA.CD` | Current account balance, current US dollars | 2000-2024 | 200 |
| `SP.POP.TOTL` | Population, total | 2000-2024 | 200 |

Total: 800 normalized annual observations.

## Commands

```sh
COUNTRIES='USA;IND;BRA;MEX;ZAF;IDN;TUR;CHN'

for IND in NY.GDP.MKTP.CD FP.CPI.TOTL.ZG BN.CAB.XOKA.CD SP.POP.TOTL; do
  emf-macro source-fetch world_bank_indicators \
    --root . \
    --country "$COUNTRIES" \
    --indicator "$IND" \
    --start-year 2000 \
    --end-year 2024
done
```

## Artifacts

Generated local files are ignored by git:

```text
data/raw/world_bank_indicators/*.json
data/derived/world_bank_indicators/ny_gdp_mktp_cd/
data/derived/world_bank_indicators/fp_cpi_totl_zg/
data/derived/world_bank_indicators/bn_cab_xoka_cd/
data/derived/world_bank_indicators/sp_pop_totl/
```

Each indicator folder contains:

```text
source_manifest.json
observations.jsonl
dataset_record.json
dataset_mapping.json
```

## Notes

- This is broad annual macro context, not high-frequency central-bank data.
- It is latest-revised World Bank data and not real-time vintage safe.
- The data is ready to be joined later as annual country controls or panel
  context after frequency mapping is explicit.

# World Bank Indicators Data

This bundle publishes Marco's current World Bank annual macro controls.

Indicators:

```text
NY.GDP.MKTP.CD     gdp_current_usd
FP.CPI.TOTL.ZG     inflation_cpi_annual_pct
BN.CAB.XOKA.CD     current_account_usd
SP.POP.TOTL        population_total
```

Coverage:

```text
countries: USA, IND, BRA, MEX, ZAF, IDN, TUR, CHN
years: 2000-2024
800 normalized observations
latest_revised_snapshot vintage policy
```

Each indicator directory contains:

```text
observations.jsonl
dataset_record.json
dataset_mapping.json
source_manifest.json
```

`raw/` contains the hash-addressed World Bank JSON responses.

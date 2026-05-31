# Global Macro Panel Data

This bundle publishes Marco's first normalized annual global macro panel.

Files:

```text
panel_annual.csv
panel_annual.jsonl
summary.json
```

Coverage:

```text
countries: BRA, CHN, IDN, IND, MEX, TUR, USA, ZAF
years: 2000-2024
rows: 200 country-year rows
features: current_account_usd, gdp_current_usd, inflation_cpi_annual_pct, population_total
latest_revised_snapshot vintage policy
```

This panel currently joins World Bank annual features. ECB observations are
tracked as source observations but are not joined into the annual panel.

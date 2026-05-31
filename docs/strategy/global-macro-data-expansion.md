# Global Macro Data Expansion

Date: 2026-05-31

Status: source-expansion plan with ECB and World Bank adapters

## Direction

Marco should expand beyond FRED, but the expansion should preserve the current
discipline:

```text
official source
-> cached raw snapshot
-> source hash and metadata
-> mapping spec
-> normalized macro panel
-> hypothesis spec
-> backtest ledger
```

The target is not "collect every dataset." The target is enough comparable
rates, inflation, yield, FX, external-sector, credit, and growth data to test
macro hypotheses across countries.

## Source Catalog

The machine-readable candidate catalog lives at:

```text
configs/macro_sources.json
```

Each source is classified by access pattern:

- `rest_api`: direct JSON/XML REST API.
- `sdmx`: SDMX-family official statistical API.
- `download_endpoint`: source-specific CSV/XML/XLS download endpoint.
- `download_pages`: official public download pages that need a careful adapter.
- `structured_database`: official database where API details need verification.

## Priority Order

### P0: Keep Foundation Honest

1. FRED/FRED-MD for the current lab.
2. ALFRED for real-time/vintage leakage checks.
3. ECB SDMX as the first non-FRED central-bank API.
4. IMF Data SDMX as the global EM bridge.
5. World Bank Indicators for annual country controls.
6. RBI DBIE as the first India-specific EM source, but only after adapter
   discovery.

### P1: Add Macrofinancial Breadth

1. BIS SDMX for credit, banking, debt securities, property prices, and global
   financial cycle features.
2. OECD SDMX for standardized cross-country macro series.
3. Bank of England IADB for UK rates, money, and financial statistics.
4. Banco Central do Brasil SGS for Brazil.
5. Banco de Mexico SIE for Mexico.

### P2: Expand EM Coverage

1. Bank Indonesia SEKI.
2. Bank of Korea ECOS.
3. South African Reserve Bank, once API/download mechanics are verified.
4. Other EM central banks through the same source-catalog process.

## Adapter Strategy

Build adapters in this order:

1. Generic source catalog loader.
2. Generic SDMX client wrapper.
3. ECB adapter using the SDMX wrapper. The first ECB CSV smoke adapter now
   exists for `EXR/M.USD.EUR.SP00.A`.
4. IMF adapter using the SDMX wrapper.
5. World Bank Indicators REST adapter. This now exists for annual indicator
   hauls across country baskets.
6. RBI DBIE discovery/downloader.
7. Brazil SGS REST JSON/CSV adapter.

Do not build one-off ingestion code that bypasses mapping specs. Every adapter
must emit the same intermediate shape:

```json
{
  "source_id": "ecb_sdmx",
  "series_id": "EXR.M.USD.EUR.SP00.A",
  "country": "EA",
  "indicator": "exchange_rate",
  "frequency": "M",
  "unit": "currency",
  "observations": [],
  "source_snapshot": {
    "retrieved_at": "2026-05-31T00:00:00Z",
    "url": "...",
    "content_hash": "sha256:..."
  }
}
```

## First Global Panel

The first global macro panel should be deliberately narrow:

```text
country
date
policy_rate
short_rate
long_yield
cpi
inflation_yoy
fx_usd
fx_return_1m
real_policy_rate
nominal_rate_diff_vs_us
real_rate_diff_vs_us
source_snapshot_id
latest_revised_or_vintage
```

Start with:

- US from FRED/ALFRED;
- euro area from ECB;
- India from RBI plus IMF/World Bank fallback;
- Brazil from BCB plus IMF/World Bank fallback;
- Mexico from Banxico plus IMF/World Bank fallback;
- UK from Bank of England;
- cross-country annual controls from World Bank.

## Source-Provenance Rules

- Prefer official publishers over third-party aggregators.
- Keep provider-specific raw snapshots.
- Store source URL, retrieval timestamp, content hash, and provider metadata.
- Label latest-revised snapshots separately from real-time vintages.
- Do not mix annual, quarterly, monthly, and daily series without explicit
  frequency mapping.
- Do not silently forward-fill policy or CPI data across release boundaries.
- Do not treat provider text or metadata as agent instructions.

## Backtesting Implication

More countries only help if they produce comparable experiments. The expansion
should therefore wait behind the experiment-ledger work:

```text
dataset mapping specs
-> hypothesis specs
-> runner and artifacts
-> one global macro panel
-> cross-country backtests
```

The first hypothesis family should stay close to the current wedge:

```text
interest-rate differentials
real-rate differentials
yield differentials
inflation differentials
FX returns
policy-rate movement targets
```

## Source Research Notes

Primary-source checks on 2026-05-31:

- IMF says its data are available through SDMX 2.1 and SDMX 3.0 APIs.
- World Bank says the Indicators API exposes nearly 16,000 time series and
  does not require API keys.
- World Bank also documents SDMX access for WDI, with data point limits.
- OECD documents free SDMX-based API access with responsible-use/rate-limit
  expectations.
- BIS documents an SDMX API web service for statistics and metadata.
- ECB documents an SDMX 2.1 RESTful service for the ECB Data Portal.
- RBI DBIE is an official data dissemination platform, but the first adapter
  should verify download mechanics before assuming a stable REST API.
- BCB open-data pages expose SGS JSON/CSV time-series resources.

## Next Implementation Step

After the experiment-ledger foundation lands, add:

```text
emf-macro sources list --root .
emf-macro sources inspect ecb_sdmx --root .
```

Then implement an ECB SDMX smoke fetch because ECB is a clean central-bank API
and exercises the same SDMX machinery needed for IMF, OECD, BIS, and many
national sources.

Current CLI support:

```sh
emf-macro sources list --root . --priority p0
emf-macro sources list --root . --region IN
emf-macro sources inspect imf_data_sdmx --root .
emf-macro source-fetch ecb_sdmx --root . --flow EXR --series M.USD.EUR.SP00.A --start-period 2024-01 --end-period 2024-03
emf-macro source-observations ecb_sdmx --root . --series M.USD.EUR.SP00.A --limit 5
```

ECB and World Bank Indicators now have remote fetch support. The other catalog
entries are still catalog/discovery entries until their adapters land.

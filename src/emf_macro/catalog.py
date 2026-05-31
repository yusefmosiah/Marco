from __future__ import annotations

from dataclasses import dataclass


FRED_MD_CURRENT_URL = (
    "https://www.stlouisfed.org/-/media/project/frbstl/stlouisfed/"
    "research/fred-md/monthly/2026-04-md.csv"
)


@dataclass(frozen=True)
class SeriesSpec:
    series_id: str
    indicator: str
    geo_id: str
    unit: str
    frequency: str = "monthly"
    dataset: str = "FRED"
    direction: str | None = None


@dataclass(frozen=True)
class PairSpec:
    pair: str
    country: str
    fx: SeriesSpec
    local_rate: SeriesSpec
    local_cpi: SeriesSpec
    local_yield_10y: SeriesSpec
    quote_convention: str
    positive_return_means: str


US_RATE = SeriesSpec("FEDFUNDS", "rates.policy.fed_funds", "US", "percent")
US_CPI = SeriesSpec("CPIAUCSL", "prices.cpi.all_items", "US", "index")
US_YIELD_10Y = SeriesSpec("DGS10", "rates.yield.10y", "US", "percent")


PAIR_SPECS: list[PairSpec] = [
    PairSpec(
        pair="EUR_USD",
        country="EA",
        fx=SeriesSpec(
            "DEXUSEU",
            "fx.spot.usd_per_eur",
            "EA",
            "USD per EUR",
            direction="USD_PER_FOREIGN",
        ),
        local_rate=SeriesSpec("IR3TIB01EZM156N", "rates.short.interbank_3m", "EA", "percent"),
        local_cpi=SeriesSpec("CP0000EZ19M086NEST", "prices.cpi.all_items", "EA", "index"),
        local_yield_10y=SeriesSpec("IRLTLT01EZM156N", "rates.yield.10y", "EA", "percent"),
        quote_convention="USD_PER_FOREIGN",
        positive_return_means="foreign_currency_appreciation_vs_usd",
    ),
    PairSpec(
        pair="USD_JPY",
        country="JP",
        fx=SeriesSpec(
            "DEXJPUS",
            "fx.spot.jpy_per_usd",
            "JP",
            "JPY per USD",
            direction="LOCAL_PER_USD",
        ),
        local_rate=SeriesSpec("IR3TIB01JPM156N", "rates.short.interbank_3m", "JP", "percent"),
        local_cpi=SeriesSpec("JPNCPIALLMINMEI", "prices.cpi.all_items", "JP", "index"),
        local_yield_10y=SeriesSpec("IRLTLT01JPM156N", "rates.yield.10y", "JP", "percent"),
        quote_convention="LOCAL_PER_USD",
        positive_return_means="foreign_currency_depreciation_vs_usd",
    ),
    PairSpec(
        pair="GBP_USD",
        country="GB",
        fx=SeriesSpec(
            "DEXUSUK",
            "fx.spot.usd_per_gbp",
            "GB",
            "USD per GBP",
            direction="USD_PER_FOREIGN",
        ),
        local_rate=SeriesSpec("IR3TIB01GBM156N", "rates.short.interbank_3m", "GB", "percent"),
        local_cpi=SeriesSpec("GBRCPIALLMINMEI", "prices.cpi.all_items", "GB", "index"),
        local_yield_10y=SeriesSpec("IRLTLT01GBM156N", "rates.yield.10y", "GB", "percent"),
        quote_convention="USD_PER_FOREIGN",
        positive_return_means="foreign_currency_appreciation_vs_usd",
    ),
    PairSpec(
        pair="USD_CAD",
        country="CA",
        fx=SeriesSpec(
            "DEXCAUS",
            "fx.spot.cad_per_usd",
            "CA",
            "CAD per USD",
            direction="LOCAL_PER_USD",
        ),
        local_rate=SeriesSpec("IR3TIB01CAM156N", "rates.short.interbank_3m", "CA", "percent"),
        local_cpi=SeriesSpec("CANCPIALLMINMEI", "prices.cpi.all_items", "CA", "index"),
        local_yield_10y=SeriesSpec("IRLTLT01CAM156N", "rates.yield.10y", "CA", "percent"),
        quote_convention="LOCAL_PER_USD",
        positive_return_means="foreign_currency_depreciation_vs_usd",
    ),
    PairSpec(
        pair="USD_MXN",
        country="MX",
        fx=SeriesSpec(
            "DEXMXUS",
            "fx.spot.mxn_per_usd",
            "MX",
            "MXN per USD",
            direction="LOCAL_PER_USD",
        ),
        local_rate=SeriesSpec("IR3TIB01MXM156N", "rates.short.interbank_3m", "MX", "percent"),
        local_cpi=SeriesSpec("MEXCPIALLMINMEI", "prices.cpi.all_items", "MX", "index"),
        local_yield_10y=SeriesSpec("IRLTLT01MXM156N", "rates.yield.10y", "MX", "percent"),
        quote_convention="LOCAL_PER_USD",
        positive_return_means="foreign_currency_depreciation_vs_usd",
    ),
]


def selected_series() -> list[SeriesSpec]:
    seen: dict[str, SeriesSpec] = {}
    for spec in [US_RATE, US_CPI, US_YIELD_10Y]:
        seen[spec.series_id] = spec
    for pair in PAIR_SPECS:
        for spec in [pair.fx, pair.local_rate, pair.local_cpi, pair.local_yield_10y]:
            seen[spec.series_id] = spec
    return list(seen.values())

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pandas as pd

from .catalog import FRED_MD_CURRENT_URL, SeriesSpec
from .io import SourceRecord, cache_source


def fred_csv_url(series_id: str) -> str:
    return f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"


def fetch_fred_md(raw_dir: Path) -> SourceRecord:
    return cache_source("fred_md_current", FRED_MD_CURRENT_URL, raw_dir)


def fetch_fred_series(spec: SeriesSpec, raw_dir: Path) -> SourceRecord:
    return cache_source(f"fred_{spec.series_id}", fred_csv_url(spec.series_id), raw_dir)


def parse_fred_md(record: SourceRecord) -> tuple[pd.DataFrame, dict[str, int]]:
    path = Path(record.raw_path)
    raw = pd.read_csv(path)
    if raw.empty or raw.iloc[0, 0] != "Transform:":
        raise ValueError("FRED-MD file did not contain expected Transform row")
    transform_row = raw.iloc[0].to_dict()
    tcodes = {
        col: int(transform_row[col])
        for col in raw.columns
        if col != "sasdate" and pd.notna(transform_row[col])
    }
    data = raw.iloc[1:].copy()
    data["sasdate"] = pd.to_datetime(data["sasdate"], errors="coerce")
    data = data.dropna(subset=["sasdate"]).set_index("sasdate")
    data = data.apply(pd.to_numeric, errors="coerce")
    data.index = data.index.to_period("M").to_timestamp("M")
    return data, tcodes


def parse_fred_series(record: SourceRecord, spec: SeriesSpec) -> pd.DataFrame:
    df = pd.read_csv(record.raw_path)
    expected = ["observation_date", spec.series_id]
    if list(df.columns[:2]) != expected:
        raise ValueError(f"{spec.series_id} CSV columns were {list(df.columns[:2])}")
    df["observation_date"] = pd.to_datetime(df["observation_date"], errors="coerce")
    df[spec.series_id] = pd.to_numeric(df[spec.series_id], errors="coerce")
    df = df.dropna(subset=["observation_date"])
    df = df.set_index("observation_date").sort_index()
    monthly = df[spec.series_id].resample("ME").last().to_frame(spec.series_id)
    return monthly


def catalog_row(spec: SeriesSpec, record: SourceRecord) -> dict:
    row = asdict(spec)
    row.update(
        {
            "source_url": record.url,
            "source_snapshot": record.sha256,
            "raw_path": record.raw_path,
            "vintage_policy": "latest_revised_snapshot",
        }
    )
    return row


def fred_md_catalog_rows(tcodes: dict[str, int], record: SourceRecord) -> list[dict]:
    return [
        {
            "series_id": series_id,
            "indicator": f"fred_md.{series_id}",
            "geo_id": "US",
            "unit": "source_reported",
            "frequency": "monthly",
            "dataset": "FRED-MD",
            "direction": None,
            "transformation_code": tcode,
            "source_url": record.url,
            "source_snapshot": record.sha256,
            "raw_path": record.raw_path,
            "vintage_policy": "latest_revised_snapshot",
        }
        for series_id, tcode in tcodes.items()
    ]

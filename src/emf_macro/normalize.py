from __future__ import annotations

import math

import pandas as pd

from .catalog import SeriesSpec


def facts_from_frame(
    frame: pd.DataFrame,
    catalog: dict[str, SeriesSpec],
    source_snapshots: dict[str, str],
) -> list[dict]:
    rows: list[dict] = []
    for period, values in frame.iterrows():
        period_str = period.to_period("M").strftime("%Y-%m")
        for series_id, value in values.dropna().items():
            spec = catalog.get(series_id)
            if not spec:
                continue
            rows.append(
                {
                    "geo_id": spec.geo_id,
                    "dataset": spec.dataset,
                    "source_series_id": series_id,
                    "indicator": spec.indicator,
                    "period": period_str,
                    "frequency": "monthly",
                    "value_raw": float(value),
                    "unit": spec.unit,
                    "direction": spec.direction,
                    "source_snapshot": source_snapshots[series_id],
                    "vintage_policy": "latest_revised_snapshot",
                    "evidence_id": f"fred:{series_id}:{period_str}",
                }
            )
    return rows


def fred_md_facts(frame: pd.DataFrame, source_snapshot: str) -> list[dict]:
    rows: list[dict] = []
    for period, values in frame.iterrows():
        period_str = period.to_period("M").strftime("%Y-%m")
        for series_id, value in values.dropna().items():
            if not math.isfinite(float(value)):
                continue
            rows.append(
                {
                    "geo_id": "US",
                    "dataset": "FRED-MD",
                    "source_series_id": series_id,
                    "indicator": f"fred_md.{series_id}",
                    "period": period_str,
                    "frequency": "monthly",
                    "value_raw": float(value),
                    "unit": "source_reported",
                    "direction": None,
                    "source_snapshot": source_snapshot,
                    "vintage_policy": "latest_revised_snapshot",
                    "evidence_id": f"fred-md:{series_id}:{period_str}",
                }
            )
    return rows

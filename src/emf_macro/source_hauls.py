from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .ecb import fetch_ecb_series
from .world_bank import fetch_world_bank_indicator


HAUL_SCHEMA = "marco.source_hauls.v1"


def load_source_hauls(root: Path) -> dict[str, Any]:
    path = root / "configs" / "source_hauls.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != HAUL_SCHEMA:
        raise ValueError(f"unsupported source haul schema: {payload.get('schema')}")
    return payload


def list_source_hauls(root: Path) -> list[dict[str, Any]]:
    return sorted(load_source_hauls(root)["hauls"], key=lambda row: row["id"])


def get_source_haul(root: Path, haul_id: str) -> dict[str, Any]:
    for haul in list_source_hauls(root):
        if haul["id"] == haul_id:
            return haul
    raise KeyError(haul_id)


def run_source_haul(root: Path, haul_id: str) -> dict[str, Any]:
    haul = get_source_haul(root, haul_id)
    results: list[dict[str, Any]] = []

    wb = haul.get("world_bank", {})
    countries = haul.get("countries", [])
    for indicator in wb.get("indicators", []):
        results.append(
            fetch_world_bank_indicator(
                root,
                countries,
                indicator["id"],
                start_year=wb.get("start_year"),
                end_year=wb.get("end_year"),
            )
        )

    ecb = haul.get("ecb", {})
    for series in ecb.get("series", []):
        results.append(
            fetch_ecb_series(
                root,
                series["key"],
                flow=series.get("flow", "EXR"),
                start_period=series.get("start_period"),
                end_period=series.get("end_period"),
            )
        )

    return {
        "schema_version": "marco.source_haul_result.v1",
        "haul_id": haul_id,
        "result_count": len(results),
        "results": results,
    }

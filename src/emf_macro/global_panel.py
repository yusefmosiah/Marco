from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .ecb import load_ecb_observations
from .io import ensure_dir, write_json, write_jsonl
from .source_hauls import get_source_haul
from .world_bank import load_world_bank_observations


PANEL_SCHEMA = "marco.global_macro_panel.v1"


def build_global_macro_panel(root: Path, haul_id: str = "global_macro_starter_20260531") -> dict[str, Any]:
    haul = get_source_haul(root, haul_id)
    wb_feature_names = {
        indicator["id"]: indicator["feature_name"]
        for indicator in haul.get("world_bank", {}).get("indicators", [])
    }
    wb_rows = load_world_bank_observations(root)
    ecb_rows = load_ecb_observations(root)

    panel_rows = build_world_bank_panel_rows(wb_rows, wb_feature_names)
    source_summary = summarize_sources(wb_rows, ecb_rows, wb_feature_names)
    derived_dir = ensure_dir(root / "data" / "derived" / "global_macro_panel")
    artifact_dir = ensure_dir(root / "artifacts" / "global-macro-panel" / haul_id)

    write_jsonl(derived_dir / "panel_annual.jsonl", panel_rows)
    write_panel_csv(derived_dir / "panel_annual.csv", panel_rows)

    summary = {
        "schema_version": PANEL_SCHEMA,
        "haul_id": haul_id,
        "vintage_policy": haul.get("vintage_policy", "latest_revised_snapshot"),
        "country_count": len({row["country"] for row in panel_rows}),
        "countries": sorted({row["country"] for row in panel_rows}),
        "year_count": len({row["year"] for row in panel_rows}),
        "years": sorted({row["year"] for row in panel_rows}),
        "panel_rows": len(panel_rows),
        "feature_count": len(wb_feature_names),
        "features": sorted(wb_feature_names.values()),
        "world_bank_observations": len(wb_rows),
        "ecb_observations": len(ecb_rows),
        "sources": source_summary,
        "generated_paths": {
            "panel_jsonl": str((derived_dir / "panel_annual.jsonl").relative_to(root)),
            "panel_csv": str((derived_dir / "panel_annual.csv").relative_to(root)),
        },
        "notes": [
            "World Bank data are annual latest-revised observations.",
            "ECB smoke observations are retained as source observations; they are not yet joined to the annual panel.",
            "Frequency joins must stay explicit before this panel is used in backtests.",
        ],
    }
    write_json(derived_dir / "summary.json", summary)
    write_json(artifact_dir / "summary.json", summary)
    return summary


def load_global_macro_summary(root: Path, haul_id: str = "global_macro_starter_20260531") -> dict[str, Any]:
    path = root / "artifacts" / "global-macro-panel" / haul_id / "summary.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    derived = root / "data" / "derived" / "global_macro_panel" / "summary.json"
    if derived.exists():
        return json.loads(derived.read_text(encoding="utf-8"))
    raise FileNotFoundError(path)


def build_world_bank_panel_rows(rows: list[dict[str, Any]], feature_names: dict[str, str]) -> list[dict[str, Any]]:
    keyed: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        feature = feature_names.get(row["indicator_code"])
        if feature is None:
            continue
        key = (row["country"], row["period"])
        panel_row = keyed.setdefault(
            key,
            {
                "schema_version": "marco.global_macro_panel_row.v1",
                "country": row["country"],
                "country_name": row["country_name"],
                "year": row["period"],
                "frequency": "A",
                "vintage_policy": row["vintage_policy"],
            },
        )
        panel_row[feature] = row["value"]
        panel_row[f"{feature}_source_snapshot_id"] = row["source_snapshot_id"]
    return [keyed[key] for key in sorted(keyed)]


def summarize_sources(
    wb_rows: list[dict[str, Any]],
    ecb_rows: list[dict[str, Any]],
    feature_names: dict[str, str],
) -> list[dict[str, Any]]:
    summary = []
    for indicator_code, feature_name in sorted(feature_names.items()):
        rows = [row for row in wb_rows if row["indicator_code"] == indicator_code]
        summary.append(
            {
                "source_id": "world_bank_indicators",
                "indicator_code": indicator_code,
                "feature_name": feature_name,
                "observation_count": len(rows),
                "countries": sorted({row["country"] for row in rows}),
                "years": sorted({row["period"] for row in rows}),
            }
        )
    if ecb_rows:
        summary.append(
            {
                "source_id": "ecb_sdmx",
                "series_keys": sorted({row["series_key"] for row in ecb_rows}),
                "observation_count": len(ecb_rows),
                "periods": sorted({row["period"] for row in ecb_rows}),
                "join_status": "retained_as_source_observations_not_joined_to_annual_panel",
            }
        )
    return summary


def write_panel_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    fieldnames = sorted({field for row in rows for field in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

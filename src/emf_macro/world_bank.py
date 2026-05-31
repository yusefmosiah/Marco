from __future__ import annotations

import json
import urllib.parse
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from .datasets import build_dataset_mapping_spec
from .io import SourceRecord, download_bytes, ensure_dir, sha256_bytes, write_json, write_jsonl


WORLD_BANK_SOURCE_ID = "world_bank_indicators"
WORLD_BANK_API_BASE = "https://api.worldbank.org/v2"


def world_bank_indicator_url(
    countries: list[str],
    indicator: str,
    *,
    start_year: int | None = None,
    end_year: int | None = None,
    per_page: int = 20000,
) -> str:
    country_path = ";".join(countries)
    params: dict[str, str | int] = {"format": "json", "per_page": per_page}
    if start_year is not None or end_year is not None:
        start = start_year if start_year is not None else ""
        end = end_year if end_year is not None else ""
        params["date"] = f"{start}:{end}"
    return (
        f"{WORLD_BANK_API_BASE}/country/{urllib.parse.quote(country_path, safe=';')}"
        f"/indicator/{urllib.parse.quote(indicator)}?{urllib.parse.urlencode(params)}"
    )


def fetch_world_bank_indicator(
    root: Path,
    countries: list[str],
    indicator: str,
    *,
    start_year: int | None = None,
    end_year: int | None = None,
    downloader: Callable[[str], bytes] = download_bytes,
) -> dict[str, Any]:
    url = world_bank_indicator_url(countries, indicator, start_year=start_year, end_year=end_year)
    raw_bytes = downloader(url)
    digest = sha256_bytes(raw_bytes)
    raw_dir = ensure_dir(root / "data" / "raw" / WORLD_BANK_SOURCE_ID)
    raw_path = raw_dir / f"{digest}.json"
    if not raw_path.exists():
        raw_path.write_bytes(raw_bytes)

    record = SourceRecord(
        logical_name=f"{WORLD_BANK_SOURCE_ID}:{indicator}:{';'.join(countries)}",
        url=url,
        sha256=digest,
        bytes=len(raw_bytes),
        fetched_at=utc_now_iso(),
        raw_path=str(raw_path.relative_to(root)),
    )
    observations = parse_world_bank_json(raw_bytes, source_record=record, indicator=indicator)
    if not observations:
        raise ValueError(f"World Bank response contained no observations for {indicator}")

    slug = indicator.lower().replace(".", "_")
    derived_dir = ensure_dir(root / "data" / "derived" / WORLD_BANK_SOURCE_ID / slug)
    observations_path = derived_dir / "observations.jsonl"
    dataset_record = dataset_record_for_observations(root, observations_path, observations, record, indicator, countries)
    mapping_spec = build_dataset_mapping_spec(
        dataset_record,
        date_column="period",
        value_columns=["value"],
        frequency="A",
        indicators={"value": observations[0]["indicator_code"]},
        units={"value": observations[0].get("unit") or "source_native"},
        vintage_policy="latest_revised_snapshot",
        source_snapshot_id=record.sha256,
    )

    write_json(derived_dir / "source_manifest.json", [asdict(record)])
    write_json(derived_dir / "dataset_record.json", dataset_record)
    write_json(derived_dir / "dataset_mapping.json", mapping_spec)
    write_jsonl(observations_path, observations)

    return {
        "schema_version": "marco.world_bank_fetch.v1",
        "source_id": WORLD_BANK_SOURCE_ID,
        "indicator": indicator,
        "countries": countries,
        "url": url,
        "raw_path": str(raw_path.relative_to(root)),
        "raw_sha256": digest,
        "observation_count": len(observations),
        "observations_path": str(observations_path.relative_to(root)),
        "dataset_record_path": str((derived_dir / "dataset_record.json").relative_to(root)),
        "dataset_mapping_path": str((derived_dir / "dataset_mapping.json").relative_to(root)),
    }


def parse_world_bank_json(raw_bytes: bytes, *, source_record: SourceRecord, indicator: str) -> list[dict[str, Any]]:
    payload = json.loads(raw_bytes.decode("utf-8-sig"))
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError("unexpected World Bank JSON response")
    rows = payload[1] or []
    observations = []
    for row in rows:
        value = row.get("value")
        if value is None:
            continue
        indicator_obj = row.get("indicator") or {}
        country_obj = row.get("country") or {}
        observations.append(
            {
                "schema_version": "marco.macro_observation.v1",
                "source_id": WORLD_BANK_SOURCE_ID,
                "provider": "World Bank",
                "indicator": "world_bank_indicator",
                "indicator_code": indicator_obj.get("id") or indicator,
                "indicator_name": indicator_obj.get("value"),
                "country": row.get("countryiso3code") or country_obj.get("id"),
                "country_name": country_obj.get("value"),
                "period": row.get("date"),
                "value": float(value),
                "frequency": "A",
                "unit": row.get("unit") or "",
                "decimal": row.get("decimal"),
                "observation_status": row.get("obs_status"),
                "source_snapshot_id": source_record.sha256,
                "source_url": source_record.url,
                "raw_path": source_record.raw_path,
                "vintage_policy": "latest_revised_snapshot",
            }
        )
    return sorted(observations, key=lambda row: (row["indicator_code"], row["country"], row["period"]))


def dataset_record_for_observations(
    root: Path,
    observations_path: Path,
    observations: list[dict[str, Any]],
    record: SourceRecord,
    indicator: str,
    countries: list[str],
) -> dict[str, Any]:
    return {
        "dataset_id": f"{WORLD_BANK_SOURCE_ID}-{indicator.lower().replace('.', '-')}-{record.sha256[:12]}",
        "name": f"World Bank {indicator}",
        "kind": "time_series",
        "source_type": "official_api",
        "source_uri": record.url,
        "stored_path": str(observations_path.relative_to(root)),
        "sha256": record.sha256,
        "byte_size": record.bytes,
        "created_at": record.fetched_at,
        "format": "jsonl",
        "schema": {
            "columns": sorted(observations[0].keys()),
            "sample_row_count": min(len(observations), 5),
            "column_count": len(observations[0]),
        },
        "tags": ["world_bank", "annual", indicator.lower(), *[country.lower() for country in countries[:10]]],
    }


def load_world_bank_observations(root: Path, *, indicator: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    base = root / "data" / "derived" / WORLD_BANK_SOURCE_ID
    if not base.exists():
        return []
    paths = sorted(base.glob("*/observations.jsonl"))
    rows = []
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if indicator and row.get("indicator_code") != indicator:
                continue
            rows.append(row)
            if limit and len(rows) >= limit:
                return rows
    return rows


def utc_now_iso() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat()

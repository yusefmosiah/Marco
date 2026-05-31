from __future__ import annotations

import csv
import io
import json
import urllib.parse
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from .datasets import build_dataset_mapping_spec
from .io import SourceRecord, download_bytes, ensure_dir, sha256_bytes, write_json, write_jsonl


ECB_SOURCE_ID = "ecb_sdmx"
ECB_API_BASE = "https://data-api.ecb.europa.eu/service/data"


def ecb_series_url(
    series_key: str,
    *,
    flow: str = "EXR",
    start_period: str | None = None,
    end_period: str | None = None,
    response_format: str = "csvdata",
) -> str:
    params = {"format": response_format}
    if start_period:
        params["startPeriod"] = start_period
    if end_period:
        params["endPeriod"] = end_period
    return f"{ECB_API_BASE}/{urllib.parse.quote(flow)}/{urllib.parse.quote(series_key)}?{urllib.parse.urlencode(params)}"


def fetch_ecb_series(
    root: Path,
    series_key: str,
    *,
    flow: str = "EXR",
    start_period: str | None = None,
    end_period: str | None = None,
    downloader: Callable[[str], bytes] = download_bytes,
) -> dict[str, Any]:
    url = ecb_series_url(flow=flow, series_key=series_key, start_period=start_period, end_period=end_period)
    raw_bytes = downloader(url)
    digest = sha256_bytes(raw_bytes)
    raw_dir = ensure_dir(root / "data" / "raw" / ECB_SOURCE_ID)
    raw_path = raw_dir / f"{digest}.csv"
    if not raw_path.exists():
        raw_path.write_bytes(raw_bytes)

    record = SourceRecord(
        logical_name=f"{ECB_SOURCE_ID}:{flow}:{series_key}",
        url=url,
        sha256=digest,
        bytes=len(raw_bytes),
        fetched_at=utc_now_iso(),
        raw_path=str(raw_path.relative_to(root)),
    )
    observations = parse_ecb_csv(raw_bytes, source_record=record, flow=flow, series_key=series_key)
    if not observations:
        raise ValueError(f"ECB response contained no observations for {flow}/{series_key}")

    derived_dir = ensure_dir(root / "data" / "derived" / ECB_SOURCE_ID)
    observations_path = derived_dir / "observations.jsonl"
    dataset_record = dataset_record_for_observations(root, observations_path, observations, record, flow, series_key)
    mapping_spec = build_dataset_mapping_spec(
        dataset_record,
        date_column="period",
        value_columns=["value"],
        frequency=observations[0]["frequency"],
        country=observations[0].get("country"),
        indicators={"value": observations[0]["indicator"]},
        units={"value": observations[0].get("unit") or "unknown"},
        vintage_policy="latest_revised_snapshot",
        source_snapshot_id=record.sha256,
    )

    write_json(derived_dir / "source_manifest.json", [asdict(record)])
    write_json(derived_dir / "dataset_record.json", dataset_record)
    write_json(derived_dir / "dataset_mapping.json", mapping_spec)
    write_jsonl(observations_path, observations)

    return {
        "schema_version": "marco.ecb_fetch.v1",
        "source_id": ECB_SOURCE_ID,
        "flow": flow,
        "series_key": series_key,
        "url": url,
        "raw_path": str(raw_path.relative_to(root)),
        "raw_sha256": digest,
        "observation_count": len(observations),
        "observations_path": str(observations_path.relative_to(root)),
        "dataset_record_path": str((derived_dir / "dataset_record.json").relative_to(root)),
        "dataset_mapping_path": str((derived_dir / "dataset_mapping.json").relative_to(root)),
    }


def parse_ecb_csv(
    raw_bytes: bytes,
    *,
    source_record: SourceRecord,
    flow: str,
    series_key: str,
) -> list[dict[str, Any]]:
    text = raw_bytes.decode("utf-8-sig")
    rows = csv.DictReader(io.StringIO(text))
    observations = []
    for row in rows:
        if not row.get("TIME_PERIOD") or not row.get("OBS_VALUE"):
            continue
        observations.append(
            {
                "schema_version": "marco.macro_observation.v1",
                "source_id": ECB_SOURCE_ID,
                "provider": "European Central Bank",
                "flow": flow,
                "series_key": series_key,
                "provider_series_id": row.get("KEY") or f"{flow}.{series_key}",
                "period": row["TIME_PERIOD"],
                "value": float(row["OBS_VALUE"]),
                "frequency": row.get("FREQ") or infer_frequency(series_key),
                "indicator": indicator_for_flow(flow),
                "unit": row.get("UNIT") or row.get("CURRENCY"),
                "unit_multiplier": row.get("UNIT_MULT"),
                "currency": row.get("CURRENCY"),
                "currency_denom": row.get("CURRENCY_DENOM"),
                "exchange_rate_type": row.get("EXR_TYPE"),
                "exchange_rate_suffix": row.get("EXR_SUFFIX"),
                "title": row.get("TITLE"),
                "title_complement": row.get("TITLE_COMPL"),
                "observation_status": row.get("OBS_STATUS"),
                "source_snapshot_id": source_record.sha256,
                "source_url": source_record.url,
                "raw_path": source_record.raw_path,
                "vintage_policy": "latest_revised_snapshot",
            }
        )
    return observations


def dataset_record_for_observations(
    root: Path,
    observations_path: Path,
    observations: list[dict[str, Any]],
    record: SourceRecord,
    flow: str,
    series_key: str,
) -> dict[str, Any]:
    return {
        "dataset_id": f"{ECB_SOURCE_ID}-{flow.lower()}-{series_key.lower().replace('.', '-')}-{record.sha256[:12]}",
        "name": f"ECB {flow} {series_key}",
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
        "tags": ["ecb", flow.lower(), observations[0]["indicator"]],
    }


def load_ecb_observations(root: Path, *, series_key: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    path = root / "data" / "derived" / ECB_SOURCE_ID / "observations.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if series_key and row.get("series_key") != series_key:
            continue
        rows.append(row)
        if limit and len(rows) >= limit:
            break
    return rows


def indicator_for_flow(flow: str) -> str:
    if flow == "EXR":
        return "exchange_rate"
    return flow.lower()


def infer_frequency(series_key: str) -> str:
    return series_key.split(".", 1)[0] if "." in series_key else "unknown"


def utc_now_iso() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat()

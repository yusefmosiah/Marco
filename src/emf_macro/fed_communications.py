from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from .datasets import build_dataset_mapping_spec
from .io import SourceRecord, download_bytes, ensure_dir, sha256_bytes, write_json, write_jsonl


FED_COMMUNICATIONS_SOURCE_ID = "fed_fomc_communications"
FED_COMMUNICATIONS_URL = "https://raw.githubusercontent.com/vtasca/fed-statement-scraping/master/communications.csv"


def fetch_fed_communications(
    root: Path,
    *,
    url: str = FED_COMMUNICATIONS_URL,
    downloader: Callable[[str], bytes] = download_bytes,
) -> dict[str, Any]:
    raw_bytes = downloader(url)
    digest = sha256_bytes(raw_bytes)
    raw_dir = ensure_dir(root / "data" / "raw" / FED_COMMUNICATIONS_SOURCE_ID)
    raw_path = raw_dir / f"{digest}.csv"
    if not raw_path.exists():
        raw_path.write_bytes(raw_bytes)

    record = SourceRecord(
        logical_name=f"{FED_COMMUNICATIONS_SOURCE_ID}:communications",
        url=url,
        sha256=digest,
        bytes=len(raw_bytes),
        fetched_at=utc_now_iso(),
        raw_path=str(raw_path.relative_to(root)),
    )
    observations = parse_fed_communications_csv(raw_bytes, source_record=record)
    if not observations:
        raise ValueError("Fed communications response contained no observations")

    derived_dir = ensure_dir(root / "data" / "derived" / FED_COMMUNICATIONS_SOURCE_ID)
    public_data_dir = ensure_dir(root / "data" / "fed-fomc-communications")
    observations_path = derived_dir / "observations.jsonl"
    public_csv_path = public_data_dir / "communications.csv"
    public_observations_path = public_data_dir / "observations.jsonl"
    dataset_record = dataset_record_for_observations(root, observations_path, observations, record)
    mapping_spec = build_dataset_mapping_spec(
        dataset_record,
        date_column="event_date",
        value_columns=["word_count", "text_length"],
        frequency="D",
        country="US",
        indicators={
            "word_count": "fed_communication.word_count",
            "text_length": "fed_communication.text_length",
        },
        units={"word_count": "words", "text_length": "characters"},
        vintage_policy="latest_revised_snapshot",
        source_snapshot_id=record.sha256,
    )
    summary = summarize_observations(observations, record)

    if not public_csv_path.exists() or public_csv_path.read_bytes() != raw_bytes:
        public_csv_path.write_bytes(raw_bytes)
    write_json(derived_dir / "source_manifest.json", [asdict(record)])
    write_json(derived_dir / "dataset_record.json", dataset_record)
    write_json(derived_dir / "dataset_mapping.json", mapping_spec)
    write_json(derived_dir / "summary.json", summary)
    write_json(root / "artifacts" / "fed-fomc-communications" / "summary.json", summary)
    write_jsonl(observations_path, observations)
    write_jsonl(public_observations_path, observations)
    write_json(public_data_dir / "source_manifest.json", [asdict(record)])
    write_json(public_data_dir / "dataset_record.json", dataset_record)
    write_json(public_data_dir / "dataset_mapping.json", mapping_spec)
    write_json(public_data_dir / "summary.json", summary)

    return {
        "schema_version": "marco.fed_communications_fetch.v1",
        "source_id": FED_COMMUNICATIONS_SOURCE_ID,
        "url": url,
        "raw_path": str(raw_path.relative_to(root)),
        "raw_sha256": digest,
        "observation_count": len(observations),
        "minute_count": summary["type_counts"].get("Minute", 0),
        "statement_count": summary["type_counts"].get("Statement", 0),
        "observations_path": str(observations_path.relative_to(root)),
        "dataset_record_path": str((derived_dir / "dataset_record.json").relative_to(root)),
        "dataset_mapping_path": str((derived_dir / "dataset_mapping.json").relative_to(root)),
        "summary_path": str((derived_dir / "summary.json").relative_to(root)),
        "artifact_summary_path": "artifacts/fed-fomc-communications/summary.json",
        "data_bundle_path": str(public_data_dir.relative_to(root)),
        "public_csv_path": str(public_csv_path.relative_to(root)),
        "public_observations_path": str(public_observations_path.relative_to(root)),
    }


def parse_fed_communications_csv(raw_bytes: bytes, *, source_record: SourceRecord) -> list[dict[str, Any]]:
    text = raw_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    observations = []
    for index, row in enumerate(reader):
        meeting_date = clean(row.get("Date"))
        release_date = clean(row.get("Release Date"))
        communication_type = clean(row.get("Type"))
        body = normalize_text(row.get("Text") or "")
        if not meeting_date or not communication_type or not body:
            continue
        event_date = release_date or meeting_date
        observations.append(
            {
                "schema_version": "marco.fed_communication.v1",
                "source_id": FED_COMMUNICATIONS_SOURCE_ID,
                "provider": "vtasca/fed-statement-scraping",
                "primary_source": "Federal Reserve",
                "communication_id": f"fomc-{meeting_date}-{communication_type.lower()}-{index}",
                "meeting_date": meeting_date,
                "release_date": release_date,
                "release_date_missing": not release_date,
                "event_date": event_date,
                "communication_type": communication_type,
                "text": body,
                "text_length": len(body),
                "word_count": len(body.split()),
                "sequence": index,
                "frequency": "event",
                "country": "US",
                "indicator": "fed_fomc_communication",
                "source_snapshot_id": source_record.sha256,
                "source_url": source_record.url,
                "raw_path": source_record.raw_path,
                "vintage_policy": "latest_revised_snapshot",
            }
        )
    return sorted(observations, key=lambda row: (row["event_date"], row["meeting_date"], row["communication_type"], row["sequence"]))


def dataset_record_for_observations(
    root: Path,
    observations_path: Path,
    observations: list[dict[str, Any]],
    record: SourceRecord,
) -> dict[str, Any]:
    return {
        "dataset_id": f"{FED_COMMUNICATIONS_SOURCE_ID}-{record.sha256[:12]}",
        "name": "FOMC statements and minutes communications corpus",
        "kind": "text_event_corpus",
        "source_type": "github_open_dataset",
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
        "tags": ["fed", "fomc", "minutes", "statements", "text", "monetary_policy"],
    }


def summarize_observations(observations: list[dict[str, Any]], record: SourceRecord) -> dict[str, Any]:
    type_counts: dict[str, int] = {}
    for row in observations:
        type_counts[row["communication_type"]] = type_counts.get(row["communication_type"], 0) + 1
    release_dates = [row["release_date"] for row in observations if row["release_date"]]
    event_dates = [row["event_date"] for row in observations]
    meeting_dates = [row["meeting_date"] for row in observations]
    return {
        "schema_version": "marco.fed_communications_summary.v1",
        "source_id": FED_COMMUNICATIONS_SOURCE_ID,
        "provider": "vtasca/fed-statement-scraping",
        "primary_source": "Federal Reserve",
        "source_url": record.url,
        "source_snapshot_id": record.sha256,
        "raw_path": record.raw_path,
        "vintage_policy": "latest_revised_snapshot",
        "observation_count": len(observations),
        "type_counts": dict(sorted(type_counts.items())),
        "release_date_missing_count": sum(1 for row in observations if row["release_date_missing"]),
        "first_meeting_date": min(meeting_dates),
        "last_meeting_date": max(meeting_dates),
        "first_release_date": min(release_dates) if release_dates else None,
        "last_release_date": max(release_dates) if release_dates else None,
        "first_event_date": min(event_dates),
        "last_event_date": max(event_dates),
        "fields": [
            "meeting_date",
            "release_date",
            "event_date",
            "communication_type",
            "text",
            "word_count",
            "text_length",
        ],
        "notes": [
            "This is an open GitHub dataset derived from Federal Reserve FOMC statements and minutes pages.",
            "The raw corpus contains both Statement and Minute rows; use communication_type=Minute for minutes-only analysis.",
            "Some source rows have blank release dates; event_date falls back to meeting_date for those rows.",
            "Text is event-time policy communication data, not a numeric macro time series.",
        ],
    }


def load_fed_communications(
    root: Path,
    *,
    communication_type: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    path = root / "data" / "derived" / FED_COMMUNICATIONS_SOURCE_ID / "observations.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if communication_type and row.get("communication_type", "").lower() != communication_type.lower():
            continue
        rows.append(row)
        if limit and len(rows) >= limit:
            break
    return rows


def clean(value: str | None) -> str:
    return (value or "").strip()


def normalize_text(value: str) -> str:
    return " ".join(value.split())


def utc_now_iso() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat()

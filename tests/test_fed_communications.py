from __future__ import annotations

from pathlib import Path

from emf_macro.fed_communications import (
    fetch_fed_communications,
    load_fed_communications,
    parse_fed_communications_csv,
)
from emf_macro.io import SourceRecord


def test_parse_fed_communications_fixture() -> None:
    raw = Path("tests/fixtures/fed_communications_sample.csv").read_bytes()
    record = SourceRecord(
        logical_name="test",
        url="https://example.com/communications.csv",
        sha256="abc123",
        bytes=len(raw),
        fetched_at="2026-05-31T00:00:00Z",
        raw_path="data/raw/test.csv",
    )

    rows = parse_fed_communications_csv(raw, source_record=record)

    assert len(rows) == 4
    assert [row["communication_type"] for row in rows].count("Minute") == 3
    assert rows[0]["event_date"] == "2024-01-31"
    assert rows[0]["release_date_missing"] is False
    assert any(row["release_date_missing"] for row in rows)
    assert rows[0]["word_count"] > 0
    assert rows[0]["source_snapshot_id"] == "abc123"


def test_fetch_fed_communications_writes_dataset(tmp_path: Path) -> None:
    raw = Path("tests/fixtures/fed_communications_sample.csv").read_bytes()

    result = fetch_fed_communications(tmp_path, downloader=lambda _url: raw)

    assert result["observation_count"] == 4
    assert result["minute_count"] == 3
    assert (tmp_path / result["observations_path"]).exists()
    assert (tmp_path / result["dataset_mapping_path"]).exists()
    assert (tmp_path / "artifacts" / "fed-fomc-communications" / "summary.json").exists()
    assert (tmp_path / "data" / "fed-fomc-communications" / "communications.csv").exists()
    assert (tmp_path / "data" / "fed-fomc-communications" / "observations.jsonl").exists()
    assert (tmp_path / "data" / "fed-fomc-communications" / "summary.json").exists()
    assert len(load_fed_communications(tmp_path, communication_type="Minute")) == 3

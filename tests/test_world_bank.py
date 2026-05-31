from __future__ import annotations

import json
from pathlib import Path

from emf_macro.io import SourceRecord, sha256_bytes
from emf_macro.world_bank import (
    fetch_world_bank_indicator,
    load_world_bank_observations,
    parse_world_bank_json,
    world_bank_indicator_url,
)


FIXTURE = Path("tests/fixtures/world_bank_gdp_sample.json")


def test_world_bank_indicator_url_matches_official_shape() -> None:
    url = world_bank_indicator_url(["IND", "BRA", "MEX"], "NY.GDP.MKTP.CD", start_year=2020, end_year=2023)

    assert url.startswith("https://api.worldbank.org/v2/country/IND;BRA;MEX/indicator/NY.GDP.MKTP.CD?")
    assert "format=json" in url
    assert "per_page=20000" in url
    assert "date=2020%3A2023" in url


def test_parse_world_bank_json_normalizes_observations() -> None:
    raw = FIXTURE.read_bytes()
    record = SourceRecord(
        logical_name="world_bank_indicators:NY.GDP.MKTP.CD:IND;BRA;MEX;ZAF",
        url="https://example.test/world-bank.json",
        sha256=sha256_bytes(raw),
        bytes=len(raw),
        fetched_at="2026-05-31T00:00:00+00:00",
        raw_path="data/raw/world_bank_indicators/example.json",
    )

    rows = parse_world_bank_json(raw, source_record=record, indicator="NY.GDP.MKTP.CD")

    assert len(rows) == 4
    assert rows[0]["schema_version"] == "marco.macro_observation.v1"
    assert rows[0]["source_id"] == "world_bank_indicators"
    assert rows[0]["indicator_code"] == "NY.GDP.MKTP.CD"
    assert rows[0]["frequency"] == "A"
    assert rows[0]["country"] == "BRA"
    assert rows[0]["period"] == "2023"
    assert rows[0]["source_snapshot_id"] == record.sha256


def test_fetch_world_bank_indicator_uses_downloader_and_writes_artifacts(tmp_path: Path) -> None:
    raw = FIXTURE.read_bytes()
    seen_urls: list[str] = []

    def fake_downloader(url: str) -> bytes:
        seen_urls.append(url)
        return raw

    result = fetch_world_bank_indicator(
        tmp_path,
        ["IND", "BRA", "MEX", "ZAF"],
        "NY.GDP.MKTP.CD",
        start_year=2023,
        end_year=2023,
        downloader=fake_downloader,
    )

    assert seen_urls
    assert result["schema_version"] == "marco.world_bank_fetch.v1"
    assert result["observation_count"] == 4
    assert (tmp_path / result["raw_path"]).exists()
    assert (tmp_path / result["observations_path"]).exists()
    mapping = json.loads((tmp_path / result["dataset_mapping_path"]).read_text(encoding="utf-8"))
    assert mapping["schema_version"] == "marco.dataset_mapping.v1"
    assert mapping["indicators"] == {"value": "NY.GDP.MKTP.CD"}

    rows = load_world_bank_observations(tmp_path, indicator="NY.GDP.MKTP.CD", limit=2)
    assert [row["indicator_code"] for row in rows] == ["NY.GDP.MKTP.CD", "NY.GDP.MKTP.CD"]

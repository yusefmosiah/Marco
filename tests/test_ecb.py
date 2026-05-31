from __future__ import annotations

import json
from pathlib import Path

from emf_macro.ecb import ecb_series_url, fetch_ecb_series, load_ecb_observations, parse_ecb_csv
from emf_macro.io import SourceRecord, sha256_bytes


FIXTURE = Path("tests/fixtures/ecb_exr_usd_eur.csv")


def test_ecb_series_url_matches_official_shape() -> None:
    url = ecb_series_url("M.USD.EUR.SP00.A", start_period="2024-01", end_period="2024-03")

    assert url.startswith("https://data-api.ecb.europa.eu/service/data/EXR/M.USD.EUR.SP00.A?")
    assert "format=csvdata" in url
    assert "startPeriod=2024-01" in url
    assert "endPeriod=2024-03" in url


def test_parse_ecb_csv_normalizes_observations() -> None:
    raw = FIXTURE.read_bytes()
    record = SourceRecord(
        logical_name="ecb_sdmx:EXR:M.USD.EUR.SP00.A",
        url="https://example.test/ecb.csv",
        sha256=sha256_bytes(raw),
        bytes=len(raw),
        fetched_at="2026-05-31T00:00:00+00:00",
        raw_path="data/raw/ecb_sdmx/example.csv",
    )

    observations = parse_ecb_csv(raw, source_record=record, flow="EXR", series_key="M.USD.EUR.SP00.A")

    assert len(observations) == 3
    first = observations[0]
    assert first["schema_version"] == "marco.macro_observation.v1"
    assert first["source_id"] == "ecb_sdmx"
    assert first["indicator"] == "exchange_rate"
    assert first["period"] == "2024-01"
    assert first["value"] == 1.0905136363636
    assert first["currency"] == "USD"
    assert first["currency_denom"] == "EUR"
    assert first["source_snapshot_id"] == record.sha256


def test_fetch_ecb_series_uses_downloader_and_writes_artifacts(tmp_path: Path) -> None:
    raw = FIXTURE.read_bytes()
    seen_urls: list[str] = []

    def fake_downloader(url: str) -> bytes:
        seen_urls.append(url)
        return raw

    result = fetch_ecb_series(
        tmp_path,
        "M.USD.EUR.SP00.A",
        start_period="2024-01",
        end_period="2024-03",
        downloader=fake_downloader,
    )

    assert seen_urls
    assert result["schema_version"] == "marco.ecb_fetch.v1"
    assert result["observation_count"] == 3
    assert (tmp_path / result["raw_path"]).exists()
    assert (tmp_path / result["observations_path"]).exists()
    mapping = json.loads((tmp_path / result["dataset_mapping_path"]).read_text(encoding="utf-8"))
    assert mapping["schema_version"] == "marco.dataset_mapping.v1"
    assert mapping["source_snapshot_id"] == result["raw_sha256"]
    assert mapping["indicators"] == {"value": "exchange_rate"}

    rows = load_ecb_observations(tmp_path, series_key="M.USD.EUR.SP00.A", limit=2)
    assert [row["period"] for row in rows] == ["2024-01", "2024-02"]

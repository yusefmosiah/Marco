from __future__ import annotations

import json
from pathlib import Path

from emf_macro.io import SourceRecord
from emf_macro.news import FeedResponse, fetch_news, list_news_sources, load_news_items, parse_news_feed


def write_registry(root: Path) -> None:
    config_dir = root / "configs"
    config_dir.mkdir(parents=True)
    (config_dir / "news_sources.json").write_text(
        json.dumps(
            {
                "schema_version": "marco.news_sources.v1",
                "user_agent": "MarcoNewsTest/0.1",
                "sources": [
                    {
                        "auth_policy": "none",
                        "conditional_request_mode": "etag_last_modified",
                        "enabled": True,
                        "id": "example_central_bank",
                        "languages": ["en"],
                        "name": "Example Central Bank",
                        "poll_interval_seconds": 900,
                        "provider": "Example Central Bank",
                        "rate_limit": "polite_polling",
                        "regions": ["EX"],
                        "retention_days": 3650,
                        "robots_policy": "official_public_feed",
                        "store_body_policy": "metadata_and_summary",
                        "tier": "T1a",
                        "tos_class": "official_public_feed",
                        "type": "rss",
                        "url": "https://example.test/feed.xml",
                        "verticals": ["central_bank", "monetary_policy"],
                    }
                ],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def test_parse_news_feed_fixture_stable_identity() -> None:
    raw = Path("tests/fixtures/news_feed_sample.xml").read_bytes()
    source = {
        "id": "example_central_bank",
        "type": "rss",
        "provider": "Example Central Bank",
        "url": "https://example.test/feed.xml",
        "languages": ["en"],
        "regions": ["EX"],
        "verticals": ["central_bank", "monetary_policy"],
        "tier": "T1a",
        "store_body_policy": "metadata_and_summary",
        "conditional_request_mode": "etag_last_modified",
    }
    record = SourceRecord(
        logical_name="macro_news:example_central_bank",
        url=source["url"],
        sha256="abc123",
        bytes=len(raw),
        fetched_at="2026-05-31T00:00:00+00:00",
        raw_path="data/raw/macro_news/example.xml",
    )

    first = parse_news_feed(raw, source=source, source_record=record, retrieved_at=record.fetched_at)
    second = parse_news_feed(raw, source=source, source_record=record, retrieved_at=record.fetched_at)

    assert len(first) == 2
    assert [row["id"] for row in first] == [row["id"] for row in second]
    assert first[0]["source_snapshot_id"] == "abc123"
    assert first[0]["published_at"] == "2026-05-01T14:00:00+00:00"
    assert first[0]["vintage_policy"] == "publication_snapshot"
    assert "central_bank" in first[0]["vertical_tags"]


def test_fetch_news_writes_source_ledger_bundle(tmp_path: Path) -> None:
    write_registry(tmp_path)
    raw = Path("tests/fixtures/news_feed_sample.xml").read_bytes()

    def downloader(source: dict, user_agent: str) -> FeedResponse:
        assert source["id"] == "example_central_bank"
        assert user_agent == "MarcoNewsTest/0.1"
        return FeedResponse(
            url=source["url"],
            status_code=200,
            body=raw,
            etag_received='"fixture"',
            last_modified_received="Fri, 01 May 2026 14:00:00 GMT",
            content_type="application/rss+xml",
            latency_ms=7,
        )

    result = fetch_news(tmp_path, downloader=downloader)

    assert result["item_count"] == 2
    assert result["successful_source_count"] == 1
    assert (tmp_path / "data" / "macro-news" / "news_items.jsonl").exists()
    assert (tmp_path / "data" / "macro-news" / "fetches.jsonl").exists()
    assert (tmp_path / "data" / "macro-news" / "source_registry.json").exists()
    assert (tmp_path / "data" / "macro-news" / "summary.json").exists()
    assert (tmp_path / "artifacts" / "macro-news" / "summary.json").exists()
    assert (tmp_path / "apps" / "web" / "public" / "artifacts" / "macro-news-summary.json").exists()
    assert len(load_news_items(tmp_path, source_id="example_central_bank")) == 2
    assert list_news_sources(tmp_path, enabled_only=True)[0]["id"] == "example_central_bank"

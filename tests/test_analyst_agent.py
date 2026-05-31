from __future__ import annotations

import json
from pathlib import Path

from emf_macro.analyst_agent import run_analyst_agent


def test_analyst_agent_reads_latest_payload_and_writes_handoff(tmp_path: Path) -> None:
    write_analyst_payload(tmp_path)

    packet = run_analyst_agent(tmp_path, write_handoff=True)

    assert packet["schema_version"] == "marco.analyst_agent.v1"
    assert packet["agent_id"] == "analyst_agent"
    assert packet["summary"]["article_count"] == 1
    assert packet["summary"]["domain_counts"] == {"macro_fed": 1}
    assert packet["latest_articles"][0]["article_id"] == "article-1"
    latest = tmp_path / "data" / "agents" / "latest" / "analyst_agent.md"
    assert latest.exists()
    assert "schema_version: marco.agent_handoff.v1" in latest.read_text(encoding="utf-8")


def write_analyst_payload(root: Path) -> None:
    output_dir = root / "output" / "analyst"
    output_dir.mkdir(parents=True)
    payload = {
        "agent_id": "financial-news-ingestion-v1",
        "generated_at": "2026-05-31T20:00:00Z",
        "window_start": "2026-05-17T00:00:00Z",
        "window_end": "2026-05-31T23:59:59Z",
        "article_count": 1,
        "retrieval_errors": [],
        "articles": [
            {
                "article_id": "article-1",
                "event_cluster_id": "event-1",
                "domain": "macro_fed",
                "source_name": "Federal Reserve",
                "source_url": "https://www.federalreserve.gov/newsevents/test.htm",
                "syndication_origin": None,
                "published_at": "2026-05-30T12:00:00Z",
                "retrieved_at": "2026-05-31T20:00:00Z",
                "retrieval_status": "success",
                "headline": "Policy update",
                "summary": "Summary",
                "body_excerpt": "Excerpt",
                "tickers_mentioned": [],
                "assets_mentioned": [],
                "named_entities": {"organizations": ["Federal Reserve"], "people": [], "geographies": ["US"]},
                "is_primary_source": True,
            }
        ],
    }
    (output_dir / "financial-news-ingestion-latest.json").write_text(json.dumps(payload), encoding="utf-8")
    (output_dir / "financial-news-ingestion-latest.summary.md").write_text("# Analyst Ingestion Summary\n", encoding="utf-8")

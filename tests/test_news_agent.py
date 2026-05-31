from __future__ import annotations

import json
from pathlib import Path

from emf_macro.news_agent import run_news_model_agent


def write_news_bundle(root: Path, item_count: int = 3) -> None:
    bundle = root / "data" / "macro-news"
    bundle.mkdir(parents=True)
    items = []
    for index in range(item_count):
        items.append(
            {
                "id": f"news-{index}",
                "source_id": "example_central_bank",
                "provider": "Example Central Bank",
                "canonical_uri": f"https://example.test/{index}",
                "title": f"Policy item {index}",
                "summary": f"Summary {index}",
                "published_at": f"2026-05-{31-index:02d}T12:00:00+00:00",
                "regions": ["EX"],
                "vertical_tags": ["central_bank", "monetary_policy"],
                "source_snapshot_id": "abc123",
                "raw_path": "data/raw/macro_news/example.xml",
                "vintage_policy": "publication_snapshot",
            }
        )
    (bundle / "news_items.jsonl").write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in items),
        encoding="utf-8",
    )
    (bundle / "fetches.jsonl").write_text(
        json.dumps(
            {
                "id": "fetch-1",
                "source_id": "example_central_bank",
                "status_code": 200,
                "bytes": 123,
                "latency_ms": 7,
                "sha256": "abc123",
                "raw_path": "data/raw/macro_news/example.xml",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle / "summary.json").write_text(
        json.dumps(
            {
                "schema_version": "marco.news_summary.v1",
                "source_id": "macro_news",
                "item_count": item_count,
                "source_count": 1,
                "source_counts": {"example_central_bank": item_count},
                "region_counts": {"EX": item_count},
                "vertical_counts": {"central_bank": item_count, "monetary_policy": item_count},
                "first_published_at": "2026-05-29T12:00:00+00:00",
                "last_published_at": "2026-05-31T12:00:00+00:00",
                "vintage_policy": "publication_snapshot",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def test_news_model_agent_writes_journal_model_and_state(tmp_path: Path) -> None:
    write_news_bundle(tmp_path)

    result = run_news_model_agent(tmp_path, do_fetch=False, max_items_in_update=2)

    assert result["new_item_count"] == 3
    assert (tmp_path / "data" / "macro-news" / "model.md").exists()
    assert (tmp_path / result["journal_path"]).exists()
    assert (tmp_path / "data" / "macro-news" / "model_state.json").exists()
    model = (tmp_path / "data" / "macro-news" / "model.md").read_text(encoding="utf-8")
    journal = (tmp_path / result["journal_path"]).read_text(encoding="utf-8")
    assert "Marco Macro News Model" in model
    assert "Omitted from model update: 1 additional new items" in model
    assert "`news-0`" in journal
    assert "`news-2`" in journal

    second = run_news_model_agent(tmp_path, do_fetch=False)

    assert second["new_item_count"] == 0
    state = json.loads((tmp_path / "data" / "macro-news" / "model_state.json").read_text(encoding="utf-8"))
    assert state["seen_item_count"] == 3


def test_news_model_agent_prunes_old_updates(tmp_path: Path) -> None:
    write_news_bundle(tmp_path, item_count=8)
    first = run_news_model_agent(tmp_path, do_fetch=False, max_items_in_update=8)
    assert first["pruned_update_sections"] == 0
    state_path = tmp_path / "data" / "macro-news" / "model_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["seen_item_ids"] = []
    state_path.write_text(json.dumps(state), encoding="utf-8")

    second = run_news_model_agent(
        tmp_path,
        do_fetch=False,
        max_model_tokens=1000,
        prune_target_tokens=700,
        max_items_in_update=8,
    )

    assert second["pruned_update_sections"] >= 1

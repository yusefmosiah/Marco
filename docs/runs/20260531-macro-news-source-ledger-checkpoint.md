# Macro News Source Ledger Checkpoint

Date: 2026-05-31

This checkpoint adds Marco's first news-system foundation. It adapts the
Sourcecycled source-ledger idea into Marco's artifact-first repo shape.

## Result

Live official feeds fetched successfully:

| Source ID | Items |
| --- | ---: |
| `bis_central_bank_speeches` | 25 |
| `bis_press_releases` | 25 |
| `ecb_press` | 15 |
| `federal_reserve_press_all` | 20 |
| `federal_reserve_speeches` | 15 |

Total normalized news items: 100.

## Bundle

Committed data:

```text
data/macro-news/source_registry.json
data/macro-news/source_manifest.json
data/macro-news/fetches.jsonl
data/macro-news/news_items.jsonl
data/macro-news/dataset_record.json
data/macro-news/summary.json
```

Shareable summaries:

```text
artifacts/macro-news/summary.json
apps/web/public/artifacts/macro-news-summary.json
```

## Contract

Every normalized item has:

- stable `news-...` ID derived from source ID and original feed ID;
- provider/source/feed fields;
- canonical URL;
- title and feed-provided summary;
- publication timestamp where available;
- source snapshot hash;
- raw source path;
- `publication_snapshot` vintage policy.

Every fetch has:

- source ID and URL;
- status, byte count, latency;
- ETag and Last-Modified headers where supplied;
- raw hash/path;
- source policy fields.

## Verification

```sh
.venv/bin/python -m pytest -q tests/test_news.py
.venv/bin/emf-macro news-sources --root . --compact
.venv/bin/emf-macro news-fetch --root . --compact
.venv/bin/emf-macro news-summary --root . --compact
```

Focused tests passed before the live haul.

## Next

Build the news agent on top of `data/macro-news/news_items.jsonl`. The first
agent should create cited macro-policy briefs and should only cite exact
`news_item.id` records present in the ledger.

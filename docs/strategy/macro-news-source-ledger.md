# Marco Macro News Source Ledger

Status: v0 implemented foundation.

Marco's news lane borrows the useful parts of the Sourcecycled mission without
turning Marco into the standalone `sourcecycled` service yet.

The durable object is not a dashboard, feed reader, or generated article. It is:

```text
source registry
  -> polite official-feed fetches
  -> fetch audit records
  -> stable news item IDs
  -> normalized source-ledger bundle
  -> CLI/artifact/API-ready contracts
  -> future news agent
  -> future synthesis agent with the economic-modeling agent
```

## What We Kept From Sourcecycled

The Sourcecycled mission's strongest constraints carry directly into Marco:

- good-standing-first source policy;
- source registry before source sprawl;
- stable item identity across reruns;
- fetch audit rows for every source request;
- exact source item IDs for later citations;
- news content is data, not instructions;
- generated synthesis is a projection over the ledger, not the proof.

The full standalone Sourcecycled target includes SQLite, HTTP, WebSocket,
scheduler, issue synthesis, and exports. Marco v0 is intentionally smaller:
committed JSONL/artifacts and CLI first, with the agent/API layer coming next.

## Current Source Scope

The first source haul is official public central-bank and financial-stability
RSS/RDF feeds:

| Source ID | Provider | Feed | Region |
| --- | --- | --- | --- |
| `federal_reserve_press_all` | Federal Reserve Board | All press releases | US |
| `federal_reserve_speeches` | Federal Reserve Board | Speeches | US |
| `ecb_press` | European Central Bank | Press, speeches, interviews | EA/EU |
| `bis_press_releases` | Bank for International Settlements | Press releases | global |
| `bis_central_bank_speeches` | Bank for International Settlements | Central bank speeches | global |

This is a macro-policy news foundation, not broad market news. It is suitable
for the first news agent because the sources are official, policy-relevant, and
low-risk to poll politely.

## Schemas

Registry:

```text
configs/news_sources.json
schema_version = marco.news_sources.v1
```

Normalized item:

```text
schema_version = marco.news_item.v1
id = news-{sha256(source_id || canonical_original_id)[:24]}
source_id
provider
feed_url
original_id
canonical_uri
title
summary
published_at
retrieved_at
regions
vertical_tags
content_hash
source_snapshot_id
raw_path
vintage_policy = publication_snapshot
```

Fetch audit row:

```text
schema_version = marco.news_fetch_record.v1
source_id
url
status_code
bytes
latency_ms
etag_received
last_modified_received
sha256
raw_path
source_policy
```

## CLI

```sh
.venv/bin/emf-macro news-sources --root . --compact
.venv/bin/emf-macro news-fetch --root . --compact
.venv/bin/emf-macro news-summary --root . --compact
.venv/bin/emf-macro news-items --root . --limit 10 --compact
.venv/bin/emf-macro news-fetches --root . --limit 10 --compact
```

## Committed Bundle

The shareable bundle is:

```text
data/macro-news/
  source_registry.json
  source_manifest.json
  fetches.jsonl
  news_items.jsonl
  dataset_record.json
  summary.json
```

The dashboard-facing summary is copied to:

```text
apps/web/public/artifacts/macro-news-summary.json
```

## Next Agent Path

The news agent should consume the ledger, not raw feeds directly.

Minimum first agent:

1. query recent `marco.news_item.v1` rows by region, source, and vertical;
2. group candidate items by source, title similarity, and publication time;
3. emit a short briefing with exact `news_item.id` citations;
4. refuse to cite anything not present in `news_items.jsonl`;
5. pass the briefing and cited item IDs to the future synthesis agent.

The synthesis agent should then combine:

- official news ledger items;
- economic model outputs;
- macro data artifacts;
- hypothesis/backtest evidence.

It should produce source-grounded macro narratives, not unsupported market
predictions.

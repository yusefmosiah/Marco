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

The current source haul is official public central-bank, financial-regulatory,
and economic-release RSS/RDF feeds:

| Source ID | Provider | Region | Poll interval |
| --- | --- | --- | ---: |
| `federal_reserve_press_all` | Federal Reserve Board | US | 5m |
| `federal_reserve_monetary_policy` | Federal Reserve Board | US | 5m |
| `federal_reserve_banking_reg_policy` | Federal Reserve Board | US | 10m |
| `federal_reserve_speeches` | Federal Reserve Board | US | 15m |
| `sec_press_releases` | U.S. Securities and Exchange Commission | US | 10m |
| `bea_news_releases` | U.S. Bureau of Economic Analysis | US | 15m |
| `ecb_press` | European Central Bank | EA/EU | 5m |
| `bis_press_releases` | Bank for International Settlements | global | 15m |
| `bis_central_bank_speeches` | Bank for International Settlements | global | 30m |
| `rbi_press_releases` | Reserve Bank of India | IN | 5m |
| `rbi_notifications` | Reserve Bank of India | IN | 15m |
| `rbi_speeches` | Reserve Bank of India | IN | 30m |
| `bank_of_england_news` | Bank of England | GB | 10m |
| `bank_of_england_publications` | Bank of England | GB | 15m |
| `bank_of_england_speeches` | Bank of England | GB | 30m |
| `bank_of_japan_whats_new_en` | Bank of Japan | JP | 15m |
| `bank_of_japan_statistics_en` | Bank of Japan | JP | 30m |

This is a macro-policy and official financial/economic news foundation, not
broad market journalism. It is suitable for the first news agent because the
sources are official, policy-relevant, and low-risk to poll politely.

Configured polling density, if a scheduler is enabled:

| Interval | Sources |
| --- | ---: |
| 5 minutes | 4 |
| 10 minutes | 3 |
| 15 minutes | 6 |
| 30 minutes | 4 |

That averages 98 source polls per hour, or 24.5 source polls per 15-minute
window. Marco currently performs this fetch on demand through `news-fetch`; the
daemon/scheduler remains the next step.

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
.venv/bin/emf-macro news-agent-run --root . --compact
```

`news-agent-run` is the current deterministic news model agent. It:

1. runs `news-fetch`;
2. diffs item IDs against `data/macro-news/model_state.json`;
3. writes a per-fetch journal under `data/macro-news/fetch-journal/`;
4. prepends only the marginal update to `data/macro-news/model.md`;
5. prunes old update sections when `model.md` reaches the configured token
   budget.

Default pruning policy:

```text
max_model_tokens = 80000
prune_target_tokens = 50000
```

The token count is an approximate character-based budget. The agent is
deliberately deterministic and does not call an LLM yet; the future synthesis
agent can read `model.md` plus exact `news_item.id` citations.

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
  model.md
  model_state.json
  fetch-journal/
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

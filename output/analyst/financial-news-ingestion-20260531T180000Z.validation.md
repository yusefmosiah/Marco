# Analyst Run Validation

Run: `financial-news-ingestion-20260531T180000Z`

Raw JSON:

```text
output/analyst/financial-news-ingestion-20260531T180000Z.json
```

## Schema Check

Passed local structural validation:

- exact top-level keys;
- exact article object keys;
- `article_count` equals `articles.length`;
- all article domains are valid enum values;
- all `source_url` hosts are on the approved-source list;
- all `published_at` values are inside `2026-05-17T00:00:00Z` through `2026-05-31T23:59:59Z`;
- `article_id` values match SHA-256 of `source_url`, first 16 hex chars;
- `event_cluster_id` values match SHA-256 of normalized headline, first 16 hex chars;
- every `body_excerpt` is a string of 500 characters or fewer.

## Review Location

Review the resulting JSON at:

```text
output/analyst/financial-news-ingestion-20260531T180000Z.json
```

Before handing off to `sentiment-scoring-v1`, manually spot-check article URL
resolution and source text fidelity for the 8 collected articles.

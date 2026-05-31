# Analyst Run Validation

Run: `financial-news-ingestion-20260531T205630Z`

Raw JSON:

```text
output/analyst/financial-news-ingestion-20260531T205630Z.json
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

## Source Review Caveat

The raw agent payload should be reviewed before downstream sentiment scoring.
During spot validation, this AP URL did not resolve cleanly and should be
manually checked or dropped before promotion:

```text
https://apnews.com/article/stocks-markets-oil-iran-trump-68f9166e428621a5b3349d2d2aea34b5
```

Recommended review path:

1. Open the raw JSON file above.
2. Verify every article URL in a browser or fetcher.
3. Remove or mark failed any article whose `source_url` does not resolve.
4. Re-run the schema checks before sending to `sentiment-scoring-v1`.

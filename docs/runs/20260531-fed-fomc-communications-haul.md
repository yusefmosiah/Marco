# Fed FOMC Communications Haul Checkpoint

Date: 2026-05-31

Status: local pull complete

## What Happened

Marco integrated the `vtasca/fed-statement-scraping` `communications.csv`
dataset as a source adapter named:

```text
fed_fomc_communications
```

## Current Pull

```text
source-fetch fed_fomc_communications
```

Result:

| Item | Value |
| --- | ---: |
| Total communications | 464 |
| Minutes | 241 |
| Statements | 223 |
| Blank release-date rows | 29 |
| First event date | 2000-02-02 |
| Last event date | 2026-05-20 |
| Raw bytes | 12 MB |

## Files

Raw cached source:

```text
data/raw/fed_fomc_communications/ae6eb2b8a49c6334b762f92f4d080529bcafe1b4f2c805e5956ba09fec3f05f7.csv
```

Normalized local observations:

```text
data/derived/fed_fomc_communications/observations.jsonl
data/derived/fed_fomc_communications/dataset_record.json
data/derived/fed_fomc_communications/dataset_mapping.json
data/derived/fed_fomc_communications/source_manifest.json
data/derived/fed_fomc_communications/summary.json
```

Committed summary:

```text
artifacts/fed-fomc-communications/summary.json
```

## Evidence

```text
pytest -q tests/test_fed_communications.py
2 passed
```

## Limits

- This is a GitHub-hosted open dataset derived from Federal Reserve pages, not
  a direct Federal Reserve API adapter.
- Full text is stored under ignored `data/`; only compact summary metadata is
  committed.
- Text-derived features are not implemented yet.

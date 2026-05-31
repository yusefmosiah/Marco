# Fed FOMC Communications Source Adapter

Date: 2026-05-31

Status: active text-event corpus adapter

## Source

Marco ingests:

```text
https://raw.githubusercontent.com/vtasca/fed-statement-scraping/master/communications.csv
```

The upstream repository is:

```text
https://github.com/vtasca/fed-statement-scraping
```

The dataset is an open GitHub corpus derived from Federal Reserve FOMC
statements and minutes pages. It is not the FRED numeric time-series API.

## Current Haul

The current local pull produced:

| Item | Value |
| --- | ---: |
| Total rows | 464 |
| Minutes | 241 |
| Statements | 223 |
| Rows with blank release date | 29 |
| First event date | 2000-02-02 |
| Last event date | 2026-05-20 |

The raw CSV is cached by hash:

```text
data/raw/fed_fomc_communications/ae6eb2b8a49c6334b762f92f4d080529bcafe1b4f2c805e5956ba09fec3f05f7.csv
```

Normalized JSONL:

```text
data/derived/fed_fomc_communications/observations.jsonl
```

Committed compact summary:

```text
artifacts/fed-fomc-communications/summary.json
```

## Normalized Row Shape

Each row is a text event:

```text
meeting_date
release_date
event_date
release_date_missing
communication_type
text
word_count
text_length
source_snapshot_id
source_url
vintage_policy
```

`event_date` is the release date when present. For the 29 source rows where
`Release Date` is blank, `event_date` falls back to `meeting_date` and
`release_date_missing` is `true`.

## Commands

```sh
emf-macro source-fetch fed_fomc_communications --root .
emf-macro source-observations fed_fomc_communications --root . --communication-type Minute --limit 2
emf-macro sources inspect fed_fomc_communications --root .
```

## Modeling Use

This source should feed policy-communication features:

- hawkish/dovish tone;
- inflation emphasis;
- labor-market emphasis;
- uncertainty/forward-guidance language;
- event-date joins against FX, yields, and policy-rate targets.

It should not be presented as additional FRED data. It is a complementary Fed
communications corpus.

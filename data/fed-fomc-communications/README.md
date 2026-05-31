# Fed FOMC Communications Data

This directory is the repo-root shareable data bundle for the Marco
`fed_fomc_communications` source adapter.

Source:

```text
https://github.com/vtasca/fed-statement-scraping
https://raw.githubusercontent.com/vtasca/fed-statement-scraping/master/communications.csv
```

Files:

```text
communications.csv      Raw upstream CSV.
observations.jsonl      Normalized Marco text-event rows.
dataset_record.json     Dataset registry-style record.
dataset_mapping.json    Marco dataset mapping spec.
source_manifest.json    Source URL, hash, and fetch metadata.
summary.json            Compact counts and coverage summary.
```

Current pull:

```text
464 total communications
241 minutes
223 statements
29 rows with blank release date
2000-02-02 to 2026-05-20 event-date window
```

`event_date` is the release date when present. For rows where the upstream
`Release Date` is blank, `event_date` falls back to `meeting_date` and
`release_date_missing` is `true`.

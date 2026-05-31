# Macro News

Official public macro-policy news source ledger.

Current bundle:

```text
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

The current haul covers 17 Federal Reserve Board, SEC, BEA, ECB, BIS, RBI, Bank
of England, and Bank of Japan official feeds. It is metadata/summary-oriented
and uses `publication_snapshot` vintage labeling.

The future news agent should cite exact `news_item.id` values from
`news_items.jsonl`.

The current deterministic news model agent is:

```sh
emf-macro news-agent-run --root .
```

It writes one journal per fetch and updates `model.md` with only new marginal
items since the previous state. Older update sections are pruned when the model
approaches the configured 50k-80k token budget.

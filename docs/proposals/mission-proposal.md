# EMF Mission Proposal

Date: 2026-05-31

Project: `emf` - Emerging Markets Financials

Initial market: India

Core stack target: MikeOSS + Fireworks DeepSeek-V4-Flash + custom EM financial
graph workflow

## Executive Thesis

Build a real financial-statement normalization workflow, not a demo scraper.
The artifact is a reproducible system that can pull dense emerging-market
financial filings, extract statement facts with page-level evidence, reconcile
the extracted numbers, and emit a normalized JSON graph that supports comparison
across companies even when statement layouts, naming, units, calendars, and
sector-specific disclosures differ.

The first useful target is India because official exchange sources expose annual
reports, annual-report XBRL surfaces, financial-results XBRL, and standardized
taxonomy material. MikeOSS gives us the right interaction pattern: project
workspaces, uploaded documents, cited answers, workflows, and tabular review
across many documents. Fireworks DeepSeek-V4-Flash gives us low-cost 1M-context
agent calls with medium reasoning effort.

The critical path is not UI. It is evidence-preserving normalization.

## Research Findings

MikeOSS is a self-hostable legal AI platform with a Next.js frontend, Express
backend, Supabase Postgres/Auth, and R2/S3-compatible object storage. Its public
site positions it as an open-source alternative to Harvey and Legora, and its
tabular review feature is explicitly "spreadsheet-style extraction across
hundreds of documents in parallel" with every cell cited back to page and
quote. The GitHub README confirms the app has frontend, backend, document
processing, database schema, and model-provider key support.

Fireworks lists `accounts/fireworks/models/deepseek-v4-flash` as ready,
serverless, function-calling capable, no image input, 1040k-token context, and
priced at USD 0.14 input / USD 0.03 cached input / USD 0.28 output per 1M
tokens. Fireworks also supports OpenAI-compatible chat completions at
`https://api.fireworks.ai/inference/v1` and supports `reasoning_effort` values
including `medium`.

Mike does not currently look sufficient as-is for 300-page financial reports.
The current tabular route is legal-domain prompted, trims extracted document
text to 120,000 characters, and relies on text extraction rather than a
dedicated financial table/layout pipeline. That makes Mike a strong substrate
for document projects, citations, and tabular review, but we should add a
financial extraction orchestrator instead of pretending the existing legal
workflow is already the product.

India has multiple official source surfaces:

- NSE annual report pages and annual report XBRL pages.
- NSE XBRL filing infrastructure with standardized compliance structures and
  Regulation 33 financial result taxonomies for Ind AS, other non-bank
  companies, banks, NBFCs, insurance, REITs, and InvITs.
- BSE historical annual reports and company financial-result XBRL pages.
- MCA/XBRL India taxonomy material, including Ind AS taxonomy and Commercial
  and Industrial taxonomy.

## Cognitive Transforms

Current uncertainty or obstacle:

The tempting approach is to "use Mike tabular review on annual reports." That is
too shallow. The hard object is a normalized, cited financial fact graph that
survives malformed PDFs, sector-specific filings, and inconsistent labels.

Selected transforms:

1. Depth extraction - "tabular review" is not a spreadsheet. The load-bearing
   truth is cited, parallel extraction with verifiable cell provenance.
2. Homotopy preservation - do not build a toy scraper first. Start with the same
   source, graph, verifier, and evidence interfaces at low resolution.
3. Failure-mode inversion - assume cheap long context is not enough. Tables,
   units, page references, signs, restatements, and consolidated/standalone
   variants fail before token budget does.
4. Audience translation - for the hackathon, show Mike as the source/evidence
   workbench and the custom app as the graph/comparison surface, but keep the
   engineering core independent of the demo UI.

Route-changing insights:

- Mike should be integrated as a document/citation/workflow surface plus
  optionally patched provider, while `emf` owns financial ingestion,
  normalization, validation, and graph output.
- The first proof should use 3-5 companies across at least two sectors, not one
  polished single-company extraction.
- XBRL should be used as authoritative structure where available, while PDFs are
  still required because annual reports include notes, accounting policy text,
  segment disclosures, auditor context, and tables not always captured cleanly
  in exchange result feeds.
- Verifiers must check accounting identities and cite source spans. A JSON graph
  without validation and provenance is not useful.

Changed plan:

- Implementation: build `emf` as a new repo with a MikeOSS integration layer,
  Fireworks provider support, an Indian filing source adapter, a financial
  document parser, multiagent extraction, graph normalization, and validators.
- Verifier/evidence: require each normalized fact to carry source URL,
  document hash, page, quote or table cell coordinates, extraction agent,
  confidence, and validation status.
- Scope: first mission stops at a working local workflow and JSON graph for a
  small Indian company set; UI and deployment become the next mission.
- Stopping condition: sample graphs compare across companies with traceable
  facts and pass structural + accounting validation.

Next high-information action:

Clone Mike into the `emf` workspace or attach it as a submodule/fork, patch a
Fireworks chat-completions provider, and run one real annual report through a
minimal extraction graph to reveal the PDF/table failure surface.

## Mission Gradient

Real artifact:

A repository that can run a reproducible workflow:

1. Pull official Indian financial filings.
2. Preserve raw source files and metadata.
3. Extract financial statements and notes into typed candidate facts.
4. Normalize those facts into a global JSON graph.
5. Validate and reconcile the graph.
6. Expose evidence back to Mike-style citations and later to a custom frontend.

Value criterion:

Maximize comparable, validated financial-fact coverage per company while
minimizing unsupported facts, source ambiguity, schema drift, manual mapping,
and silent accounting errors.

Hard invariants:

- No normalized fact without provenance.
- No overwrite of raw filings; store by source URL and content hash.
- No hidden model/provider secrets in repo. Use `go-choir/.env` later as the
  operator-provided secret source, copied or loaded intentionally.
- No claim of "working" from a single happy-path document.
- No UI mission before the extraction and graph verifier are credible.
- No deployment mutation to `node-a`, Cloudflare, or `choir-ip.com` until the
  local workflow has a named artifact and rollback path.
- Respect source rate limits and terms; use bounded downloads and cache raw
  filings locally.

Quality target:

Solid. The first run should be production-shaped enough to continue for eight
hours without collapsing into one-off notebooks, while still small enough to
ship a hackathon-visible artifact.

Homotopy axes:

- Market: India only -> India plus other emerging markets.
- Source breadth: handpicked official URLs -> NSE/BSE/MCA adapters -> market
  source registry.
- Company set: 1 company -> 3-5 mixed-sector companies -> Nifty 50.
- Document complexity: clean PDF/XBRL -> long annual report -> scanned or
  image-heavy reports.
- Schema coverage: core income statement, balance sheet, cash flow -> notes,
  segments, ratios, restatements, ESG/BRSR.
- Verification: JSON schema -> accounting equations -> cross-source
  reconciliation -> historical consistency checks.
- Runtime: local CLI -> Mike project workflow -> deployed worker -> custom
  frontend.

Belief state:

- Strong: Mike has the document-workspace and cited-tabular UX shape we need.
- Strong: Fireworks DeepSeek-V4-Flash supports the target model ID, low-cost
  long context, function calling, and medium reasoning effort.
- Medium: Mike can be patched quickly for Fireworks because Fireworks is
  OpenAI-compatible, but Mike's current OpenAI adapter uses Responses API, so a
  direct Fireworks chat-completions adapter is cleaner than reusing the OpenAI
  provider path.
- Medium: NSE/BSE sources are accessible enough for bounded official pulls, but
  exact API behavior, headers, throttling, and XBRL download mechanics must be
  tested empirically.
- Low: PDF table quality. This is likely the largest extraction-risk field.

## Proposed Architecture

Repository layout:

```text
emf/
  docs/proposals/
  data/raw/                 # ignored; content-addressed filings
  data/derived/             # ignored; parser outputs and graph snapshots
  packages/
    emf-core/               # schema, validators, graph builder
    emf-agents/             # orchestration and prompts
    emf-sources/            # NSE/BSE/MCA/company IR adapters
    mike-adapter/           # Mike API/provider/workflow integration
  apps/
    cli/                    # run ingestion/extraction/validation locally
    frontend/               # later mission only
  vendor/
    mike/                   # optional submodule or fork, decision pending
```

Agent topology:

- Source Scout: discovers and downloads official filings, records metadata.
- Ingestion Agent: extracts per-page text, tables, page images, and document
  structure.
- Statement Locator: finds financial statements, schedules, notes, audit
  sections, units, period labels, and standalone/consolidated variants.
- Candidate Extractor: emits typed facts from statement tables and notes.
- Normalizer: maps local line items into canonical graph concepts.
- Reconciler: checks equations, signs, units, periods, duplicate concepts, and
  consolidated vs standalone separation.
- Citation Verifier: ensures each fact links to source page and quote/table
  evidence.
- Portfolio Coordinator: compares graph coverage across companies and reports
  schema gaps.

Fireworks integration:

- Add `FIREWORKS_API_KEY`, `FIREWORKS_BASE_URL`, and model IDs to the EMF
  runtime config.
- Use `accounts/fireworks/models/deepseek-v4-flash`.
- Use chat completions, not OpenAI Responses.
- Include `reasoning_effort: "medium"` for extraction, normalization, and
  verifier calls.
- Preserve reasoning summaries internally only if useful for audit. The public
  graph should expose evidence, not private chain-of-thought.

Mike integration options:

1. Patch Mike directly with a `fireworks` provider and financial workflows.
   Fast for demo cohesion, but creates a modified AGPL app we must track
   cleanly.
2. Keep Mike as a sibling/submodule and build `emf` as an external orchestrator
   that uses Mike for documents and review UX while owning graph extraction.
   Cleaner for long-term architecture.
3. Hybrid for hackathon: patch provider support in a fork, but keep financial
   graph logic in `emf` packages so it can later run without Mike.

Recommendation: hybrid. It gives the hackathon a visible MikeOSS story without
burying the EMF ontology inside legal-review code.

## Normalized JSON Graph Shape

The graph should preserve facts, concepts, statements, periods, entities, and
evidence separately.

```json
{
  "entity": {
    "id": "IN:NSE:RELIANCE",
    "legal_name": "Reliance Industries Limited",
    "country": "IN",
    "sector": "Energy / Conglomerate"
  },
  "filing": {
    "id": "sha256:...",
    "source_url": "https://...",
    "source_type": "annual_report_pdf",
    "fiscal_year": "2024-2025",
    "currency": "INR",
    "unit_scale": "millions"
  },
  "facts": [
    {
      "id": "fact:...",
      "concept": "revenue.total",
      "statement": "income_statement",
      "period": {
        "type": "year",
        "start": "2024-04-01",
        "end": "2025-03-31"
      },
      "scope": "consolidated",
      "value": 1000000,
      "unit": "INR",
      "scale": 1000000,
      "sign": "normal",
      "local_label": "Revenue from operations",
      "evidence": [
        {
          "document_id": "sha256:...",
          "page": 214,
          "quote": "Revenue from operations",
          "table_bbox": [72, 180, 520, 430]
        }
      ],
      "confidence": 0.88,
      "validation": {
        "status": "passed",
        "checks": ["source_cited", "schema_valid", "statement_equation"]
      }
    }
  ],
  "edges": [
    {
      "type": "rolls_up_to",
      "from": "revenue.operations",
      "to": "revenue.total"
    }
  ]
}
```

Core concept families:

- Entity identity: exchange symbol, ISIN, legal name, country, sector.
- Filing identity: source, fiscal year, report type, standalone/consolidated,
  accounting standard, currency, unit scale.
- Statements: income, balance sheet, cash flow, changes in equity.
- Periods: instant, quarter, half-year, fiscal year, prior-period comparative.
- Concepts: canonical IDs with aliases for local line items and market-specific
  terms.
- Evidence: document hash, URL, page, quote, table location, extraction method.
- Validation: schema checks, accounting equations, cross-source reconciliation,
  human overrides.

## Eight-Hour Autonomous Mission Draft

Mission status target: checkpoint_incomplete unless the full stopping condition
is met. This mission is too large to call complete from setup alone.

Hour 0-1: repo and Mike orientation

- Clone or submodule Mike into `emf`.
- Confirm Node, npm, Supabase/R2 expectations.
- Decide local storage substitute for first run if Supabase/R2 is not already
  available.
- Read provider code and tabular workflow code before patching.

Hour 1-2: Fireworks provider path

- Add Fireworks model catalog entry.
- Implement chat-completions adapter with streaming, tool calls, JSON mode where
  supported, and `reasoning_effort: "medium"`.
- Load secrets from operator-provided env, using `go-choir/.env` only as the
  known local source and never committing values.
- Smoke test one model call.

Hour 2-3: Indian source adapter

- Pull 3-5 official filings from NSE/BSE/company IR.
- Cache raw files by SHA-256.
- Record source metadata in JSONL.
- Prefer annual report PDF plus XBRL financial result where available.

Hour 3-4: parser and statement locator

- Extract per-page text and table candidates.
- Locate statement pages and unit/currency declarations.
- Emit a page/section manifest.

Hour 4-6: extraction and graph builder

- Run agents over each company.
- Extract core statement facts.
- Normalize aliases into canonical concepts.
- Emit one graph JSON per company plus a combined portfolio graph.

Hour 6-7: verification

- Validate JSON schema.
- Check balance sheet equation where possible.
- Check cash-flow subtotals where possible.
- Check every fact has provenance.
- Produce a coverage and error report.

Hour 7-8: package checkpoint

- Save run evidence.
- Create a short demo script: source file -> Mike/citation view -> graph JSON
  -> comparison table.
- Write next-mission plan for frontend/deploy only after workflow evidence
  exists.

Suggested resume goal string:

```text
/goal In /Users/wiz/emf, execute the EMF workflow mission: integrate MikeOSS and
Fireworks DeepSeek-V4-Flash at medium reasoning effort, pull official Indian
financial filings for 3-5 companies, extract and normalize core statements into
cited JSON graphs, validate accounting/provenance constraints, and checkpoint
with evidence and next UI/deploy mission details.
```

## Deployment Posture

Deployment is not part of the first hard mission unless the workflow becomes
credible early.

Later deployment path:

- Use `go-choir` deployment knowledge and `node-a` as the target operator path.
- Deploy to a subdomain under `choir-ip.com`.
- Treat Cloudflare DNS as a separate operator task.
- Do not mutate Cloudflare or `node-a` until local artifacts are reproducible
  and secrets/rollback are explicitly handled.

Choir alignment:

- Choir already treats durable artifacts, traces, worker worlds, and deployed
  proof as first-class objects.
- EMF should produce durable run evidence: raw filing hashes, graph artifacts,
  logs, validation reports, provider/model config, and residual risks.
- If deployed through Choir infrastructure, proof should include health,
  commit/build identity, endpoint verification, and rollback handle.

## Risks

- Mike licensing: Mike is AGPL-3.0. Any modified network-deployed fork needs
  clean source availability and attribution handling.
- Source scraping fragility: NSE/BSE endpoints may require headers, cookies, or
  throttling. Use bounded, cached official pulls.
- PDF layout quality: annual reports often include complex tables, merged cells,
  decorative layouts, and scans.
- XBRL mismatch: XBRL result feeds may not cover all annual-report note detail
  and may have taxonomy/filing inconsistencies.
- Model overconfidence: long context lowers retrieval pain but does not remove
  numeric, sign, period, unit, and label errors.
- Cost illusion: the model is cheap, but repeated full-document calls across
  hundreds of companies can still waste time and money. Cache and chunk
  intelligently.

## Immediate Decisions For Iteration

- Submodule Mike or fork it directly inside `emf`?
- Use local filesystem/SQLite for first extraction run, or require Supabase/R2
  from the beginning?
- Initial company basket: large cross-sector set or narrow sector-first set?
- Graph schema strictness: minimal core statements only, or include segments
  and notes from the first run?
- Does the hackathon demo need Mike running live, or is a recorded workflow plus
  custom graph output enough for the first checkpoint?

## Sources

- MikeOSS website: https://mikeoss.com/
- Mike GitHub README: https://github.com/willchen96/mike
- Fireworks DeepSeek-V4-Flash model page:
  https://fireworks.ai/models/deepseek-ai/deepseek-v4-flash
- Fireworks serverless quickstart:
  https://docs.fireworks.ai/getting-started/quickstart
- Fireworks reasoning guide: https://docs.fireworks.ai/guides/reasoning
- NSE annual reports page:
  https://www.nseindia.com/companies-listing/corporate-filings-annual-reports
- NSE XBRL filing information:
  https://www.nseindia.com/static/companies-listing/xbrl-information
- XBRL India taxonomies:
  https://in.xbrl.org/about-us/xbrl-taxonomies/
- BSE historical annual reports:
  https://www.bseindia.com/corporates/HistoricalAnnualReport.aspx

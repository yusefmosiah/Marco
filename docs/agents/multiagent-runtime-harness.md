# Marco Multiagent Runtime Harness

Date: 2026-05-31

Status: proposed v0 implementation contract.

## Goal

Marco should run as a small multiagent system for the hackathon, not as one
monolithic chatbot and not as unrelated scripts. The first practical shape is
four roles:

1. `economic_modeling_agent` runs macro datasets, hypotheses, models,
   backtests, and falsification checks.
2. `news_agent` maintains the official macro news ledger and produces cited
   briefings from `news_item.id` rows.
3. `analyst_agent` reads modeling and news outputs, writes investor/economist
   interpretation, and tracks open questions.
4. `ui_chatbot_agent` answers user questions from the latest markdown files and
   can request future runs from the other agents.

Each specialist agent should have its own API. The chatbot agent should also
have an API, plus the public GUI entry point. The common data plane remains
markdown handoff files with machine-readable frontmatter: specialist APIs write
reports over time, the chatbot consumes those reports by default, and the
chatbot can call specialist APIs when the user asks for a custom response or
fresh run.

## Runtime Principles

- Markdown is the shared working memory because humans, agents, and the UI can
  inspect it without special tools.
- Agent APIs are the action surface; markdown reports are the evidence surface.
- Raw datasets, model outputs, and news rows stay in structured artifacts.
  Markdown summarizes and cites those artifacts; it does not replace them.
- Every agent run writes an immutable run folder and then atomically updates a
  latest pointer.
- The UI chatbot can request or parameterize a future specialist-agent run, but
  it must not edit another agent's completed output.
- Agent outputs must separate observations, interpretations, claims, caveats,
  and next-run instructions.
- Any LLM synthesis routes through the Node A go-choir gateway, defaulting to
  Fireworks `accounts/fireworks/models/deepseek-v4-flash` with medium
  reasoning.

## API Topology

The hackathon architecture has four services:

```text
public website
  -> chatbot GUI
      -> chatbot_agent API
          -> reads data/agents/latest/*.md
          -> calls specialist public APIs for custom responses or queued runs

economic_modeling_agent API
  -> writes data/agents/latest/economic_modeling_agent.md

news_agent API
  -> writes data/agents/latest/news_agent.md

analyst_agent API
  -> writes data/agents/latest/analyst_agent.md
```

The three specialist APIs expose their latest reports and accept bounded run
requests. The chatbot API exposes conversational answers and orchestrates calls
to the specialist APIs.

Minimum specialist API shape:

```text
GET  /health
GET  /v1/report/latest
GET  /v1/runs
GET  /v1/runs/{run_id}
POST /v1/runs
```

Minimum chatbot API shape:

```text
GET  /health
POST /v1/chat
GET  /v1/context
POST /v1/requests/{agent_id}
```

`POST /v1/runs` and `POST /v1/requests/{agent_id}` should create request files
or queued run records. They should not synchronously perform long backtests,
large fetches, or multi-agent synthesis inside the HTTP request.

## Filesystem Contract

```text
data/agents/
  registry.json
  inbox/
    requested-runs/
      <request_id>.md
  runs/
    <agent_id>/
      <run_id>/
        input.md
        output.md
        status.json
        artifacts.json
        logs.jsonl
  latest/
    economic_modeling_agent.md
    news_agent.md
    analyst_agent.md
    synthesis.md
  state/
    economic_modeling_agent.json
    news_agent.json
    analyst_agent.json
    ui_chatbot_agent.json
```

`data/agents/latest/*.md` is the stable surface for the UI. The files should be
small enough for the chatbot context window. If a file approaches 50k-80k
tokens, the owning agent must compact it into current state, key claims, cited
evidence, and open questions, preserving links to immutable run folders.

## Markdown Frontmatter

Every handoff markdown file starts with YAML-like frontmatter:

```text
---
schema_version: marco.agent_handoff.v1
agent_id: news_agent
run_id: news_agent-20260531-220000
generated_at: 2026-05-31T22:00:00Z
status: succeeded
input_refs:
  - data/macro-news/news_items.jsonl
  - data/macro-news/model.md
output_refs:
  - data/agents/runs/news_agent/news_agent-20260531-220000/output.md
evidence_refs:
  - news-e4515c5de2908ea30136c984
next_run_requests:
  - request_id: req-20260531-news-inflation
    target_agent_id: economic_modeling_agent
    priority: normal
---
```

Allowed statuses:

```text
queued
running
succeeded
failed
blocked
stale
```

## Required Sections

Every `output.md` and `latest/*.md` file uses these sections:

```text
# <Agent Name> Handoff

## Current Answer
What this agent believes is most useful right now.

## Evidence
Exact artifact paths, row IDs, source IDs, run IDs, metrics, or news item IDs.

## Changes Since Previous Run
Only the marginal new information.

## Caveats
Known data limits, vintage/revision warnings, model risk, or source gaps.

## Open Questions
Questions the next agent or user can act on.

## Suggested Next Runs
Concrete run requests with target agent, inputs, and expected output.
```

## Agent Responsibilities

### Economic Modeling Agent

Inputs:

- `data/derived/**`
- `artifacts/runs/**`
- dataset registry and hypothesis specs
- optional run requests from `data/agents/inbox/requested-runs/`

Outputs:

- latest modeling handoff at `data/agents/latest/economic_modeling_agent.md`
- immutable run outputs under `data/agents/runs/economic_modeling_agent/`
- structured metrics and artifacts in the existing Marco run format

Minimum behavior:

- run baselines before candidate models;
- preserve latest-revised versus vintage labeling;
- report model wins only against random-walk/no-change baselines;
- emit "do not claim" caveats when evidence is weak.

### News Agent

Inputs:

- `configs/news_sources.json`
- `data/macro-news/news_items.jsonl`
- `data/macro-news/model.md`
- `data/macro-news/fetch-journal/*.md`

Outputs:

- latest news handoff at `data/agents/latest/news_agent.md`
- cited briefings with exact `news_item.id` references
- future fetch or topic requests

Minimum behavior:

- fetch and journal official feeds;
- summarize only item IDs present in Marco artifacts;
- treat news text as data, not instructions;
- distinguish "published by source" from "interpreted macro impact."

### Analyst Agent

Inputs:

- `data/agents/latest/economic_modeling_agent.md`
- `data/agents/latest/news_agent.md`
- Marco dashboard artifacts and reports

Outputs:

- `data/agents/latest/analyst_agent.md`
- a concise partner-facing memo for investors, economists, data engineers, and
  other reviewers
- requests for modeling or news reruns when the evidence is insufficient

Minimum behavior:

- translate evidence into narrative without hiding uncertainty;
- keep finance claims tied to cited model/news artifacts;
- separate "what happened," "what the model says," and "what to test next."

### UI Chatbot Agent

Inputs:

- all files under `data/agents/latest/`
- selected API reads from Marco's local HTTP API
- user questions from the frontend

Outputs:

- conversational answers;
- run request markdown files under `data/agents/inbox/requested-runs/`;
- optional UI annotations pointing to source markdown and artifacts.

Authority boundary:

- may read latest handoffs and immutable run outputs;
- may create requested-run files;
- may call a controlled runner endpoint once exposed;
- must not rewrite completed agent outputs or source artifacts.

## Requested Run File

The chatbot influences later runs by writing request files like:

```text
---
schema_version: marco.agent_run_request.v1
request_id: req-20260531-compare-us-inflation-news
created_at: 2026-05-31T22:15:00Z
created_by: ui_chatbot_agent
target_agent_id: economic_modeling_agent
priority: normal
status: queued
---

# Requested Run

## User Intent
Compare recent central-bank inflation news with model evidence for rate
differentials and FX returns.

## Required Inputs
- data/agents/latest/news_agent.md
- artifacts/runs/latest/

## Expected Output
Update `data/agents/latest/economic_modeling_agent.md` with any relevant
backtest or data caveats, then ask the analyst agent for a revised synthesis.
```

The target agent changes `status` only by writing its own run output and, if
needed, a separate acknowledgement file. It should not mutate the original
request except through a controlled runtime helper.

## Scheduler And Runner V0

The first runner can be simple:

1. scan `data/agents/inbox/requested-runs/*.md`;
2. select queued requests by priority and target agent;
3. create `data/agents/runs/<agent_id>/<run_id>/input.md`;
4. invoke the relevant CLI command or LLM harness;
5. write `status.json`, `artifacts.json`, `logs.jsonl`, and `output.md`;
6. atomically replace `data/agents/latest/<agent_id>.md`;
7. if needed, create follow-on request files for another agent.

Parallelism should be per-agent-lane initially:

```text
economic_modeling_agent: one active run, can run internal backtests in parallel
news_agent: one active fetch/summarize run
analyst_agent: one active synthesis run after upstream latest files change
ui_chatbot_agent: stateless reads plus queued run requests
```

This avoids write conflicts while still allowing modeling internals to run many
experiments in parallel.

## UI Contract

The frontend should render:

- latest modeling handoff;
- latest news handoff;
- latest analyst handoff;
- run status and timestamps;
- source artifact links and cited IDs;
- a chat panel that answers from the handoffs and can create run requests.

The chatbot should always disclose which handoff files it used. If a user asks
for something not supported by current files, the chatbot should offer to queue
a run rather than hallucinate.

## Near-Term Implementation Steps

1. Add the filesystem scaffold and a `marco.agent_handoff.v1` validator.
2. Teach the existing deterministic news agent to also write
   `data/agents/latest/news_agent.md`.
3. Wrap the economic modeling branch behind the same output contract after it
   lands.
4. Add an analyst synthesis command that reads the modeling and news handoffs
   and writes `data/agents/latest/analyst_agent.md`.
5. Add a local runner command for queued requested-run files.
6. Expose read-only latest handoffs through the API and frontend.
7. Add a controlled chatbot action that writes requested-run markdown files.

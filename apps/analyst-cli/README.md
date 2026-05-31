# Marco Analyst CLI

Agentic RAG command-line wrapper for the `Analyst` agent using the OpenAI Codex
SDK.

The CLI retrieves relevant local Marco context, injects the
`agents/analyst.toml` instructions, and starts a Codex SDK thread from the repo
root. `run-ingestion` asks Codex for the Analyst JSON payload using a structured
output schema, runs local validation for approved domains, stable IDs, and
excerpt length, and writes a one-page summary report with an audit section.

## Install

From this directory, install the SDK as documented at
[developers.openai.com/codex/sdk](https://developers.openai.com/codex/sdk):

```sh
npm install
```

The secure project key is read from the repo root `.env.local` as
`OPENAI_API_KEY`.

## Commands

Preview retrieved context without calling Codex:

```sh
node ./bin/analyst-rag.js retrieve "financial news ingestion macro fed"
```

Ask the agent a question:

```sh
node ./bin/analyst-rag.js ask "How should the Analyst agent run today?"
```

Run the financial news ingestion agent:

```sh
node ./bin/analyst-rag.js run-ingestion \
  --root ../.. \
  --output output/analyst/financial-news-ingestion-latest.json
```

When `--output` is provided, the CLI also writes a Markdown report next to the
JSON using the `.summary.md` suffix. Override that path with
`--report-output path/to/report.md`.

Useful options:

```text
--topK 12
--model gpt-5.3-codex
--model-reasoning-effort medium
--network true
--webSearch true
--approvalPolicy never
--report-output output/analyst/financial-news-ingestion-latest.summary.md
--threadId <existing-codex-thread-id>
--corpus agents/analyst.toml,docs/agents,output/analyst
```

The same defaults can be supplied with environment variables:

```sh
export MARCO_CODEX_MODEL=gpt-5.4-mini
export MARCO_CODEX_REASONING_EFFORT=medium
```

For personal server deployment, install Node 18+, run `npm install` in this
directory, make sure the server has `OPENAI_API_KEY` in the environment or repo
`.env.local`, and run the command from the Marco checkout. The Codex CLI also
needs a writable home directory for its local state.

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { buildPrompt, buildSummaryReport, retrieveContext, validateAnalystPayload } from "../bin/analyst-rag.js";

describe("retrieveContext", () => {
  it("retrieves relevant analyst context from a local corpus", () => {
    const root = mkdtempSync(join(tmpdir(), "marco-analyst-"));
    mkdirSync(join(root, "agents"), { recursive: true });
    mkdirSync(join(root, "docs"), { recursive: true });
    writeFileSync(join(root, "agents", "analyst.toml"), "name = \"Analyst\"\ncrypto macro equities\n", "utf8");
    writeFileSync(join(root, "docs", "note.md"), "global macro panel and random walk baseline\n", "utf8");

    const result = retrieveContext("analyst crypto news", {
      root,
      corpusPaths: ["agents", "docs"],
      topK: 1,
    });

    assert.equal(result.length, 1);
    assert.equal(result[0].path, "agents/analyst.toml");
  });
});

describe("buildPrompt", () => {
  it("includes analyst configuration, retrieved sources, and the task", () => {
    const prompt = buildPrompt({
      analystConfig: "name = \"Analyst\"",
      contextChunks: [{ path: "agents/analyst.toml", index: 0, hash: "abc", text: "approved sources" }],
      task: "Run ingestion",
      today: new Date("2026-05-31T00:00:00Z"),
    });

    assert.match(prompt, /Analyst Agent Configuration/);
    assert.match(prompt, /Retrieved Source 1/);
    assert.match(prompt, /Run ingestion/);
  });
});

describe("validateAnalystPayload", () => {
  it("accepts a valid empty payload", () => {
    const errors = validateAnalystPayload({
      agent_id: "financial-news-ingestion-v1",
      generated_at: "2026-05-31T00:00:00Z",
      window_start: "2026-05-17T00:00:00Z",
      window_end: "2026-05-31T23:59:59Z",
      article_count: 0,
      retrieval_errors: [],
      articles: [],
    });

    assert.deepEqual(errors, []);
  });

  it("rejects unapproved source domains", () => {
    const errors = validateAnalystPayload({
      agent_id: "financial-news-ingestion-v1",
      generated_at: "2026-05-31T00:00:00Z",
      window_start: "2026-05-17T00:00:00Z",
      window_end: "2026-05-31T23:59:59Z",
      article_count: 1,
      retrieval_errors: [],
      articles: [
        {
          article_id: "6a0ee41e755e42d0",
          event_cluster_id: "7a38b94bfbfab7aa",
          domain: "equities",
          source_name: "Example",
          source_url: "https://example.com/story",
          syndication_origin: null,
          published_at: "2026-05-31T00:00:00Z",
          retrieved_at: "2026-05-31T00:01:00Z",
          retrieval_status: "success",
          headline: "Stocks rise",
          summary: null,
          body_excerpt: "Stocks rise.",
          tickers_mentioned: [],
          assets_mentioned: [],
          named_entities: { organizations: [], people: [], geographies: [] },
          is_primary_source: false,
        },
      ],
    });

    assert.ok(errors.some((error) => error.includes("approved source")));
  });
});

describe("buildSummaryReport", () => {
  it("builds a one-page report with an audit section", () => {
    const report = buildSummaryReport(
      {
        agent_id: "financial-news-ingestion-v1",
        generated_at: "2026-05-31T00:00:00Z",
        window_start: "2026-05-17T00:00:00Z",
        window_end: "2026-05-31T23:59:59Z",
        article_count: 0,
        retrieval_errors: [{ source: "reuters.com", reason: "no_results", http_status: null }],
        articles: [],
      },
      { contextChunks: [{ path: "agents/analyst.toml", index: 0 }] },
    );

    assert.match(report, /# Analyst Ingestion Summary/);
    assert.match(report, /## Audit/);
    assert.match(report, /reuters\.com:no_results 1/);
    assert.match(report, /agents\/analyst\.toml#chunk-0/);
  });
});

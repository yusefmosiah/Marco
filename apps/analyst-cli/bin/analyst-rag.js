#!/usr/bin/env node
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, extname, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DEFAULT_ROOT = resolve(__dirname, "../../..");
const MAX_FILE_BYTES = 260_000;
const DEFAULT_TOP_K = 8;
const DEFAULT_CHUNK_CHARS = 3_000;
const CHUNK_OVERLAP_CHARS = 350;
const DEFAULT_CODEX_MODEL = process.env.MARCO_CODEX_MODEL;
const DEFAULT_CODEX_REASONING_EFFORT = process.env.MARCO_CODEX_REASONING_EFFORT ?? "medium";

const APPROVED_SOURCES = [
  "reuters.com",
  "apnews.com",
  "bloomberg.com",
  "wsj.com",
  "ft.com",
  "sec.gov",
  "fred.stlouisfed.org",
  "federalreserve.gov",
  "seekingalpha.com",
  "benzinga.com",
];

const DEFAULT_CORPUS = [
  "agents/analyst.toml",
  "README.md",
  "docs/agents",
  "docs/strategy",
  "docs/runs",
  "skills/marco-agent-api",
  "artifacts/fred-fx-rate-lab",
  "artifacts/global-macro-panel",
  "output/analyst",
  "configs",
];

const TEXT_EXTENSIONS = new Set([
  ".csv",
  ".json",
  ".jsonl",
  ".md",
  ".toml",
  ".txt",
  ".yaml",
  ".yml",
]);

export const ANALYST_OUTPUT_SCHEMA = {
  type: "object",
  properties: {
    agent_id: { type: "string", const: "financial-news-ingestion-v1" },
    generated_at: { type: "string" },
    window_start: { type: "string" },
    window_end: { type: "string" },
    article_count: { type: "integer" },
    retrieval_errors: {
      type: "array",
      items: {
        type: "object",
        properties: {
          source: { type: "string" },
          reason: {
            type: "string",
            enum: ["paywall", "http_error", "timeout", "no_results", "unparseable_date"],
          },
          http_status: { anyOf: [{ type: "integer" }, { type: "null" }] },
        },
        required: ["source", "reason", "http_status"],
        additionalProperties: false,
      },
    },
    articles: {
      type: "array",
      items: {
        type: "object",
        properties: {
          article_id: { type: "string" },
          event_cluster_id: { type: "string" },
          domain: { type: "string", enum: ["equities", "macro_fed", "crypto", "commodities_forex"] },
          source_name: { type: "string" },
          source_url: { type: "string" },
          syndication_origin: { anyOf: [{ type: "string" }, { type: "null" }] },
          published_at: { type: "string" },
          retrieved_at: { type: "string" },
          retrieval_status: { type: "string", enum: ["success", "failed"] },
          headline: { type: "string" },
          summary: { anyOf: [{ type: "string" }, { type: "null" }] },
          body_excerpt: { anyOf: [{ type: "string" }, { type: "null" }] },
          tickers_mentioned: { type: "array", items: { type: "string" } },
          assets_mentioned: { type: "array", items: { type: "string" } },
          named_entities: {
            type: "object",
            properties: {
              organizations: { type: "array", items: { type: "string" } },
              people: { type: "array", items: { type: "string" } },
              geographies: { type: "array", items: { type: "string" } },
            },
            required: ["organizations", "people", "geographies"],
            additionalProperties: false,
          },
          is_primary_source: { type: "boolean" },
        },
        required: [
          "article_id",
          "event_cluster_id",
          "domain",
          "source_name",
          "source_url",
          "syndication_origin",
          "published_at",
          "retrieved_at",
          "retrieval_status",
          "headline",
          "summary",
          "body_excerpt",
          "tickers_mentioned",
          "assets_mentioned",
          "named_entities",
          "is_primary_source",
        ],
        additionalProperties: false,
      },
    },
  },
  required: ["agent_id", "generated_at", "window_start", "window_end", "article_count", "retrieval_errors", "articles"],
  additionalProperties: false,
};

export function loadDotenv(root = DEFAULT_ROOT) {
  const loaded = {};
  for (const name of [".env.local", ".env"]) {
    const path = resolve(root, name);
    if (!existsSync(path)) continue;
    for (const line of readFileSync(path, "utf8").split(/\r?\n/)) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) continue;
      const index = trimmed.indexOf("=");
      const key = trimmed.slice(0, index).trim();
      let value = trimmed.slice(index + 1).trim();
      if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
      if (key && process.env[key] === undefined) {
        process.env[key] = value;
        loaded[key] = name;
      }
    }
  }
  return loaded;
}

export function discoverCorpusFiles(root = DEFAULT_ROOT, corpusPaths = DEFAULT_CORPUS) {
  const files = [];
  const seen = new Set();
  for (const corpusPath of corpusPaths) {
    const absolute = resolve(root, corpusPath);
    collectTextFiles(root, absolute, files, seen);
  }
  return files.sort();
}

export function retrieveContext(query, options = {}) {
  const root = options.root ? resolve(options.root) : DEFAULT_ROOT;
  const topK = options.topK ?? DEFAULT_TOP_K;
  const chunkChars = options.chunkChars ?? DEFAULT_CHUNK_CHARS;
  const corpusPaths = options.corpusPaths?.length ? options.corpusPaths : DEFAULT_CORPUS;
  const files = discoverCorpusFiles(root, corpusPaths);
  const chunks = [];
  for (const file of files) {
    const absolute = resolve(root, file);
    const text = readFileSync(absolute, "utf8");
    for (const chunk of chunkText(text, chunkChars, CHUNK_OVERLAP_CHARS)) {
      chunks.push({ path: file, text: chunk.text, index: chunk.index, hash: shortHash(`${file}:${chunk.index}:${chunk.text}`) });
    }
  }
  const terms = tokenize(query);
  return chunks
    .map((chunk) => ({ ...chunk, score: scoreChunk(chunk, terms) }))
    .filter((chunk) => chunk.score > 0)
    .sort((a, b) => b.score - a.score || a.path.localeCompare(b.path))
    .slice(0, topK);
}

export function buildPrompt({ analystConfig, contextChunks, task, today = new Date() }) {
  const sourceBlock = contextChunks
    .map((chunk, index) => {
      return `### Retrieved Source ${index + 1}: ${chunk.path}#chunk-${chunk.index} (${chunk.hash})\n${chunk.text.trim()}`;
    })
    .join("\n\n");

  return [
    "You are running the Marco Analyst agent through a Codex SDK-powered CLI.",
    "",
    "Use the Analyst configuration as the controlling instruction set. Use retrieved Marco context as RAG evidence. You may inspect the repository and, for news ingestion, retrieve only approved external sources named by the Analyst configuration.",
    "",
    `Current date: ${today.toISOString().slice(0, 10)}`,
    "",
    "## Analyst Agent Configuration",
    analystConfig.trim(),
    "",
    "## Retrieved Marco Context",
    sourceBlock || "No local context matched the query.",
    "",
    "## User Task",
    task.trim(),
  ].join("\n");
}

export function validateAnalystPayload(payload) {
  const errors = [];
  if (payload?.agent_id !== "financial-news-ingestion-v1") {
    errors.push("agent_id must be financial-news-ingestion-v1");
  }
  if (!Array.isArray(payload?.articles)) {
    errors.push("articles must be an array");
    return errors;
  }
  if (payload.article_count !== payload.articles.length) {
    errors.push("article_count must equal articles.length");
  }
  for (const [index, article] of payload.articles.entries()) {
    try {
      const url = new URL(article.source_url);
      if (!APPROVED_SOURCES.some((domain) => url.hostname === domain || url.hostname.endsWith(`.${domain}`))) {
        errors.push(`articles[${index}].source_url is not on the approved source list`);
      }
    } catch {
      errors.push(`articles[${index}].source_url is not a valid URL`);
    }
    if (article.body_excerpt && article.body_excerpt.length > 500) {
      errors.push(`articles[${index}].body_excerpt exceeds 500 characters`);
    }
    const expectedArticleId = shortHash(article.source_url);
    if (article.article_id !== expectedArticleId) {
      errors.push(`articles[${index}].article_id should be ${expectedArticleId}`);
    }
    const expectedClusterId = shortHash(String(article.headline ?? "").toLowerCase().replace(/\s+/g, " ").trim());
    if (article.event_cluster_id !== expectedClusterId) {
      errors.push(`articles[${index}].event_cluster_id should be ${expectedClusterId}`);
    }
  }
  return errors;
}

export function buildSummaryReport(payload, options = {}) {
  const articles = Array.isArray(payload.articles) ? payload.articles : [];
  const retrievalErrors = Array.isArray(payload.retrieval_errors) ? payload.retrieval_errors : [];
  const domainCounts = countBy(articles, (article) => article.domain || "unknown");
  const sourceCounts = countBy(articles, (article) => article.source_name || hostname(article.source_url) || "unknown");
  const errorCounts = countBy(retrievalErrors, (error) => `${error.source || "unknown"}:${error.reason || "unknown"}`);
  const contextChunks = options.contextChunks ?? [];

  return [
    "# Analyst Ingestion Summary",
    "",
    `Generated: ${payload.generated_at ?? "unknown"}`,
    `Window: ${payload.window_start ?? "unknown"} to ${payload.window_end ?? "unknown"}`,
    `Payload: ${payload.article_count ?? articles.length} articles, ${retrievalErrors.length} retrieval errors.`,
    "",
    "## Coverage",
    "",
    `Domains: ${formatCounts(domainCounts) || "none"}.`,
    `Sources: ${formatCounts(sourceCounts) || "none"}.`,
    "",
    "## Audit",
    "",
    `The agent used the Analyst approved-source policy and rejected URLs outside: ${APPROVED_SOURCES.join(", ")}.`,
    "Included records had to be on an approved domain, fall inside the 14-day UTC window, expose a parseable publication timestamp, and carry the required schema fields.",
    "Excluded or downgraded records included stale articles, unapproved domains, unverified source URLs, unparseable dates, malformed records, and article bodies unavailable because of paywalls or HTTP failures.",
    `Validation checked article count consistency, approved source domains, deterministic article IDs, deterministic event cluster IDs, and body excerpts at or under 500 characters.`,
    `Retrieval errors: ${formatCounts(errorCounts) || "none"}.`,
    `Local RAG context: ${contextChunks.map((chunk) => `${chunk.path}#chunk-${chunk.index}`).join(", ") || "none"}.`,
    "",
    "## Handoff",
    "",
    "The JSON payload remains the machine-readable handoff for sentiment scoring. This report is a human audit companion and does not add sentiment, recommendations, or predictions.",
  ].join("\n") + "\n";
}

async function main(argv = process.argv.slice(2)) {
  const command = argv[0] ?? "help";
  if (command === "help" || command === "--help" || command === "-h") {
    printHelp();
    return;
  }

  const args = parseArgs(argv.slice(1));
  const root = resolve(args.root ?? DEFAULT_ROOT);
  loadDotenv(root);

  if (command === "retrieve") {
    const query = args._.join(" ") || args.query || "financial news ingestion analyst";
    const context = retrieveContext(query, {
      root,
      topK: Number(args.topK ?? DEFAULT_TOP_K),
      corpusPaths: toList(args.corpus),
    });
    console.log(JSON.stringify({ query, context }, null, 2));
    return;
  }

  if (command !== "ask" && command !== "run-ingestion") {
    throw new Error(`Unknown command: ${command}`);
  }

  const { Codex } = await import("@openai/codex-sdk");
  const task = buildTask(command, args);
  const analystConfig = readFileSync(resolve(root, args.agent ?? "agents/analyst.toml"), "utf8");
  const contextChunks = retrieveContext(task, {
    root,
    topK: Number(args.topK ?? DEFAULT_TOP_K),
    corpusPaths: toList(args.corpus),
  });
  const prompt = buildPrompt({ analystConfig, contextChunks, task });
  const codex = new Codex();
  const threadOptions = {
    workingDirectory: root,
    skipGitRepoCheck: args.skipGitRepoCheck === "true",
    sandboxMode: args.sandbox ?? "workspace-write",
    networkAccessEnabled: args.network !== "false",
    webSearchEnabled: args.webSearch === "true" ? true : args.webSearch === "false" ? false : undefined,
    approvalPolicy: args.approvalPolicy,
  };
  const model = args.model ?? DEFAULT_CODEX_MODEL;
  const modelReasoningEffort = args.modelReasoningEffort ?? args["model-reasoning-effort"] ?? args.reasoningEffort ?? args["reasoning-effort"] ?? DEFAULT_CODEX_REASONING_EFFORT;
  if (model) {
    threadOptions.model = model;
  }
  if (modelReasoningEffort) {
    threadOptions.modelReasoningEffort = modelReasoningEffort;
  }
  const thread = args.threadId ? codex.resumeThread(args.threadId, threadOptions) : codex.startThread(threadOptions);
  const turnOptions = command === "run-ingestion" ? { outputSchema: ANALYST_OUTPUT_SCHEMA } : {};
  const turn = await thread.run(prompt, turnOptions);
  let finalResponse = turn.finalResponse ?? "";

  if (command === "run-ingestion") {
    const payload = parseJsonResponse(finalResponse);
    const validationErrors = validateAnalystPayload(payload);
    if (validationErrors.length) {
      throw new Error(`Analyst payload failed local validation:\n${validationErrors.join("\n")}`);
    }
    finalResponse = JSON.stringify(payload, null, 2);
    const reportOutput = args.reportOutput ?? args["report-output"] ?? (args.output ? defaultReportPath(args.output) : undefined);
    if (reportOutput) {
      writeTextFile(resolve(root, reportOutput), buildSummaryReport(payload, { contextChunks, task }));
    }
  }

  if (args.output) {
    writeTextFile(resolve(root, args.output), finalResponse.endsWith("\n") ? finalResponse : `${finalResponse}\n`);
  } else {
    console.log(finalResponse);
  }
}

function buildTask(command, args) {
  if (args.prompt) return args.prompt;
  if (args._.length) return args._.join(" ");
  if (command === "run-ingestion") {
    return "Collect, structure, validate, and emit the financial-news-ingestion-v1 JSON payload for the current 14 calendar day window.";
  }
  throw new Error("Provide a prompt after the command, or pass --prompt.");
}

function collectTextFiles(root, absolute, files, seen) {
  if (!existsSync(absolute)) return;
  const stats = statSync(absolute);
  if (stats.isDirectory()) {
    for (const name of readdirSync(absolute)) {
      if (name === "node_modules" || name === ".git" || name.startsWith(".env")) continue;
      collectTextFiles(root, resolve(absolute, name), files, seen);
    }
    return;
  }
  if (!stats.isFile() || stats.size > MAX_FILE_BYTES || !TEXT_EXTENSIONS.has(extensionOf(absolute))) return;
  const rel = relative(root, absolute);
  if (!seen.has(rel)) {
    seen.add(rel);
    files.push(rel);
  }
}

function chunkText(text, maxChars, overlapChars) {
  const chunks = [];
  let offset = 0;
  while (offset < text.length) {
    const end = Math.min(offset + maxChars, text.length);
    chunks.push({ index: chunks.length, text: text.slice(offset, end) });
    if (end === text.length) break;
    offset = Math.max(0, end - overlapChars);
  }
  return chunks;
}

function scoreChunk(chunk, terms) {
  const textTerms = tokenize(`${chunk.path} ${chunk.text}`);
  if (!terms.size || !textTerms.size) return 0;
  let score = 0;
  for (const term of terms) {
    if (textTerms.has(term)) score += term.length > 4 ? 2 : 1;
  }
  if (chunk.path.includes("agents/analyst.toml")) score += 8;
  if (chunk.path.includes("output/analyst")) score += 3;
  return score;
}

function tokenize(text) {
  const terms = new Set();
  for (const match of String(text).toLowerCase().matchAll(/[a-z0-9][a-z0-9_-]{2,}/g)) {
    terms.add(match[0]);
  }
  return terms;
}

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const value = argv[i];
    if (!value.startsWith("--")) {
      args._.push(value);
      continue;
    }
    const key = value.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      args[key] = "true";
    } else {
      args[key] = next;
      i += 1;
    }
  }
  return args;
}

function toList(value) {
  if (!value) return undefined;
  return String(value)
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function countBy(rows, getKey) {
  const counts = new Map();
  for (const row of rows) {
    const key = getKey(row);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return counts;
}

function formatCounts(counts) {
  return Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(([key, count]) => `${key} ${count}`)
    .join(", ");
}

function hostname(value) {
  try {
    return new URL(value).hostname;
  } catch {
    return "";
  }
}

function defaultReportPath(outputPath) {
  const extension = extname(outputPath);
  if (!extension) return `${outputPath}.summary.md`;
  return `${outputPath.slice(0, -extension.length)}.summary.md`;
}

function writeTextFile(path, text) {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, text, "utf8");
}

function parseJsonResponse(text) {
  try {
    return JSON.parse(text);
  } catch {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}");
    if (start === -1 || end === -1 || end <= start) throw new Error("Codex response did not contain JSON");
    return JSON.parse(text.slice(start, end + 1));
  }
}

function extensionOf(path) {
  const index = path.lastIndexOf(".");
  return index === -1 ? "" : path.slice(index);
}

function shortHash(value) {
  return createHash("sha256").update(value).digest("hex").slice(0, 16);
}

function printHelp() {
  console.log(`Marco Analyst Codex SDK CLI

Usage:
  marco-analyst retrieve [query] [--root .] [--topK 8]
  marco-analyst ask "Question or task" [--root .] [--output out.txt]
  marco-analyst run-ingestion [--root .] [--output output/analyst/run.json]

Options:
  --agent <path>          Analyst TOML path, default agents/analyst.toml
  --corpus <a,b,c>        Comma-separated corpus roots/files
  --model <model>         Codex model override; defaults to Codex CLI config
  --model-reasoning-effort <effort> Reasoning effort, default ${DEFAULT_CODEX_REASONING_EFFORT}
  --network <true|false>  Enable Codex CLI network access, default true
  --webSearch <true|false> Enable or disable Codex web search
  --approvalPolicy <mode> Codex approval policy override
  --report-output <path>  Summary report path; defaults to output basename .summary.md
  --threadId <id>         Resume an existing Codex thread
  --topK <n>              Retrieved context chunk count, default ${DEFAULT_TOP_K}
`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error(error.message);
    process.exit(1);
  });
}

# Marco

Marco is a multi-agent macroeconomic research and forecasting platform. The goal is to help users understand the economy by combining official macro data, central-bank communications, and news evidence through specialized agents.

Marco has three core agents:

1. **Economic News Agent**  
   Collects and analyzes macro news, central-bank communications, speeches, minutes, and official releases to extract economic sentiment, including inflation tone, growth tone, labor-market tone, and policy-rate tone.

2. **Economic Model Agent**  
   Uses FRED/FRED-MD and other official macro datasets to forecast key economic variables such as interest rates, inflation, and growth. It compares models including baselines, VAR, linear top-factor models, XGBoost, and planned Chronos-2 zero-shot forecasting.

3. **Economic Synthesis Agent**  
   Combines the news sentiment, model forecasts, source evidence, and caveats into a coherent macroeconomic view that can answer questions like: “What do recent Fed communications and economic data imply about the path of interest rates?”

The current implementation focuses on building reliable source ingestion, provenance, model-ready macro panels, backtests, forecast artifacts, and agent-readable JSON outputs. Marco stores all major outputs as inspectable artifacts, including CSV, JSON, JSONL, Parquet, Markdown reports, and SVG forecast plots.

Current data surfaces include:

- FRED/FRED-MD macro data
- Fed FOMC communications
- Official macro news feeds
- ECB SDMX data
- World Bank indicators
- Global macro panels
- Backtest and forecast artifacts

The immediate roadmap is to strengthen the two specialist agents: the Economic News Agent and the Economic Model Agent. Once both are stable, Marco will add the synthesis layer that pulls them together into sourced, evidence-backed economic research answers.

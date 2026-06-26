# Trading And Market Agents

This section is for research, market analysis, paper trading, portfolio experiments, and agent engineering. It is not financial advice. Do not connect live order execution to an agent until permissions, audit logs, broker rules, risk controls, and compliance are reviewed.

For quantum-assisted stock, investing, day-trading, and risk-gated plugin work, use [quantum/QUANTUM-TRADING.md](../quantum/QUANTUM-TRADING.md).

For Robinhood and other broker app integrations, use [docs/BROKER-APP-INTEGRATIONS.md](BROKER-APP-INTEGRATIONS.md).

For agents that try to automate day-trading signals, paper orders, and investing allocations, use [docs/AUTONOMOUS-DAY-TRADING.md](AUTONOMOUS-DAY-TRADING.md). It is paper-first and cannot promise profit.

![Autonomous day-trading agent flow](../assets/day-trading-agent-flow.svg)

## Flow

```text
Market data, filings, news, watchlists, broker data
  -> data adapters
  -> RAG and market analysis agents
  -> backtest or paper-trade simulator
  -> risk and cost review
  -> human decision
```

## Standalone Robinhood Lane

| Repo or docs | Use it when | Note | Status |
| --- | --- | --- | --- |
| [jmfernandes/robin_stocks](https://github.com/jmfernandes/robin_stocks) | You want a Python library that can interact with Robinhood account, portfolio, stocks, options, and crypto data. | Community library; be careful with credentials and live orders. | experimental |
| [siropkin/robinhood-ai-trading-bot](https://github.com/siropkin/robinhood-ai-trading-bot) | You want a small AI-powered Robinhood bot example to study. | Treat as educational, not production. | experimental |
| [Robinhood Crypto API docs](https://docs.robinhood.com/crypto/trading/) | You want official Robinhood crypto trading API reference. | Prefer official APIs where available. | active |
| [agents/broker-connect.md](../agents/broker-connect.md) | You want a dedicated broker-connect agent with Iris monitoring and paper-mode safety. | Replaces robinhood-research example for agent-based workflows. | active |

## Stock And Market Analysis Repos

| Repo | Use it when | Connects to | Status |
| --- | --- | --- | --- |
| [OpenBB-finance/OpenBB](https://github.com/OpenBB-finance/OpenBB) | You need a financial data platform for analysts, quants, and AI agents. | RAG, Copilot Studio API bridge, notebooks. | active |
| [ai4finance-foundation/finrobot](https://github.com/ai4finance-foundation/finrobot) | You want financial analysis agents using LLMs. | Market research agents and report generation. | active |
| [AI4Finance-Foundation/FinGPT](https://github.com/AI4Finance-Foundation/FinGPT) | You want financial LLM research and models. | Domain language models and sentiment/research tasks. | active |
| [LIU-HONGYANG-GZU/Live_Trade_Bench](https://github.com/LIU-HONGYANG-GZU/Live_Trade_Bench) | You want a benchmark for LLM financial trading agents. | Evaluate before automation. | experimental |
| [ranaroussi/yfinance](https://github.com/ranaroussi/yfinance) | You want quick Yahoo Finance data access from Python. | Prototypes, notebooks, research. | active |
| [matplotlib/mplfinance](https://github.com/matplotlib/mplfinance) | You want financial charting. | Reports, dashboards, pitch demos. | active |
| [xgboosted/pandas-ta-classic](https://github.com/xgboosted/pandas-ta-classic) | You want technical analysis indicators in pandas. | Backtests and market feature pipelines. | experimental |
| [bukosabino/ta](https://github.com/bukosabino/ta) | You want another technical-analysis library. | Feature engineering for agents and models. | stale |
| [georgezouq/awesome-ai-in-finance](https://github.com/georgezouq/awesome-ai-in-finance) | You want a broader AI-in-finance discovery list. | Research queue. | active |

## Trading Agent And Backtesting Repos

| Repo | Use it when | Connects to | Status |
| --- | --- | --- | --- |
| [tauricresearch/tradingagents](https://github.com/tauricresearch/tradingagents) | You want a multi-agent LLM financial trading framework. | Research agents, market debates, analysis workflows. | active |
| [HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) | You want agentic trading experiments around Robinhood Agentic Trading/MCP ideas. | Research and paper mode. | experimental |
| [TradingAgents-AI/TradingAgents](https://github.com/TradingAgents-AI/TradingAgents) | You want another TradingAgents implementation to compare. | Research and paper mode. | experimental |
| [HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader) | You want an agent-native automated trading research repo. | Research and paper-trading architecture. | experimental |
| [MingyuJ666/Stockagent](https://github.com/MingyuJ666/Stockagent) | You want stock trading in simulated real-world environments. | Backtesting and simulated trading. | experimental |
| [AI4Finance-Foundation/FinRL](https://github.com/AI4Finance-Foundation/FinRL) | You want financial reinforcement learning. | Training, simulation, portfolio experiments. | active |
| [quantconnect/Lean](https://github.com/quantconnect/Lean) | You want an algorithmic trading engine for backtesting/live research. | Backtests, strategy research, paper trading. | active |
| [mementum/backtrader](https://github.com/mementum/backtrader) | You want classic Python backtesting. | Historical strategy tests. | stale |
| [freqtrade/freqtrade](https://github.com/freqtrade/freqtrade) | You want crypto trading bot/backtesting tooling. | Crypto research and paper trading. | active |

## Day Trading And Broker Tooling

| Repo | Use it when | Default |
| --- | --- | --- |
| [plugins/autonomous-day-trading-agent](../plugins/autonomous-day-trading-agent/README.md) | You want this repo's standalone day-trading/investing automation scaffold. | Signals, backtests, invest-plan, paper orders; live blocked. |
| [alpacahq/alpaca-py](https://github.com/alpacahq/alpaca-py) | You want Alpaca's current Python SDK. | Paper account first. |
| [alpacahq/alpaca-mcp-server](https://github.com/alpacahq/alpaca-mcp-server) | You want broker tools exposed through MCP. | Paper tools only until audited. |
| [Lumiwealth/lumibot](https://github.com/Lumiwealth/lumibot) | You want backtesting and broker integrations. | Backtest and paper trade. |
| [nautechsystems/nautilus_trader](https://github.com/nautechsystems/nautilus_trader) | You want a more advanced trading engine. | Research and simulation first. |
| [kernc/backtesting.py](https://github.com/kernc/backtesting.py) | You want simple backtests. | Good first baseline. |
| [marcozanetti-dev/intraday-mean-reversion-costs-aware](https://github.com/marcozanetti-dev/intraday-mean-reversion-costs-aware) | You want cost-aware intraday strategy research. | Research only. |

## Quantum Trading Plugin

The starter scaffold at [plugins/quantum-trading-agent](../plugins/quantum-trading-agent/README.md) provides:

- Risk-gated trade proposals.
- Paper-order mode.
- Live-order blocking by default.
- Quantum optimizer placeholder.
- Training plan for ML, RL, QML, and LLM trading workflows.

## Robinhood And Broker App Plugin

The starter scaffold at [plugins/robinhood-trading-agent](../plugins/robinhood-trading-agent/README.md) provides:

- Robinhood Crypto dry-run adapter shape.
- Community Robinhood route blocker for stocks/options.
- Broker-style risk gates.
- Paper broker.
- Live order blocking by default.
- Training plan for LLM/ML day-trading workflows.

## Autonomous Day-Trading Plugin

The starter scaffold at [plugins/autonomous-day-trading-agent](../plugins/autonomous-day-trading-agent/README.md) provides:

- Moving-average signal generation from CSV bars.
- Toy backtest output.
- Risk-gated paper orders.
- Equal-weight investing allocation proposals.
- Live-order blocking by default.
- Training plan for ML, RL, LLM, and QML day-trading workflows.

## Integration Combos

| Combo | What it gives you |
| --- | --- |
| OpenBB + RAG | Market-data-backed research assistant. |
| FinRobot + Copilot Studio | Business-facing financial analysis agent through an API bridge. |
| TradingAgents + memory | Persistent notes about strategy assumptions and research results. |
| Autonomous day-trading plugin + Alpaca paper | Signals and paper orders behind deterministic risk gates. |
| Vibe-Trading + Robinhood Agentic Trading | Study agent-to-broker design, then keep execution gated. |
| yfinance + mplfinance + Slidev | Fast market analysis deck. |
| FinRL + quantum optimization | Compare classical RL against quantum-inspired portfolio experiments. |
| Robinhood research prompt + MCP filesystem | Local research notes and watchlists without live order execution. |
| Alpaca MCP + quantum trading plugin | Use paper Alpaca tools behind deterministic risk gates. |
| Robinhood trading plugin + risk gate | Use AI proposals with paper orders and blocked live execution. |

## One-Liners

Clone finance/trading repos, PowerShell:

```powershell
$MasterRepo = (Get-Location).Path  # run from repo root; $LanePath = Read-Host "Folder where finance/trading repos should be cloned"; New-Item -ItemType Directory -Force $LanePath | Out-Null; Get-Content (Join-Path $MasterRepo "repo-lists\finance-trading-market.txt") | Where-Object { $_ -and $_ -notmatch '^#' } | ForEach-Object { gh repo clone $_ (Join-Path $LanePath ($_ -replace '/','-')) }
```

Clone finance/trading repos, WSL/Bash:

```bash
read -rp "Path to Master-Repo-Use: " master_repo; read -rp "Folder where finance/trading repos should be cloned: " lane_path; mkdir -p "$lane_path"; grep -vE '^(#|$)' "$master_repo/repo-lists/finance-trading-market.txt" | while read -r repo; do gh repo clone "$repo" "$lane_path/${repo/\//-}"; done
```

Install common Python research packages:

```powershell
python -m pip install --user openbb yfinance mplfinance ta pandas numpy
```

Install with WSL/Bash:

```bash
python3 -m pip install --user openbb yfinance mplfinance ta pandas numpy
```

Start a paper-trading lab folder:

```powershell
$MarketLab = Read-Host "Where should the standalone market lab live?"; New-Item -ItemType Directory -Force $MarketLab | Out-Null; Set-Location $MarketLab
```

## Safety Defaults

- Start with read-only market data.
- Use paper trading before broker execution.
- Keep broker credentials out of repos.
- Add manual approval for every order.
- Log prompts, data sources, decisions, and tool calls.
- Compare agent output against a simple baseline.
- Never let a model place live trades only because a prompt says so.

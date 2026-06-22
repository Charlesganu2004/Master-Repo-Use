# Autonomous Day-Trading Agent Plugin

This is a paper-first scaffold for a day-trading and investing agent. It can generate strategy signals, evaluate risk, create paper orders, and propose simple investment allocations.

It cannot guarantee profit. Live trading is intentionally blocked in this scaffold.

## Flow

```text
market data
  -> strategy signal
  -> backtest check
  -> deterministic risk gate
  -> paper broker
  -> audit output
  -> human approval before any live adapter
```

## Files

```text
plugins/autonomous-day-trading-agent/
|-- README.md
|-- plugin.json
|-- pyproject.toml
|-- risk_limits.example.json
|-- training_plan.md
`-- src/autonomous_day_trading_agent/
    |-- __init__.py
    |-- broker.py
    |-- cli.py
    |-- config.py
    |-- risk.py
    `-- strategy.py
```

## Standalone Setup

PowerShell:

```powershell
$PluginPath = Read-Host "Path to plugins\autonomous-day-trading-agent"; Set-Location $PluginPath; python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install --upgrade pip; python -m pip install -e .
```

WSL/Bash:

```bash
read -rp "Path to plugins/autonomous-day-trading-agent: " plugin_path; cd "$plugin_path"; python3 -m venv .venv && source .venv/bin/activate && python -m pip install --upgrade pip && python -m pip install -e .
```

## Smoke Test

```powershell
autonomous-day-trading-agent smoke-test --risk risk_limits.example.json
```

## Propose A Trade

```powershell
autonomous-day-trading-agent propose --symbol SPY --side buy --quantity 1 --price 500 --asset-type etf --risk risk_limits.example.json
```

## Paper Order

```powershell
autonomous-day-trading-agent paper-order --symbol SPY --side buy --quantity 1 --price 500 --asset-type etf --risk risk_limits.example.json
```

## Strategy Signal From CSV Bars

Create a CSV with `timestamp,open,high,low,close,volume` columns, then run:

```powershell
autonomous-day-trading-agent strategy-signal --bars .\bars.csv --symbol SPY --quantity 1 --risk risk_limits.example.json
```

## Backtest From CSV Bars

```powershell
autonomous-day-trading-agent backtest --bars .\bars.csv --symbol SPY
```

## Investment Allocation Proposal

```powershell
autonomous-day-trading-agent invest-plan --capital 1000 --symbols SPY,QQQ,AAPL --risk risk_limits.example.json
```

## Live Order Attempt

This remains blocked:

```powershell
autonomous-day-trading-agent live-order --symbol SPY --side buy --quantity 1 --price 500 --asset-type etf --risk risk_limits.example.json
```

## Integrations

| Integration | How |
| --- | --- |
| Alpaca paper trading | Replace `PaperBroker` with an Alpaca paper adapter after tests pass. |
| Robinhood Agentic Trading | Use as a separate broker/app route after reviewing official availability and controls. |
| Robinhood Crypto | Reuse the Robinhood plugin's crypto adapter shape. |
| MCP | Wrap `strategy-signal`, `paper-order`, and `invest-plan` as bounded tools. |
| Copilot Studio | Put a small API bridge in front of the CLI/package. |
| RAG | Retrieve strategy docs, filings, and trading notes before signal generation. |
| Quantum | Feed allocation proposals to the quantum trading plugin as a sidecar. |

## Safety

- Paper mode is true by default.
- Live order submission is blocked by code.
- Symbols, asset types, order value, position size, daily loss, and order count are limited.
- Options and short selling are off by default.
- Backtests must include costs and drawdown review before any live adapter.
- Broker keys must stay out of this repo.


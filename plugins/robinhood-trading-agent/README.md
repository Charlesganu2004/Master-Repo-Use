# Robinhood Trading Agent Plugin

This is a safe starter scaffold for connecting an AI trading agent to Robinhood-style workflows. It defaults to research and paper trading.

Important distinction:

- Robinhood's official public trading API is the Robinhood Crypto Trading API.
- Robinhood stocks/options automation generally relies on community libraries such as `robin_stocks`; treat those as unofficial, brittle, and research-first.

## Flow

```text
AI signal
  -> risk gate
  -> paper broker
  -> audit log
  -> human approval token
  -> optional live adapter
```

Live execution is intentionally blocked in this scaffold.

## Files

```text
plugins/robinhood-trading-agent/
|-- README.md
|-- plugin.json
|-- pyproject.toml
|-- risk_limits.example.json
|-- training_plan.md
`-- src/robinhood_trading_agent/
    |-- __init__.py
    |-- broker.py
    |-- cli.py
    |-- config.py
    |-- robinhood_crypto.py
    `-- risk.py
```

## Standalone Setup

PowerShell:

```powershell
$PluginPath = Read-Host "Path to plugins\robinhood-trading-agent"; Set-Location $PluginPath; python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install --upgrade pip; python -m pip install -e .
```

WSL/Bash:

```bash
read -rp "Path to plugins/robinhood-trading-agent: " plugin_path; cd "$plugin_path"; python3 -m venv .venv && source .venv/bin/activate && python -m pip install --upgrade pip && python -m pip install -e .
```

## Smoke Test

```powershell
robinhood-trading-agent smoke-test --risk risk_limits.example.json
```

## Propose A Trade

```powershell
robinhood-trading-agent propose --symbol BTC-USD --side buy --quantity 0.001 --price 65000 --asset-type crypto --risk risk_limits.example.json
```

## Paper Order

```powershell
robinhood-trading-agent paper-order --symbol BTC-USD --side buy --quantity 0.001 --price 65000 --asset-type crypto --risk risk_limits.example.json
```

## Live Order Attempt

This remains blocked by default:

```powershell
robinhood-trading-agent live-order --symbol BTC-USD --side buy --quantity 0.001 --price 65000 --asset-type crypto --risk risk_limits.example.json
```

## Robinhood Crypto Adapter

The scaffold includes `robinhood_crypto.py`, which documents the adapter boundary and builds a dry-run request shape. It does not submit network requests.

To turn it into a real adapter later:

1. Use Robinhood Crypto API credentials from the official dashboard.
2. Store credentials in environment variables, not files.
3. Implement request signing according to current Robinhood Crypto API docs.
4. Keep paper mode and dry-run logging until reviewed.
5. Add human approval token per order.
6. Add idempotency and duplicate-order protection.
7. Add full audit logs.

## Community Robinhood Stocks/Options Adapter

The scaffold includes a blocked community adapter shape for libraries like `robin_stocks`. It should remain research-only unless current platform rules and risks are reviewed.

## Integrations

| Integration | How |
| --- | --- |
| Robinhood Crypto | Implement the official crypto adapter behind risk gates. |
| Robinhood stocks/options | Use community libraries only for research/paper wrappers unless reviewed. |
| Alpaca | Use the same risk-gate shape with Alpaca paper trading. |
| MCP | Wrap `propose` and `paper-order` as MCP tools. |
| Copilot Studio | Put an API bridge in front of this CLI/package. |
| Quantum trading | Combine with [quantum trading agent](../quantum-trading-agent/README.md). |
| Training | Use [training_plan.md](training_plan.md). |

## Safety

- Paper mode is true by default.
- Live trading is blocked by code.
- Symbols and asset types are allowlisted.
- Max order value and daily limits are enforced.
- Human approval is required for live flow.
- Credentials are never stored in the repo.

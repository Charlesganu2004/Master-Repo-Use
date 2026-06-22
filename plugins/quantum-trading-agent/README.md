# Quantum Trading Agent Plugin

This is a safe starter scaffold for a quantum-assisted trading research agent. It defaults to research and paper trading. Live trading is blocked unless multiple explicit gates are enabled.

## What It Does

```text
market data or manual signal
  -> quantum/classical proposal
  -> deterministic risk gate
  -> paper broker
  -> audit log
  -> optional integration with MCP/API/Copilot Studio later
```

## What It Does Not Do

- It does not give financial advice.
- It does not place live trades by default.
- It does not bypass broker, regulatory, or compliance rules.
- It does not claim quantum advantage.

## Files

```text
plugins/quantum-trading-agent/
|-- README.md
|-- plugin.json
|-- pyproject.toml
|-- risk_limits.example.json
|-- training_plan.md
`-- src/quantum_trading_agent/
    |-- __init__.py
    |-- broker.py
    |-- cli.py
    |-- config.py
    |-- portfolio.py
    `-- risk.py
```

## Standalone Setup

PowerShell:

```powershell
$PluginPath = Read-Host "Path to plugins\quantum-trading-agent"; Set-Location $PluginPath; python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install --upgrade pip; python -m pip install -e .
```

WSL/Bash:

```bash
read -rp "Path to plugins/quantum-trading-agent: " plugin_path; cd "$plugin_path"; python3 -m venv .venv && source .venv/bin/activate && python -m pip install --upgrade pip && python -m pip install -e .
```

## Smoke Test

```powershell
quantum-trading-agent smoke-test --risk risk_limits.example.json
```

## Propose A Paper Trade

```powershell
quantum-trading-agent propose --symbol MSFT --side buy --quantity 1 --price 100 --risk risk_limits.example.json
```

## Paper Order

```powershell
quantum-trading-agent paper-order --symbol MSFT --side buy --quantity 1 --price 100 --risk risk_limits.example.json
```

## Quantum Portfolio Demo

This demo uses a simple deterministic optimizer now. It is intentionally small so you can replace the internals with Qiskit, PennyLane, OpenQAOA, or another quantum optimizer later.

```powershell
quantum-trading-agent optimize-demo
```

## Live Trading Gate

Live trading should require all of these:

1. `paper_trading_only` is false in risk config.
2. `require_human_approval` is true.
3. `ALLOW_LIVE_TRADING=true` is set in the environment.
4. A human provides an approval token for the exact order.
5. The risk gate approves the order.
6. The broker adapter is replaced with a real, audited implementation.

The included live adapter refuses live orders.

## Integrations

| Integration | How |
| --- | --- |
| MCP | Wrap `propose_trade` and `optimize_portfolio` as MCP tools. |
| Copilot Studio | Put an API bridge in front of the CLI or Python package. |
| Alpaca paper trading | Replace `PaperBroker` with an Alpaca paper adapter. |
| RAG | Feed strategy docs and market notes to the agent before proposing orders. |
| AgentMemory | Store assumptions, test results, and rejected trades. |
| Quantum | Replace the optimizer with Qiskit/PennyLane/OpenQAOA code. |

## Training

See [training_plan.md](training_plan.md) for ML, RL, QML, and LLM setup.

# Plugins

GitHub: https://github.com/Charlesganu2004/Master-Repo-Use

Plugins are self-contained agent + tool packages. Install one with a single command, run the smoke test, and it is ready. Each plugin has its own risk limits, audit log, and paper-mode default.

---

## Plugin Index

| Plugin | What it does | Status | Install |
|---|---|---|---|
| [autonomous-day-trading-agent](autonomous-day-trading-agent/README.md) | Signal generation, backtesting, paper trading, invest-plan proposals | Active | See below |
| [robinhood-trading-agent](robinhood-trading-agent/README.md) | Robinhood Crypto research and paper trading lane | Active | See below |
| [quantum-trading-agent](quantum-trading-agent/README.md) | Quantum-enhanced portfolio optimization and paper trading | Active | See below |

---

## Install Any Plugin (PowerShell)

```powershell
$PluginName = Read-Host "Plugin name (e.g. autonomous-day-trading-agent)"
$RepoRoot = (Get-Location).Path  # run from repo root
$PluginPath = Join-Path $RepoRoot "plugins\$PluginName"
Set-Location $PluginPath
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
& "$PluginName" smoke-test --risk risk_limits.example.json
```

WSL/Bash:

```bash
read -rp "Plugin name: " plugin_name
read -rp "Path to Master-Repo-Use: " repo_root
cd "$repo_root/plugins/$plugin_name"
python3 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip && python -m pip install -e .
"$plugin_name" smoke-test --risk risk_limits.example.json
```

---

## Plugin API Contract

Every plugin in this repo provides:

| File | Purpose |
|---|---|
| `plugin.json` | Declares commands, tools, MCP config, risk settings, cost profile |
| `README.md` | What it does, prerequisites, install, smoke test, commands |
| `pyproject.toml` | Python package definition with CLI entrypoints |
| `risk_limits.example.json` | Example risk configuration — copy to `risk_limits.json` to use |
| `src/` | Implementation: cli.py, config.py, risk.py, broker.py |

---

## Combine Plugins

Plugins can be used together. Example — autonomous day trading + Alpaca MCP:

```powershell
# Install the plugin
$RepoRoot = (Get-Location).Path  # run from repo root
Set-Location (Join-Path $RepoRoot "plugins\autonomous-day-trading-agent")
python -m venv .venv; .\.venv\Scripts\Activate.ps1
python -m pip install -e .

# Start the Alpaca MCP server in paper mode
$env:ALPACA_API_KEY = Read-Host "Alpaca paper API key"
$env:ALPACA_SECRET_KEY = Read-Host "Alpaca paper secret"
$env:ALPACA_PAPER = "true"
npx -y alpaca-mcp-server
```

Then wire the plugin's commands to the Alpaca MCP server in your agent config.

---

## Register a Plugin With Agent Frameworks

**Squad:**
```json
{
  "plugins": [
    { "path": "./plugins/autonomous-day-trading-agent", "enabled": true }
  ]
}
```

**Copilot Studio:**
1. Deploy the plugin as an Azure Function or hosted API.
2. Add its OpenAPI spec as a custom connector action.
3. Wire the action into a Copilot Studio topic.

**Claude Code:**
Add the plugin folder to the MCP allowed paths:
```powershell
$PluginPath = Read-Host "Path to plugin"
npx -y @modelcontextprotocol/server-filesystem $PluginPath
```

---

## Add a New Plugin

See [docs/ADDING-PLUGINS.md](../docs/ADDING-PLUGINS.md) for the full scaffold guide.

Quick summary:
1. Run the scaffold command to create the folder structure.
2. Fill in `plugin.json` and `README.md`.
3. Implement `src/[plugin]/cli.py` with at least a `smoke-test` command.
4. Add risk limits to `risk_limits.example.json`.
5. Run the smoke test clean.
6. Have Sentinel review the code.
7. Add the plugin to this index.

---

## Security Rules for All Plugins

- Paper mode is on by default. Live mode requires explicit human approval.
- No secrets in any committed file. All credentials go in environment variables.
- MCP allowed paths are scoped to the plugin folder only.
- Risk limits are enforced by the plugin, not the agent. The agent cannot bypass them.
- Every trade (paper or live) is written to an audit log.

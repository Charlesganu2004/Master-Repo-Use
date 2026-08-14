# Adding Plugins

GitHub: https://github.com/Charlesganu2004/Master-Repo-Use

A plugin is a self-contained agent + tool package. It can be installed into any project with one command and immediately runs its smoke test. This guide shows how to scaffold, document, and publish a new plugin.

Replace `REVIEWED_VERSION` with an exact package release you inspected; never use `latest` or automatic yes.

---

## Plugin Structure

Every plugin has this layout:

```text
plugins/my-plugin-name/
├── plugin.json           ← required: plugin contract
├── README.md             ← required: what it does and how to use it
├── pyproject.toml        ← required (Python) OR package.json (TypeScript)
├── risk_limits.example.json ← required for trading plugins
├── training_plan.md      ← optional: how to fine-tune or adapt the agent
└── src/
    └── my_plugin/
        ├── __init__.py
        ├── cli.py
        ├── config.py
        ├── risk.py       ← required for trading plugins
        └── broker.py     ← required for trading plugins
```

---

## plugin.json Reference

```json
{
  "name": "my-plugin-name",
  "version": "0.1.0",
  "description": "One sentence: what this plugin does.",
  "category": "trading | research | utility | devtools | finance | quantum",
  "entrypoint": "src/my_plugin/cli.py",
  "commands": [
    {
      "name": "smoke-test",
      "description": "Run a minimal test to verify installation.",
      "args": ["--risk <risk_limits_file>"]
    }
  ],
  "tools": [
    {
      "name": "tool-name",
      "description": "What this tool does (under 50 words).",
      "inputSchema": {
        "type": "object",
        "properties": {
          "param": { "type": "string", "description": "What this parameter is." }
        },
        "required": ["param"]
      }
    }
  ],
  "mcp": {
    "allowed_paths": ["./data", "./logs"],
    "env_vars": ["API_KEY", "API_SECRET"]
  },
  "risk": {
    "paper_mode_default": true,
    "live_requires_approval": true,
    "risk_limits_file": "risk_limits.example.json"
  },
  "cost": {
    "model_tier": "standard",
    "estimated_tokens_per_run": 3000
  }
}
```

---

## Scaffold a New Plugin — One Command

PowerShell:

```powershell
$PluginName = Read-Host "Plugin name (kebab-case, e.g. my-research-agent)"
$RepoRoot = (Get-Location).Path  # run from repo root
$PluginRoot = Join-Path $RepoRoot "plugins\$PluginName"
New-Item -ItemType Directory -Force "$PluginRoot\src\$($PluginName -replace '-','_')" | Out-Null
New-Item -ItemType File -Force "$PluginRoot\plugin.json" | Out-Null
New-Item -ItemType File -Force "$PluginRoot\README.md" | Out-Null
New-Item -ItemType File -Force "$PluginRoot\pyproject.toml" | Out-Null
New-Item -ItemType File -Force "$PluginRoot\risk_limits.example.json" | Out-Null
New-Item -ItemType File -Force "$PluginRoot\src\$($PluginName -replace '-','_')\__init__.py" | Out-Null
New-Item -ItemType File -Force "$PluginRoot\src\$($PluginName -replace '-','_')\cli.py" | Out-Null
Write-Host "Scaffolded at $PluginRoot — fill in plugin.json and README.md."
```

WSL/Bash:

```bash
read -rp "Plugin name (kebab-case): " plugin_name
read -rp "Path to Master-Repo-Use: " repo_root
plugin_root="$repo_root/plugins/$plugin_name"
pkg_name="${plugin_name//-/_}"
mkdir -p "$plugin_root/src/$pkg_name"
touch "$plugin_root/plugin.json" "$plugin_root/README.md" "$plugin_root/pyproject.toml" \
      "$plugin_root/risk_limits.example.json" "$plugin_root/src/$pkg_name/__init__.py" \
      "$plugin_root/src/$pkg_name/cli.py"
echo "Scaffolded at $plugin_root — fill in plugin.json and README.md."
```

---

## pyproject.toml Template

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-plugin-name"
version = "0.1.0"
description = "What this plugin does."
requires-python = ">=3.11"
dependencies = [
    # add your dependencies here
]

[project.scripts]
my-plugin-name = "my_plugin.cli:main"
```

---

## README.md Template

```markdown
# My Plugin Name

One sentence: what this plugin does.

## Prerequisites

- Python 3.11+
- [Any API key or account needed]

## Install

```powershell
$PluginPath = Read-Host "Path to plugins\my-plugin-name"
Set-Location $PluginPath
python -m venv .venv; .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip; python -m pip install -e .
```

## Smoke Test

```powershell
my-plugin-name smoke-test --risk risk_limits.example.json
```

Expected output: `Smoke test passed.`

## Commands

| Command | What it does |
|---------|-------------|
| `smoke-test` | Verifies installation |
| [add your commands] | |

## Risk Limits

Copy `risk_limits.example.json` to `risk_limits.json` and set your limits before running.

## Security Notes

- Paper mode is on by default.
- Live mode requires explicit approval. See `plugin.json` → `risk.live_requires_approval`.
```

---

## Install a Plugin Into a Project

```powershell
$PluginPath = Read-Host "Path to plugin folder"
Set-Location $PluginPath
python -m pip install -e .
```

---

## Connect a Plugin to an MCP Server

Add the plugin's allowed paths to the MCP server startup:

```powershell
$PluginPath = Read-Host "Path to plugin folder"
$DataPath = Join-Path $PluginPath "data"
npx @modelcontextprotocol/server-filesystem@REVIEWED_VERSION $DataPath
```

---

## Register a Plugin in the Index

After creating a plugin, add it to [plugins/README.md](../plugins/README.md) with a one-line description and its install command.

---

## Security Checklist Before Publishing a Plugin

- [ ] Paper mode is on by default (`risk.paper_mode_default: true` in plugin.json)
- [ ] Live mode requires explicit approval (`risk.live_requires_approval: true`)
- [ ] No secrets hardcoded in any file
- [ ] All env vars are listed in plugin.json `mcp.env_vars`
- [ ] MCP allowed paths are scoped to the plugin folder only
- [ ] Smoke test passes clean
- [ ] Risk limits file is an example, not a real configuration
- [ ] Sentinel (security-sentinel.md) has reviewed the plugin code

# GitHub Copilot Setup

This guide makes `Charlesganu2004/Master-Repo-Use` the shared instruction/catalog layer for GitHub Copilot without loading the entire catalog into every prompt.

## Repository scope

Copilot automatically reads `.github/copilot-instructions.md` when operating in this repository context. That file points Copilot to `AGENTS.md`, the catalog, vetting, security, and setup guides.

## Copilot CLI global scope

The global bootstrap scripts add a small user-level Master Repo instruction file and configure `COPILOT_CUSTOM_INSTRUCTIONS_DIRS` so Copilot CLI can discover this private repo's instructions outside the repo too.

### PowerShell

```powershell
$p="$HOME\Master-Repo-Use"; & "$p\scripts\setup-global-ai.ps1" -RepoPath $p -CopilotOnly
```

### Bash / WSL / macOS / Linux

```bash
bash "$HOME/Master-Repo-Use/scripts/setup-global-ai.sh" "$HOME/Master-Repo-Use" --copilot-only
```

Verify in Copilot CLI:

```text
/instructions
```

## How catalog repos work in Copilot

A repo in `repo-lists/all-curated.txt` is a catalog entry, not automatically a Copilot plugin. Use the best available adapter:

1. MCP server when the project exposes one.
2. Copilot skill/custom instruction/plugin when supported.
3. CLI or HTTP/API wrapper.
4. Direct library use inside the codebase.

Examples:

- GitHub operations: `github/github-mcp-server`.
- Browser automation: `microsoft/playwright-mcp`.
- Context compression: `headroomlabs-ai/headroom` via wrap/MCP/proxy.
- Agent framework: `github/copilot-sdk` or another vetted framework from the catalog.
- Portable instruction sources: `github/awesome-copilot` plus this repo's `AGENTS.md`/`.github/copilot-instructions.md`.

## GitHub.com / coding agent

Keep `.github/copilot-instructions.md` committed. When GitHub's coding agent operates on this repository, it can consume the repo-local instructions. Cross-repository private catalog access still depends on the GitHub identity and permissions available to that environment.

## Do not load everything

The correct default is:

```text
prompt -> identify lane -> search Master Repo -> read only relevant files -> activate only relevant tools
```

Do not paste `all-curated.txt` or the entire repo catalog into every Copilot prompt.

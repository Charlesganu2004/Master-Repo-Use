# Master Repo Use

Private command center and curated catalog for agent frameworks, RAG, memory, MCP servers, context/token management, GitHub Copilot, Claude Code, Codex, Microsoft Copilot Studio, autonomous-agent tooling, finance/trading research, quantum computing, cloud/cost reduction, app templates, observability, and supporting developer tools.

Repository: `Charlesganu2004/Master-Repo-Use`

The goal is simple: clone this repo once, then use it as the shared instruction/catalog layer for your AI coding tools. The catalog stays here; each client loads the same compact rules and only pulls the task-relevant repos, skills, MCP servers, or setup instructions when needed.

## Start here

### Requirements

- Git
- GitHub CLI (`gh`) authenticated to the GitHub account that can read this private repo
- PowerShell 7+ on Windows, or Bash/WSL/macOS/Linux
- Install the AI clients you actually use: GitHub Copilot CLI/IDE, Claude Code, Codex, or their supported web/cloud versions

Authenticate once:

```bash
gh auth login
```

### Clone

PowerShell:

```powershell
$RepoPath = "$HOME\Master-Repo-Use"; gh repo clone Charlesganu2004/Master-Repo-Use $RepoPath; Set-Location $RepoPath
```

Bash / WSL / macOS / Linux:

```bash
repo_path="$HOME/Master-Repo-Use"; gh repo clone Charlesganu2004/Master-Repo-Use "$repo_path" && cd "$repo_path"
```

## Global AI setup

This makes the Master Repo guidance available by default to supported local clients without installing every third-party repo in the catalog.

### Windows one-liner

```powershell
$p="$HOME\Master-Repo-Use"; if (Test-Path "$p\.git") { git -C $p pull } else { gh repo clone Charlesganu2004/Master-Repo-Use $p }; & "$p\scripts\setup-global-ai.ps1" -RepoPath $p
```

### Bash / WSL / macOS / Linux one-liner

```bash
p="$HOME/Master-Repo-Use"; if [ -d "$p/.git" ]; then git -C "$p" pull; else gh repo clone Charlesganu2004/Master-Repo-Use "$p"; fi; bash "$p/scripts/setup-global-ai.sh" "$p"
```

What the bootstrap configures:

- **GitHub Copilot CLI:** user-level instructions plus `COPILOT_CUSTOM_INSTRUCTIONS_DIRS` pointing at this repo.
- **Claude Code:** user-level `~/.claude/CLAUDE.md` guidance that points back to this repo; the repo's own `CLAUDE.md` is loaded automatically when you work here.
- **Codex:** user-level `~/.codex/AGENTS.md` guidance plus the repo's `AGENTS.md` when you work in this repo.
- Existing personal instruction files are preserved; the scripts update only the marked Master Repo block.

See [docs/GLOBAL-AI-SETUP.md](docs/GLOBAL-AI-SETUP.md) for the full setup, refresh, uninstall, and online/cloud instructions.

## GitHub Copilot setup

The repo includes `.github/copilot-instructions.md`, so GitHub Copilot automatically receives Master Repo guidance whenever Copilot is operating in this repository context.

For Copilot CLI, the global bootstrap above also makes this repo available across other local repositories.

### Copilot one-liner

PowerShell:

```powershell
$p="$HOME\Master-Repo-Use"; & "$p\scripts\setup-global-ai.ps1" -RepoPath $p -CopilotOnly
```

Bash:

```bash
bash "$HOME/Master-Repo-Use/scripts/setup-global-ai.sh" "$HOME/Master-Repo-Use" --copilot-only
```

Verify in Copilot CLI:

```text
/instructions
```

Copilot should show the repository instructions and, for CLI, the user/global Master Repo instructions.

Full guide: [docs/COPILOT-SETUP.md](docs/COPILOT-SETUP.md).

## Interactive command center

The interactive UI is `index.html`.

### Reliable local mode — works with a private repo

From the repo root:

```bash
python -m http.server 8080
```

Then open:

```text
http://localhost:8080/
```

PowerShell one-liner:

```powershell
Set-Location "$HOME\Master-Repo-Use"; python -m http.server 8080
```

### GitHub Pages mode

A Pages deployment workflow is included at `.github/workflows/pages.yml`. GitHub Pages for a **private** personal repository requires a GitHub plan that supports private-repo Pages. In repository **Settings → Pages**, set **Source** to **GitHub Actions** once. After that, pushes to `main` deploy `index.html` automatically.

If private-repo Pages is not available on the GitHub account, use the local mode above; the interactive UI itself does not require the repository to be public.

## How to use the Master Repo

1. Start with [docs/REPO-CATALOG.md](docs/REPO-CATALOG.md) or [repo-lists/all-curated.txt](repo-lists/all-curated.txt).
2. Pick only the lane needed for the current task.
3. Check [docs/VETTING-REPORT.md](docs/VETTING-REPORT.md) and [docs/REPO-HEALTH.md](docs/REPO-HEALTH.md) before depending on a third-party project.
4. Use [docs/REPO-INSTRUCTIONS.md](docs/REPO-INSTRUCTIONS.md) for install/run instructions.
5. Use [docs/COMBINING-REPOS.md](docs/COMBINING-REPOS.md) when several tools need to work together.
6. Use [docs/SECURITY.md](docs/SECURITY.md) before enabling write-capable agents, MCP servers, browser automation, secrets, or live external actions.

The default rule for every AI client is: **do not load or install the whole catalog into context. Discover the relevant lane, then load the minimum files/tools needed for that task.**

## Cross-client compatibility

The Master Repo uses portable instruction and integration layers so the same catalog can be consumed by multiple agents:

| Client | Automatic repo instructions | Global/local setup | Tool integration path |
|---|---|---|---|
| GitHub Copilot on GitHub/IDE | `.github/copilot-instructions.md` | Copilot CLI user instructions | MCP, skills, CLI/API wrappers |
| GitHub Copilot CLI | `.github/copilot-instructions.md`, `AGENTS.md`, `CLAUDE.md` | `~/.copilot/` + `COPILOT_CUSTOM_INSTRUCTIONS_DIRS` | MCP, skills, plugins, CLI/API wrappers |
| Claude Code local | `CLAUDE.md` | `~/.claude/CLAUDE.md` | MCP, skills, plugins, hooks, CLI/API wrappers |
| Claude Code on the web | committed `CLAUDE.md`, `.claude/`, `.mcp.json` | repo/cloud environment | repo-contained setup and tools |
| Codex local | `AGENTS.md` | `~/.codex/AGENTS.md` | skills, MCP, CLI/API wrappers |
| Codex cloud / ChatGPT coding workflows | committed `AGENTS.md` when the repo is selected | connect/select the GitHub repo | repo-contained skills/instructions/tools supported by the environment |
| ChatGPT web | connect this private GitHub repo | account/project instructions are configured in ChatGPT | GitHub app, supported plugins/MCP/skills |
| Claude.ai chat/projects | connect/add this GitHub repo or use Claude Code web | profile/project preferences are configured in Claude | GitHub integration and supported project tools |

A repository listed here is not automatically a native plugin for every client. When a tool does not have a native integration, use the compatibility order documented in [docs/GLOBAL-AI-SETUP.md](docs/GLOBAL-AI-SETUP.md): **MCP → skill/instructions → CLI/API wrapper → direct library**.

## Core additions and high-use tools

These are included in the catalog and setup guides:

- **Omni:** `getomnico/omni` — self-hosted workplace AI agent.
- **Claude-Mem:** `thedotmack/claude-mem` — persistent Claude Code memory; current quick install: `npx claude-mem install`.
- **Headroom:** `headroomlabs-ai/headroom` — context compression, cross-agent memory, MCP, and wrappers for Claude, Codex, Copilot, and other agents.
- **Task Observer / Agent Monitor:** `hoangsonww/Claude-Code-Agent-Monitor` — live Claude Code/Codex session, tool, subagent, and task monitoring.
- **Claude Code setup resources:** `centminmod/my-claude-code-setup` plus the repo-level `CLAUDE.md` and global setup scripts here.
- **GitHub Copilot:** `github/copilot-cli`, `github/copilot-sdk`, `github/awesome-copilot`, and `github/github-mcp-server`.
- **Watermark remover:** `D-Ogi/WatermarkRemover-AI` in the media-tools lane. Use only on media you own or are authorized to modify; do not use it to remove attribution or rights-management marks from third-party content without permission.

See [repo-lists/ai-client-tools.txt](repo-lists/ai-client-tools.txt) and [repo-lists/github-copilot.txt](repo-lists/github-copilot.txt).

## Claude-Mem

Install for Claude Code:

```bash
npx claude-mem install
```

Restart Claude Code after installation. Keep Claude-Mem optional: Claude Code already has native `CLAUDE.md` and auto-memory, so install Claude-Mem when you specifically want its persistent observation/search workflow.

## Headroom

Recommended isolated global CLI install:

```bash
uv tool install --python 3.13 "headroom-ai[all]"
headroom doctor
```

Examples:

```bash
headroom wrap claude
headroom wrap codex
headroom wrap copilot
```

Headroom is optional. Do not make it a hard dependency for every Master Repo task.

## Task Observer / Agent Monitor

Use `hoangsonww/Claude-Code-Agent-Monitor` for a visual view of Claude Code and Codex activity. Setup details live in [repo-lists/agent-observability-setup.txt](repo-lists/agent-observability-setup.txt) and the upstream repository.

## Token and work-spend limit — optional, separate setup

Token/spend limiting is **not** enabled by the global one-liners.

If you want a work budget, hard/soft caps, context compression, and a fallback to free/local models after the paid budget is reached, follow the independent guide:

**[docs/TOKEN-BUDGET.md](docs/TOKEN-BUDGET.md)**

That guide separates:

- context/token limits from dollar budgets;
- provider-native limits from local gateway limits;
- paid primary models from free/local fallback models;
- clients that can route through a gateway from clients whose subscription UI controls the model directly.

The recommended fallback path is a local OpenAI-compatible server (for example LocalAI or llama.cpp with a compatible open-weight model) so the fallback does not create another paid API bill.

## Repo map

| Path | Purpose |
|---|---|
| `AGENTS.md` | portable Master Repo contract for Codex/Copilot-compatible agents |
| `CLAUDE.md` | Claude Code entrypoint |
| `.github/copilot-instructions.md` | repository-wide GitHub Copilot instructions |
| `agents/` | named specialist agents |
| `docs/` | setup, architecture, security, usage, vetting, and integration guides |
| `repo-lists/` | curated repository lists grouped by lane |
| `skills/` | portable skills and reusable workflows |
| `plugins/` | plugin packages and plugin documentation |
| `scripts/` | health checks, auditing, and global setup helpers |
| `index.html` | interactive command center |
| `quantum/` | quantum-computing lane |
| `cost-reduction/` | cloud/token/cost lane |

## Health, vetting, and security

- Repo health: [docs/REPO-HEALTH.md](docs/REPO-HEALTH.md)
- Vetting: [docs/VETTING-REPORT.md](docs/VETTING-REPORT.md)
- Security: [docs/SECURITY.md](docs/SECURITY.md)
- Static audit: `python scripts/static_audit.py <clones-dir>`
- Catalog freshness: `python scripts/check_freshness.py`

## Update your local copy

```bash
git -C "$HOME/Master-Repo-Use" pull
```

After a major instruction change, rerun the global setup script so copied user-level instruction blocks are refreshed. Copilot CLI's `COPILOT_CUSTOM_INSTRUCTIONS_DIRS` continues pointing at the live repo automatically.

## Recommended first verification

Run these after setup:

```bash
git -C "$HOME/Master-Repo-Use" status
python "$HOME/Master-Repo-Use/scripts/check_freshness.py"
```

Then open your preferred client and ask:

```text
What Master Repo instructions are loaded, and which catalog lane would you use for this task?
```

For GitHub Copilot CLI, also run `/instructions`. For Claude Code, run `/memory`. Codex should read the root `AGENTS.md` before work in this repo.

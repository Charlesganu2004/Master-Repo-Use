# Master Repo Use

Private command center and curated catalog for agent frameworks, RAG, memory, MCP servers, token/context management, GitHub Copilot, Claude Code, Codex, Microsoft Copilot Studio, observability, finance/trading research, quantum computing, cloud/cost reduction, app templates, and supporting developer tools.

Repository: `Charlesganu2004/Master-Repo-Use`

The purpose of this repository is to be the **shared catalog + instruction layer** used by your AI coding tools. Clone it once, keep it current, and let each client discover only the task-relevant repos, skills, MCP servers, and setup instructions when needed.

## Live catalog health

![Master Repo live catalog health](docs/catalog-status.svg)

Full status: [docs/CATALOG-STATUS.md](docs/CATALOG-STATUS.md)

The Catalog Guardian runs automatically on catalog changes and every 6 hours. It tracks repository freshness and security state, immediately deep-vets newly added repos, rotates deep scans through existing repos, and updates the visual above.

Status rules:

- 🟢 **HEALTHY** — active and no current removal signal.
- 🟡 **STALE** — needs review because maintenance activity is old; staleness alone does not auto-delete a repo.
- 🟠 **REVIEW** — high-risk source/security findings need human review.
- 🔴 **REMOVE** — deleted, disabled, archived, or confirmed critical deep-scan finding; eligible for automatic removal.

## Start here

### Requirements

- Git
- GitHub CLI (`gh`) authenticated to an account that has access to this private repository
- PowerShell 7+ on Windows, or Bash/WSL/macOS/Linux
- The AI clients you actually use: GitHub Copilot, Claude Code, Codex, ChatGPT/Codex cloud, or Claude web/code environments

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

This makes the Master Repo guidance available by default to supported local clients **without installing the entire third-party catalog into every machine or prompt**.

### Windows one-liner

```powershell
$p="$HOME\Master-Repo-Use"; if (Test-Path "$p\.git") { git -C $p pull } else { gh repo clone Charlesganu2004/Master-Repo-Use $p }; & "$p\scripts\setup-global-ai.ps1" -RepoPath $p
```

### Bash / WSL / macOS / Linux one-liner

```bash
p="$HOME/Master-Repo-Use"; if [ -d "$p/.git" ]; then git -C "$p" pull; else gh repo clone Charlesganu2004/Master-Repo-Use "$p"; fi; bash "$p/scripts/setup-global-ai.sh" "$p"
```

The bootstrap configures:

- **GitHub Copilot CLI:** global/user instructions and `COPILOT_CUSTOM_INSTRUCTIONS_DIRS` pointing at this repo.
- **Claude Code:** `~/.claude/CLAUDE.md` pointer to the Master Repo plus the repo-local `CLAUDE.md`.
- **Codex:** `~/.codex/AGENTS.md` pointer plus the repo-local `AGENTS.md`.
- **Global watermark command:** `master-watermark` on Bash platforms or `$HOME\bin\master-watermark.ps1` on Windows. It installs the vetted upstream tool on first use instead of downloading its large models during the main bootstrap.
- Existing personal instruction files are preserved; only the marked Master Repo block is managed.

The watermark tool is for media you own or are authorized to modify. Do not use it to remove attribution or rights-management marks from third-party content without permission.

Full guide: [docs/GLOBAL-AI-SETUP.md](docs/GLOBAL-AI-SETUP.md).

## GitHub Copilot setup

The repository includes `.github/copilot-instructions.md`, so repository-aware GitHub Copilot sessions receive the Master Repo rules automatically.

### Copilot-only one-liner

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

Full guide: [docs/COPILOT-SETUP.md](docs/COPILOT-SETUP.md).

## Interactive command center

The interactive UI is `index.html`.

### Reliable local mode

Works even when the repository is private:

```bash
cd "$HOME/Master-Repo-Use"
python -m http.server 8080
```

Open:

```text
http://localhost:8080/
```

PowerShell:

```powershell
Set-Location "$HOME\Master-Repo-Use"; python -m http.server 8080
```

### GitHub Pages mode

The repo now includes `.github/workflows/pages.yml`, which deploys the interactive command center automatically from `main`.

One-time GitHub setting:

1. Open **Settings → Pages**.
2. Set **Source** to **GitHub Actions**.
3. Save.

Private-repository Pages availability depends on the GitHub plan. If private Pages is unavailable, use the local mode above.

## How to use the Master Repo

1. Start with [docs/REPO-CATALOG.md](docs/REPO-CATALOG.md) or [repo-lists/all-curated.txt](repo-lists/all-curated.txt).
2. Pick only the lane needed for the current task.
3. Check [docs/VETTING-REPORT.md](docs/VETTING-REPORT.md), [docs/CATALOG-STATUS.md](docs/CATALOG-STATUS.md), and [docs/REPO-HEALTH.md](docs/REPO-HEALTH.md).
4. Use [docs/REPO-INSTRUCTIONS.md](docs/REPO-INSTRUCTIONS.md) for install/run instructions.
5. Use [docs/COMBINING-REPOS.md](docs/COMBINING-REPOS.md) when multiple tools need to work together.
6. Use [docs/SECURITY.md](docs/SECURITY.md) before enabling write-capable agents, browser automation, MCP servers, secrets, or external actions.

Default rule for every AI client: **do not load or install the whole catalog into context. Discover the relevant lane, then load the minimum files/tools needed for that task.**

## Cross-client compatibility

| Client | Repo/default instructions | Global path | Integration path |
|---|---|---|---|
| GitHub Copilot IDE/GitHub | `.github/copilot-instructions.md` | repo context | MCP, skills, CLI/API wrappers |
| GitHub Copilot CLI | `.github/copilot-instructions.md`, `AGENTS.md`, `CLAUDE.md` | `~/.copilot/` + `COPILOT_CUSTOM_INSTRUCTIONS_DIRS` | MCP, skills, plugins, CLI/API wrappers |
| Claude Code local | `CLAUDE.md` | `~/.claude/CLAUDE.md` | MCP, skills, plugins, hooks, CLI/API wrappers |
| Claude Code web | committed `CLAUDE.md` and repo config | repo/cloud environment | supported repo tools |
| Codex local | `AGENTS.md` | `~/.codex/AGENTS.md` | skills, MCP, CLI/API wrappers |
| Codex cloud / ChatGPT coding | committed `AGENTS.md` when repo selected | connected private GitHub repo | supported repo-contained skills/tools |
| ChatGPT web | connected private GitHub repo | ChatGPT project/account customization | GitHub connector + supported tools |
| Claude.ai | connected/private repo or Claude Code web | Claude project/profile settings | GitHub integration + supported tools |

A catalog repo is not automatically a native plugin for every AI client. Use this compatibility order: **MCP → skill/plugin/instructions → CLI/API wrapper → direct library**.

Full cross-client guide: [docs/GLOBAL-AI-SETUP.md](docs/GLOBAL-AI-SETUP.md).

## Core additions and high-use tools

Included in the catalog and setup guides:

- **Omni:** `getomnico/omni`
- **Claude-Mem:** `thedotmack/claude-mem`
- **Headroom:** `headroomlabs-ai/headroom`
- **Task Observer / Agent Monitor:** `hoangsonww/Claude-Code-Agent-Monitor`
- **Claude Code setup:** `centminmod/my-claude-code-setup`, `anthropics/claude-plugins-official`, repo `CLAUDE.md`
- **GitHub Copilot:** `github/copilot-cli`, `github/copilot-sdk`, `github/awesome-copilot`, `github/github-mcp-server`
- **Codex:** `openai/codex`
- **Watermark remover:** `D-Ogi/WatermarkRemover-AI` — authorized media only

Lists:

- [repo-lists/ai-client-tools.txt](repo-lists/ai-client-tools.txt)
- [repo-lists/github-copilot.txt](repo-lists/github-copilot.txt)

## Claude-Mem

```bash
npx claude-mem install
```

Restart Claude Code after installation. Claude-Mem remains optional.

## Headroom

```bash
uv tool install --python 3.13 "headroom-ai[all]"
headroom doctor
```

Supported examples:

```bash
headroom wrap claude
headroom wrap codex
headroom wrap copilot
```

Headroom remains optional and is not a hard dependency for every task.

## Task Observer / Agent Monitor

`hoangsonww/Claude-Code-Agent-Monitor` provides a visual view of Claude Code/Codex sessions, tool use, subagents, and task activity. See [repo-lists/agent-observability-setup.txt](repo-lists/agent-observability-setup.txt).

## Token and work-spend limit — optional, separate setup

Token/spend limiting is **not** enabled by either global one-liner.

Use the independent guide:

**[docs/TOKEN-BUDGET.md](docs/TOKEN-BUDGET.md)**

It covers:

- context and output token limits;
- daily/weekly/monthly work budgets;
- soft and hard spending caps;
- compression before fallback;
- paid-primary → free/local fallback routing for compatible clients;
- fail-closed behavior when the budget state cannot be verified.

Recommended no-new-bill fallback: a local OpenAI-compatible server such as LocalAI or llama.cpp with an appropriate open-weight model.

Hosted subscription UIs such as ChatGPT web, Claude.ai, and GitHub.com's own model picker cannot be silently rerouted by this repo; use their native usage controls for those hosted requests.

## Automatic repo security and intake guardian

Every new catalog repo is deep-vetted automatically by `.github/workflows/catalog-guardian.yml`.

The guardian checks for:

- Unicode bidirectional/invisible control characters and hidden text patterns;
- suspicious shell download-and-execute patterns;
- encoded PowerShell and base64/dynamic execution patterns;
- likely credential exfiltration patterns;
- possible SQL-injection-style dynamic query construction;
- private keys and secret-like material;
- embedded PE/ELF executables;
- repository archived/disabled/deleted status;
- maintenance recency.

The scanner also invokes installed external security tools when available, including Semgrep SQL-injection rules and support for Gitleaks, Trivy, OSV-Scanner, and ClamAV. The catalog already contains security projects including Snyk CLI, Trivy, Semgrep, OpenGrep, OSV-Scanner, Gitleaks, TruffleHog, Cisco AI Defense MCP Scanner, OSSF Scorecard, Syft, Cosign, and Garak.

Important: static scanners can reduce risk but cannot mathematically prove third-party code is safe. Critical findings trigger removal eligibility; high-risk findings trigger human review; staleness alone is not treated as malware.

Guardian implementation: [scripts/catalog_guardian.py](scripts/catalog_guardian.py).

## Pull latest, but protect `main`

Everyone with read access can keep their clone current:

```bash
git checkout main
git pull --ff-only origin main
```

Contributors should work on branches and open pull requests:

```bash
git checkout -b feature/my-change
# make changes
git add .
git commit -m "describe change"
git push -u origin feature/my-change
```

This repo includes:

- `.github/CODEOWNERS` with `@Charlesganu2004` as owner for **all files**.
- `.github/workflows/owner-approval.yml`, which fails until `@Charlesganu2004` has approved the PR.

### One-time GitHub protection settings

Because repository rules are a GitHub server setting, enable these once in **Settings → Rules → Rulesets** or **Settings → Branches** for `main`:

1. Require a pull request before merging.
2. Require at least **1 approval**.
3. Require **review from Code Owners**.
4. Require status checks before merging and select **Owner Approval Check / owner-approval**.
5. Dismiss stale approvals when new commits are pushed.
6. Require conversation resolution before merging.
7. Block force pushes.
8. Block branch deletion.
9. Restrict direct updates/bypass so only `Charlesganu2004` can bypass when necessary.

With those server-side settings enabled, people can clone/fetch/pull the newest `main`, but cannot merge changes into `main` without your approval.

## Repo map

| Path | Purpose |
|---|---|
| `AGENTS.md` | portable cross-client Master Repo contract |
| `CLAUDE.md` | Claude Code entrypoint |
| `.github/copilot-instructions.md` | GitHub Copilot repo-wide instructions |
| `.github/CODEOWNERS` | Charles approval ownership |
| `.github/workflows/catalog-guardian.yml` | continuous health/security/vetting workflow |
| `.github/workflows/pages.yml` | interactive command-center deployment |
| `.github/workflows/owner-approval.yml` | PR owner-approval gate |
| `agents/` | named specialist agents |
| `docs/` | setup, security, vetting, status, and integration guides |
| `repo-lists/` | curated repositories grouped by lane |
| `skills/` | portable skills and reusable workflows |
| `plugins/` | plugin packages/documentation |
| `scripts/` | global setup, auditing, and guardian helpers |
| `index.html` | interactive command center |
| `quantum/` | quantum-computing lane |
| `cost-reduction/` | cloud/token/cost lane |

## Health, vetting, and security

- Live catalog: [docs/CATALOG-STATUS.md](docs/CATALOG-STATUS.md)
- Repo health: [docs/REPO-HEALTH.md](docs/REPO-HEALTH.md)
- Vetting: [docs/VETTING-REPORT.md](docs/VETTING-REPORT.md)
- Security: [docs/SECURITY.md](docs/SECURITY.md)
- Automatic guardian: `python scripts/catalog_guardian.py`
- Existing static audit: `python scripts/static_audit.py <clones-dir>`
- Catalog freshness: `python scripts/check_freshness.py`

## Update your local copy

```bash
git -C "$HOME/Master-Repo-Use" pull --ff-only
```

After a major instruction change, rerun the global setup script so copied user-level instruction blocks are refreshed. Copilot CLI's custom-instructions directory continues pointing at the live repo automatically.

## Verify setup

```bash
git -C "$HOME/Master-Repo-Use" status
python "$HOME/Master-Repo-Use/scripts/check_freshness.py"
```

Then ask your preferred client:

```text
What Master Repo instructions are loaded, and which catalog lane would you use for this task?
```

For GitHub Copilot CLI also run `/instructions`. For Claude Code use `/memory`. Codex should read the root `AGENTS.md` before work in this repo.

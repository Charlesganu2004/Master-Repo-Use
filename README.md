# Master Repo Use

Private command center and curated catalog for agent frameworks, RAG, memory, MCP servers, token/context management, GitHub Copilot, Claude Code, Codex, Microsoft Copilot Studio, observability, finance/trading research, quantum computing, cloud/cost reduction, app templates, security tooling, and supporting developer tools.

Repository: `Charlesganu2004/Master-Repo-Use`

The Master Repo is the shared **catalog + instructions + security/vetting layer** used by your AI coding tools. Clone it once, keep it current, and let each client discover only the task-relevant repos, skills, MCP servers, and setup instructions when needed.

## Live catalog health

![Master Repo live catalog health](docs/catalog-status.svg)

- Full status: [docs/CATALOG-STATUS.md](docs/CATALOG-STATUS.md)
- Latest in-depth stale/archive review: [docs/LIFECYCLE-REVIEW-2026-08-19.md](docs/LIFECYCLE-REVIEW-2026-08-19.md)
- Managed-repo policy: [managed-repos/README.md](managed-repos/README.md)

The visual is refreshed whenever Catalog Guardian is run and its owner-reviewed update is accepted. **There is no recurring AI/model maintenance loop and no six-hour scheduled Guardian job by default.** This avoids background model/API spend and recurring private-repo Actions usage.

Lifecycle rules:

- 🟢 **0–120 days since last push:** healthy from a freshness perspective.
- 🟡 **121–269 days:** stale warning.
- 🟠 **270–365 days:** replacement / managed-adoption review.
- 🔴 **>365 days:** remove from the active/runtime catalog unless an owner-approved reference/stability exception applies.
- **Archived + recent activity:** review the reason, releases, sunset/EOL notice, and successor before deciding.
- **Static research/reference repos:** may receive a `reference` override when inactivity is expected.
- **Deleted/disabled or confirmed CRITICAL security finding:** immediate removal candidate.

## Start here

Requirements:

- Git
- GitHub CLI (`gh`) authenticated to an account that can access this private repo
- PowerShell 7+ on Windows, or Bash/WSL/macOS/Linux
- The AI clients you actually use

Authenticate once:

```bash
gh auth login
```

### Clone

PowerShell:

```powershell
$RepoPath="$HOME\Master-Repo-Use"; gh repo clone Charlesganu2004/Master-Repo-Use $RepoPath; Set-Location $RepoPath
```

Bash / WSL / macOS / Linux:

```bash
repo_path="$HOME/Master-Repo-Use"; gh repo clone Charlesganu2004/Master-Repo-Use "$repo_path" && cd "$repo_path"
```

## Global AI setup

The global bootstrap installs a small instruction/pointer layer. It **does not install the entire third-party catalog into every machine or prompt**.

### Windows one-liner

```powershell
$p="$HOME\Master-Repo-Use"; if (Test-Path "$p\.git") { git -C $p pull --ff-only } else { gh repo clone Charlesganu2004/Master-Repo-Use $p }; & "$p\scripts\setup-global-ai.ps1" -RepoPath $p
```

### Bash / WSL / macOS / Linux one-liner

```bash
p="$HOME/Master-Repo-Use"; if [ -d "$p/.git" ]; then git -C "$p" pull --ff-only; else gh repo clone Charlesganu2004/Master-Repo-Use "$p"; fi; bash "$p/scripts/setup-global-ai.sh" "$p"
```

The bootstrap configures:

- **GitHub Copilot CLI:** global/user instructions + `COPILOT_CUSTOM_INSTRUCTIONS_DIRS`.
- **Claude Code:** `~/.claude/CLAUDE.md` pointer + repo `CLAUDE.md`.
- **Codex:** `~/.codex/AGENTS.md` pointer + repo `AGENTS.md`.
- **Monthly-on-next-use maintenance request:** clients run `scripts/maintenance_request.py --auto` when they already have an active Master Repo-aware session. It may create one GitHub review issue, then stops until you approve.
- **Global watermark command:** `master-watermark` on Bash platforms or `$HOME\bin\master-watermark.ps1` on Windows. The upstream tool is installed on first use, not during bootstrap.
- Existing personal instruction files are preserved; only the marked Master Repo block is managed.

Watermark removal is for media you own or are authorized to modify. Do not remove third-party attribution or rights-management marks without permission.

Full guide: [docs/GLOBAL-AI-SETUP.md](docs/GLOBAL-AI-SETUP.md).

## GitHub Copilot setup

The repository includes `.github/copilot-instructions.md`, so repo-aware Copilot sessions receive the Master Repo rules automatically.

PowerShell one-liner:

```powershell
$p="$HOME\Master-Repo-Use"; & "$p\scripts\setup-global-ai.ps1" -RepoPath $p -CopilotOnly
```

Bash one-liner:

```bash
bash "$HOME/Master-Repo-Use/scripts/setup-global-ai.sh" "$HOME/Master-Repo-Use" --copilot-only
```

Verify in Copilot CLI:

```text
/instructions
```

Full guide: [docs/COPILOT-SETUP.md](docs/COPILOT-SETUP.md).

## Interactive command center

The interactive page is `index.html`. It is dependency-free and every command card is **click-to-copy**.

### Local/private mode

PowerShell:

```powershell
Set-Location "$HOME\Master-Repo-Use"; python -m http.server 8080
```

Bash:

```bash
cd "$HOME/Master-Repo-Use" && python3 -m http.server 8080
```

Open:

```text
http://localhost:8080/
```

The page can also be opened directly as `index.html`; live JSON health refresh works best through HTTP.

### GitHub Pages mode

`.github/workflows/pages.yml` deploys `index.html` from approved `main` commits. One time: **Settings → Pages → Source → GitHub Actions**. Private-repo Pages availability depends on your GitHub plan; local mode works regardless.

## Approval-driven AI maintenance — no background model spend

The Master Repo does not continuously call GPT, Claude, Copilot, or Codex.

Instead, the first supported AI session after the 30-day review interval runs:

```bash
python scripts/maintenance_request.py --auto
```

If a review is due and no `[AI Maintenance]` issue is open, it creates one issue containing the complete maintenance prompt and assigns it to `Charlesganu2004`. The AI must stop there.

To approve the review, use the exact phrase:

```text
APPROVE AI MAINTENANCE
```

After approval, the AI may deep-review the catalog, prepare a branch, and open a PR. It still **must not merge `main` without your approval**.

Useful commands:

```bash
python scripts/maintenance_request.py --check
python scripts/maintenance_request.py --auto
python scripts/maintenance_request.py --generate
```

Full guide: [docs/AI-MAINTENANCE.md](docs/AI-MAINTENANCE.md).

`.github/workflows/catalog-guardian.yml` is manual-only. For zero Actions usage, run Guardian locally.

## How to use the Master Repo

1. Start with [docs/REPO-CATALOG.md](docs/REPO-CATALOG.md) or [repo-lists/all-curated.txt](repo-lists/all-curated.txt).
2. Pick only the lane needed for the current task.
3. Check [docs/VETTING-REPORT.md](docs/VETTING-REPORT.md), [docs/CATALOG-STATUS.md](docs/CATALOG-STATUS.md), [docs/REPO-HEALTH.md](docs/REPO-HEALTH.md), and [docs/SECURITY.md](docs/SECURITY.md).
4. Use [docs/REPO-INSTRUCTIONS.md](docs/REPO-INSTRUCTIONS.md) for install/run instructions.
5. Use [docs/COMBINING-REPOS.md](docs/COMBINING-REPOS.md) when several tools need to work together.
6. Use only the minimum task-relevant repos/files/tools; do not inject the whole catalog into every prompt.

## Cross-client compatibility

| Client | Default Master Repo path | Integration path |
|---|---|---|
| GitHub Copilot IDE/GitHub | `.github/copilot-instructions.md` | MCP → skills/instructions → CLI/API → library |
| GitHub Copilot CLI | repo instructions + `~/.copilot/` | MCP → skills/plugins → CLI/API → library |
| Claude Code local | `CLAUDE.md` + `~/.claude/CLAUDE.md` | MCP → skills/plugins/hooks → CLI/API → library |
| Claude Code web | committed repo instructions | supported repo/cloud tools |
| Codex local | `AGENTS.md` + `~/.codex/AGENTS.md` | skills → MCP → CLI/API → library |
| Codex cloud / ChatGPT coding | committed `AGENTS.md` when repo selected | supported connected-repo tools |
| ChatGPT web | connect/select private GitHub repo | GitHub connector + supported tools |
| Claude.ai | connect/add private repo/project | GitHub integration + supported tools |

A catalog repo is not automatically a native plugin for every client. The preferred compatibility order is **MCP → skill/plugin/instructions → CLI/API wrapper → direct library**.

Browser-hosted ChatGPT/Claude/Copilot cannot be forced by a shell script to execute every private-repo tool globally. Connect/select this repo so they can use the committed instructions and maintenance issue workflow.

## Core cross-agent additions

- **Omni:** `getomnico/omni`
- **Claude-Mem:** `thedotmack/claude-mem`
- **Headroom:** `headroomlabs-ai/headroom`
- **Task Observer / Agent Monitor:** `hoangsonww/Claude-Code-Agent-Monitor`
- **Claude Code setup:** `centminmod/my-claude-code-setup`, `anthropics/claude-plugins-official`, `CLAUDE.md`
- **GitHub Copilot:** `github/copilot-cli`, `github/copilot-sdk`, `github/awesome-copilot`, `github/github-mcp-server`
- **Codex:** `openai/codex`
- **Watermark remover:** `D-Ogi/WatermarkRemover-AI` — authorized media only

Lists: [repo-lists/ai-client-tools.txt](repo-lists/ai-client-tools.txt) · [repo-lists/github-copilot.txt](repo-lists/github-copilot.txt)

### Claude-Mem

```bash
npx claude-mem install
```

### Headroom

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

### Watermark remover

After the global setup:

```bash
master-watermark INPUT_FILE OUTPUT_FOLDER
```

On Windows you can also call:

```powershell
& "$HOME\bin\master-watermark.ps1" INPUT_FILE OUTPUT_FOLDER
```

## Token and work-spend limit — optional, separate setup

Token/spend limiting is **not** enabled by the large global one-liners.

Use the independent guide: **[docs/TOKEN-BUDGET.md](docs/TOKEN-BUDGET.md)**.

It covers context/output limits, work budgets, soft/hard caps, compression, and paid-primary → free/local fallback routing for compatible clients. Hosted subscription UIs cannot be silently rerouted by this repo; use their native usage controls for hosted requests.

## Security and intake guardian

Guardian: [scripts/catalog_guardian.py](scripts/catalog_guardian.py)

It checks for:

- Unicode bidirectional/invisible controls and hidden-text patterns;
- prompt/instruction injection indicators in agent/MCP content;
- suspicious download-and-execute, encoded PowerShell, base64/dynamic execution, and credential-exfiltration patterns;
- SQL-injection-style dynamic query construction and command-injection patterns;
- private keys/secrets;
- embedded PE/ELF executables and suspicious install behavior;
- repository deleted/disabled/archive/freshness state;
- external scanner findings when the tools are installed.

The security catalog includes Snyk CLI, Trivy, Semgrep, OpenGrep, OSV Scanner, Gitleaks, TruffleHog, Cisco AI Defense MCP Scanner, OSSF Scorecard, Syft, Cosign, and Garak. Guardian can also use ClamAV when installed.

Static scanners reduce risk but do not prove third-party code is safe. HIGH findings require review; confirmed CRITICAL findings are removal candidates.

New and flagged repos should be deep-vetted before use. See [docs/SECURITY-SCANNING.md](docs/SECURITY-SCANNING.md) and [docs/NEW-REPO-VETTING.md](docs/NEW-REPO-VETTING.md).

## Stale/archive decisions from the current review

The 2026-08-19 in-depth review made these important changes:

- `qiskit-community/qiskit-optimization` → replaced with `Qiskit/qiskit-addon-opt-mapper` because the upstream project is archived/unsupported despite recent code activity.
- `tastytrade/tastytrade-sdk-python` → removed from the active lane because upstream explicitly archived it; `tastyware/tastytrade` remains as an active unofficial Python alternative.
- `aarora79/aws-cost-explorer-mcp-server` → replaced by active `awslabs/mcp` billing/cost-management tooling.
- `alexgolec/schwab-py` → removed in favor of active `tylerebowers/Schwabdev`.
- `financial-datasets/mcp-server` → active-list removal + managed-adoption candidate.
- `nerfstudio-project/nerfstudio` → active-list removal + managed-adoption candidate; active 3D alternatives remain cataloged.
- `oyi77/Crypto-RL-Trading-Bot` → removed; no license was detected, so it is not a managed-adoption candidate.
- `FlowiseAI/Flowise` → retained only as transition/reference material because 3.1.4/recent activity does not cancel the explicit archive/sunset state.
- Prompt Compression Survey, IBM Quantum Challenge 2021, VSI-Bench `thinking-in-space`, RoboPoint, and compact-counter are retained as reference-only artifacts where appropriate.

Details: [docs/LIFECYCLE-REVIEW-2026-08-19.md](docs/LIFECYCLE-REVIEW-2026-08-19.md).

## Pull latest, but protect `main`

Everyone with read access can pull approved `main`:

```bash
git switch main && git pull --ff-only origin main
```

Contributors work on branches and PRs. The repo includes:

- `.github/CODEOWNERS` — `@Charlesganu2004` owns all files.
- `.github/workflows/owner-approval.yml` — checks for Charles's PR approval.

One-time GitHub server settings for `main`:

1. Require a pull request before merging.
2. Require at least 1 approval.
3. Require review from Code Owners.
4. Require **Owner Approval Check / owner-approval**.
5. Dismiss stale approvals when new commits arrive.
6. Require conversation resolution.
7. Block force pushes and branch deletion.
8. Restrict bypass/direct updates to `Charlesganu2004` only when necessary.

Those GitHub branch/ruleset settings are required for server-side enforcement; repository files alone cannot block an authorized direct push.

## Repo map

| Path | Purpose |
|---|---|
| `AGENTS.md` | portable cross-client contract |
| `CLAUDE.md` | Claude Code entrypoint |
| `.github/copilot-instructions.md` | GitHub Copilot repo instructions |
| `.github/CODEOWNERS` | owner review ownership |
| `.github/workflows/catalog-guardian.yml` | manual owner-requested guardian PR workflow |
| `.github/workflows/pages.yml` | interactive command-center deployment |
| `.github/workflows/owner-approval.yml` | PR owner-approval gate |
| `agents/` | specialist agents |
| `docs/` | setup, security, vetting, lifecycle, status, integration guides |
| `repo-lists/` | curated repositories grouped by lane |
| `managed-repos/` | candidate plans for owner-maintained replacements |
| `skills/` | portable skills/workflows |
| `plugins/` | plugin packages/docs |
| `scripts/` | setup, maintenance request, auditing, guardian helpers |
| `index.html` | click-to-copy interactive command center |
| `quantum/` | quantum-computing lane |
| `cost-reduction/` | cloud/token/cost lane |

## Update and verify

```bash
git -C "$HOME/Master-Repo-Use" pull --ff-only
python "$HOME/Master-Repo-Use/scripts/maintenance_request.py" --check
python "$HOME/Master-Repo-Use/scripts/check_freshness.py"
```

After major instruction changes, rerun the global setup script so copied user-level instruction blocks are refreshed.

Then ask your preferred client:

```text
What Master Repo instructions are loaded, and which catalog lane would you use for this task?
```

Copilot CLI: `/instructions` · Claude Code: `/memory` · Codex: root `AGENTS.md`.

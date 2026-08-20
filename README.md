# Master Repo Use

Private command center and curated catalog for agent frameworks, RAG, memory, MCP servers, token/context management, GitHub Copilot, Claude Code, Codex, Microsoft Copilot Studio, observability, finance/trading research, quantum computing, cloud/cost reduction, app templates, security tooling, and supporting developer tools.

Repository: `Charlesganu2004/Master-Repo-Use`

The Master Repo is the shared **catalog + instructions + security/vetting layer** used by your AI coding tools. Clone it once, keep it current, and let each client discover only the task-relevant repos, skills, MCP servers, and setup instructions when needed.

## Live catalog health

Once GitHub Pages is enabled, this visual refreshes when relevant catalog/site data changes on `main` or when the deployment is dispatched manually, without committing generated status changes to `main`:

![Master Repo live catalog health](https://charlesganu2004.github.io/Master-Repo-Use/docs/catalog-status.svg)

Until Pages is enabled, use the committed snapshot at [docs/catalog-status.svg](docs/catalog-status.svg).

Detailed private status remains in:

- [docs/CATALOG-STATUS.md](docs/CATALOG-STATUS.md)
- [docs/catalog-status.json](docs/catalog-status.json)
- [docs/LIFECYCLE-REVIEW-2026-08-19.md](docs/LIFECYCLE-REVIEW-2026-08-19.md)
- [managed-repos/README.md](managed-repos/README.md)

The public Pages artifact exposes **health counts only**, not the private repo-by-repo catalog JSON. Local mode shows the complete table.

Lifecycle rules:

- 🟢 **0–120 days since last push:** healthy from a freshness perspective.
- 🟡 **121–269 days:** stale warning.
- 🟠 **270–365 days:** replacement / managed-adoption review.
- 🔴 **>365 days:** remove from the active/runtime catalog unless an owner-approved reference/stability exception applies.
- **Archived + recent activity:** review releases, archive reason, sunset/EOL notice, successor, security, and reference value before deciding.
- **Static research/reference repos:** may receive a `reference` override when inactivity is expected.
- **Deleted/disabled or confirmed CRITICAL security finding:** immediate removal candidate.

A 3–4 month stale warning is intentional: it catches fast-moving AI tooling early without deleting useful software merely because it had a quiet quarter.

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

The global bootstrap installs a small instruction/pointer layer. It **does not install the entire third-party catalog into every machine or every prompt**.

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
- **Optional AI maintenance request:** `scripts/maintenance_request.py --auto` can create one owner-approval prompt when a task genuinely needs model judgment.
- **Global watermark command:** `master-watermark` on Bash platforms or `$HOME\bin\master-watermark.ps1` on Windows. The upstream tool is installed on first use, not during bootstrap.
- Existing personal instruction files are preserved; only the marked Master Repo block is managed.

Watermark removal is for media you own or are authorized to modify. Do not remove third-party attribution or rights-management marks without permission.

Full guide: [docs/GLOBAL-AI-SETUP.md](docs/GLOBAL-AI-SETUP.md).

## GitHub Copilot setup

The repository includes `.github/copilot-instructions.md`, so repo-aware Copilot sessions receive the Master Repo rules automatically.

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

Local mode can display the full private repo-by-repo health table.

### GitHub Pages mode

`.github/workflows/pages.yml` builds the command center from approved `main`. The public health visual refreshes when relevant catalog/site data changes or when the workflow is manually dispatched. Routine catalog metadata auditing runs weekly. Deep security maintenance runs only when required or owner-approved. There is no recurring Pages schedule, so the site costs Actions minutes only when something actually changed.

**One-time owner action:** open **Settings → Pages** and set **Source → GitHub Actions**.

After that, deploy immediately with:

```bash
gh workflow run pages.yml -R Charlesganu2004/Master-Repo-Use
```

The workflow now checks whether Pages is enabled before calling the Pages deployment actions. Until the one-time setting is enabled it exits successfully with a warning and skips deployment instead of repeatedly failing.

GitHub Pro allows Pages to use a private source repository, but a normal personal GitHub Pages site is public. For that reason this workflow publishes only `index.html` plus a sanitized count-only status payload/SVG. It does **not** publish the private catalog or detailed findings.

## GitHub Pro automatic audit — no paid AI background loop

GitHub Actions now handles the routine maintenance checks. GPT, Claude, Copilot, and Codex are **not** called in the background.

`.github/workflows/catalog-guardian.yml` runs:

- weekly;
- whenever catalog/security lifecycle files change;
- when you manually dispatch it.

The normal audit is metadata-only, so it stays lightweight. A newly added repo is immediately source-scanned. Existing expensive deep scans wait for your explicit approval.

Run an audit now:

```bash
gh workflow run catalog-guardian.yml -R Charlesganu2004/Master-Repo-Use
```

If anything needs attention, the workflow creates or refreshes one `[Catalog Audit]` GitHub issue as an audit trail. It does **not** change `main`.

### Approve deterministic maintenance

Comment this exact phrase on the open audit issue:

```text
APPROVE CATALOG MAINTENANCE
```

That owner comment triggers GitHub Actions to:

1. deep-scan the rotating batch and every current REVIEW/REMOVE candidate;
2. re-evaluate stale/archive/security state;
3. prepare removal/replacement/managed-adoption changes on `automation/catalog-guardian`;
4. open or refresh a PR;
5. close the audit issue with a link to the PR.

It still **does not merge `main`**.

One-time setting required for automatic PR creation: **Settings → Actions → General → Workflow permissions → Allow GitHub Actions to create and approve pull requests**. This permission lets the bot create the PR; it does not bypass your branch/Code Owner approval policy.

### Optional AI maintenance only when judgment is needed

For work that deterministic scanners cannot do safely—such as deciding how to modernize useful abandoned code—use:

```bash
python scripts/maintenance_request.py --auto
```

That creates an `[AI Maintenance]` request and stops. Approve model-assisted work with:

```text
APPROVE AI MAINTENANCE
```

The AI may then work in the active session and prepare a branch/PR. It still may not merge `main` without your approval.

## Cost control

GitHub Pro is a fixed subscription that includes **3,000 Actions minutes/month** on
Linux runners. Everything here runs on `ubuntu-latest` (1x multiplier), so routine use
lands around **20-40 minutes/month** and the metered bill stays at **$0**.

| Workflow | Trigger | Frequency |
|---|---|---|
| Pages | change to site/status files on `main`, or manual dispatch | **no recurring schedule** |
| Catalog Guardian (audit) | weekly cron, catalog changes, manual | 1x/week |
| Catalog Guardian (deep scan) | new repo added, flagged repo, owner approval | only when required |
| Owner approval check | pull request events | per PR |

- No recurring Pages deployment. The former six-hour cron was removed.
- No scheduled AI or model calls of any kind: not Claude, OpenAI, Copilot, Codex, or Gemini.
- No Codespaces requirement. No paid GitHub Models. No paid Snyk usage.
- Every job has `timeout-minutes`; every workflow has `concurrency`.

The gross figure GitHub displays is not the billed figure -- included usage is applied
first. The number that matters is the net billed amount.

Recommended one-time owner setup under **Settings -> Billing and licensing -> Budgets and
alerts**: included-usage alerts at **90%** and **100%**, plus an Actions-scoped budget of
**$1/month** with *Stop usage when budget limit is reached* enabled.

Full detail, including the rules any new workflow has to follow: [docs/COST-CONTROL.md](docs/COST-CONTROL.md).

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

Browser-hosted ChatGPT/Claude/Copilot cannot be forced by a shell script to execute every private-repo tool globally. Connect/select this repo so they can use the committed instructions and approved maintenance workflow.

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

Windows:

```powershell
& "$HOME\bin\master-watermark.ps1" INPUT_FILE OUTPUT_FOLDER
```

## Token and work-spend limit — optional, separate setup

Token/spend limiting is **not** enabled by the large global one-liners.

Use the independent guide: **[docs/TOKEN-BUDGET.md](docs/TOKEN-BUDGET.md)**.

It covers context/output limits, work budgets, soft/hard caps, compression, and paid-primary → free/local fallback routing for compatible clients. Hosted subscription UIs cannot be silently rerouted by this repo; use their native usage controls for hosted requests.

## Security and intake guardian

Guardian: [scripts/catalog_guardian.py](scripts/catalog_guardian.py)

The built-in source scanner checks for:

- Unicode bidirectional/invisible controls and hidden-text patterns;
- prompt/instruction injection indicators in agent/MCP content;
- suspicious download-and-execute, encoded PowerShell, base64/dynamic execution, and credential-exfiltration patterns;
- SQL-injection-style dynamic query construction and command-injection patterns;
- private keys/secrets;
- embedded PE/ELF executables;
- repository deleted/disabled/archive/freshness state.

When installed, Guardian can additionally consume Semgrep, Snyk CLI, Trivy, OSV Scanner, Gitleaks, and ClamAV findings. The security catalog also includes OpenGrep, TruffleHog, Cisco AI Defense MCP Scanner, OSSF Scorecard, Syft, Cosign, and Garak.

Static scanners reduce risk but cannot prove third-party code is safe. HIGH findings require review; confirmed CRITICAL findings are removal candidates.

The scanner preserves the latest expensive deep-scan state during lightweight metadata refreshes instead of erasing previous findings.

See [docs/SECURITY-SCANNING.md](docs/SECURITY-SCANNING.md) and [docs/NEW-REPO-VETTING.md](docs/NEW-REPO-VETTING.md).

## Current stale/archive decisions

The 2026-08-19 in-depth review made these changes:

- `qiskit-community/qiskit-optimization` → `Qiskit/qiskit-addon-opt-mapper`.
- `tastytrade/tastytrade-sdk-python` → removed from active lane; `tastyware/tastytrade` remains as the current Python alternative in this catalog.
- `aarora79/aws-cost-explorer-mcp-server` → replaced by active `awslabs/mcp` billing/cost-management tooling.
- `alexgolec/schwab-py` → removed in favor of `tylerebowers/Schwabdev`.
- `financial-datasets/mcp-server` → active-list removal + managed-adoption review.
- `nerfstudio-project/nerfstudio` → active-list removal + managed-adoption review; active 3D alternatives remain cataloged.
- `oyi77/Crypto-RL-Trading-Bot` → removed; no detected license means no automatic managed adoption.
- `FlowiseAI/Flowise` → retained temporarily as transition/reference material. Recent `3.1.4` activity is recorded, but the project’s explicit archive/sunset state means it is not treated as a newly maintained dependency.
- Prompt Compression Survey, IBM Quantum Challenge 2021, VSI-Bench `thinking-in-space`, RoboPoint, and compact-counter remain reference-only where appropriate.

Details: [docs/LIFECYCLE-REVIEW-2026-08-19.md](docs/LIFECYCLE-REVIEW-2026-08-19.md).

## Pull latest, but protect `main`

Everyone with read access can pull approved `main`:

```bash
git switch main && git pull --ff-only origin main
```

Contributors work on branches and PRs. The repo includes:

- `.github/CODEOWNERS` — `@Charlesganu2004` owns all files.
- `.github/workflows/owner-approval.yml` — checks for Charles’s PR approval.
- `scripts/branch-protection.json` — one-command GitHub server protection policy.

### One-line branch protection setup

Run once after cloning and authenticating `gh` as the repo owner:

```bash
gh api --method PUT -H "Accept: application/vnd.github+json" repos/Charlesganu2004/Master-Repo-Use/branches/main/protection --input "$HOME/Master-Repo-Use/scripts/branch-protection.json"
```

This requires PR review, requires Code Owner review, dismisses stale approvals, requires conversation resolution, and blocks force-push/deletion. `enforce_admins` is left off so the repository owner retains an emergency bypass.

The repository-side files alone cannot protect a branch; this GitHub server setting must be enabled once.

## Repo map

| Path | Purpose |
|---|---|
| `AGENTS.md` | portable cross-client contract |
| `CLAUDE.md` | Claude Code entrypoint |
| `.github/copilot-instructions.md` | GitHub Copilot repo instructions |
| `.github/CODEOWNERS` | owner review ownership |
| `.github/workflows/catalog-guardian.yml` | weekly/on-change audit + owner-comment maintenance workflow |
| `.github/workflows/pages.yml` | change-triggered/manual privacy-safe interactive deployment |
| `.github/workflows/owner-approval.yml` | PR owner-approval check |
| `agents/` | specialist agents |
| `docs/` | setup, security, vetting, lifecycle, status, integration guides |
| `repo-lists/` | curated repositories grouped by lane |
| `managed-repos/` | candidate plans for owner-maintained replacements |
| `skills/` | portable skills/workflows |
| `plugins/` | plugin packages/docs |
| `scripts/` | setup, maintenance, auditing, guardian, branch-protection helpers |
| `index.html` | click-to-copy interactive command center |
| `quantum/` | quantum-computing lane |
| `cost-reduction/` | cloud/token/cost lane |

## Update and verify

```bash
git -C "$HOME/Master-Repo-Use" pull --ff-only
python "$HOME/Master-Repo-Use/scripts/catalog_guardian.py"
python "$HOME/Master-Repo-Use/scripts/maintenance_request.py" --check
```

After major instruction changes, rerun the global setup script so copied user-level instruction blocks are refreshed.

Then ask your preferred client:

```text
What Master Repo instructions are loaded, and which catalog lane would you use for this task?
```

Copilot CLI: `/instructions` · Claude Code: `/memory` · Codex: root `AGENTS.md`.

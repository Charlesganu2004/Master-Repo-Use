# Master Repo Use

Private command center and curated catalog for agent frameworks, RAG, memory, MCP servers, token/context management, GitHub Copilot, Claude Code, Codex, Microsoft Copilot Studio, observability, finance/trading research, quantum computing, cloud/cost reduction, app templates, security tooling, and supporting developer tools.

Repository: `Charlesganu2004/Master-Repo-Use`

The Master Repo is the shared **catalog + instructions + security/vetting layer** used by your AI coding tools. Clone it once, keep it current, and let each client discover only the task-relevant repos, skills, MCP servers, and setup instructions when needed.

## Live catalog health

Under the approved cost-control Pages workflow, the visual refreshes when relevant catalog/site data changes on `main` or when deployment is dispatched manually; there is no recurring Pages timer:

![Master Repo live catalog health](https://charlesganu2004.github.io/Master-Repo-Use/docs/catalog-status.svg)

Detailed private status remains in:

- [docs/CATALOG-STATUS.md](docs/CATALOG-STATUS.md)
- [docs/catalog-status.json](docs/catalog-status.json)
- [docs/LIFECYCLE-REVIEW-2026-08-19.md](docs/LIFECYCLE-REVIEW-2026-08-19.md)
- [managed-repos/README.md](managed-repos/README.md)

The public Pages builder exposes **aggregate health information only**, not the private repo-by-repo catalog. Local mode shows the complete table.

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

`.github/workflows/pages.yml` in the cost-control change set builds the command center from approved `main`. The public health visual refreshes when relevant catalog/site data changes or when the workflow is manually dispatched. Routine catalog metadata auditing runs weekly. Deep security maintenance runs only when required or owner-approved. The desired workflow has no recurring Pages schedule.

Pages is configured through GitHub Actions. Deploy manually with:

```bash
gh workflow run pages.yml -R Charlesganu2004/Master-Repo-Use
```

The workflow checks whether Pages is enabled before calling deployment actions. If it is disabled, the job warns and skips deployment rather than repeatedly failing.

GitHub Pro allows Pages to use a private source repository, but a normal personal GitHub Pages site is public. The privacy-safe workflow therefore rebuilds `index.html` through `scripts/build_public_site.py`, strips `data-private` content, publishes a count-only status payload/SVG, and fails CI if catalog slugs/private findings reach the public artifact.

**Change-state warning:** until the cost-control PR is merged, the current `main` workflow may still contain the former six-hour schedule and verbatim `index.html` staging. Do not treat the branch-only privacy/cost fixes as permanently live until approved `main` contains them and a clean Pages deployment completes.

## GitHub Pro automatic audit — no paid AI background loop

GitHub Actions handles the routine maintenance checks. GPT, Claude, Copilot, and Codex are **not** called in the background.

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

One-time setting required for automatic PR creation: **Settings → Actions → General → Workflow permissions → Allow GitHub Actions to create and approve pull requests**. This permission lets the bot create the PR; it does not satisfy the separate `owner-approval` gate and does not let the bot merge protected `main`.

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

GitHub Pro is the fixed subscription; the repository is designed to keep routine Actions overage at **$0** by limiting recurring work and using included runner usage first.

| Workflow | Trigger | Frequency |
|---|---|---|
| Pages | relevant `main` change or manual dispatch | **no recurring schedule after merge of the cost-control workflow** |
| Catalog Guardian (audit) | weekly cron, catalog changes, manual | 1x/week plus real changes |
| Catalog Guardian (deep scan) | new repo added / owner-approved maintenance | only when required |
| Owner approval gate | PR/review/owner-comment events | event-driven only |
| Safety validation | relevant PR/main changes | event-driven only |

- No scheduled paid AI/model calls.
- No Codespaces requirement.
- Snyk is optional and only runs if deliberately configured.
- Jobs use timeouts and concurrency so stale/duplicate work cannot run indefinitely.

The GitHub billing UI can show **gross metered usage** even when included-usage discounts make the **billed/net amount $0**. The billed/net amount is what matters for actual overage.

Recommended one-time owner setup under **Settings → Billing and licensing → Budgets and alerts**: included-usage alerts such as **90%** and **100%**, plus an Actions-scoped small hard budget if available.

Full detail: [docs/COST-CONTROL.md](docs/COST-CONTROL.md).

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
- suspicious download-and-execute, encoded PowerShell, base64/dynamic execution, and credential-exfiltration patterns in both sink/secret orderings;
- SQL-injection-style dynamic query construction and command-injection patterns;
- private keys/secrets;
- embedded PE/ELF executables;
- repository deleted/disabled/archive/freshness state.

When installed, Guardian can additionally consume Semgrep, Snyk CLI, Trivy, OSV Scanner, Gitleaks, and ClamAV findings. External scanner stdout/stderr is not persisted as a finding: known result codes are classified, unknown/failure codes fail closed as `SCANNER-ERROR`, and Gitleaks persists redacted metadata only.

Static scanners reduce risk but cannot prove third-party code is safe. HIGH findings require review; confirmed CRITICAL findings are removal candidates. Scanner infrastructure failures are rescan signals, not accusations against the repository.

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

- `.github/CODEOWNERS` — documents `@Charlesganu2004` as owner of all files.
- `.github/workflows/owner-approval.yml` — trusted owner gate that never executes PR-head code.
- `scripts/owner_approval.py` — verifies approval against the **current PR head SHA**.
- `scripts/branch-protection.json` — one-command GitHub server protection policy.

The owner gate supports two paths:

- **PR authored by an agent/bot/other user:** Charles must submit a normal GitHub `APPROVED` review whose `commit_id` matches the current PR head SHA.
- **PR authored by Charles:** because GitHub does not permit self-approval reviews, Charles must add the exact PR conversation comment `APPROVE OWNER PR <CURRENT_HEAD_SHA>`. A new commit changes the SHA and invalidates the old approval automatically.

The desired GitHub server review count is `0` and Code Owner review is not a separate required-review rule. The **required `owner-approval` status check is the authoritative Charles gate** and itself enforces Charles review for non-owner-authored PRs. This avoids the self-authored-PR deadlock without allowing agents to approve themselves.

### One-line branch protection setup

Run after cloning and authenticating `gh` as the repo owner, and rerun after this protection policy changes:

```bash
gh api --method PUT -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" repos/Charlesganu2004/Master-Repo-Use/branches/main/protection --input "$HOME/Master-Repo-Use/scripts/branch-protection.json"
```

This requires pull requests and the SHA-bound `owner-approval` status, requires conversation resolution, and blocks force-push/deletion. `enforce_admins` is left off so the repository owner retains an emergency recovery bypass.

The repository-side file describes the desired policy; the GitHub server setting must be applied after policy changes. See [docs/GITHUB-PRO-SETUP.md](docs/GITHUB-PRO-SETUP.md) for the bootstrap case where a PR is changing the approval policy itself.

## Repo map

| Path | Purpose |
|---|---|
| `AGENTS.md` | portable cross-client contract |
| `CLAUDE.md` | Claude Code entrypoint |
| `.github/copilot-instructions.md` | GitHub Copilot repo instructions |
| `.github/CODEOWNERS` | owner metadata |
| `.github/workflows/catalog-guardian.yml` | weekly/on-change audit + owner-comment maintenance workflow |
| `.github/workflows/pages.yml` | change-triggered/manual privacy-safe interactive deployment |
| `.github/workflows/owner-approval.yml` | trusted SHA-bound PR owner-approval gate |
| `.github/workflows/safety-tests.yml` | assertion-based scanner/approval/privacy CI |
| `scripts/owner_approval.py` | owner-approval evaluator/status publisher |
| `scripts/catalog_security.py` | fail-closed scanner/redaction helpers |
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
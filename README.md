# Master Repo Use

Private command center and curated catalog for agent frameworks, RAG, memory, MCP servers, token/context management, GitHub Copilot, Claude Code, Codex, Microsoft Copilot Studio, observability, finance/trading research, quantum computing, cloud/cost reduction, app templates, security tooling, and supporting developer tools.

Repository: `Charlesganu2004/Master-Repo-Use`

The Master Repo is the shared **catalog + instructions + security/vetting layer** used by your AI coding tools. Clone it once, keep it current, and let each client discover only the task-relevant repos, skills, MCP servers, and setup instructions when needed.

## Setup site — start here

**<https://charlesganu2004.github.io/Master-Repo-Use/>**

The public command center is the fastest way to get set up. Nothing needs to be installed to
read it, and every command card is click-to-copy:

| Tab | What it gives you |
|---|---|
| **Setup** | One-liner global install for Claude Code, Codex, Copilot and Gemini |
| **Use It** | Six systems — instruction files, skills, local models, MCP, agent subgroups, security — each with the one-liner that starts it and the point where it hands back to you |
| **Local Models** | Move a slider to your RAM and OS; 36 models re-sized live, plus an install checker that answers "can this machine run it" before you download |
| **ADKs** | Which agent development kit to pick, and when an ADK is overkill |
| **System Map** | 20 clickable nodes across all five layers, from client to model |
| **Design** | The libraries and skill packs behind the interface |
| **Health & Security** | Aggregate catalog health and deep-scan coverage |
| **Access & Deploy** | Branch protection, Pages, cost controls |

There is a **light/dark toggle** in the top bar and a **build stamp** next to it.

**If the site looks unchanged after a deploy, it is your browser, not the deploy.** GitHub Pages
serves `index.html` with a cache lifetime, and browsers will keep showing the cached copy through
an ordinary refresh. The page now detects this itself: it compares its baked-in build id against
`version.json` fetched with `cache: 'no-store'`, and shows a **"a newer version was deployed"**
banner with a reload button that navigates to a fresh URL. If you ever want to force it manually,
`Ctrl+Shift+R` (`Cmd+Shift+R` on macOS).

The public site shows **aggregate health only**. Repo-by-repo detail requires a local clone —
see [Local/private mode](#localprivate-mode).

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

Sections:

- **Setup** — global and per-client installation.
- **Maintenance** — run an audit, approve deterministic maintenance.
- **Tools** *(private only)* — Claude-Mem, Headroom, Omni, Task Observer.
- **Local Models** — the hardware advisor. Pick your RAM and OS; it re-derives every fit
  decision live from the published formula in [docs/hardware-profiles.json](docs/hardware-profiles.json).
  At 4 GB on Windows it tells you the truth: nothing fits, use hosted.
- **ADKs** — Google ADK, Microsoft Agent Framework, OpenAI Agents SDK, and the AutoGen
  supersession. See [docs/ADK-GUIDE.md](docs/ADK-GUIDE.md).
- **System Map** — 20 clickable nodes across clients, instruction layer, catalog,
  automations and runtimes, plus subgroup recipes.
- **Design** — three.js and GSAP as load-bearing libraries, skill packs as advisory only.
- **Health & Security** and **Access & Deploy** — as before.

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

`.github/workflows/pages.yml` builds the command center from approved `main`. The public health visual refreshes when relevant catalog/site data changes or when the workflow is manually dispatched. Routine catalog metadata auditing runs weekly. Deep security maintenance runs only when required or owner-approved. The desired workflow has no recurring Pages schedule.

Pages is configured through GitHub Actions. Deploy manually with:

```bash
gh workflow run pages.yml -R Charlesganu2004/Master-Repo-Use
```

The workflow checks whether Pages is enabled before calling deployment actions. If it is disabled, the job warns and skips deployment rather than repeatedly failing.

GitHub Pro allows Pages to use a private source repository, but a normal personal GitHub Pages site is public. The privacy-safe workflow therefore rebuilds `index.html` through `scripts/build_public_site.py`, strips private-flagged content, publishes a count-only status payload/SVG plus the hardware-advisor dataset, and fails CI if catalog slugs or private findings reach the public artifact. The advisor dataset is allowed to name repositories only because every slug in it is on the owner-controlled [public allowlist](repo-lists/public-allowlist.txt); an unlisted slug fails the build.

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
| Pages | relevant `main` change or manual dispatch | **no recurring schedule** |
| Catalog Guardian (audit) | weekly cron, catalog changes, manual | 1x/week plus real changes |
| Catalog Guardian (deep scan) | new repo added / owner-approved maintenance | only when required |
| Owner approval gate | PR/review/owner-comment events | event-driven only |
| Safety validation | relevant PR/main changes | event-driven only |

- No scheduled paid AI/model calls.
- No Codespaces requirement.
- Snyk is optional and only runs if deliberately configured.
- Jobs use timeouts and concurrency so stale/duplicate work cannot run indefinitely.

The GitHub billing UI can show **gross metered usage** even when included-usage discounts make the **billed/net amount $0**. The billed/net amount is what matters for actual overage.

**Measured, August 2026.** Actions minutes on this private repository, computed from real job
durations (the `/actions/runs/{id}/timing` endpoint reports zeros and is unreliable — sum
`started_at`/`completed_at` from the `jobs` endpoint instead):

| Workflow | Billed minutes |
|---|---:|
| Catalog Guardian | 47 |
| Pages deploy | 29 |
| Safety Validation | 23 |
| Catalog freshness + owner approval | 5 |
| **Total** | **104 min ≈ $0.60–0.83 gross** |

GitHub Pro includes **3,000** Actions minutes per month, so that is ~3% of the allowance and the
net charge is **$0**. Most of August's total came from a single heavy development day (23 Safety
Validation runs in about an hour), not from steady-state operation. Actions is free on public
repositories; this repository is private by design, so its minutes are metered.

Reading your own numbers:

```bash
gh api "repos/Charlesganu2004/Master-Repo-Use/actions/runs?per_page=100" --jq '.workflow_runs[] | select(.created_at >= "2026-08-01") | .id'
```

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
| Gemini CLI | `GEMINI.md` + `~/.gemini/GEMINI.md` | MCP → skills/extensions → CLI/API → library |
| Gemini Code Assist | `.gemini/config.yaml` + `.gemini/styleguide.md` | automated PR review only |
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

## Security scanning — read this if you assumed it was already running

Deep scanning existed in this repository long before it ever ran. On 2026-08-25 an audit of the
scanner itself found:

**0 of 252 catalogued repositories had ever been deep-scanned.**

Not "scanned and clean" — never scanned. Three separate things caused it, and each one alone
would have been enough:

1. The weekly Catalog Guardian job was **metadata only**. It checked push dates and archive
   flags. It never passed `--deep`.
2. The scanner install step was gated on `if: steps.additions.outputs.repos != ''`, so on a
   scheduled run it was **skipped entirely**. No Semgrep, no Gitleaks, no OSV, no ClamAV.
3. `--deep` ran only inside the owner-approved maintenance job, behind a manual
   `APPROVE CATALOG MAINTENANCE` comment that had never been given at scale. And when new repos
   *were* added, the install crashed: `go install github.com/gitleaks/gitleaks/v8@latest` fails
   because that module still declares its path as `github.com/zricethezav/gitleaks/v8`.

Nothing was hiding a finding. There was simply **no scan to produce one**, and an empty findings
list looked exactly like a clean bill of health.

### What changed

- **A rotating deep scan now runs on the weekly schedule**, read-only, with no approval gate.
  Reporting a risk should never wait on a human; only *changing* the catalog stays owner-gated.
  About 19 repos per run, full coverage in roughly 13 weeks.
- **Scanner installs are non-fatal.** A broken installer degrades the run to `SCANNER-ERROR`
  instead of killing it — which is what took the whole audit down on 2026-08-25.
- **Coverage is displayed**, on the Health & Security tab and in a `[Security Scan]` issue, so
  "never scanned" can never again be mistaken for "scanned and clean".
- **`SCANNER-ERROR` means unverified**, never clean and never flagged. Those repos stay in the
  rotation.

What is scanned: malware (ClamAV), secrets (Gitleaks, `--redact`, values never printed), known
vulnerabilities (OSV), code patterns (Semgrep), plus built-in checks for invisible/bidi
characters, prompt injection, SQL injection and suspicious execution patterns.

Run the same checks over any working tree yourself:

```bash
python scripts/static_audit.py .
```

Detail: [docs/SECURITY-SCANNING.md](docs/SECURITY-SCANNING.md).

## Local models and hardware fit

Which models run on your machine, from three vendors only: **Microsoft**, **Google/Gemini**, and
**Ollama**. General training and serving stacks stay in
[repo-lists/llm-models-serving.txt](repo-lists/llm-models-serving.txt) &mdash; llama.cpp, vLLM, SGLang,
plus `NVIDIA/Megatron-LM` (large-scale training), `OptimalScale/LMFlow` (finetuning toolkit) and
`openai/parameter-golf` (the smallest-LM-in-16MB challenge, and a genuinely useful way to think
about the size/quality tradeoff). `Stability-AI/StableLM` is catalogued as a **historical
reference only** &mdash; its last push was April 2024.

**36 models**, at least three from every vendor at every tier from 8 GB up:

| RAM | Verdict | Models that fit | Microsoft | Google | Ollama |
|---:|---|---:|---:|---:|---:|
| 4 GB | severely constrained — sub-1B only | 8 | 1 | 3 | 4 |
| 6 GB | tiny to small | 18 | 5 | 6 | 7 |
| 8 GB | first comfortable tier | 22 | 5 | 7 | 10 |
| 12 GB | comfortable small / tight mid | 25 | 5 | 9 | 11 |
| 16 GB | solid daily driver | 30 | 8 | 9 | 13 |
| 24 GB | strong | 34 | 8 | 11 | 15 |
| 32 GB | excellent | 36 | 8 | 11 | 17 |

At 4 GB, Microsoft's only entry is BitNet (1.58-bit weights) — it publishes no sub-1B open model.
Microsoft's open-weight ceiling is 14B and Google's is 27B, so the largest options at 32 GB come
from the wider Ollama library.

Figures are **computed, not benchmarked**, from a formula published in
[docs/LOCAL-MODEL-HARDWARE.md](docs/LOCAL-MODEL-HARDWARE.md); `tests/test_hardware_profiles.py`
re-derives every minimum and fails if the data drifts. Interactive version: the **Local Models**
tab on the [setup site](https://charlesganu2004.github.io/Master-Repo-Use/).

Tag names could not be verified automatically when this data was written, so the repo ships a
checker instead of an assurance — it already caught one tag that does not exist:

```bash
python scripts/verify_model_tags.py
```

Both the dataset and the guide are generated, so tables cannot drift from data:
`scripts/generate_hardware_profiles.py` then `scripts/generate_hardware_doc.py`.

Catalog lane: [repo-lists/local-models.txt](repo-lists/local-models.txt)

> **Licensing:** Gemma ships under the Gemma Terms of Use, not an OSI licence. Phi and BitNet are MIT.

## Agent development kits

First-party, vendor-maintained agent frameworks — the supported successors to the earlier
community stacks. `microsoft/agent-framework` is the announced AutoGen + Semantic Kernel merger.

Guide: [docs/ADK-GUIDE.md](docs/ADK-GUIDE.md) · Lane: [repo-lists/adk-agent-kits.txt](repo-lists/adk-agent-kits.txt)

All three kits speak MCP, so keep tools in MCP servers rather than in the framework — the
cheapest hedge against picking the wrong one.

## Gemini

Two Gemini surfaces touch this repository and they have different jobs:

| Surface | Reads | Job |
|---|---|---|
| Gemini CLI | [GEMINI.md](GEMINI.md) | interactive local work |
| Gemini Code Assist | [.gemini/config.yaml](.gemini/config.yaml), [.gemini/styleguide.md](.gemini/styleguide.md) | automated PR review |

The style guide tells Code Assist what is deliberately out of scope (curation decisions in
`repo-lists/`, dense single-file HTML, markdown prose style) so reviews stay signal. **Gemini has
no authority in the approval gate**; only Charles approves, with the exact phrase.

The global setup scripts install the Gemini pointer alongside Claude, Codex and Copilot.

## Design, motion and 3D

- **Libraries (load-bearing):** `mrdoob/three.js`, `greensock/GSAP` — GSAP is not OSI-licensed.
- **Design systems:** `zanwei/design-dna` (turns a reference UI into quantified design-token
  JSON), `creativetimofficial/ui` (components and blocks exposed through a registry and MCP).
- **UI over MCP:** `MCP-UI-Org/mcp-ui` (protocol + SDK for interactive MCP responses),
  `Jpisnice/shadcn-ui-mcp-server` (gives an LLM real shadcn/ui component context).
- **Skill packs (advisory only):** motion-design, apple-design, genjutsu. These are instruction
  files, not dependencies: small, young, community-run, with near-identical forks. Read one
  end-to-end before pointing an agent at it.

Lane: [repo-lists/design-ui-motion.txt](repo-lists/design-ui-motion.txt)

## Local MCP servers, skill collections and self-hosted apps

Three lanes added 2026-08-27, every slug verified against the GitHub API:

- [repo-lists/mcp-local-servers.txt](repo-lists/mcp-local-servers.txt) — Context7, Chrome
  DevTools, Playwright, Blender, Graphiti, Cognee, Atlassian, Firecrawl, Exa, Cloudflare,
  mermaid, and the `modelcontextprotocol/servers` collection that actually contains the
  filesystem/SQLite/sequential-thinking servers.
- [repo-lists/agent-skill-collections.txt](repo-lists/agent-skill-collections.txt) — the large
  community skill libraries. **Advisory only:** a skill pack silently changes how an agent
  decides things, so read one end-to-end before pointing an agent at it.
- [repo-lists/self-hosted-apps.txt](repo-lists/self-hosted-apps.txt) — Coolify, Penpot, Immich,
  Vaultwarden, RustDesk and friends. **Mostly AGPL-3.0**: fine to run, fine to link, *not* fine
  to copy into a repository you intend to keep closed.

Five entries from the source list had been **renamed upstream** and are corrected here:
`mindsdb/mindsdb`→`mindsdb/mindshub`, `mendableai/…`→`firecrawl/firecrawl-mcp-server`,
`calcom/cal.com`→`calcom/cal.diy`, `AmruthPillai/Reactive-Resume`→`amruthpillai/reactive-resume`,
`sickn33/antigravity-awesome-skills`→`sickn33/agentic-awesome-skills`. Three more do not exist on
GitHub at all (they were marketplace listings, not repositories) and were dropped.

## Managed adoption — what can and cannot be absorbed

Adopting an abandoned repository is a **licensing** question before it is an engineering one.
A repository with no licence is not open source: copyright defaults to all rights reserved, so
copying its code into a repository you own is infringement no matter how abandoned it looks.

The 2026-08-27 licence audit of 29 stale/review candidates:

| Licence | Count | Adoption |
|---|---:|---|
| MIT / Apache-2.0 / CC0 | 18 | permitted with attribution |
| **No licence at all** | **7** | **forbidden** |
| AGPL-3.0 | 1 | permitted, obligations follow the code |
| NOASSERTION (custom) | 3 | read the actual LICENSE file first |

Seven entries were **delisted, not adopted** — six were 1–21 star personal projects with no
licence and nothing distinctive; the seventh (`aitrados/finance-trading-ai-agents-mcp`, 64
stars) had real reach but is still legally unusable.

Recommended adoption: **`langchain-ai/open_deep_research`** (MIT, 12.7k stars, archived) — worth
taking for its planner → parallel searchers → synthesiser loop, not for its codebase.

Explicitly **not** adopted: **`FlowiseAI/Flowise`**. It is a 55k-star product under a custom
restricted licence reaching EOL on 2026-08-31 — "take what we can" is not a meaningful operation
on it. Replace with `langflow-ai/langflow` instead.

Nothing has been copied. Adoption stays owner-gated, and when approved it happens on a branch
with upstream `LICENSE`/`NOTICE` preserved and an `ATTRIBUTION.md` recording the source commit.

Full reasoning: [docs/MANAGED-ADOPTION-PLAN.md](docs/MANAGED-ADOPTION-PLAN.md).

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

The 2026-08-25 triage resolved the open `[Catalog Audit]` issue and cut items needing attention
from 44 to 27 (REVIEW 16 → 4, REMOVE 1 → 0) while adding 21 repositories:

- Removed: `marcozanetti-dev/intraday-mean-reversion-costs-aware` (deleted upstream, HTTP 404),
  `phildougherty/infracost_mcp` and `bradygaster/CustomAgent` (both superseded by first-party
  entries already catalogued).
- Transferred: `geekan/MetaGPT` → `FoundationAgents/MetaGPT`. It only looked stale because the
  catalog pointed at the pre-transfer namespace.
- Superseded: `microsoft/autogen` → `microsoft/agent-framework`; `coinbase/cdp-sdk-python` →
  `coinbase/cdp-sdk`; `FlowiseAI/Flowise` → `langflow-ai/langflow`.
- **Flowise correction:** its `3.1.4` release on 2026-07-29 was the *final sunset* release, not
  evidence of maintenance. Feature freeze 2026-07-27, archived 2026-08-10, EOL 2026-08-31. A
  recent release does not imply a maintained project — check the `archived` flag.

Details: [docs/CATALOG-TRIAGE-2026-08-25.md](docs/CATALOG-TRIAGE-2026-08-25.md) ·
[docs/LIFECYCLE-REVIEW-2026-08-19.md](docs/LIFECYCLE-REVIEW-2026-08-19.md).

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
| `GEMINI.md` | Gemini CLI entrypoint |
| `.gemini/` | Gemini Code Assist review config and style guide |
| `docs/hardware-profiles.json` | hardware advisor dataset (formula + tiers + models) |
| `docs/LOCAL-MODEL-HARDWARE.md` | local model sizing guide |
| `docs/ADK-GUIDE.md` | agent development kit comparison |
| `docs/CATALOG-TRIAGE-2026-08-25.md` | lifecycle triage resolving the open catalog audit |
| `repo-lists/public-allowlist.txt` | owner-controlled slugs permitted on the public site |
| `scripts/catalog_freshness_gate.py` | annotates how stale the committed catalog metadata is |
| `scripts/security_report.py` | publishes deep-scan coverage and findings to a `[Security Scan]` issue |
| `scripts/verify_model_tags.py` | checks every model tag in the advisor actually resolves |
| `scripts/generate_hardware_profiles.py` | regenerates the advisor dataset from the sizing formula |
| `scripts/generate_hardware_doc.py` | regenerates `docs/LOCAL-MODEL-HARDWARE.md` from that dataset |
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
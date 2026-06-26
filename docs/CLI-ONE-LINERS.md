# CLI One-Liners

These commands are built for different computers. Most of them ask where you want files to go instead of assuming a fixed path.

## Path Prompt Pattern

PowerShell path prompt:

```powershell
$TargetPath = Read-Host "Where should this go? Enter a full folder path"; New-Item -ItemType Directory -Force $TargetPath | Out-Null
```

WSL/Bash path prompt:

```bash
read -rp "Where should this go? Enter a full folder path: " target_path; mkdir -p "$target_path"
```

Placeholder style:

```text
Replace <PATH_YOU_CHOOSE> with the folder where you want the files.
```

## Clone This Master Repo

PowerShell:

```powershell
$RepoPath = Read-Host "Where should Master-Repo-Use be cloned? Example: C:\Users\You\Source\Master-Repo-Use"; git clone https://github.com/Charlesganu2004/Master-Repo-Use.git $RepoPath; Set-Location $RepoPath
```

WSL/Bash:

```bash
read -rp "Where should Master-Repo-Use be cloned? Example: /path/you/choose/Master-Repo-Use: " repo_path; git clone https://github.com/Charlesganu2004/Master-Repo-Use.git "$repo_path" && cd "$repo_path"
```

GitHub CLI:

```bash
read -rp "Where should Master-Repo-Use be cloned? " repo_path; gh repo clone Charlesganu2004/Master-Repo-Use "$repo_path" && cd "$repo_path"
```

Open an existing copy, PowerShell:

```powershell
$RepoPath = Read-Host "Where is Master-Repo-Use on this computer?"; Set-Location $RepoPath; code $RepoPath
```

Open an existing copy, WSL/Bash:

```bash
read -rp "Where is Master-Repo-Use on this computer? " repo_path; cd "$repo_path"; code "$repo_path"
```

## Choose A Lab Folder

Use one folder for cloned experiments so the master repo stays clean.

PowerShell:

```powershell
$LabRoot = Read-Host "Where should cloned experiment repos go?"; New-Item -ItemType Directory -Force $LabRoot | Out-Null; Set-Location $LabRoot
```

WSL/Bash:

```bash
read -rp "Where should cloned experiment repos go? " lab_root; mkdir -p "$lab_root"; cd "$lab_root"
```

## Clone All Curated Repos

PowerShell with GitHub CLI:

```powershell
$MasterRepo = (Get-Location).Path  # run from repo root; $LabRoot = Read-Host "Folder where all repos should be cloned"; New-Item -ItemType Directory -Force $LabRoot | Out-Null; Get-Content (Join-Path $MasterRepo "repo-lists\all-curated.txt") | Where-Object { $_ -and $_ -notmatch '^#' } | ForEach-Object { gh repo clone $_ (Join-Path $LabRoot ($_ -replace '/','-')) }
```

PowerShell with plain Git:

```powershell
$MasterRepo = (Get-Location).Path  # run from repo root; $LabRoot = Read-Host "Folder where all repos should be cloned"; New-Item -ItemType Directory -Force $LabRoot | Out-Null; Get-Content (Join-Path $MasterRepo "repo-lists\all-curated.txt") | Where-Object { $_ -and $_ -notmatch '^#' } | ForEach-Object { git clone "https://github.com/$_.git" (Join-Path $LabRoot ($_ -replace '/','-')) }
```

WSL/Bash with GitHub CLI:

```bash
read -rp "Path to Master-Repo-Use: " master_repo; read -rp "Folder where all repos should be cloned: " lab_root; mkdir -p "$lab_root"; grep -vE '^(#|$)' "$master_repo/repo-lists/all-curated.txt" | while read -r repo; do gh repo clone "$repo" "$lab_root/${repo/\//-}"; done
```

WSL/Bash with plain Git:

```bash
read -rp "Path to Master-Repo-Use: " master_repo; read -rp "Folder where all repos should be cloned: " lab_root; mkdir -p "$lab_root"; grep -vE '^(#|$)' "$master_repo/repo-lists/all-curated.txt" | while read -r repo; do git clone "https://github.com/$repo.git" "$lab_root/${repo/\//-}"; done
```

## Clone One Category

PowerShell reusable category clone:

```powershell
$MasterRepo = (Get-Location).Path  # run from repo root; $ListName = Read-Host "Repo list file name, for example quantum-computing.txt"; $LabRoot = Read-Host "Folder where this category should be cloned"; New-Item -ItemType Directory -Force $LabRoot | Out-Null; Get-Content (Join-Path $MasterRepo "repo-lists\$ListName") | Where-Object { $_ -and $_ -notmatch '^#' } | ForEach-Object { gh repo clone $_ (Join-Path $LabRoot ($_ -replace '/','-')) }
```

WSL/Bash reusable category clone:

```bash
read -rp "Path to Master-Repo-Use: " master_repo; read -rp "Repo list file name, for example quantum-computing.txt: " list_name; read -rp "Folder where this category should be cloned: " lab_root; mkdir -p "$lab_root"; grep -vE '^(#|$)' "$master_repo/repo-lists/$list_name" | while read -r repo; do gh repo clone "$repo" "$lab_root/${repo/\//-}"; done
```

Category list names:

```text
agent-frameworks.txt
rag-knowledge-memory.txt
context-token-management.txt
app-mobile-structure.txt
cloud-aspire-samples.txt
hackathon-pitch-slides.txt
mcp-servers-extended.txt
copilot-studio-integration.txt
quantum-computing.txt
quantum-finance-trading.txt
finance-trading-market.txt
autonomous-day-trading-agents.txt
day-trading-bots.txt
broker-app-integrations.txt
trading-agent-risk-tools.txt
cost-reduction.txt
article-discoveries.txt
```

## Standalone Installs

Agent framework CLIs:

```powershell
npm install -g @github/copilot @bradygaster/squad-cli @microsoft/m365agentstoolkit-cli
```

Python agent and compression packages:

```powershell
python -m pip install --user runagent llmlingua
```

RAG and memory packages:

```powershell
npm install -g @agentmemory/agentmemory; npm install @upstash/vector; pnpm add @upstash/rag-chat
```

Quantum lab, PowerShell:

```powershell
$LabPath = Read-Host "Where should the quantum lab be created?"; New-Item -ItemType Directory -Force $LabPath | Out-Null; Set-Location $LabPath; python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install --upgrade pip qiskit qiskit-finance qiskit-optimization pennylane matplotlib pandas
```

Quantum lab, WSL/Bash:

```bash
read -rp "Where should the quantum lab be created? " lab_path; mkdir -p "$lab_path"; cd "$lab_path"; python3 -m venv .venv && source .venv/bin/activate && python -m pip install --upgrade pip qiskit qiskit-finance qiskit-optimization pennylane matplotlib pandas
```

Finance research lab, PowerShell:

```powershell
$LabPath = Read-Host "Where should the finance research lab be created?"; New-Item -ItemType Directory -Force $LabPath | Out-Null; Set-Location $LabPath; python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install --upgrade pip openbb yfinance mplfinance ta pandas numpy
```

Finance research lab, WSL/Bash:

```bash
read -rp "Where should the finance research lab be created? " lab_path; mkdir -p "$lab_path"; cd "$lab_path"; python3 -m venv .venv && source .venv/bin/activate && python -m pip install --upgrade pip openbb yfinance mplfinance ta pandas numpy
```

Quantum trading plugin, PowerShell:

```powershell
$PluginPath = Read-Host "Path to plugins\quantum-trading-agent"; Set-Location $PluginPath; python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install --upgrade pip; python -m pip install -e .; quantum-trading-agent smoke-test --risk risk_limits.example.json
```

Quantum trading plugin, WSL/Bash:

```bash
read -rp "Path to plugins/quantum-trading-agent: " plugin_path; cd "$plugin_path"; python3 -m venv .venv && source .venv/bin/activate && python -m pip install --upgrade pip && python -m pip install -e . && quantum-trading-agent smoke-test --risk risk_limits.example.json
```

Robinhood trading plugin, PowerShell:

```powershell
$PluginPath = Read-Host "Path to plugins\robinhood-trading-agent"; Set-Location $PluginPath; python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install --upgrade pip; python -m pip install -e .; robinhood-trading-agent smoke-test --risk risk_limits.example.json
```

Robinhood trading plugin, WSL/Bash:

```bash
read -rp "Path to plugins/robinhood-trading-agent: " plugin_path; cd "$plugin_path"; python3 -m venv .venv && source .venv/bin/activate && python -m pip install --upgrade pip && python -m pip install -e . && robinhood-trading-agent smoke-test --risk risk_limits.example.json
```

Autonomous day-trading plugin, PowerShell:

```powershell
$PluginPath = Read-Host "Path to plugins\autonomous-day-trading-agent"; Set-Location $PluginPath; python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install --upgrade pip; python -m pip install -e .; autonomous-day-trading-agent smoke-test --risk risk_limits.example.json
```

Autonomous day-trading plugin, WSL/Bash:

```bash
read -rp "Path to plugins/autonomous-day-trading-agent: " plugin_path; cd "$plugin_path"; python3 -m venv .venv && source .venv/bin/activate && python -m pip install --upgrade pip && python -m pip install -e . && autonomous-day-trading-agent smoke-test --risk risk_limits.example.json
```

Autonomous investing allocation proposal, PowerShell:

```powershell
$PluginPath = Read-Host "Path to plugins\autonomous-day-trading-agent"; Set-Location $PluginPath; autonomous-day-trading-agent invest-plan --capital 1000 --symbols SPY,QQQ,AAPL --risk risk_limits.example.json
```

Clone day-trading repos, PowerShell:

```powershell
$MasterRepo = (Get-Location).Path  # run from repo root; $LanePath = Read-Host "Folder where day-trading repos should be cloned"; New-Item -ItemType Directory -Force $LanePath | Out-Null; Get-Content (Join-Path $MasterRepo "repo-lists\day-trading-bots.txt") | Where-Object { $_ -and $_ -notmatch '^#' } | ForEach-Object { git clone "https://github.com/$_.git" (Join-Path $LanePath ($_ -replace '/','-')) }
```

Clone autonomous day-trading agent repos, PowerShell:

```powershell
$MasterRepo = (Get-Location).Path  # run from repo root; $LanePath = Read-Host "Folder where autonomous day-trading repos should be cloned"; New-Item -ItemType Directory -Force $LanePath | Out-Null; Get-Content (Join-Path $MasterRepo "repo-lists\autonomous-day-trading-agents.txt") | Where-Object { $_ -and $_ -notmatch '^#' } | ForEach-Object { git clone "https://github.com/$_.git" (Join-Path $LanePath ($_ -replace '/','-')) }
```

Clone autonomous day-trading agent repos, WSL/Bash:

```bash
read -rp "Path to Master-Repo-Use: " master_repo; read -rp "Folder where autonomous day-trading repos should be cloned: " lane_path; mkdir -p "$lane_path"; grep -vE '^(#|$)' "$master_repo/repo-lists/autonomous-day-trading-agents.txt" | while read -r repo; do git clone "https://github.com/$repo.git" "$lane_path/${repo/\//-}"; done
```

Clone broker app integration repos, PowerShell:

```powershell
$MasterRepo = (Get-Location).Path  # run from repo root; $LanePath = Read-Host "Folder where broker integration repos should be cloned"; New-Item -ItemType Directory -Force $LanePath | Out-Null; Get-Content (Join-Path $MasterRepo "repo-lists\broker-app-integrations.txt") | Where-Object { $_ -and $_ -notmatch '^#' } | ForEach-Object { git clone "https://github.com/$_.git" (Join-Path $LanePath ($_ -replace '/','-')) }
```

Clone quantum-finance trading repos, WSL/Bash:

```bash
read -rp "Path to Master-Repo-Use: " master_repo; read -rp "Folder where quantum-finance trading repos should be cloned: " lane_path; mkdir -p "$lane_path"; grep -vE '^(#|$)' "$master_repo/repo-lists/quantum-finance-trading.txt" | while read -r repo; do git clone "https://github.com/$repo.git" "$lane_path/${repo/\//-}"; done
```

Pitch deck standalone:

```bash
read -rp "Where should the Slidev deck be created? " deck_path; mkdir -p "$deck_path"; cd "$deck_path"; npm init slidev
```

Cloud/API cost tools:

```powershell
python -m pip install --user c7n llmlingua; npm install -g @agentmemory/agentmemory
```

Context Gateway in WSL/Bash:

```bash
curl -fsSL https://compresr.ai/api/install | sh && context-gateway
```

## MCP With Chosen Folders

Filesystem server, PowerShell:

```powershell
$AllowedOne = Read-Host "First folder the agent may access"; $AllowedTwo = Read-Host "Second folder the agent may access, or press Enter to skip"; if ($AllowedTwo) { npx -y @modelcontextprotocol/server-filesystem $AllowedOne $AllowedTwo } else { npx -y @modelcontextprotocol/server-filesystem $AllowedOne }
```

Filesystem server, WSL/Bash:

```bash
read -rp "First folder the agent may access: " allowed_one; read -rp "Second folder the agent may access, or press Enter to skip: " allowed_two; if [ -n "$allowed_two" ]; then npx -y @modelcontextprotocol/server-filesystem "$allowed_one" "$allowed_two"; else npx -y @modelcontextprotocol/server-filesystem "$allowed_one"; fi
```

Docker filesystem server with a chosen local folder:

```bash
read -rp "Folder to expose to the MCP filesystem server: " allowed_path; docker run -i --rm --mount type=bind,src="$allowed_path",dst=/projects/workspace mcp/filesystem /projects
```

Docker filesystem server, read-only:

```bash
read -rp "Folder to expose read-only: " allowed_path; docker run -i --rm --mount type=bind,src="$allowed_path",dst=/projects/workspace,ro mcp/filesystem /projects
```

GitHub MCP server with selected toolsets:

```bash
docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_PERSONAL_ACCESS_TOKEN" -e GITHUB_TOOLSETS="context,repos,issues,pull_requests" ghcr.io/github/github-mcp-server
```

## Copilot Studio Bridge Examples

Open the example REST bridge contracts, PowerShell:

```powershell
$MasterRepo = (Get-Location).Path  # run from repo root; code (Join-Path $MasterRepo "examples\copilot-studio\market-research-openapi.yaml"); code (Join-Path $MasterRepo "examples\copilot-studio\quantum-bridge-openapi.yaml")
```

Serve a chosen bridge folder locally:

```powershell
$BridgePath = Read-Host "Folder containing your API bridge files"; Set-Location $BridgePath; python -m http.server 8787
```

WSL/Bash:

```bash
read -rp "Folder containing your API bridge files: " bridge_path; cd "$bridge_path"; python3 -m http.server 8787
```

## Update Every Cloned Repo

PowerShell:

```powershell
$LabRoot = Read-Host "Folder containing cloned repos"; Get-ChildItem $LabRoot -Recurse -Directory -Filter .git | ForEach-Object { git -C $_.Parent.FullName pull --ff-only }
```

WSL/Bash:

```bash
read -rp "Folder containing cloned repos: " lab_root; find "$lab_root" -name .git -type d -print0 | while IFS= read -r -d '' gitdir; do git -C "$(dirname "$gitdir")" pull --ff-only; done
```

## Search Across A Chosen Folder

PowerShell:

```powershell
$SearchRoot = Read-Host "Folder to search"; rg "context compaction|RAG|MCP|agent memory|quantum|trading|cost" $SearchRoot
```

WSL/Bash:

```bash
read -rp "Folder to search: " search_root; rg "context compaction|RAG|MCP|agent memory|quantum|trading|cost" "$search_root"
```

## Repo Health Check

Check one repo's status via GitHub API, PowerShell:

```powershell
$Repo = Read-Host "owner/repo (e.g. HKUDS/LightRAG)"
$Headers = if ($env:GITHUB_TOKEN) { @{Authorization = "Bearer $env:GITHUB_TOKEN"} } else { @{} }
$Info = Invoke-RestMethod "https://api.github.com/repos/$Repo" -Headers $Headers
[PSCustomObject]@{Repo=$Repo; Archived=$Info.archived; LastPush=$Info.pushed_at; Stars=$Info.stargazers_count} | Format-Table
```

Bulk check all curated repos, WSL/Bash:

```bash
read -rp "Path to Master-Repo-Use: " master_repo
grep -vE '^(#|$)' "$master_repo/repo-lists/all-curated.txt" | while read -r repo; do
  result=$(gh api "repos/$repo" --jq '{archived:.archived,pushed:.pushed_at}' 2>/dev/null || echo "api-error")
  echo "$repo | $result"
done
```

## Token Counting Before a Run

Count tokens without sending, Python:

```python
import anthropic
client = anthropic.Anthropic()
response = client.messages.count_tokens(
    model="claude-sonnet-4-6",
    system="Your system prompt here",
    messages=[{"role": "user", "content": "Your message here"}]
)
print(f"Input tokens: {response.input_tokens}")
print(f"Estimated cost (Sonnet): ${response.input_tokens / 1_000_000 * 3:.4f}")
```

## Agent File Scaffold

Create a new agent `.md` from a template, PowerShell:

```powershell
$AgentName = Read-Host "Agent file name (kebab-case, e.g. my-new-agent)"
$RepoRoot = (Get-Location).Path  # run from repo root
$OutPath = Join-Path $RepoRoot "agents\$AgentName.md"
@"
# $((Get-Culture).TextInfo.ToTitleCase($AgentName.Replace('-',' ')))

**Job:** [Job title]
**Category:** [Category]
**Model tier:** Sonnet 4.6

---

## Persona

[Describe the persona]

## System Prompt

``````text
[System prompt here]
``````

## Knowledge Base Setup

[What to index]

## Tools To Attach

| Tool | Purpose |
|---|---|
| filesystem (read/write) | [describe] |

## Escalation Rules

- [Rule 1]

## Cost Profile

| Item | Estimate |
|---|---|
| Model | Sonnet 4.6 |
| Tokens per session | ~[range] |
"@ | Out-File -FilePath $OutPath -Encoding utf8
Write-Host "Agent scaffolded at $OutPath"
```

## MCP Server Start and Test

Start filesystem MCP, then open inspector:

```powershell
$AllowedPath = Read-Host "Folder the MCP server may access"
Start-Job { npx -y @modelcontextprotocol/server-filesystem $using:AllowedPath }
npx @modelcontextprotocol/inspector npx @modelcontextprotocol/server-filesystem $AllowedPath
```

Start GitHub MCP with limited toolsets:

```bash
docker run -i --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_PERSONAL_ACCESS_TOKEN" \
  -e GITHUB_TOOLSETS="repos,issues" \
  ghcr.io/github/github-mcp-server
```

## GitHub CLI Bulk Operations

Fork all repos in a list:

```bash
read -rp "Repo list file (full path): " list_file
grep -vE '^(#|$)' "$list_file" | while read -r repo; do
  gh repo fork "$repo" --clone=false 2>/dev/null && echo "Forked: $repo" || echo "Skip (already forked or error): $repo"
done
```

Create issues in bulk (one per line in a file):

```bash
read -rp "Target repo (owner/repo): " target_repo
read -rp "Issues file (one title per line): " issues_file
while IFS= read -r title; do
  gh issue create --repo "$target_repo" --title "$title" --body "Auto-created by Iris health check."
done < "$issues_file"
```

## Open Interactive Diagram

PowerShell:

```powershell
$RepoRoot = (Get-Location).Path  # run from repo root
Start-Process (Join-Path $RepoRoot "assets\interactive-diagram.html")
```

WSL/Bash:

```bash
read -rp "Path to Master-Repo-Use: " repo_root
xdg-open "$repo_root/assets/interactive-diagram.html" 2>/dev/null || open "$repo_root/assets/interactive-diagram.html"
```

## Commit From Any Computer

PowerShell:

```powershell
$RepoPath = Read-Host "Path to the repo you want to commit"; $Branch = Read-Host "Branch name to create"; $Message = Read-Host "Commit message"; git -C $RepoPath checkout -b $Branch; git -C $RepoPath add .; git -C $RepoPath commit -m $Message
```

WSL/Bash:

```bash
read -rp "Path to the repo you want to commit: " repo_path; read -rp "Branch name to create: " branch; read -rp "Commit message: " message; git -C "$repo_path" checkout -b "$branch" && git -C "$repo_path" add . && git -C "$repo_path" commit -m "$message"
```

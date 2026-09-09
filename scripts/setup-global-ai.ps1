param(
  [string]$RepoPath = "$HOME\Master-Repo-Use",
  # Which client instruction files to write. 'all' is the default because a rule
  # that lives in only one client is a rule the other clients will contradict.
  # 'gpt' is accepted as an alias for codex, which is the GPT surface.
  [ValidateSet('all','claude','codex','gemini','copilot','antigravity','cursor','gpt','chatgpt','openai','ag','google-antigravity')]
  [string]$Client = 'all',
  [switch]$CopilotOnly,
  [switch]$AutoSkills = $true
)

if ($CopilotOnly) { $Client = 'copilot' }
if ($Client -in @('gpt','chatgpt','openai')) { $Client = 'codex' }
if ($Client -in @('ag','google-antigravity')) { $Client = 'antigravity' }
function Test-Writes([string]$Name) { return ($Client -eq 'all' -or $Client -eq $Name) }

$ErrorActionPreference = 'Stop'
$begin = '<!-- MASTER-REPO-USE:BEGIN -->'
$end = '<!-- MASTER-REPO-USE:END -->'

if (-not (Test-Path "$RepoPath\.git")) { throw "Master Repo not found at $RepoPath" }

function Set-MasterRepoBlock {
  param([string]$Path,[string]$Body)
  $dir = Split-Path -Parent $Path
  if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $text = if (Test-Path $Path) { Get-Content -Raw -Path $Path } else { '' }
  $escapedBegin = [regex]::Escape($begin)
  $escapedEnd = [regex]::Escape($end)
  $block = "$begin`n$($Body.TrimEnd())`n$end"
  if ($text -match "$escapedBegin[\s\S]*?$escapedEnd") {
    $text = [regex]::Replace($text,"$escapedBegin[\s\S]*?$escapedEnd",$block)
  } else {
    if ($text.Trim()) { $text = $text.TrimEnd() + "`n`n" }
    $text += $block + "`n"
  }
  Set-Content -Path $Path -Value $text -Encoding utf8
}

$common = @"
Master Repo path: $RepoPath
Use $RepoPath\AGENTS.md as the canonical portable contract. For tasks that may benefit from an agent framework, RAG, memory, MCP, observability, security, cloud/cost, quantum, Copilot, or another cataloged tool, search the Master Repo first and load only the relevant lane. Do not load the entire catalog into context. Follow its vetting, health, and security gates before installing or executing third-party code.
Routine maintenance is GitHub-first: use the repository Catalog Guardian and [Catalog Audit] owner-approval issue rather than scheduling model calls. Only Charles may approve deterministic maintenance with `APPROVE CATALOG MAINTENANCE`. Use `python "$RepoPath\scripts\maintenance_request.py" --auto` only when a maintenance task genuinely needs model judgment, and do not perform that work until Charles states `APPROVE AI MAINTENANCE`. Never merge main without Charles approval.
"@

$autoFile = Join-Path $RepoPath "docs/auto-mode-block.txt"
if ($AutoSkills) {
  if (-not (Test-Path $autoFile)) { throw "Auto mode block not found at $autoFile" }
  $common = $common.TrimEnd() + "`n" + (Get-Content -Raw -Path $autoFile).TrimEnd()
}

if (Test-Writes 'claude') {
  Set-MasterRepoBlock "$HOME\.claude\CLAUDE.md" ($common + "`nClaude-specific entrypoint: $RepoPath\CLAUDE.md")
}
if (Test-Writes 'codex') {
  Set-MasterRepoBlock "$HOME\.codex\AGENTS.md" $common
}
# One file, two clients. Verified 2026-09-04 against
# antigravity.google/docs/rules-workflows/: Antigravity reads its GLOBAL rules
# from ~/.gemini/GEMINI.md, the same path the Gemini CLI uses, and not from any
# ~/.antigravity/ tree. Written once for whichever of the two was asked for,
# because writing it twice would let the second body replace the first.
if ((Test-Writes 'gemini') -or (Test-Writes 'antigravity')) {
  $geminiBody = $common + "`nGemini-specific entrypoint: $RepoPath\GEMINI.md" +
    "`nGoogle Antigravity reads this same file as its global rules. Its skills live in ~/.gemini/config/skills/, its plugins in ~/.gemini/config/plugins/, and its MCP servers in ~/.gemini/config/mcp_config.json."
  Set-MasterRepoBlock "$HOME\.gemini\GEMINI.md" $geminiBody
}

# The part that is genuinely Antigravity-only. Its documented global skill path is
# ~/.gemini/config/skills/<folder>/SKILL.md, which the Gemini CLI does not read.
# Every skill in this repository already carries the one frontmatter field
# Antigravity requires, description, so they install as-is with no rewriting.
if (Test-Writes 'antigravity') {
  $skillRoot = Join-Path $HOME '.gemini\config\skills'
  New-Item -ItemType Directory -Force -Path $skillRoot | Out-Null
  $installed = @()
  Get-ChildItem -Path (Join-Path $RepoPath 'skills') -Directory | Sort-Object Name | ForEach-Object {
    if (Test-Path (Join-Path $_.FullName 'SKILL.md')) {
      $destination = Join-Path $skillRoot $_.Name
      New-Item -ItemType Directory -Force -Path $destination | Out-Null
      # Merge every shipped file into the existing skill. Extra files already
      # present remain in place, so refreshing auto mode never prunes a skill.
      Get-ChildItem -LiteralPath $_.FullName -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $destination -Recurse -Force
      }
      $installed += $_.Name
    }
  }
  if ($installed.Count -gt 0) { Write-Host ("Antigravity skills installed: " + ($installed -join ', ')) }
  else { Write-Host 'Antigravity skills installed: none found' }
}
if (Test-Writes 'copilot') {
  Set-MasterRepoBlock "$HOME\.copilot\copilot-instructions.md" ($common + "`nCopilot-specific guide: $RepoPath\docs\COPILOT-SETUP.md")
}

# Every client setup includes its discoverable skills and supported hooks.
# The compatibility -AutoSkills switch remains accepted; auto mode is default.
& python (Join-Path $RepoPath 'scripts/install_auto_mode.py') --repo $RepoPath --home $HOME --client $Client
if ($LASTEXITCODE -ne 0) { throw 'Automatic skill and hook setup failed.' }

[Environment]::SetEnvironmentVariable('COPILOT_CUSTOM_INSTRUCTIONS_DIRS',$RepoPath,'User')
$env:COPILOT_CUSTOM_INSTRUCTIONS_DIRS = $RepoPath

$bin = "$HOME\bin"
New-Item -ItemType Directory -Force -Path $bin | Out-Null
$wrapper = @'
param(
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$Args
)
$ErrorActionPreference = 'Stop'
$tool = "$HOME\.master-repo-tools\WatermarkRemover-AI"
Write-Host 'Use only on media you own or are authorized to modify.' -ForegroundColor Yellow
if (-not (Test-Path "$tool\.git")) {
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $tool) | Out-Null
  git clone https://github.com/D-Ogi/WatermarkRemover-AI.git $tool
  Push-Location $tool
  try { .\setup.ps1 } finally { Pop-Location }
} else {
  git -C $tool pull --ff-only | Out-Null
}
Push-Location $tool
try { python remwm.py @Args } finally { Pop-Location }
'@
Set-Content -Path "$bin\master-watermark.ps1" -Value $wrapper -Encoding utf8

$userPath = [Environment]::GetEnvironmentVariable('Path','User')
if (($userPath -split ';') -notcontains $bin) {
  $newPath = if ($userPath) { "$userPath;$bin" } else { $bin }
  [Environment]::SetEnvironmentVariable('Path',$newPath,'User')
}

Write-Host 'Master Repo global AI setup complete.' -ForegroundColor Green
Write-Host "Repo: $RepoPath"
Write-Host "Copilot: $HOME\.copilot\copilot-instructions.md"
if ($Client -ne 'copilot') { Write-Host "Claude: $HOME\.claude\CLAUDE.md | Codex: $HOME\.codex\AGENTS.md | Gemini and Antigravity: $HOME\.gemini\GEMINI.md" }
Write-Host "Watermark command: & '$bin\master-watermark.ps1' <input> <output-folder>"
Write-Host 'GitHub audit: gh workflow run catalog-guardian.yml -R Charlesganu2004/Master-Repo-Use'
Write-Host "Optional AI request: python '$RepoPath\scripts\maintenance_request.py' --auto"
Write-Host "Token budget remains opt-in: $RepoPath\docs\TOKEN-BUDGET.md"
Write-Host 'Auto mode, discoverable skills and supported hooks installed for the selected client(s).' -ForegroundColor Green

param(
  [string]$RepoPath = "$HOME\Master-Repo-Use",
  [switch]$CopilotOnly
)

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
When shell access and authenticated gh are available, run `python "$RepoPath\scripts\maintenance_request.py" --auto` once near the start of a Master Repo-aware session. This only creates/checks the monthly-on-next-use maintenance request; do not perform maintenance until Charles states `APPROVE AI MAINTENANCE`. Never merge main without Charles approval. Do not schedule background model maintenance calls.
"@

if (-not $CopilotOnly) {
  Set-MasterRepoBlock "$HOME\.claude\CLAUDE.md" ($common + "`nClaude-specific entrypoint: $RepoPath\CLAUDE.md")
  Set-MasterRepoBlock "$HOME\.codex\AGENTS.md" $common
}
Set-MasterRepoBlock "$HOME\.copilot\copilot-instructions.md" ($common + "`nCopilot-specific guide: $RepoPath\docs\COPILOT-SETUP.md")

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
if (-not $CopilotOnly) { Write-Host "Claude: $HOME\.claude\CLAUDE.md | Codex: $HOME\.codex\AGENTS.md" }
Write-Host "Watermark command: & '$bin\master-watermark.ps1' <input> <output-folder>"
Write-Host "Maintenance request: python '$RepoPath\scripts\maintenance_request.py' --auto"
Write-Host "Token budget remains opt-in: $RepoPath\docs\TOKEN-BUDGET.md"

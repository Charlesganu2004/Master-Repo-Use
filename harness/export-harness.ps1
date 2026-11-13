<#
.SYNOPSIS
  Refresh harness/files from the live harness on the owner's PC.

.DESCRIPTION
  Copies the rule files, CaveCrew agents, skills, hooks, plugins and the local-rag
  engine out of the live client folders, replaces every machine-specific value with
  a placeholder, writes the JSON merge fragments, and then runs a leak gate over the
  result. The gate fails the export if any personal name, internal identifier or
  secret-shaped string is left. install.ps1 renders the placeholders back on the
  colleague's PC.

  Placeholders: {{HOME}} {{HOME_JSON}} {{HOME_FWD}} {{TEMP}} {{TEMP_JSON}}
  {{REPO}} {{REPO_JSON}} {{VERTEX_PROJECT}} {{VERTEX_LOCATION}}

.PARAMETER OutDir
  Snapshot folder. Defaults to harness/files next to this script.

.PARAMETER Check
  Build the snapshot in a temporary folder, run the leak gate and report drift
  against OutDir without writing to it.

.NOTES
  Requires PowerShell 7. Windows PowerShell 5.1 formats JSON differently, so it
  would rewrite the merge fragments and report drift on every check.
#>
#Requires -Version 7.0
[CmdletBinding()]
param(
    [string]$OutDir,
    [switch]$Check,
    [string]$SourceHome = $HOME
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

if (-not $OutDir) { $OutDir = Join-Path $PSScriptRoot 'files' }
$Utf8NoBom = New-Object Text.UTF8Encoding($false)

# The private terms never live in this public repository. They come from an
# owner-only file, one term per line, or from HARNESS_LEAK_TERMS (semicolon-
# separated). A "name:" prefix marks the owner's first name, which is also
# rewritten to "the user" in the snapshot.
$TermsFile = Join-Path $SourceHome '.config\harness\leak-terms.txt'
$rawTerms = @()
if ($env:HARNESS_LEAK_TERMS -and (Test-Path -LiteralPath $env:HARNESS_LEAK_TERMS -PathType Leaf)) {
    # A path here would become one harmless "term" and let the gate pass silently.
    throw 'HARNESS_LEAK_TERMS holds terms separated by semicolons, not a file path; put the file at %USERPROFILE%\.config\harness\leak-terms.txt'
}
if ($env:HARNESS_LEAK_TERMS) { $rawTerms = $env:HARNESS_LEAK_TERMS.Split(';') }
elseif (Test-Path -LiteralPath $TermsFile) { $rawTerms = Get-Content -LiteralPath $TermsFile }
else { throw "No leak terms: create $TermsFile (one term per line) or set HARNESS_LEAK_TERMS." }
$OwnerNames = @()
$PrivateTerms = @(Split-Path $SourceHome -Leaf)
foreach ($line in $rawTerms) {
    $t = $line.Trim()
    if (-not $t -or $t.StartsWith('#')) { continue }
    if ($t.StartsWith('name:')) { $t = $t.Substring(5).Trim(); $OwnerNames += $t }
    $PrivateTerms += $t
}
if ($PrivateTerms.Count -lt 2) { throw 'The leak term list is empty.' }

# Whole-word match, so a term inside a longer word (a public repo slug that starts
# with the owner's name, or "extraneous") is not a finding.
function Get-TermPattern([string]$term) { '(?<![A-Za-z0-9])' + [regex]::Escape($term) + '(?![A-Za-z0-9])' }
$GateTerms = @()
$i = 0
foreach ($t in ($PrivateTerms | Select-Object -Unique)) { $i++; $GateTerms += @{ Name = "private term #$i"; Pattern = (Get-TermPattern $t) } }
$GateTerms += @(
    @{ Name = 'secret';    Pattern = 'ghp_[A-Za-z0-9]{20,}' },
    @{ Name = 'secret';    Pattern = 'github_pat_[A-Za-z0-9_]{20,}' },
    @{ Name = 'secret';    Pattern = 'gho_[A-Za-z0-9]{20,}' },
    @{ Name = 'secret';    Pattern = 'AIza[0-9A-Za-z_\-]{30,}' },
    @{ Name = 'secret';    Pattern = '-----BEGIN [A-Z ]+-----' },
    @{ Name = 'secret';    Pattern = '"?password"?\s*[:=]\s*["''][^"''\s{}<>]{4,}["'']' }
)

# ---- sources -------------------------------------------------------------------
$OpenCodeDir = Join-Path $SourceHome '.config\opencode'
$CopilotDir  = Join-Path $SourceHome '.copilot'
$ClaudeDir   = Join-Path $SourceHome '.claude'
$KbDir       = Join-Path $SourceHome '.local\lib\kb'
$LocalBin    = Join-Path $SourceHome '.local\bin'
$TempDir     = Join-Path $SourceHome 'AppData\Local\Temp'

$liveConfig = Get-Content (Join-Path $OpenCodeDir 'opencode.json') -Raw | ConvertFrom-Json
$VertexProject = ''
if ($liveConfig.PSObject.Properties['providers'] -and $liveConfig.providers.PSObject.Properties['google-vertex']) {
    $VertexProject = [string]$liveConfig.providers.'google-vertex'.settings.project
}

# The Master Repo path is read from the rules file, where the auto-mode block names it.
$RepoDir = ''
$agentsText = [IO.File]::ReadAllText((Join-Path $OpenCodeDir 'AGENTS.md'))
$m = [regex]::Match($agentsText, 'Master Repo path:\s*(\S[^\r\n]*)')
if ($m.Success) { $RepoDir = $m.Groups[1].Value.Trim() }

# Never exported: secrets, personal login state, per-PC generated hooks, backups.
$ExcludeName = '(?i)(^service\.json$|^config\.json$|\.bak|^data\.db|^session-|\.log$|^master-repo-auto\.json$|\.pyc$)'
$ExcludeDir  = '(?i)^(__pycache__|node_modules|\.venv|_backup-preinstall|\.git)$'

# ---- templating ----------------------------------------------------------------
function Replace-CI([string]$text, [string]$find, [string]$with) {
    if (-not $find) { return $text }
    return [regex]::Replace($text, [regex]::Escape($find), $with.Replace('$', '$$'),
        [Text.RegularExpressions.RegexOptions]::IgnoreCase)
}

function Convert-ToTemplate([string]$text) {
    $pairs = New-Object System.Collections.ArrayList
    foreach ($p in @(@($TempDir, 'TEMP'), @($RepoDir, 'REPO'))) {
        if ($p[0]) {
            [void]$pairs.Add(@($p[0].Replace('\', '\\'), "{{$($p[1])_JSON}}"))
            [void]$pairs.Add(@($p[0], "{{$($p[1])}}"))
        }
    }
    [void]$pairs.Add(@($SourceHome.Replace('\', '\\'), '{{HOME_JSON}}'))
    [void]$pairs.Add(@($SourceHome, '{{HOME}}'))
    [void]$pairs.Add(@($SourceHome.Replace('\', '/'), '{{HOME_FWD}}'))
    if ($VertexProject) { [void]$pairs.Add(@($VertexProject, '{{VERTEX_PROJECT}}')) }
    foreach ($pair in $pairs) { $text = Replace-CI $text $pair[0] $pair[1] }

    # The rules name their owner; the public copy names the reader instead.
    $text = [regex]::Replace($text, "in his own words", "in their own words")
    $text = [regex]::Replace($text, "let him decide", "let them decide")
    foreach ($name in $OwnerNames) {
        $word = Get-TermPattern $name
        $text = [regex]::Replace($text, $word + "'s", "the user's")
        # Capital only where a sentence starts; a line wrap mid-sentence stays lower case.
        $text = [regex]::Replace($text, '(?<=[.!?]\s+)' + $word, 'The user')
        $text = [regex]::Replace($text, '\A' + $word, 'The user')
        $text = [regex]::Replace($text, $word, 'the user')
    }
    return $text
}

function Test-Binary([byte[]]$bytes) {
    $n = [Math]::Min($bytes.Length, 8000)
    for ($i = 0; $i -lt $n; $i++) { if ($bytes[$i] -eq 0) { return $true } }
    return $false
}

# ---- staging -------------------------------------------------------------------
$Stage = Join-Path ([IO.Path]::GetTempPath()) ('harness-export-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $Stage -Force | Out-Null
$Counts = [ordered]@{}

function Add-Count([string]$area) {
    if ($Counts.Contains($area)) { $Counts[$area]++ } else { $Counts[$area] = 1 }
}

function Write-Staged([string]$rel, [string]$text) {
    $dest = Join-Path $Stage $rel
    New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force | Out-Null
    [IO.File]::WriteAllText($dest, $text, $Utf8NoBom)
}

function Export-File([string]$src, [string]$homeRel, [string]$area) {
    $bytes = [IO.File]::ReadAllBytes($src)
    $rel = 'home\' + $homeRel
    if (Test-Binary $bytes) {
        $dest = Join-Path $Stage $rel
        New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force | Out-Null
        [IO.File]::WriteAllBytes($dest, $bytes)
    } else {
        Write-Staged $rel (Convert-ToTemplate ([IO.File]::ReadAllText($src)))
    }
    Add-Count $area
}

function Export-Tree([string]$srcDir, [string]$homeRel, [string]$area) {
    foreach ($item in Get-ChildItem -LiteralPath $srcDir -Force) {
        if ($item.PSIsContainer) {
            if ($item.Name -match $ExcludeDir) { continue }
            Export-Tree $item.FullName ($homeRel + '\' + $item.Name) $area
        } elseif ($item.Name -notmatch $ExcludeName) {
            Export-File $item.FullName ($homeRel + '\' + $item.Name) $area
        }
    }
}

function Require([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Source missing: $path" }
    return $path
}

# OpenCode: rules, auto-loaded plugins, the graphify skill.
Export-File (Require (Join-Path $OpenCodeDir 'AGENTS.md')) '.config\opencode\AGENTS.md' 'opencode'
foreach ($f in Get-ChildItem (Require (Join-Path $OpenCodeDir 'plugins')) -File) {
    if ($f.Name -notmatch $ExcludeName) { Export-File $f.FullName ('.config\opencode\plugins\' + $f.Name) 'opencode' }
}
Export-Tree (Require (Join-Path $OpenCodeDir 'skills\graphify')) '.config\opencode\skills\graphify' 'opencode'

# Copilot CLI: rules, CaveCrew agents, hooks, rustwright launcher.
Export-File (Require (Join-Path $CopilotDir 'copilot-instructions.md')) '.copilot\copilot-instructions.md' 'copilot'
foreach ($name in 'cavecrew-builder.md', 'cavecrew-investigator.md', 'cavecrew-reviewer.md') {
    Export-File (Require (Join-Path $CopilotDir "agents\$name")) ".copilot\agents\$name" 'copilot'
}
foreach ($name in 'cavecrew-rules-sync.json', 'cavecrew-rules-sync.mjs', 'caveman-autocompress.js',
                  'caveman-autocompress.json', 'token-goat.json', 'token-goat-shim.js') {
    Export-File (Require (Join-Path $CopilotDir "hooks\$name")) ".copilot\hooks\$name" 'copilot'
}
Export-File (Require (Join-Path $CopilotDir 'bin\rustwright-launch.js')) '.copilot\bin\rustwright-launch.js' 'copilot'

# Copilot skills: every folder except the internal graphweave tool.
$skillCount = 0
foreach ($dir in Get-ChildItem (Require (Join-Path $CopilotDir 'skills')) -Directory) {
    if ($dir.Name -eq 'graphweave-cli' -or $dir.Name -match $ExcludeDir) { continue }
    Export-Tree $dir.FullName ('.copilot\skills\' + $dir.Name) 'copilot-skills-files'
    $skillCount++
}
$Counts['copilot-skills'] = $skillCount

# Claude skills folder (OpenCode reads it): token-goat only.
Export-Tree (Require (Join-Path $ClaudeDir 'skills\token-goat')) '.claude\skills\token-goat' 'claude-skills'

# local-rag engine, pinned requirements and the wrapper.
foreach ($name in 'kb.py', 'kb_extract.py', 'kb_graph.py', 'kb_store.py') {
    Export-File (Require (Join-Path $KbDir $name)) ".local\lib\kb\$name" 'local-rag'
}
$venvPython = Join-Path $KbDir '.venv\Scripts\python.exe'
if (Test-Path $venvPython) {
    # In Windows PowerShell 5.1, stderr from a native command raises a terminating
    # error under 'Stop', and uv prints its "Using Python ..." notice to stderr.
    $ErrorActionPreference = 'Continue'
    $frozen = & uv pip freeze --python $venvPython 2>$null
    $ErrorActionPreference = 'Stop'
    if ($LASTEXITCODE -ne 0 -or -not $frozen) { throw "uv pip freeze failed for $venvPython" }
    $reqs = ($frozen | Where-Object { $_ -and $_ -notmatch '^\s*-e\s|@ file:' }) -join "`n"
    Write-Staged 'home\.local\lib\kb\requirements.txt' ($reqs + "`n")
    Add-Count 'local-rag'
} else {
    throw "local-rag venv missing at $venvPython; cannot pin requirements"
}
Export-File (Require (Join-Path $LocalBin 'local-rag.cmd')) '.local\bin\local-rag.cmd' 'local-rag'

# ---- JSON merge fragments ------------------------------------------------------
function ConvertTo-V2Mcp($server, [int]$execution) {
    # V1 kept one integer timeout; V2 splits it. execution comes from the brief's
    # per-server budget, so the V1 integer is not carried over.
    $out = [ordered]@{ type = 'local'; command = @($server.command) }
    if ($server.PSObject.Properties['environment'] -and $server.environment) { $out.environment = $server.environment }
    $out.disabled = $false
    $out.timeout = [ordered]@{ startup = 120000; catalog = 120000; execution = $execution }
    return $out
}

# Allowlist: only these servers are exported. Any other server in the owner's live
# configs (a local model runner, say) stays on that PC and never reaches the bundle.
$HarnessServers = @('local-rag', 'graphify', 'playwright', 'rustwright')
$servers = [ordered]@{}
foreach ($name in $HarnessServers) {
    if (-not $liveConfig.mcp.PSObject.Properties[$name]) { throw "opencode.json has no mcp server '$name'" }
    $exec = 120000
    if ($name -eq 'local-rag') { $exec = 600000 }
    $servers[$name] = ConvertTo-V2Mcp $liveConfig.mcp.$name $exec
}
$opencode = [ordered]@{
    '$schema'     = $liveConfig.'$schema'
    default_agent = $liveConfig.default_agent
    agents        = $liveConfig.agents
    mcp           = [ordered]@{ servers = $servers }
    skills        = @("$SourceHome\.copilot\skills")
}
Write-Staged 'merge\opencode.json' (Convert-ToTemplate ($opencode | ConvertTo-Json -Depth 32))

$vertex = [ordered]@{ 'google-vertex' = [ordered]@{ settings = [ordered]@{ project = '{{VERTEX_PROJECT}}'; location = '{{VERTEX_LOCATION}}' } } }
Write-Staged 'merge\vertex-provider.json' ($vertex | ConvertTo-Json -Depth 32)

$copilotMcp = Get-Content (Require (Join-Path $CopilotDir 'mcp-config.json')) -Raw | ConvertFrom-Json
foreach ($name in $HarnessServers) {
    if (-not $copilotMcp.mcpServers.PSObject.Properties[$name]) { throw "mcp-config.json has no server '$name'" }
}
$copilotServers = [ordered]@{}
foreach ($p in $copilotMcp.mcpServers.PSObject.Properties) {
    if ($HarnessServers -contains $p.Name) { $copilotServers[$p.Name] = $p.Value }
}
Write-Staged 'merge\copilot-mcp-config.json' (Convert-ToTemplate ([ordered]@{ mcpServers = $copilotServers } | ConvertTo-Json -Depth 32))

$copilotSettings = Get-Content (Require (Join-Path $CopilotDir 'settings.json')) -Raw | ConvertFrom-Json
Write-Staged 'merge\copilot-settings.json' ([ordered]@{ enabledPlugins = $copilotSettings.enabledPlugins } | ConvertTo-Json -Depth 32)
$Counts['merge'] = 4

# ---- leak gate -----------------------------------------------------------------
$leaks = New-Object System.Collections.ArrayList
# The snapshot, plus every other public file in harness/ and this lane's test.
$filesRoot = [IO.Path]::GetFullPath($OutDir).TrimEnd('\')
$scan = @(Get-ChildItem $Stage -Recurse -File)
$scan += @(Get-ChildItem $PSScriptRoot -Recurse -File | Where-Object { -not $_.FullName.StartsWith($filesRoot + '\', [StringComparison]::OrdinalIgnoreCase) })
$testFile = Join-Path (Split-Path $PSScriptRoot -Parent) 'tests\test_harness_bundle.py'
if (Test-Path $testFile) { $scan += Get-Item $testFile }
foreach ($file in $scan) {
    $text = [Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($file.FullName))
    $lineNo = 0
    foreach ($line in $text -split "`n") {
        $lineNo++
        foreach ($term in $GateTerms) {
            if ([regex]::IsMatch($line, $term.Pattern, [Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
                [void]$leaks.Add(('{0}:{1}: {2}' -f $file.FullName.Replace($Stage, 'files'), $lineNo, $term.Name))
            }
        }
    }
}
foreach ($file in Get-ChildItem (Join-Path $Stage 'merge') -File) {
    $null = [IO.File]::ReadAllText($file.FullName) | ConvertFrom-Json
}

Write-Host 'Harness export summary'
foreach ($k in $Counts.Keys) { Write-Host ('  {0,-22} {1}' -f $k, $Counts[$k]) }

if ($leaks.Count -gt 0) {
    Write-Host "LEAK GATE FAILED: $($leaks.Count) finding(s)" -ForegroundColor Red
    $leaks | Select-Object -First 50 | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    Remove-Item $Stage -Recurse -Force
    throw 'Leak gate failed; nothing written.'
}
Write-Host 'Leak gate: clean'

if ($Check) {
    $drift = @()
    if (Test-Path $OutDir) {
        $a = Get-ChildItem $Stage -Recurse -File | ForEach-Object { $_.FullName.Substring($Stage.Length + 1) + '|' + (Get-FileHash $_.FullName).Hash }
        $b = Get-ChildItem $OutDir -Recurse -File | ForEach-Object { $_.FullName.Substring($OutDir.Length + 1) + '|' + (Get-FileHash $_.FullName).Hash }
        $drift = @(Compare-Object @($a) @($b) | ForEach-Object { $_.InputObject.Split('|')[0] } | Sort-Object -Unique)
    } else { $drift = @('(snapshot missing)') }
    Remove-Item $Stage -Recurse -Force
    if ($drift.Count) { Write-Host "Drift against ${OutDir}: $($drift.Count) file(s)"; $drift | Select-Object -First 30 | ForEach-Object { Write-Host "  $_" } }
    else { Write-Host 'Snapshot is up to date.' }
    return
}

if (Test-Path $OutDir) { Remove-Item $OutDir -Recurse -Force }
New-Item -ItemType Directory -Path (Split-Path $OutDir -Parent) -Force | Out-Null
Move-Item $Stage $OutDir
Write-Host "Snapshot written to $OutDir"

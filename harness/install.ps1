<#
.SYNOPSIS
  One-line installer for the AI harness: GitHub Copilot CLI and OpenCode Desktop on Windows.

.DESCRIPTION
  Installs the apps and pinned tools, clones the Master Repo, writes the harness
  (rules, CaveCrew agents, skills, hooks, MCP servers, plugins, opencode.json) into
  the home folder, and walks through GitHub sign-in. Safe to rerun: every step
  checks before it changes anything, and every file it changes is backed up first
  to %USERPROFILE%\.harness-backup\<timestamp>\.

  irm https://raw.githubusercontent.com/Charlesganu2004/Master-Repo-Use/main/harness/install.ps1 | iex
  & ([scriptblock]::Create((irm https://raw.githubusercontent.com/Charlesganu2004/Master-Repo-Use/main/harness/install.ps1))) -VertexProject <id>

  Env overrides for irm | iex runs: HARNESS_REPO_PATH, HARNESS_BRANCH,
  HARNESS_VERTEX_PROJECT, HARNESS_VERTEX_LOCATION, HARNESS_NO_PATH_UPDATE=1.

  Advanced and testing switches:
    -NoPathUpdate   leave the User PATH alone (the tools still work by full path).
    -TargetHome     write the harness under that folder instead of the profile;
                    implies -SkipApps -SkipTools -NoSignIn -NoPathUpdate.
    -SandboxTools   with -TargetHome, run the tools step too, inside the target:
                    every tool, cache and browser path is rooted there through
                    environment redirects, and the run aborts if any resolved write
                    path falls outside it.

  Windows PowerShell 5.1 compatible. Never call exit here: under irm | iex it would
  close the user's own PowerShell window.
#>
[CmdletBinding()]
param(
    [string]$RepoPath,
    [string]$Branch,
    [string]$VertexProject,
    [string]$VertexLocation,
    [string]$OpenCodeVersion = '2.2.7',
    [switch]$WithClaudeCode,
    [switch]$SkipApps,
    [switch]$SkipTools,
    [switch]$NoSignIn,
    [string]$TargetHome,
    [switch]$DryRun,
    [switch]$NoPathUpdate,
    [switch]$SandboxTools
)

$ErrorActionPreference = 'Stop'

$RepoUrl      = 'https://github.com/Charlesganu2004/Master-Repo-Use.git'
$RepoZipBase  = 'https://codeload.github.com/Charlesganu2004/Master-Repo-Use/zip/refs/heads/'
$NodeVersion  = '24.20.0'
$UvVersion    = '0.12.23'
$NpmPackages  = @('token-goat@2.9.1', '@playwright/mcp@0.0.80', 'playwright@1.62.1', 'rustwright-mcp@0.1.0')
$GraphifySpec = 'graphifyy[mcp,office,pdf]==0.9.79'
$GraphifyVersion = '0.9.79'
$PlaywrightChrome = 'chromium-1243'

# SHA-256 of every file this script downloads and then runs or unpacks. Nothing
# unverified is executed. Sources: nodejs.org SHASUMS256.txt, and the asset digests
# of the GitHub releases (gh api repos/<owner>/<repo>/releases/tags/<tag>).
$NodeSha256 = @{
    'x64'   = '6cac9ffbca8f6a47091e4b5c772e0606049c3871cb67d900c0cedde630e545ba'
    'arm64' = '31c6799744de8a54601643098040c68c3697e56c94e407d61d0e5fa5f34191d7'
}
$UvSha256 = @{
    'x64'   = '75d05de6762778c31ee183398de7dd15093fad0ed90b1f236d8205ea5ec00c90'
    'arm64' = '13294e232ececbe709c06b74e6ced06f2a225ea5591476685362f22be56a50d5'
}
$OpenCodeSha256 = @{
    '2.2.7' = @{
        'x64'   = '2ea501f83e627bf2b1ba2afb5124391ab27c86b9dd5071324ea5cf8b168b7d2a'
        'arm64' = '7c67275453c74b8bf9d1bd5dda52d19de4042399b0401ba55c55acdceba6c4e1'
    }
}
# Chrome for Testing has no published digest and its binaries are unsigned, so the
# fallback download is pinned per build (the same bytes from cdn.playwright.dev and
# storage.googleapis.com). The pin is looked up before downloading; a build without
# one is not downloaded at all, the fallback warns and leaves it to Playwright's installer.
$ChromeSha256 = @{
    '153.0.8010.12' = @{
        'chrome-win64'                = '415968b02065d4a9e2c10b85f0ae9f489b8fba500e94d9d0a7b7c4852a7234c1'
        'chrome-headless-shell-win64' = '7aec872f3090e639c4237467624ea863c20fe2878914c93a6556bdbb52aa6c4c'
    }
}
# Top-level keys of the OpenCode V2 config (Config.InfoEncoded). Anything else in
# a colleague's opencode.json is a V1 key that OpenCode migrates on load; the
# installer leaves those untouched.
$OpenCodeV2Keys = @('$schema', 'shell', 'model', 'default_agent', 'update', 'share', 'enterprise', 'username',
    'timezone', 'permissions', 'policies', 'agents', 'snapshots', 'watcher', 'formatter', 'lsp', 'media',
    'tool_output', 'mcp', 'compaction', 'skills', 'commands', 'instructions', 'references', 'websearch',
    'plugins', 'worktree', 'warming', 'providers', 'experimental')
$RuleMarkers = @(
    @('<!-- token-goat-begin -->', '<!-- token-goat-end -->'),
    @('<!-- rag-graph-begin -->', '<!-- rag-graph-end -->'),
    @('<!-- protected-rules-begin -->', '<!-- protected-rules-end -->'),
    @('<!-- MASTER-REPO-USE:BEGIN -->', '<!-- MASTER-REPO-USE:END -->')
)

# ---- parameters and environment overrides --------------------------------------
$RunningFromFile = $false
if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot 'files\home')) -and
    (Test-Path (Join-Path (Split-Path $PSScriptRoot -Parent) '.git'))) {
    $RunningFromFile = $true
}
if (-not $RepoPath) { $RepoPath = $env:HARNESS_REPO_PATH }
if (-not $RepoPath -and $RunningFromFile) { $RepoPath = Split-Path $PSScriptRoot -Parent }
if (-not $RepoPath) { $RepoPath = Join-Path $HOME 'Master-Repo-Use' }
if (-not $Branch) { $Branch = $env:HARNESS_BRANCH }
if (-not $Branch) { $Branch = 'main' }
if (-not $VertexProject) { $VertexProject = $env:HARNESS_VERTEX_PROJECT }
if (-not $VertexLocation) { $VertexLocation = $env:HARNESS_VERTEX_LOCATION }
if (-not $VertexLocation) { $VertexLocation = 'us' }
if ($env:HARNESS_NO_PATH_UPDATE -eq '1') { $NoPathUpdate = $true }
if ($SandboxTools -and -not $TargetHome) { throw '-SandboxTools needs -TargetHome.' }

$Sandbox = $false
if ($TargetHome) {
    $Sandbox = $true
    $SkipApps = $true; $NoSignIn = $true; $NoPathUpdate = $true
    $SkipTools = -not $SandboxTools
    if (-not (Test-Path $TargetHome)) { New-Item -ItemType Directory -Path $TargetHome -Force | Out-Null }
    $HomeDir = (Resolve-Path $TargetHome).Path.TrimEnd('\')
    $TempDir = Join-Path $HomeDir 'AppData\Local\Temp'
    $LocalAppData = Join-Path $HomeDir 'AppData\Local'
    $RoamingAppData = Join-Path $HomeDir 'AppData\Roaming'
} else {
    $HomeDir = $HOME.TrimEnd('\')
    $TempDir = (Get-Item $env:TEMP).FullName.TrimEnd('\')
    $LocalAppData = $env:LOCALAPPDATA
    $RoamingAppData = $env:APPDATA
}
$RepoPath = [IO.Path]::GetFullPath($RepoPath).TrimEnd('\')
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$BackupDir = Join-Path $HomeDir ".harness-backup\$Stamp"
$NodeDir = Join-Path $HomeDir '.local\node'
$LocalBin = Join-Path $HomeDir '.local\bin'
$KbDir = Join-Path $HomeDir '.local\lib\kb'
$Utf8NoBom = New-Object Text.UTF8Encoding($false)
$Script:Warnings = New-Object System.Collections.ArrayList
$Script:Changed = 0
$Script:BackedUp = 0
$Script:NeedCopilotNpm = $false
$Script:NeedUvPython = $false
$Script:LastNativeOutput = @()

# A sandbox dry run still logs inside the target, never in the real %TEMP%.
if ((-not $DryRun -or $Sandbox) -and -not (Test-Path $TempDir)) { New-Item -ItemType Directory -Path $TempDir -Force | Out-Null }
$LogDir = $TempDir
if (-not (Test-Path $LogDir)) { $LogDir = [IO.Path]::GetTempPath() }
$LogFile = Join-Path $LogDir "harness-install-$Stamp.log"

# ---- logging and helpers -------------------------------------------------------
function Write-Log([string]$Message, [string]$Level = 'INFO') {
    $line = '{0} [{1}] {2}' -f (Get-Date -Format 'HH:mm:ss'), $Level, $Message
    try { Add-Content -Path $LogFile -Value $line -Encoding UTF8 } catch { }
    switch ($Level) {
        'WARN'  { Write-Host "  ! $Message" -ForegroundColor Yellow }
        'ERROR' { Write-Host "  x $Message" -ForegroundColor Red }
        'STEP'  { Write-Host ''; Write-Host "== $Message" -ForegroundColor Cyan }
        'OK'    { Write-Host "  + $Message" -ForegroundColor Green }
        default { Write-Host "    $Message" }
    }
}

function Add-Warning([string]$Message) {
    [void]$Script:Warnings.Add($Message)
    Write-Log $Message 'WARN'
}

# Runs a native program, sends its output to the log, returns the exit code.
# ErrorActionPreference is lowered locally: in PowerShell 5.1 a native program
# writing to stderr under 2>&1 raises a terminating error when it is 'Stop'.
function Invoke-Native([string]$Exe, [string[]]$Arguments, [switch]$Quiet) {
    $ErrorActionPreference = 'Continue'
    if ($DryRun) { Write-Log ("would run: {0} {1}" -f $Exe, ($Arguments -join ' ')); return 0 }
    Write-Log ("run: {0} {1}" -f $Exe, ($Arguments -join ' '))
    $output = & $Exe @Arguments 2>&1
    $code = $LASTEXITCODE
    $Script:LastNativeOutput = @($output | ForEach-Object { "$_" })
    foreach ($o in $output) {
        $text = "$o"
        try { Add-Content -Path $LogFile -Value "      $text" -Encoding UTF8 } catch { }
        if (-not $Quiet) { Write-Host "      $text" -ForegroundColor DarkGray }
    }
    if ($null -eq $code) { $code = 0 }
    return $code
}

# Same, but returns the text output, for version probes.
function Get-NativeOutput([string]$Exe, [string[]]$Arguments) {
    $ErrorActionPreference = 'Continue'
    try {
        $out = & $Exe @Arguments 2>&1
        if ($LASTEXITCODE -ne 0) { return '' }
        return (($out | ForEach-Object { "$_" }) -join "`n").Trim()
    } catch { return '' }
}

# Interactive console runs (irm | iex included) prompt; piped or scheduled runs do not.
function Test-Interactive {
    try { return ([Environment]::UserInteractive -and -not [Console]::IsInputRedirected) } catch { return $false }
}

function Confirm-Step([string]$Question) {
    if (-not (Test-Interactive)) { Write-Log "not interactive, skipped: $Question"; return $false }
    $answer = Read-Host "$Question [Y/n]"
    return ($answer -eq '' -or $answer -match '^(y|yes)$')
}

function Update-SessionPath {
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    # The harness folders go first so its pinned node, uv and graphify win.
    $env:Path = (@($NodeDir, $LocalBin, $machine, $user) | Where-Object { $_ }) -join ';'
}

# ---- sandbox guard -------------------------------------------------------------
# With -TargetHome every write must land inside the target. Callers pass each path
# they are about to write; anything outside aborts the whole run.
function Assert-InTarget([string]$Path) {
    if (-not $Sandbox -or -not $Path) { return }
    $full = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    if ($full -ieq $HomeDir -or $full.StartsWith($HomeDir + '\', [StringComparison]::OrdinalIgnoreCase)) { return }
    throw "SAFETY: refusing to write outside the target home: $full"
}

# Child programs find the profile through environment variables, so the tools
# step in a sandbox points every one of them at the target. PowerShell's own
# $HOME and [Environment]::GetFolderPath read the Windows profile API instead;
# this script never uses them after start-up, it uses $HomeDir and friends.
function Get-SandboxEnvironment {
    $e = [ordered]@{}
    $e['USERPROFILE'] = $HomeDir
    $e['HOME'] = $HomeDir
    $e['HOMEDRIVE'] = $HomeDir.Substring(0, 2)
    $e['HOMEPATH'] = $HomeDir.Substring(2)
    $e['APPDATA'] = $RoamingAppData
    $e['LOCALAPPDATA'] = $LocalAppData
    $e['TEMP'] = $TempDir
    $e['TMP'] = $TempDir
    $e['XDG_CONFIG_HOME'] = Join-Path $HomeDir '.config'
    $e['XDG_DATA_HOME'] = Join-Path $HomeDir '.local\share'
    $e['XDG_CACHE_HOME'] = Join-Path $HomeDir '.cache'
    $e['XDG_BIN_HOME'] = $LocalBin
    $e['UV_TOOL_DIR'] = Join-Path $RoamingAppData 'uv\tools'
    $e['UV_TOOL_BIN_DIR'] = $LocalBin
    $e['UV_PYTHON_INSTALL_DIR'] = Join-Path $RoamingAppData 'uv\python'
    $e['UV_PYTHON_BIN_DIR'] = $LocalBin
    $e['UV_CACHE_DIR'] = Join-Path $LocalAppData 'uv\cache'
    $e['UV_INSTALL_DIR'] = $LocalBin
    $e['UV_UNMANAGED_INSTALL'] = $LocalBin
    $e['UV_NO_MODIFY_PATH'] = '1'
    $e['npm_config_cache'] = Join-Path $LocalAppData 'npm-cache'
    $e['npm_config_prefix'] = $NodeDir
    $e['npm_config_userconfig'] = Join-Path $HomeDir '.npmrc'
    $e['PLAYWRIGHT_BROWSERS_PATH'] = Join-Path $LocalAppData 'ms-playwright'
    $e['KB_HOME'] = Join-Path $HomeDir '.local\share\kb'
    return $e
}

function Enter-ToolSandbox {
    $Script:SavedEnv = @{}
    $redirects = Get-SandboxEnvironment
    foreach ($k in $redirects.Keys) {
        # Only absolute paths are checked: HOMEDRIVE is a bare "C:" and the flags are "1".
        if ($redirects[$k] -match '^[A-Za-z]:\\') { Assert-InTarget $redirects[$k] }
        $Script:SavedEnv[$k] = [Environment]::GetEnvironmentVariable($k, 'Process')
        [Environment]::SetEnvironmentVariable($k, $redirects[$k], 'Process')
    }
    Write-Log "tool sandbox: profile, uv, npm and Playwright paths redirected into $HomeDir"
}

function Exit-ToolSandbox {
    if (-not $Script:SavedEnv) { return }
    foreach ($k in $Script:SavedEnv.Keys) { [Environment]::SetEnvironmentVariable($k, $Script:SavedEnv[$k], 'Process') }
    $Script:SavedEnv = $null
}

function Get-PlaywrightBrowsersDir {
    if ($env:PLAYWRIGHT_BROWSERS_PATH) { return $env:PLAYWRIGHT_BROWSERS_PATH }
    return (Join-Path $LocalAppData 'ms-playwright')
}

function Get-Download([string]$Url, [string]$OutFile) {
    Assert-InTarget $OutFile
    Write-Log "download: $Url"
    if ($DryRun) { return }
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing
}

function Test-Command([string]$Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

# .NET instead of Get-FileHash and Expand-Archive: when Windows PowerShell 5.1 is
# started from PowerShell 7, the inherited PSModulePath can hide those cmdlets.
function Get-Sha256([string]$Path) {
    $sha = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($Path)
    try { return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-', '') }
    finally { $stream.Dispose(); $sha.Dispose() }
}

# A download whose hash does not match is deleted and never run or unpacked.
function Assert-Sha256([string]$Path, [string]$Expected, [string]$Label) {
    if (-not $Expected) { Remove-Item $Path -Force -ErrorAction SilentlyContinue; throw "no pinned SHA-256 for $Label; not running it" }
    $actual = Get-Sha256 $Path
    if ($actual -ne $Expected.ToUpperInvariant()) {
        Remove-Item $Path -Force -ErrorAction SilentlyContinue
        throw "SHA-256 mismatch for ${Label}: got $actual, expected $($Expected.ToUpperInvariant())"
    }
    Write-Log "$Label SHA-256 verified"
}

# Pinned for the default version; for any other -OpenCodeVersion, the digest the
# GitHub release API publishes for the asset.
function Get-OpenCodeDigest([string]$Asset) {
    $arch = Get-Arch
    if ($OpenCodeSha256.ContainsKey($OpenCodeVersion)) { return $OpenCodeSha256[$OpenCodeVersion][$arch] }
    $api = "https://api.github.com/repos/anomalyco/opencode/releases/tags/v$OpenCodeVersion"
    Write-Log "fetching the release digest from $api"
    $release = Invoke-RestMethod -Uri $api -UseBasicParsing -Headers @{ 'User-Agent' = 'harness-install' }
    $entry = $release.assets | Where-Object { $_.name -eq $Asset } | Select-Object -First 1
    if (-not $entry -or -not $entry.PSObject.Properties['digest'] -or -not $entry.digest) { throw "release v$OpenCodeVersion publishes no digest for $Asset" }
    return ([string]$entry.digest).Replace('sha256:', '')
}

# Running programs pick up a registry PATH change only after this broadcast.
function Send-EnvironmentChange {
    try {
        if (-not ('HarnessInstall.Native' -as [type])) {
            Add-Type -Namespace 'HarnessInstall' -Name 'Native' -MemberDefinition @'
[DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam, uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);
'@
        }
        $result = [UIntPtr]::Zero
        [void][HarnessInstall.Native]::SendMessageTimeout([IntPtr]0xffff, 0x1A, [UIntPtr]::Zero, 'Environment', 2, 5000, [ref]$result)
    } catch { Write-Log "environment change broadcast failed: $($_.Exception.Message)" }
}

function Expand-Zip([string]$Zip, [string]$Dest) {
    Assert-InTarget $Dest
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    if (Test-Path $Dest) { Remove-Item $Dest -Recurse -Force }
    [IO.Compression.ZipFile]::ExtractToDirectory($Zip, $Dest)
}

function Get-Arch {
    if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64' -or $env:PROCESSOR_ARCHITEW6432 -eq 'ARM64') { return 'arm64' }
    return 'x64'
}

# ---- backup-aware file writes --------------------------------------------------
function Get-HomeRelative([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    if ($full.StartsWith($HomeDir + '\', [StringComparison]::OrdinalIgnoreCase)) { return $full.Substring($HomeDir.Length + 1) }
    return ($full -replace '[:\\/]+', '_')
}

function Backup-File([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return }
    $dest = Join-Path $BackupDir (Get-HomeRelative $Path)
    Assert-InTarget $dest
    if (Test-Path -LiteralPath $dest) { return }
    if ($DryRun) { Write-Log "would back up $Path"; return }
    New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force | Out-Null
    Copy-Item -LiteralPath $Path -Destination $dest -Force
    $Script:BackedUp++
}

function Write-HarnessText([string]$Path, [string]$Text) {
    Assert-InTarget $Path
    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        $current = [IO.File]::ReadAllText($Path)
        if ($current -ceq $Text) { return $false }
        Backup-File $Path
    }
    if ($DryRun) { Write-Log "would write $Path"; return $true }
    $parent = Split-Path $Path -Parent
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    [IO.File]::WriteAllText($Path, $Text, $Utf8NoBom)
    $Script:Changed++
    Write-Log "wrote $Path"
    return $true
}

function Write-HarnessBytes([string]$Path, [byte[]]$Bytes) {
    Assert-InTarget $Path
    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        $current = [IO.File]::ReadAllBytes($Path)
        if ([Convert]::ToBase64String($current) -eq [Convert]::ToBase64String($Bytes)) { return $false }
        Backup-File $Path
    }
    if ($DryRun) { Write-Log "would write $Path"; return $true }
    $parent = Split-Path $Path -Parent
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    [IO.File]::WriteAllBytes($Path, $Bytes)
    $Script:Changed++
    Write-Log "wrote $Path"
    return $true
}

# ---- templating ----------------------------------------------------------------
function Get-Tokens {
    $t = [ordered]@{}
    $t['{{TEMP_JSON}}'] = $TempDir.Replace('\', '\\')
    $t['{{TEMP}}'] = $TempDir
    $t['{{REPO_JSON}}'] = $RepoPath.Replace('\', '\\')
    $t['{{REPO}}'] = $RepoPath
    $t['{{HOME_JSON}}'] = $HomeDir.Replace('\', '\\')
    $t['{{HOME_FWD}}'] = $HomeDir.Replace('\', '/')
    $t['{{HOME}}'] = $HomeDir
    $t['{{VERTEX_PROJECT}}'] = [string]$VertexProject
    $t['{{VERTEX_LOCATION}}'] = [string]$VertexLocation
    return $t
}

function Expand-Template([string]$Text) {
    $tokens = Get-Tokens
    foreach ($k in $tokens.Keys) { $Text = $Text.Replace($k, $tokens[$k]) }
    return $Text
}

function Test-Binary([byte[]]$Bytes) {
    $n = [Math]::Min($Bytes.Length, 8000)
    for ($i = 0; $i -lt $n; $i++) { if ($Bytes[$i] -eq 0) { return $true } }
    return $false
}

function Read-MergeJson([string]$Name) {
    $path = Join-Path $Script:BundleDir "merge\$Name"
    return (Expand-Template ([IO.File]::ReadAllText($path))) | ConvertFrom-Json
}

# ---- JSON merge helpers --------------------------------------------------------
function Set-Prop($Object, [string]$Name, $Value) {
    if ($Object.PSObject.Properties[$Name]) { $Object.$Name = $Value }
    else { $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value }
}

function Get-OrAddObject($Object, [string]$Name) {
    if (-not $Object.PSObject.Properties[$Name] -or $null -eq $Object.$Name -or $Object.$Name -isnot [psobject]) {
        Set-Prop $Object $Name (New-Object psobject)
    }
    return $Object.$Name
}

function Read-JsonFile([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return (New-Object psobject) }
    $raw = [IO.File]::ReadAllText($Path)
    if (-not $raw.Trim()) { return (New-Object psobject) }
    try { return ($raw | ConvertFrom-Json) }
    catch {
        throw ("could not parse $Path ($($_.Exception.Message.Split("`n")[0].Trim())). " +
            'It probably has comments or trailing commas: Windows PowerShell 5.1 cannot read JSONC. ' +
            "Remove them and rerun; the file was left unchanged. Backups of changed files: $BackupDir")
    }
}

function Write-JsonFile([string]$Path, $Object) {
    $json = $Object | ConvertTo-Json -Depth 32
    if (Test-Path -LiteralPath $Path) {
        # Skip the write when the content is already the same, whatever the formatting.
        $existing = (Read-JsonFile $Path) | ConvertTo-Json -Depth 32 -Compress
        if ($existing -ceq ($Object | ConvertTo-Json -Depth 32 -Compress)) { return $false }
    }
    return (Write-HarnessText $Path ($json + "`n"))
}

# V1 keys in a colleague's opencode.json stay exactly as they are: OpenCode 2.2.7
# migrates them on load next to the V2 keys this installer writes (verified with a
# config mixing theme, provider, agent, providers, agents and mcp.servers).
function Get-V1Keys($Config) {
    $found = @()
    foreach ($p in $Config.PSObject.Properties) { if ($OpenCodeV2Keys -notcontains $p.Name) { $found += $p.Name } }
    if ($Config.PSObject.Properties['mcp'] -and $Config.mcp -is [psobject]) {
        foreach ($p in $Config.mcp.PSObject.Properties) {
            if ($p.Name -ne 'servers' -and $p.Name -ne 'timeout') { $found += "mcp.$($p.Name)" }
        }
    }
    return $found
}

# ---- block upsert --------------------------------------------------------------
function Get-Block([string]$Text, [string]$Begin, [string]$End) {
    $start = $Text.IndexOf($Begin)
    if ($start -lt 0) { return $null }
    $stop = $Text.IndexOf($End, $start)
    if ($stop -lt 0) { return $null }
    return $Text.Substring($start, $stop + $End.Length - $start)
}

function Update-RuleBlocks([string]$Text, [string]$Source) {
    $nl = "`n"
    if ($Text.Contains("`r`n")) { $nl = "`r`n" }
    foreach ($pair in $RuleMarkers) {
        $block = Get-Block $Source $pair[0] $pair[1]
        if ($null -eq $block) { continue }
        if ($nl -eq "`r`n") { $block = $block.Replace("`r`n", "`n").Replace("`n", "`r`n") }
        else { $block = $block.Replace("`r`n", "`n") }
        $first = $Text.IndexOf($pair[0])
        if ($first -ge 0 -and $Text.IndexOf($pair[1], $first) -ge 0) {
            $existing = Get-Block $Text $pair[0] $pair[1]
            $Text = $Text.Substring(0, $first) + $block + $Text.Substring($first + $existing.Length)
            # Drop any later copies so a rerun never leaves duplicates.
            $after = $first + $block.Length
            while ($true) {
                $dup = $Text.IndexOf($pair[0], $after)
                if ($dup -lt 0) { break }
                $dupEnd = $Text.IndexOf($pair[1], $dup)
                if ($dupEnd -lt 0) { break }
                $Text = $Text.Substring(0, $dup).TrimEnd() + $nl + $Text.Substring($dupEnd + $pair[1].Length)
            }
        } else {
            if ($Text.Length -and -not $Text.EndsWith($nl)) { $Text += $nl }
            if ($Text.Length) { $Text += $nl }
            $Text += $block + $nl
        }
    }
    return $Text
}

# =================================================================================
# Steps
# =================================================================================
function Step-Preflight {
    Write-Log 'Preflight' 'STEP'
    if ([Environment]::OSVersion.Platform -ne 'Win32NT') { throw 'This installer supports Windows only.' }
    Write-Log ("PowerShell {0}, {1}, home {2}" -f $PSVersionTable.PSVersion, (Get-Arch), $HomeDir)
    if ($PSVersionTable.PSVersion.Major -lt 5) { throw 'PowerShell 5.1 or newer is required.' }
    try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch { }
    if ($Sandbox) { Write-Log "sandbox mode: writing under $HomeDir, apps, tools and sign-in skipped" }
    if ($DryRun) { Write-Log 'dry run: nothing is written' }
    $Script:HasWinget = Test-Command 'winget'
    if (-not $Script:HasWinget -and -not $SkipApps) { Add-Warning 'winget not found; using download fallbacks where they exist' }
    if (-not $Sandbox) {
        # Effective policy. Restricted blocks the npm and token-goat .ps1 shims, so it
        # changes automatically; AllSigned is a deliberate choice and is only changed
        # when the user agrees.
        $policy = [string](Get-ExecutionPolicy)
        $change = $false
        if ($policy -eq 'Restricted') { $change = $true }
        elseif ($policy -eq 'AllSigned') {
            if ($DryRun) { Write-Log 'execution policy is AllSigned; a real run asks before changing it' }
            elseif (Confirm-Step 'Execution policy is AllSigned. Set CurrentUser to RemoteSigned so the unsigned npm and token-goat shims can run?') { $change = $true }
            else { Add-Warning 'execution policy left at AllSigned: the unsigned .ps1 shims (npm, token-goat) will not run from PowerShell; use npm.cmd and token-goat.cmd' }
        }
        if ($change) {
            if ($DryRun) { Write-Log "would set CurrentUser execution policy to RemoteSigned (now $policy)" }
            else {
                try {
                    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
                    Write-Log "execution policy was $policy; set CurrentUser to RemoteSigned" 'OK'
                } catch { Add-Warning "could not set execution policy: $($_.Exception.Message)" }
            }
        }
    }
    Write-Log "log file: $LogFile"
}

function Install-Winget([string]$Id, [string]$Label) {
    if (-not $Script:HasWinget) { return $false }
    $common = @('install', '-e', '--id', $Id, '--silent', '--accept-package-agreements', '--accept-source-agreements', '--disable-interactivity')
    $code = Invoke-Native 'winget' ($common + @('--scope', 'user')) -Quiet
    if ($code -ne 0) {
        # Some manifests have no per-user installer; retry with the package default.
        Write-Log "$Label has no user-scope installer or it failed ($code); retrying without --scope"
        $code = Invoke-Native 'winget' $common -Quiet
    }
    if ($code -eq 0) { Write-Log "$Label installed" 'OK'; return $true }
    Add-Warning "$Label install through winget failed (exit $code)"
    return $false
}

function Test-Python312 {
    if (Test-Command 'py') {
        $v = Get-NativeOutput 'py' @('-3.12', '--version')
        if ($v -match 'Python 3\.12') { return $true }
    }
    $exe = Join-Path $LocalAppData 'Programs\Python\Python312\python.exe'
    return (Test-Path $exe)
}

function Get-OpenCodeDesktop {
    $exe = Join-Path $LocalAppData 'Programs\ai.opencode.desktop\OpenCode.exe'
    if (Test-Path $exe) { return $exe }
    $keys = Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall' -ErrorAction SilentlyContinue
    foreach ($k in $keys) {
        $p = Get-ItemProperty $k.PSPath -ErrorAction SilentlyContinue
        if ($p -and $p.PSObject.Properties['DisplayName'] -and $p.DisplayName -like 'OpenCode*') {
            if ($p.PSObject.Properties['InstallLocation'] -and $p.InstallLocation) { return (Join-Path $p.InstallLocation 'OpenCode.exe') }
            return $exe
        }
    }
    return $null
}

function Step-Apps {
    Write-Log 'Apps' 'STEP'
    if ($SkipApps) { Write-Log 'skipped (-SkipApps)'; return }

    if (Test-Command 'git') { Write-Log 'Git present' } else { [void](Install-Winget 'Git.Git' 'Git') }
    if (Test-Command 'gh') { Write-Log 'GitHub CLI present' } else { [void](Install-Winget 'GitHub.cli' 'GitHub CLI') }
    if (Test-Command 'copilot') { Write-Log 'Copilot CLI present' }
    elseif (-not (Install-Winget 'GitHub.Copilot' 'GitHub Copilot CLI')) { $Script:NeedCopilotNpm = $true; Write-Log 'Copilot CLI will be installed with npm after Node' }
    if (Test-Python312) { Write-Log 'Python 3.12 present' }
    elseif (-not (Install-Winget 'Python.Python.3.12' 'Python 3.12')) { $Script:NeedUvPython = $true; Write-Log 'Python 3.12 will come from uv after the tools step' }

    $desktop = Get-OpenCodeDesktop
    if ($desktop) { Write-Log "OpenCode Desktop present: $desktop" }
    else {
        # Not winget: its manifest is stale and downloads from a host that fails TLS
        # behind some corporate proxies. The GitHub release asset is per-user NSIS.
        $asset = 'opencode-desktop-win-{0}.exe' -f (Get-Arch)
        $url = "https://github.com/anomalyco/opencode/releases/download/v$OpenCodeVersion/$asset"
        $setup = Join-Path $TempDir $asset
        try {
            $digest = Get-OpenCodeDigest $asset
            Get-Download $url $setup
            if (-not $DryRun) {
                Assert-Sha256 $setup $digest "OpenCode Desktop $OpenCodeVersion"
                $proc = Start-Process -FilePath $setup -ArgumentList '/S', '/currentuser' -Wait -PassThru
                if ($proc.ExitCode -ne 0) {
                    Add-Warning "silent OpenCode Desktop setup returned $($proc.ExitCode); starting it interactively"
                    $proc = Start-Process -FilePath $setup -Wait -PassThru
                }
                if (Get-OpenCodeDesktop) { Write-Log "OpenCode Desktop $OpenCodeVersion installed" 'OK' }
                else { Add-Warning 'OpenCode Desktop did not appear after setup' }
            }
        } catch { Add-Warning "OpenCode Desktop install failed: $($_.Exception.Message)" }
    }

    if ($VertexProject) {
        if (Test-Command 'gcloud') { Write-Log 'Google Cloud SDK present' } else { [void](Install-Winget 'Google.CloudSDK' 'Google Cloud SDK') }
    }
    if ($WithClaudeCode) {
        if (Test-Command 'claude') { Write-Log 'Claude Code present' } else { [void](Install-Winget 'Anthropic.ClaudeCode' 'Claude Code') }
    }
    Update-SessionPath
}

function Step-Repo {
    Write-Log 'Master Repo' 'STEP'
    $gitDir = Join-Path $RepoPath '.git'
    if (Test-Path $gitDir) {
        if (-not (Test-Command 'git')) { Write-Log "repo present at $RepoPath; git missing, not updated" }
        else {
            $current = Get-NativeOutput 'git' @('-C', $RepoPath, 'rev-parse', '--abbrev-ref', 'HEAD')
            if ($current -ne $Branch) {
                Add-Warning "repo at $RepoPath is on branch '$current', not '$Branch'; left as it is"
            } else {
                $code = Invoke-Native 'git' @('-C', $RepoPath, 'fetch', 'origin', $Branch)
                if ($code -eq 0) { $code = Invoke-Native 'git' @('-C', $RepoPath, 'merge', '--ff-only', "origin/$Branch") }
                if ($code -eq 0) { Write-Log "repo up to date on $Branch" 'OK' }
                else { Add-Warning "could not fast-forward $RepoPath; using the files already there" }
            }
        }
    } elseif ((Test-Path $RepoPath) -and (Test-Path (Join-Path $RepoPath 'harness\install.ps1'))) {
        Write-Log "repo files present at $RepoPath without git history; using them"
    } elseif (Test-Command 'git') {
        $code = Invoke-Native 'git' @('clone', '--branch', $Branch, $RepoUrl, $RepoPath)
        if ($code -ne 0) { throw "git clone of $RepoUrl failed (exit $code)" }
        if ($DryRun) { Write-Log "would clone $RepoUrl to $RepoPath" } else { Write-Log "cloned to $RepoPath" 'OK' }
    } else {
        $zip = Join-Path $TempDir "master-repo-$Stamp.zip"
        $unpack = Join-Path $TempDir "master-repo-$Stamp"
        Get-Download ($RepoZipBase + $Branch) $zip
        if (-not $DryRun) {
            Expand-Zip $zip $unpack
            $root = Get-ChildItem $unpack -Directory | Select-Object -First 1
            if (-not $root) { throw 'repo zip was empty' }
            New-Item -ItemType Directory -Path $RepoPath -Force | Out-Null
            Copy-Item -Path (Join-Path $root.FullName '*') -Destination $RepoPath -Recurse -Force
            Remove-Item $unpack -Recurse -Force
            Remove-Item $zip -Force
        }
        Add-Warning "git missing: downloaded $Branch as a zip; the repo installer needs a git checkout and will be skipped"
    }
    $Script:BundleDir = Join-Path $RepoPath 'harness\files'
    if (-not $DryRun -and -not (Test-Path (Join-Path $Script:BundleDir 'home'))) {
        throw "harness bundle missing at $Script:BundleDir"
    }
}

function Add-UserPath([string]$Folder) {
    if ($NoPathUpdate) { Write-Log "User PATH left alone (-NoPathUpdate): $Folder"; return }
    # Read and write the raw registry value: [Environment]::GetEnvironmentVariable
    # expands %VAR% entries, and writing that back would freeze them for good.
    $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Environment', $true)
    try {
        $user = [string]$key.GetValue('Path', '', [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
        $parts = @()
        if ($user) { $parts = @($user.Split(';') | Where-Object { $_ }) }
        foreach ($p in $parts) {
            if ([Environment]::ExpandEnvironmentVariables($p).TrimEnd('\') -ieq $Folder.TrimEnd('\')) { return }
        }
        if ($DryRun) { Write-Log "would add $Folder to the user PATH"; return }
        $key.SetValue('Path', ((@($parts) + $Folder) -join ';'), [Microsoft.Win32.RegistryValueKind]::ExpandString)
    } finally { $key.Close() }
    Send-EnvironmentChange
    Write-Log "added $Folder to the user PATH" 'OK'
}

function Install-PortableNode {
    $nodeExe = Join-Path $NodeDir 'node.exe'
    if ((Test-Path $nodeExe) -and ((Get-NativeOutput $nodeExe @('--version')) -eq "v$NodeVersion")) {
        Write-Log "Node $NodeVersion present"; return
    }
    $name = "node-v$NodeVersion-win-$(Get-Arch)"
    $base = "https://nodejs.org/dist/v$NodeVersion"
    $zip = Join-Path $TempDir "$name.zip"
    $sums = Join-Path $TempDir "node-v$NodeVersion-SHASUMS256.txt"
    Get-Download "$base/$name.zip" $zip
    Get-Download "$base/SHASUMS256.txt" $sums
    if ($DryRun) { return }
    $expected = (Get-Content $sums | Where-Object { $_ -match "\s$([regex]::Escape($name)).zip$" } | Select-Object -First 1)
    if (-not $expected) { throw "no checksum for $name.zip in SHASUMS256.txt" }
    # Pinned hash first, then the published list as a second source.
    $expected = $expected.Split(' ')[0].Trim()
    if ($NodeVersion -eq '24.20.0' -and $expected -ne $NodeSha256[(Get-Arch)]) {
        throw "SHASUMS256.txt disagrees with the pinned Node hash: $expected"
    }
    Assert-Sha256 $zip $expected "Node $NodeVersion"
    $unpack = Join-Path $TempDir "node-unpack-$Stamp"
    Expand-Zip $zip $unpack
    New-Item -ItemType Directory -Path $NodeDir -Force | Out-Null
    Copy-Item -Path (Join-Path $unpack "$name\*") -Destination $NodeDir -Recurse -Force
    Remove-Item $unpack -Recurse -Force
    Remove-Item $zip, $sums -Force
    Write-Log "Node $NodeVersion installed to $NodeDir (checksum verified)" 'OK'
}

function Install-Uv {
    $uvExe = Join-Path $LocalBin 'uv.exe'
    if (Test-Path $uvExe) { Write-Log "uv present: $(Get-NativeOutput $uvExe @('--version'))"; return }
    New-Item -ItemType Directory -Path $LocalBin -Force | Out-Null
    # The pinned GitHub release zip, verified before unpacking. The astral.sh script
    # is not used: it would run unverified code.
    $arch = Get-Arch
    $triple = 'x86_64-pc-windows-msvc'
    if ($arch -eq 'arm64') { $triple = 'aarch64-pc-windows-msvc' }
    $zip = Join-Path $TempDir "uv-$UvVersion-$triple.zip"
    $unpack = Join-Path $TempDir "uv-$Stamp"
    Get-Download "https://github.com/astral-sh/uv/releases/download/$UvVersion/uv-$triple.zip" $zip
    if ($DryRun) { return }
    try {
        Assert-Sha256 $zip $UvSha256[$arch] "uv $UvVersion"
        Expand-Zip $zip $unpack
        Get-ChildItem $unpack -Recurse -Include 'uv.exe', 'uvx.exe', 'uvw.exe' | Copy-Item -Destination $LocalBin -Force
    } finally {
        if (Test-Path $unpack) { Remove-Item $unpack -Recurse -Force }
        if (Test-Path $zip) { Remove-Item $zip -Force }
    }
    if (Test-Path $uvExe) { Write-Log "uv installed: $(Get-NativeOutput $uvExe @('--version'))" 'OK' }
    else { throw 'uv install failed' }
}

function Get-NpmPackageVersion([string]$Name) {
    $pj = Join-Path $NodeDir ("node_modules\" + $Name.Replace('/', '\') + "\package.json")
    if (-not (Test-Path $pj)) { return '' }
    try { return [string]((Get-Content $pj -Raw | ConvertFrom-Json).version) } catch { return '' }
}

function Install-NpmPackages {
    $npm = Join-Path $NodeDir 'npm.cmd'
    $missing = @()
    $wanted = @($NpmPackages)
    if ($Script:NeedCopilotNpm) { $wanted += '@github/copilot' }
    foreach ($spec in $wanted) {
        $at = $spec.LastIndexOf('@')
        if ($at -gt 0) { $name = $spec.Substring(0, $at); $version = $spec.Substring($at + 1) } else { $name = $spec; $version = '' }
        $have = Get-NpmPackageVersion $name
        if ($have -and ($version -eq '' -or $have -eq $version)) { Write-Log "$name $have present" }
        else { $missing += $spec }
    }
    if ($missing.Count) {
        # Explicit --prefix: the portable Node owns these, and an existing custom
        # npm prefix elsewhere on the PC is never changed.
        $code = Invoke-Native $npm (@('install', '-g', '--prefix', $NodeDir, '--no-fund', '--no-audit') + $missing) -Quiet
        if ($code -eq 0) { Write-Log ("npm installed: " + ($missing -join ', ')) 'OK' }
        else { Add-Warning "npm install failed (exit $code) for: $($missing -join ', ')" }
    }

    # Playwright MCP launches its own chrome-for-testing build, not the chromium that
    # the playwright package downloads, so install it with the MCP's own CLI.
    $chrome = Get-PlaywrightChromeExe
    $mcpCli = Join-Path $NodeDir 'node_modules\@playwright\mcp\cli.js'
    if (Test-Path $chrome) { Write-Log "Playwright MCP browser present ($chrome)" }
    elseif (Test-Path $mcpCli) {
        $code = Invoke-Native (Join-Path $NodeDir 'node.exe') @($mcpCli, 'install-browser', 'chrome-for-testing') -Quiet
        if ($code -eq 0 -and (Test-Path $chrome)) { Write-Log 'Playwright MCP chrome-for-testing installed' 'OK' }
        elseif (-not $DryRun) {
            # Playwright's own downloader times out behind some corporate networks
            # where PowerShell's download works, so fetch the same zip that way.
            Write-Log "Playwright's downloader failed (exit $code); downloading the same build with PowerShell"
            Install-PlaywrightChromeFallback
            if (Test-Path $chrome) { Write-Log 'Playwright MCP chrome-for-testing installed' 'OK' }
            else { Add-Warning "Playwright MCP browser install failed (exit $code)" }
        }
    } elseif (-not $DryRun) { Add-Warning 'Playwright MCP missing; browser not installed' }
}

# The build Playwright MCP expects comes from the browsers.json of the
# playwright-core copy it loads, so the folder and version follow its pin.
function Get-PlaywrightChromeBuild {
    foreach ($rel in 'node_modules\@playwright\mcp\node_modules\playwright-core\browsers.json',
                     'node_modules\playwright-core\browsers.json') {
        $path = Join-Path $NodeDir $rel
        if (-not (Test-Path $path)) { continue }
        try {
            $entry = (Get-Content $path -Raw | ConvertFrom-Json).browsers | Where-Object { $_.name -eq 'chromium' } | Select-Object -First 1
            if ($entry) { return @{ Dir = "chromium-$($entry.revision)"; Version = [string]$entry.browserVersion } }
        } catch { }
    }
    return @{ Dir = $PlaywrightChrome; Version = '' }
}

function Get-PlaywrightChromeExe {
    return (Join-Path (Get-PlaywrightBrowsersDir) ((Get-PlaywrightChromeBuild).Dir + '\chrome-win64\chrome.exe'))
}

function Install-PlaywrightChromeFallback {
    $build = Get-PlaywrightChromeBuild
    if (-not $build.Version) { Add-Warning 'Playwright browsers.json not found; no fallback download'; return }
    if ((Get-Arch) -ne 'x64') { Add-Warning 'no Chrome for Testing fallback build for this CPU'; return }
    $revision = $build.Dir.Substring('chromium-'.Length)
    # install-browser chrome-for-testing fetches the browser and its headless shell.
    $parts = @(
        @{ Dir = $build.Dir; Zip = 'chrome-win64'; Exe = 'chrome.exe' },
        @{ Dir = "chromium_headless_shell-$revision"; Zip = 'chrome-headless-shell-win64'; Exe = 'chrome-headless-shell.exe' }
    )
    foreach ($part in $parts) {
        $target = Join-Path (Get-PlaywrightBrowsersDir) $part.Dir
        Assert-InTarget $target
        if (Test-Path (Join-Path $target "$($part.Zip)\$($part.Exe)")) { continue }
        $zip = Join-Path $TempDir "$($part.Zip)-$($build.Version).zip"
        $unpack = Join-Path $TempDir "$($part.Zip)-$Stamp"
        $pin = $null
        if ($ChromeSha256.ContainsKey($build.Version)) { $pin = $ChromeSha256[$build.Version][$part.Zip] }
        if (-not $pin) {
            Add-Warning "no pinned SHA-256 for Chrome for Testing $($build.Version) $($part.Zip); fallback skipped, rerun when Playwright's own installer can reach its CDN"
            continue
        }
        try {
            Get-Download "https://cdn.playwright.dev/builds/cft/$($build.Version)/win64/$($part.Zip).zip" $zip
            Assert-Sha256 $zip $pin "Chrome for Testing $($build.Version) $($part.Zip)"
            Expand-Zip $zip $unpack
            if (-not (Test-Path (Join-Path $unpack "$($part.Zip)\$($part.Exe)"))) { throw "zip had no $($part.Zip)\$($part.Exe)" }
            if (Test-Path $target) { Remove-Item $target -Recurse -Force }
            New-Item -ItemType Directory -Path $target -Force | Out-Null
            Move-Item (Join-Path $unpack $part.Zip) (Join-Path $target $part.Zip)
            # The marker Playwright writes after a finished install; without it a later
            # playwright install would treat the folder as partial and download again.
            [IO.File]::WriteAllText((Join-Path $target 'INSTALLATION_COMPLETE'), '', $Utf8NoBom)
            Write-Log "Playwright $($part.Dir) installed by fallback download"
        } catch { Add-Warning "Chrome for Testing fallback download failed for $($part.Dir): $($_.Exception.Message)" }
        finally {
            if (Test-Path $unpack) { Remove-Item $unpack -Recurse -Force }
            if (Test-Path $zip) { Remove-Item $zip -Force }
        }
    }
}

function Install-Graphify {
    $uv = Join-Path $LocalBin 'uv.exe'
    $graphify = Join-Path $LocalBin 'graphify.exe'
    $have = ''
    if (Test-Path $graphify) { $have = Get-NativeOutput $graphify @('--version') }
    if ($have -match [regex]::Escape($GraphifyVersion)) { Write-Log "graphify $GraphifyVersion present"; return }
    $uvArgs = @('tool', 'install', $GraphifySpec)
    if ($have) { $uvArgs = @('tool', 'install', '--force', $GraphifySpec) }
    # The configs point at .local\bin\graphify-mcp.exe, so pin the tool bin folder
    # there whatever UV_TOOL_BIN_DIR or XDG_BIN_HOME the PC already sets.
    $savedBin = $env:UV_TOOL_BIN_DIR
    $env:UV_TOOL_BIN_DIR = $LocalBin
    try { $code = Invoke-Native $uv $uvArgs -Quiet } finally { $env:UV_TOOL_BIN_DIR = $savedBin }
    if ($code -eq 0 -and -not $DryRun -and -not (Test-Path (Join-Path $LocalBin 'graphify-mcp.exe'))) {
        Add-Warning "graphify installed but graphify-mcp.exe is missing from $LocalBin"
    } elseif ($code -eq 0) { Write-Log "graphify $GraphifyVersion installed" 'OK' }
    else { Add-Warning "graphify install failed (exit $code)" }
}

function Install-LocalRag {
    $uv = Join-Path $LocalBin 'uv.exe'
    foreach ($name in 'kb.py', 'kb_extract.py', 'kb_graph.py', 'kb_store.py', 'requirements.txt') {
        Copy-BundleFile (Join-Path $Script:BundleDir "home\.local\lib\kb\$name") (Join-Path $KbDir $name)
    }
    Copy-BundleFile (Join-Path $Script:BundleDir 'home\.local\bin\local-rag.cmd') (Join-Path $LocalBin 'local-rag.cmd')
    $python = Join-Path $KbDir '.venv\Scripts\python.exe'
    if (-not (Test-Path $python)) {
        $code = Invoke-Native $uv @('venv', '--python', '3.12', (Join-Path $KbDir '.venv')) -Quiet
        if ($code -ne 0) { Add-Warning "local-rag venv creation failed (exit $code)"; return }
    }
    $reqs = Join-Path $KbDir 'requirements.txt'
    $marker = Join-Path $KbDir '.venv\harness-requirements.sha256'
    $hash = ''
    if (Test-Path $reqs) { $hash = (Get-Sha256 $reqs) }
    if ((Test-Path $marker) -and ((Get-Content $marker -Raw).Trim() -eq $hash)) { Write-Log 'local-rag packages present'; return }
    $code = Invoke-Native $uv @('pip', 'install', '--python', $python, '-r', $reqs) -Quiet
    if ($code -eq 0) {
        if (-not $DryRun) { [IO.File]::WriteAllText($marker, $hash, $Utf8NoBom) }
        Write-Log 'local-rag packages installed' 'OK'
    } else { Add-Warning "local-rag package install failed (exit $code)" }
}

function Step-Tools {
    Write-Log 'Tools' 'STEP'
    if ($SkipTools) { Write-Log 'skipped (-SkipTools)'; return }
    $tasks = @(
        @{ Name = 'portable Node'; Run = { Install-PortableNode } },
        @{ Name = 'uv'; Run = { Install-Uv } },
        @{ Name = 'PATH'; Run = { Add-UserPath $NodeDir; Add-UserPath $LocalBin; Update-SessionPath } },
        @{ Name = 'npm packages'; Run = { Install-NpmPackages } },
        @{ Name = 'graphify'; Run = { Install-Graphify } },
        @{ Name = 'local-rag'; Run = { Install-LocalRag } }
    )
    if ($Sandbox) {
        # Guard failures here are not warnings: they stop the run before any tool starts.
        foreach ($p in $NodeDir, $LocalBin, $KbDir, $TempDir, $BackupDir, $LogFile) { Assert-InTarget $p }
        Enter-ToolSandbox
    }
    try {
        foreach ($task in $tasks) {
            try { & $task.Run }
            catch {
                if ($_.Exception.Message -like 'SAFETY:*') { throw }
                Add-Warning "$($task.Name) failed: $($_.Exception.Message)"
            }
        }
        if ($Script:NeedUvPython) {
            $code = Invoke-Native (Join-Path $LocalBin 'uv.exe') @('python', 'install', '3.12', '--default') -Quiet
            if ($code -eq 0) { Write-Log 'Python 3.12 installed through uv' 'OK' } else { Add-Warning 'uv python install 3.12 failed' }
        }
    } finally { Exit-ToolSandbox }
}

function Copy-BundleFile([string]$Source, [string]$Dest) {
    $bytes = [IO.File]::ReadAllBytes($Source)
    if (Test-Binary $bytes) { return (Write-HarnessBytes $Dest $bytes) }
    return (Write-HarnessText $Dest (Expand-Template ([IO.File]::ReadAllText($Source))))
}

function Find-Python {
    $candidates = @()
    if (Test-Command 'py') {
        $p = Get-NativeOutput 'py' @('-3.12', '-c', 'import sys; print(sys.executable)')
        if (-not $p) { $p = Get-NativeOutput 'py' @('-3', '-c', 'import sys; print(sys.executable)') }
        if ($p) { $candidates += $p }
    }
    foreach ($name in 'python', 'python3') {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        # The WindowsApps entry is the Store stub, which opens the Store instead of running.
        if ($cmd -and $cmd.Source -notmatch '\\WindowsApps\\') { $candidates += $cmd.Source }
    }
    $uv = Join-Path $LocalBin 'uv.exe'
    if (Test-Path $uv) { $p = Get-NativeOutput $uv @('python', 'find', '3.12'); if ($p) { $candidates += $p } }
    foreach ($c in $candidates) { if ($c -and (Test-Path $c)) { return $c } }
    return $null
}

function Invoke-RepoInstaller {
    $script = Join-Path $RepoPath 'scripts\install_auto_mode.py'
    if (-not (Test-Path $script)) { Add-Warning "repo installer not found at $script"; return }
    if (-not (Test-Path (Join-Path $RepoPath '.git'))) { Add-Warning 'repo is not a git checkout; repo installer skipped'; return }
    $python = Find-Python
    if (-not $python) { Add-Warning 'Python not found; repo installer skipped (rerun after installing Python 3.12)'; return }

    # The repo installer upserts its own MASTER-REPO-USE block and keeps .bak copies
    # beside the files it touches. Step c writes the snapshot block over it anyway,
    # so keep the instruction file as it was and clear the redundant copies; the
    # original is in the harness backup whenever step c changes it.
    $instructions = Join-Path $HomeDir '.copilot\copilot-instructions.md'
    $stateDir = Join-Path $HomeDir '.master-repo-auto'
    $watch = @((Join-Path $HomeDir '.copilot'), $stateDir, (Join-Path $HomeDir '.copilot\hooks'))
    $before = @{}
    foreach ($d in $watch) { if (Test-Path $d) { Get-ChildItem $d -File | ForEach-Object { $before[$_.FullName] = $true } } }
    $savedInstructions = $null
    if (Test-Path $instructions) { $savedInstructions = [IO.File]::ReadAllBytes($instructions) }
    $hookFile = Join-Path $HomeDir '.copilot\hooks\master-repo-auto.json'
    $savedHook = $null
    if (Test-Path $hookFile) { $savedHook = [IO.File]::ReadAllBytes($hookFile) }

    $pyArgs = @($script, '--repo', $RepoPath, '--home', $HomeDir, '--client', 'copilot')
    if ($DryRun) { $pyArgs += '--dry-run' }
    $code = Invoke-Native $python $pyArgs -Quiet
    if ($DryRun) { return }

    if ($null -ne $savedInstructions) { [IO.File]::WriteAllBytes($instructions, $savedInstructions) }
    if ($null -ne $savedHook -and (Test-Path $hookFile) -and
        [Convert]::ToBase64String([IO.File]::ReadAllBytes($hookFile)) -ne [Convert]::ToBase64String($savedHook)) {
        $dest = Join-Path $BackupDir (Get-HomeRelative $hookFile)
        Assert-InTarget $dest
        New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force | Out-Null
        [IO.File]::WriteAllBytes($dest, $savedHook)
        $Script:BackedUp++
    }
    foreach ($d in $watch) {
        if (-not (Test-Path $d)) { continue }
        foreach ($f in Get-ChildItem $d -File) {
            if ($before.ContainsKey($f.FullName) -or $f.Name -notmatch '\.bak(\.[0-9a-f]{32})?$') { continue }
            $original = Join-Path $f.DirectoryName ($f.Name -replace '\.bak(\.[0-9a-f]{32})?$', '')
            $same = (Test-Path $original) -and ((Get-Sha256 $original) -eq (Get-Sha256 $f.FullName))
            $isInstructions = ($original -ieq $instructions)
            if ($same -or $isInstructions) { Remove-Item $f.FullName -Force }
        }
    }
    if ($code -eq 0) { Write-Log 'repo installer: master-repo-auto hooks and skills registered' 'OK' }
    else {
        # On reruns it refuses to overwrite skills the snapshot replaced; expected.
        $tail = @($Script:LastNativeOutput | Where-Object { $_ -match '\bREFUSED:' })
        $onlySkills = $tail.Count -gt 0 -and -not ($tail | Where-Object { $_ -notmatch 'customized skills left unchanged' })
        if ($onlySkills) { Write-Log 'repo installer kept the harness copies of skills it also ships (expected on reruns)' }
        else { Add-Warning "repo installer exited $code; see $LogFile" }
    }
}

function Copy-HomeFiles {
    $root = Join-Path $Script:BundleDir 'home'
    $skipRel = @('.config\opencode\AGENTS.md', '.copilot\copilot-instructions.md')
    $count = 0
    foreach ($f in Get-ChildItem $root -Recurse -File -Force) {
        $rel = $f.FullName.Substring($root.Length + 1)
        if ($skipRel -contains $rel) { continue }
        [void](Copy-BundleFile $f.FullName (Join-Path $HomeDir $rel))
        $count++
    }
    Write-Log "harness files checked: $count" 'OK'
}

function Update-RuleFiles {
    foreach ($rel in '.config\opencode\AGENTS.md', '.copilot\copilot-instructions.md') {
        $source = Expand-Template ([IO.File]::ReadAllText((Join-Path $Script:BundleDir "home\$rel")))
        $dest = Join-Path $HomeDir $rel
        $text = ''
        if (Test-Path $dest) { $text = [IO.File]::ReadAllText($dest) }
        # Unbalanced markers mean someone edited a block by hand; replacing or
        # appending could eat their text, so leave the file for them to fix.
        $broken = @($RuleMarkers | Where-Object {
            ([regex]::Matches($text, [regex]::Escape($_[0]))).Count -ne ([regex]::Matches($text, [regex]::Escape($_[1]))).Count })
        if ($broken.Count) {
            Add-Warning "$rel has unbalanced markers ($($broken[0][0])); rule blocks not updated, fix the file and rerun"
            continue
        }
        $new = Update-RuleBlocks $text $source
        if (Write-HarnessText $dest $new) { Write-Log "rule blocks updated in $rel" 'OK' }
        else { Write-Log "rule blocks current in $rel" }
    }
}

function Update-OpenCodeConfig {
    $dir = Join-Path $HomeDir '.config\opencode'
    $path = Join-Path $dir 'opencode.json'
    if (Test-Path (Join-Path $dir 'opencode.jsonc')) {
        Add-Warning 'opencode.jsonc exists next to opencode.json; OpenCode may prefer it, so merge the harness keys there by hand'
    }
    $ours = Read-MergeJson 'opencode.json'
    $cfg = Read-JsonFile $path
    $legacy = @(Get-V1Keys $cfg)
    if ($legacy.Count) { Write-Log ("V1 keys left as-is (OpenCode migrates them on load): " + ($legacy -join ', ')) }

    if (-not $cfg.PSObject.Properties['$schema']) { Set-Prop $cfg '$schema' $ours.'$schema' }
    Set-Prop $cfg 'default_agent' $ours.default_agent
    $agents = Get-OrAddObject $cfg 'agents'
    foreach ($p in $ours.agents.PSObject.Properties) { Set-Prop $agents $p.Name $p.Value }

    $mcp = Get-OrAddObject $cfg 'mcp'
    $servers = Get-OrAddObject $mcp 'servers'
    foreach ($p in $ours.mcp.servers.PSObject.Properties) { Set-Prop $servers $p.Name $p.Value }
    $ollama = Join-Path $LocalAppData 'Programs\Ollama\ollama.exe'
    if (Test-Path $ollama) {
        $optional = Read-MergeJson 'opencode-optional-mcp.json'
        if ($optional.PSObject.Properties['ollama']) {
            $server = $optional.ollama
            $server.command = @($ollama, 'serve')
            Set-Prop $servers 'ollama' $server
            Write-Log 'Ollama found; ollama MCP server added'
        }
    }

    $skills = @()
    if ($cfg.PSObject.Properties['skills'] -and $cfg.skills) { $skills = @($cfg.skills) }
    foreach ($s in @($ours.skills)) { if (-not ($skills | Where-Object { $_ -ieq $s })) { $skills += $s } }
    Set-Prop $cfg 'skills' ([object[]]$skills)

    # Only the V2 "plugins" key is touched; a V1 "plugin" key stays as it is.
    $plugins = @()
    if ($cfg.PSObject.Properties['plugins'] -and $cfg.plugins) { $plugins = @($cfg.plugins) }
    $browserPlugin = Join-Path $LocalAppData 'OpenCode\browser\plugin.mjs'
    if (Test-Path $browserPlugin) {
        $entry = 'file:///' + $browserPlugin.Replace('\', '/')
        if (-not ($plugins | Where-Object { $_ -is [string] -and $_ -ieq $entry })) { $plugins += $entry }
    }
    if ($plugins.Count) { Set-Prop $cfg 'plugins' ([object[]]$plugins) }

    if ($VertexProject) {
        $providers = Get-OrAddObject $cfg 'providers'
        $vertex = Read-MergeJson 'vertex-provider.json'
        Set-Prop $providers 'google-vertex' $vertex.'google-vertex'
    }
    if (Write-JsonFile $path $cfg) { Write-Log 'opencode.json merged' 'OK' } else { Write-Log 'opencode.json current' }
}

function Update-CopilotJson {
    $mcpPath = Join-Path $HomeDir '.copilot\mcp-config.json'
    $cfg = Read-JsonFile $mcpPath
    $servers = Get-OrAddObject $cfg 'mcpServers'
    $ours = Read-MergeJson 'copilot-mcp-config.json'
    foreach ($p in $ours.mcpServers.PSObject.Properties) { Set-Prop $servers $p.Name $p.Value }
    if (Write-JsonFile $mcpPath $cfg) { Write-Log 'Copilot mcp-config.json merged' 'OK' } else { Write-Log 'Copilot mcp-config.json current' }

    $setPath = Join-Path $HomeDir '.copilot\settings.json'
    $settings = Read-JsonFile $setPath
    $plugins = Get-OrAddObject $settings 'enabledPlugins'
    $oursSettings = Read-MergeJson 'copilot-settings.json'
    foreach ($p in $oursSettings.enabledPlugins.PSObject.Properties) { Set-Prop $plugins $p.Name $p.Value }
    if (Write-JsonFile $setPath $settings) { Write-Log 'Copilot settings.json merged' 'OK' } else { Write-Log 'Copilot settings.json current' }
}

function Step-HarnessFiles {
    Write-Log 'Harness files' 'STEP'
    if (-not (Test-Path (Join-Path $Script:BundleDir 'home'))) {
        if ($DryRun) { Write-Log 'harness files: would be written after the clone'; return }
        throw "harness bundle missing at $Script:BundleDir"
    }
    $termsFile = Join-Path $HomeDir '.config\harness\leak-terms.txt'
    if (-not $Sandbox -and (Test-Path $termsFile)) {
        Add-Warning 'this looks like the harness owner''s PC (leak-terms.txt exists): the snapshot would rewrite the owner''s rule files, agents and skills, and add V2 keys to opencode.json'
        if ($DryRun) { Write-Log 'dry run: a real run asks before writing harness files here' }
        elseif (-not (Confirm-Step 'Write the harness files on this PC anyway?')) { Write-Log 'harness files skipped on the owner PC'; return }
    }
    Write-Log "backups of changed files go to $BackupDir"
    try { Invoke-RepoInstaller } catch { Add-Warning "repo installer failed: $($_.Exception.Message)" }
    Copy-HomeFiles
    Update-RuleFiles
    try { Update-OpenCodeConfig } catch { Add-Warning "opencode.json merge failed: $($_.Exception.Message)" }
    try { Update-CopilotJson } catch { Add-Warning "Copilot JSON merge failed: $($_.Exception.Message)" }
}

function Find-OpenCodeCli {
    $hit = Get-ChildItem (Join-Path $RoamingAppData 'ai.opencode.desktop\cli\*\opencode-cli.exe') -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($hit) { return $hit.FullName }
    return $null
}

function Step-SignIn {
    Write-Log 'Sign-in' 'STEP'
    if ($NoSignIn) { Write-Log 'skipped (-NoSignIn)'; return }
    if ($DryRun) { Write-Log 'dry run: sign-in skipped'; return }
    if (-not (Test-Interactive)) { Write-Log 'not interactive; run the sign-in commands from the summary later'; return }

    if ((Test-Command 'copilot') -and (Confirm-Step 'Sign in to GitHub Copilot CLI now?')) {
        try { & copilot login } catch { Add-Warning "copilot login failed: $($_.Exception.Message)" }
    }

    if (Confirm-Step 'Sign in OpenCode to GitHub Copilot now?') {
        $cli = Find-OpenCodeCli
        if (-not $cli) {
            $desktop = Get-OpenCodeDesktop
            if ($desktop -and (Test-Path $desktop)) {
                Write-Log 'starting OpenCode once so it unpacks its CLI (up to 90 s)'
                Start-Process -FilePath $desktop | Out-Null
                for ($i = 0; $i -lt 30 -and -not $cli; $i++) { Start-Sleep -Seconds 3; $cli = Find-OpenCodeCli }
            }
        }
        if ($cli) {
            Write-Host '    Enter the device code at https://github.com/login/device' -ForegroundColor Cyan
            try { & $cli auth login github-copilot --method device --answer deploymentType=github.com }
            catch { Add-Warning "OpenCode sign-in failed: $($_.Exception.Message)" }
        } else { Add-Warning 'opencode-cli.exe not found; open OpenCode Desktop and sign in from its settings' }
    }

    if (Test-Command 'gh') {
        $ErrorActionPreference = 'Continue'
        & gh auth status 2>&1 | Out-Null
        $signedIn = ($LASTEXITCODE -eq 0)
        $ErrorActionPreference = 'Stop'
        if ($signedIn) { Write-Log 'gh already signed in' }
        elseif (Confirm-Step 'Sign in the GitHub CLI (gh) now?') {
            try { & gh auth login } catch { Add-Warning "gh auth login failed: $($_.Exception.Message)" }
        }
    }

    if ($VertexProject -and (Test-Command 'gcloud') -and (Confirm-Step "Sign in Google Cloud for Vertex project $VertexProject now?")) {
        try {
            & gcloud auth application-default login
            & gcloud auth application-default set-quota-project $VertexProject
        } catch { Add-Warning "gcloud sign-in failed: $($_.Exception.Message)" }
    }
}

function Step-Summary {
    Write-Log 'Summary' 'STEP'
    $probe = [ordered]@{
        'node'       = @((Join-Path $NodeDir 'node.exe'), '--version')
        'uv'         = @((Join-Path $LocalBin 'uv.exe'), '--version')
        'graphify'   = @((Join-Path $LocalBin 'graphify.exe'), '--version')
        'token-goat' = @((Join-Path $NodeDir 'token-goat.cmd'), '--version')
        'copilot'    = @('copilot', '--version')
    }
    foreach ($k in $probe.Keys) {
        $exe = $probe[$k][0]
        $v = ''
        if ((Test-Path $exe) -or (Test-Command $exe)) { $v = (Get-NativeOutput $exe @($probe[$k][1])) -split "`n" | Select-Object -First 1 }
        if (-not $v) { $v = 'not found' }
        Write-Log ('{0,-11} {1}' -f $k, $v)
    }

    $skillCount = 0
    foreach ($rel in '.copilot\skills', '.config\opencode\skills', '.claude\skills') {
        $d = Join-Path $Script:BundleDir "home\$rel"
        if (Test-Path $d) { $skillCount += @(Get-ChildItem $d -Directory).Count }
    }
    $ocServers = 0; $cpServers = 0
    try { $ocServers = @((Read-JsonFile (Join-Path $HomeDir '.config\opencode\opencode.json')).mcp.servers.PSObject.Properties).Count } catch { }
    try { $cpServers = @((Read-JsonFile (Join-Path $HomeDir '.copilot\mcp-config.json')).mcpServers.PSObject.Properties).Count } catch { }
    Write-Log "skills written: $skillCount; MCP servers: OpenCode $ocServers, Copilot CLI $cpServers"
    Write-Log "files changed: $($Script:Changed); backed up: $($Script:BackedUp)"
    if ($Script:BackedUp -gt 0) { Write-Log "backup folder: $BackupDir" }

    if (-not $SkipTools) {
        $chrome = Get-PlaywrightChromeExe
        if (Test-Path $chrome) { Write-Log "Playwright MCP browser: $chrome" }
        else { Add-Warning "Playwright MCP browser missing ($chrome); run: & `"$NodeDir\node.exe`" `"$NodeDir\node_modules\@playwright\mcp\cli.js`" install-browser chrome-for-testing" }
    }

    Write-Host ''
    if ($Script:Warnings.Count) {
        Write-Host "Finished with $($Script:Warnings.Count) warning(s):" -ForegroundColor Yellow
        foreach ($w in $Script:Warnings) { Write-Host "  - $w" -ForegroundColor Yellow }
    } else { Write-Host 'Finished without warnings.' -ForegroundColor Green }
    Write-Host ''
    Write-Host 'Next steps:'
    Write-Host '  1. Open a new terminal so PATH changes apply.'
    Write-Host '  2. Run "copilot" in a project folder; the CaveCrew agents and skills load automatically.'
    Write-Host '  3. Open OpenCode Desktop; the orchestrator agent is the default.'
    $cli = Find-OpenCodeCli
    $cliHint = 'opencode-cli.exe (appears under %APPDATA%\ai.opencode.desktop\cli\ after OpenCode Desktop first starts)'
    if ($cli) { $cliHint = "& `"$cli`"" }
    Write-Host '  4. Missed a sign-in? Run any of:'
    Write-Host '       copilot login'
    Write-Host '       gh auth login'
    Write-Host "       $cliHint auth login github-copilot --method device --answer deploymentType=github.com"
    Write-Host "Log: $LogFile"
}

# =================================================================================
# Main
# =================================================================================
$Script:Failed = $false
try {
    Step-Preflight
    Step-Apps
    Step-Repo
    Step-Tools
    Step-HarnessFiles
    Step-SignIn
    Step-Summary
} catch {
    $Script:Failed = $true
    Write-Log "Install stopped: $($_.Exception.Message)" 'ERROR'
    Write-Log "Log: $LogFile" 'ERROR'
}
# A script file may set an exit code; under irm | iex exit would close the window.
if ($Script:Failed -and $PSCommandPath) { exit 1 }

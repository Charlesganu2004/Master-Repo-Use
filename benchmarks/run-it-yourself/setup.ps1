# Set up the 600-token harness test on Windows.
#
#   powershell -ExecutionPolicy Bypass -File benchmarks\run-it-yourself\setup.ps1
#
# Installs graphify into its own virtual environment under your home folder,
# puts a shim on your PATH if one is already there, indexes this repository
# locally (no API key, nothing leaves the machine), and writes the eight prompts.

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..").Path
$home_graphify = Join-Path $HOME ".graphify"
$venv = Join-Path $home_graphify "venv"
$exe = Join-Path $venv "Scripts\graphify.exe"

Write-Host "1. graphify" -ForegroundColor Cyan
if (Test-Path $exe) {
    Write-Host "   already installed: $(& $exe --version)"
} else {
    New-Item -ItemType Directory -Force -Path $home_graphify | Out-Null
    python -m venv $venv
    & (Join-Path $venv "Scripts\python.exe") -m pip install --quiet --disable-pip-version-check graphifyy
    Write-Host "   installed: $(& $exe --version)"
}

$binDir = Join-Path $HOME "bin"
if (Test-Path $binDir) {
    Set-Content -Path (Join-Path $binDir "graphify.cmd") -Encoding ascii -Value "@echo off`r`n`"$exe`" %*"
    Write-Host "   shim written to $binDir\graphify.cmd"
} else {
    Write-Host "   no $binDir on this machine; call graphify by full path: $exe"
}

Write-Host "2. index this repository (local AST only, no model)" -ForegroundColor Cyan
& $exe extract $repo --code-only --no-cluster | Select-Object -Last 2

Write-Host "3. write the prompts" -ForegroundColor Cyan
python (Join-Path $PSScriptRoot "harness\build_arms.py")

Write-Host ""
Write-Host "Ready. Next:" -ForegroundColor Green
Write-Host "  - paste any file from benchmarks\run-it-yourself\arms\<task>\<arm>.prompt.md into your assistant"
Write-Host "  - save each reply as benchmarks\run-it-yourself\answers\<task>\<arm>.md"
Write-Host "  - python benchmarks\run-it-yourself\harness\score.py"

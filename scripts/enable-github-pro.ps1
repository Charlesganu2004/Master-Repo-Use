<#
.SYNOPSIS
  One-time GitHub Pro bootstrap for Master-Repo-Use.

.DESCRIPTION
  Enables Pages (Actions build type), sets least-privilege workflow permissions,
  protects main, then verifies. Pages is dispatched at most once, and only after
  the API confirms Pages is actually enabled — repeatedly re-dispatching a
  deployment that cannot succeed just burns Actions minutes.

.EXAMPLE
  .\scripts\enable-github-pro.ps1
  .\scripts\enable-github-pro.ps1 -VerifyOnly
  .\scripts\enable-github-pro.ps1 -RunAudit
#>
param(
  [string]$Repository = 'Charlesganu2004/Master-Repo-Use',
  [switch]$VerifyOnly,
  [switch]$RunAudit
)

$ErrorActionPreference = 'Stop'
$ApiVersion = '2022-11-28'
$Root = Split-Path -Parent $PSScriptRoot

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  throw 'GitHub CLI (gh) is required: https://cli.github.com'
}

gh auth status | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'GitHub CLI is not authenticated. Run: gh auth login' }

function Invoke-GhApi {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest)
  gh api -H 'Accept: application/vnd.github+json' -H "X-GitHub-Api-Version: $ApiVersion" @Rest
}

function Invoke-GhJson {
  param(
    [Parameter(Mandatory = $true)][string]$Method,
    [Parameter(Mandatory = $true)][string]$Endpoint,
    [Parameter(Mandatory = $true)][string]$Json
  )
  $Json | gh api --method $Method `
    -H 'Accept: application/vnd.github+json' `
    -H "X-GitHub-Api-Version: $ApiVersion" `
    $Endpoint --input - | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "GitHub API failed: $Method $Endpoint" }
}

function Test-PagesEnabled {
  gh api -H 'Accept: application/vnd.github+json' -H "X-GitHub-Api-Version: $ApiVersion" "repos/$Repository/pages" *> $null
  return ($LASTEXITCODE -eq 0)
}

function Get-GhField {
  param([string]$Endpoint, [string]$Jq)
  $value = Invoke-GhApi $Endpoint --jq $Jq
  if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($value)) { return 'unavailable' }
  return $value.Trim()
}

if (-not $VerifyOnly) {
  Write-Host '[1/3] Enabling GitHub Pages with Actions publishing...' -ForegroundColor Cyan
  if (Test-PagesEnabled) {
    Write-Host '      Pages already enabled; ensuring build_type=workflow.'
    Invoke-GhJson -Method PUT -Endpoint "repos/$Repository/pages" -Json '{"build_type":"workflow"}'
  } else {
    Invoke-GhJson -Method POST -Endpoint "repos/$Repository/pages" -Json '{"build_type":"workflow"}'
  }

  Write-Host '[2/3] Setting least-privilege workflow permissions...' -ForegroundColor Cyan
  # Read-only GITHUB_TOKEN by default; each workflow widens what it needs.
  # can_approve_pull_request_reviews lets the owner-approved job OPEN a PR. It cannot
  # merge main: CODEOWNERS requires a review from @Charlesganu2004, and the bot is
  # not a code owner.
  Invoke-GhJson -Method PUT -Endpoint "repos/$Repository/actions/permissions/workflow" `
    -Json '{"default_workflow_permissions":"read","can_approve_pull_request_reviews":true}'

  Write-Host '[3/3] Protecting main with PR + Code Owner approval...' -ForegroundColor Cyan
  gh api --method PUT `
    -H 'Accept: application/vnd.github+json' `
    -H "X-GitHub-Api-Version: $ApiVersion" `
    "repos/$Repository/branches/main/protection" `
    --input (Join-Path $Root 'scripts\branch-protection.json') | Out-Null
  if ($LASTEXITCODE -ne 0) { throw 'Failed to enable main branch protection.' }
}

Write-Host ''
Write-Host '=== Verification ===' -ForegroundColor Cyan
Write-Host ("has_pages:            " + (Get-GhField "repos/$Repository" '.has_pages'))
if (Test-PagesEnabled) {
  Write-Host ("pages build_type:     " + (Get-GhField "repos/$Repository/pages" '.build_type'))
  Write-Host ("pages url:            " + (Get-GhField "repos/$Repository/pages" '.html_url'))
}
Write-Host ("main protected:       " + (Get-GhField "repos/$Repository/branches/main" '.protected'))
$protection = "repos/$Repository/branches/main/protection"
Write-Host ("required PR reviews:  " + (Get-GhField $protection '.required_pull_request_reviews.required_approving_review_count // "none"'))
Write-Host ("code owner reviews:   " + (Get-GhField $protection '.required_pull_request_reviews.require_code_owner_reviews // false'))
Write-Host ("force pushes allowed: " + (Get-GhField $protection '.allow_force_pushes.enabled'))
Write-Host ("deletions allowed:    " + (Get-GhField $protection '.allow_deletions.enabled'))

if ($VerifyOnly) { return }

Write-Host ''
if (Test-PagesEnabled) {
  Write-Host 'Dispatching the Pages deployment once...' -ForegroundColor Cyan
  gh workflow run pages.yml -R $Repository
  if ($LASTEXITCODE -ne 0) { throw 'Failed to dispatch Pages workflow.' }
} else {
  Write-Host 'Pages is still not enabled, so no deployment was dispatched.' -ForegroundColor Yellow
  Write-Host "Enable it at https://github.com/$Repository/settings/pages (Source: GitHub Actions), then re-run this script."
}

if ($RunAudit) {
  Write-Host 'Dispatching one catalog audit...' -ForegroundColor Cyan
  gh workflow run catalog-guardian.yml -R $Repository
  if ($LASTEXITCODE -ne 0) { throw 'Failed to dispatch Catalog Guardian.' }
} else {
  Write-Host 'Catalog audit not dispatched (it runs weekly). Pass -RunAudit to seed one now.'
}

Write-Host ''
Write-Host 'GitHub Pro bootstrap complete.' -ForegroundColor Green
Write-Host '  Pages:           https://charlesganu2004.github.io/Master-Repo-Use/'
Write-Host "  Audit trail:     https://github.com/$Repository/issues"
Write-Host "  Main protection: https://github.com/$Repository/settings/branches"
Write-Host ''
Write-Host 'Deep catalog maintenance still requires your exact owner comment: APPROVE CATALOG MAINTENANCE' -ForegroundColor Yellow

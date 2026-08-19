param(
  [string]$Repository = 'Charlesganu2004/Master-Repo-Use'
)

$ErrorActionPreference = 'Stop'
$ApiVersion = '2026-03-10'
$Root = Split-Path -Parent $PSScriptRoot

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  throw 'GitHub CLI (gh) is required.'
}

gh auth status | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'GitHub CLI is not authenticated.' }

function Invoke-GhJson {
  param(
    [Parameter(Mandatory=$true)][string]$Method,
    [Parameter(Mandatory=$true)][string]$Endpoint,
    [Parameter(Mandatory=$true)][string]$Json
  )
  $Json | gh api --method $Method `
    -H 'Accept: application/vnd.github+json' `
    -H "X-GitHub-Api-Version: $ApiVersion" `
    $Endpoint --input - | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "GitHub API failed: $Method $Endpoint" }
}

Write-Host '[1/4] Enabling GitHub Pages with Actions publishing...' -ForegroundColor Cyan
gh api -H 'Accept: application/vnd.github+json' -H "X-GitHub-Api-Version: $ApiVersion" "repos/$Repository/pages" *> $null
if ($LASTEXITCODE -eq 0) {
  Invoke-GhJson -Method PUT -Endpoint "repos/$Repository/pages" -Json '{"build_type":"workflow"}'
} else {
  Invoke-GhJson -Method POST -Endpoint "repos/$Repository/pages" -Json '{"build_type":"workflow"}'
}

Write-Host '[2/4] Allowing owner-approved workflows to create pull requests...' -ForegroundColor Cyan
Invoke-GhJson -Method PUT -Endpoint "repos/$Repository/actions/permissions/workflow" -Json '{"default_workflow_permissions":"read","can_approve_pull_request_reviews":true}'

Write-Host '[3/4] Protecting main with PR + Code Owner approval...' -ForegroundColor Cyan
gh api --method PUT `
  -H 'Accept: application/vnd.github+json' `
  -H "X-GitHub-Api-Version: $ApiVersion" `
  "repos/$Repository/branches/main/protection" `
  --input "$Root\scripts\branch-protection.json" | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Failed to enable main branch protection.' }

Write-Host '[4/4] Starting first Pages deployment and catalog audit...' -ForegroundColor Cyan
gh workflow run pages.yml -R $Repository
if ($LASTEXITCODE -ne 0) { throw 'Failed to dispatch Pages workflow.' }
gh workflow run catalog-guardian.yml -R $Repository
if ($LASTEXITCODE -ne 0) { throw 'Failed to dispatch Catalog Guardian.' }

Write-Host ''
Write-Host 'GitHub Pro bootstrap complete.' -ForegroundColor Green
Write-Host 'Pages: https://charlesganu2004.github.io/Master-Repo-Use/'
Write-Host "Audit trail: https://github.com/$Repository/issues"
Write-Host "Main protection: https://github.com/$Repository/settings/branches"
Write-Host ''
Write-Host 'Deep catalog maintenance still requires your exact owner comment: APPROVE CATALOG MAINTENANCE' -ForegroundColor Yellow

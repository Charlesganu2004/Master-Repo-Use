#!/usr/bin/env bash
set -euo pipefail

REPO="Charlesganu2004/Master-Repo-Use"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_VERSION="2026-03-10"

command -v gh >/dev/null 2>&1 || { echo "GitHub CLI (gh) is required." >&2; exit 1; }
gh auth status >/dev/null

api_json() {
  local method="$1" endpoint="$2" json="$3"
  printf '%s' "$json" | gh api \
    --method "$method" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: $API_VERSION" \
    "$endpoint" --input - >/dev/null
}

echo "[1/4] Enabling GitHub Pages with Actions publishing..."
if gh api -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: $API_VERSION" "repos/$REPO/pages" >/dev/null 2>&1; then
  api_json PUT "repos/$REPO/pages" '{"build_type":"workflow"}'
else
  api_json POST "repos/$REPO/pages" '{"build_type":"workflow"}'
fi

echo "[2/4] Allowing owner-approved workflows to create pull requests..."
api_json PUT "repos/$REPO/actions/permissions/workflow" '{"default_workflow_permissions":"read","can_approve_pull_request_reviews":true}'

echo "[3/4] Protecting main with PR + Code Owner approval..."
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: $API_VERSION" \
  "repos/$REPO/branches/main/protection" \
  --input "$ROOT/scripts/branch-protection.json" >/dev/null

echo "[4/4] Starting first Pages deployment and catalog audit..."
gh workflow run pages.yml -R "$REPO"
gh workflow run catalog-guardian.yml -R "$REPO"

echo
echo "GitHub Pro bootstrap complete."
echo "Pages: https://charlesganu2004.github.io/Master-Repo-Use/"
echo "Audit trail: https://github.com/$REPO/issues"
echo "Main protection: https://github.com/$REPO/settings/branches"
echo
echo "The audit may create/refresh [Catalog Audit]. Deep maintenance still requires your exact owner comment: APPROVE CATALOG MAINTENANCE"

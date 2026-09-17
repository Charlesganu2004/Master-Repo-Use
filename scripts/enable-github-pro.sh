#!/usr/bin/env bash
# One-time GitHub Pro bootstrap for Master-Repo-Use.
#
# Enables Pages (Actions build type), sets least-privilege workflow permissions,
# applies the protected-main + SHA-bound owner-approval policy, then verifies.
# Pages is dispatched at most once, and only after the API confirms Pages is
# enabled — repeatedly re-dispatching a deployment that cannot succeed just burns
# Actions minutes.
#
# Usage:
#   scripts/enable-github-pro.sh              # bootstrap + verify
#   scripts/enable-github-pro.sh --verify     # verify only, change nothing
#   scripts/enable-github-pro.sh --run-audit  # also kick off one catalog audit
set -euo pipefail

REPO="${REPO:-Charlesganu2004/Master-Repo-Use}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_VERSION='2022-11-28'
VERIFY_ONLY=0
RUN_AUDIT=0

for arg in "$@"; do
  case "$arg" in
    --verify|--verify-only) VERIFY_ONLY=1 ;;
    --run-audit) RUN_AUDIT=1 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

command -v gh >/dev/null 2>&1 || { echo "GitHub CLI (gh) is required: https://cli.github.com" >&2; exit 1; }
gh auth status >/dev/null

gh_api() {
  gh api -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: $API_VERSION" "$@"
}

api_json() {
  local method="$1" endpoint="$2" json="$3"
  printf '%s' "$json" | gh_api --method "$method" "$endpoint" --input - >/dev/null
}

pages_enabled() {
  gh_api "repos/$REPO/pages" >/dev/null 2>&1
}

if [[ "$VERIFY_ONLY" -eq 0 ]]; then
  echo "[1/3] Enabling GitHub Pages with Actions publishing..."
  if pages_enabled; then
    echo "      Pages already enabled; ensuring build_type=workflow."
    api_json PUT "repos/$REPO/pages" '{"build_type":"workflow"}'
  else
    api_json POST "repos/$REPO/pages" '{"build_type":"workflow"}'
  fi

  echo "[2/3] Setting least-privilege workflow permissions..."
  # Read-only GITHUB_TOKEN by default; each workflow widens what it needs.
  # Actions may not create or approve pull requests: one setting controls both,
  # and approving is a way around the owner gate (#16 turned it off). The approved
  # maintenance job pushes its branch and posts a link for the owner to open it.
  api_json PUT "repos/$REPO/actions/permissions/workflow" \
    '{"default_workflow_permissions":"read","can_approve_pull_request_reviews":false}'

  echo "[3/3] Protecting main with PR + SHA-bound owner approval..."
  gh_api --method PUT "repos/$REPO/branches/main/protection" \
    --input "$ROOT/scripts/branch-protection.json" >/dev/null
fi

echo
echo "=== Verification ==="
has_pages="$(gh_api "repos/$REPO" --jq '.has_pages')"
echo "has_pages:            $has_pages"
if pages_enabled; then
  echo "pages build_type:     $(gh_api "repos/$REPO/pages" --jq '.build_type')"
  echo "pages url:            $(gh_api "repos/$REPO/pages" --jq '.html_url')"
fi
echo "main protected:       $(gh_api "repos/$REPO/branches/main" --jq '.protected')"
echo "required status:      $(gh_api "repos/$REPO/branches/main/protection" --jq '.required_status_checks.contexts | join(",")')"
echo "required PR reviews:  $(gh_api "repos/$REPO/branches/main/protection" --jq '.required_pull_request_reviews.required_approving_review_count // "none"')"
echo "code owner reviews:   $(gh_api "repos/$REPO/branches/main/protection" --jq '.required_pull_request_reviews.require_code_owner_reviews // false')"
echo "conversation resolve: $(gh_api "repos/$REPO/branches/main/protection" --jq '.required_conversation_resolution.enabled')"
echo "force pushes allowed: $(gh_api "repos/$REPO/branches/main/protection" --jq '.allow_force_pushes.enabled')"
echo "deletions allowed:    $(gh_api "repos/$REPO/branches/main/protection" --jq '.allow_deletions.enabled')"

if [[ "$VERIFY_ONLY" -eq 1 ]]; then
  exit 0
fi

echo
if pages_enabled; then
  echo "Dispatching the Pages deployment once..."
  gh workflow run pages.yml -R "$REPO"
else
  echo "Pages is still not enabled, so no deployment was dispatched."
  echo "Enable it at https://github.com/$REPO/settings/pages (Source: GitHub Actions), then re-run this script."
fi

if [[ "$RUN_AUDIT" -eq 1 ]]; then
  echo "Dispatching one catalog audit..."
  gh workflow run catalog-guardian.yml -R "$REPO"
else
  echo "Catalog audit not dispatched (it runs weekly). Pass --run-audit to seed one now."
fi

cat <<EOF

GitHub Pro bootstrap complete.
  Pages:           https://charlesganu2004.github.io/Master-Repo-Use/
  Audit trail:     https://github.com/$REPO/issues
  Main protection: https://github.com/$REPO/settings/branches

Deep catalog maintenance still requires your exact owner comment on the audit
issue: APPROVE CATALOG MAINTENANCE

Protected-main PR approval is separate:
  - agent/bot/other-authored PR: Charles approves the current head with a review;
  - Charles-authored PR: comment APPROVE OWNER PR <CURRENT_HEAD_SHA> on that PR.
EOF

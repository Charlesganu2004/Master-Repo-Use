# Repo Health & Status Tracking

GitHub: https://github.com/Charlesganu2004/Master-Repo-Use

This file tracks the health of every repo in the catalog. Run the automated check with Iris (see [agents/repo-issue-iris.md](../agents/repo-issue-iris.md)) or run the manual commands below.

Last automated check: _not yet run — run Iris to populate_

---

## Status Definitions

| Status | Meaning | What to do |
|---|---|---|
| `active` | Committed to in the last 90 days | Safe to use |
| `slow` | Last commit 90–365 days ago | Use with caution, monitor for updates |
| `stale` | No commits in 1+ years | Research alternatives before adopting |
| `deprecated` | Maintainer explicitly says deprecated | Use replacement listed in this doc |
| `archived` | GitHub archived flag is set | Use replacement listed in this doc |
| `unmaintained` | No issue responses, no commits in 18+ months | Do not use for new projects |

---

## Manual Health Check

PowerShell — check one repo:

```powershell
$Repo = Read-Host "Enter owner/repo (e.g. HKUDS/LightRAG)"
$Token = Read-Host "GitHub token (or leave blank for public repos)"
$Headers = if ($Token) { @{Authorization = "Bearer $Token"} } else { @{} }
$Info = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo" -Headers $Headers
[PSCustomObject]@{
    Repo = $Repo
    Archived = $Info.archived
    LastPush = $Info.pushed_at
    OpenIssues = $Info.open_issues_count
    Stars = $Info.stargazers_count
} | Format-Table
```

WSL/Bash — check one repo:

```bash
repo="HKUDS/LightRAG"  # change this
curl -s "https://api.github.com/repos/$repo" | jq '{archived: .archived, last_push: .pushed_at, open_issues: .open_issues_count, stars: .stargazers_count}'
```

GitHub CLI — bulk check from repo list:

```bash
read -rp "Path to Master-Repo-Use: " master_repo
grep -vE '^(#|$)' "$master_repo/repo-lists/all-curated.txt" | while read -r repo; do
  result=$(gh api "repos/$repo" --jq '{archived: .archived, pushed: .pushed_at, issues: .open_issues_count}' 2>/dev/null)
  echo "$repo: $result"
done
```

---

## Automated Check with Iris

Start Iris in Propose mode and ask:

```
Iris, run a health check on all repos in repo-lists/all-curated.txt. Write the results to issues/ for my review.
```

Iris will output a table and wait for your approval before taking any action.

---

## Status Table

Run the health check to populate this table. Iris writes directly to this file in Act mode.

| Repo | Status | Last Push | Notes | Replacement |
|---|---|---|---|---|
| bradygaster/squad | _check needed_ | | | |
| HKUDS/LightRAG | _check needed_ | | | |
| microsoft/agents | _check needed_ | | | |
| modelcontextprotocol/servers | _check needed_ | | | |
| alpacahq/alpaca-py | _check needed_ | | | |
| OpenBB-finance/OpenBB | _check needed_ | | | |
| Qiskit/qiskit | _check needed_ | | | |
| infracost/infracost | _check needed_ | | | |
| ooples/token-optimizer-mcp | _check needed_ | | | |
| yvgude/lean-ctx | _check needed_ | | | |

_Run `Iris: health check` to populate all rows._

---

## Replacement Candidates

Repos that are known to be stale and their recommended replacements:

| Archived/Stale Repo | Recommended Replacement | Notes |
|---|---|---|
| (populated by Iris on first run) | | |

---

## How Iris Updates This File

In Act mode, Iris:
1. Runs the bulk GitHub API check.
2. Writes status and last-push date for every row.
3. Flags any repo with archived=true as `archived`.
4. Flags any repo with no commits in 365+ days as `stale`.
5. Searches the replacement candidates table and fills in replacements where known.
6. Writes a log entry to `issues/iris-YYYY-MM-DD.md` with a summary of what changed.

---

## Security Advisories

GitHub CLI — check security advisories for a repo:

```bash
gh api repos/HKUDS/LightRAG/security-advisories --jq '.[].ghsa_id' 2>/dev/null || echo "No advisories or private repo"
```

Repos with open security advisories are flagged Critical by Sentinel. See [agents/security-sentinel.md](../agents/security-sentinel.md).

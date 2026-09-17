#!/usr/bin/env python3
"""Generate a no-background-cost AI maintenance review request.

This script deliberately does NOT schedule model calls or merge changes. It is meant
to be invoked by Claude Code, Codex, GitHub Copilot CLI, or a human while they are
already using the Master Repo.

Behavior:
- checks GitHub Issues for an open [AI Maintenance] request;
- if one exists, prints it and exits;
- otherwise, creates a new request only when the last request is >= interval days old;
- if `gh` is unavailable/not authenticated, writes a local Markdown request instead;
- deep review/update work only starts after owner approval text is present.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = "Charlesganu2004/Master-Repo-Use"
LOCAL_REQUEST = ROOT / "docs" / "AI-MAINTENANCE-REQUEST.md"
TITLE_PREFIX = "[AI Maintenance]"
APPROVAL_PHRASE = "APPROVE AI MAINTENANCE"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def gh_ready() -> bool:
    if shutil.which("gh") is None:
        return False
    return run(["gh", "auth", "status"]).returncode == 0


def issues() -> list[dict]:
    proc = run([
        "gh", "issue", "list", "--repo", REPO, "--state", "all", "--limit", "100",
        "--search", f'"{TITLE_PREFIX}" in:title',
        "--json", "number,title,state,createdAt,closedAt,url",
    ])
    if proc.returncode != 0:
        return []
    try:
        return json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return []


def parse_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def request_body(today: dt.date) -> str:
    return f"""# AI Maintenance Review Request — {today.isoformat()}

Repository: `{REPO}`

## Owner gate

**Do not modify, merge, delete, fork, or adopt repositories until Charles explicitly approves this request.**

Owner approval phrase:

```text
{APPROVAL_PHRASE}
```

After approval, the AI may prepare changes on a branch and open a pull request. It must not merge `main` without Charles's approval.

## Review prompt for GPT / Claude / GitHub Copilot / Codex

Review the current Master Repo as a maintenance operation. Use the repository files as the source of truth and verify unstable upstream information before changing the catalog.

1. Run/read the Catalog Guardian and current catalog status.
2. Review every `STALE`, `REVIEW`, `REMOVE`, archived, disabled, deleted, or security-flagged repository.
3. For each flagged repo, inspect current commits, releases/tags, README notices, archive reason, successor/fork/replacement projects, license, security posture, dependency health, and whether the repo is runtime tooling versus a static research/reference artifact.
4. Deep-scan new and removal/adoption candidates for invisible/bidirectional text, prompt/instruction injection, SQL/command injection patterns, secrets, embedded executables, malware indicators, vulnerable dependencies, suspicious install hooks, and unsafe MCP/tool permissions. Use the Master Repo security stack when available: Guardian, Semgrep/OpenGrep, Gitleaks/TruffleHog, Trivy, OSV Scanner, Snyk, ClamAV, OSSF Scorecard, Syft/Cosign, Cisco AI Defense MCP Scanner, and Garak as appropriate.
5. Apply lifecycle policy: 120d stale warning; 270d replacement/adoption review; 365d active-runtime removal threshold. Treat archived repos as a review signal, not automatic death; recent releases, explicit sunset notices, stable/reference status, and maintained successors matter.
6. Prefer maintained upstream replacements over Charles-managed forks.
7. If a removed repo contains unique useful functionality and its license allows maintenance, create/update a `managed-repos/candidates/` plan. Do not copy third-party source or create a fork until Charles approves the scope.
8. Update `repo-lists/`, lifecycle overrides, health/security docs, and the interactive page/status only when supported by evidence.
9. Treat a recent release on an archived repository as a possible sunset release, not proof of maintenance: check the archive flag and the release notes before calling it healthy. Flowise shipped its final release, 3.1.4, on 2026-07-29 and reached end of life on 2026-08-31.
10. Create a PR with a concise per-repo decision table: KEEP, REFERENCE, REPLACE, REMOVE, or MANAGED-ADOPTION REVIEW. Request review from `@Charlesganu2004` and do not merge it.

## Current safeguards

- `main` is intended to be owner-controlled with CODEOWNERS + owner approval check + GitHub branch/ruleset protection.
- Scheduled AI maintenance is disabled by design to avoid recurring model/API spend.
- Catalog Guardian runs a deterministic weekly metadata audit and a read-only deep-scan rotation, with no model calls; removals still need the owner's approval comment on the `[Catalog Audit]` issue and a merged pull request.
- Token/work-spend routing is separate and opt-in in `docs/TOKEN-BUDGET.md`.

## Suggested approval flow

1. AI/user opens this issue/request and summarizes what would be checked.
2. Charles comments or states: `{APPROVAL_PHRASE}`.
3. AI performs the review in that active session.
4. AI creates/updates a branch and PR.
5. Charles reviews the PR and approves/merges manually.
"""


def write_local(body: str) -> pathlib.Path:
    LOCAL_REQUEST.write_text(body, encoding="utf-8")
    return LOCAL_REQUEST


def newest_request(items: list[dict]) -> dict | None:
    matching = [x for x in items if str(x.get("title", "")).startswith(TITLE_PREFIX)]
    if not matching:
        return None
    return max(matching, key=lambda x: x.get("createdAt") or "")


def open_request(items: list[dict]) -> dict | None:
    for item in items:
        if str(item.get("title", "")).startswith(TITLE_PREFIX) and str(item.get("state", "")).upper() == "OPEN":
            return item
    return None


def due(items: list[dict], interval_days: int) -> tuple[bool, str]:
    opened = open_request(items)
    if opened:
        return False, f"open request already exists: {opened.get('url', opened.get('number'))}"
    latest = newest_request(items)
    if not latest:
        return True, "no previous maintenance request found"
    created = parse_time(latest.get("createdAt"))
    if not created:
        return True, "could not parse latest request date"
    age = (dt.datetime.now(dt.timezone.utc) - created).days
    return age >= interval_days, f"latest request is {age}d old; interval is {interval_days}d"


def create_issue(body: str, today: dt.date) -> str | None:
    tmp = ROOT / ".git" / "ai-maintenance-request.md"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(body, encoding="utf-8")
    proc = run([
        "gh", "issue", "create", "--repo", REPO,
        "--title", f"{TITLE_PREFIX} Catalog review {today.isoformat()}",
        "--body-file", str(tmp),
        "--assignee", "Charlesganu2004",
    ])
    try:
        tmp.unlink(missing_ok=True)
    except OSError:
        pass
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval-days", type=int, default=30)
    parser.add_argument("--check", action="store_true", help="Only report whether a request is due.")
    parser.add_argument("--generate", action="store_true", help="Write a local Markdown request.")
    parser.add_argument("--open-issue", action="store_true", help="Create a GitHub issue when due.")
    parser.add_argument("--auto", action="store_true", help="Recommended client mode: check; if due create issue, else local request fallback.")
    args = parser.parse_args()

    today = dt.datetime.now(dt.timezone.utc).date()
    body = request_body(today)

    if not gh_ready():
        if args.check and not (args.generate or args.open_issue or args.auto):
            print("MAINTENANCE_STATUS=UNKNOWN gh CLI unavailable or not authenticated")
            return 0
        path = write_local(body)
        print(f"MAINTENANCE_REQUEST_LOCAL={path}")
        print("GitHub issue was not created because gh is unavailable/not authenticated.")
        return 0

    items = issues()
    is_due, reason = due(items, args.interval_days)
    opened = open_request(items)

    if args.check and not (args.generate or args.open_issue or args.auto):
        print(f"MAINTENANCE_DUE={'yes' if is_due else 'no'}")
        print(f"REASON={reason}")
        if opened:
            print(f"OPEN_REQUEST={opened.get('url', opened.get('number'))}")
        return 0

    if opened:
        print(f"MAINTENANCE_DUE=no\nREASON={reason}\nOPEN_REQUEST={opened.get('url', opened.get('number'))}")
        return 0

    if not is_due:
        print(f"MAINTENANCE_DUE=no\nREASON={reason}")
        return 0

    if args.generate and not (args.open_issue or args.auto):
        print(f"MAINTENANCE_REQUEST_LOCAL={write_local(body)}")
        return 0

    if args.open_issue or args.auto:
        url = create_issue(body, today)
        if url:
            print(f"MAINTENANCE_DUE=yes\nREQUEST_CREATED={url}")
            return 0
        path = write_local(body)
        print(f"MAINTENANCE_REQUEST_LOCAL={path}")
        print("Issue creation failed; local request generated instead.")
        return 0

    print(f"MAINTENANCE_DUE=yes\nREASON={reason}")
    print("Use --auto to create the review request without starting maintenance work.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

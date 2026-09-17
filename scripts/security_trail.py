#!/usr/bin/env python3
"""Append-only record of what the automation actually did.

Charles asked for bots that may act, provided they say what they did afterwards.
That only means anything if the saying is durable. A comment on an issue can be
edited or lost when the issue is closed; this file is in git history, so an entry
cannot be quietly revised without showing up in a diff.

Append-only by construction: this script writes to the end and never rewrites an
existing row. A run that wants to correct an earlier entry adds a new one saying
so. The no-compress guard covers this file, so a summariser cannot flatten it.

    python scripts/security_trail.py \
        --action deep-scan --scope "19 repositories" \
        --outcome "CRITICAL 0, HIGH 12" --approval "APPROVE CATALOG MAINTENANCE by owner"
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
TRAIL = ROOT / "docs" / "SECURITY-TRAIL.md"

HEADER = """# Security trail

<!-- NO-COMPRESS:BEGIN -->
An audit record that can be summarised is not an audit record. This file carries
the no-compress markers so the guard refuses any pass over it: the rows are the
evidence, and a shortened row is a changed fact.
<!-- NO-COMPRESS:END -->

Append-only. Every automated scan and every action taken on its findings lands
here, whether or not it changed anything. Written by `scripts/security_trail.py`
from the workflow that did the work.

Read this rather than the issue comments when you want to know what actually
happened: issues get closed and comments get edited, and this is in git history.

Three rules the automation follows, and this file is how you check it kept them:

1. A bot may scan, report, comment and open a pull request. It may not merge, and
   it may not delete a catalog entry.
2. Every scan writes a row here, including the ones that found nothing. A quiet
   period should be visible as quiet rows, not as an absence of rows.
3. Removals require an owner approval phrase, and the row records which one.

| UTC | Run | Action | Scope | Outcome | Authorised by | Budget |
|---|---|---|---|---|---|---|
"""


def run_link() -> str:
    """A link back to the job, so a row can be audited against real logs."""
    repo = os.getenv("GITHUB_REPOSITORY")
    run_id = os.getenv("GITHUB_RUN_ID")
    if repo and run_id:
        return f"[{run_id}](https://github.com/{repo}/actions/runs/{run_id})"
    return "local"


def cell(text: str, limit: int = 160) -> str:
    """Table-safe: pipes would split the row, newlines would break it."""
    flat = " ".join(str(text or "").split())
    flat = flat.replace("|", "/")
    return flat[:limit] if len(flat) <= limit else flat[:limit - 3] + "..."


def append(action: str, scope: str, outcome: str, approval: str, budget: str,
           path: pathlib.Path = TRAIL) -> str:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(HEADER, encoding="utf-8", newline="\n")

    existing = path.read_text(encoding="utf-8")
    if not existing.endswith("\n"):
        existing += "\n"

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
    row = (f"| {stamp} | {run_link()} | {cell(action, 40)} | {cell(scope, 70)} "
           f"| {cell(outcome, 90)} | {cell(approval, 60)} | {cell(budget, 30)} |\n")

    # Append only. Never rewrite what is already there. LF endings, so a Windows
    # session does not rewrite every existing row's line ending as it appends.
    path.write_text(existing + row, encoding="utf-8", newline="\n")
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description="Append one row to the security trail.")
    parser.add_argument("--action", required=True,
                        help="what was done, e.g. deep-scan, metadata-audit, removal-proposed")
    parser.add_argument("--scope", default="", help="what it covered")
    parser.add_argument("--outcome", default="", help="what it found or changed")
    parser.add_argument("--approval", default="none required",
                        help="the phrase or rule that authorised it")
    parser.add_argument("--budget", default="", help="minutes used at the time")
    parser.add_argument("--file", type=pathlib.Path, default=TRAIL,
                        help="trail file to append to; scripts/record_trail_row.sh passes the "
                             "automation/security-trail branch's copy")
    args = parser.parse_args()

    row = append(args.action, args.scope, args.outcome, args.approval, args.budget, args.file)
    print(f"appended to {args.file}:")
    print(row.rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Measure Actions minutes used this cycle and refuse expensive work near the cap.

Charles is on GitHub Pro: 3,000 included minutes a month on private repositories.
Public repositories are free, so this only matters while the repo is private.

The billing endpoint needs a token scope the repository's GITHUB_TOKEN does not
have, so usage is computed from job timestamps instead. That is the same number
the bill is derived from, one API call per run. The workflow token can read runs
only when the job grants `actions: read`; every job that calls this must.

When the runs cannot be read, the result is reported as unknown, never as 0. It
used to stop on the HTTP error and print "used 0 of 3000", and the gate passed on
a number nobody had measured.

Used as a gate: deep scans and any bot action check headroom first and skip
rather than overrun. A skipped scan is recoverable; a blown budget is a bill.

    python scripts/actions_budget.py --report
    python scripts/actions_budget.py --gate --reserve 500   # exit 1 if under 500 left
    python scripts/actions_budget.py --cell                 # "150 of 3000 minutes", for the trail
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import sys
import urllib.error
import urllib.request

INCLUDED_MINUTES = 3000      # GitHub Pro, private repositories
API = "https://api.github.com"

# Runner cost multipliers. Linux is the baseline; the others bill faster, so a
# workflow that quietly moves to macOS costs ten times what it did.
MULTIPLIERS = {"UBUNTU": 1, "LINUX": 1, "WINDOWS": 2, "MACOS": 10}


def request(url: str, token: str | None) -> dict:
    req = urllib.request.Request(
        url, headers={"Accept": "application/vnd.github+json",
                      "User-Agent": "master-repo-budget"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def cycle_start(today: dt.date | None = None) -> dt.date:
    """GitHub bills on calendar months for included minutes."""
    today = today or dt.datetime.now(dt.timezone.utc).date()
    return today.replace(day=1)


def minutes_used(repo: str, token: str | None, since: dt.date) -> tuple[int | None, dict, bool]:
    """Billable minutes this cycle, a per-workflow breakdown, and whether the count is complete.

    GitHub rounds each job up to the whole minute, so this does the same rather
    than summing raw seconds, which would read low. Minutes are None when not even
    the first page of runs could be read; the count is incomplete when a later
    page or a run's jobs could not be read, so the total is a lower bound.
    """
    per_workflow: dict[str, int] = {}
    total = 0
    complete = True
    page = 1
    while page <= 10:            # bounded: ten pages is 1000 runs, far past a month here
        url = f"{API}/repos/{repo}/actions/runs?per_page=100&page={page}&created=>{since:%Y-%m-%d}"
        try:
            payload = request(url, token)
        except (urllib.error.HTTPError, urllib.error.URLError):
            if page == 1:
                return None, {}, False
            complete = False
            break
        runs = payload.get("workflow_runs") or []
        if not runs:
            break
        for run in runs:
            try:
                jobs = request(f"{API}/repos/{repo}/actions/runs/{run['id']}/jobs", token)
            except (urllib.error.HTTPError, urllib.error.URLError):
                complete = False
                continue
            for job in jobs.get("jobs") or []:
                started, completed = job.get("started_at"), job.get("completed_at")
                if not started or not completed:
                    continue
                begin = dt.datetime.fromisoformat(started.replace("Z", "+00:00"))
                end = dt.datetime.fromisoformat(completed.replace("Z", "+00:00"))
                raw = max((end - begin).total_seconds(), 0) / 60
                labels = " ".join(job.get("labels") or []).upper()
                factor = next((m for key, m in MULTIPLIERS.items() if key in labels), 1)
                billed = math.ceil(raw) * factor
                total += billed
                name = run.get("name") or "unnamed"
                per_workflow[name] = per_workflow.get(name, 0) + billed
        page += 1
    return total, per_workflow, complete


def budget_cell(used: int | None, included: int, complete: bool) -> str:
    """The Budget column of the security trail: a measurement, a lower bound, or unknown."""
    if used is None:
        return "unknown (Actions runs could not be read)"
    return f"{'' if complete else 'at least '}{used} of {included} minutes"


def main() -> int:
    parser = argparse.ArgumentParser(description="Actions budget report and gate.")
    parser.add_argument("--repo", default=os.getenv("GITHUB_REPOSITORY", ""))
    parser.add_argument("--included", type=int, default=INCLUDED_MINUTES)
    parser.add_argument("--reserve", type=int, default=500,
                        help="minutes to keep free; the gate fails below this")
    parser.add_argument("--gate", action="store_true",
                        help="exit 1 when headroom is under the reserve")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--cell", action="store_true",
                        help="print only the trail's Budget cell and exit")
    args = parser.parse_args()

    if not args.repo:
        print("no repository given; pass --repo owner/name", file=sys.stderr)
        return 2

    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    since = cycle_start()
    used, breakdown, complete = minutes_used(args.repo, token, since)
    if args.cell:
        print(budget_cell(used, args.included, complete))
        return 0

    print(f"Billing cycle from {since:%Y-%m-%d}")
    if used is None:
        # Fail open, deliberately and loudly. The rotation is capped at 45 minutes a
        # week, about 200 of the 3,000 a month, so it cannot overrun the allowance on
        # its own, and failing closed would stop every security scan whenever this
        # API is unreadable. What must never happen is printing 0 as if measured.
        print("  used      unknown: Actions runs could not be read (does the job grant actions: read?)")
        if args.gate:
            print("GATE: the budget could not be read, so the gate proceeds without a measurement.",
                  file=sys.stderr)
        return 0
    headroom = args.included - used
    percent = 100 * used / max(args.included, 1)

    print(f"  used      {budget_cell(used, args.included, complete)} ({percent:.1f}%)")
    print(f"  headroom  {headroom} minutes")
    print(f"  reserve   {args.reserve} minutes")
    if args.report and breakdown:
        print("  by workflow:")
        for name, minutes in sorted(breakdown.items(), key=lambda kv: -kv[1]):
            print(f"    {minutes:>6}  {name}")

    if args.gate and headroom < args.reserve:
        print(f"\nGATE: headroom {headroom} is below the {args.reserve} minute reserve.",
              file=sys.stderr)
        print("Skipping the expensive step. A skipped scan is recoverable; an "
              "overrun is a bill.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Report how stale the committed catalog metadata is, for the Pages deploy.

Catalog Guardian owns docs/catalog-status.json and refreshes it on its own
schedule. The Pages deploy used to re-run Guardian's full catalog API sweep on
every push, paying for the same data twice and spending rate limit for a file
that was already in the tree. Deploy now renders what is committed, and this
gate turns "the committed data is getting old" into a visible warning instead
of a silent stale site.

Exit status is 0 for fresh or merely stale metadata and 1 only when the file is
missing or unreadable, so an aging catalog warns without blocking a deploy.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE = ROOT / "docs" / "catalog-status.json"

# Guardian writes "YYYY-MM-DD HH:MM UTC"; tolerate a trailing suffix or a 'T'.
STAMP_FORMATS = ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M")


def age_days(updated: str) -> int | None:
    stamp = (updated or "").strip()[:16]
    for fmt in STAMP_FORMATS:
        try:
            parsed = dt.datetime.strptime(stamp, fmt).replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
        return (dt.datetime.now(dt.timezone.utc) - parsed).days
    return None


def emit(line: str) -> None:
    print(line)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warn-after-days", type=int, default=21,
                        help="age at which the deploy annotates a warning (default: 21)")
    args = parser.parse_args()

    if not STATE.exists():
        emit("::error::docs/catalog-status.json is missing. Run the Catalog Guardian workflow before deploying.")
        return 1
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except ValueError as exc:
        emit(f"::error::docs/catalog-status.json is not valid JSON ({exc}).")
        return 1

    days = age_days(str(state.get("updated", "")))
    if days is None:
        emit("::warning::docs/catalog-status.json has no readable 'updated' stamp; cannot judge freshness.")
        return 0

    counts = state.get("counts") or {}
    summary = " · ".join(f"{k} {counts.get(k, 0)}" for k in ("HEALTHY", "STALE", "REVIEW", "REMOVE"))
    emit(f"Committed catalog metadata is {days}d old ({summary}).")
    if days > args.warn_after_days:
        emit(f"::warning::docs/catalog-status.json is {days}d old. "
             f"Run the Catalog Guardian workflow to refresh it.")

    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as handle:
            handle.write(f"### Catalog metadata\n\n`{days}d` old — {summary}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

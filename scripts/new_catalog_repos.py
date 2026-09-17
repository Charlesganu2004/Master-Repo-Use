#!/usr/bin/env python3
"""Which repositories a push genuinely added to the catalog, for intake deep scans.

    python scripts/new_catalog_repos.py --base <sha> [--head HEAD] [--limit 15]

A repository is new when no file under repo-lists/ named it at the base commit.
The audit job used to treat every added line in any list as new, so copying a
repository that was already listed into another list, as registering a lane's
repositories in all-curated.txt does, looked like fresh intake and forced a deep
scan of each one inside a 20-minute job.

At most --limit repositories are printed, one per line. The rest are reported on
stderr and left to the weekly rotation, because a skipped intake scan is recoverable
and a timed-out audit job produces no audit at all.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys

SLUG = re.compile(r"[\w.-]+/[\w.-]+")


def slugs(text: str) -> dict[str, str]:
    """Catalog slugs in one list file, keyed case-insensitively, comments ignored."""
    found: dict[str, str] = {}
    for line in text.splitlines():
        candidate = line.split("#", 1)[0].strip()
        if SLUG.fullmatch(candidate):
            found.setdefault(candidate.lower(), candidate)
    return found


def listed_at(ref: str) -> dict[str, str]:
    """Every slug named by any repo-lists/*.txt file at a commit."""
    names = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", ref, "--", "repo-lists/"],
        capture_output=True, text=True, check=True).stdout.split()
    found: dict[str, str] = {}
    for name in names:
        if not name.endswith(".txt"):
            continue
        text = subprocess.run(["git", "show", f"{ref}:{name}"], capture_output=True,
                              text=True, encoding="utf-8", check=True).stdout
        for low, slug in slugs(text).items():
            found.setdefault(low, slug)
    return found


def new_repos(base: str, head: str) -> list[str]:
    before = listed_at(base)
    after = listed_at(head)
    return sorted((slug for low, slug in after.items() if low not in before), key=str.lower)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--limit", type=int, default=15)
    args = parser.parse_args()

    added = new_repos(args.base, args.head)
    for slug in added[:args.limit]:
        print(slug)
    if len(added) > args.limit:
        print(f"{len(added) - args.limit} further new repositories left to the weekly rotation: "
              + ", ".join(added[args.limit:]), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

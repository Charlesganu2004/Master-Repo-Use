#!/usr/bin/env python3
"""Notice when the original behind one of our skills changes.

Several master-* skills are our own statement of a technique somebody else wrote
first: caveman from JuliusBrussee/caveman, full output and design taste from
Leonxlnx/taste-skill, anti-slop from hardikpandya/stop-slop, refactor from
github/awesome-copilot, refactor-ui from jaywilburn/refactoring-ui-skill. When
those move, ours should be looked at again. Before this, nothing noticed.

WHAT "AUTOMATICALLY UPDATED" MEANS HERE, and what it deliberately does not.
Detection is automatic: a weekly job runs --check, and when an upstream file's
content hash differs from the one we reviewed, it opens or refreshes a single
"[Skill Upstream]" issue listing what moved, with links to the diff.

Merging is not automatic, on purpose. These skills run on every prompt of every
client. Pulling a third party's new text straight into them would make any
upstream maintainer, or anyone who compromised their account, able to change
what every model on every one of these machines is told to do, on a schedule.
A human reads the upstream diff, updates our skill, and re-pins it with --pin.
That is the same line the catalog already holds: catalogued is not vetted.

WHAT IS RECORDED. For each tracked skill: the upstream repository and file, the
licence as verified, how our skill relates to it, and the reviewed state: commit,
release tag, byte size and SHA-256 of the upstream file at that commit. The
hash is what --check compares, so a moved tag or a rewritten file is caught even
when the release number did not change.

The manifest is written by --pin, from what the API returns. It is never typed
by hand, because hand-typed numbers are how this repository has repeatedly
published figures that were wrong.

Usage:
    python scripts/skill_upstreams.py --check
    python scripts/skill_upstreams.py --check --report upstream-report.md
    python scripts/skill_upstreams.py --pin master-caveman
    python scripts/skill_upstreams.py --pin all
    python scripts/skill_upstreams.py --list

Uses GITHUB_TOKEN when present (in Actions), unauthenticated otherwise; the
tracked set needs about three requests per entry, well under the anonymous limit.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "repo-lists" / "skill-upstreams.json"
API = "https://api.github.com"

# What each skill tracks. The reviewed state is NOT here; --pin measures it and
# writes it into the manifest, so this table only says where to look.
#
# relation:
#   derived   our skill restates the upstream technique in our own words and
#             adds house rules; an upstream change may change what we should say
TRACKED = {
    "master-caveman": {
        "upstream": "JuliusBrussee/caveman",
        "path": "skills/caveman/SKILL.md",
        "licence": "MIT for skills/; the engine-linked directories (engine, proxy, "
                   "rewriter, browse, mcp and others) are BSL-1.1 and are not used",
        "relation": "derived",
    },
    "master-full-output": {
        "upstream": "Leonxlnx/taste-skill",
        "path": "skills/output-skill/SKILL.md",
        "licence": "MIT",
        "relation": "derived",
    },
    "master-design-taste": {
        "upstream": "Leonxlnx/taste-skill",
        "path": "skills/taste-skill/SKILL.md",
        "licence": "MIT",
        "relation": "derived",
    },
    "master-anti-slop": {
        "upstream": "hardikpandya/stop-slop",
        "path": "SKILL.md",
        "licence": "MIT",
        "relation": "derived",
    },
    "master-refactor": {
        "upstream": "github/awesome-copilot",
        "path": "skills/refactor/SKILL.md",
        "licence": "MIT",
        "relation": "derived",
    },
    "master-refactor-ui": {
        "upstream": "jaywilburn/refactoring-ui-skill",
        "path": "skills/refactoring-ui/SKILL.md",
        "licence": "MIT",
        "relation": "derived",
    },
}


class UpstreamError(RuntimeError):
    pass


def _request(url: str, raw: bool = False):
    headers = {"User-Agent": "master-repo-skill-upstreams",
               "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers),
                                    timeout=30) as response:
            body = response.read()
    except urllib.error.HTTPError as problem:
        raise UpstreamError(f"{url} -> HTTP {problem.code}") from None
    except urllib.error.URLError as problem:
        raise UpstreamError(f"{url} -> {problem.reason}") from None
    return body if raw else json.loads(body)


# Tests replace this with a fake so --check can be exercised offline.
FETCH = _request


def upstream_state(slug: str, path: str) -> dict:
    """The upstream file as it stands now: commit, release, size, hash."""
    repo = FETCH(f"{API}/repos/{slug}")
    branch = repo.get("default_branch", "main")
    commit = FETCH(f"{API}/repos/{slug}/commits/{branch}")["sha"]
    body = FETCH(f"https://raw.githubusercontent.com/{slug}/{commit}/{path}", raw=True)
    try:
        release = FETCH(f"{API}/repos/{slug}/releases/latest").get("tag_name")
    except UpstreamError:
        release = None                  # many skill repos never publish a release
    return {
        "commit": commit,
        "release": release,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "archived": bool(repo.get("archived")),
        "licenceDetected": (repo.get("license") or {}).get("spdx_id"),
    }


def load_manifest() -> dict:
    if not MANIFEST.is_file():
        return {"skills": {}}
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def save_manifest(data: dict) -> None:
    MANIFEST.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def pin(names: list[str], today: str | None = None) -> list[str]:
    """Record the current upstream state as reviewed. Run AFTER reviewing it."""
    data = load_manifest()
    data.setdefault("skills", {})
    lines = []
    for name in names:
        spec = TRACKED[name]
        state = upstream_state(spec["upstream"], spec["path"])
        data["skills"][name] = {
            **spec,
            "reviewed": {
                "commit": state["commit"],
                "release": state["release"],
                "bytes": state["bytes"],
                "sha256": state["sha256"],
                "on": today or datetime.date.today().isoformat(),
            },
        }
        lines.append(f"pinned {name}: {spec['upstream']}@{state['commit'][:12]} "
                     f"{state['bytes']:,} bytes")
    save_manifest(data)
    return lines


def check() -> list[dict]:
    """Compare every tracked skill's upstream file with what we reviewed."""
    data = load_manifest().get("skills", {})
    results = []
    for name, spec in TRACKED.items():
        entry = {"skill": name, "upstream": spec["upstream"], "path": spec["path"]}
        reviewed = (data.get(name) or {}).get("reviewed")
        if not reviewed:
            results.append({**entry, "status": "unpinned",
                            "detail": "never reviewed; run --pin after reading it"})
            continue
        try:
            now = upstream_state(spec["upstream"], spec["path"])
        except UpstreamError as problem:
            # A missing file is a real finding: upstream moved or deleted it.
            results.append({**entry, "status": "error", "detail": str(problem)})
            continue
        if now["archived"]:
            status, detail = "archived", "upstream repository is archived"
        elif now["sha256"] != reviewed["sha256"]:
            status = "changed"
            detail = (f"{reviewed['bytes']:,} -> {now['bytes']:,} bytes since "
                      f"{reviewed['commit'][:12]} (reviewed {reviewed['on']})")
        else:
            status, detail = "current", f"matches {reviewed['commit'][:12]}"
        results.append({**entry, "status": status, "detail": detail,
                        "reviewedCommit": reviewed["commit"], "nowCommit": now["commit"],
                        "release": now["release"]})
    return results


def report(results: list[dict]) -> str:
    """The issue body a human reviews. Links go straight to the upstream diff."""
    moved = [r for r in results if r["status"] != "current"]
    lines = [
        "Upstream originals behind our skills have moved. Nothing has been changed",
        "in this repository: read each diff, update our skill if it should follow,",
        "then run `python scripts/skill_upstreams.py --pin <skill>` and commit.",
        "",
        "| Skill | Upstream | Status | Detail |",
        "| --- | --- | --- | --- |",
    ]
    for r in moved:
        link = r["upstream"]
        if r.get("reviewedCommit") and r.get("nowCommit"):
            link = (f"[{r['upstream']}](https://github.com/{r['upstream']}/compare/"
                    f"{r['reviewedCommit'][:12]}...{r['nowCommit'][:12]})")
        lines.append(f"| {r['skill']} | {link} | {r['status']} | {r['detail']} |")
    current = [r["skill"] for r in results if r["status"] == "current"]
    if current:
        lines += ["", f"Unchanged: {', '.join(current)}."]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true",
                        help="compare upstreams with what was reviewed; exit 1 if any moved")
    parser.add_argument("--report", metavar="FILE", help="with --check, write an issue body")
    parser.add_argument("--pin", metavar="SKILL|all", help="record the current upstream as reviewed")
    parser.add_argument("--list", action="store_true", help="show what is tracked")
    args = parser.parse_args()

    if args.list:
        for name, spec in TRACKED.items():
            print(f"{name:<22}{spec['upstream']:<34}{spec['path']}")
        return 0

    if args.pin:
        names = list(TRACKED) if args.pin == "all" else [args.pin]
        unknown = [n for n in names if n not in TRACKED]
        if unknown:
            print(f"not tracked: {', '.join(unknown)}", file=sys.stderr)
            return 2
        try:
            for line in pin(names):
                print(line)
        except UpstreamError as problem:
            print(f"could not pin: {problem}", file=sys.stderr)
            return 1
        return 0

    if args.check:
        results = check()
        for r in results:
            print(f"{r['status']:<9}{r['skill']:<22}{r['detail']}")
        if args.report:
            pathlib.Path(args.report).write_text(report(results), encoding="utf-8")
        moved = [r for r in results if r["status"] != "current"]
        return 1 if moved else 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

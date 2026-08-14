#!/usr/bin/env python3
"""Catalog freshness checker.

Reads every repo-lists/*.txt, asks GitHub how each repo is doing, classifies it
against the status definitions in docs/REPO-HEALTH.md, and rewrites the status
table in that file.

Exit codes:
  0  everything active or slow
  1  at least one repo is stale / archived / deprecated / unmaintained
  2  could not complete the check (network, rate limit)

Usage:
  python scripts/check_freshness.py                 # check, rewrite REPO-HEALTH.md
  python scripts/check_freshness.py --check-only    # no writes, just report + exit code
  python scripts/check_freshness.py --json out.json # also emit machine-readable results

Auth:
  Set GITHUB_TOKEN to raise the rate limit from 60/hr to 5000/hr. Without it,
  a catalog of ~250 repos cannot be checked in one pass.
"""
import argparse
import concurrent.futures
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LISTS = os.path.join(ROOT, "repo-lists")
HEALTH = os.path.join(ROOT, "docs", "REPO-HEALTH.md")

API = "https://api.github.com/repos/%s"
TODAY = datetime.date.today()

# thresholds in days - keep in sync with the Status Definitions table
ACTIVE_MAX = 90
SLOW_MAX = 365
UNMAINTAINED_MIN = 550

BAD = {"stale", "archived", "deprecated", "unmaintained", "missing"}

START = "<!-- FRESHNESS:START -->"
END = "<!-- FRESHNESS:END -->"


def read_lists():
    """owner/name -> [list files it appears in]"""
    repos = {}
    if not os.path.isdir(LISTS):
        return repos
    for fn in sorted(os.listdir(LISTS)):
        if not fn.endswith(".txt"):
            continue
        with open(os.path.join(LISTS, fn), encoding="utf-8") as f:
            for line in f:
                line = line.strip().lstrip("\ufeff")
                if not line or line.startswith("#"):
                    continue
                repo = line.split("#")[0].split()[0].strip()
                if repo.count("/") != 1:
                    continue
                repos.setdefault(repo, []).append(fn)
    return repos


def fetch(repo, token, retries=3):
    req = urllib.request.Request(API % repo)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "master-repo-use-freshness")
    if token:
        req.add_header("Authorization", "Bearer %s" % token)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r), None
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, "not found"
            if e.code in (403, 429):
                remaining = e.headers.get("X-RateLimit-Remaining")
                if remaining == "0":
                    reset = int(e.headers.get("X-RateLimit-Reset", 0))
                    wait = max(0, reset - int(time.time())) + 2
                    return None, "rate limited (resets in %ds)" % wait
                time.sleep(2 * (attempt + 1))
                continue
            return None, "HTTP %d" % e.code
        except Exception as e:  # network hiccup
            if attempt == retries - 1:
                return None, str(e)[:60]
            time.sleep(2 * (attempt + 1))
    return None, "gave up after %d attempts" % retries


ATOM = "https://github.com/%s/commits/HEAD.atom"


def fetch_atom(repo):
    """Rate-limit-free fallback: last commit date from the repo's Atom feed.

    Gives pushed_at only - no archived flag, no stars. Used when the REST API
    budget is exhausted so a large catalog can still be checked in one pass.
    """
    req = urllib.request.Request(ATOM % repo)
    req.add_header("User-Agent", "master-repo-use-freshness")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            text = r.read(20000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return (None, "not found") if e.code == 404 else (None, "HTTP %d" % e.code)
    except Exception as e:
        return None, str(e)[:60]
    m = re.search(r"<updated>([0-9]{4}-[0-9]{2}-[0-9]{2})", text)
    if not m:
        return None, "no date in feed"
    return {"pushed_at": m.group(1), "_source": "atom"}, None


def classify(info):
    if info is None:
        return "missing", None
    if info.get("archived"):
        return "archived", None
    desc = (info.get("description") or "").lower()
    if "deprecated" in desc or "no longer maintained" in desc:
        return "deprecated", None
    pushed = (info.get("pushed_at") or "")[:10]
    if not pushed:
        return "stale", None
    age = (TODAY - datetime.date.fromisoformat(pushed)).days
    if age <= ACTIVE_MAX:
        return "active", age
    if age <= SLOW_MAX:
        return "slow", age
    if age >= UNMAINTAINED_MIN:
        return "unmaintained", age
    return "stale", age


def render(rows):
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    order = ["missing", "archived", "deprecated", "unmaintained", "stale", "slow", "active"]
    summary = " · ".join("%s %d" % (s, counts[s]) for s in order if s in counts)

    out = [START, ""]
    out.append("**Last automated check:** %s · **Repos:** %d · %s"
               % (TODAY.isoformat(), len(rows), summary))
    out.append("")
    out.append("Regenerate with `python scripts/check_freshness.py`. "
               "Runs weekly via `.github/workflows/repo-freshness.yml`.")
    out.append("")

    flagged = [r for r in rows if r["status"] in BAD]
    if flagged:
        out.append("### Needs attention (%d)" % len(flagged))
        out.append("")
        out.append("| Repo | Status | Last push | Age (days) | Listed in |")
        out.append("| --- | --- | --- | --- | --- |")
        for r in sorted(flagged, key=lambda x: (order.index(x["status"]), x["repo"])):
            out.append("| [%s](https://github.com/%s) | `%s` | %s | %s | %s |" % (
                r["repo"], r["repo"], r["status"], r["pushed"] or "—",
                r["age"] if r["age"] is not None else "—", ", ".join(r["lists"])))
        out.append("")
    else:
        out.append("### Needs attention")
        out.append("")
        out.append("None. Every catalogued repo has been committed to within the last year.")
        out.append("")

    out.append("### All repos")
    out.append("")
    out.append("| Repo | Status | Last push | Stars |")
    out.append("| --- | --- | --- | --- |")
    for r in sorted(rows, key=lambda x: (order.index(x["status"]), x["repo"].lower())):
        mark = " †" if r.get("source") == "atom" else ""
        out.append("| [%s](https://github.com/%s) | `%s` | %s%s | %s |" % (
            r["repo"], r["repo"], r["status"], r["pushed"] or "—", mark,
            r["stars"] if r["stars"] is not None else "—"))
    out.append("")
    out.append(END)
    return "\n".join(out)


def write_health(block):
    if not os.path.exists(HEALTH):
        return False
    body = open(HEALTH, encoding="utf-8").read()
    if START in body and END in body:
        body = re.sub(re.escape(START) + r".*?" + re.escape(END), block, body, flags=re.S)
    else:
        body = re.sub(r"Last automated check:.*?\n", "", body, count=1)
        body = body.rstrip() + "\n\n---\n\n" + block + "\n"
    open(HEALTH, "w", encoding="utf-8").write(body)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true", help="do not write REPO-HEALTH.md")
    ap.add_argument("--json", metavar="PATH", help="also write machine-readable results")
    ap.add_argument("--limit", type=int, help="check at most N repos (for testing)")
    ap.add_argument("--jobs", type=int, default=8,
                    help="concurrent API requests (default 8; 1 = serial)")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repos = read_lists()
    if not repos:
        print("No repos found in %s" % LISTS, file=sys.stderr)
        return 2

    names = sorted(repos)
    if args.limit:
        names = names[:args.limit]

    if not token and len(names) > 55:
        print("WARNING: %d repos but no GITHUB_TOKEN set. Unauthenticated limit is 60/hr;\n"
              "         this run will hit it. Set GITHUB_TOKEN for a complete check.\n"
              % len(names), file=sys.stderr)

    # Each repo costs one HTTP round-trip and nothing else. Checked serially, a
    # 234-repo catalog spends most of a minute asleep on sockets. urllib releases
    # the GIL while waiting, so threads convert that wait into overlap. Kept
    # deliberately modest: GitHub throttles aggressive concurrency, and the point
    # is to stop idling, not to flood the API.
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        pending = {pool.submit(fetch, r, token): r for r in names}
        done = 0
        for fut in concurrent.futures.as_completed(pending):
            results[pending[fut]] = fut.result()
            done += 1
            if done % 25 == 0:
                print("  checked %d/%d" % (done, len(names)), file=sys.stderr)

    # Rate limiting is discovered mid-flight rather than at a known index, so the
    # fallback is a second pass over exactly the repos that hit it.
    limited = [r for r, (_i, err) in results.items() if err and "rate limited" in err]
    if limited:
        print("REST budget exhausted on %d/%d - falling back to Atom feeds "
              "(commit dates only, no archived flag)" % (len(limited), len(names)),
              file=sys.stderr)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            for repo, res in zip(limited, pool.map(fetch_atom, limited)):
                results[repo] = res

    rows, errors = [], []
    for repo in names:                       # names order keeps runs reproducible
        info, err = results[repo]
        status, age = classify(info)
        if err and err != "not found":
            errors.append("%s: %s" % (repo, err))
        rows.append({
            "repo": repo,
            "status": status,
            "age": age,
            "pushed": (info or {}).get("pushed_at", "")[:10] or None,
            "stars": (info or {}).get("stargazers_count"),
            "archived": bool((info or {}).get("archived")),
            "source": (info or {}).get("_source", "rest"),
            "lists": repos[repo],
        })

    block = render(rows)
    if not args.check_only:
        if write_health(block):
            print("updated %s" % os.path.relpath(HEALTH, ROOT))

    if args.json:
        json.dump({"checked": TODAY.isoformat(), "repos": rows},
                  open(args.json, "w", encoding="utf-8"), indent=1)
        print("wrote %s" % args.json)

    flagged = [r for r in rows if r["status"] in BAD]
    print("\n%d repos checked. %d need attention." % (len(rows), len(flagged)))
    for r in flagged:
        print("  %-9s %-45s last push %s" % (r["status"], r["repo"], r["pushed"] or "never"))
    if errors:
        print("\n%d lookup errors:" % len(errors), file=sys.stderr)
        for e in errors[:10]:
            print("  " + e, file=sys.stderr)

    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())

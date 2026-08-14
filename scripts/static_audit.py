#!/usr/bin/env python3
"""Stage B static audit — the checks that gate a repo's entry into this catalog.

Runs with the Python standard library only. No gitleaks/Trivy/Semgrep install,
no network. Point it at a directory of clones and it reports, per repo:

  1. hidden Unicode      zero-width, bidi override, Unicode tag chars, soft hyphen
  2. SQL injection       queries built by concatenation or interpolation
  3. fetch-and-exec      curl|sh, iwr|iex and friends
  4. install hooks       npm lifecycle, setup.py/pyproject build hooks,
                         GitHub Actions pull_request_target that checks out PR head
  5. malware fixtures    repos that ship live malware samples in their test corpus

Findings are STARTING POINTS, not verdicts. Every one needs a human look; see
docs/SECURITY-SCANNING.md for the triage rules and the known false-positive
shapes. A repo is not rejected because a number here is non-zero.

Usage:
  python scripts/static_audit.py <clones-dir>            # human-readable
  python scripts/static_audit.py <clones-dir> --json out.json
  python scripts/static_audit.py <clones-dir> --jobs 1   # force single process

Exit codes:
  0  no findings in the blocking classes (hidden Unicode, unsafe pull_request_target)
  1  at least one blocking-class finding needs review
"""
import argparse
import io
import json
import os
import re
import sys
import unicodedata
from concurrent.futures import ProcessPoolExecutor

SKIP_DIRS = frozenset((".git", "node_modules", "__pycache__", ".venv", "venv",
                       "target", "dist", "build", ".next", "vendor"))

TEXT_EXT = frozenset((".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".go", ".rb",
                      ".php", ".java", ".cs", ".sh", ".ps1", ".bat", ".cmd",
                      ".sql", ".md", ".txt", ".yml", ".yaml", ".json", ".toml",
                      ".cfg", ".ini", ".html", ".mjs", ".cjs"))
BARE_NAMES = frozenset(("Makefile", "Dockerfile", "install.sh"))

MAX_BYTES = 700_000

# --- 1. hidden Unicode -------------------------------------------------------
# One compiled character class, matched in C. The previous implementation looped
# over every character in Python and called ord() on each -- 2.7M calls on a
# 3k-file corpus, and the single largest cost in the whole scan.
# Built from codepoint numbers, never literal characters. Embedding the real
# codepoints here would make this file match its own rule -- the scanner would
# block itself, the same way gitleaks matches its own test fixtures.
_HIDDEN_RANGES = (
    (0x200B, 0x200F),    # zero-width space/non-joiner/joiner, LRM, RLM
    (0x202A, 0x202E),    # bidi embedding and override
    (0x2060, 0x2064),    # word joiner, invisible operators
    (0x206A, 0x206F),    # deprecated format controls
    (0xE0000, 0xE007F),  # Unicode tag characters
    (0xFEFF, 0xFEFF),    # BOM / ZWNBSP
    (0x00AD, 0x00AD),    # soft hyphen
    (0x180E, 0x180E),    # Mongolian vowel separator
)


def _charclass(ranges):
    return "[%s]" % "".join(
        chr(a) if a == b else "%s-%s" % (chr(a), chr(b)) for a, b in ranges)


HIDDEN_RE = re.compile(_charclass(_HIDDEN_RANGES))

ZWJ = chr(0x200D)
BOM = chr(0xFEFF)

# U+200D joins emoji into single glyphs (family, profession, flag sequences). That
# is the character doing its job, not concealment, so it only counts when neither
# neighbour is pictographic.
PICTOGRAPHIC_RE = re.compile(_charclass((
    (0x1F000, 0x1FAFF),  # emoji blocks
    (0x2600, 0x27BF),    # misc symbols and dingbats
    (0xFE0F, 0xFE0F),    # variation selector-16
    (0x1F3FB, 0x1F3FF),  # skin-tone modifiers
)))

# Paths whose whole purpose is to hold weird input. A hit here is the repo testing
# its own defences; it still gets reported, but as review rather than blocking.
FIXTURE_PATH = re.compile(
    r"(?:^|/)(?:tests?|spec|fixtures?|testdata|examples?|__tests__)/"
    r"|test[-_][^/]*\.(?:md|json|txt|py|js|ts)$", re.I)

# --- 2. SQL injection --------------------------------------------------------
# Tightened against the false positives seen in the 2026-08-14 run: the keyword
# must be followed by SQL syntax (not English prose), and a query whose only
# interpolation is a bare identifier next to a bound-parameter marker is safe.
SQL_KEYWORD = r"(?:SELECT\s+[\w*\{]|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|DROP\s+TABLE)"
BOUND_MARKER = re.compile(r"(\?|\$\d+|%s|:\w+)\s*[,)\]]|VALUES\s*\(\s*(\?|\$\d+|%s)", re.I)

SQLI_RULES = (
    (re.compile(r"(?i)(?:execute|query|exec|run)\s*\(\s*[\"'][^\"']*" + SQL_KEYWORD +
                r"[^\"']*[\"']\s*[%+]"), "SQL built by concatenation into execute()"),
    (re.compile(r"(?i)f[\"'][^\"']*" + SQL_KEYWORD + r"[^\"']*\{"),
     "f-string interpolation inside a SQL literal"),
    (re.compile(r"(?i)[\"'][^\"']*" + SQL_KEYWORD + r"[^\"']*[\"']\s*\+\s*[A-Za-z_]"),
     "SQL string joined with + to a variable"),
    (re.compile(r"(?i)[\"'][^\"']*" + SQL_KEYWORD + r"[^\"']*[\"']\s*\.\s*format\s*\("),
     "SQL built with .format()"),
)

# Cheap pre-filter: if none of these bare words appear, no SQL rule can match, so
# four expensive alternation searches are skipped entirely. Most files skip here.
SQL_PREFILTER = re.compile(r"(?i)\b(?:select|insert|update|delete|drop)\b")

# --- 3. fetch-and-exec -------------------------------------------------------
FETCH_EXEC = re.compile(
    r"(?:curl|wget)\s[^\n|]*\|\s*(?:sudo\s+)?(?:ba|z|d)?sh"
    r"|iwr\s[^\n|]*\|\s*iex"
    r"|Invoke-Expression\s*\(\s*(?:New-Object\s+Net\.WebClient|Invoke-WebRequest)",
    re.I)

# --- 4. install hooks --------------------------------------------------------
HOOK_RULES = {
    "package.json": (re.compile(r'"(?:preinstall|install|postinstall)"\s*:'),
                     "npm lifecycle hook"),
    "setup.py": (re.compile(r"class\s+\w*(?:Install|Develop|Build)\w*\s*\(|cmdclass\s*="),
                 "setup.py build hook"),
    "pyproject.toml": (re.compile(r"^build-backend", re.M), "pyproject build backend"),
}
PR_TARGET = re.compile(r"^\s*pull_request_target\s*:", re.M)
# The dangerous shape: checking out the PR's own head under pull_request_target.
PR_HEAD_CHECKOUT = re.compile(
    r"ref\s*:\s*\$\{\{\s*github\.event\.pull_request\.head\.(?:sha|ref)")

# --- 5. malware fixtures -----------------------------------------------------
MALWARE_FIXTURE = re.compile(
    r"(?i)(?:malware|malicious|threat|exploit|payload|virus)[-_/\\]?"
    r"(?:sample|fixture|test|corpus|sourcecode)"
    r"|tests?[/\\][^/\\]*(?:malicious|malware|exfiltrat)")

CLASSES = ("hidden", "hidden_fixture", "sqli", "fetch_exec", "hooks",
           "pr_head_checkout", "fixtures")
BLOCKING = frozenset(("hidden", "pr_head_checkout"))


def iter_files(base):
    """Yield (abs_path, repo_relative_posix_path).

    Builds the relative path by joining components already in hand. os.path.relpath
    costs a normcase + splitdrive per call on Windows, which was ~17% of total
    runtime for no benefit here.
    """
    base_len = len(base) + 1
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        prefix = dirpath[base_len:].replace("\\", "/")
        if prefix:
            prefix += "/"
        for name in filenames:
            yield os.path.join(dirpath, name), prefix + name


def _hidden_hit(text, rel):
    """First concealment character, or None. Skips BOM-at-0 and emoji ZWJ."""
    for m in HIDDEN_RE.finditer(text):
        i, ch = m.start(), m.group()
        if ch == BOM and i == 0:
            continue                      # ordinary UTF-8 BOM
        if ch == ZWJ and (
                (i and PICTOGRAPHIC_RE.match(text, i - 1)) or
                PICTOGRAPHIC_RE.match(text, i + 1)):
            continue                      # emoji ZWJ sequence
        return "%s:%d U+%04X %s" % (
            rel, text.count("\n", 0, i) + 1, ord(ch), unicodedata.name(ch, "?"))
    return None


def scan_file(args):
    """Scan one file. Top-level and picklable so a process pool can call it."""
    path, rel = args
    out = []
    if MALWARE_FIXTURE.search(rel):
        out.append(("fixtures", rel))

    base = rel.rpartition("/")[2]
    if os.path.splitext(base)[1].lower() not in TEXT_EXT and base not in BARE_NAMES:
        return rel, out, 0
    try:
        with open(path, "rb") as fh:
            text = fh.read(MAX_BYTES).decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return rel, out, 0

    hit = _hidden_hit(text, rel)
    if hit:
        out.append(("hidden_fixture" if FIXTURE_PATH.search(rel) else "hidden", hit))

    if SQL_PREFILTER.search(text):
        for rule, label in SQLI_RULES:
            m = rule.search(text)
            if not m:
                continue
            if BOUND_MARKER.search(text, m.start(), m.end() + 120):
                continue                  # real parameters present alongside
            out.append(("sqli", "%s:%d %s" % (
                rel, text.count("\n", 0, m.start()) + 1, label)))
            break

    m = FETCH_EXEC.search(text)
    if m:
        out.append(("fetch_exec", "%s:%d %s" % (
            rel, text.count("\n", 0, m.start()) + 1, m.group(0)[:70].strip())))

    hook = HOOK_RULES.get(base)
    if hook and hook[0].search(text):
        out.append(("hooks", "%s - %s" % (rel, hook[1])))

    if "/workflows/" in rel and base.endswith((".yml", ".yaml")) and PR_TARGET.search(text):
        if PR_HEAD_CHECKOUT.search(text):
            out.append(("pr_head_checkout",
                        "%s - pull_request_target checks out PR head" % rel))
        else:
            out.append(("hooks",
                        "%s - pull_request_target (checks out base, review anyway)" % rel))
    return rel, out, 1


def collect(results):
    found = {k: [] for k in CLASSES}
    found["files"] = 0
    for _rel, hits, counted in results:
        found["files"] += counted
        for cls, entry in hits:
            found[cls].append(entry)
    # os.walk order is not stable across parallel workers; sort so two runs of the
    # same corpus always produce byte-identical output.
    for k in CLASSES:
        found[k].sort()
    return found


LABELS = (
    ("hidden", "hidden unicode"),
    ("pr_head_checkout", "unsafe pr_target"),
    ("hidden_fixture", "hidden (fixture)"),
    ("sqli", "sql injection"),
    ("fetch_exec", "fetch-and-exec"),
    ("hooks", "install hooks"),
    ("fixtures", "malware fixtures"),
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clones_dir")
    ap.add_argument("--json", metavar="PATH")
    ap.add_argument("--jobs", type=int, default=0,
                    help="worker processes; 0 = auto, 1 = in-process")
    args = ap.parse_args()

    if not os.path.isdir(args.clones_dir):
        sys.exit("not a directory: %s" % args.clones_dir)

    repos = sorted(n for n in os.listdir(args.clones_dir)
                   if os.path.isdir(os.path.join(args.clones_dir, n)))
    work = {r: list(iter_files(os.path.join(args.clones_dir, r))) for r in repos}
    total = sum(len(v) for v in work.values())

    jobs = args.jobs or min(os.cpu_count() or 1, 8)
    # Process startup costs more than it saves on small trees; regex work holds the
    # GIL, so threads would not help here -- it is processes or nothing.
    if jobs > 1 and total > 400:
        chunk = max(32, total // (jobs * 4))
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            results = {r: collect(pool.map(scan_file, files, chunksize=chunk))
                       for r, files in work.items()}
    else:
        results = {r: collect(map(scan_file, files)) for r, files in work.items()}

    blocking_total = 0
    for name, r in results.items():
        print("=" * 74)
        print("%s   (%d text files)" % (name, r["files"]))
        for key, label in LABELS:
            hits = r[key]
            if not hits:
                print("  %-18s clean" % label)
                continue
            if key in BLOCKING:
                blocking_total += len(hits)
            print("  %-18s %d  [%s]" % (
                label, len(hits), "BLOCK" if key in BLOCKING else "review"))
            for h in hits[:6]:
                print("      %s" % h)
            if len(hits) > 6:
                print("      ... +%d more" % (len(hits) - 6))

    if args.json:
        io.open(args.json, "w", encoding="utf-8").write(json.dumps(results, indent=1))
        print("\nwrote %s" % args.json)

    print("\n%d finding(s) in blocking classes." % blocking_total)
    return 1 if blocking_total else 0


if __name__ == "__main__":
    sys.exit(main())

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

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "target",
             "dist", "build", ".next", "vendor"}

TEXT_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".go", ".rb", ".php",
            ".java", ".cs", ".sh", ".ps1", ".bat", ".cmd", ".sql", ".md", ".txt",
            ".yml", ".yaml", ".json", ".toml", ".cfg", ".ini", ".html", ".mjs",
            ".cjs"}
BARE_NAMES = {"Makefile", "Dockerfile", "install.sh"}

MAX_BYTES = 700_000

# --- 1. hidden Unicode -------------------------------------------------------
HIDDEN = (set(range(0x200B, 0x2010)) | set(range(0x202A, 0x202F)) |
          set(range(0x2060, 0x2065)) | set(range(0x206A, 0x2070)) |
          set(range(0xE0000, 0xE0080)) | {0xFEFF, 0x00AD, 0x180E})

# U+200D joins emoji into single glyphs (family, profession, flag sequences). That
# is the character doing its job, not concealment, so it only counts when neither
# neighbour is pictographic.
ZWJ = 0x200D


def _pictographic(ch):
    cp = ord(ch)
    return (0x1F000 <= cp <= 0x1FAFF or 0x2600 <= cp <= 0x27BF or
            0xFE0F == cp or 0x1F3FB <= cp <= 0x1F3FF)


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

SQLI_RULES = [
    (re.compile(r"(?i)(?:execute|query|exec|run)\s*\(\s*[\"'][^\"']*" + SQL_KEYWORD +
                r"[^\"']*[\"']\s*[%+]"), "SQL built by concatenation into execute()"),
    (re.compile(r"(?i)f[\"'][^\"']*" + SQL_KEYWORD + r"[^\"']*\{"),
     "f-string interpolation inside a SQL literal"),
    (re.compile(r"(?i)[\"'][^\"']*" + SQL_KEYWORD + r"[^\"']*[\"']\s*\+\s*[A-Za-z_]"),
     "SQL string joined with + to a variable"),
    (re.compile(r"(?i)[\"'][^\"']*" + SQL_KEYWORD + r"[^\"']*[\"']\s*\.\s*format\s*\("),
     "SQL built with .format()"),
]

# --- 3. fetch-and-exec -------------------------------------------------------
FETCH_EXEC = re.compile(
    r"(?:curl|wget)\s[^\n|]*\|\s*(?:sudo\s+)?(?:ba|z|d)?sh"
    r"|iwr\s[^\n|]*\|\s*iex"
    r"|Invoke-Expression\s*\(\s*(?:New-Object\s+Net\.WebClient|Invoke-WebRequest)",
    re.I)

# --- 4. install hooks --------------------------------------------------------
HOOK_RULES = [
    ("package.json", re.compile(r'"(?:preinstall|install|postinstall)"\s*:'),
     "npm lifecycle hook"),
    ("setup.py", re.compile(r"class\s+\w*(?:Install|Develop|Build)\w*\s*\(|cmdclass\s*="),
     "setup.py build hook"),
    ("pyproject.toml", re.compile(r"^build-backend", re.M), "pyproject build backend"),
]
PR_TARGET = re.compile(r"^\s*pull_request_target\s*:", re.M)
# The dangerous shape: checking out the PR's own head under pull_request_target.
PR_HEAD_CHECKOUT = re.compile(
    r"ref\s*:\s*\$\{\{\s*github\.event\.pull_request\.head\.(?:sha|ref)")

# --- 5. malware fixtures -----------------------------------------------------
MALWARE_FIXTURE = re.compile(
    r"(?i)(?:malware|malicious|threat|exploit|payload|virus)[-_/\\]?"
    r"(?:sample|fixture|test|corpus|sourcecode)"
    r"|tests?[/\\][^/\\]*(?:malicious|malware|exfiltrat)")

BLOCKING = ("hidden", "pr_head_checkout")


def iter_files(base):
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            yield os.path.join(dirpath, name)


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def scan_repo(repo_dir):
    found = {k: [] for k in ("hidden", "hidden_fixture", "sqli", "fetch_exec",
                             "hooks", "pr_head_checkout", "fixtures")}
    found["files"] = 0

    for path in iter_files(repo_dir):
        rel = os.path.relpath(path, repo_dir).replace("\\", "/")

        if MALWARE_FIXTURE.search(rel):
            found["fixtures"].append(rel)

        base = os.path.basename(path)
        if os.path.splitext(path)[1].lower() not in TEXT_EXT and base not in BARE_NAMES:
            continue
        try:
            text = io.open(path, "rb").read(MAX_BYTES).decode("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        found["files"] += 1

        is_fixture = bool(FIXTURE_PATH.search(rel))
        for i, ch in enumerate(text):
            cp = ord(ch)
            if cp not in HIDDEN:
                continue
            if cp == 0xFEFF and i == 0:
                continue              # ordinary UTF-8 BOM
            if cp == ZWJ and (
                    (i and _pictographic(text[i - 1])) or
                    (i + 1 < len(text) and _pictographic(text[i + 1]))):
                continue              # emoji ZWJ sequence
            entry = "%s:%d U+%04X %s" % (
                rel, line_of(text, i), cp, unicodedata.name(ch, "?"))
            found["hidden_fixture" if is_fixture else "hidden"].append(entry)
            break

        for rule, label in SQLI_RULES:
            m = rule.search(text)
            if not m:
                continue
            window = text[m.start():m.end() + 120]
            if BOUND_MARKER.search(window):
                continue              # real parameters present alongside
            found["sqli"].append("%s:%d %s" % (rel, line_of(text, m.start()), label))
            break

        m = FETCH_EXEC.search(text)
        if m:
            found["fetch_exec"].append("%s:%d %s" % (
                rel, line_of(text, m.start()), m.group(0)[:70].strip()))

        for fname, rule, label in HOOK_RULES:
            if base == fname and rule.search(text):
                found["hooks"].append("%s - %s" % (rel, label))

        if "/workflows/" in rel and base.endswith((".yml", ".yaml")):
            if PR_TARGET.search(text):
                if PR_HEAD_CHECKOUT.search(text):
                    found["pr_head_checkout"].append(
                        "%s - pull_request_target checks out PR head" % rel)
                else:
                    found["hooks"].append(
                        "%s - pull_request_target (checks out base, review anyway)" % rel)
    return found


LABELS = [
    ("hidden", "hidden unicode"),
    ("pr_head_checkout", "unsafe pr_target"),
    ("hidden_fixture", "hidden (fixture)"),
    ("sqli", "sql injection"),
    ("fetch_exec", "fetch-and-exec"),
    ("hooks", "install hooks"),
    ("fixtures", "malware fixtures"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clones_dir")
    ap.add_argument("--json", metavar="PATH")
    args = ap.parse_args()

    if not os.path.isdir(args.clones_dir):
        sys.exit("not a directory: %s" % args.clones_dir)

    results = {}
    for name in sorted(os.listdir(args.clones_dir)):
        d = os.path.join(args.clones_dir, name)
        if os.path.isdir(d):
            results[name] = scan_repo(d)

    blocking_total = 0
    for name, r in results.items():
        print("=" * 74)
        print("%s   (%d text files)" % (name, r["files"]))
        for key, label in LABELS:
            hits = r[key]
            if not hits:
                print("  %-18s clean" % label)
                continue
            mark = "BLOCK" if key in BLOCKING else "review"
            if key in BLOCKING:
                blocking_total += len(hits)
            print("  %-18s %d  [%s]" % (label, len(hits), mark))
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

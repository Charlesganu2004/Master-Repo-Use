#!/usr/bin/env python3
"""Continuous health/security/lifecycle guardian for Master-Repo-Use.

Policy defaults:
- healthy: pushed within 180 days
- stale grace: 181-365 days since last push
- stale removal: >365 days since last push
- archived grace: 30 days from first observation of archived=true
- deleted/disabled repos: immediate removal candidate
- CRITICAL deep-scan findings: immediate removal candidate

A repo is only auto-removed from catalog lists when --apply-removals is supplied.
Before lifecycle removal, the guardian deep-scans the repo. If it is security-clean
and has a recognized permissive/open-source license, it writes a managed-adoption
candidate under managed-repos/candidates/ for owner review. It never silently copies
third-party code or creates a fork because license obligations and maintenance scope
require an explicit owner decision.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Iterable

ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOG = ROOT / "repo-lists" / "all-curated.txt"
STATE = ROOT / "docs" / "catalog-status.json"
REPORT = ROOT / "docs" / "CATALOG-STATUS.md"
SVG = ROOT / "docs" / "catalog-status.svg"
REMOVALS = ROOT / "docs" / "AUTO-REMOVALS.md"
MANAGED = ROOT / "managed-repos" / "candidates"

INVISIBLE = {
    "\u200b", "\u200c", "\u200d", "\u2060", "\ufeff",
    "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",
    "\u2066", "\u2067", "\u2068", "\u2069",
}
TEXT_EXT = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".cs", ".cpp", ".c", ".h", ".hpp",
    ".java", ".go", ".rs", ".rb", ".php", ".sh", ".ps1", ".bat", ".cmd",
    ".sql", ".json", ".yaml", ".yml", ".toml", ".xml", ".md", ".txt",
    ".env", ".ini", ".cfg", ".conf", ".html", ".css", ".vue", ".svelte",
}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "target", "vendor"}

SUSPICIOUS_PATTERNS = [
    ("download-to-shell", re.compile(r"(?:curl|wget)[^\n|;]*(?:\||;|&&)\s*(?:sh|bash|zsh)\b", re.I)),
    ("powershell-encoded", re.compile(r"powershell(?:\.exe)?[^\n]{0,120}-(?:enc|encodedcommand)\b", re.I)),
    ("base64-exec", re.compile(r"(?:base64\s+-d|frombase64string|b64decode)[^\n]{0,180}(?:exec|eval|invoke-expression|iex|system\()", re.I)),
    ("dynamic-eval", re.compile(r"\b(?:eval|exec|Invoke-Expression|iex)\s*\(", re.I)),
    ("credential-exfil", re.compile(r"(?:AWS_SECRET_ACCESS_KEY|GITHUB_TOKEN|ANTHROPIC_API_KEY|OPENAI_API_KEY)[^\n]{0,160}(?:requests\.|fetch\(|curl|wget|http)", re.I)),
]
SQL_PATTERNS = [
    re.compile(r"(?:execute|query|raw|exec)\s*\(\s*f?[\"'][^\n]*\b(?:select|insert|update|delete)\b[^\n]*(?:\{|\+|%s|format\()", re.I),
    re.compile(r"(?:SELECT|INSERT|UPDATE|DELETE)[^\n]{0,200}(?:\+\s*\w+|\$\{\w+\}|\{\w+\})", re.I),
]
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]
EXEC_MAGIC = (b"MZ", b"\x7fELF")
ADOPTABLE_LICENSES = {
    "mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "isc",
    "mpl-2.0", "epl-2.0", "unlicense", "cc0-1.0",
}


@dataclass
class Result:
    repo: str
    status: str = "UNKNOWN"
    pushed_at: str | None = None
    archived: bool = False
    disabled: bool = False
    age_days: int | None = None
    archived_first_seen: str | None = None
    archived_days: int | None = None
    license: str | None = None
    deep_scanned: bool = False
    findings: list[str] | None = None
    critical: bool = False
    adoption_candidate: bool = False
    note: str = ""


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def parse_iso(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def repos() -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in CATALOG.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.count("/") != 1 or line in seen:
            continue
        seen.add(line)
        out.append(line)
    return out


def github_json(repo: str) -> dict | None:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "master-repo-guardian"},
    )
    token = os.getenv("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def iter_files(base: pathlib.Path) -> Iterable[pathlib.Path]:
    for path in base.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            if path.stat().st_size > 2_000_000:
                continue
        except OSError:
            continue
        yield path


def scan_text(path: pathlib.Path, text: str) -> list[str]:
    findings: list[str] = []
    controls = sorted({f"U+{ord(char):04X}" for char in text if char in INVISIBLE})
    if controls:
        findings.append(f"HIGH invisible/bidi controls {','.join(controls)} in {path}")
    for name, pattern in SUSPICIOUS_PATTERNS:
        if pattern.search(text):
            severity = "CRITICAL" if name == "credential-exfil" else "HIGH"
            findings.append(f"{severity} {name} pattern in {path}")
    for pattern in SQL_PATTERNS:
        if pattern.search(text):
            findings.append(f"HIGH possible SQL injection construction in {path}")
            break
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(f"CRITICAL secret/private-key material in {path}")
            break
    return findings


def external_scan(cmd: list[str], cwd: pathlib.Path, label: str) -> list[str]:
    if shutil.which(cmd[0]) is None:
        return []
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, text=True, capture_output=True, timeout=900,
            env=os.environ.copy(),
        )
    except Exception as exc:
        return [f"INFO {label} unavailable: {exc}"]
    if proc.returncode == 0:
        return []
    sample = (proc.stdout + "\n" + proc.stderr).strip().replace("\n", " ")[:700]
    return [f"HIGH {label} reported findings: {sample}"]


def deep_scan(repo: str) -> tuple[list[str], bool]:
    findings: list[str] = []
    with tempfile.TemporaryDirectory(prefix="master-repo-guardian-") as tmp:
        clone = pathlib.Path(tmp) / "repo"
        proc = subprocess.run(
            ["git", "clone", "--depth", "1", "--filter=blob:none", f"https://github.com/{repo}.git", str(clone)],
            text=True, capture_output=True, timeout=300,
        )
        if proc.returncode != 0:
            return [f"HIGH clone failed: {proc.stderr.strip()[:400]}"], False

        for path in iter_files(clone):
            rel = path.relative_to(clone)
            try:
                head = path.read_bytes()[:4]
            except OSError:
                continue
            if any(head.startswith(magic) for magic in EXEC_MAGIC):
                findings.append(f"HIGH embedded executable binary: {rel}")
                continue
            if path.suffix.lower() not in TEXT_EXT and path.name not in {
                "Dockerfile", "Makefile", "requirements.txt", "Pipfile", "Gemfile"
            }:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            findings.extend(scan_text(rel, text))
            if len(findings) >= 100:
                findings.append("INFO finding limit reached")
                break

        findings += external_scan(
            ["gitleaks", "detect", "--no-banner", "--source", "."], clone, "gitleaks"
        )
        findings += external_scan(
            ["trivy", "fs", "--scanners", "vuln,secret,misconfig", "--severity", "HIGH,CRITICAL", "--exit-code", "1", "."],
            clone, "trivy",
        )
        findings += external_scan(
            ["osv-scanner", "scan", "source", "-r", "."], clone, "osv-scanner"
        )
        findings += external_scan(
            ["semgrep", "--config", "p/sql-injection", "--error", "."], clone, "semgrep-sql-injection"
        )
        findings += external_scan(
            ["semgrep", "--config", "p/command-injection", "--error", "."], clone, "semgrep-command-injection"
        )
        if shutil.which("clamscan"):
            findings += external_scan(["clamscan", "-r", "--infected", "."], clone, "clamav")
        if shutil.which("snyk") and os.getenv("SNYK_TOKEN"):
            findings += external_scan(
                ["snyk", "test", "--all-projects", "--severity-threshold=high"], clone, "snyk"
            )

    critical = any(item.startswith("CRITICAL") for item in findings)
    return findings, critical


def lifecycle_status(
    repo: str,
    meta: dict | None,
    previous: dict,
    stale_after_days: int,
    remove_stale_after_days: int,
    archive_grace_days: int,
) -> Result:
    if meta is None:
        return Result(repo=repo, status="REMOVE", critical=True, note="repository deleted or inaccessible")

    pushed = meta.get("pushed_at")
    pushed_dt = parse_iso(pushed)
    age_days = (now_utc() - pushed_dt).days if pushed_dt else None
    archived = bool(meta.get("archived"))
    disabled = bool(meta.get("disabled"))
    license_key = ((meta.get("license") or {}).get("key") or "").lower() or None

    archived_first_seen = previous.get("archived_first_seen")
    archived_days = None
    if archived:
        if not archived_first_seen:
            archived_first_seen = now_utc().date().isoformat()
        seen_dt = parse_iso(archived_first_seen + "T00:00:00+00:00")
        archived_days = (now_utc() - seen_dt).days if seen_dt else 0
    else:
        archived_first_seen = None

    if disabled:
        status = "REMOVE"
        note = "repository disabled"
    elif archived:
        if archived_days is not None and archived_days >= archive_grace_days:
            status = "REMOVE"
            note = f"archived for {archived_days}d (grace {archive_grace_days}d)"
        else:
            status = "STALE"
            note = f"archived; {archived_days or 0}d into {archive_grace_days}d grace"
    elif age_days is not None and age_days > remove_stale_after_days:
        status = "REMOVE"
        note = f"no push for {age_days}d (removal threshold {remove_stale_after_days}d)"
    elif age_days is not None and age_days > stale_after_days:
        status = "STALE"
        note = f"no push for {age_days}d (stale after {stale_after_days}d)"
    else:
        status = "HEALTHY"
        note = ""

    return Result(
        repo=repo,
        status=status,
        pushed_at=pushed,
        archived=archived,
        disabled=disabled,
        age_days=age_days,
        archived_first_seen=archived_first_seen,
        archived_days=archived_days,
        license=license_key,
        note=note,
    )


def remove_from_repo_lists(repo: str) -> None:
    for path in (ROOT / "repo-lists").glob("*.txt"):
        lines = path.read_text(encoding="utf-8").splitlines()
        kept = [line for line in lines if line.split("#", 1)[0].strip() != repo]
        if kept != lines:
            path.write_text("\n".join(kept).rstrip() + "\n", encoding="utf-8")


def adoption_plan(result: Result) -> pathlib.Path | None:
    if result.critical or result.license not in ADOPTABLE_LICENSES or not result.deep_scanned:
        return None
    if any(item.startswith(("HIGH", "CRITICAL")) for item in (result.findings or [])):
        return None

    MANAGED.mkdir(parents=True, exist_ok=True)
    slug = result.repo.replace("/", "__") + ".md"
    path = MANAGED / slug
    if path.exists():
        return path

    body = f"""# Managed adoption candidate: {result.repo}

Status: **OWNER REVIEW REQUIRED**

Why it entered this lane: {result.note or result.status}

Upstream: `https://github.com/{result.repo}`
Detected license: `{result.license}`
Last upstream push: `{result.pushed_at or 'unknown'}`

## Gate passed

- Deep source scan completed.
- No HIGH or CRITICAL guardian findings were detected in the scanned revision.
- License is in the Master Repo adoptable-license allowlist.

## Required owner decision

Do not copy or fork code automatically. Charles must approve the adoption scope first.

If approved:

1. Re-check the upstream LICENSE and NOTICE files manually.
2. Identify only the still-useful components.
3. Create a maintained replacement under the Charlesganu2004 account or a clearly named `managed/` package.
4. Preserve copyright, license, NOTICE, and attribution obligations.
5. Upgrade dependencies, CI, tests, documentation, and security controls.
6. Run the full guardian plus Snyk/Trivy/OSV/Gitleaks/Semgrep before cataloging the replacement.
7. Add the maintained replacement to `repo-lists/all-curated.txt` only after the owner-approved review passes.

The stale/archived upstream may be removed from the active catalog independently of this adoption decision.
"""
    path.write_text(body, encoding="utf-8")
    return path


def render(
    results: list[Result],
    stale_after_days: int,
    remove_stale_after_days: int,
    archive_grace_days: int,
) -> None:
    now_text = now_utc().strftime("%Y-%m-%d %H:%M UTC")
    statuses = ("HEALTHY", "STALE", "REVIEW", "REMOVE")
    counts = {key: sum(result.status == key for result in results) for key in statuses}
    payload = {
        "updated": now_text,
        "policy": {
            "stale_after_days": stale_after_days,
            "remove_stale_after_days": remove_stale_after_days,
            "archive_grace_days": archive_grace_days,
        },
        "counts": counts,
        "repos": [asdict(result) for result in results],
    }
    STATE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    rows = [
        "# Catalog Status",
        "",
        f"Last automated update: **{now_text}**",
        "",
        f"Policy: stale warning after **{stale_after_days}d** without a push; automatic stale removal after **{remove_stale_after_days}d**; archived repos get a **{archive_grace_days}d** grace period from first detection.",
        "",
        f"🟢 Healthy **{counts['HEALTHY']}** · 🟡 Stale **{counts['STALE']}** · 🟠 Review **{counts['REVIEW']}** · 🔴 Remove **{counts['REMOVE']}**",
        "",
        "| Repo | Status | Last push | Age | Archived age | License | Deep scan | Managed candidate | Note |",
        "|---|---|---:|---:|---:|---|---:|---:|---|",
    ]
    icon = {"HEALTHY": "🟢", "STALE": "🟡", "REVIEW": "🟠", "REMOVE": "🔴"}
    for result in sorted(results, key=lambda item: (item.status, item.repo)):
        note = result.note or (result.findings[0] if result.findings else "")
        rows.append(
            f"| `{result.repo}` | {icon.get(result.status, '⚪')} {result.status} | "
            f"{result.pushed_at or '—'} | "
            f"{str(result.age_days) + 'd' if result.age_days is not None else '—'} | "
            f"{str(result.archived_days) + 'd' if result.archived_days is not None else '—'} | "
            f"{result.license or '—'} | {'yes' if result.deep_scanned else 'no'} | "
            f"{'yes' if result.adoption_candidate else 'no'} | {note.replace('|', '/')} |"
        )
    REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")

    total = max(1, len(results))
    review = counts["REVIEW"] + counts["STALE"]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="820" height="120" role="img" aria-label="Master Repo live catalog health">
<rect width="820" height="120" rx="10" fill="#0d1117"/>
<text x="24" y="30" fill="#f0f6fc" font-family="Segoe UI,Arial" font-size="17" font-weight="700">Master Repo — live catalog health &amp; security</text>
<text x="24" y="54" fill="#8b949e" font-family="Segoe UI,Arial" font-size="12">Updated {now_text} · stale {stale_after_days}d · remove {remove_stale_after_days}d · archived grace {archive_grace_days}d</text>
<text x="24" y="88" fill="#3fb950" font-family="Segoe UI,Arial" font-size="16">● Healthy {counts["HEALTHY"]}</text>
<text x="208" y="88" fill="#d29922" font-family="Segoe UI,Arial" font-size="16">● Review/Stale {review}</text>
<text x="440" y="88" fill="#f85149" font-family="Segoe UI,Arial" font-size="16">● Remove {counts["REMOVE"]}</text>
<text x="625" y="88" fill="#8b949e" font-family="Segoe UI,Arial" font-size="14">Total {total}</text>
</svg>"""
    SVG.write_text(svg, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stale-after-days", type=int, default=180)
    parser.add_argument("--remove-stale-after-days", type=int, default=365)
    parser.add_argument("--archive-grace-days", type=int, default=30)
    parser.add_argument("--deep", action="store_true")
    parser.add_argument("--batch-size", type=int, default=12)
    parser.add_argument("--batch-index", type=int, default=0)
    parser.add_argument("--force-repo", action="append", default=[])
    parser.add_argument("--apply-removals", action="store_true")
    args = parser.parse_args()

    if args.remove_stale_after_days <= args.stale_after_days:
        parser.error("--remove-stale-after-days must be greater than --stale-after-days")

    all_repos = repos()
    previous: dict[str, dict] = {}
    if STATE.exists():
        try:
            previous = {
                item["repo"]: item
                for item in json.loads(STATE.read_text(encoding="utf-8")).get("repos", [])
            }
        except Exception:
            previous = {}

    groups = max(1, (len(all_repos) + args.batch_size - 1) // args.batch_size)
    forced = set(args.force_repo)
    results: list[Result] = []
    auto_removed: list[Result] = []

    for index, repo in enumerate(all_repos):
        try:
            meta = github_json(repo)
        except Exception as exc:
            old = previous.get(repo, {})
            result = Result(
                repo=repo,
                status=old.get("status", "REVIEW"),
                pushed_at=old.get("pushed_at"),
                age_days=old.get("age_days"),
                archived_first_seen=old.get("archived_first_seen"),
                archived_days=old.get("archived_days"),
                license=old.get("license"),
                note=f"metadata error: {exc}",
            )
            results.append(result)
            continue

        result = lifecycle_status(
            repo,
            meta,
            previous.get(repo, {}),
            args.stale_after_days,
            args.remove_stale_after_days,
            args.archive_grace_days,
        )

        rotating = args.deep and index % groups == args.batch_index % groups
        lifecycle_removal = result.status == "REMOVE" and not result.critical
        should_deep = repo in forced or rotating or lifecycle_removal

        if should_deep and meta is not None and not result.disabled:
            result.findings, result.critical = deep_scan(repo)
            result.deep_scanned = True
            if result.critical:
                result.status = "REMOVE"
                result.note = "CRITICAL security finding"
            elif any(item.startswith("HIGH") for item in result.findings):
                result.status = "REVIEW"
                result.note = "HIGH security finding requires owner review"

        if result.status == "REMOVE" and result.deep_scanned and not result.critical:
            candidate_path = adoption_plan(result)
            result.adoption_candidate = candidate_path is not None
            if result.adoption_candidate:
                result.note = (result.note + "; managed adoption candidate created").strip("; ")

        if args.apply_removals and result.status == "REMOVE":
            remove_from_repo_lists(repo)
            auto_removed.append(result)

        results.append(result)

    render(results, args.stale_after_days, args.remove_stale_after_days, args.archive_grace_days)

    if auto_removed:
        REMOVALS.parent.mkdir(parents=True, exist_ok=True)
        stamp = now_utc().strftime("%Y-%m-%d %H:%M UTC")
        existing = REMOVALS.read_text(encoding="utf-8") if REMOVALS.exists() else "# Automatic Catalog Removals\n\n"
        lines = [existing.rstrip(), "", f"## {stamp}", ""]
        for result in auto_removed:
            managed_note = " — managed adoption candidate created" if result.adoption_candidate else ""
            lines.append(f"- `{result.repo}` — {result.note or result.status}{managed_note}")
        REMOVALS.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Continuous health/security guardian for Master-Repo-Use catalog.

Runs in two layers:
1) GitHub metadata: existence, archived/disabled state, push recency.
2) Optional deep scan: shallow-clone a rotating batch and inspect source for
   invisible/bidi text, suspicious execution/download patterns, likely SQL
   injection construction, secret-like material, and unexpected executables.
   If external scanners are installed, run them too.

Automatic removal is deliberately conservative: only deleted/disabled/archived
repos or deep-scan CRITICAL findings are removed when --apply-removals is set.
Staleness alone is flagged, never auto-removed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from typing import Iterable

ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOG = ROOT / "repo-lists" / "all-curated.txt"
STATE = ROOT / "docs" / "catalog-status.json"
REPORT = ROOT / "docs" / "CATALOG-STATUS.md"
SVG = ROOT / "docs" / "catalog-status.svg"
REMOVALS = ROOT / "docs" / "AUTO-REMOVALS.md"

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
EXEC_MAGIC = [(b"MZ", "PE"), (b"\x7fELF", "ELF")]

@dataclass
class Result:
    repo: str
    status: str = "UNKNOWN"
    pushed_at: str | None = None
    archived: bool = False
    disabled: bool = False
    age_days: int | None = None
    deep_scanned: bool = False
    findings: list[str] | None = None
    critical: bool = False
    note: str = ""


def repos() -> list[str]:
    out: list[str] = []
    seen = set()
    for raw in CATALOG.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.count("/") != 1 or line in seen:
            continue
        seen.add(line); out.append(line)
    return out


def github_json(repo: str) -> dict | None:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}",
        headers={"Accept":"application/vnd.github+json","User-Agent":"master-repo-guardian"},
    )
    token = os.getenv("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def iter_files(base: pathlib.Path) -> Iterable[pathlib.Path]:
    for p in base.rglob("*"):
        if not p.is_file() or any(part in SKIP_DIRS for part in p.parts):
            continue
        try:
            if p.stat().st_size > 2_000_000:
                continue
        except OSError:
            continue
        yield p


def scan_text(path: pathlib.Path, text: str) -> list[str]:
    f: list[str] = []
    controls = sorted({f"U+{ord(c):04X}" for c in text if c in INVISIBLE})
    if controls:
        f.append(f"HIGH invisible/bidi controls {','.join(controls)} in {path}")
    for name, pat in SUSPICIOUS_PATTERNS:
        if pat.search(text):
            sev = "HIGH" if name != "credential-exfil" else "CRITICAL"
            f.append(f"{sev} {name} pattern in {path}")
    for pat in SQL_PATTERNS:
        if pat.search(text):
            f.append(f"HIGH possible SQL injection construction in {path}")
            break
    for pat in SECRET_PATTERNS:
        if pat.search(text):
            f.append(f"CRITICAL secret/private-key material in {path}")
            break
    return f


def external_scan(cmd: list[str], cwd: pathlib.Path, label: str) -> list[str]:
    if shutil.which(cmd[0]) is None:
        return []
    try:
        p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=600)
    except Exception as e:
        return [f"INFO {label} unavailable: {e}"]
    if p.returncode == 0:
        return []
    sample = (p.stdout + "\n" + p.stderr).strip().replace("\n", " ")[:500]
    return [f"HIGH {label} reported findings: {sample}"]


def deep_scan(repo: str) -> tuple[list[str], bool]:
    findings: list[str] = []
    with tempfile.TemporaryDirectory(prefix="master-repo-guardian-") as td:
        clone = pathlib.Path(td) / "repo"
        p = subprocess.run(
            ["git", "clone", "--depth", "1", "--filter=blob:none", f"https://github.com/{repo}.git", str(clone)],
            text=True, capture_output=True, timeout=300,
        )
        if p.returncode != 0:
            return [f"HIGH clone failed: {p.stderr.strip()[:300]}"], False
        for path in iter_files(clone):
            rel = path.relative_to(clone)
            try:
                head = path.read_bytes()[:4]
            except OSError:
                continue
            if any(head.startswith(magic) for magic, _ in EXEC_MAGIC):
                findings.append(f"HIGH embedded executable binary: {rel}")
                continue
            if path.suffix.lower() not in TEXT_EXT and path.name not in {"Dockerfile", "Makefile", "requirements.txt"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            findings.extend(scan_text(rel, text))
            if len(findings) >= 80:
                findings.append("INFO finding limit reached")
                break
        findings += external_scan(["gitleaks", "detect", "--no-banner", "--source", "."], clone, "gitleaks")
        findings += external_scan(["trivy", "fs", "--scanners", "vuln,secret,misconfig", "--severity", "HIGH,CRITICAL", "--exit-code", "1", "."], clone, "trivy")
        findings += external_scan(["osv-scanner", "scan", "source", "-r", "."], clone, "osv-scanner")
        findings += external_scan(["semgrep", "--config", "p/sql-injection", "--error", "."], clone, "semgrep-sql-injection")
        if shutil.which("clamscan"):
            findings += external_scan(["clamscan", "-r", "--infected", "."], clone, "clamav")
    critical = any(x.startswith("CRITICAL") for x in findings)
    return findings, critical


def status_for(meta: dict | None, stale_days: int) -> Result:
    if meta is None:
        return Result(repo="", status="REMOVE", critical=True, note="repository deleted or inaccessible")
    pushed = meta.get("pushed_at")
    age = None
    if pushed:
        then = dt.datetime.fromisoformat(pushed.replace("Z", "+00:00"))
        age = (dt.datetime.now(dt.timezone.utc) - then).days
    archived = bool(meta.get("archived")); disabled = bool(meta.get("disabled"))
    if archived or disabled:
        status = "REMOVE"
    elif age is not None and age > stale_days:
        status = "STALE"
    else:
        status = "HEALTHY"
    return Result(repo="", status=status, pushed_at=pushed, archived=archived, disabled=disabled, age_days=age)


def remove_from_repo_lists(repo: str) -> None:
    for p in (ROOT / "repo-lists").glob("*.txt"):
        lines = p.read_text(encoding="utf-8").splitlines()
        kept = [line for line in lines if line.split("#",1)[0].strip() != repo]
        if kept != lines:
            p.write_text("\n".join(kept).rstrip()+"\n", encoding="utf-8")


def render(results: list[Result]) -> None:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    counts = {k: sum(r.status == k for r in results) for k in ("HEALTHY","STALE","REVIEW","REMOVE")}
    STATE.write_text(json.dumps({"updated":now,"counts":counts,"repos":[asdict(r) for r in results]}, indent=2)+"\n", encoding="utf-8")
    rows = ["# Catalog Status", "", f"Last automated update: **{now}**", "",
            f"🟢 Healthy **{counts['HEALTHY']}** · 🟡 Stale **{counts['STALE']}** · 🟠 Review **{counts['REVIEW']}** · 🔴 Remove **{counts['REMOVE']}**", "",
            "| Repo | Status | Last push | Age | Deep scan | Security note |", "|---|---|---:|---:|---:|---|"]
    icon={"HEALTHY":"🟢","STALE":"🟡","REVIEW":"🟠","REMOVE":"🔴"}
    for r in sorted(results,key=lambda x:(x.status,x.repo)):
        note = r.note or (r.findings[0] if r.findings else "")
        rows.append(f"| `{r.repo}` | {icon.get(r.status,'⚪')} {r.status} | {r.pushed_at or '—'} | {r.age_days if r.age_days is not None else '—'}d | {'yes' if r.deep_scanned else 'no'} | {note.replace('|','/')} |")
    REPORT.write_text("\n".join(rows)+"\n", encoding="utf-8")
    total=max(1,len(results)); healthy=counts['HEALTHY']; review=counts['REVIEW']+counts['STALE']; remove=counts['REMOVE']
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="110" role="img" aria-label="Master Repo catalog health">
<rect width="760" height="110" rx="10" fill="#0d1117"/>
<text x="24" y="30" fill="#f0f6fc" font-family="Segoe UI,Arial" font-size="17" font-weight="700">Master Repo — live catalog health</text>
<text x="24" y="56" fill="#8b949e" font-family="Segoe UI,Arial" font-size="12">Updated {now}</text>
<text x="24" y="87" fill="#3fb950" font-family="Segoe UI,Arial" font-size="16">● Healthy {healthy}</text>
<text x="205" y="87" fill="#d29922" font-family="Segoe UI,Arial" font-size="16">● Review/Stale {review}</text>
<text x="430" y="87" fill="#f85149" font-family="Segoe UI,Arial" font-size="16">● Remove {remove}</text>
<text x="610" y="87" fill="#8b949e" font-family="Segoe UI,Arial" font-size="14">Total {total}</text>
</svg>'''
    SVG.write_text(svg, encoding="utf-8")


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--stale-days",type=int,default=365)
    ap.add_argument("--deep",action="store_true")
    ap.add_argument("--batch-size",type=int,default=12)
    ap.add_argument("--batch-index",type=int,default=0)
    ap.add_argument("--apply-removals",action="store_true")
    args=ap.parse_args()

    all_repos=repos(); previous={}
    if STATE.exists():
        try: previous={x["repo"]:x for x in json.loads(STATE.read_text(encoding="utf-8")).get("repos",[])}
        except Exception: previous={}
    results=[]; auto_removed=[]
    for i, repo in enumerate(all_repos):
        try: meta=github_json(repo)
        except Exception as e:
            old=previous.get(repo,{})
            r=Result(repo=repo,status=old.get("status","REVIEW"),pushed_at=old.get("pushed_at"),age_days=old.get("age_days"),note=f"metadata error: {e}")
            results.append(r); continue
        r=status_for(meta,args.stale_days); r.repo=repo
        should_deep=args.deep and (i % max(1, (len(all_repos)+args.batch_size-1)//args.batch_size)) == args.batch_index
        if should_deep and r.status != "REMOVE":
            r.findings,r.critical=deep_scan(repo); r.deep_scanned=True
            if r.critical: r.status="REMOVE"
            elif any(x.startswith("HIGH") for x in r.findings): r.status="REVIEW"
            r.note=f"{len(r.findings)} deep-scan finding(s)" if r.findings else "deep scan clean"
        if args.apply_removals and r.status == "REMOVE" and (r.archived or r.disabled or meta is None or r.critical):
            remove_from_repo_lists(repo); auto_removed.append((repo,r.note or "remove policy"))
        results.append(r)
    if auto_removed:
        with REMOVALS.open("a",encoding="utf-8") as f:
            if REMOVALS.stat().st_size == 0: f.write("# Automatic Catalog Removals\n\n")
            stamp=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            for repo,why in auto_removed: f.write(f"- {stamp} — `{repo}` — {why}\n")
        removed={x[0] for x in auto_removed}; results=[r for r in results if r.repo not in removed]
    render(results)
    print(json.dumps({"repos":len(results),"auto_removed":[x[0] for x in auto_removed]},indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

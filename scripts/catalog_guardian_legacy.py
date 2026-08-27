#!/usr/bin/env python3
"""Master Repo catalog health, security, and lifecycle guardian.

Freshness defaults:
  <=120 days since push: HEALTHY
  121-269 days: STALE
  270-365 days: REVIEW for replacement/managed adoption
  >365 days: REMOVE candidate for active/runtime catalog

Archived repositories are not automatically dead. Recently archived projects and
owner-approved reference artifacts are reviewed before removal.

Security checks are heuristic. HIGH findings require review. CRITICAL findings are
removal candidates. Deep scans run only when --deep is supplied or a repo is named
with --force-repo. This keeps frequent metadata audits cheap while preserving the
last deep-scan state in docs/catalog-status.json.
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
OVERRIDES = ROOT / "repo-lists" / "lifecycle-overrides.json"
STATE = ROOT / "docs" / "catalog-status.json"
REPORT = ROOT / "docs" / "CATALOG-STATUS.md"
SVG = ROOT / "docs" / "catalog-status.svg"
REMOVALS = ROOT / "docs" / "AUTO-REMOVALS.md"
MANAGED = ROOT / "managed-repos" / "candidates"

INVISIBLE = set("\u200b\u200c\u200d\u2060\ufeff\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")
TEXT_EXT = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".cs", ".cpp", ".c", ".h", ".hpp",
    ".java", ".go", ".rs", ".rb", ".php", ".sh", ".ps1", ".bat", ".cmd",
    ".sql", ".json", ".yaml", ".yml", ".toml", ".xml", ".md", ".txt",
    ".env", ".ini", ".cfg", ".conf", ".html", ".css", ".vue", ".svelte",
}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "target", "vendor"}
ADOPTABLE_LICENSES = {
    "mit", "mit-0", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "isc",
    "mpl-2.0", "epl-2.0", "unlicense", "cc0-1.0",
}
SUSPICIOUS = [
    ("download-to-shell", re.compile(r"(?:curl|wget)[^\n|;]*(?:\||;|&&)\s*(?:sh|bash|zsh)\b", re.I)),
    ("powershell-encoded", re.compile(r"powershell(?:\.exe)?[^\n]{0,120}-(?:enc|encodedcommand)\b", re.I)),
    ("base64-exec", re.compile(r"(?:base64\s+-d|frombase64string|b64decode)[^\n]{0,180}(?:exec|eval|invoke-expression|iex|system\()", re.I)),
    ("credential-exfil", re.compile(r"(?:AWS_SECRET_ACCESS_KEY|GITHUB_TOKEN|ANTHROPIC_API_KEY|OPENAI_API_KEY)[^\n]{0,160}(?:requests\.|fetch\(|curl|wget|http)", re.I)),
]
PROMPT_INJECTION = [
    re.compile(r"\bignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|prompts?)\b", re.I),
    re.compile(r"\b(?:reveal|print|exfiltrate|send)\b[^\n]{0,120}\b(?:system prompt|developer message|api key|secret|credential)\b", re.I),
    re.compile(r"\b(?:disable|bypass)\b[^\n]{0,100}\b(?:safety|security|guardrail|approval)\b", re.I),
]
SQL = [
    re.compile(r"(?:execute|query|raw|exec)\s*\(\s*f?[\"'][^\n]*\b(?:select|insert|update|delete)\b[^\n]*(?:\{|\+|%s|format\()", re.I),
    re.compile(r"(?:SELECT|INSERT|UPDATE|DELETE)[^\n]{0,200}(?:\+\s*\w+|\$\{\w+\}|\{\w+\})", re.I),
]
SECRETS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]


@dataclass
class Result:
    repo: str
    status: str = "UNKNOWN"
    pushed_at: str | None = None
    updated_at: str | None = None
    age_days: int | None = None
    archived: bool = False
    archived_first_seen: str | None = None
    archived_days: int | None = None
    disabled: bool = False
    license: str | None = None
    override: str | None = None
    deep_scanned: bool = False
    critical: bool = False
    findings: list[str] | None = None
    adoption_candidate: bool = False
    note: str = ""


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def parse_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_repos() -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in CATALOG.read_text(encoding="utf-8").splitlines():
        repo = raw.split("#", 1)[0].strip()
        if repo.count("/") == 1 and repo not in seen:
            seen.add(repo)
            out.append(repo)
    return out


def load_overrides() -> dict:
    if not OVERRIDES.exists():
        return {}
    try:
        return json.loads(OVERRIDES.read_text(encoding="utf-8"))
    except Exception:
        return {}


def metadata(repo: str) -> dict | None:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "master-repo-guardian"},
    )
    if os.getenv("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
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
    out: list[str] = []
    controls = sorted({f"U+{ord(c):04X}" for c in text if c in INVISIBLE})
    if controls:
        out.append(f"HIGH invisible/bidi controls {','.join(controls)} in {path}")
    for name, pattern in SUSPICIOUS:
        if pattern.search(text):
            out.append(f"{'CRITICAL' if name == 'credential-exfil' else 'HIGH'} {name} pattern in {path}")
    if any(pattern.search(text) for pattern in PROMPT_INJECTION):
        out.append(f"HIGH possible prompt/instruction injection text in {path}")
    if any(pattern.search(text) for pattern in SQL):
        out.append(f"HIGH possible SQL injection construction in {path}")
    if any(pattern.search(text) for pattern in SECRETS):
        out.append(f"CRITICAL secret/private-key material in {path}")
    return out


# Scanners disagree about what a non-zero exit means. Only these codes mean
# "the tool ran fine and had something to report"; anything else is the scanner
# itself failing, which must never be reported as a security finding.
FINDING_EXIT_CODES = {
    "gitleaks": {1},
    "trivy": {1},
    "osv-scanner": {1},
    "semgrep-sql-injection": {1},
    "semgrep-command-injection": {1},
    "clamav": {1},
    "snyk": {1},
}

# Anything shaped like real credential material is masked before it can reach a
# log, JSON file, SVG, issue, PR body, or the Pages artifact.
REDACTIONS = [
    re.compile(r"-----BEGIN[^-]{0,60}PRIVATE KEY-----.*?-----END[^-]{0,60}PRIVATE KEY-----", re.S | re.I),
    re.compile(r"\b(?:gh[pousr]|github_pat)_[A-Za-z0-9_]{16,}"),
    re.compile(r"\bsk-(?:ant-|proj-|live-)?[A-Za-z0-9_-]{16,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    re.compile(r"(?i)\b(?:api[_-]?key|secret|token|password|passwd|pwd|authorization|bearer)\b\s*[:=]\s*\S+"),
    re.compile(r"\b[A-Za-z0-9+/]{40,}={0,2}\b"),
    re.compile(r"\b[0-9a-f]{40,}\b", re.I),
]


def redact(text: str, limit: int = 400) -> str:
    """Mask credential-shaped substrings, then truncate. Never returns raw tool output."""
    for pattern in REDACTIONS:
        text = pattern.sub("[REDACTED]", text)
    text = " ".join(text.split())
    return text[:limit]


def run_external(cmd: list[str], cwd: pathlib.Path, label: str) -> list[str]:
    """Run a scanner and classify the result as clean, a finding, or a scanner error.

    A scanner error is reported as SCANNER-ERROR and asks for a rescan. It is never
    reported as a malware/secret finding, because an unusable ClamAV database or a
    missing signature feed says nothing at all about the repository being scanned.
    """
    if shutil.which(cmd[0]) is None:
        return [f"SCANNER-ERROR {label} not installed; this scanner did not run"]
    try:
        proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=900)
    except Exception as exc:
        return [f"SCANNER-ERROR {label} could not run: {redact(str(exc), 200)}"]
    if proc.returncode == 0:
        return []
    sample = redact(proc.stdout + " " + proc.stderr)
    if proc.returncode in FINDING_EXIT_CODES.get(label, {1}):
        return [f"HIGH {label} reported findings: {sample}"]
    return [
        f"SCANNER-ERROR {label} exited {proc.returncode} without completing; "
        f"rescan required, this is not a finding about the repository: {sample}"
    ]


def clamav_database_ready() -> bool:
    """ClamAV without a signature database exits non-zero on every scan."""
    for directory in ("/var/lib/clamav", "/usr/local/share/clamav", "/opt/homebrew/var/lib/clamav"):
        base = pathlib.Path(directory)
        if base.is_dir() and any(base.glob("*.c[vl]d")):
            return True
    return False


def run_gitleaks(clone: pathlib.Path) -> list[str]:
    """Gitleaks with --redact, reporting rule/file/line only — never the secret value."""
    if shutil.which("gitleaks") is None:
        return ["SCANNER-ERROR gitleaks not installed; secret scanning did not run"]
    report = clone.parent / "gitleaks-report.json"
    cmd = [
        "gitleaks", "detect", "--no-banner", "--redact",
        "--report-format", "json", "--report-path", str(report),
        "--source", ".",
    ]
    try:
        proc = subprocess.run(cmd, cwd=clone, text=True, capture_output=True, timeout=900)
    except Exception as exc:
        return [f"SCANNER-ERROR gitleaks could not run: {redact(str(exc), 200)}"]
    if proc.returncode not in (0, 1):
        return [
            f"SCANNER-ERROR gitleaks exited {proc.returncode} without completing; "
            f"rescan required, this is not a finding about the repository: "
            f"{redact(proc.stdout + ' ' + proc.stderr, 200)}"
        ]
    if proc.returncode == 0:
        return []
    try:
        entries = json.loads(report.read_text(encoding="utf-8")) or []
    except Exception:
        return ["CRITICAL gitleaks reported secret material; report unreadable, values withheld"]
    findings = []
    for entry in entries[:20]:
        rule = str(entry.get("RuleID") or entry.get("Description") or "unknown-rule")[:60]
        location = str(entry.get("File") or "unknown-file")[:160]
        line = entry.get("StartLine")
        where = f"{location}:{line}" if line else location
        findings.append(f"CRITICAL gitleaks secret candidate rule={rule} at {where} (value withheld)")
    if len(entries) > 20:
        findings.append(f"INFO gitleaks reported {len(entries) - 20} further secret candidates (values withheld)")
    return findings


def deep_scan(repo: str) -> tuple[list[str], bool]:
    """Return (findings, critical). Scanner failures never set critical."""
    findings: list[str] = []
    with tempfile.TemporaryDirectory(prefix="master-repo-guardian-") as tmp:
        clone = pathlib.Path(tmp) / "repo"
        proc = subprocess.run(
            ["git", "clone", "--depth", "1", "--filter=blob:none", f"https://github.com/{repo}.git", str(clone)],
            text=True,
            capture_output=True,
            timeout=300,
        )
        if proc.returncode != 0:
            # A failed clone is an infrastructure problem, not evidence about the repo.
            return [f"SCANNER-ERROR clone failed, nothing was scanned: {redact(proc.stderr, 200)}"], False
        for path in iter_files(clone):
            rel = path.relative_to(clone)
            try:
                head = path.read_bytes()[:4]
            except OSError:
                continue
            if head.startswith(b"MZ") or head.startswith(b"\x7fELF"):
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
        findings += run_gitleaks(clone)
        findings += run_external(
            ["trivy", "fs", "--scanners", "vuln,secret,misconfig", "--severity", "HIGH,CRITICAL", "--exit-code", "1", "."],
            clone,
            "trivy",
        )
        findings += run_external(["osv-scanner", "scan", "source", "-r", "."], clone, "osv-scanner")
        findings += run_external(["semgrep", "--config", "p/sql-injection", "--error", "."], clone, "semgrep-sql-injection")
        findings += run_external(["semgrep", "--config", "p/command-injection", "--error", "."], clone, "semgrep-command-injection")
        if shutil.which("clamscan") is None:
            findings.append("SCANNER-ERROR clamav not installed; malware scanning did not run")
        elif not clamav_database_ready():
            findings.append(
                "SCANNER-ERROR clamav signature database is missing or not initialised (run freshclam); "
                "malware scanning was skipped and no malware conclusion can be drawn"
            )
        else:
            findings += run_external(["clamscan", "-r", "--infected", "--no-summary", "."], clone, "clamav")
        if shutil.which("snyk") and os.getenv("SNYK_TOKEN"):
            findings += run_external(["snyk", "test", "--all-projects", "--severity-threshold=high"], clone, "snyk")
    # Redact defensively: nothing leaves this function without passing the masker.
    findings = [redact(item, 500) for item in findings]
    critical = any(item.startswith("CRITICAL") for item in findings)
    return findings, critical


def has_scanner_error(findings: Iterable[str]) -> bool:
    return any(str(item).startswith("SCANNER-ERROR") for item in findings)


def classify(repo: str, meta: dict | None, old: dict, override: dict, stale: int, adopt: int, remove: int, archive_grace: int) -> Result:
    if meta is None:
        return Result(repo=repo, status="REMOVE", critical=True, note="repository deleted or inaccessible")
    pushed = meta.get("pushed_at")
    pushed_dt = parse_time(pushed)
    age = (now() - pushed_dt).days if pushed_dt else None
    archived = bool(meta.get("archived"))
    disabled = bool(meta.get("disabled"))
    first = old.get("archived_first_seen")
    archived_days = None
    if archived:
        if not first:
            first = now().date().isoformat()
        first_dt = parse_time(first + "T00:00:00+00:00")
        archived_days = (now() - first_dt).days if first_dt else 0
    else:
        first = None
    license_key = ((meta.get("license") or {}).get("key") or "").lower() or None
    mode = (override or {}).get("mode")
    note = (override or {}).get("note", "")

    if disabled:
        status, note = "REMOVE", "repository disabled"
    elif mode in {"keep", "reference"}:
        # An owner override is a decision that age is the wrong signal for this repo
        # (finished research artifact, pinned course material, stable vendor SDK).
        # Honour it: hold the row HEALTHY so the weekly audit converges instead of
        # re-reporting the same accepted exception forever. Archival is a genuine
        # state change the owner has not yet ruled on, so it still escalates.
        status = "REVIEW" if archived else "HEALTHY"
        note = note or f"owner lifecycle override: {mode}"
    elif mode == "archived-active":
        # Deliberately stays REVIEW. This mode tracks a sunset in progress and is
        # meant to keep nagging until the owner removes or replaces the entry.
        status = "REVIEW"
        note = note or "owner lifecycle override: archived-active"
    elif archived and age is not None and age <= stale:
        status, note = "REVIEW", f"archived but recently pushed {age}d ago; transition/release review required"
    elif archived and archived_days is not None and archived_days < archive_grace:
        status, note = "STALE", f"archived; {archived_days}d into {archive_grace}d observation grace"
    elif archived:
        status, note = "REMOVE", f"archived and outside {archive_grace}d observation grace"
    elif age is not None and age > remove:
        status, note = "REMOVE", f"no push for {age}d; active-catalog removal threshold is {remove}d"
    elif age is not None and age > adopt:
        status, note = "REVIEW", f"no push for {age}d; replacement/managed-adoption review starts at {adopt}d"
    elif age is not None and age > stale:
        status, note = "STALE", f"no push for {age}d; stale warning starts at {stale}d"
    else:
        status = "HEALTHY"
    return Result(
        repo=repo,
        status=status,
        pushed_at=pushed,
        updated_at=meta.get("updated_at"),
        age_days=age,
        archived=archived,
        archived_first_seen=first,
        archived_days=archived_days,
        disabled=disabled,
        license=license_key,
        override=mode,
        note=note,
    )


def restore_scan_state(result: Result, old: dict) -> None:
    """Keep the last expensive scan state during cheap metadata refreshes."""
    result.deep_scanned = bool(old.get("deep_scanned"))
    result.findings = old.get("findings") or []
    result.critical = bool(old.get("critical"))
    result.adoption_candidate = bool(old.get("adoption_candidate"))
    if result.critical:
        result.status = "REMOVE"
        result.note = "previous CRITICAL security finding pending owner-approved rescan"
    elif any(str(item).startswith("HIGH") for item in result.findings) and result.status == "HEALTHY":
        result.status = "REVIEW"
        result.note = "previous HIGH security finding pending owner-approved rescan"
    elif has_scanner_error(result.findings):
        result.deep_scanned = False
        if result.status == "HEALTHY":
            result.status = "REVIEW"
        result.note = "previous security scan did not complete (scanner error); rescan required, not a finding"


def remove_from_lists(repo: str) -> None:
    for path in (ROOT / "repo-lists").glob("*.txt"):
        lines = path.read_text(encoding="utf-8").splitlines()
        kept = [line for line in lines if line.split("#", 1)[0].strip() != repo]
        if kept != lines:
            path.write_text("\n".join(kept).rstrip() + "\n", encoding="utf-8")


def managed_candidate(result: Result) -> None:
    if result.critical or not result.deep_scanned or result.license not in ADOPTABLE_LICENSES:
        return
    if any(x.startswith(("HIGH", "CRITICAL")) for x in (result.findings or [])):
        return
    if has_scanner_error(result.findings or []):
        return
    MANAGED.mkdir(parents=True, exist_ok=True)
    path = MANAGED / (result.repo.replace("/", "__") + ".md")
    if path.exists():
        result.adoption_candidate = True
        return
    path.write_text(
        f"""# Managed adoption candidate: {result.repo}\n\nStatus: **OWNER REVIEW REQUIRED**\n\nReason: {result.note}\n\nUpstream: `https://github.com/{result.repo}`\nLicense detected: `{result.license}`\nLast push: `{result.pushed_at}`\n\nThe deep scan found no HIGH/CRITICAL guardian pattern in the scanned revision. Do not copy or fork automatically. Charles must approve scope and licensing first. If approved, preserve license/NOTICE/attribution, copy only useful components, modernize dependencies/tests/CI/security, re-scan, and add the maintained Charlesganu2004 replacement to the catalog through an owner-approved PR.\n""",
        encoding="utf-8",
    )
    result.adoption_candidate = True


def render(results: list[Result], policy: dict) -> None:
    stamp = now().strftime("%Y-%m-%d %H:%M UTC")
    keys = ["HEALTHY", "STALE", "REVIEW", "REMOVE", "UNKNOWN"]
    counts = {key: sum(r.status == key for r in results) for key in keys}
    STATE.write_text(
        json.dumps({"updated": stamp, "policy": policy, "counts": counts, "repos": [asdict(r) for r in results]}, indent=2) + "\n",
        encoding="utf-8",
    )
    rows = [
        "# Catalog Status",
        "",
        f"Last automated update: **{stamp}**",
        "",
        f"Policy: stale **{policy['stale_after_days']}d** · adoption/replacement review **{policy['adoption_review_days']}d** · active-catalog removal **{policy['remove_stale_after_days']}d** · archived observation grace **{policy['archive_grace_days']}d**.",
        "",
        f"🟢 Healthy **{counts['HEALTHY']}** · 🟡 Stale **{counts['STALE']}** · 🟠 Review **{counts['REVIEW']}** · 🔴 Remove **{counts['REMOVE']}** · ⚪ Unknown **{counts['UNKNOWN']}**",
        "",
        "| Repo | Status | Push age | Archived | License | Deep scan | Managed | Note |",
        "|---|---|---:|---:|---|---:|---:|---|",
    ]
    icon = {"HEALTHY": "🟢", "STALE": "🟡", "REVIEW": "🟠", "REMOVE": "🔴"}
    for result in sorted(results, key=lambda item: (item.status, item.repo)):
        note = (result.note or (result.findings[0] if result.findings else "")).replace("|", "/")
        rows.append(
            f"| `{result.repo}` | {icon.get(result.status, '⚪')} {result.status} | "
            f"{str(result.age_days) + 'd' if result.age_days is not None else '—'} | "
            f"{'yes' if result.archived else 'no'} | {result.license or '—'} | "
            f"{'yes' if result.deep_scanned else 'no'} | {'yes' if result.adoption_candidate else 'no'} | {note} |"
        )
    REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")
    SVG.write_text(
        f'''<svg xmlns="http://www.w3.org/2000/svg" width="850" height="120" role="img" aria-label="Master Repo live catalog health"><rect width="850" height="120" rx="10" fill="#0d1117"/><text x="24" y="30" fill="#f0f6fc" font-family="Segoe UI,Arial" font-size="17" font-weight="700">Master Repo — live catalog health &amp; security</text><text x="24" y="54" fill="#8b949e" font-family="Segoe UI,Arial" font-size="12">Updated {stamp} · stale {policy['stale_after_days']}d · review {policy['adoption_review_days']}d · remove {policy['remove_stale_after_days']}d</text><text x="24" y="88" fill="#3fb950" font-family="Segoe UI,Arial" font-size="16">● Healthy {counts['HEALTHY']}</text><text x="205" y="88" fill="#d29922" font-family="Segoe UI,Arial" font-size="16">● Stale {counts['STALE']}</text><text x="350" y="88" fill="#f0883e" font-family="Segoe UI,Arial" font-size="16">● Review {counts['REVIEW']}</text><text x="520" y="88" fill="#f85149" font-family="Segoe UI,Arial" font-size="16">● Remove {counts['REMOVE']}</text><text x="660" y="88" fill="#8b949e" font-family="Segoe UI,Arial" font-size="16">● Unknown {counts['UNKNOWN']}</text><text x="790" y="88" fill="#8b949e" font-family="Segoe UI,Arial" font-size="13">n={len(results)}</text></svg>''',
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stale-after-days", type=int, default=120)
    parser.add_argument("--adoption-review-days", type=int, default=270)
    parser.add_argument("--remove-stale-after-days", type=int, default=365)
    parser.add_argument("--archive-grace-days", type=int, default=30)
    parser.add_argument("--deep", action="store_true")
    parser.add_argument("--batch-size", type=int, default=12)
    parser.add_argument("--batch-index", type=int, default=0)
    parser.add_argument("--force-repo", action="append", default=[])
    parser.add_argument("--apply-removals", action="store_true")
    args = parser.parse_args()
    policy = {
        "stale_after_days": args.stale_after_days,
        "adoption_review_days": args.adoption_review_days,
        "remove_stale_after_days": args.remove_stale_after_days,
        "archive_grace_days": args.archive_grace_days,
    }
    repos = load_repos()
    overrides = load_overrides()
    previous: dict[str, dict] = {}
    if STATE.exists():
        try:
            previous = {item["repo"]: item for item in json.loads(STATE.read_text(encoding="utf-8")).get("repos", [])}
        except Exception:
            previous = {}

    groups = max(1, (len(repos) + args.batch_size - 1) // args.batch_size)
    forced = set(args.force_repo)
    results: list[Result] = []
    removed: list[Result] = []

    for idx, repo in enumerate(repos):
        old = previous.get(repo, {})
        try:
            meta = metadata(repo)
        except Exception as exc:
            # A metadata fetch failure is an INFRASTRUCTURE problem, not a verdict
            # about the repository. Defaulting a never-seen repo to REVIEW meant one
            # DNS blip could silently label 21 healthy repos as needing a lifecycle
            # decision. Keep the last known status when there is one; otherwise say
            # UNKNOWN, which reads as "unverified, retry" rather than as a judgement.
            result = Result(
                repo=repo,
                status=old.get("status") or "UNKNOWN",
                pushed_at=old.get("pushed_at"),
                age_days=old.get("age_days"),
                archived=bool(old.get("archived")),
                deep_scanned=bool(old.get("deep_scanned")),
                critical=bool(old.get("critical")),
                findings=old.get("findings") or [],
                adoption_candidate=bool(old.get("adoption_candidate")),
                note=f"metadata error: {exc}",
            )
            results.append(result)
            continue

        result = classify(
            repo,
            meta,
            old,
            overrides.get(repo, {}),
            args.stale_after_days,
            args.adoption_review_days,
            args.remove_stale_after_days,
            args.archive_grace_days,
        )
        rotating = args.deep and idx % groups == args.batch_index % groups
        should_scan = repo in forced or (args.deep and (rotating or result.status in {"REVIEW", "REMOVE"}))

        if should_scan and meta is not None and not result.disabled:
            result.findings, result.critical = deep_scan(repo)
            result.deep_scanned = True
            if result.critical:
                result.status, result.note = "REMOVE", "CRITICAL security finding"
            elif any(item.startswith("HIGH") for item in result.findings):
                result.status, result.note = "REVIEW", "HIGH security finding requires owner review"
            elif has_scanner_error(result.findings):
                # The scanner did not complete. That is a tooling problem, so ask for a
                # rescan instead of implying the repository contains malware or secrets.
                result.deep_scanned = False
                if result.status == "HEALTHY":
                    result.status = "REVIEW"
                result.note = "security scan did not complete (scanner error); rescan required, not a finding"
        else:
            restore_scan_state(result, old)

        if should_scan and result.status in {"REVIEW", "REMOVE"} and result.age_days is not None and result.age_days >= args.adoption_review_days:
            managed_candidate(result)

        removal_ready = result.critical or result.disabled or meta is None or result.deep_scanned
        if args.apply_removals and result.status == "REMOVE" and removal_ready:
            remove_from_lists(repo)
            removed.append(result)
        results.append(result)

    render(results, policy)
    if removed:
        existing = REMOVALS.read_text(encoding="utf-8") if REMOVALS.exists() else "# Automatic Catalog Removal Proposals\n\n"
        lines = [existing.rstrip(), "", f"## {now().strftime('%Y-%m-%d %H:%M UTC')}", ""]
        lines += [
            f"- `{result.repo}` — {result.note}{' — managed adoption candidate generated' if result.adoption_candidate else ''}"
            for result in removed
        ]
        REMOVALS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

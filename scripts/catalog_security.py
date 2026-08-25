#!/usr/bin/env python3
"""Fail-closed security helpers for Master Repo Catalog Guardian.

This module is intentionally small and testable.  It is imported by
``scripts/catalog_guardian.py`` and patches the legacy lifecycle engine so that
scanner failures can never masquerade as findings and raw scanner output can
never be persisted in catalog state, issues, PR bodies, or Pages artifacts.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
from typing import Iterable

INVISIBLE = set("\u200b\u200c\u200d\u2060\ufeff\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")

_SECRET_NAMES = (
    r"(?:AWS_SECRET_ACCESS_KEY|AWS_SESSION_TOKEN|GITHUB_TOKEN|GH_TOKEN|"
    r"ANTHROPIC_API_KEY|OPENAI_API_KEY|GOOGLE_API_KEY|GEMINI_API_KEY|"
    r"STRIPE_SECRET_KEY|NPM_TOKEN|TWILIO_AUTH_TOKEN|SENDGRID_API_KEY|"
    r"MAILGUN_API_KEY)"
)
_NETWORK_SINKS = (
    r"(?:requests\.(?:get|post|put|patch|delete)|httpx\.(?:get|post|put|patch|delete)|"
    r"urllib\.request|fetch\s*\(|curl\b|wget\b|https?://)"
)

SUSPICIOUS = [
    ("download-to-shell", re.compile(r"(?:curl|wget)[^\n|;]*(?:\||;|&&)\s*(?:sh|bash|zsh)\b", re.I)),
    ("powershell-encoded", re.compile(r"powershell(?:\.exe)?[^\n]{0,120}-(?:enc|encodedcommand)\b", re.I)),
    ("base64-exec", re.compile(r"(?:base64\s+-d|frombase64string|b64decode)[^\n]{0,180}(?:exec|eval|invoke-expression|iex|system\()", re.I)),
    (
        "credential-exfil",
        re.compile(
            rf"(?:{_SECRET_NAMES}[^\n]{{0,220}}{_NETWORK_SINKS}|"
            rf"{_NETWORK_SINKS}[^\n]{{0,220}}{_SECRET_NAMES})",
            re.I,
        ),
    ),
]

PROMPT_INJECTION = [
    re.compile(r"\bignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|prompts?)\b", re.I),
    re.compile(r"\b(?:reveal|print|exfiltrate|send)\b[^\n]{0,120}\b(?:system prompt|developer message|api key|secret|credential)\b", re.I),
    re.compile(r"\b(?:disable|bypass)\b[^\n]{0,100}\b(?:safety|security|guardrail|approval)\b", re.I),
]

SQL = [
    re.compile(r"(?:execute|query|raw|exec)\s*\(\s*f?[\"'][^\n]*\b(?:select|insert|update|delete)\b[^\n]*(?:\{|\+|%s|format\()", re.I),
    # Require real SQL *structure*, not just a keyword. The previous form matched any
    # line containing "select"/"update"/"deleted" followed by a "+ word" or "{word}",
    # which fires on ordinary English prose -- "connect/select private repo | connector
    # + supported tools", "model selection built in {x}". Constant false HIGH findings
    # teach the owner to ignore the scanner, so precision here is a safety property,
    # not a style preference.
    re.compile(
        r"\b(?:SELECT\b[^\n]{0,200}?\bFROM\b"
        r"|INSERT\s+INTO\b"
        r"|UPDATE\b[^\n]{0,200}?\bSET\b"
        r"|DELETE\s+FROM\b)"
        r"[^\n]{0,200}(?:\+\s*\w+|\$\{\w+\}|\{\w+\}|%s|\bformat\s*\()",
        re.I,
    ),
]

COMMAND = [
    re.compile(
        r"(?:subprocess\.(?:run|Popen|call|check_output)|os\.system|child_process\.(?:exec|execSync)|Runtime\.getRuntime\(\)\.exec)"
        r"[^\n]{0,180}(?:shell\s*=\s*True|request\.|req\.|params|query|user[_-]?input)",
        re.I,
    ),
    re.compile(r"(?:eval|exec|Invoke-Expression|\biex\b)\s*\([^\n]{0,160}(?:request\.|req\.|params|query|user[_-]?input)", re.I),
]

SECRETS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:gh[pousr]|github_pat)_[A-Za-z0-9_]{16,}\b"),
    re.compile(r"\bsk-(?:ant-|proj-|live-)?[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    re.compile(r"\b(?:sk|rk)_live_[0-9A-Za-z]{16,}\b"),
    re.compile(r"\bnpm_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bSG\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bkey-[0-9A-Za-z]{24,}\b"),
]

FINDING_EXIT_CODES = {
    "trivy": {1},
    "osv-scanner": {1},
    "semgrep-sql-injection": {1},
    "semgrep-command-injection": {1},
    "clamav": {1},
    "snyk": {1},
}

REDACTIONS = [
    re.compile(r"-----BEGIN[^-]{0,60}PRIVATE KEY-----.*?-----END[^-]{0,60}PRIVATE KEY-----", re.S | re.I),
    re.compile(r"\b(?:gh[pousr]|github_pat)_[A-Za-z0-9_]{16,}\b"),
    re.compile(r"\bsk-(?:ant-|proj-|live-)?[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    re.compile(r"\b(?:sk|rk)_live_[0-9A-Za-z]{16,}\b"),
    re.compile(r"\bnpm_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bSG\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bkey-[0-9A-Za-z]{24,}\b"),
    re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\bey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"(?i)\b(?:TWILIO_AUTH_TOKEN|SENDGRID_API_KEY|MAILGUN_API_KEY|AWS_SECRET_ACCESS_KEY|AWS_SESSION_TOKEN)\b\s*[:=]\s*[\"']?[^\s\"']+"),
    re.compile(r"(?i)\b(?:api[_-]?key|secret|token|password|passwd|pwd|authorization|bearer)\b\s*[:=]\s*[\"']?[^\s\"']+"),
    re.compile(r"(?i)\bhttps?://[^/\s:@]+:[^@\s/]+@"),
    re.compile(r"\b[A-Za-z0-9+/]{40,}={0,2}\b"),
    re.compile(r"\b[0-9a-f]{40,}\b", re.I),
]


def redact(text: str, limit: int = 400) -> str:
    """Best-effort masking for exception/diagnostic strings.

    Raw scanner stdout/stderr is never persisted at all; this masker is only
    defense-in-depth for short exception messages and built-in diagnostics.
    """
    for pattern in REDACTIONS:
        text = pattern.sub("[REDACTED]", text)
    text = " ".join(text.split())
    return text[:limit]


def scan_text(path: pathlib.Path, text: str) -> list[str]:
    """Heuristic source scan that reports category + path, never matched values."""
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
    if any(pattern.search(text) for pattern in COMMAND):
        out.append(f"HIGH possible command injection construction in {path}")
    if any(pattern.search(text) for pattern in SECRETS):
        out.append(f"CRITICAL secret/private-key material in {path}")
    return out


def run_external(cmd: list[str], cwd: pathlib.Path, label: str) -> list[str]:
    """Run a scanner without ever persisting its raw output."""
    if shutil.which(cmd[0]) is None:
        return [f"SCANNER-ERROR {label} not installed; this scanner did not run"]
    try:
        proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=900)
    except Exception as exc:
        return [f"SCANNER-ERROR {label} could not run: {redact(str(exc), 200)}"]
    if proc.returncode == 0:
        return []
    finding_codes = FINDING_EXIT_CODES.get(label)
    if finding_codes is None:
        return [
            f"SCANNER-ERROR {label} exited {proc.returncode}; no explicit exit-code policy exists, "
            "so the result is not classified as a finding"
        ]
    if proc.returncode in finding_codes:
        return [
            f"HIGH {label} reported findings (scanner details withheld from persisted output; "
            "rerun the scanner locally for full details)"
        ]
    return [
        f"SCANNER-ERROR {label} exited {proc.returncode} without completing; "
        "scanner output withheld and rescan required"
    ]


def clamav_database_ready() -> bool:
    for directory in ("/var/lib/clamav", "/usr/local/share/clamav", "/opt/homebrew/var/lib/clamav"):
        base = pathlib.Path(directory)
        if base.is_dir() and any(base.glob("*.c[vl]d")):
            return True
    return False


def run_gitleaks(clone: pathlib.Path) -> list[str]:
    """Run Gitleaks with --redact and persist metadata only."""
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
    if proc.returncode == 0:
        return []
    if proc.returncode != 1:
        return [
            f"SCANNER-ERROR gitleaks exited {proc.returncode} without completing; "
            "scanner output withheld and rescan required"
        ]
    try:
        entries = json.loads(report.read_text(encoding="utf-8")) or []
    except Exception:
        return [
            "SCANNER-ERROR gitleaks indicated possible findings but its redacted JSON report "
            "could not be read; values withheld and rescan required"
        ]
    if not isinstance(entries, list) or not entries:
        return [
            "SCANNER-ERROR gitleaks exited with findings status but produced no readable "
            "redacted findings; rescan required"
        ]
    findings: list[str] = []
    for entry in entries[:20]:
        if not isinstance(entry, dict):
            continue
        rule = str(entry.get("RuleID") or entry.get("Description") or "unknown-rule")[:60]
        location = str(entry.get("File") or "unknown-file")[:160]
        line = entry.get("StartLine")
        where = f"{location}:{line}" if line else location
        findings.append(f"CRITICAL gitleaks secret candidate rule={rule} at {where} (value withheld)")
    if not findings:
        return [
            "SCANNER-ERROR gitleaks report contained no safely usable finding metadata; "
            "values withheld and rescan required"
        ]
    if len(entries) > 20:
        findings.append(f"INFO gitleaks reported {len(entries) - 20} additional secret candidates (values withheld)")
    return findings


def has_scanner_error(findings: Iterable[str]) -> bool:
    return any(str(item).startswith("SCANNER-ERROR") for item in findings)

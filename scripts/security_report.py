#!/usr/bin/env python3
"""Report deep-scan security findings and scan coverage into a GitHub issue.

Context for why this file exists at all: before 2026-08-25 the catalog had never
been deep-scanned. Metadata auditing ran weekly; the scanner install step was gated
behind "were repos added this push", and `--deep` only ran after a manual owner
approval that had never been given. The result was 0/252 coverage with nothing to
make that visible.

This script is the visibility half of the fix. It writes a `[Security Scan]` issue
that always states coverage, so "we have not scanned anything" can never again look
the same as "we scanned and found nothing".

Reporting is read-only. Removing a repository from the catalog stays owner-gated.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE = ROOT / "docs" / "catalog-status.json"
TITLE = "[Security Scan] Deep scan coverage and findings"

# Severity prefixes the guardian emits, most serious first.
SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")


def load() -> dict:
    if not STATE.exists():
        print("no catalog state to report", file=sys.stderr)
        return {}
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except ValueError as exc:
        print(f"catalog state is not valid JSON: {exc}", file=sys.stderr)
        return {}


def severity_of(finding: str) -> str:
    for level in SEVERITIES:
        if finding.startswith(level):
            return level
    return "INFO"


def build_body(state: dict) -> tuple[str, int]:
    repos = state.get("repos") or []
    total = len(repos)
    scanned = [r for r in repos if r.get("deep_scanned")]
    errored = [r for r in repos
               if any("SCANNER-ERROR" in str(f) for f in (r.get("findings") or []))]
    with_findings = [r for r in repos if r.get("findings") and not
                     all("SCANNER-ERROR" in str(f) for f in r["findings"])]

    counts = {level: 0 for level in SEVERITIES}
    for repo in with_findings:
        for finding in repo.get("findings") or []:
            level = severity_of(str(finding))
            if level in counts:
                counts[level] += 1

    pct = (100 * len(scanned) // total) if total else 0
    lines = [
        "# Deep security scan",
        "",
        f"Coverage: **{len(scanned)} / {total}** repositories ever deep-scanned "
        f"(**{pct}%**). Updated: {state.get('updated', 'unknown')}",
        "",
        "Scanned for: malware (ClamAV), secrets (Gitleaks, redacted), known "
        "vulnerabilities (OSV), code patterns (Semgrep), plus the built-in checks for "
        "invisible/bidi characters, prompt injection, SQL injection and suspicious "
        "execution patterns.",
        "",
        f"Findings: **CRITICAL {counts['CRITICAL']}** · **HIGH {counts['HIGH']}** · "
        f"MEDIUM {counts['MEDIUM']} · LOW {counts['LOW']}",
        "",
    ]

    if errored:
        lines += [
            f"> **{len(errored)} repositor{'y' if len(errored) == 1 else 'ies'} reported "
            "`SCANNER-ERROR`.** That means a scanner failed to run, so those repos are "
            "**unverified** — it is not a claim that they are clean, and not a claim that "
            "anything was found. They stay in the rotation for a rescan.",
            "",
        ]

    if with_findings:
        lines += ["## Repositories with findings", "",
                  "| Repo | Severity | Finding |", "|---|---|---|"]
        for repo in sorted(with_findings, key=lambda r: r.get("repo", "")):
            for finding in repo.get("findings") or []:
                text = str(finding)
                if "SCANNER-ERROR" in text:
                    continue
                safe = text.replace("|", "/").replace("\n", " ")[:220]
                lines.append(f"| `{repo.get('repo')}` | {severity_of(text)} | {safe} |")
        lines += ["", "Secret **values** are never printed: Gitleaks runs with `--redact` "
                       "and only rule, file and line are reported.", ""]
    else:
        lines += ["## Findings", "",
                  "No security findings in the scanned slice.", ""]

    if total and len(scanned) < total:
        remaining = total - len(scanned)
        weeks = max(1, -(-remaining // 19))  # ~19 repos per weekly rotation
        lines += [
            "## Remaining coverage", "",
            f"{remaining} repositories have not been deep-scanned yet. At roughly 19 per "
            f"weekly rotation that is about **{weeks} more week(s)** to first full coverage.",
            "",
            "Scan the whole catalog sooner by dispatching the workflow repeatedly, or "
            "raise `--batch-size` in `.github/workflows/catalog-guardian.yml`.",
            "",
        ]

    lines += [
        "---",
        "",
        "This scan is **read-only** and runs without an approval gate, because reporting "
        "a risk should never wait on a human. Anything that *changes* the catalog "
        "(`--apply-removals`) still requires `APPROVE CATALOG MAINTENANCE`.",
    ]
    return "\n".join(lines), counts["CRITICAL"] + counts["HIGH"]


def gh(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], text=True, capture_output=True)


def main() -> int:
    state = load()
    if not state:
        return 0
    body, urgent = build_body(state)

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(body)

    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo or not os.environ.get("GH_TOKEN"):
        print(body)
        return 0

    path = pathlib.Path("/tmp/security-scan.md")
    path.write_text(body, encoding="utf-8")

    found = gh("issue", "list", "--repo", repo, "--state", "open",
               "--search", "in:title [Security Scan]", "--json", "number,title",
               "--jq", '[.[] | select(.title | startswith("[Security Scan]"))][0].number // empty')
    number = (found.stdout or "").strip()

    if number:
        result = gh("issue", "edit", number, "--repo", repo,
                    "--title", TITLE, "--body-file", str(path))
    else:
        result = gh("issue", "create", "--repo", repo, "--title", TITLE,
                    "--body-file", str(path), "--assignee", "Charlesganu2004")
    if result.returncode != 0:
        print(f"::warning::could not publish the security issue: {result.stderr[:400]}")

    if urgent:
        print(f"::warning::{urgent} CRITICAL/HIGH security finding(s) need owner review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

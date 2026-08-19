#!/usr/bin/env python3
"""Guardrails for the two ways the guardian could lie or leak.

1. A secret value must never survive into anything the guardian emits.
2. A scanner that fails to run must never be reported as a malware/secret finding.

The fixtures below are assembled from fragments at runtime on purpose: this file must
not itself contain a literal credential-shaped string, or every future secret scan of
this repository would flag its own test suite.

Run: python tests/test_scanner_safety.py
"""
from __future__ import annotations

import pathlib
import subprocess
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import catalog_guardian as guardian  # noqa: E402

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS  " if ok else "FAIL  ") + name + (f"  -> {detail}" if not ok else ""))
    if not ok:
        FAILURES.append(name)


def synthetic() -> list[tuple[str, str, str]]:
    """(label, text a scanner might print, the value that must never survive)."""
    gh = "gh" + "p_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
    openai = "sk" + "-proj-" + "abcdefghijklmnop1234567890ABCDEFGH"
    aws_id = "AKIA" + "IOSFODNN7EXAMPLE"
    aws_body = "wJalrXUtnFEMI" + "/K7MDENG/" + "bPxRfiCYEXAMPLEKEY"
    slack = "xox" + "b-1234567890-" + "ABCDEFGHIJKLMNOP"
    jwt = "ey" + "JhbGciOiJIUzI1NiJ9" + "." + "ey" + "JzdWIiOiIxMjM0NTY3ODkwIn0" + "." + "dBjftJeZ4CVPmB92K27uhbUJU1p1rXwW1gFWFOEjXk"
    pem_body = "MIIEowIBAAKCAQEAsyntheticfixturenotarealkey"
    pem = ("-----BEGIN RSA " + "PRIVATE KEY-----" + chr(10) + pem_body
           + chr(10) + "-----END RSA " + "PRIVATE KEY-----")
    pw_body = "hunter2CorrectHorseBattery"
    long_hex = "0123456789abcdef" * 2 + "01234567"
    return [
        ("github pat", f"found {gh} in config.yml", gh),
        ("openai key", f"OPENAI key {openai} leaked", openai),
        ("aws access key", f"{aws_id} exposed", aws_id),
        ("aws secret", f"aws_secret_access_key = {aws_body}", aws_body),
        ("jwt", jwt, jwt.rsplit(".", 1)[-1]),
        ("slack token", slack, slack),
        ("pem block", pem, pem_body),
        ("password pair", "pass" + "word: " + chr(34) + pw_body + chr(34), pw_body),
        ("long hex", f"token {long_hex}", long_hex),
    ]


def test_redaction() -> None:
    for name, raw, secret in synthetic():
        out = guardian.redact(raw)
        check(f"redact: {name}", "[REDACTED]" in out and secret not in out, repr(out))


def fake_run(label: str, code: int, output: str) -> list[str]:
    real_run, real_which = subprocess.run, guardian.shutil.which
    subprocess.run = lambda cmd, **kw: types.SimpleNamespace(returncode=code, stdout=output, stderr="")
    guardian.shutil.which = lambda name: "/usr/bin/" + name
    try:
        return guardian.run_external(["tool"], ROOT, label)
    finally:
        subprocess.run, guardian.shutil.which = real_run, real_which


def test_scanner_error_separation() -> None:
    check("clamav exit 0 is clean", fake_run("clamav", 0, "") == [])

    found = fake_run("clamav", 1, "./sample: Win.Test.EICAR_HDB-1 FOUND")
    check("clamav exit 1 is a finding", bool(found) and found[0].startswith("HIGH"), str(found))

    for code, output in (
        (2, "LibClamAV Error: cl_load(): No supported database files found in /var/lib/clamav"),
        (127, "clamscan: command not found"),
    ):
        errored = fake_run("clamav", code, output)
        check(
            f"clamav exit {code} is a scanner error, not malware",
            bool(errored)
            and errored[0].startswith("SCANNER-ERROR")
            and not any(x.startswith(("HIGH", "CRITICAL")) for x in errored),
            str(errored),
        )

    trivy = fake_run("trivy", 2, "FATAL unable to initialize scanner: db error")
    check("trivy exit 2 is a scanner error", bool(trivy) and trivy[0].startswith("SCANNER-ERROR"), str(trivy))

    missing = fake_run("osv-scanner", 128, "panic: runtime error")
    check("unexpected exit code is a scanner error", bool(missing) and missing[0].startswith("SCANNER-ERROR"), str(missing))

    check("has_scanner_error detects errors", guardian.has_scanner_error(trivy))
    check("has_scanner_error ignores real findings", not guardian.has_scanner_error(["HIGH x", "INFO y"]))


def test_findings_are_redacted() -> None:
    token = "gh" + "p_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
    leaked = fake_run("gitleaks", 1, f"secret: {token}")
    check("scanner finding text is redacted", token not in leaked[0], str(leaked))


def test_gitleaks_is_invoked_safely() -> None:
    source = (ROOT / "scripts" / "catalog_guardian.py").read_text(encoding="utf-8")
    check("gitleaks runs with --redact", '"--redact"' in source)
    check("gitleaks reports from a JSON file, not stdout", "gitleaks-report.json" in source)
    check("deep_scan redacts on the way out", "redact(item, 500)" in source)


if __name__ == "__main__":
    test_redaction()
    test_scanner_error_separation()
    test_findings_are_redacted()
    test_gitleaks_is_invoked_safely()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed: {', '.join(FAILURES)}")
        raise SystemExit(1)
    print("all scanner-safety checks passed")

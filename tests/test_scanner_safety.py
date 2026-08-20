#!/usr/bin/env python3
"""Fail-closed tests for Catalog Guardian security helpers."""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import catalog_security as security  # noqa: E402


def synthetic_secrets() -> list[tuple[str, str]]:
    gh = "gh" + "p_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
    openai = "sk" + "-proj-" + "abcdefghijklmnop1234567890ABCDEFGH"
    aws_id = "AKIA" + "IOSFODNN7EXAMPLE"
    google = "AIza" + "A" * 35
    stripe = "sk" + "_live_" + "A" * 24
    npm = "npm" + "_" + "A" * 32
    sendgrid = "SG." + "A" * 22 + "." + "B" * 30
    mailgun = "key" + "-" + "A" * 32
    slack = "xox" + "b-1234567890-" + "ABCDEFGHIJKLMNOP"
    jwt = "ey" + "JhbGciOiJIUzI1NiJ9" + "." + "ey" + "JzdWIiOiIxMjM0NTY3ODkwIn0" + "." + "A" * 32
    twilio = "A" * 32
    basic = "https://user:" + "CorrectHorseBattery" + "@example.invalid/path"
    pem_body = "MIIEowIBAAKCAQEAsyntheticfixturenotarealkey"
    pem = "-----BEGIN RSA " + "PRIVATE KEY-----\n" + pem_body + "\n-----END RSA " + "PRIVATE KEY-----"
    return [
        ("github", gh),
        ("openai", openai),
        ("aws-id", aws_id),
        ("google", google),
        ("stripe", stripe),
        ("npm", npm),
        ("sendgrid", sendgrid),
        ("mailgun", mailgun),
        ("slack", slack),
        ("jwt", jwt),
        ("twilio-labeled", "TWILIO_AUTH_TOKEN=" + twilio),
        ("basic-auth", basic),
        ("pem", pem),
    ]


class RedactionTests(unittest.TestCase):
    def test_secret_shapes_are_masked(self) -> None:
        for label, value in synthetic_secrets():
            with self.subTest(label=label):
                out = security.redact("scanner output: " + value, limit=1000)
                self.assertIn("[REDACTED]", out)
                if label == "twilio-labeled":
                    self.assertNotIn(value.split("=", 1)[1], out)
                elif label == "basic-auth":
                    self.assertNotIn("CorrectHorseBattery", out)
                elif label == "pem":
                    self.assertNotIn("syntheticfixturenotarealkey", out)
                else:
                    self.assertNotIn(value, out)

    def test_external_scanner_output_is_never_persisted(self) -> None:
        secret = synthetic_secrets()[0][1]
        proc = types.SimpleNamespace(returncode=1, stdout=f"found {secret}", stderr="")
        with mock.patch.object(security.shutil, "which", return_value="/usr/bin/tool"), \
             mock.patch.object(security.subprocess, "run", return_value=proc):
            result = security.run_external(["tool"], ROOT, "trivy")
        self.assertEqual(1, len(result))
        self.assertTrue(result[0].startswith("HIGH trivy"))
        self.assertNotIn(secret, result[0])
        self.assertNotIn("found", result[0])


class ExitCodeTests(unittest.TestCase):
    def fake(self, label: str, code: int) -> list[str]:
        proc = types.SimpleNamespace(returncode=code, stdout="raw scanner detail", stderr="raw error")
        with mock.patch.object(security.shutil, "which", return_value="/usr/bin/tool"), \
             mock.patch.object(security.subprocess, "run", return_value=proc):
            return security.run_external(["tool"], ROOT, label)

    def test_clean_exit_is_clean(self) -> None:
        self.assertEqual([], self.fake("clamav", 0))

    def test_known_finding_exit_is_finding(self) -> None:
        result = self.fake("clamav", 1)
        self.assertTrue(result[0].startswith("HIGH"))

    def test_clamav_exit_two_is_scanner_error(self) -> None:
        result = self.fake("clamav", 2)
        self.assertTrue(result[0].startswith("SCANNER-ERROR"))

    def test_unknown_scanner_exit_one_is_not_assumed_finding(self) -> None:
        result = self.fake("brand-new-scanner", 1)
        self.assertTrue(result[0].startswith("SCANNER-ERROR"))
        self.assertFalse(any(x.startswith(("HIGH", "CRITICAL")) for x in result))

    def test_missing_tool_is_scanner_error(self) -> None:
        with mock.patch.object(security.shutil, "which", return_value=None):
            result = security.run_external(["missing"], ROOT, "missing")
        self.assertTrue(result[0].startswith("SCANNER-ERROR"))


class GitleaksTests(unittest.TestCase):
    def test_gitleaks_command_uses_redaction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clone = pathlib.Path(tmp) / "repo"
            clone.mkdir()
            report = pathlib.Path(tmp) / "gitleaks-report.json"
            report.write_text(json.dumps([{
                "RuleID": "generic-api-key",
                "File": "settings.py",
                "StartLine": 7,
                "Secret": "must-never-appear",
            }]), encoding="utf-8")
            proc = types.SimpleNamespace(returncode=1, stdout="raw secret here", stderr="")
            with mock.patch.object(security.shutil, "which", return_value="/usr/bin/gitleaks"), \
                 mock.patch.object(security.subprocess, "run", return_value=proc) as run:
                result = security.run_gitleaks(clone)
            cmd = run.call_args.args[0]
            self.assertIn("--redact", cmd)
            self.assertIn("--report-format", cmd)
            self.assertNotIn("must-never-appear", " ".join(result))
            self.assertIn("settings.py:7", result[0])

    def test_unreadable_gitleaks_report_is_scanner_error_not_critical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clone = pathlib.Path(tmp) / "repo"
            clone.mkdir()
            proc = types.SimpleNamespace(returncode=1, stdout="possible secret", stderr="")
            with mock.patch.object(security.shutil, "which", return_value="/usr/bin/gitleaks"), \
                 mock.patch.object(security.subprocess, "run", return_value=proc):
                result = security.run_gitleaks(clone)
            self.assertTrue(result[0].startswith("SCANNER-ERROR"))
            self.assertFalse(any(x.startswith("CRITICAL") for x in result))


class HeuristicTests(unittest.TestCase):
    def test_credential_exfil_detects_secret_before_sink(self) -> None:
        findings = security.scan_text(
            pathlib.Path("x.py"),
            "token = os.environ['GITHUB_TOKEN']; requests.post(url, data=token)",
        )
        self.assertTrue(any("credential-exfil" in x for x in findings))

    def test_credential_exfil_detects_sink_before_secret(self) -> None:
        findings = security.scan_text(
            pathlib.Path("x.py"),
            "requests.post(url, data=os.environ['GITHUB_TOKEN'])",
        )
        self.assertTrue(any("credential-exfil" in x for x in findings))

    def test_command_injection_pattern(self) -> None:
        findings = security.scan_text(
            pathlib.Path("x.py"),
            "subprocess.run(request.args['cmd'], shell=True)",
        )
        self.assertTrue(any("command injection" in x for x in findings))


class WrapperIntegrationTests(unittest.TestCase):
    def test_catalog_guardian_entrypoint_uses_hardened_helpers(self) -> None:
        import catalog_guardian as guardian
        self.assertIs(guardian.redact, security.redact)
        self.assertIs(guardian.run_external, security.run_external)
        self.assertIs(guardian.run_gitleaks, security.run_gitleaks)
        self.assertIs(guardian.scan_text, security.scan_text)
        self.assertIs(guardian.has_scanner_error, security.has_scanner_error)


if __name__ == "__main__":
    unittest.main()

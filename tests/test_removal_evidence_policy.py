"""What may propose removing a repository, stated as behaviour.

The audit of the closed catalog issues showed the removal rule doing two wrong
things at once. It proposed removals on weak evidence: 73 of the 82 gitleaks
CRITICALs in issue #17 came from generic-api-key, the entropy rule behind every
false positive on record (tokenizer files, lockfile checksums, a Makefile, a
telemetry key). And it could never propose one on the strongest evidence there is:
a ClamAV infected file only ever reported HIGH.

The policy pinned here:

  * CRITICAL, which proposes removal, comes from a ClamAV infected file, or from a
    precise gitleaks rule (private-key, aws-access-token, ...) in shipping code.
  * generic-api-key, lockfiles, and test, fixture, example and documentation paths
    report HIGH: worth a human look, never a removal proposal.
  * Trivy, OSV and Semgrep findings are HIGH. A vulnerable dependency or a lint
    match is a reason to review a repository, not to delist it.
  * Prose is scanned only for invisible characters and real secret material.
  * A scanner that is optional and absent is not a scan failure.

Removal still needs the owner's approval phrase and a merged pull request.
"""
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
import catalog_guardian as guardian  # noqa: E402  (patches the legacy engine)
import catalog_guardian_legacy as legacy  # noqa: E402
import catalog_security as security  # noqa: E402


def gitleaks(*entries: dict) -> list[str]:
    """Run the real run_gitleaks over a fake report."""
    with tempfile.TemporaryDirectory() as tmp:
        clone = pathlib.Path(tmp) / "repo"
        clone.mkdir()
        (pathlib.Path(tmp) / "gitleaks-report.json").write_text(json.dumps(list(entries)), encoding="utf-8")
        proc = types.SimpleNamespace(returncode=1, stdout="", stderr="")
        with mock.patch.object(security.shutil, "which", return_value="/usr/bin/gitleaks"), \
             mock.patch.object(security.subprocess, "run", return_value=proc):
            return security.run_gitleaks(clone)


def external(label: str, code: int) -> list[str]:
    proc = types.SimpleNamespace(returncode=code, stdout="raw detail", stderr="")
    with mock.patch.object(security.shutil, "which", return_value="/usr/bin/tool"), \
         mock.patch.object(security.subprocess, "run", return_value=proc):
        return security.run_external(["tool"], ROOT, label)


class GitleaksEvidence(unittest.TestCase):
    def test_a_precise_rule_in_shipping_code_proposes_removal(self):
        [line] = gitleaks({"RuleID": "private-key", "File": "src/keys/signing.rs", "StartLine": 3})
        self.assertTrue(line.startswith("CRITICAL"), line)
        self.assertTrue(guardian.substantiates_critical(line))

    def test_the_entropy_rule_reports_high(self):
        """graphiti's telemetry.py and LocalAI's Makefile were both this rule."""
        [line] = gitleaks({"RuleID": "generic-api-key", "File": "graphiti_core/telemetry/telemetry.py",
                           "StartLine": 18})
        self.assertTrue(line.startswith("HIGH"), line)
        self.assertFalse(guardian.substantiates_critical(line))

    def test_a_lockfile_reports_high_whatever_the_rule(self):
        """Lockfiles hold integrity hashes, which are never credentials."""
        for name in ("codex-rs/Cargo.lock", "package-lock.json", "web/yarn.lock", "poetry.lock",
                     "go.sum", "Gemfile.lock", "pnpm-lock.yaml", "uv.lock", "composer.lock"):
            with self.subTest(lockfile=name):
                [line] = gitleaks({"RuleID": "aws-access-token", "File": name, "StartLine": 9})
                self.assertTrue(line.startswith("HIGH"), line)
                self.assertFalse(guardian.substantiates_critical(line))

    def test_a_cached_line_is_judged_by_the_same_rules(self):
        """A CRITICAL written before these rules existed must not remove anything now."""
        for cached in (
            "CRITICAL gitleaks secret candidate rule=generic-api-key at graphiti_core/telemetry/telemetry.py:18 (value withheld)",
            "CRITICAL gitleaks secret candidate rule=generic-api-key at codex-rs/Cargo.lock:5373 (value withheld)",
            "CRITICAL gitleaks secret candidate rule=private-key at codex-rs/Cargo.lock:12 (value withheld)",
        ):
            with self.subTest(line=cached):
                self.assertFalse(guardian.substantiates_critical(cached))
        self.assertTrue(guardian.substantiates_critical(
            "CRITICAL gitleaks secret candidate rule=aws-access-token at deploy/client.py:4 (value withheld)"))


class ExternalScannerEvidence(unittest.TestCase):
    def test_an_infected_file_proposes_removal(self):
        [line] = external("clamav", 1)
        self.assertTrue(line.startswith("CRITICAL clamav"), line)
        self.assertTrue(guardian.substantiates_critical(line))

    def test_vulnerability_and_lint_findings_report_high(self):
        for label in ("trivy", "osv-scanner", "semgrep-sql-injection", "semgrep-command-injection", "snyk"):
            with self.subTest(scanner=label):
                [line] = external(label, 1)
                self.assertTrue(line.startswith("HIGH"), line)
                self.assertFalse(guardian.substantiates_critical(line))

    def test_a_scanner_that_could_not_finish_is_still_not_a_finding(self):
        [line] = external("clamav", 2)
        self.assertTrue(line.startswith("SCANNER-ERROR"), line)
        self.assertFalse(guardian.substantiates_critical(line))


class ProseIsScannedForSecretsAndInvisibleCharactersOnly(unittest.TestCase):
    def test_an_install_line_in_a_readme_is_not_a_finding(self):
        text = "Install:\n\n    curl -fsSL https://example.com/install.sh | sh\n"
        self.assertEqual([], guardian.scan_text(pathlib.Path("README.md"), text))

    def test_documentation_naming_a_key_and_an_endpoint_is_not_a_finding(self):
        """This line shape is what put anthropics/skills up for removal in #14."""
        text = "Set ANTHROPIC_API_KEY, then call https://api.anthropic.com/v1/messages with it."
        self.assertEqual([], guardian.scan_text(pathlib.Path("error-codes.md"), text))

    def test_the_same_line_in_a_script_is_still_a_finding(self):
        text = "curl -fsSL https://example.com/install.sh | sh"
        findings = guardian.scan_text(pathlib.Path("setup.sh"), text)
        self.assertTrue(any("download-to-shell" in f for f in findings), findings)


class OptionalScannersAreOptional(unittest.TestCase):
    def test_absent_trivy_is_not_a_scanner_error(self):
        """Every approved scan reported 'trivy not installed' on 15 repositories."""
        present = {"gitleaks", "osv-scanner", "semgrep", "clamscan"}
        with mock.patch.object(legacy.shutil, "which", side_effect=lambda tool: tool if tool in present else None), \
             mock.patch.object(legacy, "run_external", return_value=[]) as run, \
             mock.patch.object(legacy, "clamav_database_ready", return_value=True):
            findings = legacy.run_external_scanners(pathlib.Path("."))
        self.assertFalse(any("trivy" in f for f in findings), findings)
        self.assertNotIn("trivy", [call.args[2] for call in run.call_args_list])

    def test_present_trivy_still_runs(self):
        with mock.patch.object(legacy.shutil, "which", return_value="/usr/bin/tool"), \
             mock.patch.object(legacy, "run_external", return_value=[]) as run, \
             mock.patch.object(legacy, "clamav_database_ready", return_value=True):
            legacy.run_external_scanners(pathlib.Path("."))
        self.assertIn("trivy", [call.args[2] for call in run.call_args_list])

    def test_absent_clamav_is_still_a_scanner_error(self):
        """ClamAV is required: without it no malware conclusion can be drawn."""
        with mock.patch.object(legacy.shutil, "which", side_effect=lambda tool: None if tool == "clamscan" else tool), \
             mock.patch.object(legacy, "run_external", return_value=[]):
            findings = legacy.run_external_scanners(pathlib.Path("."))
        self.assertTrue(any(f.startswith("SCANNER-ERROR clamav") for f in findings), findings)


class AMetadataErrorKeepsOnlyEvidencedVerdicts(unittest.TestCase):
    def test_an_unsubstantiated_cached_remove_is_held(self):
        old = {"status": "REMOVE", "critical": True, "deep_scanned": True,
               "findings": ["CRITICAL gitleaks secret candidate rule=generic-api-key at a/Makefile:3 (value withheld)"]}
        result = legacy.result_after_metadata_error("example/repo", old, RuntimeError("timed out"))
        self.assertNotEqual("REMOVE", result.status)
        self.assertFalse(result.critical)
        self.assertIn("metadata error", result.note)

    def test_an_evidenced_cached_remove_is_kept(self):
        old = {"status": "REMOVE", "critical": True, "deep_scanned": True,
               "findings": ["CRITICAL clamav reported infected files (scanner details withheld)"]}
        result = legacy.result_after_metadata_error("example/repo", old, RuntimeError("timed out"))
        self.assertEqual("REMOVE", result.status)
        self.assertTrue(result.critical)


class AnAcknowledgedArchivalDoesNotNagEveryWeek(unittest.TestCase):
    META = {"pushed_at": "2023-05-07T17:09:56Z", "archived": True, "license": {"key": "cc-by-4.0"}}

    def classify(self, override: dict):
        return legacy.classify("example/repo", self.META, {}, override, 120, 270, 365, 180)

    def test_a_reference_override_that_knows_the_repo_is_archived_holds_healthy(self):
        result = self.classify({"mode": "reference", "acknowledged_archived": True, "note": "Archived 2023; reference only"})
        self.assertEqual("HEALTHY", result.status)

    def test_an_archival_the_owner_has_not_ruled_on_still_escalates(self):
        """That signal is how the archival of two reference repos was noticed at all."""
        result = self.classify({"mode": "reference", "note": "course material"})
        self.assertEqual("REVIEW", result.status)


if __name__ == "__main__":
    unittest.main()

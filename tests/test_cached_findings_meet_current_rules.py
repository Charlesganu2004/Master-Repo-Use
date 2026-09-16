"""A finding restored from cache is judged by today's rules, not the rules it was written under.

The fixes for issues #16 and #17 capped gitleaks hits in fixture paths below
CRITICAL and stopped built-in heuristics raising CRITICAL at all. Both fixes act
when a finding is written. Neither acted when a finding is read back: the cheap
metadata pass restores the last deep scan from the actions cache, and it counted
any line starting with CRITICAL as grounds for REMOVE.

So a cached line from before the fix, such as ollama/ollama's gitleaks hit in
convert/testdata/, still removed the repository on the next run with
--apply-removals. Auditing the closure of #16 reproduced exactly that. These
tests call the real functions through the patched entry point, because the
source-string tests beside them passed with the bug in place.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import catalog_guardian as guardian  # noqa: E402  (patches the legacy engine)
import catalog_guardian_legacy as legacy  # noqa: E402
import catalog_security as security  # noqa: E402

# Lines of the shapes the pre-fix scanner persisted, taken from issues #16 and #17.
PRE_FIX_FIXTURE_GITLEAKS = (
    "CRITICAL gitleaks secret candidate rule=generic-api-key "
    "at convert/testdata/gemma-2b-it.json:3 (value withheld)")
PRE_FIX_HEURISTIC = "CRITICAL secret/private-key material in app/settings.py"
SCANNER_NAME_ONLY_IN_PATH = "CRITICAL credential-exfil pattern in .github/workflows/semgrep.yml"
REAL_LEAK = (
    "CRITICAL gitleaks secret candidate rule=aws-access-token "
    "at src/billing/client.py:41 (value withheld)")


def restored(*findings: str) -> guardian.Result:
    result = guardian.Result(repo="example/repo", status="HEALTHY")
    guardian.restore_scan_state(
        result, {"deep_scanned": True, "critical": True, "findings": list(findings)})
    return result


class CachedFindingsMeetCurrentRules(unittest.TestCase):
    def test_a_pre_fix_fixture_hit_no_longer_removes_a_repository(self):
        """ollama/ollama's twenty CRITICALs were all this shape."""
        result = restored(PRE_FIX_FIXTURE_GITLEAKS)
        self.assertNotEqual("REMOVE", result.status, result.note)
        self.assertFalse(result.critical)

    def test_a_pre_fix_heuristic_critical_no_longer_removes_a_repository(self):
        result = restored(PRE_FIX_HEURISTIC)
        self.assertNotEqual("REMOVE", result.status, result.note)
        self.assertFalse(result.critical)

    def test_a_scanner_name_inside_a_path_is_not_a_scanner(self):
        """Matching the name anywhere in the line let a workflow filename count."""
        result = restored(SCANNER_NAME_ONLY_IN_PATH)
        self.assertNotEqual("REMOVE", result.status, result.note)
        self.assertFalse(result.critical)

    def test_the_held_verdict_says_why_it_was_held(self):
        result = restored(PRE_FIX_FIXTURE_GITLEAKS)
        self.assertEqual("REVIEW", result.status)
        self.assertIn("rescan", result.note)

    def test_a_real_leak_in_source_still_removes(self):
        """The fix must not blunt the case the scanner exists for."""
        result = restored(PRE_FIX_FIXTURE_GITLEAKS, REAL_LEAK)
        self.assertEqual("REMOVE", result.status)
        self.assertTrue(result.critical)
        self.assertIn("src/billing/client.py", result.note,
                      "REMOVE must quote the finding that justifies it, not the first CRITICAL line")


class OneRuleForFreshAndCachedFindings(unittest.TestCase):
    CASES = {
        PRE_FIX_FIXTURE_GITLEAKS: False,
        PRE_FIX_HEURISTIC: False,
        SCANNER_NAME_ONLY_IN_PATH: False,
        REAL_LEAK: True,
        "HIGH gitleaks secret candidate rule=x at src/a.py:1 (value withheld)": False,
        "SCANNER-ERROR gitleaks not installed; secret scanning did not run": False,
    }

    def test_the_rule(self):
        for line, expected in self.CASES.items():
            with self.subTest(line=line):
                self.assertIs(expected, guardian.substantiates_critical(line))

    def test_both_modules_agree(self):
        """The legacy engine keeps its own copy; it must not drift from the hardened one.

        Importing catalog_guardian replaces legacy's copy with the hardened one, so
        comparing the two imported names compares a function with itself. Load an
        unpatched copy of the legacy module to compare the code actually written there.
        """
        spec = importlib.util.spec_from_file_location(
            "catalog_guardian_legacy_unpatched", ROOT / "scripts" / "catalog_guardian_legacy.py")
        unpatched = importlib.util.module_from_spec(spec)
        # @dataclass resolves its module through sys.modules while the class is built.
        sys.modules[spec.name] = unpatched
        try:
            spec.loader.exec_module(unpatched)
        finally:
            sys.modules.pop(spec.name, None)
        self.assertIsNot(unpatched.substantiates_critical, security.substantiates_critical)
        for line in self.CASES:
            with self.subTest(line=line):
                self.assertIs(unpatched.substantiates_critical(line),
                              security.substantiates_critical(line))

    def test_the_entry_point_uses_the_hardened_rule(self):
        self.assertIs(legacy.substantiates_critical, security.substantiates_critical)


if __name__ == "__main__":
    unittest.main()

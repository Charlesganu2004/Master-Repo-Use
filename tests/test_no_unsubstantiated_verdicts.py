"""A verdict must carry the finding it is based on, or it is not a verdict.

The audit marked ggml-org/llama.cpp REMOVE for a "CRITICAL security finding".
That repository appears nowhere in the findings report: 126k stars, MIT, pushed
that day, added two days earlier on request. A removal reason that cannot be
quoted is indistinguishable from an invented one, and with --apply-removals it
deletes a catalog entry either way.

The rule enforced here: if the critical flag is set but no CRITICAL line exists
to quote, the verdict is unsubstantiated. It becomes REVIEW, not REMOVE, and says
why. Nothing is deleted on evidence nobody can read.
"""
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "scripts" / "catalog_guardian_legacy.py").read_text(encoding="utf-8")
sys.path.insert(0, str(ROOT / "scripts"))
import catalog_guardian as guardian  # noqa: E402  (patches the legacy engine)


class EveryVerdictQuotesItsEvidence(unittest.TestCase):
    def test_remove_requires_a_quotable_critical_finding(self):
        """A critical flag with nothing to quote is held, not acted on."""
        result = guardian.Result(repo="example/repo", status="HEALTHY")
        guardian.restore_scan_state(result, {"deep_scanned": True, "critical": True, "findings": []})
        self.assertEqual("REVIEW", result.status, "REMOVE no longer looks for a finding to quote")
        self.assertFalse(result.critical)
        self.assertIn("unsubstantiated", result.note)
        # The fresh-scan path lives inside main(); pin that it selects its evidence
        # with the same rule, so the two paths cannot drift apart again.
        self.assertEqual(2, SOURCE.count("if substantiates_critical("),
                         "both REMOVE paths must choose their evidence with substantiates_critical")

    def test_both_paths_that_set_remove_require_evidence(self):
        """There are two. The cached one is what actually bit llama.cpp.

        A fresh scan sets critical from findings it just made. A cheap metadata
        pass restores critical from cached state. Only the first was ever checked,
        so a stale flag produced REMOVE with nothing to quote.
        """
        occurrences = [i for i in range(len(SOURCE))
                       if SOURCE.startswith("if result.critical:", i)]
        self.assertEqual(len(occurrences), 2,
                         "the number of REMOVE paths changed; re-check both")
        for start in occurrences:
            window = SOURCE[start:start + 1200]
            window = window[:window.index("elif ")]
            self.assertIn("unsubstantiated", window, "a REMOVE path accepts no evidence")
            self.assertIn('result.status = "REVIEW"', window)
            self.assertIn("result.critical = False", window,
                          "the flag must be cleared, or downstream still treats it as critical")

    def test_the_remove_note_contains_the_finding_text(self):
        self.assertIn('f"CRITICAL security finding: {evidence[:200]}"', SOURCE)

    def test_the_generic_note_is_gone(self):
        """'CRITICAL security finding' with nothing after it is the bug."""
        self.assertNotIn('result.status, result.note = "REMOVE", "CRITICAL security finding"',
                         SOURCE)

    def test_high_verdicts_also_quote_their_finding(self):
        self.assertIn("first_high", SOURCE)
        self.assertIn('f"HIGH security finding requires owner review: {first_high[:200]}"', SOURCE)

    def test_the_reason_is_recorded_in_the_source(self):
        flat = " ".join(SOURCE.replace("#", " ").split())
        self.assertIn("indistinguishable from an invented", flat)


class ScannerFailuresAreNotFindings(unittest.TestCase):
    """A tool that did not run has learned nothing about the repository."""

    def test_a_scanner_error_never_sets_critical(self):
        self.assertIn("Scanner failures never set critical", SOURCE)

    def test_a_scanner_error_says_it_is_not_a_finding(self):
        self.assertIn("rescan required, not a finding", SOURCE)

    def test_a_failed_clone_is_infrastructure_not_evidence(self):
        self.assertIn("not evidence about the repo", SOURCE)


class OnlyRealScannersCanRemove(unittest.TestCase):
    def test_critical_requires_a_named_external_scanner(self):
        """The scanner is the word after the severity, not a name found anywhere in the line."""
        self.assertTrue(guardian.substantiates_critical(
            "CRITICAL gitleaks secret candidate rule=aws-access-token at src/app.py:3 (value withheld)"))
        self.assertFalse(guardian.substantiates_critical(
            "CRITICAL secret/private-key material in app.py"))
        self.assertFalse(guardian.substantiates_critical(
            "CRITICAL credential-exfil pattern in .github/workflows/semgrep.yml"))
        self.assertIn("any(substantiates_critical(item) for item in findings)", SOURCE,
                      "deep_scan must set critical with the shared rule")

    def test_no_builtin_heuristic_emits_critical(self):
        """Heuristics may flag for review; they may never drive a removal."""
        builtin = SOURCE[SOURCE.index("def scan_text"):SOURCE.index("def run_gitleaks")]
        emitted = re.findall(r'out\.append\(f?"(\w+)', builtin)
        self.assertTrue(emitted, "scan_text emits nothing; the test is looking in the wrong place")
        self.assertNotIn("CRITICAL", emitted,
                         f"a built-in heuristic still emits CRITICAL: {emitted}")


if __name__ == "__main__":
    unittest.main()

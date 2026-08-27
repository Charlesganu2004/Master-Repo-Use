#!/usr/bin/env python3
"""Scan coverage must be stated, and never confused with a clean result.

The failure this guards against is the one the repository actually shipped with:
0 of 252 catalogued repositories had ever been deep-scanned, and nothing on the site
or in any issue said so. An empty findings list read exactly like a clean bill of
health. These tests pin the two properties that keep that from recurring:

  1. Coverage is always reported, including when it is zero.
  2. A scanner that failed is reported as unverified, never as clean.
"""
from __future__ import annotations

import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_public_site as builder  # noqa: E402
import security_report as reporter  # noqa: E402

GUARDIAN = ROOT / ".github" / "workflows" / "catalog-guardian.yml"


def state(repos: list[dict]) -> dict:
    return {"updated": "2026-08-25 12:00 UTC", "counts": {}, "repos": repos}


class SecurityReportTests(unittest.TestCase):
    def test_zero_coverage_is_stated_explicitly(self):
        body, urgent = reporter.build_body(state([{"repo": "a/b"}, {"repo": "c/d"}]))
        self.assertIn("0 / 2", body)
        self.assertIn("0%", body)
        self.assertEqual(0, urgent)

    def test_scanner_error_is_reported_as_unverified_not_clean(self):
        body, _ = reporter.build_body(state([
            {"repo": "a/b", "findings": ["SCANNER-ERROR clamav database missing"]},
        ]))
        self.assertIn("unverified", body)
        self.assertNotIn("| `a/b` |", body)  # not listed as a finding

    def test_critical_and_high_are_counted_as_urgent(self):
        body, urgent = reporter.build_body(state([
            {"repo": "a/b", "deep_scanned": True, "findings": ["CRITICAL credential-exfil pattern"]},
            {"repo": "c/d", "deep_scanned": True, "findings": ["HIGH possible SQL injection"]},
            {"repo": "e/f", "deep_scanned": True, "findings": ["LOW something minor"]},
        ]))
        self.assertEqual(2, urgent)
        self.assertIn("CRITICAL 1", body)
        self.assertIn("HIGH 1", body)

    def test_remaining_coverage_is_projected(self):
        body, _ = reporter.build_body(state(
            [{"repo": f"o/r{i}", "deep_scanned": i < 19} for i in range(100)]))
        self.assertIn("81 repositories have not been deep-scanned", body)
        self.assertIn("more week", body)

    def test_report_never_claims_safety_it_has_not_established(self):
        body, _ = reporter.build_body(state([{"repo": "a/b"}]))
        lowered = body.lower()
        for phrase in ("no malware", "is safe", "verified clean", "all clear"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, lowered)


class RotationWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.guardian = GUARDIAN.read_text(encoding="utf-8")

    def test_rotation_runs_on_a_schedule_without_an_approval_gate(self):
        """Reporting a risk must not wait on a human. Only changes are gated."""
        self.assertIn("deep-scan-rotation:", self.guardian)
        self.assertIn("github.event_name == 'schedule'", self.guardian)

    def test_rotation_never_applies_removals(self):
        """Read-only is what makes running it ungated defensible."""
        block = self.guardian.split("deep-scan-rotation:", 1)[1].split("approved-maintenance:", 1)[0]
        self.assertIn("--deep", block)
        self.assertNotIn("--apply-removals", block)

    def test_rotation_is_deterministic(self):
        block = self.guardian.split("deep-scan-rotation:", 1)[1].split("approved-maintenance:", 1)[0]
        self.assertIn("604800", block, "rotation index should come from whole weeks, not randomness")


class PrivateKeyCheckTests(unittest.TestCase):
    """The published advisor dataset must not carry private catalog fields."""

    def test_private_field_is_rejected(self):
        raw = json.dumps({"repos": [{"slug": "ollama/ollama", "note": "internal reasoning"}]})
        problems = builder.private_keys_present(raw, "test")
        self.assertTrue(any("note" in p for p in problems))

    def test_nested_private_field_is_rejected(self):
        raw = json.dumps({"models": [{"id": "x", "meta": {"findings": ["HIGH"]}}]})
        self.assertTrue(builder.private_keys_present(raw, "test"))

    def test_english_prose_containing_the_word_note_is_fine(self):
        """A substring check flagged "Note that ..." and pressured weakening the gate."""
        raw = json.dumps({"tiers": [{"summary": "Note that 27B is the ceiling here."}]})
        self.assertEqual([], builder.private_keys_present(raw, "test"))

    def test_shipped_profiles_carry_no_private_fields(self):
        raw = (ROOT / "docs" / "hardware-profiles.json").read_text(encoding="utf-8")
        self.assertEqual([], builder.private_keys_present(raw, "hardware-profiles.json"))


if __name__ == "__main__":
    unittest.main()

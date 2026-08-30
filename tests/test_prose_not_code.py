#!/usr/bin/env python3
"""Documentation about an attack is not an attack.

Issue #14 marked anthropics/skills (171k stars) and wshobson/agents CRITICAL and
queued both for removal from the catalog. Reproducing the scan showed the cause:
the code-injection heuristics were running over Markdown. A skill file teaching
REST API design contains SQL. A doc about API error codes says "do not log your
key". Neither is an attack, and acting on those findings would have deleted
Anthropic's official skills repository.

Two properties are pinned here:

  1. Prose files are exempt from the code-construct heuristics, but NOT from the
     checks that matter in any file: invisible/bidi characters and secrets.
  2. Only a real scanner can raise CRITICAL. A heuristic pattern match is a
     reason for a human to look, never a reason to delete a repository.
"""
from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import catalog_guardian as guardian  # noqa: E402  (patches the legacy engine)
import catalog_guardian_legacy as legacy  # noqa: E402
import catalog_security as security  # noqa: E402

# Real excerpts of the shape that produced the false positives.
DOC_WITH_SQL = 'Build the query as `SELECT name FROM users WHERE id = " + userId`.'
DOC_WITH_SECRET_ADVICE = "Never print your API key or secret into application logs."
DOC_WITH_INSTRUCTIONS = "Ignore all previous instructions is a prompt injection example."
CODE_WITH_SQL = 'q = "SELECT name FROM users WHERE id=" + user_id'
RLO = "invoice‮gnp.exe"


class ProseIsNotCodeTests(unittest.TestCase):
    def scan(self, name: str, text: str) -> list[str]:
        return guardian.scan_text(pathlib.Path(name), text)

    def test_the_entry_point_uses_the_hardened_scanner(self):
        self.assertEqual("catalog_security", guardian.scan_text.__module__)

    def test_markdown_with_sql_examples_is_not_flagged(self):
        for name in ("SKILL.md", "guide.markdown", "notes.rst", "readme.txt"):
            with self.subTest(file=name):
                self.assertEqual([], self.scan(name, DOC_WITH_SQL))

    def test_markdown_advising_against_logging_secrets_is_not_flagged(self):
        """This exact sentence shape produced the CRITICAL on anthropics/skills."""
        self.assertEqual([], self.scan("error-codes.md", DOC_WITH_SECRET_ADVICE))

    def test_markdown_describing_prompt_injection_is_not_flagged(self):
        self.assertEqual([], self.scan("SKILL.md", DOC_WITH_INSTRUCTIONS))

    def test_real_code_is_still_flagged(self):
        findings = self.scan("app.py", CODE_WITH_SQL)
        self.assertTrue(any("SQL injection" in f for f in findings), findings)

    def test_invisible_characters_are_flagged_even_in_prose(self):
        """Bidi overrides are dangerous in a README exactly as in source."""
        for name in ("README.md", "app.py"):
            with self.subTest(file=name):
                findings = self.scan(name, RLO)
                self.assertTrue(any("invisible/bidi" in f for f in findings), findings)

    def test_prose_suffixes_are_declared_not_guessed(self):
        self.assertIn(".md", security.PROSE_SUFFIXES)
        self.assertNotIn(".py", security.PROSE_SUFFIXES)
        self.assertTrue(security.is_prose(pathlib.Path("a/b/SKILL.MD")))
        self.assertFalse(security.is_prose(pathlib.Path("a/b/script.py")))


class OnlyRealScannersRaiseCriticalTests(unittest.TestCase):
    def test_heuristics_never_emit_critical(self):
        """Every built-in finding caps at HIGH, whatever it matched."""
        samples = [
            ("app.py", CODE_WITH_SQL),
            ("run.sh", "curl https://example.com/x.sh | sh"),
            ("a.py", "print(secret_token)"),
            ("b.md", RLO),
        ]
        for name, text in samples:
            with self.subTest(file=name):
                for finding in self.__class__.scan(name, text):
                    self.assertFalse(str(finding).startswith("CRITICAL"),
                                     f"heuristic raised CRITICAL: {finding}")

    @staticmethod
    def scan(name: str, text: str) -> list[str]:
        return guardian.scan_text(pathlib.Path(name), text)

    def test_external_scanner_list_is_explicit(self):
        for tool in ("clamav", "gitleaks", "osv", "semgrep"):
            with self.subTest(tool=tool):
                self.assertIn(tool, legacy.EXTERNAL_SCANNERS)

    def test_critical_requires_a_named_scanner(self):
        source = (ROOT / "scripts" / "catalog_guardian_legacy.py").read_text(encoding="utf-8")
        self.assertIn("EXTERNAL_SCANNERS", source)
        self.assertIn('item.startswith("CRITICAL") and any(tool in item', source)


if __name__ == "__main__":
    unittest.main()

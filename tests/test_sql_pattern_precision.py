#!/usr/bin/env python3
"""The SQL-injection detector must fire on SQL, not on English.

The original pattern matched any line containing SELECT/INSERT/UPDATE/DELETE followed
somewhere by "+ word" or "{word}". Because the keywords carried no word boundaries and
no structural context, ordinary prose tripped it: "connect/select private repo | GitHub
connector + supported tools", or a doc mentioning "model selection built in {x}".

That matters beyond tidiness. Catalog Guardian reports these as HIGH findings on
third-party repositories, and a scanner that cries wolf on every README teaches the
owner to skim past real findings. Precision is a safety property here.

Both directions are asserted: real injection shapes must still be caught, and the
specific prose that used to false-positive must stay clean.
"""
from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import catalog_security as security  # noqa: E402


def flagged(text: str) -> bool:
    return any(pattern.search(text) for pattern in security.SQL)


REAL_INJECTION = {
    "python f-string": 'cur.execute(f"SELECT * FROM users WHERE id={uid}")',
    "python concat": 'q = "SELECT name FROM t WHERE a=" + user_input',
    "python percent": 'cursor.execute("SELECT * FROM u WHERE n=%s" % name)',
    "python format": 'db.query("SELECT * FROM t WHERE a={}".format(v))',
    "js template": "db.run(`DELETE FROM logs WHERE u=${name}`)",
    "update set": 'sql = "UPDATE accounts SET bal=" + amt',
    "insert into": 'db.query("INSERT INTO t VALUES (" + v + ")")',
}

INNOCENT_PROSE = {
    "select in a table cell": "connect/select private GitHub repo | GitHub connector + supported tools",
    "selection substring": "hardware-aware model selection built in. {something}",
    "updated substring": "The doc was updated with {new} details",
    "deleted substring": "files deleted by the cleanup + verified",
    "insert as a verb": "insert the token into {config} manually",
    "update as a noun": "this update covers {scope} and + more",
}


class SqlPatternPrecisionTests(unittest.TestCase):
    def test_real_injection_shapes_are_still_caught(self):
        for label, snippet in REAL_INJECTION.items():
            with self.subTest(case=label):
                self.assertTrue(flagged(snippet), f"missed real injection: {snippet}")

    def test_english_prose_does_not_trip_the_detector(self):
        for label, snippet in INNOCENT_PROSE.items():
            with self.subTest(case=label):
                self.assertFalse(flagged(snippet), f"false positive on prose: {snippet}")

    def test_repository_own_documentation_is_clean(self):
        """This repo's own docs previously produced HIGH findings against themselves."""
        for name in ("README.md", "index.html", "AGENTS.md", "docs/ADK-GUIDE.md",
                     "docs/LOCAL-MODEL-HARDWARE.md", ".gemini/styleguide.md"):
            with self.subTest(file=name):
                text = (ROOT / name).read_text(encoding="utf-8")
                hits = [line.strip()[:110] for line in text.splitlines() if flagged(line)]
                self.assertEqual([], hits, f"{name} trips the SQL detector")

    def test_keywords_require_structural_context(self):
        """A bare keyword plus interpolation is not evidence of SQL."""
        self.assertFalse(flagged("SELECT {value}"))
        self.assertTrue(flagged('SELECT a FROM b WHERE c={value}'))


if __name__ == "__main__":
    unittest.main()

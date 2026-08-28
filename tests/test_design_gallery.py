from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HTML = ROOT / "design-options.html"
JS = ROOT / "design-options.js"
TS = ROOT / "design-options.ts"
SOURCES = (HTML, JS, TS)


class DesignGalleryTests(unittest.TestCase):
    def test_assets_are_present_and_wired(self):
        for path in SOURCES:
            with self.subTest(path=path.name):
                self.assertTrue(path.exists(), f"missing gallery asset: {path.name}")

        html = HTML.read_text(encoding="utf-8")
        runtime = JS.read_text(encoding="utf-8")
        self.assertIn('<script src="design-options.js"></script>', html)
        self.assertIn('id="designGrid"', html)
        self.assertIn("const DESIGNS", runtime)
        self.assertIn("design-options.ts", runtime)

    def test_v6_graphite_source_facts_are_explicit(self):
        contract = TS.read_text(encoding="utf-8")
        for fragment in (
            'release: "V6"',
            'palette: "Graphite"',
            'state: "Current"',
            "componentCount: 28",
            "laneCount: 8",
            "canvasCount: 1",
            'lensMode: "dim"',
            'routing: "hybrid"',
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, contract)

    def test_has_eighteen_unique_designs_with_matching_type_contract(self):
        runtime = JS.read_text(encoding="utf-8")
        contract = TS.read_text(encoding="utf-8")
        runtime_ids = re.findall(r"\bid:\s*'([^']+)'", runtime)
        contract_ids = re.findall(r'\bid:\s*"([^"]+)"', contract)
        accents = re.findall(r'\baccent:\s*"(#[0-9a-fA-F]{6})"', contract)

        self.assertEqual(18, len(runtime_ids))
        self.assertEqual(18, len(set(runtime_ids)))
        self.assertEqual(runtime_ids, contract_ids)
        self.assertEqual(18, len(accents))
        self.assertEqual(18, len(set(accents)))

    def test_no_em_or_en_dashes_in_studio_assets(self):
        for path in SOURCES:
            with self.subTest(path=path.name):
                self.assertNotRegex(path.read_text(encoding="utf-8"), r"[–—]")


if __name__ == "__main__":
    unittest.main()

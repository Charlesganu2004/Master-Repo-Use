from __future__ import annotations

import collections
import pathlib
import re
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
CSS = ROOT / "atlas.css"
RUNTIME = ROOT / "atlas.js"


def array_body(source: str, start: str, end: str) -> str:
    match = re.search(re.escape(start) + r"(?P<body>[\s\S]*?)" + re.escape(end), source)
    if not match:
        raise AssertionError(f"could not find registry between {start!r} and {end!r}")
    return match.group("body")


class SystemAtlasTests(unittest.TestCase):
    def test_assets_are_present_and_wired(self):
        for path in (INDEX, CSS, RUNTIME):
            with self.subTest(path=path.name):
                self.assertTrue(path.exists())
        page = INDEX.read_text(encoding="utf-8")
        self.assertIn('href="atlas.css"', page)
        self.assertIn('src="atlas.js"', page)

    def test_registry_meets_the_requested_scale(self):
        source = RUNTIME.read_text(encoding="utf-8")
        lanes = array_body(source, "const LANE_DEFINITIONS = [", "];\n\nconst COMPONENT_DEFINITIONS")
        components = array_body(source, "const COMPONENT_DEFINITIONS = [", "];\n\nconst CANVAS_DEFINITIONS")
        canvases = array_body(source, "const CANVAS_DEFINITIONS = [", "];\n\nfunction route")
        routes = array_body(source, "const ROUTE_DEFINITIONS = [", "];\n\nconst BACKBONE_EDGES")
        self.assertEqual(16, len(re.findall(r"\{ id:", lanes)))
        self.assertEqual(52, len(re.findall(r"\{ id:", components)))
        self.assertEqual(12, len(re.findall(r"\{ id:", canvases)))
        self.assertEqual(36, len(re.findall(r"\broute\('", routes)))
        for fact in ("componentCount: 52", "laneCount: 16", "canvasCount: 12", "routeCount: 36"):
            self.assertIn(fact, source)

    def test_every_requested_interaction_has_a_hook(self):
        page = INDEX.read_text(encoding="utf-8")
        runtime = RUNTIME.read_text(encoding="utf-8")
        for element_id in (
            "canvasDeck", "diagram", "mapViewport", "mapSearch", "zoomIn",
            "zoomOut", "zoomReset", "setupRail", "routeFilters", "hybridCards",
            "routeDetail", "traceRoute", "ramRange", "themeToggle"
        ):
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"', page)
                self.assertIn(element_id, runtime)

    def test_page_has_no_duplicate_ids_or_merge_markers(self):
        page = INDEX.read_text(encoding="utf-8")
        ids = re.findall(r'\sid="([^"]+)"', page)
        duplicates = [name for name, count in collections.Counter(ids).items() if count > 1]
        self.assertEqual([], duplicates)
        self.assertNotRegex(page, r"<<<<<<<|=======|>>>>>>>")

    def test_no_em_or_en_dashes_in_atlas_assets(self):
        for path in (INDEX, CSS, RUNTIME):
            with self.subTest(path=path.name):
                self.assertNotRegex(path.read_text(encoding="utf-8"), r"[–—]")

    def test_runtime_is_valid_javascript_when_node_is_available(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is not installed")
        result = subprocess.run([node, "--check", str(RUNTIME)], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_runtime_has_no_external_dependency(self):
        source = RUNTIME.read_text(encoding="utf-8")
        self.assertNotRegex(source, r"\bimport\s|\brequire\s*\(")
        self.assertNotRegex(source, r"https?://(?!www\.w3\.org/2000/svg)")


if __name__ == "__main__":
    unittest.main()

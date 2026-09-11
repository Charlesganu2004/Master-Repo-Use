"""Every advertised design must have shared navigation and local runtime assets."""
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import subprocess
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DESIGNS = ROOT / "designs"


class RuntimeAssets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "script" and values.get("src"):
            self.assets.append(values["src"])
        elif tag == "link" and values.get("rel") == "stylesheet":
            self.assets.append(values["href"])


class AllAdvertisedDesigns(unittest.TestCase):
    def setUp(self):
        gallery = (DESIGNS / "index.html").read_text(encoding="utf-8")
        self.pages = re.findall(r"file: '([^']+)'", gallery)

    def test_gallery_names_are_unique_and_backed_by_files(self):
        self.assertGreaterEqual(len(self.pages), 34)
        self.assertEqual(len(self.pages), len(set(self.pages)))
        for name in self.pages:
            with self.subTest(page=name):
                self.assertTrue((DESIGNS / name).is_file())

    def test_every_design_loads_the_shared_panes(self):
        for name in self.pages:
            with self.subTest(page=name):
                body = (DESIGNS / name).read_text(encoding="utf-8")
                for script in ("atlas-data.js", "atlas-core.js", "atlas-panes.js"):
                    self.assertIn(f'src="{script}"', body)
                self.assertLess(body.index('src="atlas-data.js"'), body.index('src="atlas-core.js"'))
                self.assertLess(body.index('src="atlas-core.js"'), body.index('src="atlas-panes.js"'))

    def test_every_local_runtime_asset_exists(self):
        for name in self.pages:
            parser = RuntimeAssets()
            parser.feed((DESIGNS / name).read_text(encoding="utf-8"))
            self.assertTrue(parser.assets, f"{name} has no runtime assets")
            for asset in parser.assets:
                url = urlsplit(asset)
                if url.scheme or url.netloc:
                    continue
                with self.subTest(page=name, asset=asset):
                    self.assertTrue((DESIGNS / url.path).is_file())

    def test_store_names_its_offline_preview_boundary(self):
        page = (DESIGNS / "d36-mongo.html").read_text(encoding="utf-8")
        self.assertIn("Offline catalog preview, not a connected database", page)
        self.assertIn("live MongoDB explain is needed", page)
        self.assertIn("AtlasExhibition.workspace", page)

    @unittest.skipUnless(shutil.which("node"), "Node is required for the page runtime contract")
    def test_store_navigation_runs_and_returns_focus(self):
        result = subprocess.run(
            ["node", str(ROOT / "tests" / "d36_navigation_runtime.cjs")],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Store navigation runtime: OK", result.stdout)

    def test_shared_harness_copy_states_its_reach_limit(self):
        panes = (DESIGNS / "atlas-panes.js").read_text(encoding="utf-8")
        self.assertIn("Requests outside those paths are not covered", panes)
        self.assertIn("the super harness adds its named review chain", panes)


if __name__ == "__main__":
    unittest.main()

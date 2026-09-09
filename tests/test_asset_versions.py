import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from build_public_site import version_asset_links


class AssetVersions(unittest.TestCase):
    def test_local_runtime_and_styles_are_versioned(self):
        page = '<script src="atlas-core.js"></script><link href="themes.css">'
        result = version_asset_links(page, "abc123")
        self.assertIn('atlas-core.js?v=abc123', result)
        self.assertIn('themes.css?v=abc123', result)

    def test_external_sources_and_page_navigation_are_unchanged(self):
        page = '<script src="https://example.com/a.js"></script><a href="d31-mycelium.html">Open</a>'
        self.assertEqual(version_asset_links(page, "abc123"), page)

    def test_replaces_version_without_dropping_other_parameters(self):
        result = version_asset_links('<script src="atlas.js?mode=full&amp;v=old"></script>', 'new')
        self.assertIn('mode=full&amp;v=new', result)
        self.assertNotIn('old', result)


if __name__ == '__main__':
    unittest.main()

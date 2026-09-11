#!/usr/bin/env python3
"""A deployed page must be able to tell it is stale.

Three deploys in a row were reported as "nothing changed" when the site had in fact
published correctly every time: the browser was serving a cached index.html, and an
ordinary refresh did not dislodge it. Nothing on the page could reveal that, because
`document.lastModified` reports the *cached* file's date and therefore always looks
current.

The fix is a build id baked into the published HTML plus a `version.json` fetched with
`cache: 'no-store'`. These tests pin the parts that make that work, since any one of
them silently disabling would restore the original invisible failure.
"""
from __future__ import annotations

import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from public_site_fixture import IsolatedPublicSite  # noqa: E402

INDEX = ROOT / "index.html"
ATLAS_RUNTIME = ROOT / "atlas.js"

class BuildVersionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.site = IsolatedPublicSite()
        self.addCleanup(self.site.cleanup)
        self.builder = self.site.builder

    def test_source_carries_the_placeholder_to_stamp(self):
        self.assertIn('<meta name="build-id" content="dev">',
                      INDEX.read_text(encoding="utf-8"))

    def test_publish_writes_version_json(self):
        self.site.stage(version=True)
        self.assertTrue(self.builder.PUBLIC_VERSION.exists())
        data = json.loads(self.builder.PUBLIC_VERSION.read_text(encoding="utf-8"))
        self.assertTrue(data.get("build_id"))
        self.assertTrue(data.get("built_at"))

    def test_published_html_is_stamped_with_the_same_id(self):
        self.site.stage(version=True)
        published = self.builder.PUBLIC_INDEX.read_text(encoding="utf-8")
        studio = self.builder.PUBLIC_DESIGN_STUDIO.read_text(encoding="utf-8")
        identifier = json.loads(
            self.builder.PUBLIC_VERSION.read_text(encoding="utf-8"))["build_id"]
        self.assertIn(f'<meta name="build-id" content="{identifier}">', published)
        self.assertIn(f'<meta name="build-id" content="{identifier}">', studio)
        self.assertNotIn('content="dev"', published,
                         "the placeholder must be replaced, or every page looks local")
        self.assertNotIn('content="dev"', studio,
                         "the design studio placeholder must be replaced")

    def test_build_id_prefers_the_commit_sha(self):
        import os
        previous = os.environ.get("GITHUB_SHA")
        os.environ["GITHUB_SHA"] = "a" * 40
        try:
            self.assertEqual("a" * 12, self.builder.build_id())
        finally:
            if previous is None:
                os.environ.pop("GITHUB_SHA", None)
            else:
                os.environ["GITHUB_SHA"] = previous

    def test_page_compares_against_a_no_store_fetch(self):
        """A cached version.json would defeat the entire mechanism."""
        page = INDEX.read_text(encoding="utf-8") + ATLAS_RUNTIME.read_text(encoding="utf-8")
        self.assertIn("version.json", page)
        self.assertIn("cache:'no-store'", page.replace(" ", ""))

    def test_reload_uses_a_fresh_url(self):
        """A plain location.reload() can still be served from the disk cache."""
        page = INDEX.read_text(encoding="utf-8") + ATLAS_RUNTIME.read_text(encoding="utf-8")
        self.assertIn("location.replace", page)

    def test_no_duplicate_element_ids(self):
        """A duplicate id makes getElementById silently return the wrong element.

        This bit once already: a new stale-cache banner used id="stale", which the
        STALE dashboard counter already owned, so the banner could never appear.
        Asserting the general invariant catches the whole class rather than that one
        instance.
        """
        import collections
        import re
        page = "\n".join(path.read_text(encoding="utf-8") for path in (
            INDEX, ROOT / "atlas.css", ATLAS_RUNTIME
        ))
        ids = re.findall(r'\sid="([^"]+)"', page)
        dupes = [i for i, n in collections.Counter(ids).items() if n > 1]
        self.assertEqual([], dupes, f"duplicate element ids: {dupes}")

    def test_no_em_or_en_dashes_in_the_page(self):
        """House style: no em-dashes or en-dashes anywhere in the interface.

        Reworded rather than swapped for hyphens, because a hyphen between two
        words reads as a compound noun instead of a break in the sentence.
        """
        page = INDEX.read_text(encoding="utf-8")
        offenders = []
        for i, line in enumerate(page.splitlines(), 1):
            if "—" in line or "–" in line:
                offenders.append(f"line {i}: {line.strip()[:90]}")
        self.assertEqual([], offenders, "em/en dashes found: " + "; ".join(offenders[:5]))

    def test_stale_banner_exists_and_is_distinct(self):
        page = INDEX.read_text(encoding="utf-8")
        self.assertIn('id="staleBar"', page)
        self.assertIn('id="staleReload"', page)


if __name__ == "__main__":
    unittest.main()

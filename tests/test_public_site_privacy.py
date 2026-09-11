#!/usr/bin/env python3
from __future__ import annotations
import concurrent.futures
import hashlib
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from public_site_fixture import IsolatedPublicSite  # noqa: E402

class PublicSitePrivacyTests(unittest.TestCase):
    def setUp(self):
        self.site = IsolatedPublicSite()
        self.addCleanup(self.site.cleanup)
        self.builder = self.site.builder

    def test_clean_build_passes(self):
        payload = self.site.stage()
        self.assertEqual([], self.builder.verify(payload))
        self.assertEqual([], payload["repos"])
        self.assertIs(True, payload["public"])

    def test_private_markup_is_removed(self):
        self.site.stage()
        private = (ROOT / "index.html").read_text(encoding="utf-8")
        public = self.builder.PUBLIC_INDEX.read_text(encoding="utf-8")
        self.assertIn("data-private", private)
        self.assertNotIn("data-private", public)
        self.assertLess(len(public), len(private))
        self.assertEqual([], sorted(
            name for name in self.builder.private_repo_names() - {self.builder.OWN_REPO}
            if name in public))
        # The public artifact must still be a working page, not a stripped husk.
        for keep in ("Catalog health", "Public privacy mode", "Graphite Atlas",
                     "Twelve views", "Thirty six ways", "platSeg", "atlas.js"):
            with self.subTest(keep=keep):
                self.assertIn(keep, public)
        # The repo-by-repo table now lives behind data-private, so it must NOT survive.
        for drop in ('id="healthRows"', "Private rows", "data-private"):
            with self.subTest(drop=drop):
                self.assertNotIn(drop, public)

    def test_verifier_rejects_per_repo_rows(self):
        payload = self.site.stage()
        payload["repos"] = [{"repo": "FlowiseAI/Flowise", "note": "x"}]
        self.assertTrue(self.builder.verify(payload))

    def test_verifier_rejects_extra_private_keys(self):
        payload = self.site.stage()
        payload["note"] = "clamav HIGH"
        self.assertTrue(self.builder.verify(payload))

    def test_verifier_rejects_repo_slug_in_value(self):
        payload = self.site.stage()
        payload["updated"] = "see thedotmack/claude-mem"
        self.assertTrue(self.builder.verify(payload))

    def test_verifier_rejects_unstripped_index(self):
        payload = self.site.stage()
        self.builder.PUBLIC_INDEX.write_bytes((ROOT / "index.html").read_bytes())
        problems = self.builder.verify(payload)
        self.assertTrue(problems)
        self.assertTrue(any("data-private" in problem for problem in problems))

    def test_design_studio_is_public_and_complete(self):
        payload = self.site.stage()
        self.assertEqual([], self.builder.verify(payload))
        self.assertTrue(self.builder.PUBLIC_DESIGN_STUDIO.exists())
        self.assertTrue(self.builder.PUBLIC_DESIGN_STUDIO_JS.exists())
        self.assertTrue(self.builder.PUBLIC_ATLAS_CSS.exists())
        self.assertTrue(self.builder.PUBLIC_ATLAS_JS.exists())
        page = self.builder.PUBLIC_DESIGN_STUDIO.read_text(encoding="utf-8")
        runtime = self.builder.PUBLIC_DESIGN_STUDIO_JS.read_text(encoding="utf-8")
        self.assertIn('src="design-options.js"', page)
        self.assertIn("const DESIGNS", runtime)

    def test_two_builds_use_distinct_guarded_roots_concurrently(self):
        def manifest(root):
            if not root.exists():
                return None
            entries = []
            for path in sorted(root.rglob("*")):
                relative = path.relative_to(root).as_posix()
                if path.is_dir():
                    entries.append((relative, "directory", ""))
                else:
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                    entries.append((relative, "file", digest))
            return tuple(entries)

        real_site = ROOT / "_site"
        before = manifest(real_site)
        first = IsolatedPublicSite()
        second = IsolatedPublicSite()
        self.addCleanup(first.cleanup)
        self.addCleanup(second.cleanup)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(site.stage, design_studio=False)
                for site in (first, second)
            ]
            for future in futures:
                future.result()

        self.assertNotEqual(first.root, second.root)
        self.assertIsNot(first.builder, second.builder)
        for site in (first, second):
            self.assertEqual(site.root / "_site", site.builder.SITE)
            self.assertNotEqual(real_site, site.builder.SITE)
            page = site.builder.PUBLIC_INDEX.read_text(encoding="utf-8")
            self.assertIn("Public privacy mode", page)
        self.assertEqual(before, manifest(real_site))

if __name__ == "__main__":
    unittest.main()

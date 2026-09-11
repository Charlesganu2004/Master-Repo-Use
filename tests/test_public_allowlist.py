#!/usr/bin/env python3
"""The public allowlist is the only sanctioned way a catalog slug reaches the public site.

The privacy contract is "the composition of the catalog is private". That rule is
correct for the curated lanes and wrong for a handful of upstreams whose whole purpose
is to be shown — the public setup page has to be able to say "install Ollama" and link
to it. repo-lists/public-allowlist.txt is that exception list, and these tests make sure
it stays an explicit, narrow, owner-controlled escape hatch rather than a hole.
"""
from __future__ import annotations

import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from public_site_fixture import IsolatedPublicSite  # noqa: E402


class PublicAllowlistTests(unittest.TestCase):
    def setUp(self) -> None:
        self.site = IsolatedPublicSite()
        self.addCleanup(self.site.cleanup)
        self.builder = self.site.builder

    def test_allowlist_is_not_empty_and_is_a_strict_subset_of_the_catalog(self):
        allowed = self.builder.public_allowlist()
        self.assertTrue(allowed, "allowlist must exist for the public setup page to work")
        catalogued: set[str] = set()
        for listing in (ROOT / "repo-lists").glob("*.txt"):
            if listing.name == self.builder.PUBLIC_ALLOWLIST_FILE.name:
                continue
            for line in listing.read_text(encoding="utf-8").splitlines():
                slug = line.split("#", 1)[0].strip()
                if slug.count("/") == 1 and slug:
                    catalogued.add(slug)
        orphans = sorted(allowed - catalogued)
        self.assertEqual([], orphans, "allowlisted slugs must be vetted in a real lane first")

    def test_allowlisting_removes_a_name_from_the_private_set(self):
        private = self.builder.private_repo_names()
        for slug in self.builder.public_allowlist():
            with self.subTest(slug=slug):
                self.assertNotIn(slug, private)

    def test_non_allowlisted_catalog_names_are_still_blocked(self):
        """The escape hatch must not disable the leak check for everything else."""
        self.site.stage(design_studio=False)
        private = self.builder.private_repo_names() - {self.builder.OWN_REPO}
        self.assertTrue(private, "there must still be private names to protect")
        page = self.builder.PUBLIC_INDEX.read_text(encoding="utf-8")
        self.assertEqual([], sorted(n for n in private if n in page))

    def test_profiles_leak_check_rejects_an_unlisted_slug(self):
        raw = json.dumps({"repos": [{"slug": "somebody/private-thing"}], "models": []})
        problems = self.builder.profile_leaks(raw, "test")
        self.assertTrue(any("somebody/private-thing" in p for p in problems))

    def test_profiles_leak_check_accepts_allowlisted_slugs(self):
        allowed = sorted(self.builder.public_allowlist())[:3]
        raw = json.dumps({"repos": [{"slug": s} for s in allowed], "models": []})
        self.assertEqual([], self.builder.profile_leaks(raw, "test"))

    def test_profiles_leak_check_ignores_prose_containing_a_slash(self):
        """"CPU/NPU" is not a repository. A regex over the whole file thinks it is."""
        raw = json.dumps({
            "repos": [{"slug": "ollama/ollama", "why": "Best CPU/NPU path; Node/TypeScript client"}],
            "models": [],
        })
        self.assertEqual([], self.builder.profile_leaks(raw, "test"))

    def test_published_profiles_pass_their_own_check(self):
        raw = (ROOT / "docs" / "hardware-profiles.json").read_text(encoding="utf-8")
        self.assertEqual([], self.builder.profile_leaks(raw, "hardware-profiles.json"))

    def test_allowlist_file_documents_the_rules(self):
        text = self.builder.PUBLIC_ALLOWLIST_FILE.read_text(encoding="utf-8")
        for phrase in ("well-known upstream", "vetted", "Never add"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()

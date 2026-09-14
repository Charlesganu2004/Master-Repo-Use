"""Raw context and benchmark evidence must never enter the public artifact."""
import unittest

from tests.public_site_fixture import IsolatedPublicSite


class PublicContextExclusion(unittest.TestCase):
    def setUp(self):
        self.site = IsolatedPublicSite()
        self.addCleanup(self.site.cleanup)
        self.builder = self.site.builder

    def test_clean_build_does_not_publish_user_upload_names(self):
        names = ("Masterpo and new context.zip", "run this test. create a prompt and.txt")
        for name in names:
            (self.site.root / name).write_bytes(b"private source upload fixture")
        payload = self.site.stage()
        self.assertEqual(self.builder.verify(payload), [])
        for name in names:
            self.assertEqual((self.site.root / name).read_bytes(), b"private source upload fixture")
            self.assertFalse((self.builder.SITE / name).exists())

    def test_verifier_rejects_extra_context_and_private_report_files(self):
        payload = self.site.stage()
        for relative in (
            "Masterpo and new context.zip",
            "run this test. create a prompt and.txt",
            "benchmarks/raw.json",
            "docs/registry-plan-2026-09-14/registry-architecture.pdf",
            "designs/nested/private-context.txt",
        ):
            with self.subTest(path=relative):
                target = self.builder.SITE / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"synthetic private test content")
                try:
                    self.assertIn(f"unexpected file in public artifact: {relative}",
                                  self.builder.verify(payload))
                finally:
                    target.unlink()


if __name__ == "__main__":
    unittest.main()

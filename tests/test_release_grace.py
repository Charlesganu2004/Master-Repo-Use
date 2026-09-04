"""A release keeps a quiet repository; a security finding still removes it.

Charles's rule: a repository that has not been pushed to recently stays in the
catalog if it has shipped a release within eighteen months, because a tagged
release means someone judged the thing ready and published it. Plenty of finished
libraries go quiet on main for a year and remain the correct dependency.

The half that matters more is the exception. This rescues from AGE only. A
repository with malware or a real secret leak is removed no matter how recently
it released, and the ordering in the source is what guarantees that: the release
check runs first, the security scan runs after and can still set REMOVE.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "scripts" / "catalog_guardian_legacy.py").read_text(encoding="utf-8")


class TheReleaseWindow(unittest.TestCase):
    def test_the_window_is_eighteen_months(self):
        self.assertIn('"--release-grace-days", type=int, default=547', SOURCE)

    def test_it_is_no_longer_tied_to_the_stale_threshold(self):
        """It used to reuse --stale-after-days, which is 120 days, far too short."""
        self.assertIn("rel_age <= args.release_grace_days", SOURCE)
        self.assertNotIn("rel_age <= args.stale_after_days", SOURCE)

    def test_the_rescue_only_applies_to_age_flagged_entries(self):
        window = SOURCE[SOURCE.index("rel_age = latest_release_age(repo)") - 400:]
        window = window[:600]
        self.assertIn('result.status in {"STALE", "REVIEW", "REMOVE"}', window)

    def test_archived_repositories_are_excluded(self):
        """A sunset release looks identical to a healthy one from the outside."""
        window = SOURCE[SOURCE.index("rel_age = latest_release_age(repo)") - 400:]
        window = window[:600]
        self.assertIn("not result.archived", window)

    def test_an_owner_override_still_wins(self):
        window = SOURCE[SOURCE.index("rel_age = latest_release_age(repo)") - 400:]
        window = window[:600]
        self.assertIn('(overrides.get(repo) or {}).get("mode")', window)


class SecurityStillOverridesAge(unittest.TestCase):
    """The ordering is the guarantee, so the ordering is what gets tested."""

    def test_the_security_scan_runs_after_the_release_rescue(self):
        rescue = SOURCE.index("rel_age = latest_release_age(repo)")
        scan = SOURCE.index("result.findings, result.critical = deep_scan(repo)")
        self.assertGreater(scan, rescue,
                           "a release would mask a malware finding if the scan ran first")

    def test_a_critical_finding_still_sets_remove(self):
        window = SOURCE[SOURCE.index("result.findings, result.critical = deep_scan(repo)"):]
        window = window[:1400]
        self.assertIn('result.status = "REMOVE"', window)

    def test_the_rescue_says_it_is_age_only(self):
        flat = " ".join(SOURCE.replace("#", " ").split())
        self.assertIn("only rescues from AGE", flat)
        self.assertIn("removed no matter how recently it shipped", flat)

    def test_removal_still_requires_a_quotable_finding(self):
        """The rescue must not have loosened the substantiation rule."""
        self.assertIn("unsubstantiated", SOURCE)
        self.assertIn("EXTERNAL_SCANNERS", SOURCE)


class TheNumbersAreCoherent(unittest.TestCase):
    def test_the_grace_is_longer_than_the_removal_threshold(self):
        """Otherwise the rescue could never save anything already past removal."""
        grace = int(re.search(r'"--release-grace-days", type=int, default=(\d+)', SOURCE).group(1))
        remove = int(re.search(r'"--remove-stale-after-days", type=int, default=(\d+)', SOURCE).group(1))
        self.assertGreater(grace, remove, f"grace {grace}d must exceed removal {remove}d")

    def test_eighteen_months_is_what_547_days_means(self):
        self.assertAlmostEqual(547 / 30.44, 18.0, places=0)


if __name__ == "__main__":
    unittest.main()

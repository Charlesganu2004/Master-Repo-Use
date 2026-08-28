"""The owner-approval comment must be forgiving to type and impossible to forge.

Charles hit this for real on PR #13: the workflow demanded a byte-exact comment
containing a 40-character SHA. Retyping that by hand is the failure mode, so a
prefix and any casing now pass. What must never pass is an approval that does not
name the commit, because the SHA is what makes approval expire on the next push.
"""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from owner_approval import is_owner_approval  # noqa: E402

SHA = "979994113ba75efb5e5693b6d503ba510a49b2fd"


class OwnerApprovalMatching(unittest.TestCase):
    def test_full_sha_is_accepted(self):
        self.assertTrue(is_owner_approval(f"APPROVE OWNER PR {SHA}", SHA))

    def test_short_sha_is_accepted(self):
        self.assertTrue(is_owner_approval(f"APPROVE OWNER PR {SHA[:7]}", SHA))

    def test_casing_and_surrounding_whitespace_are_tolerated(self):
        self.assertTrue(is_owner_approval(f"  approve owner pr {SHA[:12].upper()}  ", SHA))

    def test_bare_phrase_without_sha_is_rejected(self):
        # Without a SHA an approval would outlive the code it approved.
        self.assertFalse(is_owner_approval("APPROVE OWNER PR", SHA))

    def test_wrong_sha_is_rejected(self):
        self.assertFalse(is_owner_approval(f"APPROVE OWNER PR {'0' * 40}", SHA))

    def test_prefix_shorter_than_seven_is_rejected(self):
        self.assertFalse(is_owner_approval(f"APPROVE OWNER PR {SHA[:6]}", SHA))

    def test_phrase_must_be_the_whole_comment(self):
        self.assertFalse(is_owner_approval(f"please APPROVE OWNER PR {SHA}", SHA))
        self.assertFalse(is_owner_approval(f"APPROVE OWNER PR {SHA} and merge", SHA))

    def test_catalog_maintenance_phrase_does_not_cross_over(self):
        self.assertFalse(is_owner_approval("APPROVE CATALOG MAINTENANCE", SHA))

    def test_approval_does_not_survive_a_new_commit(self):
        older = "1111111111111111111111111111111111111111"
        self.assertFalse(is_owner_approval(f"APPROVE OWNER PR {older}", SHA))


if __name__ == "__main__":
    unittest.main()

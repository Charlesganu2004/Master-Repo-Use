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
from owner_approval import (  # noqa: E402
    PASSCODE, evaluate_approval, is_owner_approval, is_passcode_approval,
)

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

    def test_surrounding_text_is_tolerated(self):
        """Charles pasted a whole gh command as the comment. It meant approved.

        The SHA is what binds approval to a revision; other words around it do
        not weaken that, so the phrase no longer has to be the whole comment.
        """
        self.assertTrue(is_owner_approval(f"please APPROVE OWNER PR {SHA}", SHA))
        self.assertTrue(is_owner_approval(
            f'gh pr comment 13 --repo o/n --body "APPROVE OWNER PR {SHA}"', SHA))

    def test_a_commit_url_is_accepted(self):
        self.assertTrue(is_owner_approval(
            f"APPROVE OWNER PR https://github.com/o/n/commit/{SHA}", SHA))

    def test_a_pull_request_url_is_refused(self):
        """A PR URL names no revision, so it cannot pin one."""
        self.assertFalse(is_owner_approval(
            "APPROVE OWNER PR https://github.com/o/n/pull/13", SHA))

    def test_an_unrelated_pasted_command_is_refused(self):
        self.assertFalse(is_owner_approval("cd designs && python -m http.server 8000", SHA))

    def test_catalog_maintenance_phrase_does_not_cross_over(self):
        self.assertFalse(is_owner_approval("APPROVE CATALOG MAINTENANCE", SHA))

    def test_approval_does_not_survive_a_new_commit(self):
        older = "1111111111111111111111111111111111111111"
        self.assertFalse(is_owner_approval(f"APPROVE OWNER PR {older}", SHA))


class PasscodeApproval(unittest.TestCase):
    """Charles asked for a standing passcode after re-approving on every push.

    This form deliberately does NOT expire with new commits. That is the point
    of it, and the per-SHA form is still there for when a revision must be
    pinned. The passcode is a second factor on top of the owner account, never
    the only gate.
    """

    def test_the_requested_phrase_is_accepted(self):
        self.assertTrue(is_passcode_approval(f"I approve {PASSCODE}"))

    def test_casing_and_whitespace_are_tolerated(self):
        self.assertTrue(is_passcode_approval(f"  i APPROVE {PASSCODE}  "))

    def test_longer_phrasings_are_accepted(self):
        self.assertTrue(is_passcode_approval(f"I approve with passcode {PASSCODE}"))
        self.assertTrue(is_passcode_approval(f"I approve with the passcode {PASSCODE}"))

    def test_a_wrong_passcode_is_rejected(self):
        self.assertFalse(is_passcode_approval("I approve 000000"))

    def test_approval_without_a_passcode_is_rejected(self):
        self.assertFalse(is_passcode_approval("I approve"))

    def test_the_phrase_must_be_the_whole_comment(self):
        self.assertFalse(is_passcode_approval(f"I approve {PASSCODE} and merge now"))
        self.assertFalse(is_passcode_approval(f"Someone said I approve {PASSCODE}"))

    def test_only_the_owner_account_can_use_it(self):
        pr = {"head": {"sha": SHA}, "user": {"login": "Charlesganu2004"}, "draft": False}
        stranger = [{"user": {"login": "someone-else"}, "body": f"I approve {PASSCODE}"}]
        self.assertFalse(evaluate_approval(pr, stranger, []).approved)

    def test_owner_passcode_approves_an_owner_authored_pr(self):
        pr = {"head": {"sha": SHA}, "user": {"login": "Charlesganu2004"}, "draft": False}
        owner = [{"user": {"login": "Charlesganu2004"}, "body": f"I approve {PASSCODE}"}]
        self.assertTrue(evaluate_approval(pr, owner, []).approved)

    def test_owner_passcode_also_approves_someone_elses_pr(self):
        pr = {"head": {"sha": SHA}, "user": {"login": "outside-contributor"}, "draft": False}
        owner = [{"user": {"login": "Charlesganu2004"}, "body": f"I approve {PASSCODE}"}]
        self.assertTrue(evaluate_approval(pr, owner, []).approved)

    def test_a_draft_is_still_never_approved(self):
        pr = {"head": {"sha": SHA}, "user": {"login": "Charlesganu2004"}, "draft": True}
        owner = [{"user": {"login": "Charlesganu2004"}, "body": f"I approve {PASSCODE}"}]
        self.assertFalse(evaluate_approval(pr, owner, []).approved)


if __name__ == "__main__":
    unittest.main()

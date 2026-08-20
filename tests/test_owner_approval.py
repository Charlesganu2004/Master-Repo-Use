#!/usr/bin/env python3
from __future__ import annotations
import pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"scripts")); import owner_approval as approval
OWNER="Charlesganu2004"; HEAD_A="a"*40; HEAD_B="b"*40
def pr(author,sha=HEAD_A,draft=False): return {"user":{"login":author},"head":{"sha":sha},"draft":draft}
def comment(user,body): return {"user":{"login":user},"body":body}
def review(user,state,commit_id,rid=1,submitted="2026-08-20T00:00:00Z"): return {"user":{"login":user},"state":state,"commit_id":commit_id,"id":rid,"submitted_at":submitted}
class OtherAuthorApprovalTests(unittest.TestCase):
    def test_no_charles_review_fails(self): self.assertFalse(approval.evaluate_approval(pr("github-actions[bot]"),[],[]).approved)
    def test_charles_approval_current_head_passes(self): self.assertTrue(approval.evaluate_approval(pr("github-actions[bot]"),[],[review(OWNER,"APPROVED",HEAD_A)]).approved)
    def test_stale_approval_after_new_commit_fails(self): self.assertFalse(approval.evaluate_approval(pr("github-actions[bot]",HEAD_B),[],[review(OWNER,"APPROVED",HEAD_A)]).approved)
    def test_latest_changes_requested_fails(self): self.assertFalse(approval.evaluate_approval(pr("github-actions[bot]"),[],[review(OWNER,"APPROVED",HEAD_A,1,"2026-08-20T00:00:00Z"),review(OWNER,"CHANGES_REQUESTED",HEAD_A,2,"2026-08-20T00:01:00Z")]).approved)
    def test_other_user_cannot_pass(self): self.assertFalse(approval.evaluate_approval(pr("github-actions[bot]"),[],[review("Charlesganu2004-bot","APPROVED",HEAD_A)]).approved)
class CharlesAuthorApprovalTests(unittest.TestCase):
    def test_no_comment_fails(self): self.assertFalse(approval.evaluate_approval(pr(OWNER),[],[]).approved)
    def test_other_commenter_fails(self): self.assertFalse(approval.evaluate_approval(pr(OWNER),[comment("other-user",approval.exact_owner_command(HEAD_A))],[]).approved)
    def test_wrong_command_fails(self): self.assertFalse(approval.evaluate_approval(pr(OWNER),[comment(OWNER,"APPROVE OWNER PR")],[]).approved)
    def test_wrong_sha_fails(self): self.assertFalse(approval.evaluate_approval(pr(OWNER),[comment(OWNER,approval.exact_owner_command(HEAD_B))],[]).approved)
    def test_exact_current_sha_passes(self): self.assertTrue(approval.evaluate_approval(pr(OWNER),[comment(OWNER,approval.exact_owner_command(HEAD_A))],[]).approved)
    def test_new_commit_invalidates_old_comment(self):
        old=comment(OWNER,approval.exact_owner_command(HEAD_A)); self.assertTrue(approval.evaluate_approval(pr(OWNER,HEAD_A),[old],[]).approved); self.assertFalse(approval.evaluate_approval(pr(OWNER,HEAD_B),[old],[]).approved)
    def test_malformed_sha_rejected(self):
        with self.assertRaises(ValueError): approval.exact_owner_command("not-a-sha")
    def test_draft_never_passes(self): self.assertFalse(approval.evaluate_approval(pr(OWNER,HEAD_A,True),[comment(OWNER,approval.exact_owner_command(HEAD_A))],[]).approved)
class EventParsingTests(unittest.TestCase):
    def test_normal_issue_ignored(self): self.assertIsNone(approval.pr_number_from_event({"issue":{"number":9}}))
    def test_pr_issue_resolves(self): self.assertEqual(4,approval.pr_number_from_event({"issue":{"number":4,"pull_request":{"url":"x"}}}))
    def test_review_url_fallback(self): self.assertEqual(17,approval.pr_number_from_event({"review":{"pull_request_url":"https://api.github.com/repos/o/r/pulls/17"}}))
if __name__=="__main__": unittest.main()

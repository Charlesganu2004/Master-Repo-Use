#!/usr/bin/env python3
from __future__ import annotations
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class WorkflowPolicyTests(unittest.TestCase):
    def text(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_pages_has_no_recurring_schedule(self):
        pages = self.text(".github/workflows/pages.yml")
        self.assertNotIn("schedule:", pages)
        self.assertIn("workflow_dispatch:", pages)
        self.assertIn("cancel-in-progress: true", pages)
        self.assertIn("timeout-minutes:", pages)

    def test_catalog_guardian_weekly_only_and_no_scheduled_ai(self):
        guardian = self.text(".github/workflows/catalog-guardian.yml")
        self.assertIn("cron: '23 7 * * 1'", guardian)
        self.assertNotIn("api.anthropic.com", guardian)
        self.assertNotIn("api.openai.com", guardian)
        self.assertNotIn("generativelanguage.googleapis.com", guardian)

    def test_automation_pr_seeds_owner_approval_status(self):
        guardian = self.text(".github/workflows/catalog-guardian.yml")
        self.assertIn("statuses: write", guardian)
        self.assertIn("context='owner-approval'", guardian)
        self.assertIn("state='pending'", guardian)
        self.assertIn("headRefOid", guardian)

    def test_owner_gate_uses_trusted_base_branch_and_sha_bound_logic(self):
        workflow = self.text(".github/workflows/owner-approval.yml")
        policy = self.text("scripts/owner_approval.py")
        self.assertIn("pull_request_target:", workflow)
        self.assertIn("pull_request_review:", workflow)
        self.assertIn("issue_comment:", workflow)
        self.assertIn("github.event.repository.default_branch", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("APPROVE OWNER PR", policy)
        self.assertIn("commit_id != head_sha", policy)
        self.assertIn("STATUS_CONTEXT = \"owner-approval\"", policy)

    def test_branch_policy_uses_single_authoritative_owner_gate(self):
        policy = json.loads(self.text("scripts/branch-protection.json"))
        self.assertEqual(["owner-approval"], policy["required_status_checks"]["contexts"])
        reviews = policy["required_pull_request_reviews"]
        self.assertEqual(0, reviews["required_approving_review_count"])
        self.assertIs(False, reviews["require_code_owner_reviews"])
        self.assertIs(True, policy["required_conversation_resolution"])
        self.assertIs(False, policy["allow_force_pushes"])
        self.assertIs(False, policy["allow_deletions"])
        self.assertIs(False, policy["enforce_admins"])


if __name__ == "__main__":
    unittest.main()

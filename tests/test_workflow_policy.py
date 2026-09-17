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

    def test_scanner_installs_are_non_fatal(self):
        """A broken installer must degrade the audit to SCANNER-ERROR, not kill the run.

        On 2026-08-25 the whole Catalog Guardian run failed because one `go install`
        returned non-zero. Guardian is explicitly designed to treat a missing scanner
        as "rescan needed" rather than "clean", so the install step must not be the
        thing that takes the audit down.
        """
        guardian = self.text(".github/workflows/catalog-guardian.yml")
        for scanner in ("semgrep", "gitleaks", "osv-scanner", "clamav"):
            with self.subTest(scanner=scanner):
                self.assertIn(f"install_failed+=({scanner})", guardian,
                              f"{scanner} install must be guarded and recorded, not fail-hard")
        self.assertIn("SCANNER-ERROR", guardian)

    def test_gitleaks_uses_the_module_path_its_gomod_declares(self):
        """gitleaks moved org but its go.mod still says zricethezav; the new path 404s."""
        guardian = self.text(".github/workflows/catalog-guardian.yml")
        self.assertIn("go install github.com/zricethezav/gitleaks/v8@latest", guardian)
        self.assertNotIn("go install github.com/gitleaks/gitleaks/v8@latest", guardian)

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
        """One approval gate, plus the test suite.

        safety-validation runs the tests; it approves nothing, so owner-approval is
        still the only approval context. The live branch has required both since
        #16, and this file lacked the second, so re-running the documented setup
        would have silently dropped the test requirement.
        """
        policy = json.loads(self.text("scripts/branch-protection.json"))
        self.assertEqual(["owner-approval", "safety-validation"],
                         policy["required_status_checks"]["contexts"])
        self.assertIn("  safety-validation:", self.text(".github/workflows/safety-tests.yml"))
        reviews = policy["required_pull_request_reviews"]
        self.assertEqual(0, reviews["required_approving_review_count"])
        self.assertIs(False, reviews["require_code_owner_reviews"])
        self.assertIs(True, policy["required_conversation_resolution"])
        self.assertIs(False, policy["allow_force_pushes"])
        self.assertIs(False, policy["allow_deletions"])
        self.assertIs(False, policy["enforce_admins"])

    def test_setup_does_not_let_actions_approve_pull_requests(self):
        """#16 turned this off; both setup scripts turned it back on when re-run."""
        for script in ("scripts/enable-github-pro.sh", "scripts/enable-github-pro.ps1"):
            with self.subTest(script=script):
                text = self.text(script)
                self.assertIn('"can_approve_pull_request_reviews":false', text)
                self.assertNotIn('"can_approve_pull_request_reviews":true', text)

    def test_the_approved_run_links_the_pull_request_instead_of_asking_for_the_permission(self):
        guardian = self.text(".github/workflows/catalog-guardian.yml")
        self.assertIn("/compare/main...$branch?expand=1", guardian)
        self.assertNotIn("Allow GitHub Actions to create and approve pull requests", guardian)
        self.assertNotIn("Allow GitHub Actions to create and approve pull requests", self.text("README.md"))

    def test_each_approved_run_is_tagged_before_the_branch_is_replaced(self):
        guardian = self.text(".github/workflows/catalog-guardian.yml")
        tag = guardian.index('tag="catalog-guardian/run-${{ github.run_id }}"')
        self.assertLess(tag, guardian.index('git push --force origin "$branch"'),
                        "the tag must be pushed before the force-push that erases the previous run")


if __name__ == "__main__":
    unittest.main()

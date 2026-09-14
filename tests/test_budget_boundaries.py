"""Regression cases for malformed commands and already-injected requests."""
import unittest
import os
import subprocess
import sys
from pathlib import Path

from tests.test_token_limit_and_super_mode import IsolatedStore, harness_proxy, sp


class BudgetBoundaries(IsolatedStore):
    def test_large_number_does_not_overflow_or_crash_hook(self):
        action, limit, rest = sp.parse_token_command("/token limit " + "9" * 400 + " work")
        self.assertEqual((action, limit, rest), ("set", sp.TOKEN_LIMIT_MAX, "work"))

    def test_malformed_numbers_do_not_change_existing_limit(self):
        sp.save_token_limit(700, "session")
        for value in ("-1", "0.5", "1,2", "1,,000", "1,", "2.5.4", "nan", "inf", "3cats"):
            with self.subTest(value=value):
                prompt = "/token limit " + value
                self.assertIsNone(sp.parse_token_command(prompt)[0])
                self.assertEqual(sp.resolve_token_limit(prompt, "session"), 700)
                self.assertIn("TOKEN LIMIT ERROR", sp.context_for(prompt, "session"))

    def test_boolean_persisted_limit_is_not_one_token(self):
        sp.save_token_limit(True, "session")
        self.assertIsNone(sp.load_token_limit("session"))

    def test_invalid_budget_does_not_become_a_standing_goal(self):
        sp.context_for("/token limit definitely-not-a-number", "session")
        self.assertFalse(sp.load_goal("session").get("goal"))

    def test_carried_goal_is_not_a_numbered_pipeline_step(self):
        context = sp.context_for("Redesign the settings page and check security issues.",
                                 "session", mode="base")
        self.assertIn("STANDING GOAL, carried across turns", context)
        self.assertNotRegex(context, r"(?m)^\d+\. STANDING GOAL")
        self.assertLessEqual(len(context.encode("utf-8")), 3600)

    def test_existing_chat_marker_cannot_bypass_cap(self):
        messages = [
            {"role": "system", "content": harness_proxy.MARKER},
            {"role": "user", "content": "/token limit 100 work"},
        ]
        body = {"messages": messages, "max_tokens": 500}
        result, changed = harness_proxy.inject(body, "/v1/chat/completions")
        self.assertTrue(changed)
        self.assertEqual(result["max_tokens"], 100)
        self.assertEqual(result["messages"], messages)
        _, changed = harness_proxy.inject(result, "/v1/chat/completions")
        self.assertFalse(changed)

    def test_existing_generate_marker_cannot_bypass_cap(self):
        body = {"system": harness_proxy.MARKER, "prompt": "/token limit 100 work"}
        result, changed = harness_proxy.inject(body, "/api/generate")
        self.assertTrue(changed)
        self.assertEqual(result["options"]["num_predict"], 100)
        self.assertEqual(result["system"], harness_proxy.MARKER)

    def test_advisory_and_output_only_limits_are_explicit(self):
        self.assertIn("advisory", sp.token_block(50))
        self.assertIn("not a total-token", sp.token_block(50, enforced=True))

    def test_proxy_session_persists_resets_and_does_not_leak(self):
        def request(text, session):
            return harness_proxy.inject(
                {"messages": [{"role": "user", "content": text}]},
                "/v1/chat/completions", session)[0]
        self.assertEqual(request("/token limit 70 work", "proxy:a")["max_tokens"], 70)
        self.assertEqual(request("continue", "proxy:a")["max_tokens"], 70)
        self.assertNotIn("max_tokens", request("continue", "proxy:b"))
        self.assertNotIn("max_tokens", request("continue", None))
        self.assertNotIn("max_tokens", request("/token limit off", "proxy:a"))
        self.assertNotIn("max_tokens", request("continue", "proxy:a"))

    def test_dry_run_mode_and_global_limit_do_not_write_state(self):
        directory = sp.STATE_FILE.parent / "dry-run"
        environment = {**os.environ, "MASTER_REPO_GOAL_DIR": str(directory)}
        script = Path(__file__).resolve().parents[1] / "scripts" / "harness_super.py"
        for option in (["--mode", "super"], ["--token-limit", "200"]):
            result = subprocess.run([sys.executable, str(script), "--dry-run", *option],
                                    capture_output=True, text=True, env=environment)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("would set", result.stdout)
            self.assertFalse(directory.exists())


if __name__ == "__main__":
    unittest.main()

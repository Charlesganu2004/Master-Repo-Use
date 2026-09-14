import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from benchmarks.verified_2026.isolated import (
    audit, headroom, invocation, remaining, response_contract, validate_invocation,
)


class IsolatedBenchmark(unittest.TestCase):
    def setUp(self):
        self.argv = invocation("copilot", "synthetic", pathlib.Path("cell"))
        self.events = [
            {"type": "session.mcp_servers_loaded", "data": {"servers": [
                {"name": "github-mcp-server", "status": "disabled"}]}},
            {"type": "model.call_start"},
        ]
        self.usage = {"modelMetrics": {"claude-sonnet-5": {"requests": {"count": 1}}}}

    def test_corrected_exact_vector_is_accepted(self):
        validate_invocation(self.argv)
        self.assertEqual(self.argv[1:3], ["--available-tools", "__benchmark_no_tools__"])
        self.assertNotIn("--deny-tool", self.argv)
        self.assertTrue(audit(self.events, self.usage, self.argv)["control_valid"])

    def test_original_empty_allowlist_is_rejected(self):
        argv = self.argv.copy()
        argv[1:3] = ["--available-tools="]
        with self.assertRaisesRegex(ValueError, "Unisolated"):
            validate_invocation(argv)

    def test_missing_each_isolation_flag_is_rejected(self):
        for flag in ("--disable-builtin-mcps", "--disable-mcp-server",
                     "--no-custom-instructions", "--no-bash-env", "--no-auto-update"):
            with self.subTest(flag=flag):
                argv = self.argv.copy()
                argv.remove(flag)
                with self.assertRaises(ValueError):
                    validate_invocation(argv)

    def test_rejected_wildcard_deny_vector_cannot_be_launched(self):
        argv = self.argv.copy()
        argv[3:3] = ["--deny-tool", "*"]
        with self.assertRaises(ValueError):
            validate_invocation(argv)

    def test_native_tool_call_invalidates_control(self):
        events = self.events + [{"type": "tool.execution_start"}]
        self.assertFalse(audit(events, self.usage, self.argv)["control_valid"])

    def test_unexpected_mcp_or_missing_inventory_invalidates_control(self):
        for events in (
            [{"type": "model.call_start"}],
            self.events + [{"type": "session.mcp_servers_loaded", "data": {
                "servers": [{"name": "unknown", "status": "ready"}]}}],
        ):
            self.assertFalse(audit(events, self.usage, self.argv)["control_valid"])

    def test_missing_or_multiple_requests_invalidates_control(self):
        for count in (0, 2, True, None):
            usage = {"modelMetrics": {"claude-sonnet-5": {"requests": {"count": count}}}}
            self.assertFalse(audit(self.events, usage, self.argv)["control_valid"])
        self.assertFalse(audit(self.events, None, self.argv)["control_valid"])
        self.assertFalse(audit(self.events * 2, self.usage, self.argv)["control_valid"])

    def test_timeout_and_exit_failure_invalidate_control(self):
        self.assertFalse(audit(self.events, self.usage, self.argv, timed_out=True)["control_valid"])
        self.assertFalse(audit(self.events, self.usage, self.argv, exit_code=1)["control_valid"])

    def test_budget_includes_canary_and_blocks_unknown_spend(self):
        row = {"audit": {"control_valid": True, "finalized_requests": 1}}
        self.assertEqual(headroom([row]), 15)
        self.assertEqual(headroom([row] * 15), 1)
        for ledger in ([row] * 16, [{"status": "started"}],
                       [{"audit": {"control_valid": False, "finalized_requests": 1}}]):
            with self.assertRaises(ValueError):
                headroom(ledger)

    def test_batch_stops_on_first_invalid_cell(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            ledger = [{"task": "complex", "arm": "bare",
                       "audit": {"control_valid": True, "finalized_requests": 1}}]
            (root / "generation-ledger.json").write_text(json.dumps(ledger))
            from benchmarks.verified_2026.tasks import ARMS, TASKS
            for task in TASKS:
                (root / task).mkdir()
                for arm in ARMS:
                    (root / task / f"{arm}.txt").write_text("synthetic")
            with patch("benchmarks.verified_2026.isolated.run_one") as run, \
                    patch("benchmarks.verified_2026.isolated.score"):
                run.return_value = {"audit": {"control_valid": False, "finalized_requests": None}}
                self.assertFalse(remaining(root, root, pathlib.Path("copilot")))
                self.assertEqual(run.call_count, 1)

    def test_batch_rejects_unverified_canary_before_spawn(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "generation-ledger.json").write_text("[]")
            with patch("benchmarks.verified_2026.isolated.run_one") as run:
                with self.assertRaises(ValueError):
                    remaining(root, root, pathlib.Path("copilot"))
                run.assert_not_called()

    def test_response_contract_rejects_prose_and_fences(self):
        answer = json.dumps({"solution": "class Ledger: pass", "tests": "", "explanation": ""})
        for text, valid in ((answer, True), ("Done.\n" + answer, False),
                            ("```json\n" + answer + "\n```", False)):
            raw = json.dumps({"type": "assistant.message", "data": {"content": text}})
            self.assertEqual(response_contract(raw), valid)

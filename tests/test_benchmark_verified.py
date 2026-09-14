"""Focused guard tests for the private reproducible benchmark suite."""
import inspect
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from benchmarks.verified_2026 import hidden, reference, run, tasks
from benchmarks.verified_2026.correction import TARGETS, recover


class BenchmarkScoringTests(unittest.TestCase):
    def test_reference_passes_complex(self):
        score = hidden.evaluate(inspect.getsource(reference), "complex")
        self.assertEqual((score["passed"], score["total"]), (8, 8))
        self.assertTrue(score["all_correct"])

    def test_reference_passes_super_complex(self):
        score = hidden.evaluate(inspect.getsource(reference), "super_complex")
        self.assertEqual((score["passed"], score["total"]), (9, 9))
        self.assertTrue(score["all_correct"])

    def test_constant_ledger_rejected(self):
        score = hidden.evaluate(
            "class Ledger:\n"
            " def __init__(self, balances): self.balances = balances\n"
            " def snapshot(self): return self.balances\n"
            " def apply(self, operations): return [True for x in operations]\n", "complex")
        self.assertFalse(score["all_correct"])
        self.assertLess(score["passed"], score["total"])

    def test_missing_rollback_rejected(self):
        source = inspect.getsource(reference).replace(
            "balances, history, result = dict(self.balances), dict(self.history), []",
            "balances, history, result = self.balances, self.history, []")
        score = hidden.evaluate(source, "complex")
        self.assertFalse(score["all_correct"])
        self.assertTrue(any("rolls_back" in row["test"] for row in score["failures"]))

    def test_wrong_expiry_rejected(self):
        source = inspect.getsource(reference).replace(
            "event[0] > now - self.window", "event[0] >= now - self.window")
        score = hidden.evaluate(source, "super_complex")
        self.assertFalse(score["all_correct"])
        self.assertTrue(any("exact_boundary" in row["test"] for row in score["failures"]))

    def test_denied_partial_record_rejected(self):
        source = inspect.getsource(reference).replace("if allowed:\n", "if True:\n")
        self.assertFalse(hidden.evaluate(source, "super_complex")["all_correct"])

    def test_unsafe_import_blocked(self):
        with self.assertRaises(ValueError):
            hidden.validate_source("import os\nos.remove('anything')")

    def test_future_annotations_allowed(self):
        hidden.validate_source("from __future__ import annotations\nx: int = 1")

    def test_unsafe_builtin_blocked(self):
        for source in ["open('file')", "eval('1')", "getattr(object, 'x')", "x.__class__"]:
            with self.subTest(source=source), self.assertRaises(ValueError):
                hidden.validate_source(source)

    def test_no_negative_partial_failure_scores(self):
        source = inspect.getsource(reference).replace("self.balances = dict(balances)", "self.balances = {}")
        score = hidden.evaluate(source, "complex")
        self.assertGreaterEqual(score["passed"], 0)
        self.assertLessEqual(score["passed"], score["total"])

    def test_failed_subtests_count_once_per_method(self):
        source = inspect.getsource(reference).replace(
            'raise ValueError("invalid operation values")', "return []")
        score = hidden.evaluate(source, "complex")
        self.assertGreaterEqual(score["passed"], 0)
        failures = {row["test"].split(" (")[0] for row in score["failures"]}
        self.assertGreaterEqual(len(failures), 1)


class BenchmarkProtocolTests(unittest.TestCase):
    def test_correction_targets_only_authorized_cells(self):
        self.assertEqual(TARGETS, (
            ("complex", "super_ponytail_nocaveman"),
            ("super_complex", "super_ponytail_nocaveman"),
            ("super_complex", "super")))

    def test_correction_recovers_complete_python_fence(self):
        raw = json.dumps({"type": "assistant.message", "data": {
            "content": "```python\nclass Ledger:\n    value = 1\n```\nExplanation."}})
        answer, source = recover(raw, "complex")
        self.assertIn("class Ledger:", answer["solution"])
        self.assertIn("JSON-only contract remains false", source)

    def test_correction_does_not_recover_partial_python_fence(self):
        raw = json.dumps({"type": "assistant.message", "data": {
            "content": "```python\nclass Ledger:\n    value = 1\n"}})
        with self.assertRaises(ValueError):
            recover(raw, "complex")

    def test_report_metrics_mask_without_erasing_history(self):
        original = [{"input_tokens": 123, "output_tokens": 45, "cost_usd": 0.4}]
        result = run.reporting_rows(original)
        self.assertEqual(original[0]["input_tokens"], 123)
        self.assertIsNone(result[0]["input_tokens"])
        self.assertIsNone(result[0]["output_tokens"])
        self.assertIsNone(result[0]["cost_usd"])

    def test_graph_title_and_axis_carry_scope_label(self):
        path = Mock()
        run.svg_chart(path, "Tokens", [("cell", None)], "tokens")
        text = path.write_text.call_args.args[0]
        self.assertIn("<title>PROMPT-ONLY SYNTHETIC", text)
        self.assertIn("PROMPT-ONLY SYNTHETIC | axis: tokens", text)
        self.assertIn("null / unavailable", text)

    def test_coding_fails_closed_without_model_calls(self):
        with (patch.object(run, "prepare"), patch.object(run, "save"),
              patch("subprocess.run") as execute):
            result = run.coding(Path("evidence"), "copilot", 12)
        execute.assert_not_called()
        self.assertEqual(result["model_calls_started"], 0)
        self.assertEqual(result["status"], "blocked-before-execution")

    def test_eight_arms_two_tasks(self):
        """Eight, not six. graphify and super_graphify were added when graphify
        became rule 1 of the installed pipeline: an arm that ships enforced on
        every prompt has to be measurable, and super_graphify is the pairing the
        repository actually ships. The count is asserted so a ninth arm is a
        decision rather than a drift, and uniqueness is asserted because a
        duplicated name would silently halve a cell's sample."""
        self.assertEqual(len(tasks.ARMS), 8)
        self.assertEqual(len(tasks.TASKS), 2)
        self.assertEqual(len(set(tasks.ARMS)), 8)
        self.assertIn("graphify", tasks.ARMS)
        self.assertIn("super_graphify", tasks.ARMS)

    def test_common_safety_every_arm(self):
        for arm in tasks.ARMS:
            prompt = tasks.compose("complex", arm, "SUPER", "PONY", "CAVE")
            self.assertTrue(prompt.startswith(tasks.COMMON))
            self.assertIn(tasks.TASKS["complex"], prompt)

    def test_exact_ablations(self):
        context = "plan\nCaveman instructions\nverify"
        full = tasks.compose("complex", "super_ponytail_caveman", context, "PONY", "CAVE")
        removed = tasks.compose("complex", "super_ponytail_nocaveman", context, "PONY", "CAVE")
        self.assertIn("Caveman instructions", full)
        self.assertIn("CAVE", full)
        self.assertNotIn("Caveman instructions", removed)
        self.assertNotIn("CAVE", removed)
        self.assertIn("PONY", removed)
        self.assertIn("plan\nverify", removed)

    def test_bare_has_no_extra_context(self):
        prompt = tasks.compose("complex", "bare", "SUPER", "PONY", "CAVE")
        self.assertEqual(prompt, tasks.COMMON + "\n\n" + tasks.TASKS["complex"])

    def test_super_ablation_preserves_non_caveman_clauses(self):
        plain = tasks.remove_caveman(run.SUPER_PROXY)
        self.assertIn("finish with completed work and explicit limitations.", plain)
        self.assertNotIn("Caveman:", plain)
        self.assertNotIn("terse explanation only", plain)

    def test_two_harder_transfer_prompts(self):
        self.assertEqual(set(tasks.TRANSFER), set(tasks.TASKS))
        for name in tasks.TASKS:
            self.assertGreater(len(tasks.TRANSFER[name]), len(tasks.TASKS[name]))
            self.assertIn(tasks.TASKS[name], tasks.TRANSFER[name])

    def test_extract_jsonl_answer(self):
        answer = {"solution": "answer = 42", "tests": "", "explanation": "done"}
        raw = json.dumps({"type": "assistant.message", "data": {"content": json.dumps(answer)}})
        self.assertEqual(run.extract_answer(raw), answer)

    def test_recover_complete_fenced_answer_after_prose(self):
        answer = {"solution": "answer = 42", "tests": "", "explanation": "done"}
        raw = json.dumps({"type": "assistant.message", "data": {
            "content": "I completed this task.\n\n```json\n" + json.dumps(answer) + "\n```"}})
        self.assertEqual(run.extract_answer(raw), answer)

    def test_unclosed_fence_is_not_complete_response(self):
        raw = json.dumps({"type": "assistant.message", "data": {
            "content": 'Prose.\n```json\n{"solution":"answer = 42"}'}})
        with self.assertRaises(ValueError):
            run.extract_answer(raw)

    def test_streaming_delta_is_not_final_answer(self):
        raw = json.dumps({"type": "assistant.message_delta", "data": {
            "deltaContent": '{"solution":"answer = 42"}'}})
        with self.assertRaises(ValueError):
            run.extract_answer(raw)

    def test_missing_answer_is_failure(self):
        with self.assertRaises(ValueError):
            run.extract_answer('{"type":"session.error","data":{}}')

    def test_capture_preserves_exact_bytes_and_status(self):
        process = type("Result", (), {"stdout": b"a\r\n", "stderr": b"\xfferror\n", "returncode": 3})()
        with patch("subprocess.run", return_value=process):
            row = run.capture(["fixture"], ".")
        self.assertEqual(bytes.fromhex(row["stdout_hex"]), process.stdout)
        self.assertEqual(bytes.fromhex(row["stderr_hex"]), process.stderr)
        self.assertEqual(row["exit_code"], 3)
        self.assertEqual(row["stdout_bytes"], 3)

    def test_usage_preserves_real_counts_not_price(self):
        usage = {"currentModel": "observed-model", "totalPremiumRequestCost": 1,
                 "tokenDetails": {"input": {"tokenCount": 2}},
                 "modelMetrics": {"observed-model": {"usage": {
                     "inputTokens": 100, "outputTokens": 50,
                     "cacheReadTokens": 20, "cacheWriteTokens": 78}}}}
        row = run.usage_metrics(usage)
        self.assertEqual(row["input_tokens"], 100)
        self.assertEqual(row["output_tokens"], 50)
        self.assertEqual(row["uncached_input_tokens"], 2)
        self.assertIsNone(row["cost_usd"])
        self.assertIsNone(row["rate_provenance"])

    def test_missing_usage_not_zero(self):
        row = run.usage_metrics({})
        self.assertIsNone(row["input_tokens"])
        self.assertIsNone(row["output_tokens"])
        self.assertIsNone(row["model"])


if __name__ == "__main__":
    unittest.main()

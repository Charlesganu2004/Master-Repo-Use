"""The A/B script: exact measurement, and a baseline that refuses to lie.

The script's value is two claims. --measure reports the exact bytes each arm
injects, from the real context functions, without touching this machine's goal
or limit. --run never reports a comparison whose "without" arm was secretly
harnessed. Both are tested here without a model: the measured bytes against the
functions themselves, and the probe with a fake backend that answers YES.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "hooks"))

import harness_ab_test as ab  # noqa: E402
import harness_super  # noqa: E402
import skill_pipeline  # noqa: E402


class Measure(unittest.TestCase):
    def test_arms_are_exact_bytes_of_the_real_contexts(self):
        result = ab.measure(ab.DEFAULT_PROMPT)
        with skill_pipeline.isolated_store():
            base = skill_pipeline.context_for(ab.DEFAULT_PROMPT, capturing=False, mode="base")
            sup = harness_super.context_for(ab.DEFAULT_PROMPT, capturing=False)
        arms = result["arms"]
        self.assertEqual(arms["without"]["injectedBytes"], 0)
        self.assertEqual(arms["base"]["injectedBytes"], len(base.encode("utf-8")))
        self.assertEqual(arms["super"]["injectedBytes"], len(sup.encode("utf-8")))
        prompt = len(ab.DEFAULT_PROMPT.encode("utf-8"))
        for arm in arms.values():
            self.assertEqual(arm["totalInputBytes"], arm["injectedBytes"] + prompt)
            self.assertEqual(arm["estimatedInputTokens"],
                             round(arm["totalInputBytes"] / ab.BYTES_PER_TOKEN_ESTIMATE))

    def test_super_carries_the_base_layers_and_the_chain(self):
        arms = ab.measure(ab.HARDER_PROMPT)["arms"]
        self.assertGreater(arms["super"]["injectedBytes"], arms["base"]["injectedBytes"])
        with skill_pipeline.isolated_store():
            sup = harness_super.context_for(ab.HARDER_PROMPT, capturing=False)
        self.assertIn("Standing pipeline", sup)
        self.assertIn("S10.", sup)

    def test_the_estimate_is_labelled_as_one(self):
        self.assertIn("NOT a tokenizer count", ab.measure("x" * 40)["note"])

    def test_measuring_sets_no_goal_and_no_limit_on_this_machine(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(__import__("os").environ, MASTER_REPO_GOAL_DIR=tmp)
            subprocess.run([sys.executable, str(ROOT / "scripts" / "harness_ab_test.py"),
                            "--measure", "--prompt", "/token limit 900 goal: measure me please"],
                           cwd=ROOT, env=env, capture_output=True, text=True, check=True)
            self.assertEqual(list(pathlib.Path(tmp).iterdir()), [],
                             "measuring wrote a goal, a limit or a mode into the store")

    def test_measure_writes_json_when_asked(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "harness_ab_test.py"),
                 "--measure", "--harder", "--out", tmp],
                cwd=ROOT, capture_output=True, text=True, check=True)
            data = json.loads((pathlib.Path(tmp) / "measure.json").read_text(encoding="utf-8"))
            self.assertEqual(data["prompt"], ab.HARDER_PROMPT)
            self.assertIn("est. tokens", proc.stdout)


class Features(unittest.TestCase):
    def test_counts_are_countable_properties(self):
        text = ("Plan:\n1. parse\n```python\ndef test_x():\n    assert f('1h') == 3600\n```\n"
                "Not handled: leap seconds. Uses master-caveman \u2014 oops.")
        got = ab.features(text)
        self.assertEqual(got["codeBlocks"], 1)
        self.assertEqual(got["emDashes"], 1)
        self.assertTrue(got["hasTests"])
        self.assertTrue(got["statesPlan"])
        self.assertTrue(got["namesSkills"])
        self.assertTrue(got["statesWhatIsLeft"])
        self.assertFalse(ab.features("just prose")["hasTests"])


class Baseline(unittest.TestCase):
    """--run must refuse a contaminated baseline instead of reporting it."""

    def setUp(self):
        self.calls = []
        self.original = dict(ab.BACKENDS)

    def tearDown(self):
        ab.BACKENDS.clear()
        ab.BACKENDS.update(self.original)

    def fake(self, probe_answer):
        def call(prompt, system, model, workdir):
            self.calls.append((prompt, system))
            text = probe_answer if prompt == ab.PROBE else "```python\nassert True\n```"
            return {"inputTokens": 10 + len(system), "cacheCreationTokens": 0, "cacheReadTokens": 0,
                    "outputTokens": 5, "costUsd": None, "seconds": 0.0, "text": text}
        return call

    def test_a_baseline_that_sees_the_pipeline_stops_the_run(self):
        ab.BACKENDS["claude"] = self.fake("YES")
        with self.assertRaises(ab.BackendUnavailable) as caught:
            ab.run(ab.DEFAULT_PROMPT, "claude", None)
        self.assertIn("NOT clean", str(caught.exception))
        self.assertEqual(len(self.calls), 1, "no arm may run after a failed probe")

    def test_a_clean_baseline_runs_both_arms_and_only_super_gets_the_harness(self):
        ab.BACKENDS["claude"] = self.fake("NO")
        result = ab.run(ab.DEFAULT_PROMPT, "claude", None)
        self.assertEqual(result["probe"], "clean")
        (_, probe_system), (_, bare_system), (_, super_system) = self.calls
        self.assertEqual(probe_system, "")
        self.assertEqual(bare_system, "")
        self.assertIn("Standing pipeline", super_system)
        self.assertEqual(result["arms"]["without"]["injectedBytes"], 0)
        self.assertTrue(result["arms"]["super"]["features"]["hasTests"])
        self.assertEqual(len(ab.summary_lines(result)), 9)

    def test_the_raw_api_needs_no_probe(self):
        ab.BACKENDS["api"] = self.fake("YES")
        result = ab.run(ab.DEFAULT_PROMPT, "api", None)
        self.assertEqual(len(self.calls), 2)
        self.assertIn("not needed", result["probe"])

    def test_no_api_key_is_reported_not_crashed(self):
        env = {k: v for k, v in __import__("os").environ.items() if k != "ANTHROPIC_API_KEY"}
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "harness_ab_test.py"), "--run", "--backend", "api"],
            cwd=ROOT, env=env, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 3)
        self.assertIn("ANTHROPIC_API_KEY is not set", proc.stderr)


if __name__ == "__main__":
    unittest.main()

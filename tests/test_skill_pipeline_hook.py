"""The standing pipeline has to fire without anyone typing a slash.

Charles asked why using a skill needs `/name`. It does not, and the distinction
is worth pinning in a test because it is easy to lose:

  a slash command   is EXPLICIT invocation, and always runs
  a skill           is MODEL-INVOCABLE, and runs when the model judges it fits
  a UserPromptSubmit hook  runs on EVERY prompt, before the model reads it

Only the third is deterministic. The first two both depend on somebody deciding,
and the one turn where it matters is the turn nobody thought to decide.

The other half of this file is the cost. This text is prepended to every prompt
in every session forever, so the core stays short and the lane lines only attach
when the prompt is actually that kind of work. A test that lets the injected
block grow without bound would recreate exactly the always-loaded bloat that
docs/auto-mode-block.txt already has a budget for.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOOK = ROOT / "scripts" / "hooks" / "skill_pipeline.py"
INSTALLER = (ROOT / "scripts" / "install_auto_mode.py").read_text(encoding="utf-8")

sys.path.insert(0, str(ROOT / "scripts" / "hooks"))
import skill_pipeline as pipeline  # noqa: E402


def run(prompt: str) -> str:
    """The hook's additionalContext for a prompt, or '' when it stays silent."""
    event = json.dumps({"input": {"prompt": prompt}})
    proc = subprocess.run([sys.executable, str(HOOK)], input=event,
                          capture_output=True, text=True)
    if proc.returncode != 0 or not proc.stdout.strip():
        return ""
    return json.loads(proc.stdout)["hookSpecificOutput"]["additionalContext"]


class ItFiresOnEveryOrdinaryPrompt(unittest.TestCase):
    def test_a_plain_prompt_gets_the_core_rules(self):
        out = run("fix the flaky test in the retry module")
        self.assertTrue(out, "the hook emitted nothing for an ordinary prompt")
        for rule in ("caveman", "Never compact a skill", "Full output", "Verify before claiming"):
            self.assertIn(rule, out, f"the core is missing: {rule}")

    def test_the_event_name_is_the_one_the_client_expects(self):
        event = json.dumps({"input": {"prompt": "hello"}})
        proc = subprocess.run([sys.executable, str(HOOK)], input=event,
                              capture_output=True, text=True)
        payload = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(payload["hookEventName"], "UserPromptSubmit")

    def test_it_reads_a_prompt_at_either_nesting(self):
        """Clients have shipped both shapes; accepting one only is a silent no-op."""
        for event in ({"input": {"prompt": "build a thing"}}, {"prompt": "build a thing"}):
            proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event),
                                  capture_output=True, text=True)
            self.assertTrue(proc.stdout.strip(), f"no output for {event}")


class ItStaysQuietWhenItShould(unittest.TestCase):
    def test_a_slash_command_is_left_alone(self):
        """The user already named what they want. Injecting competes with it."""
        self.assertEqual(run("/brandkit make me a board"), "")
        self.assertEqual(run("  /code-review high"), "")

    def test_an_empty_prompt_produces_nothing(self):
        self.assertEqual(run("   "), "")

    def test_a_malformed_event_never_breaks_the_session(self):
        proc = subprocess.run([sys.executable, str(HOOK)], input="not json",
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")


class TheLanesAttachOnlyWhenRelevant(unittest.TestCase):
    """Each conditional line costs nothing on the turns it does not apply to."""

    def test_ui_work_pulls_in_the_design_rules(self):
        out = run("redo the landing page css and make the layout cooler")
        self.assertIn("design taste skills", out)
        self.assertIn("no em dashes", out)

    def test_adding_a_dependency_pulls_in_the_audit_rule(self):
        out = run("add this npm package to the project")
        self.assertIn("dep-audit", out)

    def test_a_question_about_current_facts_demands_retrieval(self):
        out = run("what is the latest model pricing")
        self.assertIn("retrieve it, do not recall it", out)

    def test_security_work_demands_quotable_evidence(self):
        out = run("scan this repo for a vulnerability")
        self.assertIn("evidence that can be quoted", out)

    def test_an_unrelated_prompt_gets_no_lane_line(self):
        out = run("rename this variable")
        self.assertNotIn("5.", out, "a lane attached to a prompt it does not fit")

    def test_only_one_lane_ever_attaches(self):
        """Stacking them would defeat the budget on any broad prompt."""
        out = run("install the css design package and scan it for secrets")
        self.assertEqual(out.count("\n5."), 1)


class ItAsksForFanOutOnlyOnBigPrompts(unittest.TestCase):
    def test_a_short_single_task_prompt_does_not(self):
        self.assertNotIn("fan them out", run("rename this variable"))

    def test_a_multi_part_prompt_does(self):
        out = run("add the parser. Also wire the CLI. And then update the docs, plus tests.")
        self.assertIn("fan them out", out)

    def test_a_long_prompt_does(self):
        self.assertIn("fan them out", run("x " * 400))


class TheInjectedBlockStaysCheap(unittest.TestCase):
    """Charged on every prompt of every session, so it needs a ceiling."""

    def test_the_core_is_small(self):
        self.assertLess(len(pipeline.CORE.encode("utf-8")), 800,
                        "the always-injected core is growing; move detail into a skill")

    def test_the_worst_case_is_still_small(self):
        worst = max(len(run(p).encode("utf-8")) for p in (
            "redo the css landing page design " + "x " * 400,
            "install an npm package and also scan it, plus update docs",
        ))
        self.assertLess(worst, 1400, "the worst-case injection is too large per turn")


class TheInstallerRegistersIt(unittest.TestCase):
    def test_it_binds_to_the_prompt_event_not_a_tool_event(self):
        self.assertIn('"skill_pipeline": ("UserPromptSubmit", None)', INSTALLER)

    def test_the_prompt_hook_carries_no_tool_matcher(self):
        """A matcher on UserPromptSubmit would silently never fire."""
        self.assertIn("if matcher:", INSTALLER)

    def test_the_guards_still_bind_to_pretooluse_on_bash(self):
        self.assertIn('"no_prune_guard": ("PreToolUse", "Bash")', INSTALLER)
        self.assertIn('"no_compress_guard": ("PreToolUse", "Bash")', INSTALLER)

    def test_all_three_are_installed(self):
        self.assertIn('ALL_HOOKS = GUARDS + ("skill_pipeline",)', INSTALLER)


if __name__ == "__main__":
    unittest.main()

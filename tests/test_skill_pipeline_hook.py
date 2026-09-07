"""The standing pipeline has to fire without anyone typing a slash.

Charles asked why using a skill needs `/name`. It does not, and the distinction
is worth pinning in a test because it is easy to lose:

  a slash command   is EXPLICIT invocation, and always runs
  a skill           is MODEL-INVOCABLE, and runs when the model judges it fits
  a UserPromptSubmit hook  runs on EVERY prompt, before the model reads it

Only the third is deterministic. The first two both depend on somebody deciding,
and the one turn where it matters is the turn nobody thought to decide.

The other half of this file is the cost. This text is prepended to every prompt
in every session forever. Seven mandatory rules is about 1.2 kB, call it 290
tokens a turn; that price was quoted to Charles and accepted, so the ceiling
here exists to make the NEXT addition a decision rather than a drift. The four
lanes stay conditional on top of the core, because a lane firing on a prompt it
does not fit is noise rather than enforcement.
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
    MANDATORY = ("PLAN first", "CAVEMAN", "DESIGN", "ANTI-SLOP",
                 "FULL OUTPUT", "NEVER COMPACT", "VERIFY")

    def test_a_plain_prompt_gets_every_mandatory_rule(self):
        """All seven, unconditionally. Charles asked for these on every prompt
        and every conversation across chat, cowork and code, was told the
        per-turn cost, and confirmed. Nothing here is allowed to be conditional
        on the prompt looking like the right kind of work."""
        out = run("fix the flaky test in the retry module")
        self.assertTrue(out, "the hook emitted nothing for an ordinary prompt")
        for rule in self.MANDATORY:
            self.assertIn(rule, out, f"the mandatory core is missing: {rule}")

    def test_the_mandatory_core_survives_a_prompt_about_nothing(self):
        """The worst case for a conditional design rule is a prompt with no
        design words in it, which is exactly when it used to vanish."""
        out = run("what time is it")
        for rule in self.MANDATORY:
            self.assertIn(rule, out, f"{rule} dropped out on an unrelated prompt")

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


class ItFiresOnCommandsToo(unittest.TestCase):
    def test_a_slash_command_gets_the_pipeline_too(self):
        """Reversed deliberately. The first version skipped slash commands on
        the reasoning that the user had already said what they wanted. The
        instruction here is "every command has this too", and a /command is
        exactly where a design or full-output rule most needs to hold."""
        for command in ("/brandkit make me a board", "  /code-review high"):
            out = run(command)
            self.assertTrue(out, f"{command} got no pipeline")
            self.assertIn("FULL OUTPUT", out)
            self.assertIn("ANTI-SLOP", out)

    def test_an_empty_prompt_produces_nothing(self):
        self.assertEqual(run("   "), "")

    def test_a_malformed_event_never_breaks_the_session(self):
        proc = subprocess.run([sys.executable, str(HOOK)], input="not json",
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")


class TheLanesAttachOnlyWhenRelevant(unittest.TestCase):
    """Each conditional line costs nothing on the turns it does not apply to."""

    def test_ui_work_adds_the_audit_rule_on_top_of_the_mandatory_design_one(self):
        """The design and anti-slop rules moved into the unconditional core, so
        the UI lane now carries only what is specific to UI: audit before
        replacing, and name the aesthetic rather than defaulting."""
        out = run("redo the landing page css and make the layout cooler")
        self.assertIn("audit the existing surface", out)
        self.assertIn("DESIGN.", out)            # from the core, not the lane
        self.assertIn("No em dashes anywhere", out)

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
        self.assertNotIn("8.", out, "a lane attached to a prompt it does not fit")

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

    def test_the_core_is_tracked_not_unbounded(self):
        """Seven mandatory rules is roughly 1.2 kB, call it 290 tokens a prompt.
        That price was quoted and accepted. The ceiling exists so the next
        addition is a decision rather than a drift."""
        self.assertLess(len(pipeline.CORE.encode("utf-8")), 1400,
                        "the always-injected core grew past what was agreed")

    def test_the_worst_case_stays_bounded(self):
        worst = max(len(run(p).encode("utf-8")) for p in (
            "redo the css landing page design " + "x " * 400,
            "install an npm package and also scan it, plus update docs",
        ))
        self.assertLess(worst, 1900, "the worst-case injection is too large per turn")


class ItServesAntigravityToo(unittest.TestCase):
    """Antigravity is the only other client verified to have a real hook, so it
    is the only other one where these rules are enforced rather than merely
    written down. Its schema differs in three ways that each fail silently if
    assumed, so each is pinned here.

    One hook script serves both clients on purpose. A second file holding the
    same rules for Antigravity would drift from this one, and the entire point
    is that every client gets the SAME standing pipeline.
    """

    def ag(self, event: dict) -> dict:
        proc = subprocess.run([sys.executable, str(HOOK), "--antigravity"],
                              input=json.dumps(event), capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        return json.loads(proc.stdout) if proc.stdout.strip() else {}

    def test_it_emits_the_injectsteps_shape_not_the_claude_shape(self):
        out = self.ag({"input": {"prompt": "build a thing"}})
        self.assertIn("injectSteps", out)
        self.assertNotIn("hookSpecificOutput", out)

    def test_the_context_rides_as_an_ephemeral_message(self):
        """ephemeralMessage reaches the model for this invocation without being
        recorded as something the user said."""
        step = self.ag({"input": {"prompt": "build a thing"}})["injectSteps"][0]
        self.assertIn("ephemeralMessage", step)
        self.assertIn("PLAN first", step["ephemeralMessage"])

    def test_it_reads_the_last_user_message_from_a_trajectory(self):
        """PreInvocation hands over a trajectory, not a single prompt field."""
        out = self.ag({"messages": [
            {"role": "user", "content": "an older thing"},
            {"role": "assistant", "content": "done"},
            {"role": "user", "content": "scan this for a vulnerability"}]})
        self.assertIn("evidence that can be quoted", out["injectSteps"][0]["ephemeralMessage"])

    def test_it_reads_a_content_part_array(self):
        out = self.ag({"messages": [{"role": "user", "content": [{"text": "redo the css layout"}]}]})
        self.assertIn("audit the existing surface", out["injectSteps"][0]["ephemeralMessage"])

    def test_both_clients_receive_identical_rules(self):
        prompt = "refactor the parser"
        claude = run(prompt)
        antigravity = self.ag({"input": {"prompt": prompt}})["injectSteps"][0]["ephemeralMessage"]
        self.assertEqual(claude, antigravity, "the two clients drifted apart")


class TheInstallerRegistersAntigravity(unittest.TestCase):
    """Every one of these was read from the vendor docs, not assumed."""

    def test_it_writes_the_documented_path(self):
        self.assertIn('".gemini" / "config" / "hooks.json"', INSTALLER)

    def test_it_uses_preinvocation_not_userpromptsubmit(self):
        """Antigravity has no UserPromptSubmit. Binding to one would never fire."""
        self.assertIn('entry["PreInvocation"]', INSTALLER)

    def test_preinvocation_carries_no_matcher(self):
        """The docs are explicit that the matcher is ignored for this event."""
        block = INSTALLER[INSTALLER.index("def register_antigravity_hook"):]
        block = block[:block.index("def main")]
        self.assertNotIn('"matcher"', block)

    def test_the_entry_is_keyed_by_hook_name_at_the_top_level(self):
        self.assertIn('data.setdefault("master-repo-pipeline", {})', INSTALLER)

    def test_it_passes_the_antigravity_flag(self):
        self.assertIn("--antigravity", INSTALLER)

    def test_it_backs_up_before_overwriting(self):
        block = INSTALLER[INSTALLER.index("def register_antigravity_hook"):]
        self.assertIn('with_suffix(".json.bak")', block[:block.index("def main")])

    def test_it_refuses_rather_than_clobber_unreadable_json(self):
        block = INSTALLER[INSTALLER.index("def register_antigravity_hook"):]
        self.assertIn("REFUSED", block[:block.index("def main")])


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

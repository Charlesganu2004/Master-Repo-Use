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
import os
import pathlib
import subprocess
import tempfile
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOOK = ROOT / "scripts" / "hooks" / "skill_pipeline.py"
INSTALLER = (ROOT / "scripts" / "install_auto_mode.py").read_text(encoding="utf-8")

sys.path.insert(0, str(ROOT / "scripts" / "hooks"))
import skill_pipeline as pipeline  # noqa: E402


def installer_function(name: str) -> str:
    """Return one installer function, without accidentally scanning later ones."""
    body = INSTALLER[INSTALLER.index(f"def {name}("):]
    stop = body.find("\n\ndef ", 1)
    return body if stop < 0 else body[:stop]


# The hook now CAPTURES a goal from the prompt, so running it writes state.
# Without this every test run would append a fixture goal to the real store,
# which is exactly how the previous store reached 168 kB of test goals.
GOAL_STORE = tempfile.mkdtemp(prefix="pipeline-goal-")


def hook_env() -> dict:
    env = dict(os.environ)
    env["MASTER_REPO_GOAL_DIR"] = GOAL_STORE
    return env


def run(prompt: str, goal_dir: str | None = None) -> str:
    """The hook's additionalContext for a prompt, or '' when it stays silent.

    `goal_dir` overrides the shared store. Any test whose RESULT depends on the
    goal state has to pass one, because the shared store makes that result
    depend on which test ran first. The budget test did not, and passed only in
    file order: an earlier test had already captured a short goal, so the long
    prompt never became the goal and the worst case was never measured.
    """
    event = json.dumps({"input": {"prompt": prompt}})
    env = hook_env()
    if goal_dir is not None:
        env["MASTER_REPO_GOAL_DIR"] = goal_dir
    proc = subprocess.run([sys.executable, str(HOOK)], input=event,
                          capture_output=True, text=True, env=env)
    if proc.returncode != 0 or not proc.stdout.strip():
        return ""
    return json.loads(proc.stdout)["hookSpecificOutput"]["additionalContext"]


# One probe per lane, each long enough to also pull in the orchestration line.
# Keyed by lane so a new lane with no probe fails the count assertion below
# rather than quietly going unmeasured.
LANE_PROBES = {
    "security": "scan this repo for a vulnerability and a leaked credential",
    "computer": "playwright browser automation screenshot the gui and the keyboard",
    "ui": "redo the css landing page design layout theme and typography",
    "refactor": "refactor the duplicated dead code and reduce the technical debt",
    "install": "install an npm package dependency from the marketplace",
    "changes": "what is the latest model pricing version released today",
    "graph": "orient in this unfamiliar codebase and build a knowledge graph to trace the path between two modules",
}


class ItFiresOnEveryOrdinaryPrompt(unittest.TestCase):
    MANDATORY = ("CAVEMAN", "FULL OUTPUT", "ANTI-SLOP", "PLAN", "DESIGN",
                 "CAPABILITIES", "AGENTS AND ACTIONS", "RE-APPLY LAYER 1",
                 "NEVER COMPACT", "VERIFY")

    def test_a_plain_prompt_gets_every_mandatory_rule(self):
        """All ten, unconditionally. Charles asked for these on every prompt
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

    def test_it_arrives_as_three_named_layers(self):
        """Charles asked for layers, not a list, and the shape is the point:
        one pass before the request is read, one before anything is produced,
        and a third while acting."""
        out = run("do some work")
        for layer in ("LAYER 1, before reading the request",
                      "LAYER 2, before producing anything",
                      "LAYER 3, while acting and again before answering"):
            self.assertIn(layer, out, f"missing: {layer}")
        self.assertLess(out.index("LAYER 1"), out.index("LAYER 2"))
        self.assertLess(out.index("LAYER 2"), out.index("LAYER 3"))

    def test_layer_three_reapplies_layer_one(self):
        """A rule read once at the top of a long turn has stopped applying by
        the end of it, and the end is where the skeleton gets written."""
        out = run("build something long")
        self.assertIn("RE-APPLY LAYER 1", out)
        self.assertIn("caveman, full output, anti-slop, again", out)

    def test_layer_three_forces_capability_selection(self):
        """The difference between having a catalog and using one."""
        out = run("do some work")
        self.assertIn("CAPABILITIES", out)
        for word in ("skills", "tools", "plugins", "MCP servers"):
            self.assertIn(word, out, f"{word} is not in the forced selection")
        self.assertIn("name what you picked", out)

    def test_the_event_name_is_the_one_the_client_expects(self):
        event = json.dumps({"input": {"prompt": "hello"}})
        proc = subprocess.run([sys.executable, str(HOOK)], input=event,
                              capture_output=True, text=True, env=hook_env())
        payload = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(payload["hookEventName"], "UserPromptSubmit")

    def test_it_reads_a_prompt_at_either_nesting(self):
        """Clients have shipped both shapes; accepting one only is a silent no-op."""
        for event in ({"input": {"prompt": "build a thing"}}, {"prompt": "build a thing"}):
            proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event),
                                  capture_output=True, text=True, env=hook_env())
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
                              capture_output=True, text=True, env=hook_env())
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
        self.assertIn("DESIGN.", out)            # from layer 2, not the lane
        self.assertIn("No em dashes.", out)      # from layer 1

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
        """12, not 11. Layer 3 gained REFACTOR as rule 8 when the refactor
        skills went in, so the mandatory core now runs to 11 and the conditional
        lane line is 12. Asserting the old number would have passed forever
        while testing nothing, since 11 is now always present."""
        out = run("say hello")
        self.assertIn("11. VERIFY", out, "the core should still end at 11")
        self.assertNotIn("12.", out, "a lane attached to a prompt it does not fit")

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
        """Eleven mandatory rules in three layers is roughly 1.9 kB, call it 480
        tokens a prompt. That price was quoted and accepted. The ceiling exists
        so the next addition is a decision rather than a drift, and this is the
        ledger of the decisions:

            1900 bytes   ten rules, the original three layers
            2000 bytes   2026-09-09: rule 8, REFACTOR, in layer 3. About 300
                         bytes. Asked for directly, and placed in layer 3
                         because a refactor is something done to what was just
                         written rather than something planned in advance.
            2200 bytes   2026-09-14: graphify placed ahead of caveman in rule 1,
                         about 90 bytes. Asked for directly. The graph answers a
                         code question for a fraction of the tokens a whole-file
                         read costs, so it belongs first in layer 1 rather than
                         in a lane that only attaches when the prompt happens to
                         mention a codebase. Paying 90 bytes on every prompt to
                         avoid whole-file reads on the ones that touch code is
                         the trade, and it is a decision rather than a drift.
        """
        self.assertLess(len(pipeline.CORE.encode("utf-8")), 2200,
                        "the always-injected core grew past what was agreed")

    def test_every_lane_has_a_probe_so_none_goes_unmeasured(self):
        """A lane with no probe is a lane whose cost nobody measures. Adding one
        without a probe should fail here rather than pass silently and blow the
        budget in production."""
        self.assertEqual(len(LANE_PROBES), len(pipeline.LANES),
                         "a lane was added or removed without updating LANE_PROBES")

    def test_the_worst_case_stays_bounded(self):
        """The ceiling, and the ledger of what each rise bought.

            2400 bytes   core, one lane, and the orchestration line
            2600 bytes   2026-09-08: the standing goal block, about 544 bytes
            3000 bytes   2026-09-09: REFACTOR in the core, plus the goal block's
                         origin sentence. This number was WRONG, see below.
            3600 bytes   2026-09-10: the real worst case, measured properly, is
                         3464 bytes. The 3000 above was never true; the test
                         passed only because of the order it ran in.
            3700 bytes   2026-09-14: graphify leads rule 1, about 200 bytes, and
                         the core rides every lane so every lane pays it. Bought
                         deliberately: a graph query answers a code question for
                         a fraction of what a whole-file read costs, so the rise
                         is meant to be repaid many times over on any prompt that
                         touches code. The conditional graph lane was trimmed of
                         what rule 1 now states, so the net rise is 200 rather
                         than 400, and the worst lane is refactor at 3648.

        WHY THE OLD NUMBER WAS WRONG, because it is the more useful half of this
        ledger. run() used one module-level store shared by the whole file, so
        by the time this test executed an earlier test had already captured a
        short goal. The long probe prompt therefore never became the goal, the
        goal block stayed small, and the worst case was never measured. Run on
        its own the same assertion failed at 3286. Measured properly, against a
        goal at the truncation cap and across every lane rather than two ad-hoc
        prompts, it is 3464: the refactor lane added in that same commit is the
        longest of the six, so the real cost went up by more than the ceiling
        was raised.

        The goal block rides only while a goal is set, so an ordinary session
        pays nothing for it. It is counted in the worst case anyway, because a
        session with a goal is the case this repository is usually in and a
        budget that excludes the normal case is not a budget.
        """
        with tempfile.TemporaryDirectory() as store:
            # A goal past the 400-character truncation cap, which makes the goal
            # block as large as it can ever be. Set explicitly, so capture
            # cannot replace it with one of the probe prompts mid-measurement.
            subprocess.run([sys.executable, str(ROOT / "scripts" / "harness_goal.py"),
                            "--set", "z" * 900],
                           capture_output=True, cwd=ROOT,
                           env={**os.environ, "MASTER_REPO_GOAL_DIR": store})

            sizes = {}
            for lane, probe in LANE_PROBES.items():
                # Padded so the orchestration line attaches too: worst case
                # means every conditional piece present at once.
                text = run(f"{probe} " + "x " * 400, goal_dir=store)
                self.assertIn("STANDING GOAL", text,
                              f"the {lane} probe measured no goal block")
                sizes[lane] = len(text.encode("utf-8"))

        worst_lane = max(sizes, key=sizes.get)
        self.assertLess(sizes[worst_lane], 3700,
                        f"the worst-case injection is too large per turn: "
                        f"{worst_lane} lane at {sizes[worst_lane]} bytes")


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
                              input=json.dumps(event), capture_output=True, text=True, env=hook_env())
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
        self.assertIn("LAYER 1, before reading the request", step["ephemeralMessage"])

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


class ItServesCursorAndCopilotToo(unittest.TestCase):
    def mode(self, flag: str, event: dict) -> dict:
        proc = subprocess.run([sys.executable, str(HOOK), flag],
                              input=json.dumps(event), capture_output=True, text=True, env=hook_env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.strip(), f"{flag} emitted no context")
        return json.loads(proc.stdout)

    def test_cursor_uses_its_documented_additional_context_key(self):
        prompt = "refactor the parser"
        out = self.mode("--cursor", {"prompt": prompt})
        self.assertEqual(set(out), {"additional_context"})
        self.assertEqual(out["additional_context"], run(prompt))

    def test_copilot_session_uses_camel_case_additional_context(self):
        out = self.mode("--copilot-session", {})
        self.assertEqual(set(out), {"additionalContext"})
        self.assertIn("LAYER 1, before reading the request", out["additionalContext"])
        self.assertIn("LAYER 3, while acting", out["additionalContext"])

    def test_copilot_session_does_not_need_a_user_prompt_to_fire(self):
        out = self.mode("--copilot-session", {"source": "startup"})
        self.assertIn("CAVEMAN", out["additionalContext"])

    def test_copilot_transform_uses_prompt_and_preserves_transformed_prompt(self):
        original = "Refactor the parser and keep its public API."
        out = self.mode("--copilot-transform", {
            "prompt": "redo the landing page css",
            "transformedPrompt": original,
        })
        self.assertEqual(set(out), {"modifiedTransformedPrompt"})
        transformed = out["modifiedTransformedPrompt"]
        self.assertTrue(
            transformed.startswith("MASTER REPO AUTO MODE APPLIED\n"),
            "the idempotency marker must be the first line",
        )
        self.assertIn("LAYER 1, before reading the request", transformed)
        self.assertIn("LAYER 3, while acting", transformed)
        self.assertIn("audit the existing surface", transformed,
                      "the original prompt did not select its UI lane")
        self.assertIn(original, transformed,
                      "the already-transformed user request was discarded")

    def test_copilot_transform_does_not_stack_the_pipeline(self):
        first = self.mode("--copilot-transform", {
            "prompt": "build it", "transformedPrompt": "build it"
        })[
            "modifiedTransformedPrompt"
        ]
        second = self.mode("--copilot-transform", {
            "prompt": "build it", "transformedPrompt": first,
        })
        self.assertEqual(second, {}, "an already-marked prompt was rewritten again")
        self.assertEqual(first.count("MASTER REPO AUTO MODE APPLIED\n"), 1)

    def test_gemini_uses_before_agent_additional_context(self):
        out = self.mode("--gemini", {"prompt": "redo the landing page css"})
        self.assertEqual(set(out), {"hookSpecificOutput"})
        hook = out["hookSpecificOutput"]
        self.assertEqual(hook.get("hookEventName"), "BeforeAgent")
        self.assertIn("LAYER 1, before reading the request", hook["additionalContext"])
        self.assertIn("audit the existing surface", hook["additionalContext"])

    def test_gemini_empty_session_still_receives_the_mandatory_core(self):
        out = self.mode("--gemini", {})["hookSpecificOutput"]
        self.assertEqual(out.get("hookEventName"), "BeforeAgent")
        self.assertIn("CAVEMAN", out["additionalContext"])


class TheInstallerRegistersAntigravity(unittest.TestCase):
    """Every one of these was read from the vendor docs, not assumed."""

    def test_it_writes_the_documented_path(self):
        self.assertIn('".gemini" / "config" / "hooks.json"', INSTALLER)

    def test_it_uses_preinvocation_not_userpromptsubmit(self):
        """Antigravity has no UserPromptSubmit. Binding to one would never fire."""
        self.assertIn('entry["PreInvocation"]', INSTALLER)

    def test_preinvocation_carries_no_matcher(self):
        """The docs are explicit that the matcher is ignored for this event."""
        block = installer_function("register_antigravity_hook")
        self.assertNotIn('"matcher"', block)

    def test_the_entry_is_keyed_by_hook_name_at_the_top_level(self):
        self.assertIn('data.setdefault("master-repo-pipeline", {})', INSTALLER)

    def test_it_passes_the_antigravity_flag(self):
        self.assertIn("--antigravity", INSTALLER)

    def test_it_backs_up_before_overwriting(self):
        block = installer_function("register_antigravity_hook")
        self.assertIn('with_suffix(".json.bak")', block)

    def test_it_refuses_rather_than_clobber_unreadable_json(self):
        block = installer_function("register_antigravity_hook")
        self.assertIn("REFUSED", block)


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

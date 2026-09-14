"""/token limit, super mode on every prompt, and one copy of the goal.

Three things landed together, and each closes a gap between what the super
harness was said to do and what it did.

SUPER MODE. The chain reached a model only through harness_super --run, --serve
or --context. The per-prompt hook, which is what every Claude Code, Codex,
Gemini, Cursor and Copilot session actually runs, had never heard of it. So in
the sessions that matter most, the super harness had never fired. It now reads a
mode stored beside the goal state; super mode appends the chain on every prompt.

/TOKEN LIMIT. The one command the super harness keeps. It needs an explicit
marker so a question ABOUT token limits never caps its own answer, it persists
per session, and through the proxy it becomes a real max_tokens.

ONE GOAL. harness_goal rendered the pipeline, which already carried the goal,
then appended its own detailed goal block: the goal text twice on every
goal-carrying prompt. Found by a verification pass that measured the bytes.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "hooks"))

import skill_pipeline as sp  # noqa: E402
import super_chain  # noqa: E402
import harness_goal  # noqa: E402
import harness_super  # noqa: E402
import harness_proxy  # noqa: E402
import auto_mode_harness  # noqa: E402

BACKSLASH = chr(92)


class IsolatedStore(unittest.TestCase):
    """Every test here gets its own goal, token and mode store."""

    def setUp(self):
        store = sp.isolated_store()
        store.__enter__()
        self.addCleanup(store.__exit__, None, None, None)
        previous = os.environ.pop("MASTER_HARNESS_MODE", None)
        if previous is not None:
            self.addCleanup(os.environ.__setitem__, "MASTER_HARNESS_MODE", previous)


class TheCommandNeedsItsMarker(unittest.TestCase):
    def test_every_documented_spelling_sets_it(self):
        for text, expected in (("/token limit 4000", 4000),
                               (BACKSLASH + "token limit 4000", 4000),
                               ("/tokenlimit 4k", 4000),
                               ("/token-limit 2.5k", 2500),
                               ("/token_limit 5,000", 5000),
                               ("token limit: 1200", 1200),
                               ("/token limit 1m", 1_000_000)):
            action, value, _rest = sp.parse_token_command(text)
            self.assertEqual((action, value), ("set", expected), text)

    def test_off_and_its_synonyms_lift_it(self):
        for word in ("off", "clear", "none", "lift", "reset"):
            self.assertEqual(sp.parse_token_command(f"/token limit {word}")[0], "clear", word)

    def test_a_question_about_token_limits_sets_nothing(self):
        """Without the marker requirement this would silently cap the answer to
        the very question being asked."""
        for prose in ("what is the token limit 200000 on opus?",
                      "set the tokenlimit to 5 please",
                      "the token limit: is it per turn?",
                      "a/token limit 50"):
            self.assertIsNone(sp.parse_token_command(prose)[0], prose)

    def test_the_command_is_removed_from_the_request(self):
        action, value, rest = sp.parse_token_command("/token limit 3000 refactor the loader")
        self.assertEqual((action, value, rest), ("set", 3000, "refactor the loader"))

    def test_absurd_values_are_bounded(self):
        self.assertEqual(sp.parse_token_command("/token limit 99999999999")[1],
                         sp.TOKEN_LIMIT_MAX)
        self.assertEqual(sp.parse_token_command("/token limit 0")[0], "clear")


class ItPersistsTheWayTheGoalDoes(IsolatedStore):
    def test_a_session_keeps_its_limit_for_later_prompts(self):
        sp.context_for("/token limit 3000 refactor the loader", "claude:a")
        self.assertIn("TOKEN LIMIT: 3,000", sp.context_for("now review it", "claude:a"))

    def test_another_session_does_not_inherit_it(self):
        sp.context_for("/token limit 3000 refactor the loader", "claude:a")
        self.assertNotIn("TOKEN LIMIT", sp.context_for("hello there friend", "claude:b"))

    def test_a_global_limit_reaches_every_session(self):
        sp.save_token_limit(4000)
        self.assertIn("TOKEN LIMIT: 4,000", sp.context_for("explain it", "claude:new"))

    def test_a_session_that_lifted_it_is_not_overridden_by_the_global_one(self):
        """Someone who typed /token limit off in their conversation should not
        find it quietly reinstated by a global limit."""
        sp.save_token_limit(4000)
        sp.context_for("/token limit off", "claude:a")
        self.assertNotIn("TOKEN LIMIT", sp.context_for("explain it", "claude:a"))

    def test_without_a_session_it_applies_to_that_prompt_only(self):
        self.assertIn("TOKEN LIMIT: 900", sp.context_for("/token limit 900 write a poem"))
        self.assertNotIn("TOKEN LIMIT", sp.context_for("write another poem please"))

    def test_the_command_never_becomes_the_standing_goal(self):
        sp.context_for("/token limit 3000 refactor the retry loader module", "claude:a")
        goal = sp.load_goal("claude:a").get("goal") or ""
        self.assertNotIn("/token", goal)
        self.assertIn("refactor the retry loader module", goal)


class TheRuleTellsTheTruthAboutEnforcement(IsolatedStore):
    def test_the_block_plans_to_fit_and_names_what_was_left_out(self):
        block = sp.token_block(2000)
        for phrase in ("Plan to fit before writing", "last clean break",
                       "what was left out", "/token limit off"):
            self.assertIn(phrase, block)

    def test_it_only_claims_a_hard_stop_where_one_exists(self):
        self.assertIn("hard stop", sp.token_block(2000, enforced=True))
        self.assertNotIn("hard stop", sp.token_block(2000, enforced=False))
        self.assertIn("advisory", sp.token_block(2000, enforced=False))
        self.assertIn("not a total-token", sp.token_block(2000, enforced=True))


class TheProxyEnforcesItForReal(IsolatedStore):
    def body(self, text, **extra):
        return {"model": "m", "messages": [{"role": "user", "content": text}], **extra}

    def test_an_openai_request_gets_max_tokens(self):
        out, _ = harness_proxy.inject(self.body("/token limit 800 write"), "/v1/chat/completions")
        self.assertEqual(out["max_tokens"], 800)

    def test_it_lowers_but_never_raises_a_callers_limit(self):
        out, _ = harness_proxy.inject(self.body("/token limit 800 go", max_tokens=300),
                                      "/v1/chat/completions")
        self.assertEqual(out["max_tokens"], 300)

    def test_the_newer_openai_field_is_respected(self):
        out, _ = harness_proxy.inject(self.body("/token limit 800 go", max_completion_tokens=5000),
                                      "/v1/chat/completions")
        self.assertEqual(out["max_completion_tokens"], 800)
        self.assertNotIn("max_tokens", out)

    def test_ollama_gets_num_predict_and_nothing_openai_shaped(self):
        out, _ = harness_proxy.inject(self.body("/token limit 800 go"), "/api/chat")
        self.assertEqual(out["options"]["num_predict"], 800)
        self.assertNotIn("max_tokens", out)

    def test_an_openai_request_never_gets_ollama_options(self):
        """OpenAI rejects unrecognised request arguments. The first draft added
        `options` to every request, which would have broken every OpenAI call
        through the proxy the moment anyone set a limit."""
        out, _ = harness_proxy.inject(self.body("/token limit 800 go"), "/v1/chat/completions")
        self.assertNotIn("options", out)

    def test_no_limit_changes_nothing(self):
        out, _ = harness_proxy.inject(self.body("write a haiku"), "/v1/chat/completions")
        self.assertNotIn("max_tokens", out)
        self.assertNotIn("options", out)


class SuperModeReachesEveryPrompt(IsolatedStore):
    def test_base_is_the_default(self):
        self.assertEqual(sp.harness_mode(), "base")
        self.assertNotIn("SUPER HARNESS", sp.context_for("refactor it", "claude:a"))

    def test_super_mode_puts_the_chain_on_the_hooks_prompt(self):
        """The gap this closes: the hook every client runs never carried it."""
        sp.set_harness_mode("super")
        self.assertIn("SUPER HARNESS", sp.context_for("refactor it", "claude:a"))

    def test_the_real_hook_process_carries_it_in_super_mode(self):
        with tempfile.TemporaryDirectory() as store:
            env = {**os.environ, "MASTER_REPO_GOAL_DIR": store}
            env.pop("MASTER_HARNESS_MODE", None)
            pathlib.Path(store, "mode.json").write_text('{"mode": "super"}', encoding="utf-8")
            event = json.dumps({"input": {"prompt": "refactor the loader", "session_id": "x"}})
            proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "hooks" / "skill_pipeline.py")],
                                  input=event, capture_output=True, text=True, env=env)
            context = json.loads(proc.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("SUPER HARNESS", context)

    def test_the_environment_overrides_the_file_for_one_invocation(self):
        sp.set_harness_mode("super")
        os.environ["MASTER_HARNESS_MODE"] = "base"
        self.addCleanup(os.environ.pop, "MASTER_HARNESS_MODE", None)
        self.assertNotIn("SUPER HARNESS", sp.context_for("refactor it", "claude:a"))

    def test_a_check_cannot_flip_a_real_machine(self):
        """The mode lives beside the goal state, so isolation covers it too."""
        sp.set_harness_mode("super")
        with sp.isolated_store():
            self.assertEqual(sp.harness_mode(), "base")

    def test_an_invalid_mode_is_refused(self):
        with self.assertRaises(ValueError):
            sp.set_harness_mode("turbo")


class TheGoalAppearsOnce(IsolatedStore):
    GOAL = "ship the standalone package and verify every client"

    def setUp(self):
        super().setUp()
        sp.set_goal(self.GOAL, source="explicit")

    def test_the_goal_harness_carries_the_goal_text_once(self):
        out = harness_goal.context_for("refactor the loader", capturing=False)
        self.assertEqual(out.count(self.GOAL), 1)

    def test_the_super_harness_carries_it_once_and_the_chain_after_it(self):
        out = harness_super.context_for("refactor the loader", capturing=False)
        self.assertEqual(out.count(self.GOAL), 1)
        self.assertLess(out.index(self.GOAL), out.index("SUPER HARNESS"))

    def test_the_hook_in_super_mode_carries_it_once(self):
        sp.set_harness_mode("super")
        out = sp.context_for("refactor the loader", "claude:a")
        self.assertEqual(out.count(self.GOAL), 1)


class OneCopyOfTheChain(unittest.TestCase):
    def test_the_super_harness_re_exports_rather_than_redefines(self):
        self.assertIs(harness_super.PASSES, super_chain.PASSES)
        self.assertIs(harness_super.super_block, super_chain.super_block)

    def test_the_hook_does_not_import_the_whole_harness_to_render_it(self):
        """super_chain has no imports beyond the standard library, so the hook
        can load it on every prompt without loading five harnesses."""
        source = (ROOT / "scripts" / "hooks" / "super_chain.py").read_text(encoding="utf-8")
        self.assertNotIn("import harness_", source)
        self.assertNotIn("import auto_mode_harness", source)

    def test_the_wheel_carries_it(self):
        self.assertIn('"super_chain.py"', (ROOT / "setup.py").read_text(encoding="utf-8"))

    def test_the_chain_points_at_the_long_procedure(self):
        self.assertIn("master-super-harness", super_chain.super_block())
        self.assertIn("master-super-harness", super_chain.EXTRA_SKILLS)
        self.assertTrue((ROOT / "skills" / "master-super-harness" / "SKILL.md").is_file())


class ChatSurfacesGetTheChainToo(unittest.TestCase):
    def test_a_super_bundle_carries_the_chain_the_limit_and_the_procedure(self):
        """A chat product has no hook, so the bundle is the whole enforcement.
        `harness_super --bundle` used to write the base bundle."""
        bundle = auto_mode_harness.build_bundle("chatgpt", mode="super")
        self.assertIn("SUPER HARNESS", bundle)
        self.assertIn("/token limit", bundle)
        self.assertIn("### master-super-harness", bundle)

    def test_a_base_bundle_stays_base(self):
        bundle = auto_mode_harness.build_bundle("chatgpt")
        self.assertNotIn("SUPER HARNESS", bundle)


class TheSuperHarnessCommands(unittest.TestCase):
    def run_super(self, *args, store):
        env = {**os.environ, "MASTER_REPO_GOAL_DIR": store}
        env.pop("MASTER_HARNESS_MODE", None)
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "harness_super.py"), *args],
                              capture_output=True, text=True, env=env, cwd=ROOT, timeout=120)

    def test_mode_can_be_shown_set_and_reset(self):
        with tempfile.TemporaryDirectory() as store:
            self.assertIn("mode: base", self.run_super("--mode", "show", store=store).stdout)
            self.run_super("--mode", "super", store=store)
            self.assertIn("mode: super", self.run_super("--mode", "show", store=store).stdout)
            self.run_super("--mode", "base", store=store)
            self.assertIn("mode: base", self.run_super("--mode", "show", store=store).stdout)

    def test_a_global_limit_can_be_set_and_lifted(self):
        with tempfile.TemporaryDirectory() as store:
            self.assertIn("4,000", self.run_super("--token-limit", "4k", store=store).stdout)
            self.assertIn("lifted", self.run_super("--token-limit", "off", store=store).stdout)

    def test_a_dry_run_install_does_not_flip_the_mode(self):
        with tempfile.TemporaryDirectory() as store:
            out = self.run_super("--install", "all", "--dry-run", store=store)
            self.assertIn("would set mode: super", out.stdout)
            self.assertIn("mode: base", self.run_super("--mode", "show", store=store).stdout)


class TheSiteTellsPeopleAboutIt(unittest.TestCase):
    """A feature nobody can find on the page is a feature nobody uses."""

    def setUp(self):
        root = ROOT
        data = json.loads((root / "designs" / "atlas-data.json").read_text(encoding="utf-8"))
        self.chain = data["pipeline"]["superChain"]
        self.atlas = (root / "atlas.js").read_text(encoding="utf-8")
        self.panes = (root / "designs" / "atlas-panes.js").read_text(encoding="utf-8")

    def test_every_advertised_spelling_parses(self):
        spellings = self.chain["tokenLimit"]["spellings"]
        self.assertGreaterEqual(len(spellings), 4)
        for spelling in spellings:
            with self.subTest(spelling=spelling):
                action, _value, _rest = sp.parse_token_command(spelling)
                self.assertIn(action, ("set", "clear"))

    def test_the_rule_shown_is_the_rule_injected(self):
        self.assertEqual(self.chain["tokenLimit"]["rule"],
                         sp.token_block(2000, enforced=False))

    def test_mode_commands_are_real_flags(self):
        commands = [entry["command"] for entry in self.chain["modeCommands"]]
        self.assertIn("python scripts/harness_super.py --mode super", commands)
        self.assertIn("python scripts/harness_super.py --token-limit off", commands)

    def test_both_pages_render_it(self):
        for name, body in (("atlas.js", self.atlas), ("atlas-panes.js", self.panes)):
            with self.subTest(page=name):
                self.assertIn("tokenLimit", body)
                self.assertIn("modeCommands", body)
                self.assertIn("The one thing you type: /token limit", body)


if __name__ == "__main__":
    unittest.main()

"""Four harnesses, and the differences between them are the point.

Charles asked for the harness described, three more like it, and a fourth that
adds a goal enforcing the harness itself in every prompt.

The failure this file guards against is the four collapsing into one. They inject
the same three layers, so it is tempting to treat them as variants of a single
tool. They are not: each stands in a different place, and where a harness stands
decides what it can reach. A surface harness cannot touch a program that is
already running. A proxy cannot reach a browser tab. A wrapper covers one
invocation. The goal harness is the only one that survives the turn.

So the tests hold the boundaries, and hold that each one states its own limit,
because a harness that advertises a capability it does not have is worse than one
that admits the gap.
"""
import json
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "hooks"))

import auto_mode_harness as surface  # noqa: E402
import harness_proxy as proxy  # noqa: E402
import harness_wrap as wrap  # noqa: E402
import harness_goal as goal  # noqa: E402
import skill_pipeline as pipeline  # noqa: E402

DATA = json.loads((ROOT / "designs" / "atlas-data.json").read_text(encoding="utf-8"))
HARNESSES = DATA.get("harnesses", [])
CORE_JS = (ROOT / "designs" / "atlas-core.js").read_text(encoding="utf-8")
PANES_JS = (ROOT / "designs" / "atlas-panes.js").read_text(encoding="utf-8")

SCRIPTS = {
    "auto-mode-harness": "scripts/auto_mode_harness.py",
    "harness-proxy": "scripts/harness_proxy.py",
    "harness-wrap": "scripts/harness_wrap.py",
    "harness-goal": "scripts/harness_goal.py",
}


def run_check(script: str):
    return subprocess.run([sys.executable, str(ROOT / script), "--check"],
                          cwd=ROOT, capture_output=True, text=True)


class AllFourExistAndCheckThemselves(unittest.TestCase):
    def test_there_are_four(self):
        self.assertEqual(len(HARNESSES), 4)

    def test_each_one_is_a_real_file(self):
        for harness in HARNESSES:
            self.assertTrue((ROOT / harness["file"]).is_file(),
                            f"{harness['name']} names a file that does not exist")

    def test_every_declared_file_is_one_of_the_four_scripts(self):
        declared = {h["file"] for h in HARNESSES}
        self.assertEqual(declared, set(SCRIPTS.values()))

    def test_each_one_passes_its_own_check(self):
        """Run, not read. A check that is only asserted to exist proves nothing."""
        for script in SCRIPTS.values():
            result = run_check(script)
            self.assertEqual(result.returncode, 0,
                             f"{script} --check failed:\n{result.stdout}\n{result.stderr}")

    def test_the_check_command_on_the_card_is_the_one_that_works(self):
        for harness in HARNESSES:
            self.assertIn("--check", harness["check"])
            self.assertIn(harness["file"], harness["check"],
                          f"{harness['name']} shows a check for a different file")

    def test_each_one_states_what_it_cannot_do(self):
        """A harness that advertises a capability it does not have is worse than
        one that admits the gap, because the gap is invisible until it matters."""
        for harness in HARNESSES:
            self.assertGreater(len(harness["limit"]), 40,
                               f"{harness['name']} does not say what it cannot do")
            self.assertGreater(len(harness["useWhen"]), 15,
                               f"{harness['name']} does not say when to reach for it")

    def test_no_em_or_en_dashes_in_the_harness_copy(self):
        blob = json.dumps(HARNESSES, ensure_ascii=False)
        self.assertNotIn("—", blob)
        self.assertNotIn("–", blob)


class TheyStandInDifferentPlaces(unittest.TestCase):
    def test_the_proxy_covers_what_the_surface_harness_cannot(self):
        """The surface harness says it cannot reach a program already running.
        That is precisely the proxy's case, and the two descriptions have to
        agree or one of them is wrong."""
        by_id = {h["id"]: h for h in HARNESSES}
        self.assertIn("already running", by_id["auto-mode-harness"]["limit"])
        self.assertIn("cannot configure", by_id["harness-proxy"]["useWhen"])

    def test_the_proxy_does_not_claim_to_cover_untouched_traffic(self):
        by_id = {h["id"]: h for h in HARNESSES}
        self.assertIn("routed through it", by_id["harness-proxy"]["limit"])

    def test_the_wrapper_is_scoped_to_one_invocation(self):
        by_id = {h["id"]: h for h in HARNESSES}
        self.assertIn("One invocation", by_id["harness-wrap"]["limit"])

    def test_only_the_goal_harness_claims_to_survive_the_turn(self):
        survives = [h for h in HARNESSES if "turn" in h["detail"].lower()]
        self.assertEqual([h["id"] for h in survives], ["harness-goal"])


class TheProxyInjectsWithoutDamagingTheRequest(unittest.TestCase):
    def test_it_puts_the_rules_ahead_of_the_conversation(self):
        payload, changed = proxy.inject(
            {"model": "m", "messages": [{"role": "user", "content": "plan a page"}]})
        self.assertTrue(changed)
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertIn("LAYER 1", payload["messages"][0]["content"])

    def test_it_keeps_the_callers_own_system_message(self):
        """Theirs is theirs. Ours frames it, rather than replacing it."""
        payload, _ = proxy.inject({"model": "m", "messages": [
            {"role": "system", "content": "You are terse."},
            {"role": "user", "content": "hi"}]})
        self.assertEqual(len(payload["messages"]), 3)
        self.assertEqual(payload["messages"][1]["content"], "You are terse.")

    def test_a_second_pass_does_not_stack_another_copy(self):
        once, _ = proxy.inject({"model": "m", "messages": [{"role": "user", "content": "x"}]})
        twice, changed = proxy.inject(once)
        self.assertFalse(changed)
        self.assertEqual(len(twice["messages"]), 2)

    def test_an_unrecognised_payload_is_passed_through_untouched(self):
        original = {"model": "m", "input": "some other API"}
        payload, changed = proxy.inject(dict(original))
        self.assertFalse(changed)
        self.assertEqual(payload, original)

    def test_it_never_writes_prompts_to_a_log(self):
        body = (ROOT / "scripts" / "harness_proxy.py").read_text(encoding="utf-8")
        self.assertIn("does not log prompts", body)
        self.assertIn("def log_message", body,
                      "the default handler logs the request line, which can carry a prompt")

    def test_it_warns_when_bound_off_loopback(self):
        body = (ROOT / "scripts" / "harness_proxy.py").read_text(encoding="utf-8")
        self.assertIn("open relay", body)


class TheWrapperIsTransparent(unittest.TestCase):
    def test_every_mode_gets_the_rules_to_the_tool(self):
        for name in wrap.PROFILES:
            argv, stdin_text, env = wrap.build(name, "do the thing", ["tool", "{prompt}"], None) \
                if wrap.PROFILES[name]["mode"] != "file" else (None, None, None)
            if argv is None:
                continue
            blob = " ".join(argv) + (stdin_text or "") + " ".join(env.values())
            self.assertIn("LAYER 1", blob, f"{name} did not carry the rules")

    def test_the_prompt_still_ends_up_in_the_command(self):
        argv, _, _ = wrap.build("generic", "UNIQUEPROMPT", ["tool", "--p", "{prompt}"], None)
        self.assertIn("UNIQUEPROMPT", argv[2])

    def test_an_unverified_profile_would_say_so(self):
        body = (ROOT / "scripts" / "harness_wrap.py").read_text(encoding="utf-8")
        self.assertIn("UNVERIFIED", body)
        self.assertIn("has not been checked against a real", body)

    def test_the_wrapped_exit_code_is_not_swallowed(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "harness_wrap.py"),
             "--profile", "generic", "--prompt", "x",
             "--", sys.executable, "-c", "raise SystemExit(7)"],
            capture_output=True)
        self.assertEqual(result.returncode, 7)


class TheGoalSurvivesTheTurn(unittest.TestCase):
    def setUp(self):
        self.original = goal.load_goal().get("goal")
        self.addCleanup(self.restore)

    def restore(self):
        if self.original:
            goal.set_goal(self.original)
        else:
            goal.clear_goal()

    def test_every_spelling_sets_it(self):
        """People type all three. A rule that depends on remembering a slash is
        not a rule, which is the whole reason this system exists."""
        for text in ("/goal ship it", "\\goal ship it", "goal: ship it", "goal ship it"):
            parsed = goal.parse_command(text)
            self.assertEqual(parsed, ("set", "ship it"), f"{text!r} did not set the goal")

    def test_clear_is_recognised(self):
        for text in ("/goal clear", "\\goal off", "goal: none"):
            self.assertEqual(goal.parse_command(text)[0], "clear", text)

    def test_a_sentence_about_goals_is_not_a_command(self):
        self.assertIsNone(goal.parse_command("what is the goal of this repository?"))
        self.assertIsNone(goal.parse_command("my goal is to finish the designs"))

    def test_no_goal_means_no_goal_block(self):
        goal.clear_goal()
        self.assertNotIn("STANDING GOAL", goal.context_for("anything"))

    def test_a_set_goal_rides_every_prompt(self):
        goal.set_goal("finish the designs")
        context = goal.context_for("add a settings page")
        self.assertIn("STANDING GOAL", context)
        self.assertIn("finish the designs", context)

    def test_the_layers_come_before_the_goal(self):
        """The goal says what the session is for; the layers say how a turn is
        done. A goal without the layers is an intention."""
        goal.set_goal("finish the designs")
        context = goal.context_for("x")
        self.assertLess(context.index("LAYER 1"), context.index("STANDING GOAL"))

    def test_the_hook_carries_the_goal_too_so_no_command_is_needed(self):
        """The point of a goal harness is that the goal arrives automatically.
        If only harness_goal.py injected it, you would have to remember to use
        harness_goal.py, which is the habit being removed."""
        goal.set_goal("finish the designs")
        self.assertIn("STANDING GOAL", pipeline.context_for("add a page"))

    def test_the_hook_survives_a_missing_or_broken_goal_file(self):
        """This runs on every prompt of every client. A half-written save must
        cost the turn nothing."""
        original = goal.GOAL_FILE.read_text(encoding="utf-8") if goal.GOAL_FILE.is_file() else None
        try:
            goal.GOAL_FILE.write_text("{ not json", encoding="utf-8")
            self.assertEqual(pipeline.standing_goal(), "")
            self.assertIn("LAYER 1", pipeline.context_for("x"))
        finally:
            if original is not None:
                goal.GOAL_FILE.write_text(original, encoding="utf-8")

    def test_a_very_long_goal_is_bounded(self):
        goal.set_goal("x" * 5000)
        block = pipeline.standing_goal()
        # The template is about 530 bytes and the goal is capped at 400, so a
        # bounded block lands near 930. The number matters less than the fact
        # that a 5000 character goal cannot ride every prompt unbounded.
        self.assertLess(len(block), 1000)
        self.assertLess(len(block), len("x" * 5000))
        self.assertIn("truncated", block)

    def test_the_previous_goal_is_kept_rather_than_lost(self):
        goal.set_goal("first goal")
        goal.set_goal("second goal")
        history = " ".join(entry.get("goal", "") for entry in goal.load_goal()["history"])
        self.assertIn("first goal", history)

    def test_the_skill_documents_both_slashes(self):
        skill = (ROOT / "skills" / "master-goal" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("/goal", skill)
        self.assertIn("\\goal", skill)
        self.assertIn("goal:", skill)

    def test_only_the_person_who_set_it_lifts_it(self):
        for source in (goal.GOAL_BLOCK, pipeline.GOAL_TEMPLATE):
            self.assertIn("compaction pass", source)
            self.assertIn("token budget", source)


class TheHarnessIsReachableInEveryDesign(unittest.TestCase):
    def test_the_shared_shell_offers_a_harness_tab(self):
        self.assertIn("id: 'harness'", CORE_JS)
        self.assertIn("function harnessHTML()", PANES_JS)
        self.assertIn("tab === 'harness' ? harnessHTML()", PANES_JS)

    def test_the_pane_reads_the_payload_rather_than_restating_it(self):
        self.assertIn("A.harnesses()", PANES_JS)
        self.assertIn("function harnesses()", CORE_JS)

    def test_the_pane_shows_the_limit_next_to_the_capability(self):
        pane = PANES_JS[PANES_JS.index("function harnessHTML()"):]
        pane = pane[:pane.index("function routesHTML")]
        self.assertIn("h.limit", pane)
        self.assertIn("h.useWhen", pane)
        self.assertIn("h.check", pane)

    def test_the_check_command_is_copyable(self):
        pane = PANES_JS[PANES_JS.index("function harnessHTML()"):]
        pane = pane[:pane.index("function routesHTML")]
        self.assertIn("data-copy-cmd", pane)

    def test_every_class_the_pane_introduces_has_a_rule(self):
        """Scoped to the classes this pane brings with it.

        The shell has a shared vocabulary, `.empty`, `.sub`, `.grid`,
        `.lane-card`, that each design styles in its own stylesheet or lets fall
        back to plain text. `.empty` alone is used 21 times across the panes and
        styled by 6 of the 30 designs. Asserting those here would be asserting a
        convention this pane did not set. What must not happen is a NEW class
        rendered with no rule anywhere, which is how .cmd-action shipped inert.
        """
        import re
        shared = {"empty", "sub", "grid", "lane-card", "src"}
        pane = PANES_JS[PANES_JS.index("function harnessHTML()"):]
        pane = pane[:pane.index("function routesHTML")]
        names = set()
        for group in re.findall(r'class="([a-z][a-z0-9 -]*)"', pane):
            names |= {n for n in group.split() if n}
        introduced = sorted(names - shared)
        self.assertTrue(introduced, "the pane introduced no classes, which cannot be right")
        for name in introduced:
            self.assertRegex(PANES_JS, r"\." + re.escape(name) + r"\b",
                             f".{name} is rendered with no rule")


if __name__ == "__main__":
    unittest.main()


class TheHarnessOnTheMainPage(unittest.TestCase):
    """The designs get the harness through a shared pane. The main page has its
    own markup, so it needs its own assertions or the two drift apart."""

    def setUp(self):
        self.index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.script = (ROOT / "atlas.js").read_text(encoding="utf-8")
        self.styles = (ROOT / "atlas.css").read_text(encoding="utf-8")

    def test_the_section_exists_and_is_in_the_nav(self):
        self.assertIn('id="harness"', self.index)
        self.assertIn('href="#harness"', self.index)

    def test_it_renders_from_the_payload_rather_than_hard_coded_copy(self):
        body = self.script[self.script.index("function renderHarness()"):]
        body = body[:body.index("function renderStore()")]
        self.assertIn("catalog.data.harnesses", body)
        for field in ("harness.name", "harness.detail", "harness.useWhen",
                      "harness.limit", "harness.check"):
            self.assertIn("escapeHtml(" + field + ")", body, f"{field} is not rendered or not escaped")

    def test_the_renderer_runs_after_the_catalog_loads(self):
        loader = self.script[self.script.index("async function loadCatalog"):]
        loader = loader[:loader.index("function renderCatalogMetrics")]
        self.assertIn("renderHarness()", loader)

    def test_all_three_spellings_are_shown_on_the_page(self):
        body = self.script[self.script.index("function renderHarness()"):]
        body = body[:body.index("function renderStore()")]
        self.assertIn("/goal finish", body)
        self.assertIn("\\goal finish", body)
        self.assertIn("goal: finish", body)

    def test_the_page_says_who_can_lift_the_goal(self):
        section = self.index[self.index.index('id="harness"'):]
        section = section[:section.index('id="store"')]
        self.assertIn("only the person who set it lifts it", section)

    def test_every_class_the_section_introduces_has_a_rule(self):
        import re
        section = self.index[self.index.index('id="harness"'):]
        section = section[:section.index('id="store"')]
        body = self.script[self.script.index("function renderHarness()"):]
        body = body[:body.index("function renderStore()")]
        shared = {"routes-section", "page-shell", "section-heading", "route-heading",
                  "eyebrow", "quiet-button", "out-code"}
        names = set()
        for blob in (section, body):
            for group in re.findall(r'class="([a-z][a-z0-9 -]*)"', blob):
                names |= {n for n in group.split() if n}
        for name in sorted(names - shared):
            self.assertRegex(self.styles, r"\." + re.escape(name) + r"\b",
                             f".{name} is rendered with no rule")

    def test_the_check_commands_do_not_ligate(self):
        """Cascadia turns "--check" into one long dash, and this block exists to
        be retyped."""
        rule = re.search(r"\.harness-check code\s*\{[^}]*\}", self.styles)
        self.assertIsNotNone(rule)
        self.assertIn("font-variant-ligatures: none", rule.group(0))

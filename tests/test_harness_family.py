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
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile
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

INJECTION_SCRIPTS = {
    "auto-mode-harness": "scripts/auto_mode_harness.py",
    "harness-proxy": "scripts/harness_proxy.py",
    "harness-wrap": "scripts/harness_wrap.py",
    "harness-goal": "scripts/harness_goal.py",
    # Last, because the list runs from least to most reach and this one calls
    # the other four rather than standing anywhere new itself.
    "harness-super": "scripts/harness_super.py",
}
COMPUTER_SCRIPT = "scripts/harness_computer.py"


def run_check(script: str):
    return subprocess.run([sys.executable, str(ROOT / script), "--check"],
                          cwd=ROOT, capture_output=True, text=True)


class EveryInjectionHarnessExistsAndChecksItself(unittest.TestCase):
    def test_the_declared_harnesses_are_exactly_the_injection_scripts(self):
        self.assertEqual([h["id"] for h in HARNESSES], list(INJECTION_SCRIPTS))

    def test_every_harness_can_reach_the_agents_and_the_browser(self):
        """Charles asked for computer control, Playwright and agents to be
        reachable from every harness rather than from one of them."""
        for harness in HARNESSES:
            blob = (harness["detail"] + harness["useWhen"] + harness["limit"]).lower()
            self.assertTrue("playwright" in blob or "browser" in blob,
                            f"{harness['name']} does not mention the browser path")
            self.assertIn("agent", blob, f"{harness['name']} does not mention agents")

    def test_every_harness_mentions_the_machine_it_can_reach(self):
        for harness in HARNESSES:
            blob = (harness["detail"] + harness["useWhen"] + harness["limit"]).lower()
            self.assertTrue("computer" in blob or "desktop" in blob or "machine" in blob,
                            f"{harness['name']} does not mention computer control")

    def test_each_one_is_a_real_file(self):
        for harness in HARNESSES:
            self.assertTrue((ROOT / harness["file"]).is_file(),
                            f"{harness['name']} names a file that does not exist")

    def test_every_declared_file_is_one_of_the_injection_scripts(self):
        declared = {h["file"] for h in HARNESSES}
        self.assertEqual(declared, set(INJECTION_SCRIPTS.values()))

    def test_each_one_passes_its_own_check(self):
        """Run, not read. A check that is only asserted to exist proves nothing."""
        for script in INJECTION_SCRIPTS.values():
            result = run_check(script)
            self.assertEqual(result.returncode, 0,
                             f"{script} --check failed:\n{result.stdout}\n{result.stderr}")

    def test_computer_control_is_shared_diagnostic_metadata(self):
        controls = [h.get("computerControl") for h in HARNESSES]
        self.assertTrue(all(controls), "an injection harness lost the shared router")
        self.assertTrue(all(control == controls[0] for control in controls[1:]),
                        "the shared computer-control route drifted between harnesses")
        control = controls[0]
        self.assertEqual(control["kind"], "capability-router")
        self.assertEqual(control["skill"], "master-computer-control")
        self.assertEqual(control["file"], COMPUTER_SCRIPT)
        self.assertEqual(control["check"], "python scripts/harness_computer.py --check")
        self.assertEqual(control["routes"], ["native", "browser-js", "browser-rust"])
        self.assertIn("does not grant tools", control["detail"])

    def test_computer_control_diagnostic_passes_its_own_check(self):
        result = run_check(COMPUTER_SCRIPT)
        self.assertEqual(result.returncode, 0,
                         f"{COMPUTER_SCRIPT} --check failed:\n{result.stdout}\n{result.stderr}")

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
        """Isolate BOTH paths.

        The store has two: the runtime state it writes, and the committed seed
        it falls back to. Redirecting only the first would leave every test
        reading the repository's real goal as its starting state, which passes
        or fails depending on what Charles happened to be working on.
        """
        self.goal_store = tempfile.TemporaryDirectory()
        self.addCleanup(self.goal_store.cleanup)
        self.original_state = pipeline.STATE_FILE
        self.original_seed = pipeline.SEED_FILE
        store = pathlib.Path(self.goal_store.name)
        pipeline.STATE_FILE = store / "goal.json"
        pipeline.SEED_FILE = store / "seed.json"     # deliberately absent
        self.addCleanup(self.restore_goal_paths)

    def restore_goal_paths(self):
        pipeline.STATE_FILE = self.original_state
        pipeline.SEED_FILE = self.original_seed

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
        pipeline.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        pipeline.STATE_FILE.write_text("{ not json", encoding="utf-8")
        self.assertEqual(pipeline.standing_goal(), "")
        self.assertIn("LAYER 1", pipeline.context_for("x"))

    def test_the_seed_is_read_when_no_runtime_state_exists_yet(self):
        """A fresh checkout has the committed goal and no runtime file. It must
        still carry the goal on the first prompt rather than starting blank."""
        self.assertFalse(pipeline.STATE_FILE.exists())
        pipeline.SEED_FILE.write_text(
            '{"goal": "seeded objective", "history": []}', encoding="utf-8")
        self.assertIn("seeded objective", pipeline.standing_goal())

    def test_a_hook_write_never_touches_the_committed_seed(self):
        """Capture writes on the first prompt of every session. Writing that to
        a tracked file would dirty the working tree constantly, which is how the
        old store reached 168 kB of fixture goals."""
        pipeline.SEED_FILE.write_text(
            '{"goal": null, "history": []}', encoding="utf-8")
        before = pipeline.SEED_FILE.read_text(encoding="utf-8")
        pipeline.capture("rebuild the atlas payload and verify it", session="s")
        self.assertEqual(pipeline.SEED_FILE.read_text(encoding="utf-8"), before)
        self.assertTrue(pipeline.STATE_FILE.exists())

    def test_the_first_task_of_a_session_becomes_the_goal_with_no_slash(self):
        """The ask, in one test. Charles should not have to type anything for
        the goal to be standing; the first real task is the goal."""
        pipeline.clear_goal()
        first = "finish the harness layers and verify the web UI commands"
        context = pipeline.context_for(first, session="s1")
        self.assertIn("STANDING GOAL", context)
        self.assertIn(first, context)
        self.assertEqual(pipeline.load_goal()["source"], "captured")

    def test_a_captured_goal_holds_across_the_turns_after_it(self):
        """Otherwise the goal is just the last message with extra steps, and the
        drift it exists to catch is exactly an objective that quietly changed."""
        pipeline.clear_goal()
        first = "finish the harness layers and verify the web UI commands"
        pipeline.capture(first, session="s1")
        for later in ("continue", "also fix the gallery links",
                      "now rebuild the payload and push it"):
            pipeline.capture(later, session="s1")
        self.assertEqual(pipeline.load_goal()["goal"], first)

    def test_a_new_session_replaces_a_captured_goal(self):
        """A goal captured yesterday must not bind today's work."""
        pipeline.clear_goal()
        pipeline.capture("finish the harness layers and verify them", session="s1")
        pipeline.capture("load the catalog into mongo and check the indexes",
                         session="s2")
        self.assertIn("mongo", pipeline.load_goal()["goal"])

    def test_an_explicit_goal_is_never_overwritten_by_capture(self):
        """Someone typed it on purpose. Only they lift it."""
        pipeline.clear_goal()
        pipeline.set_goal("ship the designs", source="explicit", session="s1")
        pipeline.capture("rewrite the catalog loader from scratch", session="s2")
        self.assertEqual(pipeline.load_goal()["goal"], "ship the designs")

    def test_capture_ignores_continuations_and_questions(self):
        """A wrong yes rides in front of every prompt for the rest of the
        session, so this side of the trade is the conservative one."""
        for noise in ("continue", "ok", "thanks", "yes", "do it",
                      "what does this function do?", "why is it slow?"):
            pipeline.clear_goal()
            pipeline.capture(noise, session="s")
            self.assertIsNone(pipeline.load_goal()["goal"], noise)

    def test_the_history_is_capped_so_the_store_cannot_grow_without_bound(self):
        """The old store reached 168 kB because history was unbounded and every
        --check run appended to it. That file is read on every prompt."""
        pipeline.clear_goal()
        for index in range(60):
            pipeline.set_goal(f"objective number {index}", source="explicit")
        self.assertLessEqual(len(pipeline.load_goal()["history"]),
                             pipeline.HISTORY_LIMIT)

    def test_a_very_long_goal_is_bounded(self):
        goal.set_goal("x" * 5000)
        block = pipeline.standing_goal()
        # The template is about 650 bytes and the goal is capped at 400, so a
        # bounded block lands near 1050. It was near 930 until the template
        # gained the two sentences that say the goal was captured rather than
        # commanded, which is the behaviour Charles asked for and worth the
        # bytes. The number matters less than the fact that a 5000 character
        # goal cannot ride every prompt unbounded.
        self.assertLess(len(block), 1100)
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
        self.assertIn("/mastergoal", skill)

    def test_the_skill_documents_that_no_command_is_needed(self):
        """The spellings are the fallback now, not the route."""
        skill = (ROOT / "skills" / "master-goal" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("captured", skill.lower())
        self.assertIn("no slash", skill.lower())

    def test_only_the_person_who_set_it_lifts_it(self):
        for source in (goal.GOAL_BLOCK, pipeline.GOAL_TEMPLATE):
            self.assertIn("compaction pass", source)
            self.assertIn("token budget", source)


class NoCheckWritesTheRealGoal(unittest.TestCase):
    """A verifier must not change the thing it verifies.

    Capture made every --check a writer: rendering the pipeline for a fixture
    prompt sets that prompt as the standing goal. The first run after capture
    landed left "Plan and design a small interface." as the repository's
    objective, and a full test run left "Use Playwright browser automation to
    verify this page." Neither failed anything. Both were found by reading
    .auto-mode/goal.json after a green run.

    So the guard is static and cheap: every harness that renders the pipeline in
    its check has to go through the shared isolation.
    """

    HARNESSES = ("auto_mode_harness", "harness_proxy", "harness_wrap",
                 "harness_goal")

    def test_every_harness_check_isolates_the_goal_store(self):
        for name in self.HARNESSES:
            source = (ROOT / "scripts" / f"{name}.py").read_text(encoding="utf-8")
            self.assertIn("isolated_store()", source,
                          f"{name} --check can write the real goal store")

    def test_the_isolation_restores_both_paths_even_when_the_body_raises(self):
        """A check that fails must not leave the store pointed at a deleted
        temporary directory, which would make every later prompt goalless."""
        before = (pipeline.STATE_FILE, pipeline.SEED_FILE)
        with self.assertRaises(RuntimeError):
            with pipeline.isolated_store():
                self.assertNotEqual(pipeline.STATE_FILE, before[0])
                raise RuntimeError("the check failed")
        self.assertEqual((pipeline.STATE_FILE, pipeline.SEED_FILE), before)

    def test_the_env_override_redirects_both_paths(self):
        """The lever a subprocess needs. Without it every hook invocation in a
        test run captures a fixture goal into the real store."""
        source = (ROOT / "scripts" / "hooks" / "skill_pipeline.py").read_text(
            encoding="utf-8")
        self.assertIn("MASTER_REPO_GOAL_DIR", source)

    def test_the_runtime_store_is_not_tracked(self):
        """Capture writes on the first prompt of every session. A tracked path
        would dirty the working tree constantly, and did: the old store reached
        168 kB of fixture goals before it was noticed."""
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".auto-mode/", ignored)


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

    def test_shared_computer_control_metadata_is_visible_and_copyable(self):
        body = PANES_JS[PANES_JS.index("function computerControlHTML(items)"):]
        body = body[:body.index("function harnessHTML()")]
        for field in ("control.name", "control.skill", "control.file",
                      "control.routes", "control.check", "control.detail"):
            self.assertIn(field, body, f"the pane does not render {field}")
        self.assertIn("data-copy-cmd", body)
        self.assertIn("COMPUTER-CONTROL.md", body)
        self.assertIn("grants no host tool or permission", body)

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


class TheCatalogInMongo(unittest.TestCase):
    """Charles liked the card-wall index and asked to see the same catalog backed
    by MongoDB. An index is a claim about the documents and about the queries, and
    both rot silently: a field renamed in the generator leaves an index still
    created, still listed, and never used again. These hold both claims."""

    def setUp(self):
        self.store = DATA.get("catalogStore", {})
        self.index_file = ROOT / "scripts" / "catalog-indexes.js"

    def test_the_definitions_file_exists_and_is_parsed_not_restated(self):
        self.assertTrue(self.index_file.is_file())
        builder = (ROOT / "scripts" / "build_atlas_data.py").read_text(encoding="utf-8")
        # Parsing moved into catalog_index_spec, shared with the loader, because
        # both files had their own copy and both grew the same dotted-key bug.
        # The claim being tested is unchanged: the page reads the mongosh file
        # rather than restating what the indexes are.
        self.assertIn("catalog_index_spec.parse(CATALOG_INDEX_FILE)", builder)
        # No hand-rolled regex, rather than no mention of the word: the
        # docstrings say "parse the real createIndex calls", which is the thing
        # being described and not a fourth copy of the pattern.
        self.assertNotIn(r"createIndex\(", builder,
                         "the builder restates an index instead of reading the file")

    def test_every_created_index_reaches_the_page(self):
        """Matched inside the options object only.

        A bare name: "..." search also picks up the text index's own key spec,
        { name: "text", detail: "text" }, and reports "text" as a missing index.
        The options object is where an index name actually lives.
        """
        text = self.index_file.read_text(encoding="utf-8")
        created = set()
        for options in re.findall(r"createIndex\(.*?,\s*(\{.*?\})\s*\)", text, re.DOTALL):
            found = re.search(r'name:\s*"([^"]+)"', options)
            if found:
                created.add(found.group(1))
        shown = {i["name"] for i in self.store["indexes"]}
        self.assertEqual(created, shown)

    def test_every_index_explains_the_question_it_answers(self):
        for index in self.store["indexes"]:
            self.assertTrue(index["question"].strip(), index["name"])
            self.assertTrue(index["question"].rstrip().endswith("?"), index["name"])
            self.assertGreater(len(index["why"]), 40, index["name"])

    def test_the_checker_passes_against_the_real_catalog(self):
        """Run, not asserted. This is the check that caught two real mistakes."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "load_catalog_mongo.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("every indexed field exists", result.stdout)

    def test_the_unique_index_is_partial_because_of_the_runtime_sentinel(self):
        """A plain unique index on lanes.source fails on load: the runtime stage
        lanes all carry the sentinel "runtime" rather than a path."""
        lane_source = [i for i in self.store["indexes"] if i["name"] == "lane_source"][0]
        self.assertTrue(lane_source["unique"])
        self.assertTrue(lane_source["partial"])

    def test_no_index_claims_sparse_over_a_field_every_document_carries(self):
        """Checked against the documents that are actually stored.

        skills, agents, tools and mcp are shaped by mongo_documents and have no
        payload key of their own, so reading the payload would skip exactly the
        four collections Charles asked for. This is how agent_health was caught
        claiming sparse over a field all 50 agents carry.
        """
        import load_catalog_mongo as loader
        stored = loader.mongo_documents(DATA)
        for index in self.store["indexes"]:
            if not index["sparse"]:
                continue
            docs = stored[index["collection"]]
            first = index["fields"][0]
            carried = sum(1 for d in docs
                          if loader.field_value(d, first) not in (None, "", [], {}))
            self.assertLess(carried / len(docs), 0.95,
                            f"{index['name']} is sparse over a field on most documents")

    def test_the_numbers_in_the_prose_are_computed_not_written(self):
        """The first draft said "593 of 1120" against a catalog of 1126."""
        components = len(DATA["components"])
        with_recipe = sum(1 for c in DATA["components"] if c.get("setupRecipe"))
        by_recipe = [i for i in self.store["indexes"] if i["name"] == "by_recipe"][0]
        self.assertIn(f"{with_recipe} of {components}", by_recipe["why"])

    def test_every_query_names_an_index_that_exists(self):
        names = {i["name"] for i in self.store["indexes"]}
        for query in self.store["queries"]:
            self.assertIn(query["index"], names, query["filter"])

    def test_the_collection_counts_match_the_payload(self):
        """Only the collections that ARE a payload key.

        skills, agents, tools and mcp are shaped by the loader and have no key of
        their own, so they are checked against the loader instead, in
        TheFourCollectionsCharlesAskedFor.
        """
        key_for = {"components": "components", "lanes": "lanes", "routes": "routes",
                   "surfaces": "surfaces", "recipes": "setupRecipes"}
        for collection in self.store["collections"]:
            key = key_for.get(collection["name"])
            if key is None:
                continue
            self.assertEqual(collection["count"], len(DATA[key]), collection["name"])

    def test_the_design_renders_from_the_payload(self):
        page = (ROOT / "designs" / "d36-mongo.html").read_text(encoding="utf-8")
        self.assertIn("A.state.data.catalogStore", page)
        self.assertIn("store.indexes", page)
        self.assertIn("store.queries", page)

    def test_it_is_a_sibling_of_the_monitor_store_not_a_copy(self):
        text = self.index_file.read_text(encoding="utf-8")
        self.assertIn("monitor-indexes.js", text)
        self.assertNotIn("expireAfterSeconds", text,
                         "the catalog is rewritten wholesale; nothing expires")

    def test_no_em_or_en_dashes(self):
        for path in ("scripts/catalog-indexes.js", "scripts/load_catalog_mongo.py",
                     "designs/d36-mongo.html"):
            body = (ROOT / path).read_text(encoding="utf-8")
            self.assertNotIn("—", body, path)
            self.assertNotIn("–", body, path)


class TheGalleryHasNoDeadLinks(unittest.TestCase):
    """Four designs were listed with no file behind them, so clicking any of the
    four was a 404. That is what "the new design buttons do nothing" was."""

    def test_every_listed_design_exists(self):
        gallery = (ROOT / "designs" / "index.html").read_text(encoding="utf-8")
        listed = re.findall(r"file: '([^']+)'", gallery)
        self.assertGreater(len(listed), 30)
        missing = [f for f in listed if not (ROOT / "designs" / f).is_file()]
        self.assertFalse(missing, f"listed in the gallery with no file: {missing}")

    def test_every_exhibition_scene_has_a_page(self):
        """The shell carried scenes for broadsheet, switchboard, bathysphere and
        prism long before any page mounted them."""
        shell = (ROOT / "designs" / "atlas-exhibition.js").read_text(encoding="utf-8")
        block = shell[shell.index("const SCENES"):shell.index("function esc(")]
        scenes = set(re.findall(r"^\s{4}(\w+):\s*\{", block, re.M))
        pages = " ".join(p.name for p in (ROOT / "designs").glob("d*.html"))
        unmounted = sorted(s for s in scenes if s not in pages)
        self.assertFalse(unmounted, f"scenes with no page: {unmounted}")


class TheFourCollectionsCharlesAskedFor(unittest.TestCase):
    """Skills, agents, tools and MCP have to be findable by opening the database.

    They could have been a family filter over components, and were: then
    `show collections` answers with one bucket you must already know the field
    name to search. These hold that the four are real collections, that a skill
    we own carries its whole text, and that a catalogued entry carries a record
    and never the code.
    """

    def setUp(self):
        import load_catalog_mongo as loader
        self.loader = loader
        self.stored = loader.mongo_documents(loader.payload())
        self.store = DATA.get("catalogStore", {})

    def test_all_four_are_collections_of_their_own(self):
        for name in ("skills", "agents", "tools", "mcp"):
            self.assertIn(name, self.stored, f"{name} is not a collection")
            self.assertTrue(self.stored[name], f"{name} is empty")

    def test_the_page_count_matches_what_the_loader_would_write(self):
        """The page describes the store, so a number it shows that the loader
        does not produce is the drift the store section exists to prevent."""
        page = {c["name"]: c["count"] for c in self.store["collections"]}
        for name, count in page.items():
            self.assertEqual(count, len(self.stored.get(name, [])), name)

    def test_every_skill_this_repo_owns_is_in_the_skills_collection(self):
        """Three of the fifteen were named by no component and would have been
        missing entirely, which is the failure the collection exists to stop."""
        on_disk = {p.name for p in (ROOT / "skills").iterdir()
                   if p.is_dir() and (p / "SKILL.md").is_file()}
        stored_paths = {d["definition"]["path"] for d in self.stored["skills"]
                        if d.get("definition")}
        for name in sorted(on_disk):
            self.assertIn(f"skills/{name}/SKILL.md", stored_paths,
                          f"{name} is on disk but would not be in MongoDB")

    def test_a_local_skill_carries_its_whole_body(self):
        with_body = [d for d in self.stored["skills"] if d.get("definition")]
        on_disk = [p for p in (ROOT / "skills").iterdir()
                   if p.is_dir() and (p / "SKILL.md").is_file()]
        self.assertEqual(len(with_body), len(on_disk),
                         "every skill on disk should carry its body, and no more")
        for doc in with_body:
            path = ROOT / doc["definition"]["path"]
            raw = path.read_bytes()
            self.assertEqual(doc["definition"]["body"].encode("utf-8"), raw,
                             f"{doc['_id']} body differs from the file")
            self.assertEqual(doc["definition"]["sha256"], hashlib.sha256(raw).hexdigest(),
                             f"{doc['_id']} checksum differs from the file")

    def test_a_catalogued_entry_carries_a_record_and_not_the_code(self):
        """The deliberate line. This repository does not vendor third-party
        source, and a database copy would undo that and go stale unscanned."""
        catalogued = [d for d in self.stored["agents"] if d["origin"] == "catalog"]
        self.assertTrue(catalogued)
        for doc in catalogued:
            self.assertNotIn("definition", doc,
                             f"{doc['_id']} carries third-party code")
            self.assertIn("slug", doc)
            self.assertTrue(doc["url"].startswith("https://github.com/"))

    def test_a_catalogued_entry_carries_the_health_the_guardian_recorded(self):
        withhealth = [d for d in self.stored["agents"] if d.get("health")]
        self.assertTrue(withhealth)
        for doc in withhealth:
            for field in ("status", "license", "archived", "critical", "findings"):
                self.assertIn(field, doc["health"], doc["_id"])

    def test_origin_separates_the_two_tiers_on_every_document(self):
        for name in ("skills", "agents", "tools", "mcp"):
            for doc in self.stored[name]:
                self.assertIn(doc["origin"], ("local", "catalog"), doc["_id"])

    def test_every_document_uses_a_natural_id_so_a_reload_replaces(self):
        for name, docs in self.stored.items():
            ids = [d["_id"] for d in docs]
            self.assertEqual(len(ids), len(set(ids)), f"{name} has duplicate _id")
            self.assertTrue(all(isinstance(i, str) and i for i in ids), name)

    def test_no_secret_reaches_the_documents(self):
        blob = json.dumps(self.stored)
        # Anchored to the shapes real credentials take. A bare "sk-" matches
        # task-intake and risk-tools, and a check that fires on ordinary
        # hyphenated words is a check somebody deletes.
        patterns = [
            r"ghp_[A-Za-z0-9]{20,}",
            r"github_pat_[A-Za-z0-9_]{20,}",
            r"sk-[A-Za-z0-9]{20,}",
            r"AKIA[0-9A-Z]{16}",
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
            r"(?i)(password|api_key|secret|token)\s*[=:]\s*[\"']?[A-Za-z0-9_\-]{12,}",
        ]
        for pattern in patterns:
            found = re.search(pattern, blob)
            self.assertIsNone(found, f"{pattern} matched: {found.group(0)[:40] if found else ''}")

    def test_the_loader_writes_the_shaped_documents_not_the_raw_payload(self):
        """Loading the payload instead would store documents with no origin, no
        health and no skill bodies, and every new index would be dead."""
        body = (ROOT / "scripts" / "load_catalog_mongo.py").read_text(encoding="utf-8")
        load = body[body.index("def load("):]
        self.assertIn("mongo_documents(data)", load)

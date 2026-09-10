"""One harness that does what the other four do, and a longer chain on top.

Two claims worth holding, because both were false at first.

"Does what the others do" has to mean it calls them. A fifth copy of the
injection logic would drift from the other four the week it existed, so the test
is that the delegations reach the real modules rather than that some equivalent
behaviour exists here.

"And more" has to reach those delegations. It did not. `--run` and `--serve`
spawn the wrapper and the proxy as SUBPROCESSES, so the chain that lives in this
process reached neither: the wrapped command got the base pipeline and nothing
else, and the claim was true of the doing and false of the more. Both now take
--super, and the tests below check the flag is on the argv this file builds, not
only that the seam works in-process.
"""
import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "hooks"))

import harness_super as sup  # noqa: E402
import harness_proxy as proxy  # noqa: E402
import harness_wrap as wrap  # noqa: E402
import auto_mode_harness as surface  # noqa: E402
import skill_pipeline as pipeline  # noqa: E402

DATA = json.loads((ROOT / "designs" / "atlas-data.json").read_text(encoding="utf-8"))
SOURCE = (ROOT / "scripts" / "harness_super.py").read_text(encoding="utf-8")


class TheChainCarriesEveryPassCharlesNamed(unittest.TestCase):
    NAMED = ("CAVEMAN", "FULL OUTPUT", "PLAN", "DESIGN", "ARCHITECT",
             "REFACTOR", "COMPRESS", "REVIEW")

    def test_every_named_pass_is_in_the_chain(self):
        block = sup.super_block()
        for label in self.NAMED:
            self.assertIn(label, block, f"the chain is missing {label}")

    def test_the_order_is_the_one_asked_for(self):
        """Caveman and full output first, architect after design, review last.
        The order is what this harness contributes; the rules already existed."""
        block = sup.super_block()
        positions = [block.index(label) for label in self.NAMED]
        self.assertEqual(positions, sorted(positions),
                         "the passes are not in the order they were named")

    def test_architect_runs_before_producing_and_review_before_answering(self):
        by_label = {p[0]: p for p in sup.PASSES}
        self.assertIn("before producing", by_label["ARCHITECT"][3])
        self.assertIn("before answering", by_label["REVIEW"][3])

    def test_every_pass_names_a_skill_that_exists(self):
        """A chain pointing at a missing skill reads exactly like one that
        works, right up to the moment a model tries to load it."""
        for label, skill, _base, _when, _rule in sup.PASSES:
            self.assertTrue((ROOT / "skills" / skill / "SKILL.md").is_file(),
                            f"the {label} pass names {skill}, which is not on disk")

    def test_no_pass_restates_a_rule_the_core_already_carries(self):
        """The first chain wrote all ten rules out and seven of them already
        existed in the core. Two copies of one rule is the drift this repository
        keeps paying for, and it cost 4.3 kB a prompt to carry."""
        for label, _skill, base_rule, _when, rule in sup.PASSES:
            if base_rule is None:
                self.assertNotIn(label, pipeline.CORE,
                                 f"{label} adds a rule the core already has")
                self.assertTrue(rule, f"{label} adds nothing and points at nothing")
            else:
                self.assertFalse(rule, f"{label} points at rule {base_rule} and also restates it")

    def test_token_reduction_is_described_as_continuous_not_a_step(self):
        """It reads as a step in a numbered list, which is the misreading worth
        preventing: compressing a finished answer is the least valuable place to
        do it, because the tokens were already spent getting there."""
        block = sup.super_block()
        self.assertIn("not a step", block)
        self.assertIn("already spent", block)


class ItReallyDelegates(unittest.TestCase):
    def test_it_does_not_reimplement_the_pipeline(self):
        """The whole point of a shared pipeline is that there is one."""
        self.assertNotIn("LAYER 1, before reading", SOURCE,
                         "the super harness has its own copy of the core rules")

    def test_the_base_pipeline_comes_first_and_the_chain_extends_it(self):
        with pipeline.isolated_store():
            full = sup.context_for("refactor the loader", capturing=False)
        self.assertLess(full.index("LAYER 1"), full.index("SUPER HARNESS"),
                        "the chain is placed before the layers it extends")

    def test_each_delegation_reaches_the_real_module(self):
        for name, target in (("install", surface.install_surfaces),
                             ("repo files", surface.install_repo_instructions),
                             ("bundle", surface.write_bundles),
                             ("proxy", proxy.inject),
                             ("wrapper", wrap.build)):
            self.assertTrue(callable(target), f"{name} is not callable")

    def test_the_subprocess_argv_carries_the_super_flag(self):
        """The in-process seam can pass while the real subprocess sends the base
        pipeline only. This checks the argv the file actually builds."""
        self.assertIn('"--super", "--port"', SOURCE)
        self.assertIn('"--super", "--profile"', SOURCE)


class TheChainReachesTheProxyAndTheWrapper(unittest.TestCase):
    def setUp(self):
        self.original = (proxy.CONTEXT, wrap.CONTEXT)
        self.addCleanup(self.restore)
        store = pipeline.isolated_store()
        store.__enter__()
        self.addCleanup(store.__exit__, None, None, None)

    def restore(self):
        proxy.CONTEXT, wrap.CONTEXT = self.original

    def test_the_proxy_carries_the_chain_when_told_to(self):
        proxy.use_super_context()
        payload, _ = proxy.inject({"model": "m", "messages": [
            {"role": "user", "content": "refactor the loader and review it"}]})
        text = payload["messages"][0]["content"]
        self.assertIn("LAYER 1", text)
        self.assertIn("SUPER HARNESS", text)
        self.assertIn("ARCHITECT", text)

    def test_the_wrapper_carries_the_chain_when_told_to(self):
        wrap.use_super_context()
        text = wrap.rules_for("refactor the loader and review it")
        self.assertIn("LAYER 1", text)
        self.assertIn("SUPER HARNESS", text)
        self.assertIn("REVIEW", text)

    def test_neither_carries_it_unless_told(self):
        """The other four harnesses must keep their own smaller cost. The chain
        is roughly three times the base pipeline per turn."""
        self.assertNotIn("SUPER HARNESS", wrap.rules_for("refactor the loader"))
        payload, _ = proxy.inject({"model": "m", "messages": [
            {"role": "user", "content": "refactor the loader"}]})
        self.assertNotIn("SUPER HARNESS", payload["messages"][0]["content"])


class ItRunsEndToEnd(unittest.TestCase):
    def run_super(self, *args, **kwargs):
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "harness_super.py"),
                               *args], cwd=ROOT, capture_output=True, text=True,
                              timeout=180, **kwargs)

    def test_its_own_check_passes(self):
        result = self.run_super("--check")
        self.assertEqual(result.returncode, 0,
                         f"--check failed:\n{result.stdout}\n{result.stderr}")

    def test_the_wrapped_command_actually_receives_the_chain(self):
        """Not that the seam exists: that a real subprocess got the bytes."""
        probe = ("import sys;d=sys.stdin.read();"
                 "print('CHAIN' if 'SUPER HARNESS' in d else 'BASE-ONLY')")
        result = self.run_super("--profile", "stdin", "--run", "--",
                                sys.executable, "-c", probe)
        self.assertIn("CHAIN", result.stdout,
                      f"the wrapped command did not receive the chain:\n{result.stdout}")

    def test_the_wrapped_commands_exit_code_survives(self):
        result = self.run_super("--run", "--", sys.executable, "-c", "raise SystemExit(7)")
        self.assertEqual(result.returncode, 7)

    def test_context_shows_without_setting(self):
        """--context exists to show what a prompt would receive. Rendering it
        must not make it the standing goal."""
        before = pipeline.load_goal().get("goal")
        result = self.run_super("--context", "rebuild the entire loader from scratch")
        self.assertEqual(result.returncode, 0)
        self.assertIn("SUPER HARNESS", result.stdout)
        self.assertEqual(pipeline.load_goal().get("goal"), before,
                         "--context changed the standing goal")


class ItIsOnThePageWithTheOthers(unittest.TestCase):
    def test_it_is_one_of_the_declared_harnesses(self):
        ids = [h["id"] for h in DATA["harnesses"]]
        self.assertIn("harness-super", ids)
        self.assertEqual(ids[-1], "harness-super",
                         "the list runs least to most reach; this one is last")

    def test_its_card_states_the_cost_rather_than_hiding_it(self):
        card = [h for h in DATA["harnesses"] if h["id"] == "harness-super"][0]
        self.assertIn("token", card["limit"].lower())

    def test_its_card_does_not_claim_reach_the_others_lack(self):
        """It calls the other four. It cannot reach anywhere they cannot."""
        card = [h for h in DATA["harnesses"] if h["id"] == "harness-super"][0]
        self.assertIn("no reach the other four lack", card["limit"])

    def test_the_two_new_skills_are_enforced_everywhere(self):
        for name in ("master-architect", "master-review"):
            self.assertIn(name, surface.ENFORCED_SKILLS)
            self.assertTrue((ROOT / "skills" / name / "SKILL.md").is_file())
            self.assertTrue((ROOT / ".agents" / "skills" / name / "SKILL.md").is_file())


class EveryDesignSaysWhoItIsFor(unittest.TestCase):
    """Charles asked for the designs to be understandable by everyone from a
    non-technical reader to an experienced engineer. Six of them shipped with no
    description at all, and the rest described themselves in vocabulary that
    assumes you already read interfaces."""

    def test_no_design_is_listed_without_a_description(self):
        empty = [d["file"] for d in DATA["designs"] if not (d.get("detail") or "").strip()]
        self.assertEqual(empty, [], "designs listed with no description")

    def test_every_design_says_who_it_suits_and_what_to_do_first(self):
        for design in DATA["designs"]:
            self.assertTrue(design.get("audience"),
                            f"{design['file']} does not say who it is for")
            self.assertTrue(design.get("howto"),
                            f"{design['file']} does not say what to do first")

    def test_the_audience_is_one_of_the_four_levels(self):
        import build_atlas_data as builder
        allowed = set(builder.AUDIENCE_ORDER)
        for design in DATA["designs"]:
            self.assertIn(design["audience"], allowed, design["file"])

    def test_every_level_is_actually_used(self):
        """Four labels where three are never applied is three labels and a
        decoration."""
        used = {d["audience"] for d in DATA["designs"]}
        import build_atlas_data as builder
        self.assertEqual(used, set(builder.AUDIENCE_ORDER))

    def test_no_audience_entry_names_a_file_that_does_not_exist(self):
        """Fifteen of the first thirty-six did. Each silently did nothing,
        because a missing key returns empty strings on purpose, and the page
        looked correct. Only counting catches a wrong key."""
        import build_atlas_data as builder
        self.assertEqual(builder.audience_keys_that_name_nothing(), [])

    def test_the_how_to_line_avoids_interface_vocabulary(self):
        """It exists for the reader who has not met these words. If it uses
        them it is a second copy of the description."""
        jargon = ("specular", "oklch", "anisotropic", "backdrop-filter",
                  "viewport", "grotesque", "orthogonal", "emissive")
        for design in DATA["designs"]:
            lowered = design["howto"].lower()
            for word in jargon:
                self.assertNotIn(word, lowered,
                                 f"{design['file']} explains itself with {word!r}")

    def test_the_main_page_renders_both_new_fields(self):
        script = (ROOT / "atlas.js").read_text(encoding="utf-8")
        body = script[script.index("function renderDesignLinks()"):]
        body = body[:body.index("function escapeHtml")]
        self.assertIn("design.audience", body)
        self.assertIn("design.howto", body)

    def test_both_new_classes_have_a_rule(self):
        styles = (ROOT / "atlas.css").read_text(encoding="utf-8")
        for name in ("design-audience", "design-howto"):
            self.assertIn("." + name, styles, f".{name} is rendered with no rule")


class TheGalleryReadsTheAudienceRatherThanTypingItAgain(unittest.TestCase):
    """The gallery already had hand-written copy for every design, aimed at a
    reader who knows what a specular rim is. The audience line is for the reader
    who does not, and it comes from the payload so there is no third copy."""

    def setUp(self):
        self.gallery = (ROOT / "designs" / "index.html").read_text(encoding="utf-8")

    def test_it_reads_the_payload(self):
        self.assertIn("function audienceFor(", self.gallery)
        self.assertIn("data.designs", self.gallery)

    def test_it_uses_the_global_that_actually_exists(self):
        """__ATLAS_DATA__, not ATLAS_DATA. Both names look right, only one is
        defined, and the wrong one returns undefined: every card renders without
        the line, nothing errors, and the page still looks finished."""
        body = self.gallery[self.gallery.index("function audienceFor("):]
        body = body[:body.index(chr(10) + "}")]
        self.assertIn("window.__ATLAS_DATA__", body)
        self.assertNotIn("window.ATLAS_DATA ", body)

    def test_it_escapes_with_a_function_this_file_defines(self):
        """It first called esc(), which this file does not define. That throws
        inside the template and takes the whole card render with it."""
        self.assertIn("function escText(", self.gallery)
        body = self.gallery[self.gallery.index("function audienceFor("):]
        body = body[:body.index(chr(10) + "}")]
        self.assertNotIn("${esc(", body)

    def test_both_card_templates_render_it(self):
        """There are two: the featured cards and the archive grid. Adding the
        line to one leaves the other silently without it."""
        self.assertEqual(self.gallery.count("${audienceFor(d.file)}"), 2)

    def test_the_classes_it_introduces_are_styled(self):
        for name in ("who", "who-tag"):
            self.assertIn("." + name + "{", self.gallery.replace(" {", "{"),
                          f".{name} is rendered with no rule")


if __name__ == "__main__":
    unittest.main()

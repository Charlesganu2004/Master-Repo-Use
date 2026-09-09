"""Refactor is layer 3, and the page reads the layers rather than restating them.

Two things landed together and each guards the other.

The rule: layer 3 gained REFACTOR, so every prompt now carries a
behaviour-preserving pass over what was just written. It is in layer 3 rather
than layer 2 because a refactor is something done to code that exists; noticing
you would not want to read it again is not a thing you can plan in advance.

The page: the harness section used to describe the layers in hand-written prose,
and prose drifts from the thing it describes silently. It now renders what the
builder parsed out of skill_pipeline.CORE. The first version of that parser read
nine of eleven rules and looked completely correct, because nine rules render
fine and nobody counts them. The count assertions below are the part that
actually caught it.
"""
import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "hooks"))

import build_atlas_data as builder  # noqa: E402
import skill_pipeline as pipeline  # noqa: E402

DATA = json.loads((ROOT / "designs" / "atlas-data.json").read_text(encoding="utf-8"))
PANES = (ROOT / "designs" / "atlas-panes.js").read_text(encoding="utf-8")
CORE_JS = (ROOT / "designs" / "atlas-core.js").read_text(encoding="utf-8")


class RefactorIsInLayerThree(unittest.TestCase):
    def test_the_rule_is_in_the_core_not_a_lane(self):
        """A lane fires only on prompts that mention refactoring, and the code
        you would not want to read again is usually written on a prompt about
        something else entirely."""
        self.assertIn("8. REFACTOR.", pipeline.CORE)

    def test_it_sits_inside_layer_three(self):
        core = pipeline.CORE
        self.assertLess(core.index("LAYER 3"), core.index("8. REFACTOR."))
        self.assertLess(core.index("8. REFACTOR."), core.index("9. RE-APPLY LAYER 1"))

    def test_it_carries_the_three_rules_that_make_it_a_refactor(self):
        rule = pipeline.CORE[pipeline.CORE.index("8. REFACTOR."):]
        rule = rule[:rule.index("\n9.")]
        self.assertIn("behaviour-preserving", rule)
        self.assertIn("one transformation at a time", rule)
        self.assertIn("tests green after each", rule)
        self.assertIn("never mixed with a feature change", rule)

    def test_the_surface_half_is_there_too(self):
        rule = pipeline.CORE[pipeline.CORE.index("8. REFACTOR."):]
        rule = rule[:rule.index("\n9.")]
        self.assertIn("grayscale first, colour last", rule)


class TheRefactorLaneAttachesToRefactorWork(unittest.TestCase):
    def context(self, prompt: str) -> str:
        with pipeline.isolated_store():
            return pipeline.context_for(prompt)

    def test_a_refactor_prompt_names_both_skills(self):
        out = self.context("this module is full of duplication, refactor it")
        self.assertIn("master-refactor", out)

    def test_it_demands_the_test_gate_before_the_first_change(self):
        out = self.context("clean up the technical debt in the parser")
        self.assertIn("Tests green before the first change", out)

    def test_a_deletion_needs_the_search_that_proves_it_dead(self):
        """A symbol reached by string dispatch is invisible to a call graph and
        to a reading of the file, and deleting it fails in production."""
        out = self.context("remove the dead code from the loader")
        self.assertIn("search that proves the symbol dead", out)

    def test_an_unrelated_prompt_does_not_pay_for_it(self):
        out = self.context("what is the weather")
        self.assertNotIn("master-refactor", out)


class BothSkillsExistAndAreEnforced(unittest.TestCase):
    NAMES = ("master-refactor", "master-refactor-ui")

    def test_each_one_is_a_real_skill_file(self):
        for name in self.NAMES:
            path = ROOT / "skills" / name / "SKILL.md"
            self.assertTrue(path.is_file(), f"{name} has no SKILL.md")
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\nname: " + name),
                            f"{name} frontmatter does not match its folder")
            self.assertIn("description:", text)

    def test_each_one_is_mirrored_for_project_discovery(self):
        for name in self.NAMES:
            self.assertTrue((ROOT / ".agents" / "skills" / name / "SKILL.md").is_file(),
                            f"{name} is not in .agents/skills")

    def test_the_harness_enforces_them_on_every_surface(self):
        import auto_mode_harness as surface
        for name in self.NAMES:
            self.assertIn(name, surface.ENFORCED_SKILLS)

    def test_the_code_skill_refuses_to_refactor_without_a_test(self):
        """The one rule that makes it a refactor rather than a rewrite."""
        text = (ROOT / "skills" / "master-refactor" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("characterisation tests", text)
        self.assertIn("no refactor yet", text)

    def test_the_ui_skill_leads_with_grayscale(self):
        text = (ROOT / "skills" / "master-refactor-ui" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Grayscale first", text)
        self.assertLess(text.index("Grayscale first"), text.index("Colour, last"))

    def test_the_ui_skill_carries_the_verification_lesson_this_repo_paid_for(self):
        """Counting DOM elements cannot tell a working page from one hidden
        behind an opaque fixed layer. Both have the same node count."""
        text = (ROOT / "skills" / "master-refactor-ui" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("hit-test", text)


class TheLaneIsCataloguedWithItsMeasurements(unittest.TestCase):
    def setUp(self):
        self.text = (ROOT / "repo-lists" / "refactoring-skills.txt").read_text(encoding="utf-8")

    def test_the_lane_exists_and_reached_the_payload(self):
        lanes = {lane["id"] for lane in DATA["lanes"]}
        self.assertIn("cat-refactoring-skills", lanes)

    def test_the_two_unlicensed_repos_are_recorded_as_rejected_not_catalogued(self):
        """Both were named in the brief. Neither has a licence, so neither can
        be copied into a skill root, and a rejection nobody wrote down gets
        re-found and re-argued."""
        self.assertIn("MEASURED, THEN REJECTED", self.text)
        for repo in ("LovroPodobnik/refactoring-ui-skill", "LoveHikari/full-stack-skills"):
            self.assertIn(repo, self.text)
            entries = [line.split("#")[0].strip() for line in self.text.splitlines()
                       if line.strip() and not line.strip().startswith("#")]
            self.assertNotIn(repo, entries, f"{repo} is catalogued despite having no licence")

    def test_every_entry_reaches_the_page_with_its_measurement(self):
        """Not that a note exists in the file: that it reaches the payload.

        Three entries here had a note one line below the slug, because the slug
        ran past the note column. The parser dropped all three and the page
        showed "Catalogued in refactoring-skills.txt" where a licence and a star
        count were written. It is invisible reading the file, since the note is
        right there.
        """
        entries = [c for c in DATA["components"]
                   if c.get("lane") == "cat-refactoring-skills"]
        self.assertEqual(len(entries), 12, "the lane lost or gained an entry")
        for entry in entries:
            detail = entry.get("detail") or ""
            self.assertFalse(detail.startswith("Catalogued in "),
                             f"{entry['slug']} shows the placeholder, not its note")
            self.assertRegex(detail, r"MIT|ISC|Apache-2\.0",
                             f"{entry['slug']} does not state its licence")

    def test_no_lane_in_the_catalog_silently_drops_a_written_note(self):
        """The same parser bug, checked across every lane rather than this one.

        A note written directly under its entry is a note the author wrote and
        expected to see. Seven entries across the catalog were in that state
        before the parser was fixed.
        """
        import re
        slug_re = re.compile(r"^[\w.\-]+/[\w.\-]+$")
        dropped = []
        for path in sorted((ROOT / "repo-lists").glob("*.txt")):
            lines = path.read_text(encoding="utf-8").splitlines()
            by_slug = {c["slug"]: c for c in DATA["components"]
                       if c.get("lane") == f"cat-{path.stem}"}
            for index, line in enumerate(lines):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                slug = stripped.split("#")[0].strip()
                if not slug_re.fullmatch(slug) or slug not in by_slug:
                    continue
                following = lines[index + 1].strip() if index + 1 < len(lines) else ""
                wrote_a_note = "#" in stripped or following.startswith("#")
                shown = by_slug[slug].get("detail") or ""
                if wrote_a_note and shown.startswith("Catalogued in "):
                    dropped.append(f"{path.name}: {slug}")
        self.assertEqual(dropped, [], "notes written but never shown")


class ThePageReadsTheRulesRatherThanRestatingThem(unittest.TestCase):
    def setUp(self):
        self.payload = DATA.get("pipeline")

    def test_the_payload_exists(self):
        self.assertIsNotNone(self.payload, "run scripts/build_atlas_data.py")

    def test_every_rule_the_hook_injects_reaches_the_page(self):
        """Nine of eleven parsed cleanly and silently once. The count is the
        guard; reading the page is not."""
        import re
        expected = len([line for line in pipeline.CORE.splitlines()
                        if re.match(r"^\d+\. ", line.strip())])
        self.assertEqual(self.payload["ruleCount"], expected)
        self.assertEqual(sum(len(layer["rules"]) for layer in self.payload["layers"]),
                         expected)

    def test_the_two_awkward_shapes_both_parse(self):
        """ANTI-SLOP has a hyphen in its name and NEVER COMPACT has no full stop
        after it. Each was dropped by the first pattern."""
        names = {rule["name"] for layer in self.payload["layers"]
                 for rule in layer["rules"]}
        self.assertIn("ANTI-SLOP", names)
        self.assertIn("NEVER COMPACT", names)
        self.assertIn("REFACTOR", names)

    def test_the_rule_text_is_the_hook_text_byte_for_byte(self):
        for layer in self.payload["layers"]:
            for rule in layer["rules"]:
                joined = f"{rule['number']}. {rule['name']}"
                self.assertIn(joined, pipeline.CORE,
                              f"rule {rule['number']} is not in the hook")
                self.assertIn(rule["body"][:60], pipeline.CORE,
                              f"rule {rule['number']} body was rewritten for the page")

    def test_the_byte_count_is_measured_not_typed(self):
        self.assertEqual(self.payload["byteCount"],
                         len(pipeline.CORE.encode("utf-8")))

    def test_every_lane_reaches_the_page(self):
        self.assertEqual(len(self.payload["lanes"]), len(pipeline.LANES))
        lines = " ".join(lane["line"] + lane["detail"] for lane in self.payload["lanes"])
        self.assertIn("Refactor work", lines)

    def test_the_parser_refuses_to_ship_a_short_read(self):
        """The assertion is inside the builder, not only in this file, so a
        broken parse fails the build rather than quietly shipping fewer rules."""
        source = (ROOT / "scripts" / "build_atlas_data.py").read_text(encoding="utf-8")
        self.assertIn("the layer parser read", source)

    def test_the_goal_policy_says_capture_first(self):
        goal = self.payload["goal"]
        self.assertTrue(goal["captured"])
        self.assertIn("nothing typed", goal["detail"])
        self.assertIn("/mastergoal <text>", goal["spellings"])

    def test_every_command_on_the_page_actually_runs(self):
        """A page that prints a command nobody ran is the failure this
        repository keeps hitting. These are run, not read."""
        for entry in self.payload["commands"]:
            command = entry["command"]
            if "--install" in command or "--set" in command or "--clear" in command:
                continue        # these change state; covered by the harness checks
            result = subprocess.run(command, shell=True, cwd=ROOT,
                                    capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0,
                             f"{command} exited {result.returncode}:\n{result.stderr}")


class BothSurfacesRenderTheLayers(unittest.TestCase):
    def test_the_shared_pane_reads_the_payload(self):
        self.assertIn("function layersHTML()", PANES)
        self.assertIn("A.pipeline()", PANES)
        self.assertIn("function pipeline()", CORE_JS)

    def test_the_pane_renders_rules_rather_than_only_counting_them(self):
        pane = PANES[PANES.index("function layersHTML()"):]
        pane = pane[:pane.index("function harnessHTML()")]
        for field in ("rule.number", "rule.name", "rule.body", "layer.number"):
            self.assertIn(field, pane, f"{field} is never rendered")

    def test_the_main_page_reads_the_payload_too(self):
        script = (ROOT / "atlas.js").read_text(encoding="utf-8")
        body = script[script.index("function renderPipeline()"):]
        body = body[:body.index("function renderStore()")]
        self.assertIn("catalog.data.pipeline", body)
        for field in ("rule.number", "rule.name", "rule.body"):
            self.assertIn(field, body, f"{field} is never rendered on the main page")

    def test_the_main_page_has_the_hosts_the_renderer_writes_into(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        for node in ("pipelineSummary", "pipelineLayers", "pipelineLanes", "goalCapture"):
            self.assertIn(f'id="{node}"', index, f"{node} is written to but does not exist")

    def test_every_new_class_on_the_main_page_has_a_rule(self):
        """.cmd-action shipped inert once because it was rendered and never
        styled. Same check, new classes."""
        styles = (ROOT / "atlas.css").read_text(encoding="utf-8")
        for name in ("pipeline-panel", "pipeline-layer", "pipeline-layer-num",
                     "pipeline-rules", "pipeline-rule-num", "pipeline-rule-body",
                     "pipeline-lanes", "pipeline-plain", "pipeline-lede",
                     "harness-grid-title", "harness-grid-lede", "harness-capture"):
            self.assertIn("." + name, styles, f".{name} is rendered with no rule")

    def test_the_main_page_styles_use_tokens_this_sheet_defines(self):
        """--accent and --dim belong to the design shell, not to atlas.css. A
        var() naming neither falls back to nothing and paints invisibly."""
        styles = (ROOT / "atlas.css").read_text(encoding="utf-8")
        block = styles[styles.index("/* The standing pipeline"):]
        for missing in ("var(--accent)", "var(--dim)"):
            self.assertNotIn(missing, block,
                             f"{missing} is not defined in atlas.css")


if __name__ == "__main__":
    unittest.main()

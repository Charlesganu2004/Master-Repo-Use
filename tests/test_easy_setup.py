"""Four answers to "new machine, what do I run?", and a picker for the client.

A profile is an ordered list of the same reviewed recipes the Build tab uses. It
installs nothing Build could not install one node at a time; what it removes is
having to know which nodes, and in what order.

Two of its steps are tokens rather than fixed ids, because the right answer is
not the same for everyone: which assistant should receive the rules, and how much
memory this machine has. The tests that matter most here are about what happens
when a token cannot be resolved - the answer must be a visible note, never a
command with a placeholder still in it.
"""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "atlas-data.json").read_text(encoding="utf-8"))
PROFILES = {p["id"]: p for p in DATA.get("profiles", [])}
CLIENTS = {c["id"]: c for c in DATA.get("profileClients", [])}
RECIPES = {r["id"]: r for r in DATA["setupRecipes"]}
CORE = (ROOT / "designs" / "atlas-core.js").read_text(encoding="utf-8")
PANES = (ROOT / "designs" / "atlas-panes.js").read_text(encoding="utf-8")
TOKENS = {"rules:{client}", "model:{tier}", "model:{tier2}", "ALL_MODEL_TAGS"}


class TheFourProfilesExist(unittest.TestCase):
    def test_there_are_exactly_four(self):
        self.assertEqual(len(PROFILES), 4, "Charles asked for four options")

    def test_each_one_says_what_it_is_for(self):
        for pid, profile in PROFILES.items():
            for field in ("name", "summary", "detail", "bestFor"):
                self.assertTrue(profile.get(field, "").strip(), f"{pid} has no {field}")
            self.assertGreater(len(profile["detail"]), 60, pid)

    def test_they_are_ordered_smallest_commitment_first(self):
        order = [p["id"] for p in DATA["profiles"]]
        self.assertEqual(order[0], "rules-only")
        self.assertEqual(order[-1], "everything")

    def test_each_step_is_a_real_recipe_or_a_known_token(self):
        for pid, profile in PROFILES.items():
            for step in profile["steps"]:
                self.assertTrue(step in RECIPES or step in TOKENS,
                                f"{pid} names {step}, which is neither")

    def test_every_profile_writes_the_rules_and_then_checks_them(self):
        for pid, profile in PROFILES.items():
            self.assertEqual(profile["steps"][0], "rules:{client}", pid)
            self.assertEqual(profile["steps"][-1], "setup-rules-verify", pid)

    def test_the_runtime_is_ordered_before_any_model_tag(self):
        """ollama pull fails with no ollama, so the order is the instruction."""
        for pid, profile in PROFILES.items():
            steps = profile["steps"]
            models = [i for i, s in enumerate(steps)
                      if s.startswith("model:") or s == "ALL_MODEL_TAGS"]
            if not models:
                continue
            self.assertIn("setup-ollama-runtime", steps, pid)
            self.assertLess(steps.index("setup-ollama-runtime"), min(models), pid)

    def test_no_profile_runs_the_all_clients_setup_after_picking_one(self):
        """master-repo-global passes no client, so it would undo the picker."""
        for pid, profile in PROFILES.items():
            self.assertNotIn("master-repo-global", profile["steps"], pid)


class TheClientPicker(unittest.TestCase):
    def test_it_offers_all_four_clients_plus_all_at_once(self):
        self.assertEqual(set(CLIENTS), {"all", "claude", "codex", "gemini", "copilot"})

    def test_all_is_offered_first(self):
        self.assertEqual(DATA["profileClients"][0]["id"], "all")

    def test_each_names_the_file_it_writes(self):
        for cid, client in CLIENTS.items():
            if cid == "all":
                continue
            self.assertRegex(client["detail"], r"~/\.\w+/",
                             f"{cid} does not say which file it writes")

    def test_every_client_has_a_recipe_behind_it(self):
        for cid in CLIENTS:
            recipe = "setup-rules-all-clients" if cid == "all" else f"setup-rules-{cid}"
            self.assertIn(recipe, RECIPES, cid)

    def test_the_gpt_label_is_visible_on_the_codex_option(self):
        """Charles asked for GPT; Codex is the surface. Both names must appear."""
        self.assertIn("GPT", CLIENTS["codex"]["name"])


class UnresolvableStepsFailVisibly(unittest.TestCase):
    """The failure mode that matters: a token that cannot be filled in."""

    def test_an_unresolved_model_token_produces_a_note_not_a_command(self):
        window = CORE[CORE.index("function resolveProfile("):]
        window = window[:2600]
        self.assertIn("notes.push('No model chosen", window)
        self.assertIn("return;", window)

    def test_an_unknown_recipe_id_is_named_rather_than_skipped_silently(self):
        window = CORE[CORE.index("function resolveProfile("):][:2600]
        self.assertIn("names a recipe that is not in this data file", window)

    def test_a_recipe_with_no_command_for_this_platform_is_listed_as_blocked(self):
        window = CORE[CORE.index("function profileScriptFor("):][:2600]
        self.assertIn("blocked.push(", window)

    def test_a_placeholder_command_can_never_reach_the_script(self):
        window = CORE[CORE.index("function profileScriptFor("):][:2600]
        self.assertIn("REVIEWED_VERSION|<[^>]+>", window)

    def test_no_platform_chosen_asks_rather_than_defaulting(self):
        window = CORE[CORE.index("function profileScriptFor("):][:1400]
        self.assertIn("Choose your operating system first", window)


class TheCloneRunsOnce(unittest.TestCase):
    """Three identical clones in a row reads as a bug even when it is harmless."""

    def test_owner_recipes_record_their_shared_preamble(self):
        with_preamble = [r for r in RECIPES.values() if "preambles" in r]
        self.assertGreaterEqual(len(with_preamble), 6,
                                "the clone preamble is no longer being recorded")

    def test_a_recorded_preamble_plus_body_reconstructs_the_command_exactly(self):
        """The standalone command must stay intact; Build still runs these alone."""
        for rid, recipe in RECIPES.items():
            if "preambles" not in recipe:
                continue
            for platform, command in recipe["commands"].items():
                rebuilt = recipe["preambles"][platform] + recipe["bodies"][platform]
                self.assertEqual(rebuilt, command, f"{rid}/{platform}")

    def test_the_repeat_is_dropped_by_the_recorded_field_not_by_matching_strings(self):
        window = CORE[CORE.index("function profileScriptFor("):][:2600]
        self.assertIn("seenPreambles", window)
        self.assertIn("recipe.preambles && recipe.preambles[platformId]", window)

    def test_every_preamble_is_identical_across_recipes_on_a_platform(self):
        """If two differed, dropping the second would skip a step that mattered."""
        seen = {}
        for recipe in RECIPES.values():
            for platform, preamble in (recipe.get("preambles") or {}).items():
                seen.setdefault(platform, set()).add(preamble)
        for platform, values in seen.items():
            self.assertEqual(len(values), 1, f"{platform} has divergent preambles")


class TheModelsComeFromTheHardwareDocument(unittest.TestCase):
    """Not from a list in the builder. One drifted, which is why this exists."""

    VETTED = json.loads(
        (ROOT / "docs" / "hardware-profiles.json").read_text(encoding="utf-8"))["models"]

    def test_no_tier_names_a_tag_the_document_never_vetted(self):
        """gemma2:2b was offered for a while and appears nowhere in the document."""
        vetted = {m["tag"] for m in self.VETTED}
        for tier in DATA["hardware"]:
            for tag in tier["models"]:
                self.assertIn(tag, vetted, f"{tier['id']} offers an unvetted tag")

    def test_no_tier_offers_a_model_larger_than_it_can_hold(self):
        limits = {m["tag"]: m["min_ram_gb"] for m in self.VETTED}
        for tier in DATA["hardware"]:
            if not tier["gb"]:
                continue
            for tag in tier["models"]:
                self.assertLessEqual(limits[tag], tier["gb"],
                                     f"{tier['id']} offers {tag}, which needs more RAM")

    def test_a_tier_offers_a_choice_of_vendor_where_it_can(self):
        vendors = {m["tag"]: m["vendor"] for m in self.VETTED}
        for tier in DATA["hardware"]:
            if len(tier["models"]) > 1:
                names = [vendors[t] for t in tier["models"]]
                self.assertEqual(len(names), len(set(names)),
                                 f"{tier['id']} offers two builds from one vendor")

    def test_the_tier_list_is_read_rather_than_written(self):
        builder = (ROOT / "scripts" / "build_atlas_data.py").read_text(encoding="utf-8")
        self.assertIn("def tier_tags(", builder)
        self.assertIn('HARDWARE_PROFILES["models"]', builder)
        self.assertNotRegex(builder, r'"8gb".*\[\s*"phi3:mini"')


class TheInterfaceIsWired(unittest.TestCase):
    def test_easy_setup_is_a_tab(self):
        self.assertIn("id: 'easy'", CORE)
        self.assertIn("easyHTML()", PANES)

    def test_it_sits_before_build(self):
        """Build is the manual path; the easy one should be met first."""
        self.assertLess(CORE.index("id: 'easy'"), CORE.index("id: 'basket'"))

    def test_the_picker_persists_between_visits(self):
        self.assertIn("load('atlas.profileClient', 'all')", CORE)
        self.assertIn("save('atlas.profileClient', id)", CORE)

    def test_the_script_can_be_copied(self):
        self.assertIn("data-copy-profile", PANES)

    def test_the_styles_beat_an_element_reset(self):
        """:where() lost to the plain button{} several designs carry."""
        window = PANES[PANES.index("const BASE_STYLE = `"):][:1800]
        self.assertIn(".easyclients .chip{", window)
        self.assertNotIn(":where(.easyclients)", window)

    def test_the_injected_styles_go_in_before_a_design_stylesheet(self):
        self.assertIn("document.head.insertBefore(style, document.head.firstChild)", PANES)

    def test_every_value_the_page_prints_is_escaped(self):
        window = PANES[PANES.index("function easyProfile("):][:2200]
        for raw in ("${profile.name}", "${profile.detail}", "${result.text}"):
            self.assertNotIn(raw, window)


if __name__ == "__main__":
    unittest.main()

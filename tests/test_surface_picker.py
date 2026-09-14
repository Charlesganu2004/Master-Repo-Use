"""The setup section asks what you actually run, then writes only that.

The control it replaced was a single-select "which assistant" chip row, and it
was wrong in two ways that these tests pin down.

It could only hold one answer. Charles runs Claude Code, Antigravity and two
browser assistants at once, so the picker is multi-select.

Worse, it treated every client as command-shaped. A shell line cannot reach
ChatGPT in a browser tab; emitting one would look like configuration and do
nothing. So each surface declares how it can be reached, `shell` or `connect`,
and the page is forbidden from offering a command to a surface that has no shell
to run it in. That is the invariant most of this file defends.
"""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "designs" / "atlas-data.json").read_text(encoding="utf-8"))
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
SCRIPT = (ROOT / "atlas.js").read_text(encoding="utf-8")
STYLES = (ROOT / "atlas.css").read_text(encoding="utf-8")

SURFACES = DATA.get("surfaces", [])
GROUPS = DATA.get("surfaceGroups", [])
RECIPES = {r["id"]: r for r in DATA.get("setupRecipes", [])}
BY_ID = {s["id"]: s for s in SURFACES}


class TheSurfaceData(unittest.TestCase):
    def test_every_surface_declares_a_group_that_exists(self):
        declared = {g["id"] for g in GROUPS}
        self.assertTrue(declared, "no surface groups declared")
        for surface in SURFACES:
            self.assertIn(surface["group"], declared,
                          f"{surface['id']} is in group {surface['group']}, which is not declared")

    def test_every_group_has_at_least_one_surface(self):
        used = {s["group"] for s in SURFACES}
        for group in GROUPS:
            self.assertIn(group["id"], used, f"group {group['id']} would render empty")

    def test_ids_are_unique(self):
        ids = [s["id"] for s in SURFACES]
        self.assertEqual(len(ids), len(set(ids)), "duplicate surface id")

    def test_the_five_named_clients_are_all_present(self):
        """Charles named these by hand: Copilot, Gemini Code Assist, Gemini,
        Claude, ChatGPT. Each has to be reachable somewhere in the picker."""
        haystack = " ".join(s["name"].lower() for s in SURFACES)
        for named in ("copilot", "gemini code assist", "gemini", "claude", "chatgpt"):
            self.assertIn(named, haystack, f"{named} is not offered anywhere")

    def test_local_clients_and_web_chat_are_both_represented(self):
        for group in ("local-client", "web-chat", "local-model"):
            self.assertTrue([s for s in SURFACES if s["group"] == group],
                            f"nothing in the {group} group")

    def test_cursor_is_a_local_client_with_a_real_setup_recipe(self):
        cursor = BY_ID.get("cursor")
        self.assertIsNotNone(cursor, "Cursor is missing from the local client picker")
        self.assertEqual(cursor["group"], "local-client")
        self.assertEqual(cursor["runs"], "shell")
        self.assertEqual(cursor["setupRecipe"], "setup-rules-cursor")
        self.assertIn(cursor["setupRecipe"], RECIPES)

    def test_a_surface_runs_either_a_shell_command_or_a_connect_step(self):
        for surface in SURFACES:
            self.assertIn(surface["runs"], ("shell", "connect"),
                          f"{surface['id']} has an unknown runs mode")

    def test_shell_surfaces_point_at_a_recipe_that_exists(self):
        for surface in SURFACES:
            if surface["runs"] != "shell":
                continue
            self.assertIn(surface["setupRecipe"], RECIPES,
                          f"{surface['id']} points at a missing recipe")

    def test_a_browser_surface_is_never_given_a_command(self):
        """The whole reason for the group split. A connect surface that carried a
        recipe id would be one render away from printing a command that cannot
        run anywhere."""
        for surface in SURFACES:
            if surface["runs"] == "connect":
                self.assertIsNone(surface.get("setupRecipe"),
                                  f"{surface['id']} is a browser surface with a command attached")

    def test_a_connect_surface_says_where_it_reads_its_instructions_from(self):
        for surface in SURFACES:
            if surface["runs"] == "connect":
                self.assertTrue(surface.get("target", "").strip(),
                                f"{surface['id']} does not say where to paste the rules")

    def test_every_surface_explains_itself(self):
        for surface in SURFACES:
            self.assertGreater(len(surface.get("detail", "")), 25,
                               f"{surface['id']} has no usable description")

    def test_local_models_carry_a_memory_floor(self):
        for surface in SURFACES:
            if surface["group"] != "local-model":
                continue
            floor = surface.get("minRamGb")
            self.assertIsInstance(floor, int, f"{surface['id']} has no memory floor")
            self.assertGreaterEqual(floor, 4, f"{surface['id']} claims to fit under 4 GB")

    def test_only_local_models_carry_a_memory_floor(self):
        # A floor on a client would silently hide it from a low-memory machine,
        # which is wrong: the rules install regardless of how much memory is free.
        for surface in SURFACES:
            if surface["group"] != "local-model":
                self.assertIsNone(surface.get("minRamGb"),
                                  f"{surface['id']} is gated on memory but is not a model")

    def test_the_smallest_floor_matches_what_the_empty_state_promises(self):
        floors = [s["minRamGb"] for s in SURFACES if s["group"] == "local-model"]
        self.assertEqual(min(floors), 4,
                         "the page tells the user the smallest tag needs 4 GB")

    def test_a_four_gigabyte_machine_is_still_offered_something(self):
        fits = [s for s in SURFACES if s["group"] == "local-model" and s["minRamGb"] <= 4]
        self.assertTrue(fits, "a 4 GB machine would see an empty model group")

    def test_model_floors_rise_with_the_model_list_order(self):
        """The list is rendered in data order, so an out-of-order floor makes the
        column look shuffled to anyone scanning down it."""
        floors = [s["minRamGb"] for s in SURFACES if s["group"] == "local-model"]
        self.assertEqual(floors, sorted(floors), "model tags are not ordered by memory floor")

    def test_group_notes_are_written_for_a_reader(self):
        for group in GROUPS:
            self.assertGreater(len(group.get("note", "")), 30,
                               f"group {group['id']} has no note")

    def test_no_em_or_en_dashes_anywhere_in_the_surface_copy(self):
        for surface in SURFACES:
            for field in ("name", "target", "detail"):
                self.assertNotIn("—", surface.get(field, ""), surface["id"])
                self.assertNotIn("–", surface.get(field, ""), surface["id"])
        for group in GROUPS:
            self.assertNotIn("—", group.get("note", ""), group["id"])


class TheSetupMarkup(unittest.TestCase):
    def test_the_picker_has_a_mount_point_for_every_control(self):
        for element_id in ("setupOs", "setupRam", "setupProfile", "setupProfileNote",
                           "surfaceGroups", "setupOutput"):
            self.assertIn(f'id="{element_id}"', INDEX, f"#{element_id} is missing from the page")

    def test_the_old_single_select_control_is_gone_from_both_files(self):
        for stale in ("clientRow", "profileGrid", "renderClients", "renderProfiles"):
            self.assertNotIn(stale, INDEX, f"{stale} survives in the markup")
            self.assertNotIn(stale, SCRIPT, f"{stale} survives in the script")

    def test_the_output_region_announces_itself_to_a_screen_reader(self):
        # The script rewrites it on every tick, so a silent region would leave a
        # keyboard user with no idea the commands changed.
        match = re.search(r'id="setupOutput"[^>]*', INDEX)
        self.assertIsNotNone(match)
        self.assertIn("aria-live", match.group(0))

    def test_the_segmented_controls_are_labelled(self):
        for control in ("setupOs", "setupProfile"):
            match = re.search(r'id="' + control + r'"[^>]*', INDEX)
            self.assertIsNotNone(match, control)
            self.assertIn("aria-labelledby", match.group(0), f"#{control} has no label")

    def test_the_memory_field_has_a_real_label_element(self):
        self.assertIn('for="setupRam"', INDEX)

    def test_the_heading_says_the_picker_writes_only_what_was_ticked(self):
        self.assertIn("It writes only those commands", INDEX)


class ThePickerScript(unittest.TestCase):
    def test_it_renders_the_three_pieces_after_the_catalog_loads(self):
        loader = SCRIPT[SCRIPT.index("async function loadCatalog"):]
        loader = loader[:loader.index("function renderCatalogMetrics")]
        for call in ("renderSetupControls()", "renderSurfaces()", "renderSetupOutput()"):
            self.assertIn(call, loader, f"{call} never runs")

    def test_selection_is_a_set_so_more_than_one_surface_can_be_on(self):
        self.assertIn("const picked = new Set(", SCRIPT)

    def test_the_checkboxes_are_real_checkboxes(self):
        self.assertIn('type="checkbox"', SCRIPT)

    def test_models_require_an_explicit_validated_report(self):
        self.assertIn("catalog.hardwareReport.platform !== catalog.os", SCRIPT)
        self.assertIn("catalog.hardwareReport.modelIds.includes(s.id)", SCRIPT)

    def test_lowering_the_memory_unticks_a_model_that_no_longer_fits(self):
        """Otherwise the tick survives out of sight and the script emits a pull
        for a model the machine cannot hold, which is the one failure this
        control exists to prevent."""
        window = SCRIPT[SCRIPT.index("const ram = document.getElementById('setupRam')"):]
        window = window[:window.index("function currentProfile")]
        self.assertIn("picked.delete(model.id)", window)
        self.assertIn("model.minRamGb > floor", window)

    def test_the_command_list_comes_from_the_profile_step_order(self):
        # Order lives in the data so a new profile is a data change, and so the
        # page shows the same order the catalog documents elsewhere.
        self.assertIn("profile.steps", SCRIPT)

    def test_both_model_tokens_are_expanded_from_the_ticks(self):
        for token in ("model:", "ALL_MODEL_TAGS"):
            self.assertIn(token, SCRIPT, f"{token} is never expanded")

    def test_a_repeated_recipe_is_only_emitted_once(self):
        # model:{tier} and model:{tier2} resolve to the same ticked list.
        self.assertIn("if (!id || seen[id]) return;", SCRIPT)

    def test_the_ollama_runtime_is_skipped_when_no_model_is_ticked(self):
        window = SCRIPT[SCRIPT.index("function stepsForSelection"):]
        window = window[:window.index("function renderSetupOutput")]
        runtime = window[window.index("if (step === 'setup-ollama-runtime'"):]
        runtime = runtime[:runtime.index("return;")]
        self.assertIn("if (useModels.length)", runtime)
        self.assertIn("push(step);", runtime)
        self.assertLess(runtime.index("if (useModels.length)"), runtime.index("push(step);"))

    def test_a_depth_that_installs_no_models_says_so_rather_than_dropping_them(self):
        self.assertIn("plan.dropped", SCRIPT)
        self.assertIn("installs no models", SCRIPT)

    def test_browser_surfaces_get_their_own_block_with_no_command(self):
        block = SCRIPT[SCRIPT.index("These cannot take a command"):]
        block = block[:block.index("host.innerHTML = blocks.join")]
        self.assertIn("surface.target", block)
        self.assertNotIn("commandFor", block)

    def test_every_rendered_value_is_escaped(self):
        """innerHTML with catalog strings in it. The detail fields are ours, but
        the escape is what keeps that true after the next data change."""
        for field in ("surface.name", "surface.target", "surface.detail"):
            self.assertIn("escapeHtml(" + field + ")", SCRIPT, f"{field} goes in raw")

    def test_the_os_choice_covers_every_key_the_recipes_publish(self):
        offered = set(re.findall(r"\['(\w+)', '[^']+'\]", SCRIPT))
        keys = set()
        for recipe in RECIPES.values():
            keys |= set(recipe["commands"])
        keys.discard("other")
        self.assertTrue(keys <= offered,
                        f"recipes publish {sorted(keys - offered)} with no way to select it")

    def test_an_os_with_no_command_falls_back_rather_than_printing_nothing(self):
        self.assertIn("commands[catalog.os] || commands.other", SCRIPT)


class ThePickerStyles(unittest.TestCase):
    def test_every_class_the_script_emits_has_a_rule(self):
        emitted = set(re.findall(r'class="([a-z][a-z0-9 -]*)"', SCRIPT))
        names = set()
        for group in emitted:
            names |= {n for n in group.split() if n}
        # Rendered by other sections of the page, not by the picker.
        names -= {"route-chip", "design-link", "primary-button"}
        for name in sorted(names):
            self.assertRegex(STYLES, r"\." + re.escape(name) + r"\b",
                             f".{name} is rendered with no rule anywhere")

    def test_no_undefined_custom_properties(self):
        """A var() with no declaration and no fallback silently unsets the
        property. This caught --accent, which two rules used and nothing ever
        declared, so the design-link hover border resolved to currentColor.

        Seven names are set as inline styles from the script rather than in the
        stylesheet (node and route colours, the map transform, the health bars),
        so being written anywhere in atlas.js counts as a declaration.
        """
        used = set(re.findall(r"var\((--[a-z0-9-]+)", STYLES))
        declared = set(re.findall(r"(--[a-z0-9-]+)\s*:", STYLES))
        set_at_runtime = {name for name in used if name in SCRIPT}
        missing = used - declared - set_at_runtime
        self.assertFalse(missing, f"used but never declared: {sorted(missing)}")

    def test_the_ticked_state_uses_the_one_page_accent(self):
        rule = re.search(r"\.surface-pick\.on\s*\{[^}]*\}", STYLES)
        self.assertIsNotNone(rule, "the ticked state has no rule")
        self.assertIn("--orange", rule.group(0),
                      "the ticked state introduces a second accent")

    def test_the_script_block_can_scroll_instead_of_running_off_the_page(self):
        rule = re.search(r"\.out-code\s*\{[^}]*\}", STYLES)
        self.assertIsNotNone(rule)
        self.assertIn("overflow", rule.group(0))


    def test_the_script_block_does_not_ligate_double_hyphens(self):
        """Cascadia Code renders "--" as one long dash. In a block whose whole
        job is to be trusted or retyped verbatim, "--Client claude" reading as a
        single dash is a correctness problem, not a style one."""
        rule = re.search(r"\.out-code\s*\{[^}]*\}", STYLES)
        self.assertIsNotNone(rule)
        self.assertIn("font-variant-ligatures: none", rule.group(0))

    def test_the_model_grid_collapses_to_one_column_on_a_phone(self):
        self.assertIn(".surface-grid { grid-template-columns: 1fr; }", STYLES)


if __name__ == "__main__":
    unittest.main()

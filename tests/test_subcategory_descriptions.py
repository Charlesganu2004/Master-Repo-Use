"""A sub-category chip has to fit a row, so clicking it must say what it holds.

"Data interchange", "Multi-model databases" and "Usable" all read as
self-explanatory and none of them are. Charles asked for the description to
appear on click.

The text is not generated here. It comes from the parenthetical or colon clause
on the list's own '# ---' header, so it is written once beside the entries it
describes and cannot drift from them. That constraint is the reason for most of
the tests below: the pipeline must carry the author's words through unchanged,
and must not quietly invent one where the author wrote none.
"""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "atlas-data.json").read_text(encoding="utf-8"))
LANES = {lane["id"]: lane for lane in DATA["lanes"]}
CORE = (ROOT / "designs" / "atlas-core.js").read_text(encoding="utf-8")
PANES = (ROOT / "designs" / "atlas-panes.js").read_text(encoding="utf-8")
CSS = (ROOT / "designs" / "atlas-next.css").read_text(encoding="utf-8")

CATALOG_LANES = [lane for lane in DATA["lanes"] if lane.get("catalog")]
INFO = [(lane, info) for lane in CATALOG_LANES for info in lane.get("subcategoryInfo", [])]


class EverySubCategoryExplainsItself(unittest.TestCase):
    def test_there_are_sub_categories_to_describe(self):
        self.assertGreater(len(INFO), 20, "the lists lost their section headers")

    def test_none_is_left_without_a_description(self):
        naked = [f"{lane['name']} / {info['name']}" for lane, info in INFO
                 if not info["description"].strip()]
        self.assertEqual(naked, [], "these chips would click through to nothing")

    def test_a_description_is_a_sentence_not_a_restatement(self):
        """'Data interchange: data interchange' helps nobody."""
        for lane, info in INFO:
            description = info["description"].lower()
            self.assertNotEqual(description.rstrip("."), info["name"].lower(), lane["id"])
            self.assertGreater(len(info["description"]), 20,
                               f"{lane['id']} / {info['name']} is too short to say anything")

    def test_the_count_matches_the_entries_actually_in_it(self):
        for lane, info in INFO:
            actual = sum(1 for component in DATA["components"]
                         if component.get("lane") == lane["id"]
                         and component.get("sub") == info["name"])
            self.assertEqual(info["count"], actual, f"{lane['id']} / {info['name']}")

    def test_the_chip_label_is_still_short_enough_for_a_row(self):
        for lane, info in INFO:
            self.assertLessEqual(len(info["name"]), 38, f"{lane['id']} / {info['name']}")

    def test_the_description_never_leaks_into_the_label(self):
        """The label is the text before the clause; adding prose must not move it."""
        for lane, info in INFO:
            self.assertNotIn("(", info["name"], lane["id"])
            self.assertIn(info["name"], lane["subcategories"], lane["id"])


class TheDescriptionsComeFromTheListFiles(unittest.TestCase):
    """Not from the builder. A description invented in code is one nobody edits."""

    def test_each_description_appears_verbatim_in_its_source_list(self):
        for lane, info in INFO:
            source = ROOT / lane["source"]
            self.assertTrue(source.exists(), lane["source"])
            text = " ".join(source.read_text(encoding="utf-8").split())
            self.assertIn(info["description"], text,
                          f"{lane['id']} / {info['name']} was not written in {lane['source']}")

    def test_the_builder_holds_no_hardcoded_description_table(self):
        builder = (ROOT / "scripts" / "build_atlas_data.py").read_text(encoding="utf-8")
        self.assertNotIn("SUBCATEGORY_DESCRIPTIONS", builder)

    def test_a_header_with_no_clause_yields_no_description(self):
        """Absence has to survive, or the next empty header gets a fake answer."""
        self.assertIn('"description": " ".join(" ".join(blurbs.get(name, [])).split())',
                      (ROOT / "scripts" / "build_atlas_data.py").read_text(encoding="utf-8"))


class TheClientRendersIt(unittest.TestCase):
    def test_the_core_resolves_a_description_for_a_chip(self):
        self.assertIn("function subDescription(", CORE)
        self.assertIn("description: subDescription(id)", CORE)

    def test_it_is_exported_so_every_design_can_reach_it(self):
        self.assertRegex(CORE, r"subcategories,\s*subDescription,")

    def test_the_same_name_in_two_lanes_keeps_both_meanings(self):
        """One lane silently overwriting another's description would be a lie."""
        window = CORE[CORE.index("function subDescription("):]
        self.assertIn("seen.join(' | ')", window[:900])

    def test_the_catalog_bucket_says_what_it_is(self):
        """The largest chip is not a section anyone wrote, so it needs saying."""
        window = CORE[CORE.index("function subDescription("):][:900]
        self.assertIn("id === 'Catalog'", window)
        self.assertIn("no section headers", window)

    def test_selecting_a_chip_prints_its_description(self):
        self.assertIn("function subNotes(", PANES)
        self.assertIn("A.state.activeSubs.has(s.id) && s.description", PANES)
        self.assertIn("${subNotes(subs)}", PANES)

    def test_hovering_shows_it_too(self):
        """Click is the asked-for gesture; a title attribute costs nothing."""
        self.assertIn('title="${esc(s.description)}"', PANES)

    def test_the_note_is_styled_rather_than_inheriting_button_type(self):
        self.assertIn("#filters .subnote", CSS)

    def test_the_description_is_escaped_before_it_reaches_the_page(self):
        """List files are plain text and nothing stops a '<' being typed in one."""
        window = PANES[PANES.index("function subNotes("):]
        window = window[:900]
        self.assertNotRegex(window, r"\$\{s\.description\}")
        self.assertIn("esc(s.description)", window)

    def test_nothing_is_printed_when_no_chip_is_selected(self):
        window = PANES[PANES.index("function subNotes("):][:900]
        self.assertIn("if (!chosen.length) return '';", window)


class TheListFilesStayReadable(unittest.TestCase):
    """The clause lives in a file people edit by hand, so it has to stay tidy."""

    HEADER = re.compile(r"^# --- (.+)$")

    def test_no_header_line_runs_past_a_sane_width(self):
        for path in sorted((ROOT / "repo-lists").glob("*.txt")):
            for number, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
                if self.HEADER.match(line):
                    self.assertLess(len(line), 160, f"{path.name}:{number}")

    def test_every_clause_closes_its_bracket(self):
        for path in sorted((ROOT / "repo-lists").glob("*.txt")):
            for number, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
                if self.HEADER.match(line):
                    self.assertEqual(line.count("("), line.count(")"), f"{path.name}:{number}")


if __name__ == "__main__":
    unittest.main()

"""The store section shows what indexing means; it does not describe it.

Charles asked to be shown what "indexed" and "the MongoDB store" mean here, not
told. The difference matters, because a page that describes a store drifts from
the store the moment anyone edits the index file, and there is no way to notice.

So the section renders from scripts/monitor-indexes.js, parsed at build time. An
index added there appears on the page. An index removed there disappears from it.
The tests below hold that link, and hold the three MongoDB facts the page states,
each of which is a thing that silently does nothing when you get it wrong.
"""
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_atlas_data as build  # noqa: E402

DATA = json.loads((ROOT / "designs" / "atlas-data.json").read_text(encoding="utf-8"))
INDEX_JS = (ROOT / "scripts" / "monitor-indexes.js").read_text(encoding="utf-8")
INDEX_HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SCRIPT = (ROOT / "atlas.js").read_text(encoding="utf-8")
STYLES = (ROOT / "atlas.css").read_text(encoding="utf-8")
STORE = DATA.get("store", {})


class ThePageIsReadFromTheRealFile(unittest.TestCase):
    def test_every_created_index_reaches_the_page(self):
        """The whole point. A createIndex the page does not show is a store the
        reader has not been shown."""
        created = set(re.findall(r'name:\s*"([^"]+)"', INDEX_JS))
        shown = {index["name"] for index in STORE["indexes"]}
        self.assertEqual(created, shown,
                         "the page and scripts/monitor-indexes.js disagree")

    def test_the_key_specification_is_the_one_in_the_file(self):
        for index in STORE["indexes"]:
            pattern = re.compile(
                r"db\." + index["collection"] + r"\.createIndex\(\s*(\{.*?\})",
                re.DOTALL)
            found = [" ".join(m.split()) for m in pattern.findall(INDEX_JS)]
            self.assertIn(index["keys"], found,
                          f"{index['name']} shows keys that are not in the file")

    def test_the_unique_flag_is_read_rather_than_assumed(self):
        unique = {i["name"] for i in STORE["indexes"] if i["unique"]}
        self.assertEqual(unique, {"source_unique"})

    def test_the_ttl_flag_is_read_rather_than_assumed(self):
        ttl = {i["name"] for i in STORE["indexes"] if i["ttl"]}
        self.assertEqual(ttl, {"events_ttl"})

    def test_an_index_with_no_explanation_would_be_caught(self):
        """An index rendered with an empty question is a blank row on the page,
        which reads as a rendering bug rather than as missing documentation."""
        for index in STORE["indexes"]:
            self.assertTrue(index["question"].strip(),
                            f"{index['name']} has no question; add it to INDEX_QUESTIONS")
            self.assertTrue(index["why"].strip(),
                            f"{index['name']} has no explanation")

    def test_the_parser_finds_all_seven_and_not_a_subset(self):
        self.assertEqual(len(STORE["indexes"]), INDEX_JS.count("createIndex("))

    def test_the_question_is_written_as_a_question(self):
        for index in STORE["indexes"]:
            self.assertTrue(index["question"].rstrip().endswith("?"),
                            f"{index['name']} leads with something that is not a question")

    def test_the_command_shown_is_the_command_in_the_files_own_header(self):
        self.assertIn(STORE["command"], INDEX_JS,
                      "the page shows a command the index file does not document")

    def test_it_points_at_the_source_and_the_design(self):
        self.assertEqual(STORE["file"], "scripts/monitor-indexes.js")
        self.assertTrue((ROOT / STORE["doc"]).exists(), "the linked design doc is gone")


class TheThreeFactsThatSilentlyFail(unittest.TestCase):
    """Each of these is a MongoDB behaviour that does nothing rather than erroring
    when you get it wrong, which is why the page states them."""

    def test_the_ttl_field_is_declared_a_date(self):
        expires = [f for f in STORE["document"]["fields"] if f[0] == "expires_at"]
        self.assertTrue(expires, "the document does not show the TTL field")
        self.assertEqual(expires[0][1], "Date")
        self.assertIn("never fires", expires[0][2].lower() + expires[0][2])

    def test_the_page_says_the_ttl_index_must_stay_single_field(self):
        ttl = [i for i in STORE["indexes"] if i["ttl"]][0]
        self.assertIn("single-field", ttl["why"])
        self.assertEqual(ttl["keys"].count(":"), 1,
                         "the TTL index in the file is no longer single-field")

    def test_the_page_explains_expire_after_seconds_zero(self):
        ttl = [i for i in STORE["indexes"] if i["ttl"]][0]
        self.assertIn("expireAfterSeconds: 0", ttl["why"])
        self.assertIn("expires_at", ttl["why"])

    def test_search_is_separated_from_ordinary_queries(self):
        modes = {m["mode"] for m in STORE["search"]}
        self.assertTrue(any("$search" in m for m in modes))
        self.assertTrue(any("$vectorSearch" in m for m in modes))

    def test_the_self_managed_search_requirement_is_stated_with_its_date(self):
        """Checked against MongoDB's own documentation on 2026-09-04. It moved
        from Atlas-only, so an undated claim here ages badly."""
        text = " ".join(m["detail"] for m in STORE["search"])
        self.assertIn("8.2", text)
        self.assertIn("mongot", text)
        self.assertIn("replica set", text)
        self.assertRegex(text, r"\d{4}-\d{2}-\d{2}")

    def test_the_summaries_have_no_ttl_and_the_page_says_why(self):
        summaries = [i for i in STORE["indexes"] if i["collection"] == "summaries"]
        self.assertTrue(summaries)
        self.assertFalse(any(i["ttl"] for i in summaries))
        self.assertIn("no TTL", " ".join(i["why"] for i in summaries))


class TheSectionOnThePage(unittest.TestCase):
    def test_the_section_exists_and_is_reachable_from_the_nav(self):
        self.assertIn('id="store"', INDEX_HTML)
        self.assertIn('href="#store"', INDEX_HTML)

    def test_every_mount_point_the_renderer_writes_to_exists(self):
        for element_id in ("storeCollection", "storeDocument", "storeIndexCount",
                           "storeIndexList", "storeSearch", "storeCommand",
                           "storeSource", "copyStore"):
            self.assertIn(f'id="{element_id}"', INDEX_HTML, f"#{element_id} is missing")

    def test_the_renderer_runs_after_the_catalog_loads(self):
        loader = SCRIPT[SCRIPT.index("async function loadCatalog"):]
        loader = loader[:loader.index("function renderCatalogMetrics")]
        self.assertIn("renderStore()", loader)

    def test_the_renderer_survives_a_payload_with_no_store(self):
        body = SCRIPT[SCRIPT.index("function renderStore()"):]
        body = body[:body.index("function renderDesignLinks")]
        self.assertIn("if (!store) return;", body)

    def test_every_rendered_value_is_escaped(self):
        body = SCRIPT[SCRIPT.index("function renderStore()"):]
        body = body[:body.index("function renderDesignLinks")]
        for value in ("index.question", "index.keys", "index.name", "index.why",
                      "mode.mode", "mode.detail", "store.file"):
            self.assertIn("escapeHtml(" + value + ")", body, f"{value} goes in raw")

    def test_the_command_is_set_as_text_not_markup(self):
        body = SCRIPT[SCRIPT.index("function renderStore()"):]
        body = body[:body.index("function renderDesignLinks")]
        self.assertIn("command.textContent = store.command", body)

    def test_the_copy_button_is_wired_once_not_once_per_render(self):
        body = SCRIPT[SCRIPT.index("function renderStore()"):]
        body = body[:body.index("function renderDesignLinks")]
        self.assertIn("copy.dataset.wired", body)


class TheSectionStyles(unittest.TestCase):
    def test_every_class_the_renderer_emits_has_a_rule(self):
        body = SCRIPT[SCRIPT.index("function renderStore()"):]
        body = body[:body.index("function renderDesignLinks")]
        names = set()
        for group in re.findall(r'class="([a-z][a-z0-9 -]*)"', body):
            names |= {n for n in group.split() if n}
        for name in sorted(names):
            self.assertRegex(STYLES, r"\." + re.escape(name) + r"\b",
                             f".{name} is rendered with no rule")

    def test_the_two_badges_reuse_page_tokens_rather_than_new_colours(self):
        for selector in (r"\.index-tag\.unique\s*\{[^}]*\}", r"\.index-tag\.ttl\s*\{[^}]*\}"):
            rule = re.search(selector, STYLES)
            self.assertIsNotNone(rule, selector)
            self.assertRegex(rule.group(0), r"var\(--(orange|yellow)\)",
                             "a badge introduced a colour outside the palette")

    def test_the_key_specification_does_not_ligate(self):
        """Cascadia Code turns "-1" into a single glyph. A sort direction is the
        one place that is not cosmetic."""
        rule = re.search(r"\.index-spec\s*\{[^}]*\}", STYLES)
        self.assertIsNotNone(rule)
        self.assertIn("font-variant-ligatures: none", rule.group(0))

    def test_the_two_column_split_collapses_on_a_narrow_screen(self):
        self.assertIn(".store-grid, .store-foot { grid-template-columns: 1fr; }", STYLES)

    def test_the_cards_do_not_stretch_to_each_others_height(self):
        rule = re.search(r"\.store-grid\s*\{[^}]*\}", STYLES)
        self.assertIsNotNone(rule)
        self.assertIn("align-items: start", rule.group(0))


class TheProse(unittest.TestCase):
    def test_no_em_or_en_dashes_in_the_generated_store_copy(self):
        blob = json.dumps(STORE, ensure_ascii=False)
        self.assertNotIn("—", blob)
        self.assertNotIn("–", blob)

    def test_no_em_or_en_dashes_in_the_section_markup(self):
        section = INDEX_HTML[INDEX_HTML.index('id="store"'):]
        section = section[:section.index('id="designs"')]
        self.assertNotIn("—", section)
        self.assertNotIn("–", section)

    def test_the_heading_promises_to_show_rather_than_to_explain(self):
        section = INDEX_HTML[INDEX_HTML.index('id="store"'):]
        section = section[:section.index('id="designs"')]
        self.assertIn("read from the real file", section)


class TheParserItself(unittest.TestCase):
    def test_it_reads_the_file_rather_than_a_copy_of_it(self):
        source = (ROOT / "scripts" / "build_atlas_data.py").read_text(encoding="utf-8")
        self.assertIn('STORE_INDEX_FILE = ROOT / "scripts" / "monitor-indexes.js"', source)
        # Reading moved into catalog_index_spec, which parses any mongosh index
        # file. It was the third hand-rolled copy of one regex, and two of the
        # three had grown the same dotted-key bug. The claim is unchanged: the
        # page reads monitor-indexes.js rather than restating its indexes.
        self.assertIn("catalog_index_spec.parse(STORE_INDEX_FILE)", source)
        self.assertNotIn("createIndex\(", source,
                         "the builder restates an index instead of reading the file")

    def test_a_renamed_index_loses_its_question_rather_than_borrowing_one(self):
        """Keyed by name on purpose: a rename should surface as a missing
        explanation, not as the old explanation attached to new keys."""
        self.assertEqual(
            build.INDEX_QUESTIONS.get("a_name_that_does_not_exist", ("", ""))[0], "")

    def test_the_root_and_designs_payloads_stay_identical(self):
        root = json.loads((ROOT / "atlas-data.json").read_text(encoding="utf-8"))
        self.assertEqual(root.get("store"), STORE)


if __name__ == "__main__":
    unittest.main()

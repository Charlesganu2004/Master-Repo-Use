"""Five designs share one data layer. These tests stop them drifting apart.

The data layer is generated from files that exist, so the most valuable checks
are the ones that catch a lane pointing at something deleted, a component in a
lane that is gone, a route naming a component that never existed, and a private
catalog slug reaching a file that gets published.
"""
import json
import pathlib
import re
import unittest
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "atlas-data.json"
DESIGNS = ROOT / "designs"
INTERACTIVE = ["d2-constellation.html", "d3-console.html",
               "d4-orbital.html", "d5-blueprint.html"]

# Charles asked for at least 120 lanes. Padding the count with invented names
# would satisfy the number and defeat the point, so the generator grounds every
# lane in a file and this floor guards the result.
MIN_LANES = 120


def data():
    return json.loads(DATA.read_text(encoding="utf-8"))


class IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        found = dict(attrs).get("id")
        if found:
            self.ids.append(found)


class TheDataLayer(unittest.TestCase):
    def setUp(self):
        self.d = data()

    def test_data_file_exists_and_parses(self):
        self.assertTrue(DATA.exists(), "run scripts/build_atlas_data.py")

    def test_meets_the_lane_floor(self):
        self.assertGreaterEqual(len(self.d["lanes"]), MIN_LANES)

    def test_lane_ids_are_unique(self):
        ids = [l["id"] for l in self.d["lanes"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_component_ids_are_unique(self):
        ids = [c["id"] for c in self.d["components"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_component_sits_in_a_lane_that_exists(self):
        lanes = {l["id"] for l in self.d["lanes"]}
        orphans = sorted({c["id"] for c in self.d["components"] if c["lane"] not in lanes})
        self.assertFalse(orphans, f"components in missing lanes: {orphans[:5]}")

    def test_every_lane_belongs_to_a_declared_family(self):
        families = {f["id"] for f in self.d["families"]}
        stray = sorted({l["family"] for l in self.d["lanes"]} - families)
        self.assertFalse(stray, f"undeclared families: {stray}")

    def test_every_route_member_is_a_real_component(self):
        known = {c["id"] for c in self.d["components"]}
        for route in self.d["routes"]:
            missing = [m for m in route["members"] if m not in known]
            self.assertFalse(missing, f"route {route['id']} names missing {missing}")

    def test_file_backed_lanes_point_at_files_that_exist(self):
        missing = []
        for lane in self.d["lanes"]:
            source = lane["source"]
            if source in {"runtime", "custom (this browser only)"} or lane.get("custom"):
                continue
            if not (ROOT / source).exists():
                missing.append(source)
        self.assertFalse(missing, f"lanes point at deleted files: {missing[:5]}")

    def test_every_lane_has_a_description(self):
        blank = [l["id"] for l in self.d["lanes"] if not (l.get("description") or "").strip()]
        self.assertFalse(blank, f"lanes with no description: {blank[:5]}")

    def test_hardware_tiers_cover_the_range_charles_asked_for(self):
        ids = {h["id"] for h in self.d["hardware"]}
        for needed in ("4gb", "8gb", "16gb", "32gb", "apple", "gpu"):
            self.assertIn(needed, ids)

    def test_no_private_catalog_slug_reaches_the_published_data(self):
        """This file ships to a public site; catalog composition is private.

        Checked against the real catalog rather than by guessing what a slug
        looks like. Prose such as "Finance/Trading" is slug-shaped and harmless;
        an actual unallowlisted repository name is the thing that matters.
        """
        allow, catalog = set(), set()
        for path in (ROOT / "repo-lists").glob("*.txt"):
            for line in path.read_text(encoding="utf-8").splitlines():
                candidate = line.split("#")[0].strip()
                if not re.fullmatch(r"[\w.-]+/[\w.-]+", candidate):
                    continue
                (allow if path.stem == "public-allowlist" else catalog).add(candidate)
        blob = json.dumps(self.d)
        private = catalog - allow
        leaked = sorted(slug for slug in private if slug in blob)
        self.assertFalse(leaked, f"private catalog slugs in published data: {leaked}")


class TheDataLayerCopies(unittest.TestCase):
    """The designs fetch the data relative to themselves, so there are two copies.

    Both are written by one generator run. If they ever differ, someone edited a
    generated file by hand and the designs are now showing something the root
    data does not say.
    """

    def test_root_and_designs_copies_are_identical(self):
        root = DATA.read_text(encoding="utf-8")
        beside = (DESIGNS / "atlas-data.json").read_text(encoding="utf-8")
        self.assertEqual(root, beside,
                         "atlas-data.json copies differ; re-run scripts/build_atlas_data.py")


class TheOfflineFallback(unittest.TestCase):
    """The designs must open by double-click, with no server.

    Charles clicked a design and got an error page. Browsers block fetch() over
    file://, so the data is also emitted as a script tag, which is not blocked.
    """

    def test_data_is_also_emitted_as_a_script(self):
        self.assertTrue((DESIGNS / "atlas-data.js").exists(),
                        "run scripts/build_atlas_data.py")

    def test_the_script_assigns_the_global_the_core_reads(self):
        body = (DESIGNS / "atlas-data.js").read_text(encoding="utf-8")
        self.assertIn("window.__ATLAS_DATA__ =", body)

    def test_the_script_holds_the_same_data_as_the_json(self):
        body = (DESIGNS / "atlas-data.js").read_text(encoding="utf-8")
        start = body.index("window.__ATLAS_DATA__ =") + len("window.__ATLAS_DATA__ =")
        embedded = json.loads(body[start:].rstrip().rstrip(";"))
        self.assertEqual(embedded, json.loads((DESIGNS / "atlas-data.json").read_text(encoding="utf-8")))

    def test_every_design_loads_the_script_before_the_core(self):
        for name in INTERACTIVE:
            body = (DESIGNS / name).read_text(encoding="utf-8")
            self.assertIn("atlas-data.js", body, f"{name} has no offline fallback")
            self.assertLess(body.index("atlas-data.js"), body.index("atlas-core.js"),
                            f"{name} loads the data after the core")

    def test_the_core_prefers_the_embedded_data(self):
        core = (DESIGNS / "atlas-core.js").read_text(encoding="utf-8")
        self.assertIn("window.__ATLAS_DATA__", core)
        self.assertLess(core.index("window.__ATLAS_DATA__"), core.index("await fetch("),
                        "the core must check the embedded data before fetching")


class TheDesigns(unittest.TestCase):
    def test_all_interactive_designs_exist(self):
        for name in INTERACTIVE + ["index.html", "atlas-core.js", "atlas-panes.js"]:
            self.assertTrue((DESIGNS / name).exists(), f"missing designs/{name}")

    def test_each_design_uses_the_shared_data_layer(self):
        for name in INTERACTIVE:
            body = (DESIGNS / name).read_text(encoding="utf-8")
            self.assertIn("atlas-core.js", body, f"{name} does not load the core")
            self.assertIn("atlas-panes.js", body, f"{name} does not load the shared panes")

    def test_no_design_reimplements_the_shared_panes(self):
        """Duplicated pane code is exactly how five designs stop agreeing."""
        for name in INTERACTIVE:
            body = (DESIGNS / name).read_text(encoding="utf-8")
            self.assertNotIn("function lanesHTML", body, f"{name} has its own pane code")
            self.assertNotIn("function hardwareHTML", body, f"{name} has its own pane code")

    def test_no_duplicate_element_ids(self):
        for name in INTERACTIVE + ["index.html"]:
            parser = IdCollector()
            parser.feed((DESIGNS / name).read_text(encoding="utf-8"))
            dupes = sorted({i for i in parser.ids if parser.ids.count(i) > 1})
            self.assertFalse(dupes, f"{name} has duplicate ids: {dupes}")

    def test_no_css_custom_property_declared_twice_in_a_row(self):
        """A stray character once produced '--line:#1e3category; --line:#1e3552;'."""
        for name in INTERACTIVE + ["index.html"]:
            body = (DESIGNS / name).read_text(encoding="utf-8")
            doubles = re.findall(r"--(\w+):[^;]*;\s*--\1:", body)
            self.assertFalse(doubles, f"{name} redeclares {doubles}")

    def test_no_stray_control_characters(self):
        for name in INTERACTIVE + ["index.html", "atlas-core.js", "atlas-panes.js"]:
            body = (DESIGNS / name).read_text(encoding="utf-8")
            stray = {hex(ord(c)) for c in body if ord(c) < 32 and c not in "\n\r\t"}
            self.assertFalse(stray, f"{name} has control characters {stray}")

    def test_every_design_declares_a_distinct_title(self):
        titles = []
        for name in INTERACTIVE:
            body = (DESIGNS / name).read_text(encoding="utf-8")
            match = re.search(r"<title>(.*?)</title>", body)
            self.assertIsNotNone(match, f"{name} has no title")
            titles.append(match.group(1))
        self.assertEqual(len(titles), len(set(titles)), "designs share a title")

    def test_gallery_links_to_every_design(self):
        gallery = (DESIGNS / "index.html").read_text(encoding="utf-8")
        for name in INTERACTIVE:
            self.assertIn(name, gallery, f"gallery does not link {name}")
        self.assertIn("../index.html", gallery, "gallery does not link the Graphite design")


class TheSharedCore(unittest.TestCase):
    def setUp(self):
        self.core = (DESIGNS / "atlas-core.js").read_text(encoding="utf-8")
        self.panes = (DESIGNS / "atlas-panes.js").read_text(encoding="utf-8")

    def test_core_declares_every_tab_charles_asked_for(self):
        for tab in ("agents", "skills", "tools", "plugins", "mcp",
                    "routes", "hardware", "custom", "suggest"):
            self.assertIn(f"id: '{tab}'", self.core, f"missing the {tab} tab")

    def test_scan_commands_exist_for_every_platform(self):
        for platform in ("windows", "wsl", "linux", "macos"):
            self.assertIn(platform, self.core)

    def test_apple_unified_memory_is_called_out(self):
        """Charles asked specifically; unified memory is shared with the GPU."""
        payload = json.dumps(data())
        self.assertIn("Unified memory", payload)

    def test_browser_storage_failures_are_survivable(self):
        """Private windows throw on localStorage; the page must still render."""
        self.assertIn("catch", self.core)
        self.assertIn("localStorage", self.core)

    def test_lane_filters_compose_rather_than_replace(self):
        self.assertIn("activeFamilies", self.core)
        self.assertIn("activeKinds", self.core)

    def test_detail_exposes_connections_routes_and_command(self):
        for field in ("connections", "routes", "command", "laneSource"):
            self.assertIn(field, self.core)

    def test_panes_never_transmit_suggestions(self):
        """Suggestions are local. No fetch or beacon may appear in the panes."""
        for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon"):
            self.assertNotIn(forbidden, self.panes,
                             f"panes must not transmit; found {forbidden}")


if __name__ == "__main__":
    unittest.main()

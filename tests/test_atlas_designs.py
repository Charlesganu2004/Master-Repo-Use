"""Twenty-eight designs share one data layer. These stop them drifting.

The data layer is generated from files that exist, so the most valuable checks
are the ones that catch a lane pointing at something deleted, a component in a
lane that is gone, a route naming a component that never existed, and a private
catalog slug reaching a file that gets published.
"""
import json
import importlib.util
import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "atlas-data.json"
DESIGNS = ROOT / "designs"
INTERACTIVE = [
    # The first thirteen share the atlas-next runtime and its palette layer.
    "d3-console.html", "d4-orbital.html", "d5-blueprint.html",
    "d6-graphite.html", "d7-material.html",
    "d8-metro.html", "d9-workbench.html", "d10-journal.html",
    "d11-command.html", "d12-index.html", "d13-skill-tree.html",
    "d14-river.html", "d15-city.html",
    # The last fifteen share the DATA and the INSPECTOR and nothing else. Each
    # owns its shell, palette, type system and motion law, because the previous
    # set called one shared shell function and so read as a single design with a
    # different chart dropped into the middle of it.
    "d16-declassified.html", "d17-spatial.html", "d18-boresight.html",
    "d19-vitrine.html", "d20-tube.html", "d21-poster.html",
    "d22-membrane.html", "d23-panes.html", "d24-plate.html",
    "d25-riso.html", "d26-stage.html", "d27-machined.html",
    "d28-depth.html", "d29-reactor.html", "d30-atrium.html",
]

EXHIBITION_SCENES = {
    "d16-declassified.html": "declassified",
    "d17-spatial.html": "spatial",
    "d18-boresight.html": "boresight",
    "d19-vitrine.html": "vitrine",
    "d20-tube.html": "tube",
    "d21-poster.html": "poster",
    "d22-membrane.html": "membrane",
    "d23-panes.html": "panes",
    "d24-plate.html": "plate",
    "d25-riso.html": "riso",
    "d26-stage.html": "stage",
    "d27-machined.html": "machined",
    "d28-depth.html": "depth",
    "d29-reactor.html": "reactor",
    "d30-atrium.html": "atrium",
}

# Retired with d18, d19 and d20. Those three shipped an authored .ts/.jsx/.tsx
# beside a compiled .js; the fifteen that replaced them are single self-contained
# files, so there is no compiled-from pair left to keep honest.
AUTHORED_SOURCE_PAIRS = []

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

    def test_the_private_file_does_carry_catalog_entries(self):
        """Otherwise the redaction test below would pass vacuously.

        atlas-data.json at the repository root is a private working artifact. It
        is meant to contain the catalog; the local designs are useless without it.
        The published copy is a different file, built by redacting this one.
        """
        entries = [c for c in self.d["components"] if c.get("private")]
        self.assertGreater(len(entries), 300,
                           "the private data layer lost its catalog entries")

    def test_no_private_catalog_slug_survives_into_the_published_artifact(self):
        """Checked on the built artifact, not the source, because they differ.

        Verified against the real catalog rather than by guessing what a slug
        looks like: prose such as "Finance/Trading" is slug-shaped and harmless,
        while an actual unallowlisted repository name is the thing that matters.
        """
        published = ROOT / "_site" / "designs" / "atlas-data.json"
        if not published.exists():
            self.skipTest("run scripts/build_public_site.py first")
        allow, catalog = set(), set()
        for path in (ROOT / "repo-lists").glob("*.txt"):
            for line in path.read_text(encoding="utf-8").splitlines():
                candidate = line.split("#")[0].strip()
                if not re.fullmatch(r"[\w.-]+/[\w.-]+", candidate):
                    continue
                (allow if path.stem == "public-allowlist" else catalog).add(candidate)
        blob = published.read_text(encoding="utf-8")
        leaked = sorted(slug for slug in (catalog - allow) if slug in blob)
        self.assertFalse(leaked, f"private catalog slugs in published data: {leaked[:8]}")

    def test_the_published_artifact_drops_every_private_component(self):
        published = ROOT / "_site" / "designs" / "atlas-data.json"
        if not published.exists():
            self.skipTest("run scripts/build_public_site.py first")
        data = json.loads(published.read_text(encoding="utf-8"))
        self.assertTrue(data["meta"].get("redacted"), "published data is not marked redacted")
        self.assertFalse([c for c in data["components"] if c.get("private")])
        self.assertEqual(len(data["lanes"]), len(self.d["lanes"]),
                         "lanes should survive redaction; only entries are private")

    def test_setup_recipes_are_explicit_and_catalog_clones_are_not_setup(self):
        recipes = {recipe["id"]: recipe for recipe in self.d.get("setupRecipes", [])}
        self.assertIn("master-repo-global", recipes)
        for component in self.d["components"]:
            recipe_id = component.get("setupRecipe")
            if recipe_id:
                self.assertIn(recipe_id, recipes, component["id"])
            if component.get("slug"):
                self.assertNotIn("setupRecipe", component,
                                 "catalogued is not the same thing as reviewed for setup")
                self.assertNotIn("cmd", component,
                                 "a bare repository clone must not masquerade as setup")
                self.assertEqual(component.get("setupState"), "review-required")

    def test_master_repo_setup_is_real_for_every_platform(self):
        recipe = next(r for r in self.d["setupRecipes"] if r["id"] == "master-repo-global")
        for platform in ("windows", "wsl", "macos", "linux", "other"):
            command = recipe["commands"].get(platform, "")
            self.assertIn("setup-global-ai", command)
            self.assertNotRegex(command, r"REVIEWED_VERSION|<[^>]+>")
        by_id = {component["id"]: component for component in self.d["components"]}
        self.assertEqual(by_id["task-intake"].get("setupRecipe"), "master-repo-global")
        self.assertEqual(by_id["scope-resolver"].get("setupRecipe"), "master-repo-global")


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


class ThePublicDesignBuilder(unittest.TestCase):
    """Publication keeps authored sources and cannot retain a removed design."""

    def test_sources_are_copied_and_stale_top_level_files_are_cleared(self):
        script = ROOT / "scripts" / "build_public_site.py"
        spec = importlib.util.spec_from_file_location("atlas_public_builder_test", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)

        with tempfile.TemporaryDirectory() as scratch:
            scratch_path = pathlib.Path(scratch)
            private = scratch_path / "private-designs"
            public = scratch_path / "public-designs"
            private.mkdir()
            public.mkdir()
            private_data = scratch_path / "atlas-data.json"
            private_data.write_text("{}", encoding="utf-8")

            for name in ("page.html", "runtime.js", "source.ts", "source.jsx", "source.tsx"):
                (private / name).write_text(f"/* {name} */", encoding="utf-8")
            (private / "ignored.exe").write_text("not published", encoding="utf-8")
            stale = public / "d2-constellation.html"
            stale.write_text("obsolete", encoding="utf-8")

            builder.PRIVATE_DESIGNS = private
            builder.PUBLIC_DESIGNS = public
            builder.PRIVATE_ATLAS_DATA = private_data
            self.assertEqual(builder.build_designs(), [])

            self.assertFalse(stale.exists(), "a removed design survived publication")
            for name in ("page.html", "runtime.js", "source.ts", "source.jsx", "source.tsx"):
                self.assertTrue((public / name).exists(), f"publication omitted {name}")
            self.assertFalse((public / "ignored.exe").exists())


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
        for name in INTERACTIVE + ["index.html", "atlas-core.js", "atlas-panes.js",
                                   "atlas-theme.js", "themes.css"]:
            self.assertTrue((DESIGNS / name).exists(), f"missing designs/{name}")

    def test_each_design_uses_the_shared_data_layer(self):
        for name in INTERACTIVE:
            body = (DESIGNS / name).read_text(encoding="utf-8")
            self.assertIn("atlas-core.js", body, f"{name} does not load the core")
            self.assertIn("atlas-panes.js", body, f"{name} does not load the shared panes")

    def test_last_fifteen_load_their_expected_exhibition_scene(self):
        self.assertTrue((DESIGNS / "atlas-exhibition.css").is_file())
        self.assertTrue((DESIGNS / "atlas-exhibition.js").is_file())
        for name, scene in EXHIBITION_SCENES.items():
            body = (DESIGNS / name).read_text(encoding="utf-8")
            self.assertIn('href="atlas-exhibition.css"', body,
                          f"{name} does not load the exhibition styles")
            self.assertIn('src="atlas-exhibition.js"', body,
                          f"{name} does not load the exhibition runtime")
            self.assertIn(f"AtlasExhibition.mount('{scene}')", body,
                          f"{name} does not mount its {scene!r} scene")

    def test_pages_redeploys_when_a_design_changes(self):
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(
            encoding="utf-8"
        )
        self.assertRegex(workflow, r"(?m)^\s*-\s*['\"]designs/\*\*['\"]\s*$",
                         "Pages ignores design-only commits")

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
        # Graphite used to live at the repository root; it is now d6 alongside
        # the others, rebuilt on the shared engine.
        gallery = (DESIGNS / "index.html").read_text(encoding="utf-8")
        for name in INTERACTIVE:
            self.assertIn(name, gallery, f"gallery does not link {name}")

    def test_constellation_is_removed_from_source_and_gallery(self):
        gallery = (DESIGNS / "index.html").read_text(encoding="utf-8")
        self.assertFalse((DESIGNS / "d2-constellation.html").exists())
        self.assertNotIn("d2-constellation.html", gallery)
        self.assertNotIn("Constellation", gallery)

    def test_new_designs_keep_authored_source_beside_browser_runtime(self):
        for page_name, source_name, runtime_name in AUTHORED_SOURCE_PAIRS:
            source = DESIGNS / source_name
            runtime = DESIGNS / runtime_name
            self.assertTrue(source.is_file(), f"missing authored source designs/{source_name}")
            self.assertTrue(runtime.is_file(), f"missing browser runtime designs/{runtime_name}")
            page = (DESIGNS / page_name).read_text(encoding="utf-8")
            self.assertIn(runtime_name, page,
                          f"{page_name} does not load its compiled browser runtime")
            self.assertIn("AtlasNext.boot", runtime.read_text(encoding="utf-8"),
                          f"{runtime_name} does not start an Atlas design")

    def test_the_two_designs_charles_picked_are_marked_as_such(self):
        gallery = (DESIGNS / "index.html").read_text(encoding="utf-8")
        self.assertIn("your pick", gallery)
        for name in ("d6-graphite.html", "d3-console.html"):
            index = gallery.index(name)
            self.assertIn("pick: true", gallery[index:index + 400],
                          f"{name} is not marked as a pick")


class TheSharedCore(unittest.TestCase):
    def setUp(self):
        self.core = (DESIGNS / "atlas-core.js").read_text(encoding="utf-8")
        self.panes = (DESIGNS / "atlas-panes.js").read_text(encoding="utf-8")

    def test_core_declares_every_tab_charles_asked_for(self):
        for tab in ("agents", "skills", "tools", "plugins", "mcp",
                    "routes", "hardware", "basket", "custom", "suggest"):
            self.assertIn(f"id: '{tab}'", self.core, f"missing the {tab} tab")

    def test_every_platform_is_selectable_and_has_a_scan(self):
        for platform in ("windows", "wsl", "linux", "macos", "other"):
            self.assertIn(f"id: '{platform}'", self.core, f"{platform} is not selectable")
            self.assertIn(f"{platform}:", self.core, f"{platform} has no scan command")

    def test_platform_is_chosen_not_sniffed(self):
        """A user-agent guess hands someone the wrong shell, and WSL is invisible."""
        self.assertNotIn("navigator.userAgent", self.core)
        self.assertIn("setPlatform", self.core)

    def test_no_command_is_offered_before_a_platform_is_chosen(self):
        self.assertIn("if (!state.platform) return null;", self.core)

    def test_all_four_hardware_fields_exist(self):
        for field in ("ram", "vram", "storage", "cpu"):
            self.assertIn(f"id: '{field}'", self.core, f"missing the {field} field")

    def test_apple_unified_memory_is_handled_not_double_counted(self):
        """On Apple silicon VRAM is the same pool as RAM, so it must not add."""
        self.assertIn("usableMemory", self.core)
        self.assertIn("if (state.platform === 'macos') return ram;", self.core)

    def test_filters_compose_across_family_kind_sub_and_text(self):
        for field in ("activeFamilies", "activeKinds", "activeSubs", "query"):
            self.assertIn(field, self.core, f"{field} is not a filter dimension")

    def test_the_build_basket_produces_one_script(self):
        for fn in ("addToBasket", "removeFromBasket", "combinedCommand"):
            self.assertIn(fn, self.core, f"missing {fn}")

    def test_build_uses_setup_recipes_not_action_commands(self):
        for marker in ("setupRecipeFor", "setupCommandFor", "canBuild", "commands.join('\\n')"):
            self.assertIn(marker, self.core)
        self.assertIn("The copy block contains commands only", self.panes)
        self.assertNotIn("Master Repo Atlas combination", self.core)

    def test_every_plus_surface_checks_setup_readiness(self):
        for name in ("atlas-panes.js", "atlas-next.js", "d3-console.html",
                     "d6-graphite.html", "d7-material.html"):
            body = (DESIGNS / name).read_text(encoding="utf-8")
            self.assertIn("canBuild", body, f"{name} still offers + without a setup recipe")

    def test_combined_setup_is_commands_only_deduped_and_exact_platform(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node is not installed")
        core_path = json.dumps(str(DESIGNS / "atlas-core.js"))
        script = f"""
const A = require({core_path});
A.state.data = {{
  setupRecipes: [
    {{id:'same', kind:'setup', state:'ready', commands:{{windows:'winget install Example.Tool',linux:'sudo apt install example'}}}},
    {{id:'linux-only', kind:'setup', state:'ready', commands:{{linux:'sudo apt install linux-only'}}}},
    {{id:'placeholder', kind:'setup', state:'ready', commands:{{windows:'winget install <PACKAGE>'}}}}
  ], routes: [], hardware: []
}};
const components = [
  {{id:'one', name:'One', lane:'lane', setupRecipe:'same'}},
  {{id:'two', name:'Two', lane:'lane', setupRecipe:'same'}},
  {{id:'source', name:'Source only', lane:'lane', sourceUrl:'https://github.com/example/source'}},
  {{id:'linux', name:'Linux only', lane:'lane', setupRecipe:'linux-only'}},
  {{id:'placeholder', name:'Placeholder', lane:'lane', setupRecipe:'placeholder'}}
];
A.state.components = components;
A.state.byId.clear(); components.forEach(c => A.state.byId.set(c.id, c));
A.state.lanesById.clear(); A.state.lanesById.set('lane', {{id:'lane', name:'Lane'}});
A.setPlatform('windows');
const added = [A.addToBasket('one'), A.addToBasket('two')];
const rejected = [A.addToBasket('source'), A.addToBasket('linux'), A.addToBasket('placeholder')];
console.log(JSON.stringify({{added, rejected, result:A.combinedCommand(), linuxFallback:A.setupCommandFor(components[3])}}));
"""
        proc = subprocess.run([node, "-e", script], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["added"], [True, True])
        self.assertEqual(result["rejected"], [False, False, False])
        self.assertIsNone(result["linuxFallback"])
        self.assertEqual(result["result"]["text"], "winget install Example.Tool")
        self.assertEqual(result["result"]["commandCount"], 1)
        self.assertNotIn("#", result["result"]["text"])

    def test_the_popover_carries_description_command_and_plus(self):
        for marker in ("popname", "data-pop-add", "popdesc"):
            self.assertIn(marker, self.panes, f"popover missing {marker}")

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


class ThePalettes(unittest.TestCase):
    """One palette layer for twenty-eight designs, so colours can be judged together.

    Each design keeps its own layout and defines its own tokens; themes.css
    overrides those tokens at higher specificity. A design that stops loading it
    silently drops out of the comparison, which these tests prevent.
    """

    PALETTES = ["ember", "ash", "viper", "cobalt", "plum", "sand"]
    TOKENS = ["--bg", "--panel", "--line", "--ink", "--dim", "--accent",
              "--instruction", "--capability", "--knowledge", "--control",
              "--model", "--delivery"]

    def setUp(self):
        self.css = (DESIGNS / "themes.css").read_text(encoding="utf-8")
        self.js = (DESIGNS / "atlas-theme.js").read_text(encoding="utf-8")

    def test_every_palette_is_declared_in_css_and_js(self):
        for palette in self.PALETTES:
            self.assertIn(f'[data-theme="{palette}"]', self.css, f"{palette} missing from CSS")
            self.assertIn(f"id: '{palette}'", self.js, f"{palette} missing from the switcher")

    def test_every_palette_defines_every_token(self):
        """A missing token silently falls back to the design's own colour."""
        for palette in self.PALETTES:
            start = self.css.index(f'[data-theme="{palette}"]')
            block = self.css[start:self.css.index("}", start)]
            for token in self.TOKENS:
                self.assertIn(token, block, f"{palette} does not define {token}")

    def test_red_and_black_is_the_default(self):
        """Charles asked for red and black; ember is that palette."""
        self.assertIn("'ember'", self.js)
        for name in INTERACTIVE:
            body = (DESIGNS / name).read_text(encoding="utf-8")
            self.assertIn("AtlasTheme.mount", body, f"{name} has no palette switcher")
            self.assertIn("'ember'", body, f"{name} does not default to ember")

    def test_every_design_boots_a_layer_that_actually_exists(self):
        """A page whose boot key is unknown throws on load and passes every other test.

        Nothing else here reads the argument to AtlasNext.boot(). A design could
        ship pointing at a layer that was never written, or at one whose key was
        renamed, and the file checks, the gallery check and the palette check
        would all still be green while the page rendered nothing but an error in
        the console. This is the check that the page runs at all.
        """
        runtime = (DESIGNS / "atlas-next.js").read_text(encoding="utf-8")
        for name in INTERACTIVE:
            body = (DESIGNS / name).read_text(encoding="utf-8")
            key = re.search(r"AtlasNext\.boot\('([\w-]+)'\)", body)
            if not key:
                continue          # the five original designs boot their own runtime
            key = key.group(1)
            for registry in ("LABELS", "SHELLS", "MAPS"):
                start = runtime.index(f"{registry} = {{" if registry != "LABELS"
                                      else "const LABELS = {")
                block = runtime[start:start + 20000]
                self.assertIn(key, block,
                              f"{name} boots '{key}', which is missing from {registry}")

    def test_every_design_loads_the_palette_layer(self):
        for name in INTERACTIVE + ["index.html"]:
            body = (DESIGNS / name).read_text(encoding="utf-8")
            self.assertIn("themes.css", body, f"{name} does not load themes.css")
            self.assertIn("atlas-theme.js", body, f"{name} does not load the switcher")

    def test_a_palette_can_travel_in_a_url(self):
        self.assertIn("URLSearchParams", self.js)
        self.assertIn("theme", self.js)

    def test_there_is_a_light_palette(self):
        """Every dark theme looks fine until you sit next to a window."""
        self.assertIn('[data-theme="sand"]', self.css)

    def test_the_gallery_links_every_design_in_every_palette(self):
        gallery = (DESIGNS / "index.html").read_text(encoding="utf-8")
        for name in INTERACTIVE:
            self.assertIn(name, gallery, f"gallery does not link {name}")
        self.assertIn("?theme=", gallery, "gallery links carry no palette")

    def test_the_palette_class_does_not_collide_with_a_design_class(self):
        """themes.css owns .swatch; the gallery preview once inherited its 22px."""
        gallery = (DESIGNS / "index.html").read_text(encoding="utf-8")
        self.assertNotIn(".swatch{height", gallery,
                         "the gallery redefines .swatch, which themes.css owns")


class TheGalleryCounts(unittest.TestCase):
    """The gallery must not assert a number it cannot see.

    The published copy is redacted and holds fewer components than the local one,
    so a hardcoded figure is wrong in one place or the other. It went live saying
    777 when the published data had 376.
    """

    def setUp(self):
        self.gallery = (DESIGNS / "index.html").read_text(encoding="utf-8")

    def test_counts_are_not_hardcoded(self):
        self.assertIn('id="counts"', self.gallery)
        self.assertIn("window.__ATLAS_DATA__", self.gallery,
                      "the gallery does not read the data it describes")

    def test_the_gallery_loads_the_data(self):
        self.assertIn("atlas-data.js", self.gallery)

    def test_a_redacted_copy_says_so(self):
        self.assertIn("meta.redacted", self.gallery,
                      "a redacted publish must explain its smaller counts")

    def test_no_stale_component_figure_is_asserted(self):
        # Any four-digit-ish literal next to "components" is a hardcoded claim.
        stale = re.findall(r"<b>\d{3,}</b>\s*components", self.gallery)
        self.assertFalse(stale, f"hardcoded component counts: {stale}")


class BuildShowsOneSystem(unittest.TestCase):
    """Build answers with the system you selected, not a menu of five.

    This showed all five platforms at once. Charles pointed out the obvious
    problem: you choose your system in step 1, so making you find yours among
    four you cannot run is the wrong answer to a question you already answered.
    """

    def setUp(self):
        self.panes = (DESIGNS / "atlas-panes.js").read_text(encoding="utf-8")

    def test_the_heading_names_the_selected_system(self):
        self.assertIn("Setup commands for ${esc(chosen.label)}", self.panes)

    def test_only_the_current_platform_renders_outside_the_disclosure(self):
        self.assertIn("all.find(entry => entry.current)", self.panes)
        self.assertIn("all.filter(entry => !entry.current)", self.panes)

    def test_the_other_systems_are_behind_a_closed_disclosure(self):
        section = self.panes[self.panes.index("function setupCommandsSection"):]
        section = section[:section.index("function scriptBlock")]
        self.assertIn("<details class=\"otheros\">", section)
        self.assertNotIn("<details open", section, "the disclosure must start closed")

    def test_choosing_no_platform_prompts_rather_than_guessing(self):
        self.assertIn("Choose your operating system in step 1", self.panes)

    def test_the_other_platforms_are_kept_not_deleted(self):
        """Handing a teammate the macOS script is worth one collapsed section."""
        self.assertIn("combinedCommandAll", self.panes)
        self.assertIn("does not run", self.panes)

    def test_every_design_styles_the_disclosure(self):
        """Either inline, or via the shared sheet the newer designs load."""
        shared = (DESIGNS / "atlas-next.css").read_text(encoding="utf-8")
        for name in INTERACTIVE:
            body = (DESIGNS / name).read_text(encoding="utf-8")
            styled = ".otheros{" in body or (
                "atlas-next.css" in body and ".otheros{" in shared)
            self.assertTrue(styled, f"{name} does not style the disclosure")


if __name__ == "__main__":
    unittest.main()

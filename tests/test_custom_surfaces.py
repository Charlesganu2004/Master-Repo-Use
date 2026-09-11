"""The "+" on every client-surface group, on the main page and every design.

A client the vetted list does not name, an open frontier model behind an API,
Copilot in an editor, a CLI with no hook, a chat product, gets exact commands
from one shared generator (designs/custom-surfaces.js) filled from templates in
atlas-data.json. These tests hold the three things that could quietly go wrong:
a page that stops loading the generator, a template naming a flag the CLI does
not have, and a field pattern that lets a shell metacharacter into a command
someone copies.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys
import tomllib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_atlas_data  # noqa: E402

DATA = json.loads((ROOT / "designs" / "atlas-data.json").read_text(encoding="utf-8"))
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
ATLAS_JS = (ROOT / "atlas.js").read_text(encoding="utf-8")
PANES_JS = (ROOT / "designs" / "atlas-panes.js").read_text(encoding="utf-8")


class GeneratorRuntime(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is required for the generator runtime")
    def test_generator_runs_against_the_real_payload(self):
        result = subprocess.run(
            ["node", str(ROOT / "tests" / "custom_surfaces_runtime.cjs")],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Custom surfaces runtime: OK", result.stdout)


class BothPagesUseTheSharedGenerator(unittest.TestCase):
    def test_main_page_loads_the_generator_before_atlas_js(self):
        self.assertIn('<script src="designs/custom-surfaces.js" defer></script>', INDEX)
        self.assertLess(INDEX.index("designs/custom-surfaces.js"), INDEX.index('src="atlas.js"'),
                        "deferred scripts run in order; the generator must come first")

    def test_designs_fetch_the_generator_from_beside_themselves(self):
        self.assertIn("script.src = 'custom-surfaces.js'", PANES_JS)
        self.assertTrue((ROOT / "designs" / "custom-surfaces.js").is_file())

    def test_neither_page_carries_its_own_copy_of_the_templates(self):
        for name, body in (("atlas.js", ATLAS_JS), ("atlas-panes.js", PANES_JS)):
            with self.subTest(page=name):
                self.assertIn("CustomSurfaces", body)
                self.assertIn("data-add-client", body)
                self.assertNotIn("master-harness-super --serve", body,
                                 "a command template in page code is a second copy that will drift")

    def test_every_group_renders_the_plus(self):
        self.assertIn("customClientsHtml(group.id)", ATLAS_JS)
        self.assertIn("customClientHTML(group.id)", PANES_JS)

    def test_the_public_build_copies_the_generator(self):
        # build_designs publishes every flat .js file in designs/; the generator
        # must stay flat and a .js file, or the public page loses the "+".
        source = (ROOT / "scripts" / "build_public_site.py").read_text(encoding="utf-8")
        self.assertIn('".html", ".js", ".css"', source)
        self.assertEqual((ROOT / "designs" / "custom-surfaces.js").parent.name, "designs")


class TemplatesMatchTheRealCli(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        cls.scripts = set(pyproject["project"]["scripts"])
        cls.help = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "harness_super.py"), "--help"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout

    def test_payload_ships_the_kinds_at_top_level(self):
        kinds = DATA.get("customSurfaceKinds")
        self.assertTrue(kinds, "atlas-data.json has no customSurfaceKinds; rebuild it")
        self.assertEqual([k["id"] for k in kinds],
                         [k["id"] for k in build_atlas_data.CUSTOM_SURFACE_KINDS])
        self.assertNotIn("customSurfaceKinds", DATA.get("pipeline", {}))

    def test_every_command_names_an_installed_entry_point_and_real_flags(self):
        for kind in DATA["customSurfaceKinds"]:
            for step in kind["steps"]:
                command = step["command"]
                if not command.startswith("master-harness"):
                    continue
                with self.subTest(kind=kind["id"], command=command):
                    program = command.split()[0]
                    self.assertIn(program, self.scripts)
                    if program == "master-harness-super":
                        for flag in re.findall(r"(?<!\S)(--[a-z][a-z-]*)", command):
                            self.assertIn(flag, self.help, f"{flag} is not a harness_super flag")

    def test_every_group_preselects_a_kind(self):
        groups = {g["id"] for g in DATA["surfaceGroups"]}
        covered = {g for kind in DATA["customSurfaceKinds"] for g in kind["defaultFor"]}
        self.assertEqual(groups, covered, "a group whose + preselects nothing")

    def test_chat_products_are_shown_by_name_and_sent_by_id(self):
        chat = next(k for k in DATA["customSurfaceKinds"] if k["id"] == "chat")
        field = chat["fields"][0]
        self.assertEqual(set(field["optionLabels"]), set(field["options"]))
        self.assertEqual(field["optionLabels"]["chatgpt"], "ChatGPT")
        self.assertIn("(field.optionLabels || {})[option]", ATLAS_JS)
        self.assertIn("(field.optionLabels || {})[option]", PANES_JS)

    def test_limits_are_stated_for_every_kind(self):
        for kind in DATA["customSurfaceKinds"]:
            with self.subTest(kind=kind["id"]):
                self.assertTrue(kind["limit"].strip())
                self.assertTrue(kind["plain"].strip())


class PatternsAreAllowlists(unittest.TestCase):
    """The same patterns, checked in Python, so a JS-only run is not the only guard."""

    URL = re.compile(build_atlas_data.URL_PATTERN)
    COMMAND = re.compile(build_atlas_data.COMMAND_PATTERN)

    def test_urls_a_person_would_paste_are_accepted(self):
        for url in ("https://openrouter.ai/api/v1", "http://127.0.0.1:11434",
                    "http://localhost:8000/v1", "http://[::1]:11434",
                    "https://api.together.xyz/v1", "https://api.fireworks.ai/inference/v1"):
            with self.subTest(url=url):
                self.assertTrue(self.URL.match(url))

    def test_urls_that_would_run_something_are_refused(self):
        for url in ("https://x.example/$(id)", "https://x.example/${IFS}",
                    "https://x.example/`id`", "https://x.example/%USERPROFILE%",
                    "https://x.example/a;b", "https://x.example/a b", "https://x.example/\"",
                    "https://x.example/a\nb", "javascript:alert(1)", "file:///etc/passwd"):
            with self.subTest(url=url):
                self.assertIsNone(self.URL.match(url))

    def test_commands_refuse_every_shell_operator(self):
        self.assertTrue(self.COMMAND.match("aider --message"))
        self.assertTrue(self.COMMAND.match("ollama run qwen3:4b"))
        for char in ";&|<>$`()%\"'\n!*?{}[]#~^":
            with self.subTest(char=char):
                self.assertIsNone(self.COMMAND.match(f"aider {char} x"))

    def test_the_build_refuses_a_field_with_no_guard(self):
        original = build_atlas_data.CUSTOM_SURFACE_KINDS
        try:
            build_atlas_data.CUSTOM_SURFACE_KINDS = [dict(original[0], fields=[
                {"id": "url", "label": "Base URL"}])]
            with self.assertRaises(SystemExit):
                build_atlas_data.custom_surface_payload()
        finally:
            build_atlas_data.CUSTOM_SURFACE_KINDS = original

    def test_the_build_refuses_a_placeholder_no_field_fills(self):
        original = build_atlas_data.CUSTOM_SURFACE_KINDS
        try:
            build_atlas_data.CUSTOM_SURFACE_KINDS = [dict(original[2], steps=[
                {"label": "x", "command": "master-harness-super --bundle {product}"}])]
            with self.assertRaises(SystemExit):
                build_atlas_data.custom_surface_payload()
        finally:
            build_atlas_data.CUSTOM_SURFACE_KINDS = original


if __name__ == "__main__":
    unittest.main()

"""Models and global rules must ship real commands, not a promise of one.

Charles's report was specific: the atlas showed setup commands for the repository
itself and nothing for the models or the global rules. A node with a plus button
and no recipe behind it is worse than a node with no button, because it looks
finished.

Two rules are in tension here and both get tested:

* Catalog repositories stay fail-closed. A GitHub URL is not a vetted install,
  and the change that gave models recipes must not have opened that gate.
* Model tags and client rule files are not catalog entries. Each names a vendor
  runtime at an exact tag, or a script inside this repository, so each carries a
  reviewed recipe and Build can emit it.
"""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "atlas-data.json").read_text(encoding="utf-8"))
RECIPES = {r["id"]: r for r in DATA["setupRecipes"]}
COMPONENTS = {c["id"]: c for c in DATA["components"]}
PLATFORMS = {"windows", "wsl", "macos", "linux", "other"}


def components_in(lane: str) -> list[dict]:
    return [c for c in DATA["components"] if c.get("lane") == lane]


class EveryRecipeIsUsable(unittest.TestCase):
    """Whatever else a recipe is, it has to be runnable without editing."""

    def test_every_recipe_covers_every_platform(self):
        for rid, recipe in RECIPES.items():
            self.assertEqual(set(recipe["commands"]), PLATFORMS, rid)

    def test_no_recipe_contains_a_placeholder(self):
        """A <path-to-thing> is the caller doing the work, not the recipe."""
        for rid, recipe in RECIPES.items():
            for platform, command in recipe["commands"].items():
                self.assertNotRegex(command, r"<[a-z][a-z -]*>", f"{rid}/{platform}")

    def test_no_recipe_is_empty(self):
        for rid, recipe in RECIPES.items():
            for platform, command in recipe["commands"].items():
                self.assertGreater(len(command.strip()), 8, f"{rid}/{platform}")

    def test_every_recipe_states_its_trust_basis(self):
        for rid, recipe in RECIPES.items():
            self.assertIn(recipe["trust"], {"owner-repository", "named-vendor-runtime"}, rid)


class TheModelsHaveSetupCommands(unittest.TestCase):
    LANE = "sys-model-setup"

    def test_the_lane_exists(self):
        self.assertTrue(components_in(self.LANE), "no model setup lane was generated")

    def test_the_runtime_comes_before_the_tags(self):
        """ollama pull fails with no ollama. Order in the lane is the instruction."""
        order = [c["id"] for c in sorted(components_in(self.LANE), key=lambda c: c["order"])]
        self.assertEqual(order[0], "ollama-runtime")

    def test_every_tier_that_can_host_anything_names_something(self):
        """4 GB, Apple and GPU list nothing on purpose; the RAM tiers must not."""
        for tier in DATA["hardware"]:
            if tier["id"] in {"8gb", "16gb", "32gb"}:
                self.assertTrue(tier["models"], f"{tier['id']} offers no model at all")

    def test_every_vetted_ollama_model_can_be_installed(self):
        """The lane is derived from the hardware document, so none may go missing."""
        vetted = {model["tag"] for model in json.loads(
            (ROOT / "docs" / "hardware-profiles.json").read_text(encoding="utf-8"))["models"]
            if model.get("runtime") == "ollama"}
        offered = {c["name"] for c in components_in(self.LANE)}
        self.assertEqual(vetted - offered, set(), "vetted models with no setup command")

    def test_every_model_component_is_setup_ready(self):
        for component in components_in(self.LANE):
            self.assertEqual(component["setupState"], "ready", component["id"])
            self.assertIn(component["setupRecipe"], RECIPES, component["id"])

    def test_every_pull_names_a_tag_that_was_actually_vetted(self):
        """The tag must be one docs/hardware-profiles.json already records.

        A colon check was the first version of this, on the theory that a bare
        name means a floating :latest. It is a real concern, but ten of the
        thirty-six vetted tags are deliberately bare - phi4, mistral, phi3.5 -
        because the vendor's default tag is the intended one. So the rule that
        matters is not punctuation. It is that the atlas cannot offer to pull
        something the hardware document never vetted.
        """
        vetted = {model["tag"] for model in json.loads(
            (ROOT / "docs" / "hardware-profiles.json").read_text(encoding="utf-8"))["models"]}
        for component in components_in(self.LANE):
            command = component["cmd"]["linux"]
            if command.startswith("ollama pull"):
                self.assertIn(command.split()[-1], vetted, component["id"])

    def test_a_tier_tag_and_its_recipe_name_agree_exactly(self):
        """Easy Setup resolves a tier's tag to a recipe by name, so drift breaks it."""
        by_name = {c["name"]: c for c in components_in(self.LANE)}
        for tier in DATA["hardware"]:
            for tag in tier["models"]:
                self.assertIn(tag, by_name, f"{tier['id']} names {tag} with no recipe")
                self.assertEqual(by_name[tag]["cmd"]["linux"], f"ollama pull {tag}")

    def test_each_tag_records_its_download_size(self):
        """The tier question is 'does it fit', so the size has to be on the card."""
        for component in components_in(self.LANE):
            if component["cmd"]["linux"].startswith("ollama pull"):
                self.assertRegex(component["detail"], r"\d+(\.\d+)?\s*GB", component["id"])


class TheGlobalRulesHaveSetupCommands(unittest.TestCase):
    LANE = "sys-global-rules"

    def test_the_lane_exists(self):
        self.assertTrue(components_in(self.LANE), "no global rules lane was generated")

    def test_every_client_can_be_set_up_on_its_own(self):
        names = {c["id"] for c in components_in(self.LANE)}
        for client in ("claude", "codex", "gemini", "copilot", "cursor"):
            self.assertIn(f"rules-{client}", names, f"{client} has no standalone setup")

    def test_all_clients_at_once_is_offered_first(self):
        order = [c["id"] for c in sorted(components_in(self.LANE), key=lambda c: c["order"])]
        self.assertEqual(order[0], "rules-all-clients")

    def test_the_rules_commands_enable_auto_mode(self):
        """Charles asked for auto mode always on, so the recipe must pass the flag."""
        for client in ("all-clients", "claude", "codex", "gemini", "copilot", "cursor"):
            recipe = RECIPES[f"setup-rules-{client}"]
            self.assertIn("-AutoSkills", recipe["commands"]["windows"], client)
            self.assertIn("--auto-skills", recipe["commands"]["linux"], client)

    def test_cursor_recipe_selects_cursor_on_every_shell_family(self):
        recipe = RECIPES["setup-rules-cursor"]
        self.assertIn("-Client cursor", recipe["commands"]["windows"])
        for platform in ("wsl", "macos", "linux", "other"):
            self.assertIn("--client cursor", recipe["commands"][platform], platform)

    def test_cursor_is_available_in_easy_setup(self):
        clients = {client["id"] for client in DATA.get("profileClients", [])}
        self.assertIn("cursor", clients)

    def test_the_guards_are_installable(self):
        recipe = RECIPES["setup-rules-guards"]
        for command in recipe["commands"].values():
            self.assertIn("install_auto_mode.py", command)

    def test_a_verify_step_exists(self):
        """A setup you cannot check is a setup you have to believe.

        This asserted the literal marker MASTER-REPO-USE:BEGIN, because the step
        used to be a grep for it. The step is now verify_auto_mode.py, which
        checks the same block plus the hooks, the skills and the schema, and
        reports per client. The intent is unchanged and the proxy for it was
        the implementation detail, so the assertion moved to the intent.
        """
        recipe = RECIPES["setup-rules-verify"]
        self.assertTrue(recipe["commands"], "the verify recipe has no commands")
        for platform, command in recipe["commands"].items():
            self.assertIn("verify_auto_mode.py", command, platform)
            self.assertIn("--installed-only", command, platform)

    def test_the_verify_step_only_reads(self):
        """It runs on a machine that is already set up, so it must not change it."""
        body = (ROOT / "scripts" / "verify_auto_mode.py").read_text(encoding="utf-8")
        for writer in ("write_text(", "shutil.copy", "shutil.rmtree", "os.remove",
                       "unlink(", "mkdir("):
            self.assertNotIn(writer, body,
                             f"the verifier calls {writer}, so it is not read-only")

    def test_the_scripts_the_recipes_call_are_present(self):
        for name in ("setup-global-ai.ps1", "setup-global-ai.sh", "install_auto_mode.py"):
            self.assertTrue((ROOT / "scripts" / name).exists(), name)


class CatalogEntriesStayFailClosed(unittest.TestCase):
    """The regression this change could plausibly have caused."""

    def test_a_catalog_entry_never_gains_a_setup_recipe(self):
        for component in DATA["components"]:
            if component.get("slug"):
                self.assertNotIn("setupRecipe", component, component["id"])
                self.assertEqual(component["action"]["state"], "review-required")

    def test_third_party_runtime_stages_are_still_unavailable(self):
        """Only nodes with a reviewed recipe are ready; the rest still fail closed."""
        unavailable = [c for c in DATA["components"]
                       if c.get("setupState") == "unavailable"]
        self.assertTrue(unavailable, "nothing is fail-closed any more, which is wrong")
        for component in unavailable:
            self.assertNotIn("setupRecipe", component, component["id"])


class TheClientSelectorWorks(unittest.TestCase):
    """Functional, not textual: the script is run and the files it wrote counted.

    Grepping the source would pass on a script that parses the flag and ignores it.
    """

    SH = ROOT / "scripts" / "setup-global-ai.sh"
    FILES = {
        "claude": ".claude/CLAUDE.md",
        "codex": ".codex/AGENTS.md",
        "gemini": ".gemini/GEMINI.md",
        "copilot": ".copilot/copilot-instructions.md",
    }

    def setUp(self):
        if not shutil.which("bash"):
            self.skipTest("bash is not available")
        if not (ROOT / ".git").exists():
            self.skipTest("the script refuses to run outside a checkout")

    def run_setup(self, client: str):
        home = pathlib.Path(tempfile.mkdtemp(prefix=f"mru-{client}-"))
        env = dict(os.environ, HOME=str(home))
        proc = subprocess.run(
            ["bash", str(self.SH), str(ROOT), "--client", client, "--auto-skills"],
            env=env, capture_output=True, text=True)
        written = {name for name, path in self.FILES.items() if (home / path).exists()}
        shutil.rmtree(home, ignore_errors=True)
        return proc, written

    def test_a_single_client_writes_only_its_own_file(self):
        for client in self.FILES:
            proc, written = self.run_setup(client)
            self.assertEqual(proc.returncode, 0, proc.stderr[-400:])
            self.assertEqual(written, {client}, f"--client {client} wrote {written}")

    def test_all_writes_every_client(self):
        proc, written = self.run_setup("all")
        self.assertEqual(proc.returncode, 0, proc.stderr[-400:])
        self.assertEqual(written, set(self.FILES))

    def test_broken_python3_alias_uses_working_python(self):
        with tempfile.TemporaryDirectory(prefix="mru-python-alias-") as directory:
            bin_path = pathlib.Path(directory)
            broken = bin_path / "python3"
            broken.write_text("#!/bin/sh\nexit 49\n", encoding="utf-8")
            working = bin_path / "python"
            executable = pathlib.Path(sys.executable).as_posix()
            working.write_text(f'#!/bin/sh\nexec "{executable}" "$@"\n', encoding="utf-8")
            broken.chmod(0o755)
            working.chmod(0o755)
            with patch.dict(os.environ, {"PATH": str(bin_path) + os.pathsep + os.environ["PATH"]}):
                proc, written = self.run_setup("copilot")
            self.assertEqual(proc.returncode, 0, proc.stderr[-400:])
            self.assertEqual(written, {"copilot"})

    def test_gpt_is_an_accepted_alias_for_codex(self):
        proc, written = self.run_setup("gpt")
        self.assertEqual(proc.returncode, 0, proc.stderr[-400:])
        self.assertEqual(written, {"codex"})

    def test_an_unknown_client_is_rejected_rather_than_ignored(self):
        """Silently falling back to 'all' would write files nobody asked for."""
        proc, _ = self.run_setup("nonexistent")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Unknown --client", proc.stderr)


class TheSetupScriptsAreWellFormed(unittest.TestCase):
    def test_the_shell_script_parses(self):
        if not shutil.which("bash"):
            self.skipTest("bash is not available")
        proc = subprocess.run(["bash", "-n", str(ROOT / "scripts" / "setup-global-ai.sh")],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_no_literal_backslash_n_survives_in_shell_source(self):
        r"""A '\n' typed into a shell line prints a stray 'n'; it bit this file once."""
        source = (ROOT / "scripts" / "setup-global-ai.sh").read_text(encoding="utf-8")
        # Heredoc bodies are Python and shell wrappers, where \n is correct. Only
        # the shell lines of this script are in scope.
        terminator = None
        for number, line in enumerate(source.split("\n"), 1):
            if terminator is not None:
                if line.strip() == terminator:
                    terminator = None
                continue
            opened = re.search(r"<<-?'([A-Z]+)'", line)
            if opened:
                terminator = opened.group(1)
                continue
            if line.lstrip().startswith("#") or "printf" in line:
                continue
            self.assertNotIn("\\n", line, f"line {number}: {line.strip()[:70]}")

    def test_the_interpreter_is_resolved_not_assumed(self):
        """A discovered command may still be a broken Windows Store alias."""
        source = (ROOT / "scripts" / "setup-global-ai.sh").read_text(encoding="utf-8")
        self.assertIn("for candidate in python3 python", source)
        self.assertIn('command -v "$candidate"', source)
        self.assertIn('sys.exit(sys.version_info[0] != 3)', source)

    def test_the_powershell_script_validates_its_client_argument(self):
        source = (ROOT / "scripts" / "setup-global-ai.ps1").read_text(encoding="utf-8")
        self.assertIn("ValidateSet", source)
        for client in ("claude", "codex", "gemini", "copilot", "all", "gpt"):
            self.assertIn(f"'{client}'", source, client)


if __name__ == "__main__":
    unittest.main()

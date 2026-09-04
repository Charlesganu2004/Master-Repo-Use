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
import tempfile
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

    def test_every_hardware_tier_has_at_least_one_tag(self):
        names = {c["name"] for c in components_in(self.LANE)}
        for tier_tag in ("gemma2:2b", "phi3:mini", "phi3:medium", "gemma2:9b", "gemma2:27b"):
            self.assertIn(tier_tag, names, f"{tier_tag} has no setup command")

    def test_every_model_component_is_setup_ready(self):
        for component in components_in(self.LANE):
            self.assertEqual(component["setupState"], "ready", component["id"])
            self.assertIn(component["setupRecipe"], RECIPES, component["id"])

    def test_the_pull_commands_name_an_exact_tag(self):
        """'ollama pull gemma2' would fetch whatever latest happens to be today."""
        for component in components_in(self.LANE):
            command = component["cmd"]["linux"]
            if command.startswith("ollama pull"):
                self.assertIn(":", command.split()[-1], component["id"])

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
        for client in ("claude", "codex", "gemini", "copilot"):
            self.assertIn(f"rules-{client}", names, f"{client} has no standalone setup")

    def test_all_clients_at_once_is_offered_first(self):
        order = [c["id"] for c in sorted(components_in(self.LANE), key=lambda c: c["order"])]
        self.assertEqual(order[0], "rules-all-clients")

    def test_the_rules_commands_enable_auto_mode(self):
        """Charles asked for auto mode always on, so the recipe must pass the flag."""
        for client in ("all-clients", "claude", "codex", "gemini", "copilot"):
            recipe = RECIPES[f"setup-rules-{client}"]
            self.assertIn("-AutoSkills", recipe["commands"]["windows"], client)
            self.assertIn("--auto-skills", recipe["commands"]["linux"], client)

    def test_the_guards_are_installable(self):
        recipe = RECIPES["setup-rules-guards"]
        for command in recipe["commands"].values():
            self.assertIn("install_auto_mode.py", command)

    def test_a_verify_step_exists(self):
        """A setup you cannot check is a setup you have to believe."""
        recipe = RECIPES["setup-rules-verify"]
        for command in recipe["commands"].values():
            self.assertIn("MASTER-REPO-USE:BEGIN", command)

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
        """Git Bash on Windows has python but no python3."""
        source = (ROOT / "scripts" / "setup-global-ai.sh").read_text(encoding="utf-8")
        self.assertIn("command -v python3 || command -v python", source)

    def test_the_powershell_script_validates_its_client_argument(self):
        source = (ROOT / "scripts" / "setup-global-ai.ps1").read_text(encoding="utf-8")
        self.assertIn("ValidateSet", source)
        for client in ("claude", "codex", "gemini", "copilot", "all", "gpt"):
            self.assertIn(f"'{client}'", source, client)


if __name__ == "__main__":
    unittest.main()

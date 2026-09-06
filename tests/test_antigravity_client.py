"""Google Antigravity is a client surface, and its paths are the easy thing to guess wrong.

Every fact pinned here was read from antigravity.google on 2026-09-04, not recalled.
Two of them are counter-intuitive enough that a future edit will probably reintroduce
the wrong version:

  1. Antigravity's GLOBAL rules file is ``~/.gemini/GEMINI.md`` - the same file the
     Gemini CLI reads. There is no ``~/.antigravity/`` tree at all. A setup script
     that invents one writes a file nothing ever loads, and reports success.
  2. Its skills live under ``~/.gemini/config/skills/``, which the Gemini CLI does
     NOT read. So the two clients overlap on rules and diverge on skills, and
     collapsing them into one option loses the skills.

The install commands are the third pinned fact. The pipe-to-shell one-liners are
real: both URLs were fetched and returned 200 from Google Frontend, and install.sh
was read byte-for-byte. They cover the CLI only. Antigravity 2.0, the IDE and the
SDK are native downloads, apt/dnf repositories and PyPI respectively, and
generalising the one-liner to them would be inventing a command.
"""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "atlas-data.json").read_text(encoding="utf-8"))
SH = (ROOT / "scripts" / "setup-global-ai.sh").read_text(encoding="utf-8")
PS = (ROOT / "scripts" / "setup-global-ai.ps1").read_text(encoding="utf-8")
INSTALLER = (ROOT / "scripts" / "install_auto_mode.py").read_text(encoding="utf-8")
RECIPES = {r["id"]: r for r in DATA["setupRecipes"]}
CLIENTS = {c["id"]: c for c in DATA["profileClients"]}


class TheRulesFileIsSharedWithGemini(unittest.TestCase):
    def test_no_script_invents_an_antigravity_home(self):
        """The single most likely wrong guess, refused in every file that could make it.

        Matched as a path rather than as a word, because the comments in these
        files say the words "~/.antigravity/ tree" in order to explain that it does
        not exist. Banning the string would ban the explanation.
        """
        for name, body in (("setup-global-ai.sh", SH), ("setup-global-ai.ps1", PS),
                           ("install_auto_mode.py", INSTALLER)):
            for path in ('$HOME/.antigravity', '$HOME\\.antigravity',
                         '"~/.antigravity', '".antigravity'):
                self.assertNotIn(path, body,
                                 f"{name} writes to {path}, which does not exist")

    def test_both_scripts_write_the_gemini_file_for_antigravity(self):
        self.assertIn("writes gemini || writes antigravity", SH)
        self.assertIn("(Test-Writes 'gemini') -or (Test-Writes 'antigravity')", PS)

    def test_the_block_is_written_to_that_path_once_not_twice(self):
        """Two upserts on one file would let the second body replace the first."""
        self.assertEqual(SH.count('upsert_block "$HOME/.gemini/GEMINI.md"'), 1)
        self.assertEqual(PS.count('Set-MasterRepoBlock "$HOME\\.gemini\\GEMINI.md"'), 1)

    def test_the_installer_lists_one_entry_for_both_clients(self):
        self.assertIn('"Gemini + Antigravity": ".gemini/GEMINI.md"', INSTALLER)
        self.assertEqual(INSTALLER.count('".gemini/GEMINI.md"'), 1)


class TheSkillsTreeIsAntigravityOnly(unittest.TestCase):
    def test_the_documented_global_skill_path_is_used(self):
        for name, body in (("setup-global-ai.sh", SH), ("setup-global-ai.ps1", PS)):
            self.assertIn("gemini", body.lower())
            self.assertIn("config", body.lower(), name)
        self.assertIn('".gemini/config/skills"', INSTALLER)

    def test_every_repository_skill_carries_what_antigravity_requires(self):
        """description is the only mandatory frontmatter field. Without it, a skill
        folder is copied and then never selected, which fails silently."""
        skills = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
        self.assertGreater(len(skills), 0, "no skills to install")
        for skill in skills:
            definition = skill / "SKILL.md"
            self.assertTrue(definition.exists(), f"{skill.name} has no SKILL.md")
            head = definition.read_text(encoding="utf-8").split("---")[1]
            self.assertIn("description:", head, f"{skill.name} has no description")

    def test_the_installer_installs_all_skills_not_only_the_auto_mode_one(self):
        """A skill that was never copied cannot be auto-selected, which is the rule."""
        self.assertNotIn('source = repo / "skills" / "master-repo-auto"', INSTALLER)
        self.assertIn('source = repo / "skills"', INSTALLER)


class TheClientIsAcceptedEverywhere(unittest.TestCase):
    def test_the_shell_script_accepts_it_and_its_aliases(self):
        self.assertIn("all|claude|codex|gemini|copilot|antigravity", SH)
        self.assertIn("ag|google-antigravity", SH)

    def test_the_powershell_script_accepts_it_and_its_aliases(self):
        self.assertIn("'antigravity'", PS)
        self.assertIn("'ag','google-antigravity'", PS)

    def test_the_error_message_lists_it(self):
        """A client the script accepts but does not advertise gets used by nobody."""
        self.assertIn("Use all|claude|codex|gemini|copilot|antigravity.", SH)

    def test_the_picker_offers_it_and_a_recipe_stands_behind_it(self):
        self.assertIn("antigravity", CLIENTS)
        self.assertIn("setup-rules-antigravity", RECIPES)

    def test_the_recipe_passes_the_right_client_on_every_platform(self):
        recipe = RECIPES["setup-rules-antigravity"]
        for platform, command in recipe["commands"].items():
            self.assertIn("antigravity", command, platform)


class TheHostedModelsAreReferenceNotSetup(unittest.TestCase):
    def setUp(self):
        self.models = [c for c in DATA["components"]
                       if c.get("lane") == "sys-antigravity-models"]

    def test_the_lane_exists_and_holds_the_documented_models(self):
        lane = next(l for l in DATA["lanes"] if l["id"] == "sys-antigravity-models")
        self.assertEqual(lane["count"], len(self.models))
        names = {m["name"] for m in self.models}
        for expected in ("Gemini 3.8 Flash", "Gemini 3.1 Pro",
                         "Claude Sonnet 4.6 (thinking)", "Claude Opus 4.6 (thinking)",
                         "GPT-OSS-120b", "Nano Banana 2"):
            self.assertIn(expected, names)

    def test_none_of_them_offers_an_install_command(self):
        """A hosted model is picked in the client. Any command here is invented."""
        for model in self.models:
            self.assertNotIn("setupRecipe", model, model["name"])
            self.assertNotIn("cmd", model, model["name"])
            self.assertEqual(model["action"]["kind"], "reference", model["name"])
            self.assertEqual(model["setupState"], "hosted", model["name"])

    def test_hosted_is_distinct_from_unavailable(self):
        """"No recipe yet" reads as work outstanding. Here there is none to do."""
        core = (ROOT / "designs" / "atlas-core.js").read_text(encoding="utf-8")
        self.assertIn("setupState === 'hosted'", core)
        self.assertIn("Hosted, sign in rather than install", core)
        for model in self.models:
            self.assertNotEqual(model["setupState"], "unavailable", model["name"])

    def test_the_plan_restricted_models_say_so(self):
        """Charles runs a paid tier; which models a plan change removes is the point."""
        for model in self.models:
            if model["name"].startswith(("Claude ", "GPT-OSS")):
                self.assertIn("Enterprise", model["detail"], model["name"])

    def test_they_are_not_mixed_into_the_local_model_lane(self):
        local = [c for c in DATA["components"] if c.get("lane") == "sys-model-setup"]
        self.assertTrue(all("ollama" in c.get("cmd", {}).get("linux", "") or
                            "ollama" in c.get("detail", "").lower() or
                            c["id"].startswith(("ollama", "model-"))
                            for c in local),
                        "a hosted model leaked into the local setup lane")


class TheCliInstallerIsTheVendorsOwn(unittest.TestCase):
    def test_the_cli_recipe_exists_and_targets_the_vendor_host(self):
        recipe = RECIPES["setup-antigravity-cli"]
        for platform, command in recipe["commands"].items():
            self.assertIn("antigravity.google/cli/install", command, platform)

    def test_the_one_liner_is_not_generalised_to_the_other_products(self):
        """It covers the CLI only. The IDE, 2.0 and the SDK are different paths."""
        source = (ROOT / "scripts" / "build_atlas_data.py").read_text(encoding="utf-8")
        for invented in ("brew install antigravity", "winget install --id Google.Antigravity",
                         "pip install antigravity", "npm install -g antigravity"):
            self.assertNotIn(invented, source, f"{invented} is not a documented command")


if __name__ == "__main__":
    unittest.main()

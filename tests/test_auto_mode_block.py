"""Auto mode is split across three layers, cheapest first, and must stay split.

    hook   scripts/hooks/no_prune_guard.py   0 tokens, runs outside the model
    skill  skills/master-repo-auto/SKILL.md  name and description only until used
    block  docs/auto-mode-block.txt          loaded every session by every client

The block used to hold everything, at about 616 tokens per session per client.
These tests stop the full rules drifting back into it, and stop the two standing
rules drifting out of it into a file nobody reads in time.
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BLOCK = ROOT / "docs" / "auto-mode-block.txt"
SKILL = ROOT / "skills" / "master-repo-auto" / "SKILL.md"
HOOK = ROOT / "scripts" / "hooks" / "no_prune_guard.py"

# The whole point of the split. Generous enough for a rewording, tight enough
# that pasting the rules back in fails loudly.
BLOCK_BUDGET_BYTES = 700


class TheAlwaysLoadedBlock(unittest.TestCase):
    def setUp(self):
        self.text = BLOCK.read_text(encoding="utf-8")

    def test_stays_within_its_token_budget(self):
        self.assertLess(
            len(self.text.encode("utf-8")), BLOCK_BUDGET_BYTES,
            "the always-loaded block is growing back; move detail into the skill")

    def test_points_at_the_skill_rather_than_restating_it(self):
        self.assertIn("master-repo-auto", self.text)

    def test_carries_the_no_pruning_rule(self):
        # Must be known before any lookup, or a tool is gone before the skill loads.
        self.assertIn("Never remove, disable or unload", self.text)

    def test_carries_the_multiple_command_rule(self):
        self.assertIn("Run every slash command", self.text)
        self.assertIn("in the order written", self.text)

    def test_does_not_restate_the_detail_that_lives_in_the_skill(self):
        for moved in ("byte-for-byte", "15 percent", "speculative scanning"):
            self.assertNotIn(moved, self.text,
                             f"'{moved}' belongs in the skill, not in every session")

    def test_no_em_or_en_dashes(self):
        self.assertNotIn("—", self.text)
        self.assertNotIn("–", self.text)


class TheOnDemandSkill(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")

    def test_has_frontmatter_so_it_is_discoverable(self):
        self.assertTrue(self.text.startswith("---"))
        self.assertIn("name: master-repo-auto", self.text)
        self.assertIn("description:", self.text)

    def test_carries_the_token_discipline_rules(self):
        for fragment in ("rtk <command>", "caveman", "Never paste a whole catalog file"):
            self.assertIn(fragment, self.text)

    def test_carries_the_compression_safety_list(self):
        for fragment in ("Code blocks", "URLs", "file paths", "exact error strings"):
            self.assertIn(fragment, self.text)

    def test_carries_the_full_no_pruning_policy(self):
        self.assertIn("Never prune what the user chose to keep", self.text)
        self.assertIn("owner-approved pull request", self.text)

    def test_auto_mode_cannot_widen_permissions(self):
        self.assertIn("never what is permitted", self.text)
        # Kept short so a line wrap in the skill does not fail the test.
        self.assertIn("Nothing third-party is installed", self.text)

    def test_no_em_or_en_dashes(self):
        self.assertNotIn("—", self.text)
        self.assertNotIn("–", self.text)


class TheInstaller(unittest.TestCase):
    def test_hook_exists_and_is_the_zero_token_layer(self):
        self.assertTrue(HOOK.exists())

    def test_installer_wires_all_three_layers(self):
        body = (ROOT / "scripts" / "install_auto_mode.py").read_text(encoding="utf-8")
        for fragment in ("install_skill", "register_hook", "upsert_block"):
            self.assertIn(fragment, body)

    def test_installer_backs_up_settings_before_touching_them(self):
        body = (ROOT / "scripts" / "install_auto_mode.py").read_text(encoding="utf-8")
        self.assertIn(".json.bak", body)

    def test_installer_refuses_to_overwrite_unreadable_settings(self):
        body = (ROOT / "scripts" / "install_auto_mode.py").read_text(encoding="utf-8")
        self.assertIn("refusing to overwrite", body)

    def test_setup_scripts_still_reference_the_block(self):
        for script in ("setup-global-ai.ps1", "setup-global-ai.sh"):
            body = (ROOT / "scripts" / script).read_text(encoding="utf-8")
            self.assertIn("auto-mode-block.txt", body, f"{script} lost its reference")

    def test_setup_scripts_contain_no_control_characters(self):
        # A backslash escape twice collapsed text here into control characters.
        for script in ("setup-global-ai.ps1", "setup-global-ai.sh", "install_auto_mode.py",
                       "hooks/no_prune_guard.py"):
            body = (ROOT / "scripts" / script).read_text(encoding="utf-8")
            stray = {hex(ord(c)) for c in body if ord(c) < 32 and c not in "\n\r\t"}
            self.assertFalse(stray, f"{script} has control characters {stray}")


if __name__ == "__main__":
    unittest.main()

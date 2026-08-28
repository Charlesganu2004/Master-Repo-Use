"""The auto-mode block is the one file four clients read, so its rules must not drift.

setup-global-ai.ps1 and setup-global-ai.sh both splice this file into Claude,
Codex, Gemini and Copilot instruction files. A rule silently dropped here is a
rule silently dropped everywhere at once.
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BLOCK = ROOT / "docs" / "auto-mode-block.txt"


class AutoModeBlock(unittest.TestCase):
    def setUp(self):
        self.text = BLOCK.read_text(encoding="utf-8")

    def test_block_exists_and_is_substantial(self):
        self.assertGreater(len(self.text), 800)

    def test_carries_the_no_pruning_rule(self):
        # Charles asked for this after tools he chose kept disappearing.
        self.assertIn("Never prune what the user chose to keep", self.text)
        self.assertIn("unless Charles explicitly asks for removal", self.text)

    def test_carries_the_multiple_command_rule(self):
        self.assertIn("Run every command in the prompt", self.text)
        self.assertIn("in the order written", self.text)

    def test_carries_the_token_discipline_rules(self):
        for fragment in ("rtk <command>", "caveman-compress", "Never paste a whole catalog file"):
            self.assertIn(fragment, self.text)

    def test_preserves_the_compression_safety_list(self):
        for fragment in ("Code blocks", "URLs", "file paths", "exact error strings"):
            self.assertIn(fragment, self.text)

    def test_auto_mode_cannot_widen_permissions(self):
        # Auto mode changes how work is done, never what is allowed.
        self.assertIn("never what is permitted", self.text)
        self.assertIn("No third-party code is installed or executed", self.text)

    def test_no_em_or_en_dashes(self):
        self.assertNotIn("—", self.text)
        self.assertNotIn("–", self.text)

    def test_both_setup_scripts_reference_the_block(self):
        for script in ("setup-global-ai.ps1", "setup-global-ai.sh"):
            body = (ROOT / "scripts" / script).read_text(encoding="utf-8")
            self.assertIn("auto-mode-block.txt", body, f"{script} lost its reference")

    def test_setup_scripts_contain_no_control_characters(self):
        # A backslash escape once collapsed this path into a BEL character.
        for script in ("setup-global-ai.ps1", "setup-global-ai.sh"):
            body = (ROOT / "scripts" / script).read_text(encoding="utf-8")
            stray = {hex(ord(c)) for c in body if ord(c) < 32 and c not in "\n\r\t"}
            self.assertFalse(stray, f"{script} has control characters {stray}")


if __name__ == "__main__":
    unittest.main()

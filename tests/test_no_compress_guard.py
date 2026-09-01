"""The protected block must survive every compression pass and every session.

Charles asked for the caveman and token-reduction rules to be mandatory and never
compressed. Two halves to that: the block says so, and a hook enforces it outside
the model, because an instruction reading "do not compress me" only holds while
something is reading it, and a compression pass is exactly when nothing is.

False positives matter as much here as in the no-prune guard. Writing about a
compressor, or compressing an unprotected file, must still work.
"""
import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOOK = ROOT / "scripts" / "hooks" / "no_compress_guard.py"
BLOCK = ROOT / "docs" / "auto-mode-block.txt"
BEGIN = "<!-- NO-COMPRESS:BEGIN -->"
END = "<!-- NO-COMPRESS:END -->"


def run(command: str, tool: str = "Bash") -> int:
    event = json.dumps({"tool_name": tool, "tool_input": {"command": command},
                        "cwd": str(ROOT)})
    proc = subprocess.run([sys.executable, str(HOOK)], input=event,
                          capture_output=True, text=True)
    return proc.returncode


class TheProtectedBlock(unittest.TestCase):
    def setUp(self):
        self.text = BLOCK.read_text(encoding="utf-8")

    def test_the_markers_are_present_and_ordered(self):
        self.assertIn(BEGIN, self.text)
        self.assertIn(END, self.text)
        self.assertLess(self.text.index(BEGIN), self.text.index(END))

    def test_it_declares_itself_exempt_from_compression(self):
        body = self.text[self.text.index(BEGIN):self.text.index(END)]
        self.assertIn("exempt from every", body.lower())
        for tool in ("caveman", "token-compact", "LLMLingua", "Headroom"):
            self.assertIn(tool, body, f"{tool} is not named as a pass that must skip it")

    def test_caveman_use_is_mandatory_not_optional(self):
        # Whitespace-normalised: the block is hard-wrapped, and a rule that moved
        # across a line break is still the same rule.
        body = " ".join(self.text[self.text.index(BEGIN):self.text.index(END)].lower().split())
        self.assertIn("mandatory, automatic, every conversation", body)
        self.assertIn("default action, not a suggestion", body)

    def test_token_reducers_are_named(self):
        body = self.text[self.text.index(BEGIN):self.text.index(END)]
        for tool in ("rtk", "rtt"):
            self.assertIn(tool, body)

    def test_every_model_is_addressed_not_just_claude(self):
        body = self.text[self.text.index(BEGIN):self.text.index(END)]
        for model in ("Claude", "Codex", "Gemini", "Copilot", "ChatGPT"):
            self.assertIn(model, body, f"{model} is not covered by the block")

    def test_the_no_prune_rule_lives_inside_the_protected_block(self):
        """It is the rule most likely to be dropped, so it must be protected."""
        body = self.text[self.text.index(BEGIN):self.text.index(END)]
        self.assertIn("Never remove, disable or unload", body)


class TheGuardBlocks(unittest.TestCase):
    def test_running_caveman_on_the_protected_file(self):
        self.assertEqual(run("python -m caveman auto-mode-block.txt"), 2)

    def test_token_compact_on_the_protected_file(self):
        self.assertEqual(run("python compress.py docs/auto-mode-block.txt"), 2)

    def test_truncating_the_protected_file(self):
        self.assertEqual(run("truncate -s 100 docs/auto-mode-block.txt"), 2)

    def test_overwriting_the_protected_file_wholesale(self):
        self.assertEqual(run("echo short > docs/auto-mode-block.txt"), 2)

    def test_llmlingua_on_the_protected_file(self):
        self.assertEqual(run("llmlingua --input docs/auto-mode-block.txt"), 2)


class TheGuardAllows(unittest.TestCase):
    def test_compressing_a_file_with_no_protected_block(self):
        self.assertEqual(run("python -m caveman README.md"), 0)

    def test_reading_the_protected_file(self):
        self.assertEqual(run("cat docs/auto-mode-block.txt"), 0)

    def test_grepping_the_protected_file(self):
        self.assertEqual(run("grep -n MANDATORY docs/auto-mode-block.txt"), 0)

    def test_writing_a_document_that_mentions_a_compressor(self):
        self.assertEqual(
            run("cat > notes.md <<'EOF'\nrun caveman on docs/auto-mode-block.txt\nEOF"), 0)

    def test_ordinary_commands(self):
        self.assertEqual(run("git status --short"), 0)
        self.assertEqual(run("rtk git status"), 0)

    def test_non_bash_tools_are_ignored(self):
        self.assertEqual(run("truncate -s 0 docs/auto-mode-block.txt", tool="Read"), 0)

    def test_explicit_override_is_honoured(self):
        self.assertEqual(
            run("truncate -s 100 docs/auto-mode-block.txt  # APPROVED RECOMPRESS"), 0)

    def test_a_malformed_event_never_breaks_the_session(self):
        proc = subprocess.run([sys.executable, str(HOOK)], input="not json",
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)


class TheInstallerWiresIt(unittest.TestCase):
    def test_the_installer_registers_both_guards(self):
        body = (ROOT / "scripts" / "install_auto_mode.py").read_text(encoding="utf-8")
        for guard in ("no_prune_guard", "no_compress_guard"):
            self.assertIn(guard, body, f"{guard} is not installed")


if __name__ == "__main__":
    unittest.main()

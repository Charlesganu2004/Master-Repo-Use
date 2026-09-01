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
        self.assertIn("Never remove, disable", body)


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


class CapabilityDefinitionsAreProtected(unittest.TestCase):
    """Skills, MCP servers, tools and agents are never compressed.

    These are protected by path rather than by a marker, because nobody thinks to
    annotate a SKILL.md, and because the failure is silent: compress the
    description a client matches against and the capability simply stops being
    selected. Nothing errors, so nothing gets noticed.
    """

    def test_a_skill_definition_cannot_be_compressed(self):
        self.assertEqual(run("python -m caveman ~/.claude/skills/master-repo-auto/SKILL.md"), 2)

    def test_a_skill_definition_cannot_be_truncated(self):
        self.assertEqual(run("truncate -s 200 skills/master-repo-auto/SKILL.md"), 2)

    def test_mcp_config_cannot_be_compressed(self):
        self.assertEqual(run("python compress.py .mcp.json"), 2)

    def test_client_settings_cannot_be_compressed(self):
        self.assertEqual(run("llmlingua --input ~/.claude/settings.json"), 2)

    def test_agent_definitions_cannot_be_compressed(self):
        self.assertEqual(run("python -m caveman .claude/agents/reviewer.md"), 2)

    def test_client_contracts_cannot_be_compressed(self):
        for target in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", "copilot-instructions.md"):
            self.assertEqual(run(f"python -m caveman {target}"), 2, target)

    def test_the_skills_directory_is_covered_wholesale(self):
        self.assertEqual(run("python -m caveman .claude/skills/"), 2)

    def test_ordinary_prose_is_still_compressible(self):
        """The point of the reducers is that they still work on what they should."""
        for target in ("README.md", "docs/REPO-CATALOG.md", "notes/journal.md"):
            self.assertEqual(run(f"python -m caveman {target}"), 0, target)

    def test_reading_a_capability_definition_is_allowed(self):
        self.assertEqual(run("cat .claude/skills/master-repo-auto/SKILL.md"), 0)
        self.assertEqual(run("grep -n description .mcp.json"), 0)

    def test_writing_about_a_capability_is_not_compressing_one(self):
        heredoc = "cat > notes.md <<'EOF'\nrun caveman on SKILL.md sometime\nEOF"
        self.assertEqual(run(heredoc), 0)

    def test_the_override_still_works(self):
        self.assertEqual(
            run("truncate -s 200 skills/x/SKILL.md  # APPROVED RECOMPRESS"), 0)


class TheAutoSelectionRule(unittest.TestCase):
    def test_best_fit_selection_is_mandatory_and_protected(self):
        text = BLOCK.read_text(encoding="utf-8")
        body = " ".join(text[text.index(BEGIN):text.index(END)].lower().split())
        self.assertIn("best-fit skill, tool, mcp or agent", body)
        self.assertIn("automatically", body)

    def test_capability_definitions_are_named_as_uncompressible(self):
        text = BLOCK.read_text(encoding="utf-8")
        body = " ".join(text[text.index(BEGIN):text.index(END)].lower().split())
        self.assertIn("their definitions are exempt from compression", body)


class RedirectsOnlyGuardTheirTarget(unittest.TestCase):
    """A '>' only truncates what it points at.

    The first version matched any redirect in a command that also mentioned a
    protected filename, so the audit tool was blocked from writing its own row:
    the filename was an argument and the redirect went to /dev/null. A guard that
    stops the logging is worse than no guard.
    """

    def test_redirecting_onto_a_protected_file_is_blocked(self):
        self.assertEqual(run("echo x > docs/SECURITY-TRAIL.md"), 2)
        self.assertEqual(run("echo x > docs/auto-mode-block.txt"), 2)

    def test_redirecting_onto_a_capability_is_blocked(self):
        self.assertEqual(run("echo x > skills/a/SKILL.md"), 2)

    def test_a_protected_name_as_an_argument_is_not_a_write(self):
        self.assertEqual(
            run('python scripts/security_trail.py --scope "docs/SECURITY-TRAIL.md" >/dev/null'), 0)

    def test_copying_a_protected_file_out_is_allowed(self):
        self.assertEqual(run("cat docs/SECURITY-TRAIL.md > /tmp/backup.md"), 0)

    def test_grep_output_elsewhere_is_allowed(self):
        self.assertEqual(run("grep SKILL.md notes.txt > results.txt"), 0)

    def test_staging_a_protected_file_is_allowed(self):
        self.assertEqual(run("git add docs/SECURITY-TRAIL.md"), 0)

    def test_compressor_verbs_still_scan_the_whole_command(self):
        """Compressors take the file as an argument, so argument position counts."""
        self.assertEqual(run("python -m caveman docs/auto-mode-block.txt"), 2)
        self.assertEqual(run("truncate -s 10 docs/SECURITY-TRAIL.md"), 2)


if __name__ == "__main__":
    unittest.main()

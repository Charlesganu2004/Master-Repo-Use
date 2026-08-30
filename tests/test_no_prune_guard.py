"""The no-prune guard must stop real deletions and stay invisible otherwise.

False positives are the real risk: a guard that interrupts ordinary work gets
turned off, and then it protects nothing. Most cases below are things that must
still be allowed.
"""
import json
import pathlib
import subprocess
import sys
import unittest

HOOK = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "hooks" / "no_prune_guard.py"

HEREDOC_NOTE = "cat > note.md <<'EOF'\nrm -rf ~/.claude/skills\nEOF"
HEREDOC_UNQUOTED = "cat > n.md <<EOF\nrm -rf ~/.claude/skills\nEOF"
HEREDOC_THEN_DELETE = "cat > n.md <<'EOF'\nhello\nEOF\nrm -rf ~/.claude/skills"
HEREDOC_LANE = "cat > repo-lists/new-lane.txt <<'EOF'\nfoo/bar\nEOF"
JSON_FIXTURE = "echo '{\"command\":\"rm -rf ~/.claude/skills\"}' | python3 h.py"


def run(command: str, tool: str = "Bash") -> int:
    event = json.dumps({"tool_name": tool, "tool_input": {"command": command}})
    proc = subprocess.run([sys.executable, str(HOOK)], input=event,
                          capture_output=True, text=True)
    return proc.returncode


class Blocks(unittest.TestCase):
    def test_deleting_a_skill_directory(self):
        self.assertEqual(run("rm -rf ~/.claude/skills/caveman-ultra-compact"), 2)

    def test_deleting_settings(self):
        self.assertEqual(run("rm ~/.claude/settings.json"), 2)

    def test_deleting_a_catalog_lane(self):
        self.assertEqual(run("rm repo-lists/context-token-management.txt"), 2)

    def test_git_rm_on_skills(self):
        self.assertEqual(run("git rm -r skills/master-repo-auto"), 2)

    def test_powershell_remove_item(self):
        self.assertEqual(run("Remove-Item -Recurse .claude/plugins"), 2)

    def test_mcp_removal_command(self):
        self.assertEqual(run("claude mcp remove github .mcp.json"), 2)

    def test_windows_backslash_paths_are_caught(self):
        self.assertEqual(run(r"rm -rf C:\Users\Charl\.claude\skills\foo"), 2)

    def test_deleting_an_agent_contract(self):
        self.assertEqual(run("rm AGENTS.md"), 2)

    def test_chained_deletion(self):
        self.assertEqual(run("rm -rf ~/.claude/skills && echo done"), 2)

    def test_double_quoted_target(self):
        # Double quotes are kept, because real targets are written this way.
        self.assertEqual(run('rm -rf "$HOME/.claude/skills"'), 2)


class Allows(unittest.TestCase):
    def test_ordinary_build_cleanup(self):
        self.assertEqual(run("rm -rf node_modules dist build"), 0)

    def test_removing_a_scratch_file(self):
        self.assertEqual(run("rm /tmp/scratch.txt"), 0)

    def test_reading_a_protected_path(self):
        self.assertEqual(run("cat repo-lists/all-curated.txt"), 0)

    def test_grepping_a_protected_path(self):
        self.assertEqual(run("grep -rn foo .claude/skills"), 0)

    def test_writing_a_new_skill_directory(self):
        self.assertEqual(run("mkdir -p skills/new-thing"), 0)

    def test_word_containing_rm_is_not_a_delete(self):
        self.assertEqual(run("npx prettier --write skills/master-repo-auto/SKILL.md"), 0)
        self.assertEqual(run("echo confirm repo-lists/all-curated.txt"), 0)

    def test_non_bash_tools_are_ignored(self):
        self.assertEqual(run("rm -rf .claude/skills", tool="Read"), 0)

    def test_explicit_override_is_honoured(self):
        self.assertEqual(run("rm -rf .claude/skills/old  # APPROVED PRUNE"), 0)

    def test_malformed_event_never_breaks_the_session(self):
        proc = subprocess.run([sys.executable, str(HOOK)], input="not json",
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)

    def test_git_status_is_untouched(self):
        self.assertEqual(run("git status --short"), 0)


class DataIsNotAnInstruction(unittest.TestCase):
    """The guard blocked its own bug fix once. These keep that fixed.

    Writing, echoing or grepping text that mentions a deletion is not a deletion.
    """

    def test_heredoc_body_mentioning_a_deletion(self):
        self.assertEqual(run(HEREDOC_NOTE), 0)

    def test_unquoted_heredoc_tag(self):
        self.assertEqual(run(HEREDOC_UNQUOTED), 0)

    def test_single_quoted_test_fixture(self):
        self.assertEqual(run(JSON_FIXTURE), 0)

    def test_searching_for_the_phrase(self):
        self.assertEqual(run("grep -rn 'rm -rf .claude/skills' docs/"), 0)

    def test_writing_a_catalog_lane(self):
        self.assertEqual(run(HEREDOC_LANE), 0)

    def test_a_real_deletion_after_a_heredoc_still_blocks(self):
        # Stripping the body must not swallow a genuine command that follows.
        self.assertEqual(run(HEREDOC_THEN_DELETE), 2)


if __name__ == "__main__":
    unittest.main()

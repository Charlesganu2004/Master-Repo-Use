"""Regression tests for non-destructive global skill refreshes."""
import importlib.util
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install_auto_mode.py"


def load_installer():
    spec = importlib.util.spec_from_file_location("install_auto_mode_test", INSTALLER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {INSTALLER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NonDestructiveSkillRefresh(unittest.TestCase):
    def test_extra_destination_file_survives_refresh(self):
        installer = load_installer()
        with tempfile.TemporaryDirectory() as scratch:
            root = pathlib.Path(scratch)
            repo = root / "repo"
            home = root / "home"
            source = repo / "skills" / "example"
            destination = home / ".claude" / "skills" / "example"
            source.mkdir(parents=True)
            destination.mkdir(parents=True)

            (source / "SKILL.md").write_text("new managed skill\n", encoding="utf-8")
            (source / "managed.txt").write_text("refreshed\n", encoding="utf-8")
            owner_file = destination / "owner-note.txt"
            owner_file.write_text("keep me\n", encoding="utf-8")

            result = installer.install_skill(repo, home, dry=False)

            self.assertEqual(owner_file.read_text(encoding="utf-8"), "keep me\n")
            self.assertEqual((destination / "SKILL.md").read_text(encoding="utf-8"),
                             "new managed skill\n")
            self.assertEqual((destination / "managed.txt").read_text(encoding="utf-8"),
                             "refreshed\n")
            self.assertIn("without deleting existing files", result)

    def test_installers_do_not_remove_a_skill_destination_before_refresh(self):
        scripts = [
            INSTALLER,
            ROOT / "scripts" / "setup-global-ai.ps1",
            ROOT / "scripts" / "setup-global-ai.sh",
        ]
        forbidden = [
            r"shutil\.rmtree\(\s*destination\s*\)",
            r"Remove-Item[^\r\n]*\$destination[^\r\n]*-Recurse",
            r"Remove-Item[^\r\n]*-Recurse[^\r\n]*\$destination",
            r"rm\s+-rf\s+['\"]?\$\{?destination\}?",
        ]
        for script in scripts:
            body = script.read_text(encoding="utf-8")
            for pattern in forbidden:
                self.assertIsNone(
                    re.search(pattern, body, flags=re.IGNORECASE),
                    f"{script.name} still deletes a skill destination with {pattern!r}",
                )


class CursorAndCopilotInstall(unittest.TestCase):
    """The native client files must be installed, not merely documented."""

    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory()
        cls.home = pathlib.Path(cls.scratch.name) / "home"
        cls.proc = subprocess.run(
            [sys.executable, str(INSTALLER), "--repo", str(ROOT),
             "--home", str(cls.home)],
            capture_output=True,
            text=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def test_installer_succeeds(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr or self.proc.stdout)

    def test_cursor_and_copilot_skill_roots_are_declared_and_populated(self):
        installer = load_installer()
        roots = set(installer.SKILL_ROOTS.values())
        for expected in (".agents/skills", ".codex/skills", ".gemini/skills",
                         ".cursor/skills", ".copilot/skills"):
            self.assertIn(expected, roots)
        for relative in (".agents/skills", ".codex/skills", ".gemini/skills",
                         ".cursor/skills", ".copilot/skills"):
            skill = (self.home / pathlib.PurePosixPath(relative)
                     / "master-repo-auto" / "SKILL.md")
            self.assertTrue(skill.is_file(), f"installer did not populate {relative}")

    def test_cursor_rule_is_mdc_and_always_applies(self):
        rule = self.home / ".cursor" / "rules" / "master-repo-auto.mdc"
        self.assertTrue(rule.is_file(), "Cursor's global MDC rule was not written")
        text = rule.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"), "Cursor rule has no YAML frontmatter")
        frontmatter = text.split("---", 2)[1]
        self.assertRegex(frontmatter, r"(?m)^alwaysApply:\s*true\s*$")
        self.assertRegex(frontmatter, r"(?m)^description:\s*\S")
        self.assertIn("MASTER-REPO-USE:BEGIN", text)

    def test_cursor_global_hooks_inject_and_guard(self):
        path = self.home / ".cursor" / "hooks.json"
        self.assertTrue(path.is_file(), "Cursor's user-level hooks.json was not written")
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload.get("version"), 1)
        hooks = payload.get("hooks", {})
        prompt_hooks = hooks.get("sessionStart", [])
        prompt_commands = "\n".join(str(h.get("command", "")) for h in prompt_hooks)
        self.assertIn("skill_pipeline.py", prompt_commands)
        self.assertIn("--cursor", prompt_commands)

        tool_hooks = hooks.get("preToolUse", [])
        guard_commands = "\n".join(str(h.get("command", "")) for h in tool_hooks)
        for guard in ("no_prune_guard.py", "no_compress_guard.py"):
            self.assertIn(guard, guard_commands)
        self.assertTrue(tool_hooks, "Cursor has no preToolUse guards")
        for hook in tool_hooks:
            self.assertEqual(hook.get("matcher"), "Shell")

    def test_copilot_global_instructions_and_personal_hooks_are_written(self):
        instructions = self.home / ".copilot" / "copilot-instructions.md"
        self.assertTrue(instructions.is_file())
        self.assertIn("MASTER-REPO-USE:BEGIN",
                      instructions.read_text(encoding="utf-8"))

        path = self.home / ".copilot" / "hooks" / "master-repo-auto.json"
        self.assertTrue(path.is_file(), "Copilot's personal hook file was not written")
        self.assert_copilot_hook_schema(json.loads(path.read_text(encoding="utf-8")))

    def assert_copilot_hook_schema(self, payload):
        self.assertEqual(payload.get("version"), 1)
        hooks = payload.get("hooks", {})
        session_hooks = hooks.get("sessionStart", [])
        session_commands = self._copilot_commands(session_hooks)
        self.assertIn("skill_pipeline.py", session_commands)
        self.assertIn("--copilot-session", session_commands)

        transform_hooks = hooks.get("userPromptTransformed", [])
        transform_commands = self._copilot_commands(transform_hooks)
        self.assertIn("skill_pipeline.py", transform_commands)
        self.assertIn("--copilot-transform", transform_commands)

        # This block used to assert "PreToolUse" and to accept an exec/args pair,
        # and both were wrong, so the test blessed a config Copilot silently
        # ignores. Copilot's event names are lower camelCase and its entry takes
        # `bash` and `powershell` script strings. Read from GitHub's hooks
        # reference and the CLI hooks how-to on 2026-09-08:
        #   sessionStart, sessionEnd, userPromptSubmitted, userPromptTransformed,
        #   preToolUse, postToolUse, errorOccurred, agentStop
        self.assertNotIn("PreToolUse", hooks,
                         "capitalised event name; Copilot fires nothing for it")
        tool_hooks = hooks.get("preToolUse", [])
        tool_commands = self._copilot_commands(tool_hooks)
        for guard in ("no_prune_guard.py", "no_compress_guard.py"):
            self.assertIn(guard, tool_commands)
        self.assertTrue(tool_hooks, "Copilot has no preToolUse guards")
        for hook in session_hooks + transform_hooks + tool_hooks:
            self.assertEqual(hook.get("type"), "command")
            self.assertTrue(str(hook.get("bash", "")).strip(),
                            f"no bash script, which is the documented key: {hook}")
            self.assertTrue(str(hook.get("powershell", "")).strip(),
                            f"no powershell script, so Windows runs nothing: {hook}")
            self.assertNotIn("exec", hook,
                             "exec/args is not part of Copilot's hook entry shape")

    @staticmethod
    def _copilot_commands(hooks):
        return "\n".join(
            " ".join(str(value) for value in (
                hook.get("command", ""), hook.get("exec", ""),
                *hook.get("args", []), hook.get("bash", ""),
                hook.get("powershell", ""),
            ))
            for hook in hooks
        )

    def test_repository_copilot_hook_exists_and_has_the_same_schema(self):
        path = ROOT / ".github" / "hooks" / "master-repo-auto.json"
        self.assertTrue(path.is_file(), "repository Copilot hook is missing")
        self.assert_copilot_hook_schema(json.loads(path.read_text(encoding="utf-8")))

    def test_codex_global_hooks_use_the_claude_compatible_schema(self):
        path = self.home / ".codex" / "hooks.json"
        self.assertTrue(path.is_file(), "Codex's user-level hooks.json was not written")
        payload = json.loads(path.read_text(encoding="utf-8"))
        hooks = payload.get("hooks", {})

        prompt_entries = hooks.get("UserPromptSubmit", [])
        prompt_hooks = [hook for entry in prompt_entries
                        for hook in entry.get("hooks", [])]
        pipeline_hooks = [hook for hook in prompt_hooks
                          if "skill_pipeline.py" in str(hook.get("command", ""))]
        self.assertEqual(len(pipeline_hooks), 1)
        self.assertEqual(pipeline_hooks[0].get("additionalContextLimit"), 0)
        for entry in prompt_entries:
            self.assertNotIn("matcher", entry)

        tool_entries = hooks.get("PreToolUse", [])
        guard_commands = "\n".join(
            str(hook.get("command", ""))
            for entry in tool_entries for hook in entry.get("hooks", [])
        )
        for guard in ("no_prune_guard.py", "no_compress_guard.py"):
            self.assertIn(guard, guard_commands)
        self.assertTrue(tool_entries, "Codex has no PreToolUse guards")
        for entry in tool_entries:
            self.assertEqual(entry.get("matcher"), "Bash")

    def test_gemini_global_hooks_use_before_agent_and_before_tool(self):
        path = self.home / ".gemini" / "settings.json"
        self.assertTrue(path.is_file(), "Gemini's user settings were not written")
        payload = json.loads(path.read_text(encoding="utf-8"))
        hooks = payload.get("hooks", {})

        agent_entries = hooks.get("BeforeAgent", [])
        agent_hooks = [hook for entry in agent_entries
                       for hook in entry.get("hooks", [])]
        agent_commands = "\n".join(str(hook.get("command", ""))
                                   for hook in agent_hooks)
        self.assertIn("skill_pipeline.py", agent_commands)
        self.assertIn("--gemini", agent_commands)

        tool_entries = hooks.get("BeforeTool", [])
        tool_commands = "\n".join(
            str(hook.get("command", ""))
            for entry in tool_entries for hook in entry.get("hooks", [])
        )
        for guard in ("no_prune_guard.py", "no_compress_guard.py"):
            self.assertIn(guard, tool_commands)
        self.assertTrue(tool_entries, "Gemini has no BeforeTool guards")
        for entry in tool_entries:
            self.assertEqual(entry.get("matcher"), "run_shell_command")


if __name__ == "__main__":
    unittest.main()

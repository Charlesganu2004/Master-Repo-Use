"""Executable installer checks for rollback, conflicts and Windows hooks."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tests.test_install_auto_mode import load_installer
from tests.test_verify_auto_mode import load_verifier


class InstallPreservation(unittest.TestCase):
    def setUp(self):
        self.installer = load_installer()
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)

    def test_hook_backups_never_replace_previous_bytes(self):
        path = self.root / "hooks.json"
        first = '{"hooks": {}}\n'
        second = '{"hooks": {}, "user": true}\n'
        path.write_text(first)
        self.installer._load_hook_file(path, False)
        path.write_text(second)
        self.installer._load_hook_file(path, False)
        contents = [item.read_text() for item in self.root.glob("hooks.json.bak*")]
        self.assertCountEqual(contents, [first, second])

    def test_managed_refresh_preserves_user_content_and_backups(self):
        path = self.root / "instructions.md"
        path.write_text("user instructions\n")
        self.installer.upsert_block(path, "first", False)
        previous = path.read_bytes()
        self.installer.upsert_block(path, "second", False)
        self.assertIn("user instructions", path.read_text())
        self.assertIn(previous, [p.read_bytes() for p in self.root.glob("instructions.md.bak*")])

    def test_ambiguous_markers_are_refused(self):
        path = self.root / "instructions.md"
        text = self.installer.BEGIN + "\nuser content"
        path.write_text(text)
        result = self.installer.upsert_block(path, "new", False)
        self.assertTrue(result.startswith("REFUSED"))
        self.assertEqual(path.read_text(), text)

    def test_unmanaged_same_name_skill_is_not_overwritten(self):
        repo, home = self.root / "repo", self.root / "home"
        source = repo / "skills" / "example" / "SKILL.md"
        output = home / ".copilot" / "skills" / "example" / "SKILL.md"
        source.parent.mkdir(parents=True)
        output.parent.mkdir(parents=True)
        source.write_text("upstream")
        output.write_text("personal customization")
        result = self.installer.install_skill(repo, home, False, ".copilot/skills")
        self.assertTrue(result.startswith("REFUSED"), result)
        self.assertEqual(output.read_text(), "personal customization")

    def test_legacy_acceptance_requires_approval_both_hashes_and_only_newlines(self):
        source = self.root / "source" / "SKILL.md"
        output = self.root / "installed" / "SKILL.md"
        source.parent.mkdir()
        output.parent.mkdir()
        source.write_bytes(b"first\nsecond\n")
        output.write_bytes(b"first\r\nsecond\r\n")
        record = {"approved": True, "kind": "legacy-line-endings",
                  "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                  "installed_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
        match = self.installer.accepted_legacy_representation
        self.assertTrue(match(source, output, record))
        self.assertFalse(match(source, output, None))
        self.assertFalse(match(source, output, {**record, "approved": False}))
        source.write_bytes(b"new revision\n")
        self.assertFalse(match(source, output, record))
        source.write_bytes(b"first\nsecond\n")
        output.write_bytes(b"first \r\nsecond\r\n")
        self.assertFalse(match(source, output, record))
        forged = {**record, "installed_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
        self.assertFalse(match(source, output, forged))

    def test_known_managed_skill_updates_but_later_user_edit_is_preserved(self):
        repo, home = self.root / "repo", self.root / "home"
        source = repo / "skills" / "example" / "SKILL.md"
        source.parent.mkdir(parents=True)
        source.write_text("first")
        self.installer.install_skill(repo, home, False, ".copilot/skills")
        source.write_text("second")
        self.installer.install_skill(repo, home, False, ".copilot/skills")
        output = home / ".copilot" / "skills" / "example" / "SKILL.md"
        self.assertEqual(output.read_text(), "second")
        backups = home / ".master-repo-auto" / "backups"
        self.assertIn(b"first", [p.read_bytes() for p in backups.iterdir()])
        output.write_text("user edit")
        source.write_text("third")
        self.installer.install_skill(repo, home, False, ".copilot/skills")
        self.assertEqual(output.read_text(), "user edit")

    def test_verifier_reports_approved_legacy_representation_not_byte_equality(self):
        verifier_module = load_verifier()
        canonical = self.root / "skills"
        source = canonical / "example" / "SKILL.md"
        home = self.root / "home"
        destination = home / ".copilot" / "skills"
        output = destination / "example" / "SKILL.md"
        source.parent.mkdir(parents=True)
        output.parent.mkdir(parents=True)
        source.write_bytes(b"body\n")
        output.write_bytes(b"body\r\n")
        record = {"approved": True, "kind": "legacy-line-endings",
                  "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                  "installed_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
        state = home / ".master-repo-auto"
        state.mkdir()
        manifest = state / ("skills-" + hashlib.sha256(b".copilot/skills").hexdigest() + ".json")

        def check(entry):
            manifest.write_text(json.dumps({"example/SKILL.md": entry}))
            verifier = verifier_module.Verifier(self.root, home, ("copilot",))
            verifier.skills = (source.parent,)
            with mock.patch.object(verifier_module.harness_paths, "skills_dir", return_value=canonical):
                verifier._check_skill_tree(destination, "copilot", "skills")
            return verifier.results[-1]

        result = check(record)
        self.assertEqual(result.status, "WARN")
        self.assertIn("accepted legacy line-ending representation", result.detail)
        for entry in (None, {**record, "approved": False},
                      {**record, "source_sha256": "new canonical hash"}):
            self.assertEqual(check(entry).status, "FAIL")
        output.write_bytes(b"user changed body\r\n")
        self.assertEqual(check(record).status, "FAIL")

    @unittest.skipUnless(os.name == "nt", "Windows PowerShell hook execution")
    def test_copilot_hook_executes_verified_python_without_store_alias(self):
        self.installer.register_copilot_hooks(Path.cwd(), self.root, False)
        config = json.loads((self.root / ".copilot/hooks/master-repo-auto.json").read_text())
        command = config["hooks"]["userPromptTransformed"][0]["powershell"]
        self.assertIn(sys.executable, command)
        event = json.dumps({"sessionId": "test", "transformedPrompt": "hello", "prompt": "hello"})
        script = "$input | " + command
        result = subprocess.run(["powershell", "-NoProfile", "-Command", script],
                                input=event, text=True, capture_output=True,
                                env={**os.environ, "MASTER_REPO_GOAL_DIR": str(self.root / "state")})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("MASTER REPO AUTO MODE APPLIED", json.loads(result.stdout)["modifiedTransformedPrompt"])


if __name__ == "__main__":
    unittest.main()

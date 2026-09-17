"""An out-of-date installed skill can be updated; an edited one must not be.

The installer refuses to overwrite any installed skill it did not write, because it
cannot tell those two cases apart, so seven clients sat on a copy eighteen lines
behind the repository. Matching the installed bytes against this repository's own
history separates them: a copy that equals some committed version came from here and
is merely old.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "refresh_installed_skills.py"


class RefreshInstalledSkills(unittest.TestCase):
    def setUp(self):
        self.work = pathlib.Path(tempfile.mkdtemp())
        self.repo = self.work / "repo"
        (self.repo / "skills" / "demo-skill").mkdir(parents=True)
        (self.repo / "scripts").mkdir()
        shutil.copy(SCRIPT, self.repo / "scripts" / SCRIPT.name)
        self.skill = self.repo / "skills" / "demo-skill" / "SKILL.md"
        self.git("init", "--quiet", "--initial-branch=main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.com")
        self.old = "# Demo\n\nThe first version.\n"
        self.write(self.old, "first")
        self.new = "# Demo\n\nThe second version, longer than the first.\n"
        self.write(self.new, "second")
        self.home = self.work / "home"

    def tearDown(self):
        shutil.rmtree(self.work, ignore_errors=True)

    def git(self, *args):
        return subprocess.run(("git",) + args, cwd=self.repo, check=True, capture_output=True, text=True).stdout

    def write(self, text: str, message: str):
        self.skill.write_text(text, encoding="utf-8", newline="\n")
        self.git("add", "-A")
        self.git("commit", "--quiet", "-m", message)

    def install(self, client: str, text: str) -> pathlib.Path:
        path = self.home / client / "demo-skill" / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        return path

    def run_script(self, *argv):
        return subprocess.run([sys.executable, str(self.repo / "scripts" / SCRIPT.name),
                               "--home", str(self.home), *argv],
                              capture_output=True, text=True, check=True)

    def test_a_stale_copy_is_reported_and_then_updated(self):
        installed = self.install(".claude/skills", self.old)
        report = self.run_script()
        self.assertIn("stale", report.stdout)
        self.assertEqual(self.old, installed.read_text(encoding="utf-8"), "a report must not write")

        self.run_script("--apply")
        self.assertEqual(self.new, installed.read_text(encoding="utf-8"))
        self.assertEqual([], list(installed.parent.glob("SKILL.md.pre-*")),
                         "a backup inside a skill directory is a file the clients would read")
        kept = list((self.home / ".master-repo-skill-backups").rglob("SKILL.md"))
        self.assertEqual(1, len(kept), "the replaced copy must be kept somewhere")
        self.assertEqual(self.old, kept[0].read_text(encoding="utf-8"))

    def test_a_locally_edited_copy_is_left_alone(self):
        edited = "# Demo\n\nCharles changed this line by hand.\n"
        installed = self.install(".codex/skills", edited)
        report = self.run_script("--apply")
        self.assertIn("EDITED", report.stdout)
        self.assertEqual(edited, installed.read_text(encoding="utf-8"),
                         "an edited skill must never be overwritten")

    def test_a_current_copy_is_not_touched(self):
        installed = self.install(".cursor/skills", self.new)
        before = installed.stat().st_mtime_ns
        report = self.run_script("--apply")
        self.assertNotIn("demo-skill", report.stdout.split("\n\n")[0])
        self.assertEqual(before, installed.stat().st_mtime_ns)

    def test_every_client_directory_is_covered(self):
        text = SCRIPT.read_text(encoding="utf-8")
        for client in (".claude/skills", ".agents/skills", ".codex/skills", ".cursor/skills",
                       ".copilot/skills", ".gemini/skills", ".gemini/config/skills"):
            with self.subTest(client=client):
                self.assertIn(client, text)


if __name__ == "__main__":
    unittest.main()

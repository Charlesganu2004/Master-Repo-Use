"""Intake scans are for repositories new to the catalog, not for lines new to a file.

Registering a lane's repositories in all-curated.txt adds lines for repositories
the catalog already lists. The audit job read every added line as a new
repository and forced a deep scan of each inside a 20-minute job, so registering
82 at once would have timed the audit out.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "new_catalog_repos.py"
WORKFLOW = (ROOT / ".github" / "workflows" / "catalog-guardian.yml").read_text(encoding="utf-8")


class NewCatalogRepos(unittest.TestCase):
    def setUp(self):
        self.repo = pathlib.Path(tempfile.mkdtemp())
        self.git("init", "--quiet", "--initial-branch=main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.com")
        (self.repo / "repo-lists").mkdir()

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def git(self, *args):
        return subprocess.run(("git",) + args, cwd=self.repo, check=True,
                              capture_output=True, text=True).stdout.strip()

    def commit(self, files: dict[str, str]) -> str:
        for name, text in files.items():
            (self.repo / "repo-lists" / name).write_text(text, encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "--quiet", "-m", "change")
        return self.git("rev-parse", "HEAD")

    def run_script(self, base: str, limit: int = 15):
        return subprocess.run([sys.executable, str(SCRIPT), "--base", base, "--limit", str(limit)],
                              cwd=self.repo, capture_output=True, text=True)

    def test_registering_already_listed_repositories_is_not_intake(self):
        base = self.commit({"all-curated.txt": "a/one\n", "lane.txt": "b/two  # a lane entry\nc/three\n"})
        self.commit({"all-curated.txt": "a/one\n# registered lane repos\nb/two\nC/Three\n"})
        done = self.run_script(base)
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertEqual("", done.stdout.strip())

    def test_a_repository_new_to_every_list_is_intake(self):
        base = self.commit({"all-curated.txt": "a/one\n", "lane.txt": "a/one\n"})
        self.commit({"all-curated.txt": "a/one\nd/four\n", "lane.txt": "a/one\nd/four  # new\n"})
        self.assertEqual(["d/four"], self.run_script(base).stdout.split())

    def test_comments_and_removed_lines_are_not_intake(self):
        base = self.commit({"all-curated.txt": "a/one\nx/gone\n"})
        self.commit({"all-curated.txt": "a/one\n# e/five was considered and rejected\n"})
        self.assertEqual("", self.run_script(base).stdout.strip())

    def test_a_bulk_addition_is_capped_and_the_rest_named(self):
        base = self.commit({"all-curated.txt": "a/one\n"})
        self.commit({"all-curated.txt": "a/one\n" + "".join(f"new/repo{i}\n" for i in range(20))})
        done = self.run_script(base, limit=5)
        self.assertEqual(5, len(done.stdout.split()))
        self.assertIn("15 further new repositories left to the weekly rotation", done.stderr)

    def test_the_audit_job_uses_it(self):
        self.assertIn("scripts/new_catalog_repos.py", WORKFLOW)
        self.assertNotIn("git diff \"$base\" HEAD -- 'repo-lists/*.txt'", WORKFLOW)


if __name__ == "__main__":
    unittest.main()

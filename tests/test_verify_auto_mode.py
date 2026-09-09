"""Fixture tests for the read-only auto-mode installation verifier."""
from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install_auto_mode.py"
VERIFIER = ROOT / "scripts" / "verify_auto_mode.py"


def load_verifier():
    spec = importlib.util.spec_from_file_location("verify_auto_mode_test", VERIFIER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {VERIFIER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def verify(home: pathlib.Path, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VERIFIER), "--repo", str(ROOT),
         "--home", str(home), *arguments],
        capture_output=True,
        text=True,
    )


def snapshot(root: pathlib.Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


class InstalledFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory()
        cls.home = pathlib.Path(cls.scratch.name) / "home"
        cls.install = subprocess.run(
            [sys.executable, str(INSTALLER), "--repo", str(ROOT),
             "--home", str(cls.home), "--client", "all"],
            capture_output=True,
            text=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def test_fixture_install_succeeds(self):
        self.assertEqual(self.install.returncode, 0,
                         self.install.stderr or self.install.stdout)

    def test_every_client_passes_file_and_schema_verification(self):
        proc = verify(self.home, "--client", "all")
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn("0 failed", proc.stdout)
        self.assertIn("hook trust", proc.stdout)

    def test_verification_is_read_only(self):
        before = snapshot(self.home)
        proc = verify(self.home, "--client", "all")
        after = snapshot(self.home)
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertEqual(after, before)

    def test_a_changed_managed_instruction_fails(self):
        path = self.home / ".codex" / "AGENTS.md"
        original = path.read_bytes()
        try:
            path.write_bytes(original.replace(b"Master Repo path:",
                                              b"Wrong repository path:"))
            proc = verify(self.home, "--client", "codex")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("managed block does not match", proc.stdout)
        finally:
            path.write_bytes(original)

    def test_invalid_hook_json_fails_without_a_traceback(self):
        path = self.home / ".cursor" / "hooks.json"
        original = path.read_bytes()
        try:
            path.write_text("{ invalid", encoding="utf-8")
            proc = verify(self.home, "--client", "cursor")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("invalid JSON", proc.stdout)
            self.assertNotIn("Traceback", proc.stderr + proc.stdout)
        finally:
            path.write_bytes(original)


class SelectionAndPartialInstall(unittest.TestCase):
    def test_installed_only_skips_an_empty_home(self):
        with tempfile.TemporaryDirectory() as scratch:
            proc = verify(pathlib.Path(scratch), "--installed-only", "--client", "all")
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn("6 skipped", proc.stdout)

    def test_installed_only_does_not_hide_a_partial_install(self):
        with tempfile.TemporaryDirectory() as scratch:
            home = pathlib.Path(scratch)
            (home / ".cursor" / "skills").mkdir(parents=True)
            proc = verify(home, "--installed-only", "--client", "cursor")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("FAIL cursor", proc.stdout)

    def test_client_aliases_and_repeated_values_are_stable(self):
        verifier = load_verifier()
        self.assertEqual(
            verifier.parse_clients(["gpt,cursor", "copilot-cli"]),
            ("codex", "cursor", "copilot"),
        )

    def test_unknown_client_is_an_argument_error(self):
        with tempfile.TemporaryDirectory() as scratch:
            proc = verify(pathlib.Path(scratch), "--client", "not-a-client")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("unknown client", proc.stderr)


class RepositoryInstructionCopies(unittest.TestCase):
    def test_cloud_instruction_blocks_match_the_canonical_bytes(self):
        verifier = load_verifier()
        block = (ROOT / "docs" / "auto-mode-block.txt").read_text(encoding="utf-8")
        expected = f"{verifier.BEGIN}\n{block.strip()}\n{verifier.END}"
        for relative in (
            "AGENTS.md",
            "CLAUDE.md",
            "GEMINI.md",
            ".github/copilot-instructions.md",
            ".gemini/styleguide.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertEqual(verifier.Verifier._managed_block(text), expected, relative)


if __name__ == "__main__":
    unittest.main()

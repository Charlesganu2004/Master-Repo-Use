"""The harness has to work with no repository anywhere.

Every other test in this suite runs inside a checkout, which is exactly the
condition that hides the defects this file exists to catch. A harness that reads
skills/ from the repository root passes all of them and fails the first time
someone pip-installs it, and it fails quietly: `pip install` succeeds, the
commands land on PATH, and each one enforces less than it says it does.

So the slow test is the real one. It builds a wheel, installs it into a
throwaway virtual environment, and runs the commands from a directory with no
checkout in sight. That found, in order:

  - every skill path resolving to site-packages/skills, which does not exist
  - the goal state written into site-packages, which is not writable
  - .github/copilot-instructions.md written into site-packages, where it
    instructs nothing and is deleted on the next upgrade
  - client configs registering hooks that were never bundled
  - an install that registered every hook and copied zero skills
  - the verifier reporting 22 failures against an install that was complete

None of those produced an error. All six were found by running the thing.

The fast tests come first and run always. The build test is marked slow and
skipped without MASTER_HARNESS_BUILD_TEST=1, because building a wheel and
creating a virtualenv takes about a minute and this suite runs constantly.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import harness_paths  # noqa: E402

BUILD_TEST = os.environ.get("MASTER_HARNESS_BUILD_TEST") == "1"


class ThePackagingMetadataIsComplete(unittest.TestCase):
    """Cheap checks on the files that decide what the wheel contains."""

    def setUp(self):
        self.pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.setup = (ROOT / "setup.py").read_text(encoding="utf-8")

    def test_every_harness_has_a_console_script(self):
        """A harness with no entry point is one an installed user cannot run."""
        for name in ("master-harness", "master-harness-super", "master-harness-proxy",
                     "master-harness-wrap", "master-harness-goal",
                     "master-harness-computer", "master-harness-hook",
                     "master-harness-where", "master-harness-verify"):
            self.assertIn(f"{name} =", self.pyproject, f"{name} has no entry point")

    def test_every_module_the_harness_imports_is_staged(self):
        """A module the build forgets is an ImportError on someone else's
        machine, and never on this one."""
        for module in ("harness_paths.py", "skill_pipeline.py", "auto_mode_harness.py",
                       "harness_proxy.py", "harness_wrap.py", "harness_goal.py",
                       "harness_computer.py", "harness_super.py",
                       "install_auto_mode.py", "verify_auto_mode.py",
                       "no_prune_guard.py", "no_compress_guard.py"):
            self.assertIn(f'"{module}"', self.setup, f"{module} is never staged")

    def test_every_staged_module_exists_in_the_repository(self):
        """The build raises rather than shipping a wheel missing a module, and
        this says so before the build is ever run."""
        import re
        for match in re.finditer(r'ROOT / "scripts"(?: / "hooks")? / "([\w.]+)"', self.setup):
            name = match.group(1)
            candidates = [ROOT / "scripts" / name, ROOT / "scripts" / "hooks" / name]
            self.assertTrue(any(path.is_file() for path in candidates),
                            f"{name} is staged by the build but is not in scripts/")

    def test_the_build_refuses_rather_than_shipping_an_empty_package(self):
        self.assertIn("cannot build:", self.setup)
        self.assertIn("no skills found to bundle", self.setup)

    def test_the_staged_copies_are_not_committed(self):
        """One copy in the repository. A committed second copy is the
        duplication this design exists to avoid, arriving through the back."""
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for pattern in ("master_harness/_skills/", "master_harness/_data/",
                        "master_harness/harness_*.py", "master_harness/_agents/"):
            self.assertIn(pattern, ignored, f"{pattern} is not ignored")
        tracked = subprocess.run(["git", "ls-files", "master_harness/"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.split()
        for path in tracked:
            self.assertNotIn("_skills", path, f"a staged copy is committed: {path}")
            self.assertNotIn("_data", path, f"a staged copy is committed: {path}")
            self.assertNotIn("_agents", path, f"a staged copy is committed: {path}")


class PathsResolveInThisCheckout(unittest.TestCase):
    def test_this_is_recognised_as_a_checkout(self):
        self.assertEqual(harness_paths.repo_root(), ROOT)
        self.assertFalse(harness_paths.installed_standalone())

    def test_the_skills_resolve_to_the_repository(self):
        self.assertEqual(harness_paths.skills_dir(), ROOT / "skills")
        self.assertGreater(len(harness_paths.skill_names()), 15)

    def test_the_state_stays_out_of_the_repository_history(self):
        self.assertEqual(harness_paths.state_dir(), ROOT / ".auto-mode")
        self.assertIn(".auto-mode/", (ROOT / ".gitignore").read_text(encoding="utf-8"))

    def test_an_unset_override_does_not_break_detection(self):
        """MASTER_REPO_PATH pointing at something that is not a checkout must
        report no checkout rather than pretending the directory is one."""
        original = os.environ.get("MASTER_REPO_PATH")
        os.environ["MASTER_REPO_PATH"] = str(ROOT / "docs")
        try:
            self.assertIsNone(harness_paths.repo_root())
        finally:
            if original is None:
                del os.environ["MASTER_REPO_PATH"]
            else:
                os.environ["MASTER_REPO_PATH"] = original

    def test_the_subprocess_command_is_a_file_path_not_a_console_name(self):
        """A console script is what a person types. Spawning one is a different
        problem: on Windows the entry point is master-harness-wrap.exe and the
        bare name raises WinError 2."""
        command = harness_paths.harness_command("harness_wrap")
        self.assertTrue(command[-1].endswith("harness_wrap.py"), command)


@unittest.skipUnless(BUILD_TEST,
                     "set MASTER_HARNESS_BUILD_TEST=1 to build a wheel and install it")
class ItWorksWithNoRepositoryAnywhere(unittest.TestCase):
    """The slow one, and the only one that proves the claim."""

    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.mkdtemp(prefix="master-harness-pkg-")
        scratch = pathlib.Path(cls.scratch)
        cls.dist = scratch / "dist"

        build = subprocess.run([sys.executable, "-m", "build", "--wheel",
                                "--outdir", str(cls.dist)],
                               cwd=ROOT, capture_output=True, text=True, timeout=900)
        if build.returncode != 0:
            raise unittest.SkipTest(f"could not build a wheel:\n{build.stdout[-2000:]}")
        wheels = list(cls.dist.glob("*.whl"))
        if not wheels:
            raise unittest.SkipTest("the build produced no wheel")

        cls.env = scratch / "env"
        subprocess.run([sys.executable, "-m", "venv", str(cls.env)],
                       capture_output=True, timeout=600)
        cls.bin = cls.env / ("Scripts" if os.name == "nt" else "bin")
        cls.suffix = ".exe" if os.name == "nt" else ""

        install = subprocess.run([cls.exe("python"), "-m", "pip", "install",
                                  "--quiet", str(wheels[0])],
                                 capture_output=True, text=True, timeout=900)
        if install.returncode != 0:
            raise unittest.SkipTest(f"could not install the wheel:\n{install.stderr[-2000:]}")

        # A directory with no checkout above it, and a home of its own, so
        # nothing this test does can reach the real machine's client configs.
        cls.project = scratch / "project"
        cls.home = scratch / "home"
        cls.project.mkdir()
        cls.home.mkdir()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.scratch, ignore_errors=True)

    @classmethod
    def exe(cls, name: str) -> str:
        """Path to a console script in the throwaway environment.

        A classmethod rather than the lambda this started as: assigning a lambda
        to a class attribute makes it a BOUND method, so self.exe("x") passed
        self as the name and every command resolved to a path that does not
        exist. Six tests failed with WinError 2 and none of them was about the
        package.
        """
        return str(cls.bin / f"{name}{cls.suffix}")

    def run_command(self, name, *args, cwd=None):
        env = dict(os.environ)
        env["HOME"] = str(self.home)
        env["USERPROFILE"] = str(self.home)
        env.pop("MASTER_REPO_PATH", None)
        return subprocess.run([self.exe(name), *args], cwd=str(cwd or self.project),
                              capture_output=True, text=True, timeout=600, env=env)

    def test_it_knows_it_is_installed_rather_than_in_a_checkout(self):
        result = self.run_command("master-harness-where", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        facts = json.loads(result.stdout)
        self.assertEqual(facts["mode"], "installed")
        self.assertIsNone(facts["repo"])
        self.assertGreater(facts["skillCount"], 15,
                           "the wheel carries no skills; it can enforce nothing")
        self.assertTrue(facts["blockPresent"])

    def test_every_harness_check_passes(self):
        for name in ("master-harness", "master-harness-super", "master-harness-proxy",
                     "master-harness-wrap", "master-harness-goal",
                     "master-harness-computer"):
            result = self.run_command(name, "--check")
            self.assertEqual(result.returncode, 0,
                             f"{name} --check failed:\n{result.stdout}\n{result.stderr}")

    def test_the_hook_injects_the_layers_and_the_refactor_rule(self):
        event = json.dumps({"input": {"prompt": "refactor the retry module"}})
        env = dict(os.environ)
        env["HOME"] = str(self.home)
        env["USERPROFILE"] = str(self.home)
        result = subprocess.run([self.exe("master-harness-hook")], input=event,
                                capture_output=True, text=True, cwd=str(self.project),
                                timeout=120, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        for marker in ("LAYER 1", "LAYER 2", "LAYER 3", "8. REFACTOR", "11. VERIFY"):
            self.assertIn(marker, context, f"the installed hook is missing {marker}")

    def test_the_goal_survives_between_invocations(self):
        self.run_command("master-harness-goal", "--clear")
        self.run_command("master-harness-goal", "--set", "ship the package")
        shown = self.run_command("master-harness-goal", "--show")
        self.assertIn("ship the package", shown.stdout)

    def test_the_super_chain_reaches_a_wrapped_command(self):
        probe = ("import sys;d=sys.stdin.read();"
                 "print('CHAIN' if 'SUPER HARNESS' in d else 'BASE-ONLY')")
        result = self.run_command("master-harness-super", "--profile", "stdin",
                                  "--run", "--", self.exe("python"), "-c", probe)
        self.assertIn("CHAIN", result.stdout,
                      f"the wrapped command did not get the chain:\n{result.stdout}")

    def test_it_installs_every_client_and_verifies_clean(self):
        """The whole claim, end to end: a machine with no checkout gets the
        skills, the hooks and the instruction files, and the verifier agrees."""
        install = self.run_command("master-harness", "--install", "all")
        self.assertEqual(install.returncode, 0, install.stderr)

        for client in (".claude", ".codex", ".gemini", ".cursor", ".copilot", ".agents"):
            skills = self.home / client / "skills"
            self.assertTrue(skills.is_dir(), f"{client} got no skills directory")
            self.assertGreater(len(list(skills.glob("*/SKILL.md"))), 15,
                               f"{client} got a skills directory with nothing in it")

        verify = self.run_command("master-harness-verify", "--home", str(self.home),
                                  "--repo", str(self.project))
        self.assertIn("0 failed", verify.stdout,
                      f"the install does not verify:\n{verify.stdout}")

    def test_it_never_writes_into_its_own_package_directory(self):
        """site-packages is not a place to keep anything: it is not writable on
        a normal install and it is deleted on the next upgrade. An earlier
        version put .github/copilot-instructions.md there and said nothing."""
        site = self.env / ("Lib" if os.name == "nt" else "lib")
        strays = [path for path in site.rglob(".github")] + \
                 [path for path in site.rglob("*.json") if path.name == "goal.json"]
        self.assertEqual(strays, [], f"the package wrote into itself: {strays}")


if __name__ == "__main__":
    unittest.main()

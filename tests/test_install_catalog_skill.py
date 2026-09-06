"""Adopting a third-party skill pack is a reviewed step, and these are the review.

Catalog entries are reference-only on purpose: a repository URL is not a vetted
install. install_catalog_skill.py adds the missing middle step without weakening
that, and every property below is one of the reasons it is safe to run at all.
Losing any of them turns it back into `git clone` pointed at a config directory.

The one that matters most is the first. A skills marketplace is precisely where a
near-name repository gets installed by mistake, and the catalog already knows
which one was vetted, so an uncatalogued slug is refused rather than scanned.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "install_catalog_skill.py"
SOURCE = SCRIPT.read_text(encoding="utf-8")

sys.path.insert(0, str(ROOT / "scripts"))
import install_catalog_skill as installer  # noqa: E402


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True, cwd=str(ROOT))


class TheCatalogGate(unittest.TestCase):
    def test_an_uncatalogued_slug_is_refused_before_anything_is_fetched(self):
        result = run("definitely-not-real/nothing-here", "--dry-run")
        self.assertEqual(result.returncode, 2)
        self.assertIn("not in repo-lists", result.stderr)

    def test_the_refusal_explains_itself_rather_than_just_failing(self):
        result = run("definitely-not-real/nothing-here")
        self.assertIn("typosquat", result.stderr.lower())

    def test_a_catalogued_slug_passes_the_gate(self):
        catalog = installer.catalogued_slugs()
        self.assertIn("mattpocock/skills", catalog)
        self.assertTrue(catalog["mattpocock/skills"].endswith(".txt"))

    def test_the_gate_reads_the_lists_not_the_generated_data(self):
        """It has to work in a fresh clone, before anything has been built."""
        self.assertIn('ROOT / "repo-lists"', SOURCE)
        self.assertNotIn("atlas-data.json", SOURCE)

    def test_a_near_name_match_is_surfaced_rather_than_silently_accepted(self):
        result = run("someone-else/skills")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Catalogued repositories with that name", result.stderr)


class NothingFromTheRepositoryIsExecuted(unittest.TestCase):
    """The whole risk of a skill pack is that installing one runs its code."""

    def test_git_is_the_only_thing_this_script_ever_runs(self):
        """Checked on the argv lists, not on the prose.

        An earlier version of this test banned the strings, and failed on the
        comment explaining that submodules are deliberately not fetched. Naming a
        thing in order to refuse it is not doing it, which is the same mistake the
        no-compress guard had.
        """
        argv = re.findall(r"subprocess\.run\(\s*\[([^\]]*)\]", SOURCE, re.S)
        self.assertTrue(argv, "no subprocess call found; the check would pass vacuously")
        for call in argv:
            first = call.strip().split(",")[0].strip().strip("\"'")
            self.assertEqual(first, "git", f"this script runs {first!r}, not only git")

    def test_no_package_manager_appears_in_any_command(self):
        argv = re.findall(r"subprocess\.run\(\s*\[([^\]]*)\]", SOURCE, re.S)
        for call in argv:
            for runner in ("npm", "npx", "yarn", "pnpm", "pip", "make", "setup.sh"):
                self.assertNotIn(runner, call, f"{runner} would execute repository code")

    def test_git_hooks_are_disabled_for_the_clone(self):
        """A repository's own hooks run during clone unless hooksPath is emptied."""
        self.assertIn('"core.hooksPath="', SOURCE)

    def test_the_clone_never_prompts_for_credentials(self):
        self.assertIn('GIT_TERMINAL_PROMPT"] = "0"', SOURCE)

    def test_submodules_are_not_fetched(self):
        """A submodule is a second repository nobody catalogued."""
        argv = re.findall(r"subprocess\.run\(\s*\[([^\]]*)\]", SOURCE, re.S)
        for call in argv:
            self.assertNotIn("recurse-submodules", call)

    def test_the_clone_is_shallow(self):
        self.assertIn('"--depth", "1"', SOURCE)


class TheScanDecides(unittest.TestCase):
    def test_it_uses_the_repositorys_own_scanner(self):
        self.assertIn("import catalog_security as security", SOURCE)
        self.assertIn("security.scan_text", SOURCE)

    def test_findings_are_printed_before_the_refusal(self):
        """--accept-findings has to be a decision, not a flag copied off a wiki."""
        printed = SOURCE.index("for finding in findings:")
        refused = SOURCE.index("REFUSED: {len(serious)} finding")
        self.assertLess(printed, refused)

    def test_an_incomplete_scan_is_reported(self):
        self.assertIn("has_scanner_error", SOURCE)

    def test_only_high_and_above_block_an_install(self):
        """INFO lines are noise; blocking on them would train people to force it."""
        self.assertIn('f.startswith(("CRITICAL", "HIGH"))', SOURCE)


class NoCapabilityIsQuietlyReplaced(unittest.TestCase):
    """The no-prune rule, applied to the one script that writes into skill roots."""

    def test_install_names_are_namespaced_by_owner(self):
        name = installer.install_name(
            "mattpocock/skills",
            pathlib.Path("/tmp/clone/skills/engineering/teach"),
            pathlib.Path("/tmp/clone"))
        self.assertEqual(name, "mattpocock-teach")

    def test_two_owners_shipping_the_same_skill_name_do_not_collide(self):
        clone = pathlib.Path("/tmp/clone")
        first = installer.install_name("alice/packs", clone / "review", clone)
        second = installer.install_name("bob/packs", clone / "review", clone)
        self.assertNotEqual(first, second)

    def test_a_folder_this_script_did_not_install_is_never_overwritten(self):
        self.assertIn(".installed-from", SOURCE)
        self.assertIn("already exists and was not installed by this", SOURCE)

    def test_provenance_is_written_beside_every_install(self):
        """So an audit can answer where a skill came from without guessing."""
        self.assertIn('(target / ".installed-from").write_text', SOURCE)


class ItServesEveryClient(unittest.TestCase):
    def test_both_skill_roots_are_written(self):
        self.assertEqual(set(installer.SKILL_ROOTS), {"Claude Code", "Antigravity"})

    def test_the_antigravity_path_is_the_documented_one(self):
        self.assertEqual(installer.SKILL_ROOTS["Antigravity"].as_posix(),
                         ".gemini/config/skills")
        # As above: the comment explains that ~/.antigravity does not exist, so the
        # ban is on writing there, not on saying so.
        self.assertNotIn('Path(".antigravity")', SOURCE)
        self.assertNotIn('"$HOME/.antigravity', SOURCE)


class ADryRunWritesNothing(unittest.TestCase):
    def test_the_dry_run_branch_precedes_every_write(self):
        body = SOURCE[SOURCE.index("for client, folder, target, name in planned:"):]
        self.assertLess(body.index("if args.dry_run:"), body.index("shutil.copytree"))

    def test_a_skill_pack_with_no_skill_md_is_reported_not_installed(self):
        self.assertIn("no SKILL.md anywhere in this repository", SOURCE)


if __name__ == "__main__":
    unittest.main()

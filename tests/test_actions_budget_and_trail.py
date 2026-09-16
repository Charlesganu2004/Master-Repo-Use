"""The automation may act, provided it stays in budget and says what it did.

Two guarantees worth testing, because both fail silently otherwise: a scan that
overruns the Actions allowance costs real money, and a scan that acts without
recording it leaves nothing to audit.
"""
import datetime as dt
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import actions_budget as budget  # noqa: E402
import security_trail as trail  # noqa: E402

WORKFLOW = (ROOT / ".github" / "workflows" / "catalog-guardian.yml").read_text(encoding="utf-8")


class TheBudgetGate(unittest.TestCase):
    def test_the_pro_allowance_is_what_charles_actually_has(self):
        self.assertEqual(budget.INCLUDED_MINUTES, 3000)

    def test_runner_multipliers_are_applied(self):
        """A workflow that drifts to macOS bills ten times what it did."""
        self.assertEqual(budget.MULTIPLIERS["UBUNTU"], 1)
        self.assertEqual(budget.MULTIPLIERS["WINDOWS"], 2)
        self.assertEqual(budget.MULTIPLIERS["MACOS"], 10)

    def test_the_cycle_starts_at_the_month_boundary(self):
        self.assertEqual(budget.cycle_start(dt.date(2026, 9, 17)), dt.date(2026, 9, 1))

    def test_the_expensive_job_checks_headroom_first(self):
        self.assertIn("actions_budget.py --gate", WORKFLOW)

    def test_every_costly_step_respects_the_gate(self):
        """A gate that only guards the first step saves nothing."""
        for step in ("Install scanners", "Rotating deep scan", "Report security findings"):
            index = WORKFLOW.index(step)
            window = WORKFLOW[index:index + 200]
            self.assertIn("budget.outputs.ok", window, f"{step} is not gated")


class TheSecurityTrail(unittest.TestCase):
    def test_cells_cannot_break_the_table(self):
        self.assertNotIn("|", trail.cell("a | b | c"))
        self.assertNotIn("\n", trail.cell("line one\nline two"))

    def test_long_values_are_truncated_not_dropped(self):
        out = trail.cell("x" * 500, limit=40)
        self.assertEqual(len(out), 40)
        self.assertTrue(out.endswith("..."))

    def test_the_trail_states_what_a_bot_may_not_do(self):
        self.assertIn("It may not merge", trail.HEADER)
        self.assertIn("may not delete a catalog entry", trail.HEADER)

    def test_quiet_scans_are_still_recorded(self):
        """An absence of rows must never be mistakable for an absence of scans."""
        self.assertIn("including the ones that found nothing", trail.HEADER)

    def test_the_trail_file_exists_and_has_rows(self):
        path = ROOT / "docs" / "SECURITY-TRAIL.md"
        self.assertTrue(path.exists(), "run scripts/security_trail.py")
        self.assertIn("| UTC | Run | Action |", path.read_text(encoding="utf-8"))


class LeastPrivilege(unittest.TestCase):
    """The job that clones untrusted code must never hold a write token."""

    def test_the_scanning_job_cannot_write(self):
        start = WORKFLOW.index("  deep-scan-rotation:")
        end = WORKFLOW.index("  record-trail:")
        self.assertIn("contents: read", WORKFLOW[start:end])
        self.assertNotIn("contents: write", WORKFLOW[start:end])

    def test_the_writing_job_does_not_clone_third_party_code(self):
        start = WORKFLOW.index("  record-trail:")
        end = WORKFLOW.index("  approved-maintenance:")
        body = WORKFLOW[start:end]
        self.assertIn("contents: write", body)
        for scanner in ("gitleaks", "trivy", "osv-scanner", "semgrep", "catalog_guardian"):
            self.assertNotIn(scanner, body, f"{scanner} runs in the job that can push")

    def test_the_bot_pushes_to_a_branch_never_to_main(self):
        self.assertIn("HEAD:automation/security-trail", WORKFLOW)
        self.assertNotIn("push origin main", WORKFLOW)

    def test_the_push_still_works_the_second_week(self):
        """It pushed once, created the branch, and refused every week after.

        `--force-with-lease` with no argument compares against the remote-tracking
        ref, and this job's checkout fetches only main. Creating a branch needs no
        lease, so the first run passed and every later one died on "stale info"
        with the row already committed and nothing recorded. Run the workflow's own
        push block twice against a real remote, which is the case that failed.
        """
        script = push_block()
        self.assertIn("git push origin", script)

        work = pathlib.Path(tempfile.mkdtemp())
        try:
            remote, seed = work / "remote.git", work / "seed"
            subprocess.run(["git", "init", "--quiet", "--bare", "--initial-branch=main",
                            str(remote)], check=True)
            subprocess.run(["git", "clone", "--quiet", str(remote), str(seed)], check=True)

            def git(cwd, *args):
                return subprocess.run(("git",) + args, cwd=cwd, check=True,
                                      capture_output=True, text=True).stdout

            git(seed, "config", "user.name", "Test")
            git(seed, "config", "user.email", "test@example.com")
            git(seed, "checkout", "--quiet", "-b", "main")
            (seed / "docs").mkdir()
            (seed / "docs" / "SECURITY-TRAIL.md").write_text("| seeded |", encoding="utf-8")
            git(seed, "add", "-A")
            git(seed, "commit", "--quiet", "-m", "seed")
            git(seed, "push", "--quiet", "origin", "main")

            for week in (1, 2):
                # A scheduled run is a fresh shallow checkout of main, so it holds
                # no remote-tracking ref for the trail branch. A push in a reused
                # clone creates one and hides the bug, so clone again each week.
                run = work / f"week{week}"
                subprocess.run(["git", "clone", "--quiet", "--depth", "1", "--single-branch",
                                "--branch", "main", str(remote), str(run)], check=True)
                git(run, "config", "user.name", "Test")
                git(run, "config", "user.email", "test@example.com")
                (run / "docs" / "SECURITY-TRAIL.md").write_text(
                    f"| seeded |{chr(10)}| week {week} |", encoding="utf-8")
                done = subprocess.run(["bash", "-c", script], cwd=run,
                                      capture_output=True, text=True)
                self.assertNotIn("stale info", done.stderr,
                                 f"week {week} refused the push it had no ref to compare")
                self.assertEqual(done.returncode, 0,
                                 f"week {week} push failed: {done.stdout} {done.stderr}")

            pushed = git(remote, "log", "--oneline", "automation/security-trail")
            self.assertEqual(pushed.count("trail: deep-scan rotation"), 1,
                             "each run replaces the branch with main plus its own row")
            self.assertIn("week 2", git(remote, "show",
                                        "automation/security-trail:docs/SECURITY-TRAIL.md"))
        finally:
            shutil.rmtree(work, ignore_errors=True)


def push_block():
    """The shell of the workflow step that records the row, ready to run."""
    step = WORKFLOW.index("      - name: Commit to the automation branch, never to main")
    body = WORKFLOW[WORKFLOW.index("run: |", step) + len("run: |"):]
    lines = []
    for line in body.splitlines()[1:]:
        if line.strip() and not line.startswith(" " * 10):
            break
        lines.append(line[10:])
    return re.sub(r"\$\{\{[^}]*\}\}", "test-run", "\n".join(lines))


if __name__ == "__main__":
    unittest.main()

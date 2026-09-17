"""The automation may act, provided it stays in budget and says what it did.

Two guarantees worth testing, because both fail silently otherwise: a scan that
overruns the Actions allowance costs real money, and a scan that acts without
recording it leaves nothing to audit.
"""
import datetime as dt
import os
import pathlib
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
RECORD = ROOT / "scripts" / "record_trail_row.sh"


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


class TheBudgetIsReadOrSaysItCouldNot(unittest.TestCase):
    """A gate that cannot read the budget reported 0 minutes used and passed.

    No job granted actions: read, so the runs API refused the workflow token, the
    loop stopped on the HTTP error, and the script printed "used 0 of 3000". The
    only automated trail row on record says exactly that. A number the script
    could not measure must never be printed as a measurement.
    """

    RUN = {"id": 1, "name": "Catalog Guardian"}
    JOB = {"started_at": "2026-09-14T14:16:00Z", "completed_at": "2026-09-14T14:25:30Z",
           "labels": ["ubuntu-latest"]}

    def run_main(self, *argv, responses):
        from unittest import mock
        import io
        import contextlib
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(budget, "request", side_effect=responses), \
             mock.patch.object(sys, "argv", ["actions_budget.py", "--repo", "o/r", *argv]), \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = budget.main()
        return code, out.getvalue(), err.getvalue()

    @staticmethod
    def refused(*_args, **_kwargs):
        import urllib.error
        raise urllib.error.HTTPError("https://api.github.com", 403, "Resource not accessible by integration", {}, None)

    def test_an_unreadable_budget_is_reported_as_unknown(self):
        code, out, _ = self.run_main("--cell", responses=self.refused)
        self.assertEqual(0, code)
        self.assertIn("unknown", out)
        self.assertNotIn("0 of 3000", out)

    def test_the_gate_proceeds_on_an_unreadable_budget_and_says_so(self):
        """Fail open, deliberately and loudly.

        The rotation is capped at 45 minutes a week, about 200 of 3,000 a month,
        so it cannot overrun the allowance by itself; failing closed would stop
        every security scan whenever the API is unreadable.
        """
        code, out, err = self.run_main("--gate", "--reserve", "600", responses=self.refused)
        self.assertEqual(0, code)
        self.assertIn("could not be read", out + err)

    def test_a_readable_budget_is_a_measurement(self):
        responses = [{"workflow_runs": [self.RUN]}, {"jobs": [self.JOB]}, {"workflow_runs": []}]
        code, out, _ = self.run_main("--cell", responses=responses)
        self.assertEqual(0, code)
        self.assertEqual("10 of 3000 minutes", out.strip())

    def test_a_partial_read_is_a_lower_bound(self):
        """One run's jobs refused, as a rate limit does partway through."""
        def respond(url, token):
            if "/runs/2/jobs" in url:
                self.refused()
            if "/runs/1/jobs" in url:
                return {"jobs": [self.JOB]}
            if "page=1&" in url:
                return {"workflow_runs": [self.RUN, {"id": 2, "name": "Pages"}]}
            return {"workflow_runs": []}
        code, out, _ = self.run_main("--cell", responses=respond)
        self.assertEqual("at least 10 of 3000 minutes", out.strip())

    def test_the_gate_still_stops_when_headroom_is_measured_low(self):
        job = dict(self.JOB, completed_at="2026-09-16T14:16:00Z")   # 2 days = 2880 minutes
        responses = [{"workflow_runs": [self.RUN]}, {"jobs": [job]}, {"workflow_runs": []}]
        code, _, _ = self.run_main("--gate", "--reserve", "600", responses=responses)
        self.assertEqual(1, code)

    def test_every_job_that_reads_the_budget_may_read_actions(self):
        for job in ("  deep-scan-rotation:", "  record-trail:", "  approved-maintenance:"):
            start = WORKFLOW.index(job)
            block = WORKFLOW[start:start + 700]
            with self.subTest(job=job.strip()):
                self.assertIn("actions: read", block[:block.index("steps:")])


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
        script = RECORD.read_text(encoding="utf-8")
        self.assertIn("branch=automation/security-trail", script)
        self.assertIn('"HEAD:refs/heads/$branch"', script)
        pushes = [line for line in script.splitlines() if " push " in line and not line.lstrip().startswith("#")]
        self.assertTrue(pushes)
        for line in pushes:
            self.assertNotIn("--force", line, "an append-only trail must never be force-pushed")
        self.assertNotIn("push origin main", WORKFLOW)
        jobs = {"record-trail": WORKFLOW[WORKFLOW.index("  record-trail:"):WORKFLOW.index("  approved-maintenance:")],
                "approved-maintenance": WORKFLOW[WORKFLOW.index("  approved-maintenance:"):]}
        for name, body in jobs.items():
            with self.subTest(job=name):
                self.assertIn("scripts/record_trail_row.sh", body)

    def test_rows_accumulate_week_after_week(self):
        """Two failures, both in the step this script replaced.

        It pushed with a bare --force-with-lease, which git reads as stale when the
        checkout fetched only main, so every run after the one that created the
        branch recorded nothing. And it pushed "main plus this run's row" over the
        branch, so even a run that got through erased the previous run's row. An
        append-only trail has to keep both weeks.
        """
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
            (seed / "scripts").mkdir()
            shutil.copy(ROOT / "scripts" / "security_trail.py", seed / "scripts" / "security_trail.py")
            trail.append("seeded", "", "", "", "", seed / "docs" / "SECURITY-TRAIL.md")
            git(seed, "add", "-A")
            git(seed, "commit", "--quiet", "-m", "seed")
            git(seed, "push", "--quiet", "origin", "main")
            main_before = git(remote, "rev-parse", "main")

            for week in (1, 2):
                # A scheduled run is a fresh shallow single-branch checkout of main,
                # so it holds no ref for the trail branch. Clone again each week.
                run = work / f"week{week}"
                subprocess.run(["git", "clone", "--quiet", "--depth", "1", "--single-branch",
                                "--branch", "main", remote.as_uri(), str(run)], check=True)
                done = subprocess.run(
                    ["bash", str(RECORD), "--action", f"rotation-week-{week}", "--budget", "1 of 3000 minutes"],
                    cwd=run, capture_output=True, text=True,
                    env={**os.environ, "TRAIL_SUBJECT": f"week {week}"})
                self.assertEqual(done.returncode, 0,
                                 f"week {week} failed: {done.stdout} {done.stderr}")
                self.assertNotIn("stale info", done.stderr)

            rows = git(remote, "show", "automation/security-trail:docs/SECURITY-TRAIL.md")
            self.assertIn("rotation-week-1", rows, "week 2 erased week 1's row")
            self.assertIn("rotation-week-2", rows)
            self.assertEqual(main_before, git(remote, "rev-parse", "main"), "the trail touched main")
            self.assertNotIn("rotation-week", git(remote, "show", "main:docs/SECURITY-TRAIL.md"))
        finally:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

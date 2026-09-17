"""A rotation that runs out of time must keep what it scanned.

Every deep-scan rotation on record ended cancelled at the job's 45 minute timeout:
2026-09-07, 2026-09-14 and the dispatched run on 2026-09-17, which was cut at
45m16s in the scan step. Cancellation skips the cache-save step, so nothing was
persisted, coverage stayed at 14 of 304 from 2026-09-01, and the trail row read
"cancelled".

Scanning now stops at a time budget inside the job's timeout. The repositories not
reached keep their previous state, and the run finishes: it writes the status file,
the report and its trail row.
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import catalog_guardian_legacy as legacy  # noqa: E402

WORKFLOW = (ROOT / ".github" / "workflows" / "catalog-guardian.yml").read_text(encoding="utf-8")


class Clock:
    """Advances only when a scan runs, so a test never waits."""

    def __init__(self, minutes_per_scan: float = 5.0):
        self.now = 0.0
        self.minutes_per_scan = minutes_per_scan

    def __call__(self) -> float:
        return self.now

    def scan(self) -> None:
        self.now += self.minutes_per_scan * 60


class TheScanBudget(unittest.TestCase):
    def test_it_is_unlimited_when_unset(self):
        clock = Clock()
        budget = legacy.ScanBudget(0, clock)
        clock.now = 10_000 * 60
        self.assertFalse(budget.exhausted())

    def test_it_reports_exhausted_at_the_limit(self):
        clock = Clock()
        budget = legacy.ScanBudget(30, clock)
        clock.now = 29 * 60
        self.assertFalse(budget.exhausted())
        clock.now = 30 * 60
        self.assertTrue(budget.exhausted())


class TheRotationFinishesAndKeepsWhatItScanned(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.clock = Clock(minutes_per_scan=5)
        catalog = self.tmp / "all-curated.txt"
        catalog.write_text("".join(f"owner/repo{i}\n" for i in range(8)), encoding="utf-8")
        self.state = self.tmp / "catalog-status.json"
        self.patches = [
            mock.patch.object(legacy, "CATALOG", catalog),
            mock.patch.object(legacy, "STATE", self.state),
            mock.patch.object(legacy, "REPORT", self.tmp / "CATALOG-STATUS.md"),
            mock.patch.object(legacy, "SVG", self.tmp / "catalog-status.svg"),
            mock.patch.object(legacy, "OVERRIDES", self.tmp / "overrides.json"),
            mock.patch.object(legacy, "metadata", lambda repo: {
                "pushed_at": "2026-09-01T00:00:00Z", "updated_at": "2026-09-01T00:00:00Z",
                "archived": False, "disabled": False, "license": {"key": "mit"}}),
            mock.patch.object(legacy, "latest_release_age", lambda repo: None),
        ]
        for patch in self.patches:
            patch.start()
        self.scanned: list[str] = []

        def fake_deep_scan(repo):
            self.scanned.append(repo)
            self.clock.scan()
            return [], False

        mock.patch.object(legacy, "deep_scan", fake_deep_scan).start()
        self.patches.append(mock.patch.object(legacy, "deep_scan", fake_deep_scan))

    def tearDown(self):
        mock.patch.stopall()

    def run_main(self, *argv):
        with mock.patch.object(sys, "argv", ["catalog_guardian.py", *argv]), \
             mock.patch.object(legacy.time, "monotonic", self.clock):
            return legacy.main()

    def test_scanning_stops_at_the_budget_and_the_run_still_finishes(self):
        code = self.run_main("--deep", "--batch-size", "8", "--time-budget-minutes", "12")
        self.assertEqual(0, code)
        # 5 simulated minutes per scan: the third starts at 10 minutes, the fourth at 15.
        self.assertEqual(3, len(self.scanned), self.scanned)
        written = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertEqual(8, len(written["repos"]), "every repository must still get a row")
        self.assertEqual(3, sum(1 for r in written["repos"] if r["deep_scanned"]),
                         "the scans that did run must be saved, or coverage never advances")

    def test_without_a_budget_every_repository_in_the_slice_is_scanned(self):
        self.run_main("--deep", "--batch-size", "8")
        self.assertEqual(8, len(self.scanned))

    def test_the_rotation_job_sets_a_budget_inside_its_timeout(self):
        rotation = WORKFLOW[WORKFLOW.index("  deep-scan-rotation:"):WORKFLOW.index("  record-trail:")]
        timeout = int(rotation.split("timeout-minutes:")[1].split()[0])
        budget = int(rotation.split("--time-budget-minutes")[1].split()[0].strip("'\""))
        self.assertLess(budget, timeout, "the budget must stop the scan before the runner kills the job")

    def test_the_approved_job_sets_one_too(self):
        approved = WORKFLOW[WORKFLOW.index("  approved-maintenance:"):]
        timeout = int(approved.split("timeout-minutes:")[1].split()[0])
        budget = int(approved.split("--time-budget-minutes")[1].split()[0].strip("'\""))
        self.assertLess(budget, timeout)


if __name__ == "__main__":
    unittest.main()

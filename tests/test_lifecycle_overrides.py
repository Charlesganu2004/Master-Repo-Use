#!/usr/bin/env python3
"""Owner lifecycle overrides must actually settle the audit.

Before this was fixed, `reference` and `keep` overrides still classified as REVIEW
whenever the repo was older than the stale threshold. That made the override
mechanism useless for its main purpose: the weekly [Catalog Audit] issue re-reported
the same owner-accepted exceptions forever and never converged. These tests pin the
corrected behaviour, including the deliberate exception for archived repos.
"""
from __future__ import annotations

import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import catalog_guardian_legacy as guardian  # noqa: E402

OVERRIDES = ROOT / "repo-lists" / "lifecycle-overrides.json"
THRESHOLDS = dict(stale=120, adopt=270, remove=365, archive_grace=180)


def meta(age_days: int, archived: bool = False) -> dict:
    """Minimal repo metadata shaped like the GitHub API response Guardian consumes."""
    pushed = guardian.now() - guardian.dt.timedelta(days=age_days)
    return {
        "pushed_at": pushed.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "archived": archived,
        "disabled": False,
        "license": {"key": "mit"},
    }


def classify(age_days: int, archived: bool = False, override: dict | None = None):
    return guardian.classify("owner/repo", meta(age_days, archived), {}, override or {}, **THRESHOLDS)


class LifecycleOverrideTests(unittest.TestCase):
    def test_reference_override_holds_healthy_however_old(self):
        for age in (150, 400, 900):
            with self.subTest(age=age):
                self.assertEqual("HEALTHY", classify(age, override={"mode": "reference"}).status)

    def test_keep_override_holds_healthy(self):
        self.assertEqual("HEALTHY", classify(500, override={"mode": "keep"}).status)

    def test_archived_still_escalates_under_an_override(self):
        """Archival is a new fact the owner has not ruled on. It must not be silenced."""
        self.assertEqual("REVIEW", classify(30, archived=True, override={"mode": "reference"}).status)

    def test_archived_active_always_reviews(self):
        """This mode exists to keep nagging through a sunset."""
        for age, archived in ((5, True), (5, False), (400, True)):
            with self.subTest(age=age, archived=archived):
                self.assertEqual("REVIEW", classify(age, archived, {"mode": "archived-active"}).status)

    def test_override_note_is_preserved(self):
        note = "finished research artifact; age is the wrong metric"
        self.assertEqual(note, classify(400, override={"mode": "reference", "note": note}).note)

    def test_disabled_beats_every_override(self):
        data = meta(10)
        data["disabled"] = True
        result = guardian.classify("owner/repo", data, {}, {"mode": "keep"}, **THRESHOLDS)
        self.assertEqual("REMOVE", result.status)

    def test_unoverridden_repo_still_ages_normally(self):
        self.assertEqual("HEALTHY", classify(10).status)
        self.assertEqual("STALE", classify(200).status)

    def test_committed_overrides_use_only_supported_modes(self):
        supported = {"keep", "reference", "archived-active"}
        data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
        for repo, entry in data.items():
            with self.subTest(repo=repo):
                self.assertIn(entry.get("mode"), supported)
                self.assertTrue(str(entry.get("note", "")).strip(),
                                f"{repo} override must say why age is the wrong signal")

    def test_an_acknowledged_archival_says_so_in_its_note(self):
        """acknowledged_archived silences the weekly REVIEW, so the reason has to be written down."""
        data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
        acknowledged = {repo: entry for repo, entry in data.items() if entry.get("acknowledged_archived")}
        self.assertTrue(acknowledged)
        for repo, entry in acknowledged.items():
            with self.subTest(repo=repo):
                self.assertIn("archived", entry["note"].lower())
                self.assertIn(entry["mode"], {"keep", "reference"})

    def test_notes_fit_the_audit_table(self):
        """The audit issue cut notes at 300 characters; #21 showed one mid-sentence.

        Owner-written notes are decision records and are not shortened to fit, so
        the table's limit is what has to hold every note.
        """
        import re
        workflow = (OVERRIDES.parents[1] / ".github" / "workflows" / "catalog-guardian.yml").read_text(encoding="utf-8")
        limit = int(re.search(r"note = \(r\.get\('note'\).*?\[:(\d+)\]", workflow).group(1))
        data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
        for repo, entry in data.items():
            with self.subTest(repo=repo):
                self.assertLessEqual(len(entry["note"]), limit)


if __name__ == "__main__":
    unittest.main()

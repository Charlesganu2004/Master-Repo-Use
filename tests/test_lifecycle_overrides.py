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


if __name__ == "__main__":
    unittest.main()

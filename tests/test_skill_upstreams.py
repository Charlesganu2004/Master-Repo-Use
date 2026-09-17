"""Noticing when the original behind one of our skills changes.

Offline: every test swaps the network for a fake GitHub, so the suite never
depends on api.github.com being reachable or on its rate limit.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import skill_upstreams as su  # noqa: E402


class FakeGitHub:
    """Serves repo metadata, a head commit, one file and an optional release."""

    def __init__(self, files: dict, commit="c" * 40, archived=False, missing=()):
        self.files, self.commit, self.archived, self.missing = files, commit, archived, set(missing)

    def __call__(self, url, raw=False):
        if raw:
            for path, body in self.files.items():
                if url.endswith("/" + path):
                    if path in self.missing:
                        raise su.UpstreamError(f"{url} -> HTTP 404")
                    return body
            raise su.UpstreamError(f"{url} -> HTTP 404")
        if url.endswith("/releases/latest"):
            return {"tag_name": "v1.0.0"}
        if "/commits/" in url:
            return {"sha": self.commit}
        return {"default_branch": "main", "archived": self.archived,
                "license": {"spdx_id": "MIT"}}


class TrackerTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.original = (su.MANIFEST, su.FETCH, su.TRACKED)
        su.MANIFEST = pathlib.Path(self.dir.name) / "skill-upstreams.json"
        su.TRACKED = {"master-caveman": {"upstream": "JuliusBrussee/caveman",
                                         "path": "skills/caveman/SKILL.md",
                                         "licence": "MIT", "relation": "derived"}}
        self.addCleanup(self.restore)

    def restore(self):
        su.MANIFEST, su.FETCH, su.TRACKED = self.original

    def serve(self, body: bytes, **kwargs):
        su.FETCH = FakeGitHub({"skills/caveman/SKILL.md": body}, **kwargs)


class PinningRecordsWhatWasMeasured(TrackerTest):
    def test_pin_writes_the_commit_size_and_hash(self):
        self.serve(b"caveman v1")
        su.pin(["master-caveman"], today="2026-09-11")
        reviewed = json.loads(su.MANIFEST.read_text())["skills"]["master-caveman"]["reviewed"]
        self.assertEqual(reviewed["sha256"], hashlib.sha256(b"caveman v1").hexdigest())
        self.assertEqual(reviewed["bytes"], len(b"caveman v1"))
        self.assertEqual(reviewed["commit"], "c" * 40)
        self.assertEqual(reviewed["on"], "2026-09-11")


class CheckingComparesContentNotLabels(TrackerTest):
    def test_an_unchanged_upstream_is_current(self):
        self.serve(b"caveman v1")
        su.pin(["master-caveman"])
        self.assertEqual(su.check()[0]["status"], "current")

    def test_a_changed_file_is_caught_even_with_no_new_release(self):
        """The hash is compared, not the tag, so a rewritten file or a moved tag
        is caught when the release number never changed."""
        self.serve(b"caveman v1")
        su.pin(["master-caveman"])
        self.serve(b"caveman v2, rewritten", commit="d" * 40)
        result = su.check()[0]
        self.assertEqual(result["status"], "changed")
        self.assertIn("compare", su.report([result]))

    def test_never_reviewed_is_its_own_status(self):
        self.serve(b"caveman v1")
        self.assertEqual(su.check()[0]["status"], "unpinned")

    def test_a_deleted_upstream_file_is_reported_not_swallowed(self):
        self.serve(b"caveman v1")
        su.pin(["master-caveman"])
        su.FETCH = FakeGitHub({"skills/caveman/SKILL.md": b"x"},
                              missing=["skills/caveman/SKILL.md"])
        self.assertEqual(su.check()[0]["status"], "error")

    def test_an_archived_upstream_is_flagged(self):
        self.serve(b"caveman v1")
        su.pin(["master-caveman"])
        self.serve(b"caveman v1", archived=True)
        self.assertEqual(su.check()[0]["status"], "archived")


class TheRealManifestIsMeasuredAndComplete(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "repo-lists" / "skill-upstreams.json")
                               .read_text(encoding="utf-8"))["skills"]

    def test_every_tracked_skill_is_pinned(self):
        self.assertEqual(set(self.data), set(su.TRACKED))

    def test_every_pin_carries_a_commit_and_a_real_hash(self):
        for name, entry in self.data.items():
            reviewed = entry["reviewed"]
            self.assertRegex(reviewed["commit"], r"^[0-9a-f]{40}$", name)
            self.assertRegex(reviewed["sha256"], r"^[0-9a-f]{64}$", name)
            self.assertGreater(reviewed["bytes"], 0, name)

    def test_every_tracked_skill_exists_and_names_its_upstream(self):
        for name, entry in self.data.items():
            skill = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn(entry["upstream"], skill,
                          f"{name} does not credit {entry['upstream']}")

    def test_caveman_records_the_licence_split(self):
        """Its engine-linked directories are BSL-1.1, which is not open source.
        Recording only 'MIT' would invite someone to reuse the wrong part."""
        self.assertIn("BSL-1.1", self.data["master-caveman"]["licence"])


class TheWorkflowDetectsButNeverMerges(unittest.TestCase):
    def setUp(self):
        self.workflow = (ROOT / ".github" / "workflows" / "skill-upstreams.yml").read_text(encoding="utf-8")

    def test_it_cannot_write_to_the_repository(self):
        """These skills run on every prompt. Whoever controls an upstream must
        not be able to change them on a schedule."""
        self.assertNotIn("contents: write", self.workflow)

    def test_it_can_open_the_review_issue(self):
        self.assertIn("issues: write", self.workflow)
        self.assertIn("[Skill Upstream]", self.workflow)

    def test_a_crash_fails_the_job_rather_than_opening_an_issue(self):
        self.assertIn('if [ "$status" -gt 1 ]; then exit "$status"; fi', self.workflow)

    def test_it_calls_no_model(self):
        for vendor in ("anthropic", "openai", "claude -p", "ANTHROPIC_API_KEY"):
            self.assertNotIn(vendor, self.workflow)

    def test_it_closes_the_issue_once_the_upstreams_match_again(self):
        """Nothing closed it, so a request stayed open after the work was done."""
        close = self.workflow.index("gh issue close")
        guard = self.workflow.rindex("moved == 'false'", 0, close)
        self.assertLess(guard, close, "the close step must run only when nothing moved")
        self.assertIn("--state open --search 'in:title [Skill Upstream]'", self.workflow[guard:close])


if __name__ == "__main__":
    unittest.main()

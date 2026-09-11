"""Behavioral regressions for interleaved clients, not one-file shape checks."""
from __future__ import annotations

import concurrent.futures
import json
import os
import pathlib
import subprocess
import sys
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "hooks"))
import skill_pipeline as pipeline


class GoalIsolation(unittest.TestCase):
    def setUp(self):
        self.store = self.enterContext(pipeline.isolated_store())

    def test_interleaved_sessions_resume_their_own_goals(self):
        first = "finish the atlas navigation and verify every command"
        second = "load the catalog into mongo and check every index"
        pipeline.context_for(first, "s1")
        pipeline.context_for(second, "s2")
        resumed = pipeline.context_for("continue", "s1")
        self.assertIn(first, resumed)
        self.assertNotIn(second, resumed)
        self.assertEqual(pipeline.load_goal("s2")["goal"], second)

    def test_explicit_session_goal_does_not_bind_another_session(self):
        pipeline.capture("goal: finish this private project", "s1")
        self.assertNotIn("private project", pipeline.context_for("continue", "s2"))
        self.assertIsNone(pipeline.load_goal("s2")["goal"])

    def test_explicit_global_goal_is_opt_in_and_session_clear_is_local(self):
        pipeline.set_goal("finish the shared release")
        self.assertIn("shared release", pipeline.context_for("continue", "s1"))
        pipeline.clear_goal("s1")
        self.assertNotIn("shared release", pipeline.context_for("continue", "s1"))
        self.assertIn("shared release", pipeline.context_for("continue", "s2"))
        self.assertEqual(pipeline.load_goal()["goal"], "finish the shared release")

    def test_old_captured_global_state_is_never_inherited(self):
        pipeline.save_goal({**pipeline.EMPTY, "goal": "private objective from an old session",
                            "source": "captured", "session": "old"})
        for session in (None, "new"):
            self.assertNotIn("private objective", pipeline.context_for("continue", session))

    def test_no_id_task_is_ephemeral_and_does_not_write(self):
        prompt = "finish the loader and verify its retry handling"
        context = pipeline.context_for(prompt)
        self.assertIn(prompt, context)
        self.assertIn("not saved", context)
        self.assertEqual(list(self.store.iterdir()), [])
        self.assertNotIn(prompt, pipeline.context_for("continue"))

    def test_read_only_context_does_not_capture_or_change_scoped_state(self):
        pipeline.context_for("finish the atlas and verify its navigation", "s1")
        path = pipeline.goal_path("s1")
        before = path.read_bytes()
        context = pipeline.context_for("goal clear", "s1", capturing=False)
        self.assertIn("finish the atlas", context)
        self.assertEqual(path.read_bytes(), before)
        pipeline.context_for("build a totally different project tomorrow", "s2", capturing=False)
        self.assertFalse(pipeline.goal_path("s2").exists())

    def test_full_goal_text_is_preserved_and_unicode_preview_is_bounded(self):
        original = "Build this exactly:\n    x = 'a  b'\n" + "\U0001f680" * 1000
        pipeline.set_goal(original, session="s1")
        self.assertEqual(pipeline.load_goal("s1")["goal"], original)
        excerpt = pipeline.goal_excerpt(pipeline.load_goal("s1"), "s1")
        self.assertLessEqual(len(excerpt.encode("utf-8")), 400)
        self.assertIn(str(pipeline.goal_path("s1")), excerpt)

    def test_session_ids_cannot_escape_the_runtime_directory(self):
        path = pipeline.goal_path("../../elsewhere/\u202efile")
        self.assertEqual(path.parent, self.store / "sessions")
        self.assertEqual(len(path.stem), 64)

    def test_concurrent_writers_use_distinct_temporary_files(self):
        paths = []
        original = pathlib.Path.replace
        def observe(path, target):
            paths.append(path)
            return original(path, target)
        with mock.patch.object(pathlib.Path, "replace", observe):
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(lambda n: pipeline.save_goal(
                    {**pipeline.EMPTY, "goal": f"goal {n}", "source": "explicit"}), range(30)))
        self.assertTrue(all(results))
        self.assertEqual(len(set(paths)), 30, "each save owns one temporary file, including retries")
        self.assertEqual(list(self.store.glob("*.tmp")), [])
        self.assertTrue(pipeline.load_goal()["goal"].startswith("goal "))

    def test_transient_windows_replacement_error_is_retried(self):
        original = pathlib.Path.replace
        attempts = []
        def sharing_violation(path, target):
            attempts.append(path)
            if len(attempts) <= 2:
                raise PermissionError("transient Windows sharing violation")
            return original(path, target)
        with mock.patch.object(pathlib.Path, "replace", sharing_violation):
            self.assertTrue(pipeline.save_goal({**pipeline.EMPTY, "goal": "retained objective"}))
        self.assertEqual(len(attempts), 3)
        self.assertEqual(pipeline.load_goal()["goal"], "retained objective")

    def test_persistent_write_failure_keeps_the_previous_goal(self):
        pipeline.set_goal("previous objective")
        before = pipeline.STATE_FILE.read_bytes()
        with mock.patch.object(pathlib.Path, "replace", side_effect=PermissionError("read only")):
            self.assertFalse(pipeline.save_goal({**pipeline.EMPTY, "goal": "replacement"}))
        self.assertEqual(pipeline.STATE_FILE.read_bytes(), before)
        self.assertEqual(list(self.store.glob("*.tmp")), [])

    def test_same_id_from_different_clients_does_not_collide(self):
        env = {**os.environ, "MASTER_REPO_GOAL_DIR": str(self.store)}
        def hook(prompt, flag=None):
            args = [sys.executable, str(ROOT / "scripts/hooks/skill_pipeline.py")]
            if flag:
                args.append(flag)
            result = subprocess.run(args, input=json.dumps({"prompt": prompt, "session_id": "same"}),
                                    text=True, capture_output=True, env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout
        hook("finish the claude parser and verify every token")
        hook("finish the gemini gallery and verify every route", "--gemini")
        self.assertNotIn("gemini gallery", hook("continue"))
        self.assertIn("claude parser", hook("continue"))

    def test_goal_cli_session_context_is_read_only(self):
        env = {**os.environ, "MASTER_REPO_GOAL_DIR": str(self.store)}
        args = [sys.executable, str(ROOT / "scripts/harness_goal.py"), "--session", "cli:one"]
        set_result = subprocess.run(args + ["--set", "finish the scoped CLI project"],
                                    capture_output=True, text=True, env=env)
        self.assertEqual(set_result.returncode, 0, set_result.stderr)
        before = pipeline.goal_path("cli:one").read_bytes()
        result = subprocess.run(args + ["--context", "goal clear"], capture_output=True,
                                text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("finish the scoped CLI project", result.stdout)
        self.assertEqual(pipeline.goal_path("cli:one").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()

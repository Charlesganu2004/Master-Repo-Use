import hashlib
import json
import pathlib
import tempfile
import unittest

from benchmarks.verified_2026.export import clean, export


class BenchmarkExport(unittest.TestCase):
    def test_metrics_survive_but_transcripts_and_identity_do_not(self):
        original = {"seconds": 2.31, "input_tokens": 23543, "cost_usd": None,
                    "raw": {"stdout": "private transcript", "stdout_hex": "deadbeef",
                            "stdout_bytes": 751, "exit_code": 128},
                    "path": r"C:\Users\u301268\private\file", "argv": ["private"]}
        result = clean(original)
        self.assertEqual(result["input_tokens"], 23543)
        self.assertEqual(result["seconds"], 2.31)
        self.assertIsNone(result["cost_usd"])
        self.assertEqual(result["raw"], {"stdout_bytes": 751, "exit_code": 128})
        self.assertEqual(result["argv"], ["private"])
        self.assertEqual(result["path"], r"<USER_HOME>\private\file")

    def test_export_hashes_distinguish_raw_and_sanitized_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            source, destination = root / "raw", root / "export"
            source.mkdir()
            raw = json.dumps({"path": r"C:\Users\u301268\private", "input_tokens": 99}).encode()
            (source / "coding-runs.json").write_bytes(raw)
            (source / "browser").mkdir()
            (source / "browser" / "not-evidence.dll").write_bytes(b"not evidence")
            result = export(source, destination)
            item = result["files"][0]
            self.assertEqual(item["raw_source_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertNotEqual(item["raw_source_sha256"], item["export_sha256"])
            self.assertEqual((source / "coding-runs.json").read_bytes(), raw)
            self.assertFalse((destination / "browser").exists())
            with self.assertRaises(ValueError):
                export(source, destination)

    def test_unix_and_windows_home_paths_are_redacted(self):
        self.assertEqual(clean("/mnt/c/Users/u301268/work"), "<USER_HOME>/work")
        self.assertEqual(clean("C:/Users/another/work"), "<USER_HOME>/work")

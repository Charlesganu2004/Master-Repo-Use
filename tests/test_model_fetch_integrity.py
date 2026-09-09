"""Model readiness requires byte verification, not merely a successful pull."""
import contextlib
import hashlib
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import vendor_models as vendor


class ModelIntegrity(unittest.TestCase):
    def test_refuses_unbounded_fetch(self):
        with patch.object(vendor, "have_ollama") as probe, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(vendor.fetch(None, False), 2)
            probe.assert_not_called()

    def test_verifies_actual_local_weight_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "blobs").mkdir()
            content = b"tiny test weight, not a model"
            expected = "sha256:" + hashlib.sha256(content).hexdigest()
            path = root / "blobs" / expected.replace(":", "-", 1)
            path.write_bytes(content)
            model = {"tag": "fixture:1", "digest": expected}
            result = subprocess.CompletedProcess([], 0, f'FROM "{path}"\n')
            with patch.dict(os.environ, {"OLLAMA_MODELS": str(root)}), patch.object(vendor.subprocess, "run", return_value=result):
                self.assertTrue(vendor.verify_local_weight(model))
                path.write_bytes(b"tampered")
                self.assertFalse(vendor.verify_local_weight(model))

    def test_registry_drift_prevents_pull(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "manifest.json"
            path.write_text(json.dumps({"models": [{"tag": "fixture:1", "minRamGb": 8,
                                                    "bytes": 10, "digest": "sha256:" + "a" * 64}]}))
            with patch.object(vendor, "MANIFEST", path), patch.object(vendor, "have_ollama", return_value=True), \
                    patch.object(vendor, "fetch_manifest", return_value={"layers": [{"mediaType": "model", "digest": "sha256:" + "b" * 64}]}), \
                    patch.object(vendor.subprocess, "run") as run, contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(vendor.fetch(8, False), 1)
                run.assert_not_called()

    def test_dry_run_has_no_network_or_model_calls(self):
        with patch.object(vendor, "fetch_manifest") as network, patch.object(vendor.subprocess, "run") as run, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(vendor.fetch(8, True), 0)
            network.assert_not_called()
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()

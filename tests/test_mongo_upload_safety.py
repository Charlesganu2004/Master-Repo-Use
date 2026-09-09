"""Offline upload safety. No real database or model is contacted."""
import contextlib
import hashlib
import io
import pathlib
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import load_catalog_mongo as loader
from capability_definitions import read_owned_definition


class MongoUploadSafety(unittest.TestCase):
    def test_rejects_secret_without_printing_value(self):
        value = "ghp_" + "A" * 30
        problems = loader.validate_documents({"skills": [{"_id": "demo", "body": value}]})
        self.assertTrue(problems)
        self.assertNotIn(value, " ".join(problems))

    def test_rejects_duplicate_ids(self):
        self.assertTrue(loader.validate_documents({"tools": [{"_id": "same"}, {"_id": "same"}]}))

    def test_empty_uri_never_connects(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(loader.load(None, "atlas"), 2)

    def test_bad_database_never_connects(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(loader.load("mongodb://unused", "bad;command"), 2)

    def test_connection_error_does_not_echo_driver_secret(self):
        secret = "mongodb+srv://username:sensitive-password@private-cluster/"
        fake = types.SimpleNamespace(MongoClient=lambda *a, **k: (_ for _ in ()).throw(ValueError(secret)), ReplaceOne=object)
        out = io.StringIO()
        with patch.dict(sys.modules, {"pymongo": fake}), patch.object(loader, "payload", return_value={}), \
                patch.object(loader, "mongo_documents", return_value={}), contextlib.redirect_stderr(out):
            self.assertEqual(loader.load(secret, "atlas"), 1)
        self.assertNotIn("sensitive-password", out.getvalue())
        self.assertNotIn("private-cluster", out.getvalue())

    def test_owned_definition_preserves_bytes_and_path_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = pathlib.Path(directory)
            (repo / "agents").mkdir()
            raw = b"\xef\xbb\xbf# Example\r\nContract intact.\r\n"
            (repo / "agents" / "role.md").write_bytes(raw)
            definition = read_owned_definition(repo, "agents/role.md")
            self.assertEqual(definition["body"].encode("utf-8"), raw)
            self.assertEqual(definition["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertIsNone(read_owned_definition(repo, "../outside.md"))

    def test_partial_index_uses_supported_equality(self):
        index = next(i for i in loader.parse_indexes() if i["name"] == "lane_source")
        self.assertEqual(index["partial"].group(1), "isFileSource")
        self.assertEqual(index["partial"].group(2), "true")


if __name__ == "__main__":
    unittest.main()

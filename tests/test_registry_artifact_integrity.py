"""The downloadable proposal must match its recorded artifact digests."""
import hashlib
import json
from pathlib import Path
import unittest


class RegistryArtifactIntegrity(unittest.TestCase):
    def test_published_document_sources_match_provenance(self):
        root = Path(__file__).resolve().parents[1] / "docs" / "registry-plan-2026-09-14"
        provenance = json.loads((root / "registry-architecture.provenance.json").read_text())
        self.assertEqual(provenance["status"], "proposal-not-deployed")
        for kind in ("markdown", "diagram", "pdf"):
            with self.subTest(artifact=kind):
                actual = hashlib.sha256((root / provenance[kind]).read_bytes()).hexdigest()
                self.assertEqual(actual, provenance[kind + "_sha256"])


if __name__ == "__main__":
    unittest.main()

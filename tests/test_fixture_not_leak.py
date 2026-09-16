"""A fake secret in a test fixture is not a leaked credential.

Third time this class of false positive has tried to delete healthy repositories.

  1. Prose. Documentation about attacks read as attacks, and the audit proposed
     removing anthropics/skills (171k stars) and wshobson/agents.
  2. Now fixtures. ollama/ollama drew twenty CRITICALs entirely from
     convert/testdata/*.json, which are model tokenizer files whose long base64
     runs gitleaks reports as generic-api-key. lobehub/lobe-chat drew its
     CRITICALs from .test.ts files and __tests__ directories.

CRITICAL is not a label, it is an instruction: it sets status REMOVE, and with
--apply-removals that deletes the entry. Deleting the runtime the whole
local-model lane is built on, over a tokenizer file, is a far worse outcome than
the finding it reacts to.

These findings still report at HIGH. Worth a human look, never worth a removal.
"""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import catalog_guardian_legacy as guardian  # noqa: E402
import catalog_security as security  # noqa: E402


class FixturePathsAreRecognised(unittest.TestCase):
    REAL_CASES = [
        "convert/testdata/gemma-2b-it.json",          # ollama, the actual false positive
        "convert/testdata/Qwen2.5-0.5B-Instruct.json",
        "src/features/SettingsSearch/analytics.test.ts",   # lobe-chat
        "apps/server/src/routers/lambda/__tests__/integration/aiAgent/execAgent.integration.test.ts",
        ".agents/acceptance/scripts/setup-auth.test.sh",
        "tests/expt_results/deep_research_bench_gpt-5.jsonl",  # open_deep_research
        ".github/secret_scanning.yml",                # graphiti: a config about secrets
        "docs/CLI.md",                                # Depth-Anything-3: a doc example
        ".env.example",
        "spec/fixtures/creds.json",
    ]

    NOT_FIXTURES = [
        "src/config/production.json",
        "deploy/credentials.json",
        "app/settings.py",
        "lib/auth.go",
        "terraform/main.tf",
    ]

    def test_every_real_false_positive_is_recognised(self):
        for path in self.REAL_CASES:
            for module in (guardian, security):
                self.assertTrue(module.is_fixture_path(path),
                                f"{module.__name__} does not treat {path} as a fixture")

    def test_real_source_paths_are_not_exempted(self):
        """The exemption must not swallow a genuine leak in shipping code."""
        for path in self.NOT_FIXTURES:
            for module in (guardian, security):
                self.assertFalse(module.is_fixture_path(path),
                                 f"{module.__name__} wrongly exempts {path}")

    def test_the_two_modules_agree(self):
        for path in self.REAL_CASES + self.NOT_FIXTURES:
            self.assertEqual(guardian.is_fixture_path(path), security.is_fixture_path(path),
                             f"the scanners disagree about {path}")


class OnlyExternalScannersRaiseCritical(unittest.TestCase):
    """CRITICAL sets REMOVE, so a heuristic must never be able to reach it."""

    def test_builtin_secret_heuristic_caps_at_high(self):
        source = (ROOT / "scripts" / "catalog_guardian_legacy.py").read_text(encoding="utf-8")
        self.assertIn('out.append(f"HIGH secret/private-key material in {path}")', source)
        self.assertNotIn('out.append(f"CRITICAL secret/private-key material', source)

    def test_credential_exfil_heuristic_caps_at_high(self):
        """It once fired on documentation telling people not to log their key."""
        for name in ("catalog_guardian_legacy.py", "catalog_security.py"):
            source = (ROOT / "scripts" / name).read_text(encoding="utf-8")
            self.assertNotIn("'CRITICAL' if name == 'credential-exfil'", source, name)

    def test_gitleaks_in_a_fixture_path_is_capped(self):
        for name in ("catalog_guardian_legacy.py", "catalog_security.py"):
            source = (ROOT / "scripts" / name).read_text(encoding="utf-8")
            self.assertIn("fixture path, capped below CRITICAL", source, name)

    def test_gitleaks_outside_a_fixture_path_still_raises_critical(self):
        """The exemption is narrow; a real leak in shipping code must still bite."""
        for name in ("catalog_guardian_legacy.py", "catalog_security.py"):
            source = (ROOT / "scripts" / name).read_text(encoding="utf-8")
            self.assertIn('f"CRITICAL gitleaks secret candidate', source, name)

    def test_removal_still_requires_a_named_external_scanner(self):
        """And a gitleaks line in a fixture path does not count, even one cached before the cap."""
        import catalog_guardian as entry
        self.assertFalse(entry.substantiates_critical(
            "CRITICAL gitleaks secret candidate rule=generic-api-key "
            "at convert/testdata/gemma-2b-it.json:3 (value withheld)"))
        self.assertTrue(entry.substantiates_critical(
            "CRITICAL gitleaks secret candidate rule=generic-api-key at cmd/serve.go:88 (value withheld)"))


class TheSeverityContractIsDocumented(unittest.TestCase):
    def test_the_fixture_rule_explains_why_it_exists(self):
        source = (ROOT / "scripts" / "catalog_guardian_legacy.py").read_text(encoding="utf-8")
        # Whitespace-normalised: the comment is hard-wrapped and a sentence that
        # crossed a line break is still the same sentence.
        flat = " ".join(source.replace("#", " ").split())
        self.assertIn("testdata", flat)
        self.assertIn("is not a leaked credential", flat)


if __name__ == "__main__":
    unittest.main()

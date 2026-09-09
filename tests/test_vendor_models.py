"""The repository states which models and which versions, without holding weights.

Charles asked for the local models to live in the repository so nobody has to go
to Hugging Face. The weights cannot: measured on 2026-09-09, the smallest is
274 MB against GitHub's hard 100 MB file limit, and the set totals 227 GB against
a 5 GB repository cap.

So the repository holds the manifest, the Modelfiles and the commands, and these
tests hold the two things that would quietly stop being true: that the pinned
data matches the catalog, and that the documented sizes match the pinned data.
"""
import json
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import vendor_models as vendor  # noqa: E402

MANIFEST = json.loads((ROOT / "docs" / "model-manifest.json").read_text(encoding="utf-8"))
DOC = (ROOT / "docs" / "MODELS.md").read_text(encoding="utf-8")
BY_TAG = {m["tag"]: m for m in MANIFEST["models"]}


class TheManifestMatchesTheCatalog(unittest.TestCase):
    def test_every_catalogued_tag_is_pinned(self):
        catalogued = {m["tag"] for m in vendor.profiles()}
        self.assertEqual(catalogued, set(BY_TAG),
                         "the manifest and the hardware profiles disagree")

    def test_every_model_has_a_real_digest(self):
        for tag, model in BY_TAG.items():
            self.assertTrue(model["digest"].startswith("sha256:"), tag)
            self.assertGreater(len(model["digest"]), 20, tag)

    def test_every_model_has_a_real_size(self):
        for tag, model in BY_TAG.items():
            self.assertGreater(model["bytes"], 1_000_000, f"{tag} size looks wrong")


class WhyTheWeightsAreNotHere(unittest.TestCase):
    """The refusal rests on numbers, so the numbers are asserted."""

    def test_not_one_model_fits_gits_file_limit(self):
        over = [t for t, m in BY_TAG.items() if m["bytes"] <= vendor.GIT_FILE_LIMIT]
        self.assertFalse(over, f"these are claimed to fit git: {over}")

    def test_the_smallest_is_still_over_the_limit(self):
        smallest = min(BY_TAG.values(), key=lambda m: m["bytes"])
        self.assertGreater(smallest["bytes"], vendor.GIT_FILE_LIMIT)

    def test_the_set_is_far_past_the_repository_cap(self):
        total = sum(m["bytes"] for m in BY_TAG.values())
        self.assertGreater(total, vendor.REPO_SOFT_LIMIT * 10,
                           "if this ever fits, revisit the decision")

    def test_the_doc_states_the_limits_it_relies_on(self):
        for needle in ("100 MB", "5 GB", "2 GiB", "227 GB"):
            self.assertIn(needle, DOC, f"{needle} is not stated in MODELS.md")


class TheDocDoesNotDriftFromTheManifest(unittest.TestCase):
    """A hand-typed table is a second copy, and the first draft already had one
    number wrong: phi4-mini-reasoning was written 3.21 GB against 3.15 GB."""

    ROW = re.compile(r"^\| (`?)([\w.:\-]+)\1 \| ([\d.]+) GB \| (\d+) GB \|", re.M)

    def test_every_model_appears_in_the_table(self):
        listed = {tag for _, tag, _, _ in self.ROW.findall(DOC)}
        self.assertEqual(listed, set(BY_TAG))

    def test_every_size_matches_the_manifest(self):
        for _, tag, size, _ in self.ROW.findall(DOC):
            self.assertAlmostEqual(float(size), BY_TAG[tag]["bytes"] / 1e9, places=2,
                                   msg=f"{tag} size differs from the manifest")

    def test_every_memory_floor_matches(self):
        for _, tag, _, ram in self.ROW.findall(DOC):
            self.assertEqual(int(ram), BY_TAG[tag]["minRamGb"], tag)


class RedistributionIsGatedOnLicenceNotSize(unittest.TestCase):
    def test_only_permissive_licences_are_offered(self):
        for tag, model in BY_TAG.items():
            if model["redistribution"] != "redistributable":
                continue
            self.assertIn(model["license"].lower(), vendor.REDISTRIBUTABLE, tag)

    def test_conditional_licences_carry_the_reason(self):
        conditional = [m for m in BY_TAG.values() if m["redistribution"] == "conditional"]
        self.assertTrue(conditional, "gemma and llama should be conditional")
        for model in conditional:
            self.assertGreater(len(model["redistributionNote"]), 40, model["tag"])

    def test_gemma_and_llama_are_never_marked_redistributable(self):
        """Both permit redistribution only with conditions a file copy cannot
        meet, so neither is staged on Charles's behalf."""
        for tag, model in BY_TAG.items():
            licence = model["license"].lower()
            if "gemma" in licence or "llama" in licence:
                self.assertNotEqual(model["redistribution"], "redistributable", tag)

    def test_a_release_candidate_is_both_clean_and_small(self):
        for model in BY_TAG.values():
            if model["redistribution"] == "redistributable" and model["fitsReleaseAsset"]:
                self.assertLessEqual(model["bytes"], vendor.RELEASE_ASSET_LIMIT,
                                     model["tag"])


class TheModelfilesAreCommitted(unittest.TestCase):
    def test_one_per_pinned_model(self):
        files = sorted((ROOT / "models").glob("*.Modelfile"))
        self.assertEqual(len(files), len(BY_TAG))

    def test_each_names_its_tag_and_pins_its_digest(self):
        for tag, model in BY_TAG.items():
            path = ROOT / "models" / (tag.replace(":", "-").replace("/", "-") + ".Modelfile")
            self.assertTrue(path.is_file(), f"no Modelfile for {tag}")
            body = path.read_text(encoding="utf-8")
            self.assertIn(f"FROM {tag}", body)
            self.assertIn(model["digest"], body, f"{tag} digest is not pinned")


class TheCheckRunsOffline(unittest.TestCase):
    def test_it_passes_and_contacts_nothing(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "vendor_models.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("all agree", result.stdout)

    def test_no_em_or_en_dashes(self):
        for path in ("scripts/vendor_models.py", "docs/MODELS.md"):
            body = (ROOT / path).read_text(encoding="utf-8")
            self.assertNotIn("\u2014", body, path)
            self.assertNotIn("\u2013", body, path)


if __name__ == "__main__":
    unittest.main()


class TheProseMatchesTheMeasurement(unittest.TestCase):
    """Every number written in prose is checked against the manifest.

    A parallel edit on 2026-09-09 introduced four wrong figures into the module
    docstring at once: the smallest model named as gemma3:270m at 290 MB when it
    is nomic-embed-text at 274 MB, the multiple as 2.9x when it is 2.6x, the LFS
    clone as 202 GB when it is 227 GB, and the release-asset count as 19 of 35
    when it is 9. Prose that restates a measurement is a second copy, and a
    second copy drifts. This is the check that makes it stop being silent.
    """

    def setUp(self):
        self.body = (ROOT / "scripts" / "vendor_models.py").read_text(encoding="utf-8")
        self.models = MANIFEST["models"]

    def test_the_smallest_model_is_named_correctly(self):
        smallest = min(self.models, key=lambda m: m["bytes"])
        self.assertIn(smallest["tag"], self.body,
                      "the docstring names the wrong smallest model")
        megabytes = round(smallest["bytes"] / 1e6)
        self.assertIn(f"{megabytes} MB", self.body,
                      f"the docstring does not say {megabytes} MB")

    def test_the_multiple_over_the_git_limit_is_right(self):
        smallest = min(self.models, key=lambda m: m["bytes"])
        multiple = smallest["bytes"] / vendor.GIT_FILE_LIMIT
        self.assertIn(f"{multiple:.1f}x", self.body,
                      f"the docstring should say {multiple:.1f}x the git limit")

    def test_the_total_is_right_everywhere_it_appears(self):
        total = round(sum(m["bytes"] for m in self.models) / 1e9)
        self.assertIn(f"{total} GB", self.body)
        for wrong in ("202 GB", "200 GB"):
            self.assertNotIn(wrong, self.body, f"stale total {wrong} is still written")

    def test_the_release_asset_count_is_right(self):
        fits = sum(1 for m in self.models if m["fitsReleaseAsset"])
        self.assertIn(f"{fits} of the 35", self.body,
                      f"the docstring should say {fits} of the 35 fit a release asset")

    def test_the_doc_and_the_module_agree_on_the_smallest(self):
        smallest = min(self.models, key=lambda m: m["bytes"])
        self.assertIn(f"{round(smallest['bytes']/1e6)} MB", DOC,
                      "MODELS.md and the module disagree on the smallest model")

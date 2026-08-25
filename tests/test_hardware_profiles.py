#!/usr/bin/env python3
"""Keep docs/hardware-profiles.json honest.

The command center tells people what will run on their machine. If the declared
`min_ram_gb` for a model drifts away from what the published formula actually
computes, the advisor confidently recommends something that swaps or OOMs. These
tests make the data prove itself against its own stated arithmetic.
"""
from __future__ import annotations

import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROFILES = ROOT / "docs" / "hardware-profiles.json"
ALLOWLIST = ROOT / "repo-lists" / "public-allowlist.txt"


def load() -> dict:
    return json.loads(PROFILES.read_text(encoding="utf-8"))


class HardwareProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = load()
        self.formula = self.data["formula"]
        self.tiers = sorted(t["ram_gb"] for t in self.data["tiers"])

    def smallest_tier_that_fits(self, need_gb: float) -> int | None:
        return next((t for t in self.tiers if t >= need_gb), None)

    def test_every_model_min_ram_matches_the_published_formula(self):
        bpp = self.formula["bytes_per_param"]
        overhead = self.formula["runtime_overhead_gb"] + self.formula["kv_cache_gb_per_4k_ctx"]
        reserve = self.formula["os_reserve_gb"]["windows"]
        for model in self.data["models"]:
            if model.get("why_special"):
                # Documented exception: the generic q4 term does not describe it.
                continue
            with self.subTest(model=model["id"]):
                weights = model["params_b"] * bpp[model["quant"]]
                expected = self.smallest_tier_that_fits(weights + overhead + reserve)
                self.assertEqual(
                    expected, model["min_ram_gb"],
                    f"{model['id']} declares {model['min_ram_gb']} GB but the formula needs "
                    f"{weights + overhead + reserve:.2f} GB (tier {expected})",
                )

    def test_special_cased_models_explain_themselves(self):
        for model in self.data["models"]:
            if model["min_ram_gb"] and model.get("why_special"):
                self.assertTrue(model["why_special"].strip(), f"{model['id']} needs a reason")

    def test_tier_usable_memory_matches_the_reserve(self):
        reserve = self.formula["os_reserve_gb"]["windows"]
        for tier in self.data["tiers"]:
            with self.subTest(tier=tier["ram_gb"]):
                self.assertAlmostEqual(tier["ram_gb"] - reserve, tier["usable_gb"], places=1)

    def test_lowest_tier_recommends_no_local_chat_model(self):
        """4 GB on Windows genuinely cannot host a chat model. Say so, don't fudge it."""
        lowest = min(self.tiers)
        fits = [m for m in self.data["models"] if m["min_ram_gb"] <= lowest]
        self.assertEqual([], fits, "the 4 GB tier must not claim a local model fits")

    def test_every_referenced_repo_is_catalogued_and_public(self):
        catalogued: set[str] = set()
        for listing in (ROOT / "repo-lists").glob("*.txt"):
            for line in listing.read_text(encoding="utf-8").splitlines():
                slug = line.split("#", 1)[0].strip()
                if slug.count("/") == 1 and slug:
                    catalogued.add(slug)
        allowed = {
            line.split("#", 1)[0].strip()
            for line in ALLOWLIST.read_text(encoding="utf-8").splitlines()
            if line.split("#", 1)[0].strip().count("/") == 1
        }
        for repo in self.data["repos"]:
            with self.subTest(repo=repo["slug"]):
                self.assertIn(repo["slug"], catalogued, "advisor names an uncatalogued repo")
                self.assertIn(repo["slug"], allowed, "advisor repo must be public-allowlisted")

    def test_vendor_scope_is_microsoft_google_ollama_only(self):
        allowed_vendors = {"Microsoft", "Google", "Ollama"}
        for entry in self.data["models"] + self.data["repos"]:
            with self.subTest(entry=entry.get("id") or entry.get("slug")):
                self.assertIn(entry["vendor"], allowed_vendors)


if __name__ == "__main__":
    unittest.main()

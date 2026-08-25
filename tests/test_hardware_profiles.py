#!/usr/bin/env python3
"""Keep docs/hardware-profiles.json honest.

The command center tells people what will run on their machine. If a declared
`min_ram_gb` drifts from what the published formula actually computes, the advisor
confidently recommends something that swaps or OOMs. These tests make the data prove
itself against its own arithmetic, and pin the coverage promise: every RAM tier from
4 GB up offers real choices from each of the three vendors in scope.
"""
from __future__ import annotations

import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROFILES = ROOT / "docs" / "hardware-profiles.json"
ALLOWLIST = ROOT / "repo-lists" / "public-allowlist.txt"
VENDORS = ("Microsoft", "Google", "Ollama")


class HardwareProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = json.loads(PROFILES.read_text(encoding="utf-8"))
        self.formula = self.data["formula"]
        self.tiers = sorted(t["ram_gb"] for t in self.data["tiers"])

    def required_gb(self, model: dict) -> float:
        f = self.formula
        per_b = (f["bytes_per_param"][model["quant"]]
                 + f["overhead_per_b_gb"] + f["kv_cache_per_b_4k_gb"])
        return model["params_b"] * per_b + f["overhead_base_gb"]

    def smallest_tier_that_fits(self, need_gb: float):
        return next((t for t in self.tiers if t >= need_gb), None)

    def test_every_model_min_ram_matches_the_published_formula(self):
        reserve = self.formula["os_reserve_gb"]["windows"]
        for model in self.data["models"]:
            if model.get("why_special"):
                continue  # documented exception; the generic term does not describe it
            with self.subTest(model=model["id"]):
                need = self.required_gb(model) + reserve
                self.assertEqual(
                    self.smallest_tier_that_fits(need), model["min_ram_gb"],
                    f"{model['id']} declares {model['min_ram_gb']} GB but needs {need:.2f} GB",
                )

    def test_special_cased_models_explain_themselves(self):
        for model in self.data["models"]:
            if model.get("why_special"):
                self.assertTrue(model["why_special"].strip(), f"{model['id']} needs a reason")

    def test_tier_usable_memory_matches_the_reserve(self):
        reserve = self.formula["os_reserve_gb"]["windows"]
        for tier in self.data["tiers"]:
            with self.subTest(tier=tier["ram_gb"]):
                self.assertAlmostEqual(tier["ram_gb"] - reserve, tier["usable_gb"], places=1)

    def test_every_tier_offers_something_from_every_vendor(self):
        """The whole point of the advisor: no RAM budget is a dead end."""
        for tier in self.data["tiers"]:
            fits = [m for m in self.data["models"] if m["min_ram_gb"] <= tier["ram_gb"]]
            for vendor in VENDORS:
                with self.subTest(tier=tier["ram_gb"], vendor=vendor):
                    self.assertTrue(
                        [m for m in fits if m["vendor"] == vendor],
                        f"{vendor} has no option at {tier['ram_gb']} GB",
                    )

    def test_mid_and_upper_tiers_offer_at_least_three_per_vendor(self):
        """From 8 GB up there is enough choice to pick on merit, not availability.

        4 and 6 GB are deliberately exempt: Microsoft publishes no sub-1B open-weight
        model, so claiming three would mean inventing them.
        """
        for tier in self.data["tiers"]:
            if tier["ram_gb"] < 8:
                continue
            fits = [m for m in self.data["models"] if m["min_ram_gb"] <= tier["ram_gb"]]
            for vendor in VENDORS:
                with self.subTest(tier=tier["ram_gb"], vendor=vendor):
                    self.assertGreaterEqual(
                        len([m for m in fits if m["vendor"] == vendor]), 3,
                        f"{vendor} offers fewer than 3 options at {tier['ram_gb']} GB",
                    )

    def test_lowest_tier_is_flagged_as_constrained(self):
        """4 GB must never look comfortable, even though a few tiny models now fit."""
        lowest = min(self.data["tiers"], key=lambda t: t["ram_gb"])
        self.assertEqual(4, lowest["ram_gb"])
        self.assertEqual("red", lowest["class"])
        fits = [m for m in self.data["models"] if m["min_ram_gb"] <= 4]
        biggest = max(m["params_b"] for m in fits if not m.get("why_special"))
        self.assertLessEqual(biggest, 1.0,
                             "nothing above 1B parameters may claim to fit in 4 GB")

    def test_tier_fit_counts_match_the_model_list(self):
        for tier in self.data["tiers"]:
            fits = [m for m in self.data["models"] if m["min_ram_gb"] <= tier["ram_gb"]]
            with self.subTest(tier=tier["ram_gb"]):
                self.assertEqual(len(fits), tier["fits_total"])
                for vendor in VENDORS:
                    self.assertEqual(
                        len([m for m in fits if m["vendor"] == vendor]),
                        tier["fits_by_vendor"][vendor],
                    )

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
        for entry in self.data["models"] + self.data["repos"]:
            with self.subTest(entry=entry.get("id") or entry.get("slug")):
                self.assertIn(entry["vendor"], VENDORS)

    def test_provenance_admits_tags_are_unverified(self):
        """Tags could not be checked from the build environment. Say so, don't imply otherwise."""
        self.assertIn("verify_model_tags", self.data["provenance"])

    def test_every_model_declares_a_licence(self):
        for model in self.data["models"]:
            with self.subTest(model=model["id"]):
                self.assertTrue(str(model.get("license", "")).strip())


if __name__ == "__main__":
    unittest.main()

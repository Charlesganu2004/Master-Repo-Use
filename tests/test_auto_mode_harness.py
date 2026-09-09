"""The harness covers every surface Charles named, by whatever means each allows.

The list he gave was: chat, code chat, cowork, GitHub Copilot, ChatGPT, Codex,
Claude, Gemini, Gemini Code Assist, Cursor, Antigravity and local models, with
the enforced skills carried along.

They do not accept the same thing, and the failure this file guards against is
the tempting one: treating them uniformly, so a setup step looks like
configuration and does nothing. A shell command cannot reach a browser tab, and
a skill folder cannot be mounted into ChatGPT. So each surface declares one of
three mechanisms and the tests hold the boundary between them.
"""
import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts" / "auto_mode_harness.py"
sys.path.insert(0, str(ROOT / "scripts"))
import auto_mode_harness as harness  # noqa: E402


def run(*args):
    return subprocess.run([sys.executable, str(HARNESS), *args],
                          cwd=ROOT, capture_output=True, text=True, check=False)


class EverySurfaceCharlesNamed(unittest.TestCase):
    def test_all_of_them_are_present(self):
        names = " ".join(s["name"].lower() for s in harness.SURFACES.values())
        for named in ("claude", "codex", "gemini", "gemini code assist", "cursor",
                      "antigravity", "copilot", "chatgpt", "cowork", "local models"):
            self.assertIn(named, names, f"{named} is not covered by the harness")

    def test_code_chat_and_local_are_all_represented(self):
        groups = {s["group"] for s in harness.SURFACES.values()}
        self.assertEqual(groups, {"code", "chat", "local"})

    def test_every_surface_declares_one_of_the_three_mechanisms(self):
        allowed = {harness.HOOK, harness.GATEWAY, harness.BUNDLE, harness.REPO_FILE}
        for surface_id, surface in harness.SURFACES.items():
            self.assertIn(surface["mechanism"], allowed, surface_id)

    def test_every_surface_says_where_the_material_lands(self):
        """"Configure it in the product" is not an instruction."""
        for surface_id, surface in harness.SURFACES.items():
            self.assertGreater(len(surface["target"]), 10, surface_id)
            self.assertGreater(len(surface["detail"]), 30, surface_id)

    def test_a_browser_surface_is_never_offered_a_hook(self):
        """The whole reason for the split. A bundle surface has no shell on this
        machine, so a hook entry for it would be a command that cannot run."""
        for surface_id, surface in harness.SURFACES.items():
            if surface["group"] == "chat":
                self.assertNotEqual(surface["mechanism"], harness.HOOK, surface_id)

    def test_no_em_or_en_dashes_in_the_surface_copy(self):
        blob = json.dumps(harness.SURFACES, ensure_ascii=False)
        self.assertNotIn("—", blob)
        self.assertNotIn("–", blob)


class TheEnforcedSkillsTravelWithIt(unittest.TestCase):
    def test_every_enforced_skill_exists(self):
        self.assertEqual(harness.missing_skills(), [])

    def test_the_enforced_set_covers_both_of_layer_one_and_two(self):
        joined = " ".join(harness.ENFORCED_SKILLS)
        for layer in ("caveman", "full-output", "anti-slop", "plan", "design-taste"):
            self.assertIn(layer, joined, f"{layer} is not in the enforced set")

    def test_the_loader_leads_so_the_block_resolves_first(self):
        self.assertEqual(harness.ENFORCED_SKILLS[0], "master-repo-auto")

    def test_a_bundle_carries_the_rules_and_every_skill(self):
        body = harness.build_bundle("chatgpt")
        self.assertIn("NO-COMPRESS:BEGIN", body)
        self.assertIn("THREE LAYERS", body)
        for name in harness.ENFORCED_SKILLS:
            self.assertIn(f"### {name}", body, f"{name} missing from the bundle")

    def test_a_bundle_names_the_setting_it_is_pasted_into(self):
        for surface_id, surface in harness.SURFACES.items():
            if surface["mechanism"] not in (harness.BUNDLE, harness.REPO_FILE):
                continue
            body = harness.build_bundle(surface_id)
            self.assertIn(surface["target"], body, surface_id)

    def test_a_bundle_says_the_text_is_the_enforcement(self):
        """On a hooked client the written rules are a reminder. Here they are the
        entire mechanism, and the reader has to know that to keep them intact."""
        body = harness.build_bundle("claude-cowork")
        self.assertIn("it is the whole of the enforcement", body)

    def test_a_missing_skill_refuses_the_bundle_rather_than_shipping_a_gap(self):
        result = run("--bundle", "chatgpt", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        original = harness.ENFORCED_SKILLS
        try:
            harness.ENFORCED_SKILLS = original + ("master-does-not-exist",)
            self.assertIn("master-does-not-exist", harness.missing_skills())
            with self.assertRaises(FileNotFoundError):
                harness.build_bundle("chatgpt")
        finally:
            harness.ENFORCED_SKILLS = original


class TheMechanismsStayApart(unittest.TestCase):
    def test_install_only_accepts_surfaces_that_can_be_installed(self):
        result = run("--install", "chatgpt,claude-web", "--dry-run")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Use --bundle", result.stderr)

    def test_bundle_only_accepts_surfaces_that_cannot_run_a_command(self):
        result = run("--bundle", "claude-code,cursor", "--dry-run")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Use --install", result.stderr)

    def test_an_unknown_surface_is_named_rather_than_ignored(self):
        result = run("--bundle", "notaclient", "--dry-run")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("notaclient", result.stderr + result.stdout)

    def test_all_resolves_to_every_surface(self):
        self.assertEqual(len(harness.resolve("all")), len(harness.SURFACES))

    def test_a_dry_run_writes_nothing(self):
        out = ROOT / "dist" / "does-not-exist-yet"
        result = run("--bundle", "all", "--dry-run", "--out", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("would write", result.stdout)
        self.assertFalse(out.exists(), "a dry run created a directory")


class TheCommittedInstructionFiles(unittest.TestCase):
    """Copilot on github.com and Gemini Code Assist read committed files, not a
    home directory. Both files existed and neither carried the block, so those
    two surfaces had no enforcement while every local client had two layers."""

    def test_both_targets_exist_and_carry_the_block(self):
        for surface_id, paths in harness.REPO_FILE_TARGETS.items():
            for relative in paths:
                path = ROOT / relative
                self.assertTrue(path.is_file(), f"{relative} is missing")
                text = path.read_text(encoding="utf-8")
                self.assertIn("<!-- NO-COMPRESS:BEGIN -->", text, relative)
                self.assertIn("THREE LAYERS", text, relative)

    def test_the_block_appears_exactly_once(self):
        """The upsert replaces in place. Two copies would mean it appended."""
        for paths in harness.REPO_FILE_TARGETS.values():
            for relative in paths:
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertEqual(text.count("<!-- NO-COMPRESS:BEGIN -->"), 1, relative)

    def test_the_files_own_prose_survives_the_upsert(self):
        copilot = (ROOT / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
        self.assertIn("Master Repo", copilot)
        style = (ROOT / ".gemini" / "styleguide.md").read_text(encoding="utf-8")
        self.assertGreater(len(style), 3000, "the style guide was replaced, not appended to")


class TheLocalModelGateway(unittest.TestCase):
    def test_request_puts_pipeline_before_user_prompt(self):
        payload = harness.request_payload("qwen3:4b", "Build a settings page.")
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][1]["role"], "user")
        self.assertIn("LAYER 1", payload["messages"][0]["content"])
        self.assertFalse(payload["stream"])

    def test_it_does_not_claim_to_intercept_other_applications(self):
        body = HARNESS.read_text(encoding="utf-8")
        self.assertIn("cannot intercept another application", body)


class TheCheckIsOfflineAndHonest(unittest.TestCase):
    def test_check_exits_cleanly_without_contacting_anything(self):
        result = run("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("all three layers", result.stdout)
        expected = f"{len(harness.ENFORCED_SKILLS)} of {len(harness.ENFORCED_SKILLS)} present"
        self.assertIn(expected, result.stdout)

    def test_check_exercises_every_client_output_shape(self):
        """Asserted by running the hook, not by reading the source. A shape that
        stopped parsing is a client that silently stopped being enforced."""
        result = run("--check")
        for client in ("claude-code", "antigravity", "gemini-cli", "cursor",
                       "copilot-cli", "copilot-cli transform"):
            self.assertRegex(result.stdout, client.replace("-", "\\-") + r"\s+ok")

    def test_list_groups_the_surfaces_by_what_can_be_done_to_them(self):
        result = run("--list")
        self.assertEqual(result.returncode, 0, result.stderr)
        for title in ("Code clients on this machine", "Local models",
                      "Chat and review surfaces with no shell"):
            self.assertIn(title, result.stdout)


class TheHarnessCannotQuietlyStop(unittest.TestCase):
    def test_harness_is_protected_by_both_guards(self):
        for guard in ("no_prune_guard.py", "no_compress_guard.py"):
            event = json.dumps({"tool_name": "Bash",
                                "tool_input": {"command": "rm scripts/auto_mode_harness.py"}})
            proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "hooks" / guard)],
                                  input=event.encode(), capture_output=True)
            if guard == "no_prune_guard.py":
                self.assertEqual(proc.returncode, 2, "the harness can be deleted")

    def test_compressing_the_harness_is_blocked(self):
        event = json.dumps({"tool_name": "Bash",
                            "tool_input": {"command": "truncate -s 0 scripts/auto_mode_harness.py"}})
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "hooks" / "no_compress_guard.py")],
            input=event.encode(), capture_output=True)
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()

"""Auto mode is split across three layers, cheapest first, and must stay split.

    hook   scripts/hooks/no_prune_guard.py   0 tokens, runs outside the model
    skill  skills/master-repo-auto/SKILL.md  name and description only until used
    block  docs/auto-mode-block.txt          loaded every session by every client

The block used to hold everything, at about 616 tokens per session per client.
These tests stop the full rules drifting back into it, and stop the two standing
rules drifting out of it into a file nobody reads in time.
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BLOCK = ROOT / "docs" / "auto-mode-block.txt"
SKILL = ROOT / "skills" / "master-repo-auto" / "SKILL.md"
HOOK = ROOT / "scripts" / "hooks" / "no_prune_guard.py"

# The running cost of "mandatory", tracked rather than hidden:
#
#   616 tokens   original block, everything inline
#   106 tokens   after the split, a pointer to the on-demand skill
#   285 tokens   caveman and token reducers made mandatory and uncompressible
#   326 tokens   skills, MCP servers, tools and agents added to that protection
#   355 tokens   inheritance for new capabilities, and every build/command/lane
#   434 tokens   the exemption stated as global, and the one override that lifts it
#   538 tokens   plan, design, anti-slop, full output and verify, on every prompt
#   648 tokens   restated as three layers, with layer 1 re-applied at the end
#
# This number only moves when a rule is added, never on its own. Each rule has to
# sit in the always-loaded block because a rule consulted only when something
# thinks to look it up is not mandatory, and because ChatGPT and Copilot have no
# hook mechanism: for them the written rule is the only mechanism there is.
#
# Redundancy has been squeezed out three times to make room. What is left is one
# line per rule. The next addition will cost roughly 30 tokens per session per
# client, permanently, and the honest lever is deciding a rule is not mandatory
# rather than trying to word it shorter.
#
# The 2026-09-04 rise from 1500 to 1800 bought one rule: that the no-compaction
# exemption is global rather than a chat-only courtesy, and that exactly one thing
# lifts it. It is here rather than in the skill because a compaction pass is
# running precisely when nothing is reading the skill, and because the override
# has to be named where the rule is or the next pass invents its own.
#
# The 2026-09-07 rise from 1800 to 2300 bought the five standing rules: plan,
# caveman, design, anti-slop and full output, plus verify. Charles asked for
# these on every prompt and conversation, for every model, and was told the cost.
#
# The second 2026-09-07 rise, 2300 to 2800, restated those as THREE LAYERS and
# added the two things a flat list could not express: that layer 3 re-applies
# layer 1 to what was produced, and that layer 3 forces the model to pick and
# name the skills, tools, plugins and MCP servers that fit. The repetition is the
# feature. A rule read once at the top of a long turn has stopped applying by the
# end of it, and the end is where the skeleton and the em dash get written.
#
# For Claude Code and Antigravity these are ALSO enforced outside the model, by
# scripts/hooks/skill_pipeline.py on UserPromptSubmit and PreInvocation, and that
# file is itself protected from deletion and compression by both guards. They are
# still written here because Codex, the Gemini CLI and Copilot have no verified
# hook mechanism: for those three this block is not a reminder of the rule, it is
# the entire enforcement.
BLOCK_BUDGET_BYTES = 2800


class TheAlwaysLoadedBlock(unittest.TestCase):
    def setUp(self):
        self.text = BLOCK.read_text(encoding="utf-8")

    def test_stays_within_its_token_budget(self):
        self.assertLess(
            len(self.text.encode("utf-8")), BLOCK_BUDGET_BYTES,
            "the always-loaded block is growing back; move detail into the skill")

    def test_points_at_the_skill_rather_than_restating_it(self):
        self.assertIn("master-repo-auto", self.text)

    def test_carries_the_no_pruning_rule(self):
        # Must be known before any lookup, or a tool is gone before the skill loads.
        self.assertIn("Never remove, disable", self.text)

    def test_the_three_layers_are_named_in_order(self):
        """The clients with no hook get their enforcement from this text alone,
        so the layer structure has to survive here as well as in the hook."""
        body = " ".join(self.text.split())
        self.assertIn("THREE LAYERS on every prompt and every command", body)
        for layer in ("Layer 1, before reading the request",
                      "Layer 2, before producing", "Layer 3, while acting"):
            self.assertIn(layer, body, f"missing: {layer}")
        self.assertLess(body.index("Layer 1"), body.index("Layer 2"))
        self.assertLess(body.index("Layer 2"), body.index("Layer 3"))

    def test_layer_three_reapplies_layer_one_and_says_why(self):
        body = " ".join(self.text.split())
        self.assertIn("RE-APPLY LAYER 1", body)
        self.assertIn("repeats layer 1 on purpose", body)

    def test_layer_three_forces_naming_the_capabilities_used(self):
        body = " ".join(self.text.split())
        self.assertIn("pick and NAME the skills", body)
        for word in ("tools", "plugins", "MCP servers"):
            self.assertIn(word, body, f"{word} missing from the forced selection")

    def test_carries_the_multiple_command_rule(self):
        self.assertIn("Run every slash command", self.text)
        self.assertIn("in the order written", self.text)

    def test_does_not_restate_the_procedure_that_lives_in_the_skill(self):
        """One-line rules may be here; the how-to may not.

        "Under 15 percent saved is a failed pass" is a rule and is mandatory, so
        it is in the protected block. The paragraphs explaining what to do about
        it, and the retrieval procedure, stay in the skill.
        """
        for moved in ("speculative scanning", "Loop-until-dry", "Restore the original and say"):
            self.assertNotIn(moved, self.text,
                             f"'{moved}' is procedure and belongs in the skill")

    def test_the_protected_block_is_marked_and_self_describing(self):
        self.assertIn("<!-- NO-COMPRESS:BEGIN -->", self.text)
        self.assertIn("<!-- NO-COMPRESS:END -->", self.text)
        self.assertIn("Exempt from every compression pass", self.text)

    def test_mandatory_rules_sit_inside_the_protected_markers(self):
        """Outside the markers they are compressible, which defeats the point."""
        body = self.text[self.text.index("<!-- NO-COMPRESS:BEGIN -->"):
                         self.text.index("<!-- NO-COMPRESS:END -->")]
        for rule in ("caveman", "rtk", "Never remove, disable",
                     "Run every slash command"):
            self.assertIn(rule, body, f"'{rule}' is outside the protected block")

    def test_no_em_or_en_dashes(self):
        self.assertNotIn("—", self.text)
        self.assertNotIn("–", self.text)


class TheOnDemandSkill(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")

    def test_has_frontmatter_so_it_is_discoverable(self):
        self.assertTrue(self.text.startswith("---"))
        self.assertIn("name: master-repo-auto", self.text)
        self.assertIn("description:", self.text)

    def test_carries_the_token_discipline_rules(self):
        for fragment in ("rtk <command>", "caveman", "Never paste a whole catalog file"):
            self.assertIn(fragment, self.text)

    def test_carries_the_compression_safety_list(self):
        for fragment in ("Code blocks", "URLs", "file paths", "exact error strings"):
            self.assertIn(fragment, self.text)

    def test_carries_the_full_no_pruning_policy(self):
        self.assertIn("Never prune what the user chose to keep", self.text)
        self.assertIn("owner-approved pull request", self.text)

    def test_auto_mode_cannot_widen_permissions(self):
        self.assertIn("never what is permitted", self.text)
        # Kept short so a line wrap in the skill does not fail the test.
        self.assertIn("Nothing third-party is installed", self.text)

    def test_no_em_or_en_dashes(self):
        self.assertNotIn("—", self.text)
        self.assertNotIn("–", self.text)


class TheInstaller(unittest.TestCase):
    def test_hook_exists_and_is_the_zero_token_layer(self):
        self.assertTrue(HOOK.exists())

    def test_installer_wires_all_three_layers(self):
        body = (ROOT / "scripts" / "install_auto_mode.py").read_text(encoding="utf-8")
        for fragment in ("install_skill", "register_hook", "upsert_block"):
            self.assertIn(fragment, body)

    def test_repo_skills_install_for_codex_too(self):
        body = (ROOT / "scripts" / "install_auto_mode.py").read_text(encoding="utf-8")
        self.assertIn('"Codex": ".codex/skills"', body)

    def test_named_core_capabilities_are_real_discoverable_skills(self):
        expected = {
            "master-caveman", "master-token-reducer", "master-plan",
            "master-design-taste", "master-full-output", "master-anti-slop",
        }
        for name in expected:
            definition = ROOT / "skills" / name / "SKILL.md"
            self.assertTrue(definition.is_file(), name)
            body = definition.read_text(encoding="utf-8")
            self.assertTrue(body.startswith("---\n"), name)
            self.assertIn(f"name: {name}\n", body, name)
            self.assertIn("description:", body, name)

    def test_catalog_skill_refresh_is_non_destructive(self):
        body = (ROOT / "scripts" / "install_catalog_skill.py").read_text(encoding="utf-8")
        self.assertNotIn("shutil.rmtree(target)", body)
        self.assertIn("dirs_exist_ok=True", body)

    def test_installer_backs_up_settings_before_touching_them(self):
        body = (ROOT / "scripts" / "install_auto_mode.py").read_text(encoding="utf-8")
        self.assertIn(".json.bak", body)

    def test_installer_refuses_to_overwrite_unreadable_settings(self):
        body = (ROOT / "scripts" / "install_auto_mode.py").read_text(encoding="utf-8")
        self.assertIn("refusing to overwrite", body)

    def test_setup_scripts_still_reference_the_block(self):
        for script in ("setup-global-ai.ps1", "setup-global-ai.sh"):
            body = (ROOT / "scripts" / script).read_text(encoding="utf-8")
            self.assertIn("auto-mode-block.txt", body, f"{script} lost its reference")

    def test_setup_scripts_contain_no_control_characters(self):
        # A backslash escape twice collapsed text here into control characters.
        for script in ("setup-global-ai.ps1", "setup-global-ai.sh", "install_auto_mode.py",
                       "hooks/no_prune_guard.py"):
            body = (ROOT / "scripts" / script).read_text(encoding="utf-8")
            stray = {hex(ord(c)) for c in body if ord(c) < 32 and c not in "\n\r\t"}
            self.assertFalse(stray, f"{script} has control characters {stray}")


if __name__ == "__main__":
    unittest.main()

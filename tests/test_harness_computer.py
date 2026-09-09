"""Computer control is routed from evidence, never invented from a skill name."""
import ast
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "hooks"))

import auto_mode_harness as surface  # noqa: E402
import harness_computer as computer  # noqa: E402
import harness_goal as goal  # noqa: E402
import harness_proxy as proxy  # noqa: E402
import harness_wrap as wrap  # noqa: E402


class PrimarySourcesArePinned(unittest.TestCase):
    def setUp(self):
        self.data = computer.load_capabilities()

    def test_official_playwright_releases_have_exact_commits(self):
        sources = self.data["routes"]["browser-js"]["sources"]
        by_url = {source["url"]: source for source in sources}
        self.assertEqual(
            by_url["https://github.com/microsoft/playwright"]["commit"],
            "1b025d7e20a026371cd5f98ba0cdce48892737c8",
        )
        self.assertEqual(
            by_url["https://github.com/microsoft/playwright-mcp"]["commit"],
            "4c1fb03bad3bae379b0ae0e3d81d2660de56bd91",
        )

    def test_direct_rust_binding_is_third_party_and_pinned(self):
        route = self.data["routes"]["browser-rust"]
        candidate = next(s for s in route["sources"] if "padamson" in s["url"])
        self.assertFalse(route["official"])
        self.assertEqual(candidate["release"], "v0.18.0")
        self.assertEqual(candidate["commit"], "165554e8be114efe9e024aa45a8d00c92fa2e5c8")
        self.assertEqual(candidate["verdict"], "PASS-WITH-NOTE")
        self.assertIn("without verifying artifact digests", route["supportLimit"])

    def test_metadata_never_claims_official_rust_support(self):
        route = self.data["routes"]["browser-rust"]
        self.assertIn("Microsoft does not support", route["supportLimit"])
        self.assertIn("official Playwright JavaScript/TypeScript", route["default"])

    def test_agent_routes_reference_real_local_definitions(self):
        expected = {
            "orchestrator-maxwell", "ui-canvas", "tester-probe", "security-sentinel"
        }
        self.assertEqual({a["id"] for a in self.data["agents"]}, expected)
        for agent in self.data["agents"]:
            self.assertTrue((ROOT / agent["file"]).is_file(), agent["file"])
        self.assertIn("load a full agent definition only when", self.data["agentLoading"])


class ProbesDoNotTurnPresenceIntoPermission(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = pathlib.Path(self.temp.name)
        self.home = self.base / "home"
        self.repo = self.base / "repo"
        self.home.mkdir()
        self.repo.mkdir()

    def test_installed_native_bundle_still_reports_session_tool_unknown(self):
        package = (self.home / ".codex" / "plugins" / "cache" / "openai-bundled" /
                   "computer-use" / "26.903.61454")
        manifest = package / ".codex-plugin" / "plugin.json"
        skill = package / "skills" / "computer-use" / "SKILL.md"
        manifest.parent.mkdir(parents=True)
        skill.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({"name": "computer-use", "version": "26.903.61454"}),
                            encoding="utf-8")
        skill.write_text("---\nname: computer-use\n---\n", encoding="utf-8")

        found = computer.probe_native(self.home)
        self.assertTrue(found["packageInstalled"])
        self.assertEqual(found["sessionToolState"], "unknown")
        self.assertIsNone(found["ready"])

    def test_copied_skill_without_plugin_is_not_a_native_tool(self):
        skill = self.home / ".codex" / "skills" / "computer-use" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("---\nname: computer-use\n---\n", encoding="utf-8")
        found = computer.probe_native(self.home)
        self.assertFalse(found["packageInstalled"])
        self.assertTrue(found["copiedSkillOnly"])
        self.assertIsNone(found["ready"])

    def test_mcp_configuration_is_not_proof_the_server_is_running(self):
        config = self.home / ".cursor" / "mcp.json"
        config.parent.mkdir(parents=True)
        config.write_text('{"command":"npx @playwright/mcp@0.0.80"}', encoding="utf-8")
        with mock.patch.object(computer.shutil, "which", return_value=None):
            found = computer.probe_browser_js(self.home, self.repo)
        self.assertEqual(found["configuredPaths"], [str(config)])
        self.assertFalse(found["localExecutableEvidence"])
        self.assertEqual(found["sessionToolState"], "unknown")
        self.assertIsNone(found["ready"])

    def test_rust_manifest_is_detected_without_building_it(self):
        manifest = self.repo / "Cargo.toml"
        manifest.write_text('[dependencies]\nplaywright-rs = "=0.18.0"\n', encoding="utf-8")
        with mock.patch.object(computer.shutil, "which", return_value="C:/Rust/cargo.exe"):
            found = computer.probe_browser_rust(self.repo)
        self.assertEqual(found["bindingDeclarations"], [str(manifest)])
        self.assertEqual(found["runtimeState"], "unknown")
        self.assertIsNone(found["ready"])

    def test_rust_defaults_to_the_official_sidecar_without_a_direct_binding(self):
        with mock.patch.object(computer.shutil, "which", return_value=None):
            probes = computer.inventory(self.home, self.repo)
        decision = computer.route_decision("browser-rust", probes, computer.load_capabilities())
        self.assertEqual(decision["implementation"], "microsoft/playwright JS/TS sidecar")
        self.assertFalse(decision["actionTaken"])


class TheRouterIsReadOnly(unittest.TestCase):
    def test_source_imports_no_network_or_process_launcher(self):
        source = (ROOT / "scripts" / "harness_computer.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertTrue({"urllib", "requests", "socket", "subprocess"}.isdisjoint(imported))

    def test_its_own_check_passes_without_taking_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "harness_computer.py"),
                 "--check", "--home", str(base / "home"), "--repo", str(base / "repo")],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("READ ONLY", result.stdout)
        self.assertIn("no action taken", result.stdout)

    def test_every_route_response_says_no_action_was_taken(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            for route in computer.ROUTES:
                result = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / "harness_computer.py"),
                     "--route", route, "--json", "--home", str(base / "home"),
                     "--repo", str(base / "repo")],
                    cwd=ROOT, capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(json.loads(result.stdout)["actionTaken"], route)


class EveryPromptHarnessSharesTheRoute(unittest.TestCase):
    PROMPT = "Use Playwright browser automation to verify this page."

    def setUp(self):
        """Rendering the pipeline captures a goal, so isolate the store.

        Without this the suite left this class's fixture prompt standing as the
        repository's real goal. Found by checking .auto-mode/goal.json after a
        green run rather than by any assertion, which is the point: a test that
        writes real state fails silently somewhere else.
        """
        store = surface.skill_pipeline.isolated_store()
        store.__enter__()
        self.addCleanup(store.__exit__, None, None, None)

    def test_the_skill_travels_with_the_surface_harness(self):
        self.assertIn("master-computer-control", surface.ENFORCED_SKILLS)
        self.assertIn("### master-computer-control", surface.build_bundle("chatgpt"))

    def test_surface_proxy_wrapper_and_goal_all_name_the_same_router(self):
        proxied, _ = proxy.inject({
            "model": "m", "messages": [{"role": "user", "content": self.PROMPT}]
        })
        contexts = {
            "surface": surface.skill_pipeline.context_for(self.PROMPT),
            "proxy": proxied["messages"][0]["content"],
            "wrapper": wrap.rules_for(self.PROMPT),
            "goal": goal.context_for(self.PROMPT),
        }
        for name, context in contexts.items():
            self.assertIn("master-computer-control", context, name)
            self.assertIn("scripts/harness_computer.py", context, name)

    def test_unrelated_prompts_do_not_pay_for_the_conditional_route(self):
        context = surface.skill_pipeline.context_for("Summarize this short paragraph.")
        self.assertNotIn("scripts/harness_computer.py", context)

    def test_openai_skill_metadata_allows_automatic_selection(self):
        metadata = (ROOT / "skills" / "master-computer-control" / "agents" /
                    "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("$master-computer-control", metadata)
        self.assertIn("allow_implicit_invocation: true", metadata)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Inspect and route computer control without opening, clicking, or installing anything.

This is a capability router, not another model harness. The four prompt
harnesses call attention to it when a request needs a real screen or browser.
This script then reports which evidence is present on this machine and the
limits of each route. It never launches a browser, contacts a server, installs a
package, or treats an installed skill as proof that its host tool is active.

Usage:
    python scripts/harness_computer.py --check
    python scripts/harness_computer.py --route native
    python scripts/harness_computer.py --route browser-js --json
    python scripts/harness_computer.py --route browser-rust --repo PATH
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# Where the skills, the block and the goal state actually live. Different in a
# checkout and in a wheel with no checkout anywhere, and this is the only module
# that knows the difference.
import harness_paths  # noqa: E402

CAPABILITIES = (harness_paths.skills_dir() / "master-computer-control"
                / "references" / "capabilities.json")

ROUTES = ("native", "browser-js", "browser-rust")
CONFIG_PATHS = (
    ("home", ".codex/config.toml"),
    ("home", ".cursor/mcp.json"),
    ("home", ".claude.json"),
    ("home", ".gemini/settings.json"),
    ("repo", ".mcp.json"),
    ("repo", ".vscode/mcp.json"),
    ("repo", ".cursor/mcp.json"),
)
SKIP_DIRS = {".git", "node_modules", "target", ".venv", "venv"}


def _joined(base: pathlib.Path, relative: str) -> pathlib.Path:
    return base.joinpath(*relative.split("/"))


def _read_small(path: pathlib.Path, limit: int = 2_000_000) -> str:
    """Read enough to find a declaration, never dump or return file contents."""
    try:
        if not path.is_file() or path.stat().st_size > limit:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def load_capabilities(path: pathlib.Path = CAPABILITIES) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 1:
        raise ValueError("computer capability metadata needs schemaVersion 1")
    routes = data.get("routes")
    if not isinstance(routes, dict) or set(routes) != set(ROUTES):
        raise ValueError("computer capability metadata has the wrong route set")
    return data


def probe_native(home: pathlib.Path) -> dict:
    """Find the OpenAI bundle, without claiming its session tool is enabled."""
    base = home / ".codex" / "plugins" / "cache" / "openai-bundled" / "computer-use"
    versions = []
    if base.is_dir():
        for manifest in base.glob("*/.codex-plugin/plugin.json"):
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            skill = manifest.parent.parent / "skills" / "computer-use" / "SKILL.md"
            if data.get("name") == "computer-use" and skill.is_file():
                versions.append(str(data.get("version") or manifest.parent.parent.name))

    copied_skill = home / ".codex" / "skills" / "computer-use" / "SKILL.md"
    return {
        "packageInstalled": bool(versions),
        "packageVersions": sorted(set(versions)),
        "copiedSkillOnly": copied_skill.is_file() and not versions,
        "sessionToolState": "unknown",
        "ready": None,
        "reason": (
            "The bundled skill is present, but only the model host can report whether "
            "the Computer Use tool is enabled in this session."
            if versions else
            "No OpenAI bundled Computer Use package was found in this home directory."
        ),
    }


def _configured_playwright_paths(home: pathlib.Path, repo: pathlib.Path) -> list[str]:
    found = []
    for owner, relative in CONFIG_PATHS:
        base = home if owner == "home" else repo
        path = _joined(base, relative)
        text = _read_small(path).lower()
        if "@playwright/mcp" in text or "mcp-server-playwright" in text:
            found.append(str(path))
    return found


def probe_browser_js(home: pathlib.Path, repo: pathlib.Path) -> dict:
    packages = []
    for relative in (
        "node_modules/@playwright/mcp/package.json",
        "node_modules/@playwright/test/package.json",
        "node_modules/playwright/package.json",
    ):
        path = _joined(repo, relative)
        if path.is_file():
            packages.append(str(path))

    commands = {
        name: shutil.which(name)
        for name in ("node", "npx", "playwright", "mcp-server-playwright")
    }
    configured = _configured_playwright_paths(home, repo)
    executable = bool(packages or commands["playwright"] or commands["mcp-server-playwright"])
    if executable:
        state = "local package or executable found; browser binaries and session tool still unverified"
    elif configured:
        state = "configured only; configuration is not proof the server is installed or running"
    elif commands["node"] and commands["npx"]:
        state = "Node runtime found; Playwright is not proven installed"
    else:
        state = "no local Playwright execution evidence found"
    return {
        "commands": commands,
        "localPackages": packages,
        "configuredPaths": configured,
        "localExecutableEvidence": executable,
        "sessionToolState": "unknown",
        "ready": None,
        "reason": state,
    }


def _cargo_manifests(repo: pathlib.Path):
    count = 0
    try:
        candidates = repo.rglob("Cargo.toml")
    except OSError:
        return
    for path in candidates:
        if any(part in SKIP_DIRS for part in path.relative_to(repo).parts):
            continue
        yield path
        count += 1
        if count >= 200:
            return


def probe_browser_rust(repo: pathlib.Path) -> dict:
    declarations = []
    direct_pattern = re.compile(r"(?m)^\s*playwright-rs\s*=|\bpackage\s*=\s*[\"']playwright-rs[\"']")
    for manifest in _cargo_manifests(repo):
        if direct_pattern.search(_read_small(manifest)):
            declarations.append(str(manifest))
    lock = repo / "Cargo.lock"
    if re.search(r'(?m)^name\s*=\s*"playwright-rs"\s*$', _read_small(lock)):
        declarations.append(str(lock))

    cargo = shutil.which("cargo")
    driver_override = os.environ.get("PLAYWRIGHT_DRIVER_PATH")
    return {
        "cargo": cargo,
        "bindingDeclarations": sorted(set(declarations)),
        "driverOverrideExists": bool(driver_override and pathlib.Path(driver_override).exists()),
        "runtimeState": "unknown",
        "ready": None,
        "reason": (
            "A direct Rust binding is declared, but this read-only probe does not build it, "
            "download its driver, or launch a browser."
            if declarations else
            "No direct playwright-rs binding is declared in this project. Use official "
            "JavaScript/TypeScript Playwright as a black-box sidecar for the Rust app "
            "by default. The optional direct binding and other Rust CDP routes are "
            "documented in the capability metadata and repo-lists/browser-automation.txt; "
            "being catalogued does not prove they are installed or tested locally."
        ),
    }


def inventory(home: pathlib.Path, repo: pathlib.Path) -> dict:
    return {
        "native": probe_native(home),
        "browser-js": probe_browser_js(home, repo),
        "browser-rust": probe_browser_rust(repo),
    }


def route_decision(route: str, probes: dict, capabilities: dict) -> dict:
    evidence = probes[route]
    meta = capabilities["routes"][route]
    if route == "native":
        implementation = "OpenAI bundled Computer Use" if evidence["packageInstalled"] else "unavailable"
        next_step = (
            "Confirm the intended app and action, then use the host's active Computer Use tool."
            if evidence["packageInstalled"] else
            "Enable the OpenAI Computer Use plugin in a supported Windows host; this script cannot enable it."
        )
    elif route == "browser-js":
        implementation = "microsoft/playwright-mcp" if evidence["configuredPaths"] else "microsoft/playwright"
        next_step = (
            "Use the already configured Playwright tool or local package, then verify the browser state before acting."
            if evidence["configuredPaths"] or evidence["localExecutableEvidence"] else
            "Install a pinned official Playwright release only after explicit approval; this script does not install it."
        )
    else:
        direct = bool(evidence["bindingDeclarations"])
        implementation = "padamson/playwright-rust" if direct else "microsoft/playwright JS/TS sidecar"
        next_step = (
            "Verify the pinned driver and browser separately before running the declared third-party binding."
            if direct else
            "Test the Rust application from official Playwright JS/TS. Choose the direct Rust binding only after accepting its third-party and build-download limits."
        )
    return {
        "route": route,
        "implementation": implementation,
        "evidence": evidence,
        "supportLimit": meta["supportLimit"],
        "nextStep": next_step,
        "actionTaken": False,
    }


def _metadata_failures(capabilities: dict) -> list[str]:
    failures = []
    sha = re.compile(r"^[0-9a-f]{40}$")
    for route, record in capabilities["routes"].items():
        for source in record.get("sources", []):
            if not source.get("url", "").startswith("https://"):
                failures.append(f"{route} has a non-HTTPS source")
            commit = source.get("commit")
            if commit is not None and not sha.fullmatch(commit):
                failures.append(f"{route} has an unpinned source commit")
    for agent in capabilities.get("agents", []):
        path = harness_paths.agent_path(agent.get("file", ""))
        if not path.is_file():
            failures.append(f"agent reference is missing: {agent.get('file')}")
    if not harness_paths.skill_path("master-computer-control").is_file():
        failures.append("master-computer-control skill is missing")
    return failures


def check(home: pathlib.Path, repo: pathlib.Path, as_json: bool = False) -> int:
    """Validate metadata and report local evidence. This is entirely read-only."""
    try:
        capabilities = load_capabilities()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAILED: capability metadata: {error}", file=sys.stderr)
        return 1
    failures = _metadata_failures(capabilities)
    probes = inventory(home, repo)
    if as_json:
        print(json.dumps({"ok": not failures, "failures": failures, "routes": probes}, indent=2))
    else:
        print("Computer control capability check. READ ONLY: no app, browser, model, or network was contacted.")
        for route in ROUTES:
            print(f"{route:<14} {probes[route]['reason']}")
        print("native active   unknown by design; an installed skill is not an active host tool")
        print("agents          " + ", ".join(a["id"] for a in capabilities.get("agents", [])))
    if failures:
        for failure in failures:
            print("FAILED: " + failure, file=sys.stderr)
        return 1
    if not as_json:
        print("\ncomputer control router ready; no action taken")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="validate routes and report local evidence")
    group.add_argument("--route", choices=ROUTES, help="select one route without launching it")
    parser.add_argument("--home", type=pathlib.Path, default=pathlib.Path.home())
    parser.add_argument("--repo", type=pathlib.Path, default=ROOT)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    home = args.home.resolve()
    repo = args.repo.resolve()
    if args.check:
        return check(home, repo, args.json)

    capabilities = load_capabilities()
    decision = route_decision(args.route, inventory(home, repo), capabilities)
    if args.json:
        print(json.dumps(decision, indent=2))
    else:
        print(f"route           {decision['route']}")
        print(f"implementation  {decision['implementation']}")
        print(f"evidence        {decision['evidence']['reason']}")
        print(f"support limit   {decision['supportLimit']}")
        print(f"next step       {decision['nextStep']}")
        print("action taken    no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

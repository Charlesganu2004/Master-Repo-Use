#!/usr/bin/env python3
"""Install Master Repo auto mode on any machine that has Python.

Three layers, cheapest first:

1. A PreToolUse hook enforcing the no-prune policy. Runs outside the model, so
   it costs nothing per session and does not rely on anything being remembered.
2. The master-repo-auto skill. Only its name and description sit in the listing;
   the body loads when something needs it.
3. A short pointer in each client's global instruction file, carrying only the
   two rules that must be known before any lookup happens.

The rules used to live entirely in layer 3, at roughly 616 tokens per session
per client. This ordering exists to get that back.

Usage:
    python scripts/install_auto_mode.py [--repo PATH] [--no-hook] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import platform
import shutil
import sys

BEGIN = "<!-- MASTER-REPO-USE:BEGIN -->"
END = "<!-- MASTER-REPO-USE:END -->"

CLIENTS = {
    "Claude Code": ".claude/CLAUDE.md",
    "Codex": ".codex/AGENTS.md",
    "Gemini": ".gemini/GEMINI.md",
    "Copilot": ".copilot/copilot-instructions.md",
}


def describe_platform() -> str:
    system = platform.system()
    if system == "Linux" and "microsoft" in platform.release().lower():
        return "WSL"
    return {"Darwin": "macOS", "Windows": "Windows", "Linux": "Linux"}.get(system, system)


def upsert_block(path: pathlib.Path, body: str, dry: bool) -> str:
    """Replace the marked block in place, leaving everything else alone."""
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    block = f"{BEGIN}\n{body.strip()}\n{END}"
    if BEGIN in text and END in text:
        start = text.index(BEGIN)
        stop = text.index(END, start) + len(END)
        new = text[:start].rstrip() + "\n\n" + block + "\n" + text[stop:].lstrip()
        action = "would update" if dry else "updated"
    else:
        new = text.rstrip() + ("\n\n" if text.strip() else "") + block + "\n"
        action = "would add" if dry else "added"
    if not dry:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new, encoding="utf-8")
    return action


def install_skill(repo: pathlib.Path, home: pathlib.Path, dry: bool) -> str:
    source = repo / "skills" / "master-repo-auto"
    if not source.is_dir():
        return "skipped, source missing"
    target = home / ".claude" / "skills" / "master-repo-auto"
    if dry:
        return "would install"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    return "installed"


def register_hook(repo: pathlib.Path, home: pathlib.Path, dry: bool) -> str:
    """Add the no-prune PreToolUse hook without disturbing existing settings."""
    settings = home / ".claude" / "settings.json"
    hook_path = repo / "scripts" / "hooks" / "no_prune_guard.py"
    if not hook_path.exists():
        return "skipped, hook missing"

    data: dict = {}
    if settings.exists():
        raw = settings.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except ValueError:
            return "REFUSED: settings.json is not valid JSON, refusing to overwrite it"
        if not dry:  # never touch the file without a copy beside it
            settings.with_suffix(".json.bak").write_text(raw, encoding="utf-8")

    command = f'{json.dumps(sys.executable)} {json.dumps(str(hook_path))}'
    hooks = data.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])

    for entry in pre:
        for hook in entry.get("hooks", []):
            if "no_prune_guard" in str(hook.get("command", "")):
                hook["command"] = command  # refresh the path, do not duplicate
                if not dry:
                    settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
                return "would refresh" if dry else "refreshed"

    pre.append({"matcher": "Bash",
                "hooks": [{"type": "command", "command": command}]})
    if not dry:
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return "would register" if dry else "registered"


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Master Repo auto mode.")
    parser.add_argument("--repo", default=str(pathlib.Path(__file__).resolve().parents[1]))
    parser.add_argument("--home", default=str(pathlib.Path.home()))
    parser.add_argument("--no-hook", action="store_true", help="skip the no-prune hook")
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    args = parser.parse_args()

    repo = pathlib.Path(args.repo).expanduser().resolve()
    home = pathlib.Path(args.home).expanduser()
    dry = args.dry_run

    if not (repo / ".git").exists():
        print(f"Master Repo not found at {repo}", file=sys.stderr)
        return 1

    block_file = repo / "docs" / "auto-mode-block.txt"
    if not block_file.exists():
        print(f"Auto mode block not found at {block_file}", file=sys.stderr)
        return 1
    body = f"Master Repo path: {repo}\n" + block_file.read_text(encoding="utf-8").strip()

    print(f"Platform : {describe_platform()}")
    print(f"Repo     : {repo}")
    print(f"Home     : {home}")
    print(f"Mode     : {'dry run, nothing written' if dry else 'writing'}\n")

    print(f"skill    : {install_skill(repo, home, dry)}")
    print(f"hook     : {'skipped by request' if args.no_hook else register_hook(repo, home, dry)}")
    for name, rel in CLIENTS.items():
        print(f"{name:<9}: {upsert_block(home / rel, body, dry)}  ({rel})")

    cost = len(body.encode('utf-8'))
    print(f"\nPer-session cost of the always-loaded pointer: {cost} bytes, about {cost // 4} tokens.")
    print("The full rules stay in the skill and load only when needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

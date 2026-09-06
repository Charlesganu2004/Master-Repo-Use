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
    # Gemini CLI and Google Antigravity read the SAME file. Verified 2026-09-04
    # against antigravity.google/docs/rules-workflows/, which says global rules
    # live in ~/.gemini/GEMINI.md. There is no ~/.antigravity/ tree, so listing
    # Antigravity separately here would write the block twice to one path and let
    # the second write replace the first.
    "Gemini + Antigravity": ".gemini/GEMINI.md",
    "Copilot": ".copilot/copilot-instructions.md",
}

# Where each client looks for skill folders. Both take the same layout: one
# directory per skill, holding a SKILL.md with frontmatter. Antigravity requires
# only `description`, which every skill in this repository already has, so the
# same folders install unmodified into both.
SKILL_ROOTS = {
    "Claude Code": ".claude/skills",
    "Antigravity": ".gemini/config/skills",
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


def install_skill(repo: pathlib.Path, home: pathlib.Path, dry: bool,
                  root: str = ".claude/skills") -> str:
    """Install every skill in the repository into one client's skill root.

    All of them, not just master-repo-auto. The rule Charles asked for is that
    capabilities are global and get selected automatically when they fit, and a
    skill that was never copied to the machine cannot be selected at all. A
    directory without a SKILL.md is not a skill and is skipped rather than copied
    as an empty folder the client will scan on every start.
    """
    source = repo / "skills"
    if not source.is_dir():
        return "skipped, source missing"
    skills = sorted(p for p in source.iterdir()
                    if p.is_dir() and (p / "SKILL.md").is_file())
    if not skills:
        return "skipped, no SKILL.md found"
    if dry:
        return f"would install {len(skills)} into {root}"
    target = home / pathlib.PurePosixPath(root)
    target.mkdir(parents=True, exist_ok=True)
    for skill in skills:
        destination = target / skill.name
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(skill, destination)
    return f"installed {len(skills)} into {root}: " + ", ".join(s.name for s in skills)


GUARDS = ("no_prune_guard", "no_compress_guard")


def register_hook(repo: pathlib.Path, home: pathlib.Path, dry: bool) -> str:
    """Register both PreToolUse guards without disturbing existing settings.

    no_prune_guard keeps chosen tools from being deleted. no_compress_guard keeps
    the NO-COMPRESS block from being summarised away. Both exist because a rule
    that only holds while a model is paying attention is not a rule.
    """
    settings = home / ".claude" / "settings.json"
    available = [(name, repo / "scripts" / "hooks" / f"{name}.py") for name in GUARDS]
    available = [(name, path) for name, path in available if path.exists()]
    if not available:
        return "skipped, hooks missing"

    data: dict = {}
    if settings.exists():
        raw = settings.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except ValueError:
            return "REFUSED: settings.json is not valid JSON, refusing to overwrite it"
        if not dry:  # never touch the file without a copy beside it
            settings.with_suffix(".json.bak").write_text(raw, encoding="utf-8")

    hooks = data.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])
    added, refreshed = [], []

    for name, path in available:
        command = f'{json.dumps(sys.executable)} {json.dumps(str(path))}'
        existing = None
        for entry in pre:
            for hook in entry.get("hooks", []):
                if name in str(hook.get("command", "")):
                    existing = hook
        if existing is not None:
            existing["command"] = command      # refresh the path, do not duplicate
            refreshed.append(name)
        else:
            pre.append({"matcher": "Bash",
                        "hooks": [{"type": "command", "command": command}]})
            added.append(name)

    if not dry:
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    parts = []
    if added:
        parts.append(("would register " if dry else "registered ") + ", ".join(added))
    if refreshed:
        parts.append(("would refresh " if dry else "refreshed ") + ", ".join(refreshed))
    return "; ".join(parts) or "nothing to do"


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

    for client, root in SKILL_ROOTS.items():
        print(f"skills   : {client:<12} {install_skill(repo, home, dry, root)}")
    print(f"hook     : {'skipped by request' if args.no_hook else register_hook(repo, home, dry)}")
    for name, rel in CLIENTS.items():
        print(f"{name:<9}: {upsert_block(home / rel, body, dry)}  ({rel})")

    cost = len(body.encode('utf-8'))
    print(f"\nPer-session cost of the always-loaded pointer: {cost} bytes, about {cost // 4} tokens.")
    print("The full rules stay in the skill and load only when needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

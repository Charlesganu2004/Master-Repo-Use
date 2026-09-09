#!/usr/bin/env python3
"""Install Master Repo auto mode on any machine that has Python.

Three enforcement layers, cheapest first:

1. Native lifecycle hooks enforce the no-prune and no-compress policy wherever
   a client exposes them. They run outside the model and cost no prompt tokens.
2. The master-repo-auto skill. Only its name and description sit in the listing;
   the body loads when something needs it.
3. A protected block in every client's global instruction or always-rule file,
   so the three-layer workflow arrives without a slash command.

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
import shlex
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

# Where each verified client looks for skill folders. All take the same layout: one
# directory per skill, holding a SKILL.md with frontmatter. Antigravity requires
# only `description`, which every skill in this repository already has, so the
# same folders install unmodified into both.
SKILL_ROOTS = {
    "Claude Code": ".claude/skills",
    "Codex": ".codex/skills",
    "Gemini CLI": ".gemini/skills",
    "Antigravity": ".gemini/config/skills",
    "Cursor": ".cursor/skills",
    "GitHub Copilot": ".copilot/skills",
    "Shared agent skills": ".agents/skills",
}

CLIENT_KEYS = {
    "Claude Code": "claude", "Codex": "codex",
    "Gemini + Antigravity": "gemini", "Copilot": "copilot",
    "Antigravity": "antigravity", "Cursor": "cursor",
    "GitHub Copilot": "copilot", "Shared agent skills": "codex",
    "Gemini CLI": "gemini",
}


def hook_command(path: pathlib.Path) -> str:
    """Quote an executable and its one path argument for the platform shell."""
    if os.name == "nt":
        # cmd-compatible command text; forward slashes avoid JSON-style double
        # escaping leaking into the shell. The Python path is normally unspaced.
        import subprocess
        return subprocess.list2cmdline([sys.executable, str(path)])
    return shlex.join([sys.executable, str(path)])

CURSOR_FRONTMATTER = """---
description: Master Repo automatic three-layer workflow
alwaysApply: true
---"""


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


def upsert_cursor_rule(path: pathlib.Path, body: str, dry: bool) -> str:
    """Write Cursor's file-backed global rule with mandatory MDC metadata.

    The file is dedicated to Master Repo auto mode. Unknown prose outside the
    managed markers is preserved, while the metadata is refreshed so Cursor
    cannot silently downgrade it to an agent-selected or manual rule.
    """
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    remainder = text
    if text.startswith("---"):
        lines = text.splitlines()
        try:
            close = lines.index("---", 1)
        except ValueError:
            close = -1
        if close >= 0:
            remainder = "\n".join(lines[close + 1:]).lstrip()

    block = f"{BEGIN}\n{body.strip()}\n{END}"
    if BEGIN in remainder and END in remainder:
        start = remainder.index(BEGIN)
        stop = remainder.index(END, start) + len(END)
        remainder = (remainder[:start].rstrip() + "\n\n" + block + "\n" +
                     remainder[stop:].lstrip())
        action = "would update" if dry else "updated"
    else:
        remainder = remainder.rstrip() + ("\n\n" if remainder.strip() else "") + block + "\n"
        action = "would add" if dry else "added"

    rendered = CURSOR_FRONTMATTER + "\n\n" + remainder
    if not dry:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
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
        # Merge in place. Removing the destination first would delete files a
        # person or another client added to that capability directory, which
        # contradicts the no-prune guarantee this installer is meant to apply.
        shutil.copytree(skill, destination, dirs_exist_ok=True)
    return (f"merged {len(skills)} into {root} without deleting existing files: "
            + ", ".join(s.name for s in skills))


# Two PreToolUse guards, matched on Bash, plus one UserPromptSubmit injector.
GUARDS = ("no_prune_guard", "no_compress_guard")

# The event each hook binds to, and whether it takes a tool matcher.
# UserPromptSubmit has no matcher: it fires on every prompt, which is the whole
# reason it can enforce a standing pipeline that skills alone cannot.
HOOK_EVENTS = {
    "no_prune_guard": ("PreToolUse", "Bash"),
    "no_compress_guard": ("PreToolUse", "Bash"),
    "skill_pipeline": ("UserPromptSubmit", None),
}
ALL_HOOKS = GUARDS + ("skill_pipeline",)


def register_hook(repo: pathlib.Path, home: pathlib.Path, dry: bool) -> str:
    """Register the guards and the prompt pipeline, leaving other settings alone.

    no_prune_guard keeps chosen tools from being deleted. no_compress_guard keeps
    the NO-COMPRESS block from being summarised away. Both exist because a rule
    that only holds while a model is paying attention is not a rule.

    skill_pipeline is the answer to "why do I have to type a slash". Skills are
    model-invocable, so they fire on the model's judgement; a UserPromptSubmit
    hook fires on every prompt regardless of judgement, and injects the standing
    rules into the turn before the model reads it.
    """
    settings = home / ".claude" / "settings.json"
    available = [(name, repo / "scripts" / "hooks" / f"{name}.py") for name in ALL_HOOKS]
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
    added, refreshed = [], []

    for name, path in available:
        event, matcher = HOOK_EVENTS[name]
        bucket = hooks.setdefault(event, [])
        command = hook_command(path)
        existing = None
        for entry in bucket:
            for hook in entry.get("hooks", []):
                if name in str(hook.get("command", "")):
                    existing = hook
        if existing is not None:
            existing["command"] = command      # refresh the path, do not duplicate
            refreshed.append(name)
        else:
            entry = {"hooks": [{"type": "command", "command": command}]}
            if matcher:
                entry["matcher"] = matcher
            bucket.append(entry)
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


def register_antigravity_hook(repo: pathlib.Path, home: pathlib.Path, dry: bool) -> str:
    """Give Antigravity the same standing pipeline, in its own hook format.

    This adapter is separate from Gemini CLI, whose settings.json uses different
    events. Other clients below have their own verified lifecycle adapters.

    Schema read from antigravity.google/docs/hooks on 2026-09-07 rather than
    guessed. Three things about it differ from Claude Code and each would break
    the hook silently if assumed:
      the file is ~/.gemini/config/hooks.json, keyed by hook NAME at the top level
      the per-prompt event is PreInvocation, not UserPromptSubmit
      PreInvocation handlers sit directly under the event key and take no matcher
    """
    hook = repo / "scripts" / "hooks" / "skill_pipeline.py"
    if not hook.exists():
        return "skipped, hook missing"
    config = home / ".gemini" / "config" / "hooks.json"

    data: dict = {}
    if config.exists():
        raw = config.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except ValueError:
            return "REFUSED: hooks.json is not valid JSON, refusing to overwrite it"
        if not dry:
            config.with_suffix(".json.bak").write_text(raw, encoding="utf-8")

    command = hook_command(hook) + " --antigravity"
    entry = data.setdefault("master-repo-pipeline", {})
    existed = bool(entry.get("PreInvocation"))
    entry["enabled"] = True
    entry["PreInvocation"] = [{"type": "command", "command": command, "timeout": 15}]

    if dry:
        return "would refresh PreInvocation" if existed else "would register PreInvocation"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return "refreshed PreInvocation" if existed else "registered PreInvocation"


def _load_hook_file(path: pathlib.Path, dry: bool) -> tuple[dict, str | None]:
    """Load one hook config and make a recoverable backup before mutation."""
    if not path.exists():
        return {}, None
    raw = path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except ValueError:
        return {}, "REFUSED: hooks.json is not valid JSON, refusing to overwrite it"
    if not isinstance(data, dict):
        return {}, "REFUSED: hooks.json root is not an object, refusing to overwrite it"
    hooks = data.get("hooks", {})
    if not isinstance(hooks, dict):
        return {}, "REFUSED: hooks field is not an object, refusing to overwrite it"
    for event, bucket in hooks.items():
        if not isinstance(bucket, list) or any(not isinstance(entry, dict) for entry in bucket):
            return {}, f"REFUSED: hooks.{event} must be an array of objects"
        for entry in bucket:
            nested = entry.get("hooks", [])
            if not isinstance(nested, list) or any(not isinstance(item, dict) for item in nested):
                return {}, f"REFUSED: hooks.{event} has invalid nested handlers"
    if not dry:
        path.with_suffix(".json.bak").write_text(raw, encoding="utf-8")
    return data, None


def _merge_hook(bucket: list, needle: str, replacement: dict) -> str:
    """Refresh this installer's hook without deleting hooks owned elsewhere."""
    for index, entry in enumerate(bucket):
        command = " ".join(str(entry.get(key, ""))
                           for key in ("command", "exec", "bash", "powershell"))
        command += " " + " ".join(str(value) for value in entry.get("args", []))
        if needle in command:
            bucket[index] = replacement
            return "refreshed"
    bucket.append(replacement)
    return "registered"


def register_cursor_hooks(repo: pathlib.Path, home: pathlib.Path, dry: bool) -> str:
    """Register Cursor session context plus shell guards in its global hook file."""
    config = home / ".cursor" / "hooks.json"
    data, error = _load_hook_file(config, dry)
    if error:
        return error

    scripts = repo / "scripts" / "hooks"
    required = {
        "skill_pipeline": scripts / "skill_pipeline.py",
        "no_prune_guard": scripts / "no_prune_guard.py",
        "no_compress_guard": scripts / "no_compress_guard.py",
    }
    if any(not path.exists() for path in required.values()):
        return "skipped, hooks missing"

    data["version"] = 1
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        return "REFUSED: hooks field is not an object, refusing to overwrite it"

    statuses = []
    pipeline = hook_command(required["skill_pipeline"]) + " --cursor"
    statuses.append(_merge_hook(
        hooks.setdefault("sessionStart", []),
        "skill_pipeline.py",
        {"command": pipeline},
    ) + " sessionStart")
    for name in ("no_prune_guard", "no_compress_guard"):
        command = hook_command(required[name])
        statuses.append(_merge_hook(
            hooks.setdefault("preToolUse", []),
            f"{name}.py",
            {"command": command, "matcher": "Shell"},
        ) + f" {name}")

    if not dry:
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    prefix = "would " if dry else ""
    return prefix + ", ".join(statuses)


def register_copilot_hooks(repo: pathlib.Path, home: pathlib.Path, dry: bool) -> str:
    """Register Copilot CLI session context and Claude-compatible shell guards."""
    config = home / ".copilot" / "hooks" / "master-repo-auto.json"
    data, error = _load_hook_file(config, dry)
    if error:
        return error

    scripts = repo / "scripts" / "hooks"
    required = {
        "skill_pipeline": scripts / "skill_pipeline.py",
        "no_prune_guard": scripts / "no_prune_guard.py",
        "no_compress_guard": scripts / "no_compress_guard.py",
    }
    if any(not path.exists() for path in required.values()):
        return "skipped, hooks missing"

    data["version"] = 1
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        return "REFUSED: hooks field is not an object, refusing to overwrite it"

    # Copilot's hook entry takes `bash` and `powershell` script strings, not an
    # exec/args pair, and its event names are lower camelCase. Both were wrong
    # here, and both fail the same silent way: the file parses, the hook is
    # listed, and nothing ever runs. Shapes read from GitHub's hooks reference
    # and the CLI hooks how-to on 2026-09-08.
    def copilot_entry(script: pathlib.Path, *flags: str) -> dict:
        argv = " ".join([f'"{script}"', *flags])
        return {
            "type": "command",
            "bash": f'python3 {argv}',
            "powershell": f'python {argv}',
            "timeoutSec": 15,
        }

    statuses = []
    statuses.append(_merge_hook(
        hooks.setdefault("sessionStart", []),
        "skill_pipeline.py",
        copilot_entry(required["skill_pipeline"], "--copilot-session"),
    ) + " sessionStart")
    statuses.append(_merge_hook(
        hooks.setdefault("userPromptTransformed", []),
        "skill_pipeline.py",
        copilot_entry(required["skill_pipeline"], "--copilot-transform"),
    ) + " userPromptTransformed")
    for name in ("no_prune_guard", "no_compress_guard"):
        statuses.append(_merge_hook(
            hooks.setdefault("preToolUse", []),
            f"{name}.py",
            copilot_entry(required[name]),
        ) + f" {name}")

    if not dry:
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    prefix = "would " if dry else ""
    return prefix + ", ".join(statuses)


def register_codex_hooks(repo: pathlib.Path, home: pathlib.Path, dry: bool) -> str:
    """Install Codex native hooks; the client still requires review of their hash."""
    config = home / ".codex" / "hooks.json"
    data, error = _load_hook_file(config, dry)
    if error:
        return error
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        return "REFUSED: hooks field is not an object, refusing to overwrite it"
    for name, (event, matcher) in HOOK_EVENTS.items():
        path = repo / "scripts" / "hooks" / f"{name}.py"
        if not path.is_file():
            return "skipped, hooks missing"
        bucket = hooks.setdefault(event, [])
        handler = {"type": "command", "command": hook_command(path), "timeout": 15}
        if name == "skill_pipeline":
            handler["additionalContextLimit"] = 0
        if os.name == "nt":
            # Codex's Windows command hook runs through PowerShell.
            handler["commandWindows"] = "& '" + sys.executable.replace("'", "''") + "' '" + str(path).replace("'", "''") + "'"
        existing = next((entry for entry in bucket
                         if any(name in str(item.get("command", ""))
                                for item in entry.get("hooks", []))), None)
        if existing is None:
            entry = {"hooks": [handler]}
            if matcher:
                entry["matcher"] = matcher
            bucket.append(entry)
        else:
            _merge_hook(existing["hooks"], name, handler)
    if not dry:
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return ("would register" if dry else "registered") + " UserPromptSubmit and PreToolUse; review hooks in Codex before they run"


def register_gemini_hooks(repo: pathlib.Path, home: pathlib.Path, dry: bool) -> str:
    """Gemini CLI BeforeAgent context and BeforeTool shell guards, in milliseconds."""
    config = home / ".gemini" / "settings.json"
    data, error = _load_hook_file(config, dry)
    if error:
        return error
    hooks = data.setdefault("hooks", {})
    for name in ALL_HOOKS:
        path = repo / "scripts" / "hooks" / f"{name}.py"
        if not path.is_file():
            return "skipped, hooks missing"
        pipeline = name == "skill_pipeline"
        event = "BeforeAgent" if pipeline else "BeforeTool"
        command = hook_command(path) + (" --gemini" if pipeline else "")
        handler = {"type": "command", "name": f"master-repo-{name}",
                   "command": command, "timeout": 15000}
        bucket = hooks.setdefault(event, [])
        existing = next((entry for entry in bucket if any(
            name in str(item.get("command", "")) for item in entry.get("hooks", []))), None)
        if existing is None:
            entry = {"hooks": [handler]}
            if not pipeline:
                entry["matcher"] = "run_shell_command"
            bucket.append(entry)
        else:
            _merge_hook(existing["hooks"], name, handler)
    if not dry:
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return ("would register" if dry else "registered") + " BeforeAgent and BeforeTool"


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Master Repo auto mode.")
    parser.add_argument("--repo", default=str(pathlib.Path(__file__).resolve().parents[1]))
    parser.add_argument("--home", default=str(pathlib.Path.home()))
    parser.add_argument("--client", default="all", choices=("all", "claude", "codex", "gemini", "copilot", "antigravity", "cursor"))
    parser.add_argument("--no-hook", action="store_true", help="skip all lifecycle hooks")
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    args = parser.parse_args()

    repo = pathlib.Path(args.repo).expanduser().resolve()
    home = pathlib.Path(args.home).expanduser()
    dry = args.dry_run
    def selected(key: str) -> bool:
        return args.client == "all" or args.client == key or (args.client == "antigravity" and key == "gemini")

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
        if selected(CLIENT_KEYS[client]):
            print(f"skills   : {client:<12} {install_skill(repo, home, dry, root)}")
    failed = False
    if not args.no_hook:
        for key, register in (("claude", register_hook), ("antigravity", register_antigravity_hook),
                              ("cursor", register_cursor_hooks), ("copilot", register_copilot_hooks),
                              ("codex", register_codex_hooks), ("gemini", register_gemini_hooks)):
            if selected(key):
                result = register(repo, home, dry)
                failed = failed or result.startswith(("REFUSED", "skipped"))
                print(f"{key} hook: {result}")
    for name, rel in CLIENTS.items():
        if selected(CLIENT_KEYS[name]):
            print(f"{name:<9}: {upsert_block(home / rel, body, dry)}  ({rel})")
    if selected("cursor"):
        cursor_rule = home / ".cursor" / "rules" / "master-repo-auto.mdc"
        print(f"Cursor   : {upsert_cursor_rule(cursor_rule, body, dry)}  (.cursor/rules/master-repo-auto.mdc)")

    cost = len(body.encode('utf-8'))
    print(f"\nPer-session cost of the always-loaded block: {cost} bytes, about {cost // 4} tokens.")
    print("Skill bodies stay discoverable and load when their descriptions match the task.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

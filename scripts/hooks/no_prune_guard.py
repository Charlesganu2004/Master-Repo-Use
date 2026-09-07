#!/usr/bin/env python3
"""Block deletion of skills, plugins, MCP servers and catalog entries.

Charles kept losing tools he had chosen on purpose. An instruction in a prompt
file only works while a model is reading it and paying attention; this runs as a
PreToolUse hook, outside the model context, so it costs no tokens per session and
does not depend on anything being remembered.

Scope is deliberately narrow. It fires only on a destructive verb aimed at a
protected path, and only when that verb is an instruction rather than data.
Everything else passes untouched, because a guard that blocks ordinary work gets
switched off within a day and then protects nothing.

Escape hatch: append '# APPROVED PRUNE' to the command. That is an explicit,
typed statement of intent, which is the bar the policy asks for.
"""
from __future__ import annotations

import json
import re
import sys

OVERRIDE = "# APPROVED PRUNE"

# Paths whose contents were chosen deliberately and must not vanish silently.
PROTECTED = (
    ".claude/skills", ".claude/plugins", ".claude/settings.json",
    ".claude/agents", ".claude/commands", ".claude.json",
    ".codex/", ".gemini/", ".copilot/",
    ".mcp.json", "mcp.json",
    "repo-lists/", "docs/auto-mode-block.txt",
    "skills/", "AGENTS.md", "CLAUDE.md", "GEMINI.md",
    # The guards themselves, and the standing pipeline. Charles asked for the
    # pipeline to be a rule that cannot be deleted, and a guard that protects
    # every capability except its own source is one `rm` from protecting
    # nothing. hooks.json is Antigravity's registration of the same pipeline.
    "scripts/hooks/", "hooks.json",
)

# Destructive verbs, anchored so 'formatter' never matches 'rm'.
DESTRUCTIVE = re.compile(
    r"(?:^|[|;&]|\s)(?:"
    r"rm|rmdir|unlink|shred|srm"
    r"|del|erase"
    r"|Remove-Item|ri|rd"
    r"|git\s+rm"
    r"|npm\s+uninstall|pip\s+uninstall"
    r"|claude\s+(?:plugin|mcp)\s+(?:remove|uninstall|disable)"
    r")(?:\s|$)",
    re.IGNORECASE,
)

# Only unambiguous truncation verbs. A plain '>' redirect is deliberately left
# alone: it is overwhelmingly used to WRITE these files, so blocking it makes
# ordinary authoring impossible while protecting nothing, given that the Write
# and Edit tools never route through this hook at all.
TRUNCATING = re.compile(r"(?:^|[|;&]|\s)(?:truncate\b|Clear-Content\b)", re.IGNORECASE)

HEREDOC_START = re.compile(r"<<-?\s*(?P<quote>['\"]?)(?P<tag>\w+)(?P=quote)")
SINGLE_QUOTED = re.compile(r"'[^']*'")


def strip_heredocs(command: str) -> str:
    """Remove heredoc bodies, keeping the command line that introduced them.

    Written as a line scan rather than one multiline regex because the regex
    form needs backreferences, and those kept collapsing into control characters
    while being written through nested shell and Python escaping.
    """
    out: list[str] = []
    lines = command.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        out.append(line)
        match = HEREDOC_START.search(line)
        index += 1
        if not match:
            continue
        tag = match.group("tag")
        while index < len(lines) and lines[index].strip() != tag:
            index += 1  # body is data, drop it
        index += 1  # drop the terminator too
    return "\n".join(out)


def executable_part(command: str) -> str:
    """Strip content that is data rather than instruction.

    Writing a file whose text mentions a deletion is not a deletion, and a guard
    that cannot tell the difference blocks the work of documenting itself. This
    hook blocked its own bug fix before this function existed.

    Heredoc bodies and single-quoted literals are inert in shell, so both go
    before matching. Double-quoted text stays, because real deletion targets are
    commonly written as "$HOME/.claude/skills".
    """
    return SINGLE_QUOTED.sub(" ", strip_heredocs(command))


def protected_hits(command: str) -> list[str]:
    normalised = command.replace("\\", "/")
    return [p for p in PROTECTED if p.replace("\\", "/") in normalised]


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0  # never break a session over a malformed event

    if event.get("tool_name") != "Bash":
        return 0

    command = str((event.get("tool_input") or {}).get("command") or "")
    if not command or OVERRIDE in command:
        return 0

    scanned = executable_part(command)
    if not (DESTRUCTIVE.search(scanned) or TRUNCATING.search(scanned)):
        return 0

    hits = protected_hits(scanned)
    if not hits:
        return 0

    sys.stderr.write(
        "Blocked by the Master Repo no-prune guard.\n\n"
        f"This command would delete a protected path: {', '.join(sorted(set(hits)))}\n\n"
        "Skills, plugins, MCP servers, agents and catalog entries were chosen "
        "deliberately and are not removed on a model's initiative. Ask Charles "
        "whether he wants it gone.\n\n"
        "If he already said so, re-run with '# APPROVED PRUNE' appended.\n"
    )
    return 2  # exit 2 blocks the call and shows stderr to the model


if __name__ == "__main__":
    sys.exit(main())

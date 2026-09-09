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
    ".codex/", ".gemini/", ".copilot/", ".cursor/", ".github/hooks/",
    ".mcp.json", "mcp.json",
    "repo-lists/", "docs/auto-mode-block.txt",
    "skills/", "AGENTS.md", "CLAUDE.md", "GEMINI.md",
    # The guards themselves, and the standing pipeline. Charles asked for the
    # pipeline to be a rule that cannot be deleted, and a guard that protects
    # every capability except its own source is one `rm` from protecting
    # nothing. hooks.json is Antigravity's registration of the same pipeline.
    "scripts/hooks/", "scripts/auto_mode_harness.py", "hooks.json",
    # The source poller and the job that runs it. Charles asked for agentskill.sh
    # to be monitored and scanned regularly; monitoring that can be deleted
    # without a word is monitoring that quietly stops, and the failure mode is
    # silence rather than an error.
    "scripts/watch_sources.py", "watch-sources.yml",
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
QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
DASH_C = re.compile(r"-c\s*$")


# Every client sends a different shape for "a tool is about to run", and a guard
# that reads only one shape silently passes everything on the others. Checked
# against vendor documentation on 2026-09-08:
#
#   Claude Code   PreToolUse             tool_name / tool_input.command
#   Cursor        preToolUse             tool_name / tool_input.command, exit 2 denies
#   Cursor        beforeShellExecution   command at the top level, no tool name
#   Gemini CLI    PreToolUse             tool_name / tool_input.command
#   Copilot CLI   preToolUse             toolName  / toolArgs
#
# Copilot was the one that differed, and it differed in the direction that costs
# nothing to notice: tool_name is simply absent, so the guard returned 0 and
# every rm and every compressor ran unguarded under Copilot.
#
# Duplicated in both guards rather than imported. A hook script has to be
# self-contained: an ImportError here exits non-zero, and a non-zero exit from a
# PreToolUse hook BLOCKS the call, so a shared module that fails to resolve would
# not degrade the guard, it would wedge the session.
_SHELL_TOOLS = {
    "bash", "shell", "runshellcommand", "terminal", "execute",
    "runcommand", "shellexecution", "beforeshellexecution", "run",
}


def shell_command(event: dict) -> str:
    """The shell command this event would run, or "" if it is not a shell event."""
    name = event.get("tool_name") or event.get("toolName") or ""
    args = event.get("tool_input")
    if not isinstance(args, dict):
        args = event.get("toolArgs")
    if not isinstance(args, dict):
        args = {}

    command = args.get("command") or args.get("cmd") or event.get("command") or ""
    if not isinstance(command, str) or not command:
        return ""

    # Cursor's beforeShellExecution carries the command at the top level and
    # sends no tool name, so the command itself identifies the event.
    if not name:
        return command
    flat = str(name).replace("-", "").replace("_", "").lower()
    return command if flat in _SHELL_TOOLS else ""


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

    One quoted span is not inert: the body of `-c`, which is a command. Dropping
    it, which is what this did before, meant `sh -c 'rm -rf ~/.claude/skills'`
    walked past the guard entirely, and `bash -c "rm -rf skills/"` did too.

    A kept `-c` body is UNWRAPPED rather than left in its quotes. The verbs are
    anchored on a chain character or whitespace, so a verb sitting directly
    behind a quote would not match; adding the quote to those anchors instead
    was tried and blocked `grep -n "rm skills/" notes.md`, since real deletion
    targets are commonly written double-quoted and must stay matchable.
    """
    text = strip_heredocs(command)
    out, last = [], 0
    for match in QUOTED.finditer(text):
        before = text[last:match.start()]
        out.append(before)
        if DASH_C.search(before):
            out.append(" " + match.group(0)[1:-1] + " ")
        elif match.group(0).startswith('"'):
            out.append(match.group(0))   # double-quoted paths are real targets
        else:
            out.append(" ")              # single-quoted literals are inert
        last = match.end()
    out.append(text[last:])
    return "".join(out)


def protected_hits(command: str) -> list[str]:
    normalised = command.replace("\\", "/")
    return [p for p in PROTECTED if p.replace("\\", "/") in normalised]


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0  # never break a session over a malformed event

    command = shell_command(event)
    if not command or OVERRIDE in command:
        return 0

    scanned = executable_part(command)
    if not (DESTRUCTIVE.search(scanned) or TRUNCATING.search(scanned)):
        return 0

    # The verb is checked on executable text, but quoted paths are real targets.
    hits = protected_hits(strip_heredocs(command))
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

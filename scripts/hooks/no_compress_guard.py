#!/usr/bin/env python3
"""Refuse to compress or truncate a NO-COMPRESS protected block.

The rules that make auto mode work are the first thing a compression pass
deletes, because they read like boilerplate. Charles asked for them to be
mandatory and never compressed, so this enforces the second half of that
outside the model: an instruction that says "do not compress me" only holds
while something is reading it, and a compression pass is exactly the moment
nothing is.

Scope is narrow on purpose. It fires when a command would rewrite a file that
carries the markers, and only when that rewrite is a compression. Ordinary edits
that keep the block intact pass, because a guard that blocks normal authoring
gets switched off and then protects nothing.

Escape hatch: append '# APPROVED RECOMPRESS'. That is a typed statement of
intent, which is the bar the policy asks for.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

OVERRIDE = "# APPROVED RECOMPRESS"
BEGIN = "<!-- NO-COMPRESS:BEGIN -->"
END = "<!-- NO-COMPRESS:END -->"

# A verb only counts in COMMAND position: at the start, after a chaining
# operator, or behind an interpreter that runs it.
#
# The first version matched the token anywhere in the command, and that refused
#   head -5 ~/.claude/skills/caveman-ultra-compact/SKILL.md
# because "caveman" appears in a directory name being READ. Reading a capability
# definition has never been the risk, and the guard already has a test saying so.
# It is the same class of mistake as the redirect one below: a name appearing as
# an argument is not the tool being run.
_CHAIN = r"(?:^|[|;&(`]|&&|\|\|)"
# Ways a compressor is actually launched. Anything not on this list has to be in
# bare command position, which is what an invocation looks like.
_LAUNCHER = (r"(?:sudo\s+|\w+=\S+\s+)*"
             r"(?:(?:python3?|py)\s+-m\s+"
             # `python compress.py ...` - the script IS the compressor, so the
             # name still has to follow immediately for this to match.
             r"|(?:python3?|py)\s+"
             r"|npx\s+(?:-y\s+)?|uvx\s+|pipx\s+run\s+"
             r"|node\s+|bash\s+-c\s+|sh\s+-c\s+)?"
             # `sh -c 'llmlingua ...'` puts a quote between the launcher and the
             # tool. executable_part now keeps a `-c` body precisely so it can be
             # scanned, and without this the quote it kept blocked the match.
             r"['\"]?")
_COMPRESSOR_NAMES = (r"caveman[\w-]*"
                     r"|token-compact|compress\.py"
                     r"|llmlingua|LLMLingua"
                     r"|headroom"
                     r"|rtt|reducethemtokens")

# Tools whose whole purpose is to make a file smaller.
COMPRESSORS = re.compile(
    _CHAIN + r"\s*" + _LAUNCHER + r"(?:" + _COMPRESSOR_NAMES + r")\b",
    re.IGNORECASE,
)

# Truncating writes. A plain '>' is included here, unlike the no-prune guard,
# because rewriting a protected file wholesale is precisely the risk. Same
# command-position rule, for the same reason: a path containing the word
# "truncate" is not a truncation.
TRUNCATING = re.compile(
    _CHAIN + r"\s*" + _LAUNCHER + r"(?:truncate|Clear-Content)\b",
    re.IGNORECASE,
)

# A redirect only truncates what it points AT. The first version matched any '>'
# anywhere in a command that also happened to mention a protected filename, so
# `python security_trail.py --scope "...SECURITY-TRAIL.md..." >/dev/null` was
# refused: the redirect went to /dev/null and the filename was an argument.
# Blocking a tool from writing its own audit row is the opposite of the point.
REDIRECT_TARGET = re.compile(r">>?\s*(\"[^\"]*\"|'[^']*'|[^\s|;&>]+)")


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


def redirect_targets(command: str) -> list[str]:
    """Only the paths a redirect actually writes to."""
    return [m.group(1).strip("\"'").replace("\\", "/") for m in REDIRECT_TARGET.finditer(command)]

HEREDOC_START = re.compile(r"<<-?\s*(?P<quote>['\"]?)(?P<tag>\w+)(?P=quote)")
QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
DASH_C = re.compile(r"-c\s*$")


# Capability definitions. A skill, MCP server, tool or agent that has been
# summarised is a capability that quietly stopped working: the description a
# client matches against is gone, or the parameters it needs are. These are
# protected by path rather than by a marker, because they are not files anyone
# thinks to annotate, and because a compressed SKILL.md fails silently.
CAPABILITY_PATTERNS = (
    "SKILL.md",           # skills, wherever they live
    ".mcp.json", "mcp.json", "mcp_servers.json",
    "settings.json", "settings.local.json",
    "AGENTS.md", "CLAUDE.md", "GEMINI.md",
    "copilot-instructions.md", "master-repo-auto.mdc", "master-repo-auto.json",
    "installed_plugins.json", "known_marketplaces.json",
    # Antigravity registers the standing pipeline here, the way settings.json
    # does for Claude Code.
    "hooks.json",
    # The source poller. Compressing it out is the same loss as deleting it:
    # the monitoring stops and nothing says so.
    "watch_sources.py", "watch-sources.yml", "auto_mode_harness.py",
)
# scripts/hooks/ holds the guards and the standing pipeline. Compressing the
# pipeline is the one edit that would silently switch every rule off while
# leaving a file that still looks present, so it is protected by the same
# mechanism it enforces.
CAPABILITY_DIRS = (".claude/skills", ".claude/agents", ".claude/commands",
                   ".claude/plugins", ".cursor/skills", ".copilot/skills",
                   ".github/hooks/", "skills/", "agents/", "scripts/hooks/")


def is_capability_path(text: str) -> list[str]:
    """Names in a command that point at a capability definition."""
    normalised = text.replace("\\", "/")
    hits = [name for name in CAPABILITY_PATTERNS if name in normalised]
    hits += [d for d in CAPABILITY_DIRS if d in normalised]
    return sorted(set(hits))


def protected_files(root: pathlib.Path) -> list[pathlib.Path]:
    """Every tracked text file that actually carries the markers."""
    found = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".txt", ".md", ".json"}:
            continue
        if ".git" in path.parts or "_site" in path.parts or "node_modules" in path.parts:
            continue
        try:
            if BEGIN in path.read_text(encoding="utf-8", errors="ignore"):
                found.append(path)
        except OSError:
            continue
    return found


def strip_heredocs(command: str) -> str:
    """Drop heredoc bodies: writing text that mentions a tool is not running it."""
    out, lines, index = [], command.splitlines(), 0
    while index < len(lines):
        line = lines[index]
        out.append(line)
        match = HEREDOC_START.search(line)
        index += 1
        if not match:
            continue
        tag = match.group("tag")
        while index < len(lines) and lines[index].strip() != tag:
            index += 1
        index += 1
    return "\n".join(out)


def executable_part(command: str) -> str:
    """Drop quoted spans, which are arguments, and keep the one kind that is not.

    `grep "llmlingua" file` searches for a word. `bash -c "llmlingua file"` runs
    one. So a quoted span is dropped unless `-c` immediately precedes it, where
    the quotes hold the command itself.

    Two bugs fixed here at once, both found by the guard misfiring on this
    session's own commands. Only single quotes were stripped, so a double-quoted
    grep alternation containing "\\|llmlingua" read as a pipe into a compressor
    and blocked a read. And single quotes were stripped unconditionally, so
    `sh -c 'llmlingua ~/.claude/skills/x/SKILL.md'` walked straight past.
    """
    text = strip_heredocs(command)
    out, last = [], 0
    for match in QUOTED.finditer(text):
        before = text[last:match.start()]
        out.append(before)
        out.append(match.group(0) if DASH_C.search(before) else " ")
        last = match.end()
    out.append(text[last:])
    return "".join(out)


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0   # never break a session over a malformed event

    command = shell_command(event)
    if not command or OVERRIDE in command:
        return 0

    scanned = executable_part(command)
    compressing = COMPRESSORS.search(scanned)
    truncating = TRUNCATING.search(scanned)
    # Detect the operator on executable text, but retain quoted destination paths.
    targets = redirect_targets(strip_heredocs(command)) if ">" in scanned else []
    # Obvious interpreter truncations need no subprocess named 'truncate'. This
    # is intentionally not a general Python sandbox: alternate APIs still need
    # the host's permissions and code-review boundary.
    python_body = re.search(r"(?:^|[;&|])\s*(?:python3?|py)\s+-c\s", scanned)
    if python_body:
        targets += [m.group(2) for m in re.finditer(
            r"\bopen\(\s*(['\"])(.*?)\1\s*,\s*(?:mode\s*=\s*)?['\"]w[bt+]*['\"]", scanned)]
        targets += [m.group(2) for m in re.finditer(
            r"\bPath\(\s*(['\"])(.*?)\1\s*\)\.(?:write_text|write_bytes)\(", scanned)]

    if not (compressing or truncating or targets):
        return 0

    verb = "compress" if compressing else "truncate"

    # What gets matched depends on what fired, or the guard blocks a filename
    # merely being an argument.
    #
    #   compressor or truncate verb -> the whole command, because those tools take
    #                                  the file as an argument
    #   a redirect alone            -> only what the redirect points at
    #
    # Without this split, `security_trail.py --scope "...SECURITY-TRAIL.md..."
    # >/dev/null` was refused, which blocked the audit tool from writing its own
    # row. A guard that stops the logging is worse than no guard.
    suspect = strip_heredocs(command) if (compressing or truncating) else " ".join(targets)

    # Capability definitions first: they are protected by path, so this catches
    # a SKILL.md or an MCP config even in a repository that has no marked block.
    capability_hits = is_capability_path(suspect)
    if capability_hits:
        sys.stderr.write(
            "Blocked by the Master Repo no-compress guard.\n\n"
            f"This command would {verb} a capability definition: {', '.join(capability_hits)}\n\n"
            "Skills, MCP servers, tools and agents are never compressed. A summarised\n"
            "SKILL.md or MCP config fails silently: the description a client matches\n"
            "against is gone, or the parameters it needs are, and the capability simply\n"
            "stops being selected. Nothing errors, so nobody notices.\n\n"
            "Compress prose instead, or edit the definition in a way that keeps it whole.\n"
            "If Charles asked for it explicitly, re-run with '# APPROVED RECOMPRESS'.\n"
        )
        return 2

    root = pathlib.Path(event.get("cwd") or ".")
    names = {p.name for p in protected_files(root)}
    if not names:
        return 0

    normalised = suspect.replace("\\", "/")
    hits = sorted(n for n in names if n in normalised)
    if not hits:
        return 0

    sys.stderr.write(
        "Blocked by the Master Repo no-compress guard.\n\n"
        f"This command would {verb} a file carrying a NO-COMPRESS block: {', '.join(hits)}\n\n"
        "That block holds the mandatory auto-mode rules. They are exempt from every\n"
        "compression pass by design, because rules that only survive when context is\n"
        "roomy are not rules. Compress a different file, or edit this one in a way that\n"
        "leaves the protected block byte-for-byte intact.\n\n"
        "If Charles asked for it explicitly, re-run with '# APPROVED RECOMPRESS' appended.\n"
    )
    return 2   # exit 2 blocks the call and shows stderr to the model


if __name__ == "__main__":
    sys.exit(main())

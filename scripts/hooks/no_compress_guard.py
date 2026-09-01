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

# Tools whose whole purpose is to make a file smaller.
COMPRESSORS = re.compile(
    r"(?:^|[|;&]|\s)(?:"
    r"caveman[\w-]*"
    r"|token-compact|compress\.py"
    r"|llmlingua|LLMLingua"
    r"|headroom"
    r"|rtt|reducethemtokens"
    r")\b",
    re.IGNORECASE,
)

# Truncating writes. A plain '>' is included here, unlike the no-prune guard,
# because rewriting a protected file wholesale is precisely the risk.
TRUNCATING = re.compile(r"(?:^|[|;&]|\s)(?:truncate\b|Clear-Content\b|>\s*\S)", re.IGNORECASE)

HEREDOC_START = re.compile(r"<<-?\s*(?P<quote>['\"]?)(?P<tag>\w+)(?P=quote)")
SINGLE_QUOTED = re.compile(r"'[^']*'")


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
    return SINGLE_QUOTED.sub(" ", strip_heredocs(command))


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0   # never break a session over a malformed event

    if event.get("tool_name") != "Bash":
        return 0

    command = str((event.get("tool_input") or {}).get("command") or "")
    if not command or OVERRIDE in command:
        return 0

    scanned = executable_part(command)
    compressing = COMPRESSORS.search(scanned)
    truncating = TRUNCATING.search(scanned)
    if not (compressing or truncating):
        return 0

    root = pathlib.Path(event.get("cwd") or ".")
    names = {p.name for p in protected_files(root)}
    if not names:
        return 0

    normalised = scanned.replace("\\", "/")
    hits = sorted(n for n in names if n in normalised)
    if not hits:
        return 0

    verb = "compress" if compressing else "truncate"
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

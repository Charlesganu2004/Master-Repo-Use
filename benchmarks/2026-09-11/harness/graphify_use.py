"""Did a shell command actually invoke graphify?

Written once and shared, because getting it wrong changes a reported number.
Two earlier versions did: one counted the bare word, so a grep that EXCLUDED the
graph directory (-g '!graphify-out/**') was scored as using it; the next matched
only `graphify.exe`, so calls through the Windows `graphify.CMD` shim were scored
as not using it. A match now needs the program name, optionally with a path and
an extension, followed by one of its real subcommands.
"""
from __future__ import annotations

import re

SUBCOMMANDS = (
    "query", "path", "explain", "affected", "god-nodes", "extract", "update", "global",
    "tree", "export", "benchmark", "install", "watch", "cluster-only", "diagnose",
    "recover", "reflect", "save-result", "merge-graphs", "clone", "add", "prs",
    "check-update", "hook", "uninstall", "label", "provider",
)

BOUNDARY = r"(?:^|[\s;&|(=`\"'])"          # start, whitespace, or a shell separator or quote
DIRECTORY = r"(?:[^\s;&|\"']*[\\/])?"      # an optional leading path, either slash
PROGRAM = r"graphify(?:\.(?:exe|cmd|bat|ps1))?"
CLOSING = r"[\"']?\s+"
PATTERN = BOUNDARY + DIRECTORY + PROGRAM + CLOSING + "(?:" + "|".join(SUBCOMMANDS) + r")\b"
INVOKES_GRAPHIFY = re.compile(PATTERN, re.IGNORECASE)


def invocations(commands) -> int:
    """How many of these shell commands actually ran graphify."""
    return sum(1 for command in commands if INVOKES_GRAPHIFY.search(command or ""))

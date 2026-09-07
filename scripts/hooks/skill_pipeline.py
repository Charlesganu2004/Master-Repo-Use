#!/usr/bin/env python3
"""Make the standing pipeline fire on every prompt, with no slash command.

The question this answers: why does using a skill require typing `/name`?

It does not, and that is the whole point of this file. Claude Code has two
separate mechanisms and they are easy to confuse:

  1. A slash command is EXPLICIT invocation. You type it, it runs, every time.
  2. Skills are also model-invocable: the client shows the model a list of skill
     names and descriptions, and the model calls one when the description
     matches the task.

Mechanism 2 is automatic but it is a JUDGEMENT. The model decides. That is fine
for "use the pdf skill when there is a pdf" and useless for "always run these
four first", because the one time it matters is the time the model does not
think to look.

This hook is mechanism 3, and it is the only deterministic one. UserPromptSubmit
fires on EVERY prompt before the model reads it, and its `additionalContext` is
injected into that turn. Nothing is left to judgement: the rule arrives with the
prompt whether the model would have thought of it or not.

COST, because this is charged on every single turn of every session forever.
The core block below is deliberately short, and the conditional lines only
attach when the prompt actually looks like that kind of work. An unconditional
dump of every rule would be a few hundred tokens per turn, permanently, and
would be exactly the kind of always-loaded bloat that docs/auto-mode-block.txt
already has a budget test for.

Exit codes: 0 always. A hook that fails closed on a malformed event would make
the session unusable, and this one is advisory rather than a guard.
"""
from __future__ import annotations

import json
import re
import sys

# Always. Four rules, one line each, because this rides on every prompt.
CORE = """Standing pipeline for this turn, before anything else:
1. Compress repeatedly-loaded prose with the caveman skills; route commands through rtk. Retrieve matching entries only, never a whole catalog or file tree.
2. Never compact a skill, tool, agent, plugin, MCP server or catalog entry. Global, every conversation and every command. Only Charles asking in that message lifts it.
3. Full output. No "rest of code", no "similar to above", no skeleton where an implementation was asked for. If you run out of room, stop at a clean break and say what remains.
4. Verify before claiming. Run the check, quote the real output, and report a failure first."""

# Conditional. Each costs nothing on the turns it does not apply to.
#
# Every term is a PREFIX and the trailing \w* is what makes that true. The first
# version wrote \b(vulnerab)\b, which never matches "vulnerability" because \b
# demands a word boundary straight after the prefix. Most terms in every lane
# were dead and the lanes only ever fired on the handful of whole words. Caught
# by a test that expected a security prompt to pick the security lane.
#
# Security is declared first so it also wins an honest tie: of the four, it is
# the one where getting the wrong rule matters most.
LANES = (
    (r"\b(secur|vulnerab|exploit|secret|credential|token|auth|malware|scan|"
     r"inject|breach|leak)\w*",
     "5. Security-relevant: findings need evidence that can be quoted. A pattern match is a reason to look, never a reason to delete."),

    (r"\b(ui|ux|design|css|html|page|site|website|layout|theme|palette|"
     r"typograph|figma|landing|frontend|front-end|visual|mockup|style)\w*",
     "5. UI work: load the design taste skills before writing markup, and state the design read and the dials first. Anti-slop rules apply: no em dashes anywhere, one theme per page, one accent, one radius scale."),

    (r"\b(install|clone|dependenc|package|npm|pip|repositor|third.?party|"
     r"skill pack|marketplace|mcp server)\w*",
     "5. Adding anything third-party: run the dep-audit path first. Catalogued is not vetted, and scripts/install_catalog_skill.py is the reviewed route into a skill root."),

    (r"\b(pricing|version|latest|current|today|release|changelog|"
     r"model name|quota)\w*",
     "5. This asks for something that changes: retrieve it, do not recall it. Cite what you read."),
)

ORCHESTRATION = ("6. More than about three independent pieces of work here: fan them out, "
                 "then verify the results adversarially rather than trusting the first pass.")

# A prompt long enough to hold several asks usually does.
MULTI_TASK = re.compile(r"\balso\b|\band then\b|\bafter that\b|\bplus\b|^\s*\d[\).]", re.I | re.M)


def context_for(prompt: str) -> str:
    """The core, plus at most one lane, plus fan-out advice on a big prompt.

    The lane is chosen by how MANY distinct terms it matched, not by declaration
    order. Taking the first match was wrong in a way a test caught: "scan this
    repo for a vulnerability" hit the dependency lane on the single word "repo"
    and never reached the security lane, which matched two terms and was the one
    that mattered. Declaration order survives only as the tie-break.
    """
    lowered = prompt.lower()
    parts = [CORE]
    best, best_score = None, 0
    for pattern, line in LANES:
        score = len(set(re.findall(pattern, lowered)))
        if score > best_score:
            best, best_score = line, score
    if best:
        parts.append(best)   # one lane only; stacking them defeats the budget
    if len(prompt) > 600 or len(MULTI_TASK.findall(prompt)) >= 2:
        parts.append(ORCHESTRATION)
    return "\n".join(parts)


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0                      # never break a session over a bad event

    prompt = ""
    for holder in (event.get("input"), event):
        if isinstance(holder, dict) and isinstance(holder.get("prompt"), str):
            prompt = holder["prompt"]
            break
    if not prompt.strip():
        return 0

    # An explicit slash command is already an explicit instruction. Injecting the
    # standing pipeline on top of it is noise, and worse, it competes with the
    # skill the user just named.
    if prompt.lstrip().startswith("/"):
        return 0

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context_for(prompt),
        }
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
first", because the one time it matters is the time the model does not think to
look.

This hook is mechanism 3, and it is the only deterministic one. UserPromptSubmit
fires on EVERY prompt before the model reads it, and its `additionalContext` is
injected into that turn. Nothing is left to judgement: the rule arrives with the
prompt whether the model would have thought of it or not.

COST, stated because it is real and was accepted rather than hidden. This rides
on every turn of every session forever. Seven mandatory rules is about 1.2 kB,
call it 290 tokens per prompt. Charles asked for plan, caveman, design,
anti-slop and full-output to fire on every prompt and conversation across chat,
cowork and code, was told the price, and confirmed. So the core is unconditional
and the budget test tracks the number rather than arguing with the decision.
The four LANES stay conditional on top of it, because a lane that fires on a
prompt it does not fit is noise rather than enforcement.

Slash commands get the pipeline too. An earlier version skipped them on the
reasoning that the user had already named what they wanted, which was wrong for
this repository: "every command has this too" was the instruction, and a
/command is exactly where a design or full-output rule most needs to hold.

Exit codes: 0 always. A hook that fails closed on a malformed event would make
the session unusable, and this one is advisory rather than a guard.
"""
from __future__ import annotations

import json
import re
import sys

# MANDATORY, every prompt, no condition. Charles asked for these five to run on
# every prompt and conversation across chat, cowork and code, was told what the
# per-turn cost of that is, and confirmed. So they are unconditional and the
# budget test below tracks the price rather than arguing with it.
CORE = """Standing pipeline. Run these before anything else, every prompt, no exceptions:
1. PLAN first. State the read and the approach before producing anything. On more than a couple of steps, write the plan down and work it.
2. CAVEMAN. Compress repeatedly-loaded prose with the caveman skills; route commands through rtk. Retrieve matching entries only, never a whole catalog, file tree or log.
3. DESIGN. Any user-visible output goes through the design taste skills: state the design read and the dials, then build.
4. ANTI-SLOP. No em dashes anywhere. One theme, one accent, one radius scale per surface. No AI-purple, no three-equal-cards, no generic names, no invented precision, no filler verbs, no fake screenshots.
5. FULL OUTPUT. No "rest of code", no "similar to above", no skeleton where an implementation was asked for. Out of room means stop at a clean break and say exactly what remains.
6. NEVER COMPACT a skill, tool, agent, plugin, MCP server or catalog entry. Global, every conversation and every command. Only Charles asking in that message lifts it.
7. VERIFY before claiming. Run the check, quote the real output, report a failure first."""

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
     "8. Security-relevant: findings need evidence that can be quoted. A pattern match is a reason to look, never a reason to delete."),

    (r"\b(ui|ux|design|css|html|page|site|website|layout|theme|palette|"
     r"typograph|figma|landing|frontend|front-end|visual|mockup|style)\w*",
     "8. UI work specifically: audit the existing surface before replacing it, and name the aesthetic family you are reaching for rather than defaulting."),

    (r"\b(install|clone|dependenc|package|npm|pip|repositor|third.?party|"
     r"skill pack|marketplace|mcp server)\w*",
     "8. Adding anything third-party: run the dep-audit path first. Catalogued is not vetted, and scripts/install_catalog_skill.py is the reviewed route into a skill root."),

    (r"\b(pricing|version|latest|current|today|release|changelog|"
     r"model name|quota)\w*",
     "8. This asks for something that changes: retrieve it, do not recall it. Cite what you read."),
)

ORCHESTRATION = ("9. More than about three independent pieces of work here: fan them out, "
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


def find_prompt(event: dict) -> str:
    """The user's text, wherever this client happens to put it.

    Claude Code nests it under `input`. Antigravity's PreInvocation payload is a
    trajectory rather than a single prompt, so the last user message is the
    closest equivalent. Neither shape is guessed at: both are read, and anything
    unrecognised yields an empty string and a silent no-op.
    """
    for holder in (event.get("input"), event):
        if isinstance(holder, dict) and isinstance(holder.get("prompt"), str):
            return holder["prompt"]
    messages = event.get("messages") or event.get("trajectory")
    if isinstance(messages, list):
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                content = message.get("content")
                if isinstance(content, str):
                    return content
                if isinstance(content, list):        # content-part arrays
                    return " ".join(part.get("text", "") for part in content
                                    if isinstance(part, dict))
    return ""


def main() -> int:
    # One source for the rules, two output shapes. Writing the pipeline into a
    # second file for Antigravity would guarantee the two drift, and the whole
    # point is that every client gets the SAME standing rules.
    antigravity = "--antigravity" in sys.argv

    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0                      # never break a session over a bad event

    prompt = find_prompt(event)
    if not prompt.strip():
        return 0
    context = context_for(prompt)

    if antigravity:
        # PreInvocation fires before the model is called. ephemeralMessage is the
        # right slot: it reaches the model for this invocation without being
        # recorded as something the user said.
        print(json.dumps({"injectSteps": [{"ephemeralMessage": context}]}))
    else:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context,
            }
        }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

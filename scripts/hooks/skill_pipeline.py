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

THREE LAYERS, not a list. Charles asked for it in this shape and the shape is
the point:

  layer 1, before the request is read   caveman, full output, anti-slop
  layer 2, before anything is produced  plan, design
  layer 3, while acting and at the end  capabilities, agents, THEN layer 1 again

Layer 3 repeating layer 1 is deliberate. A rule read once at the top of a long
turn has stopped applying by the end of it, and the end is exactly where the
skeleton and the em dash get written.

Layer 3 also forces capability selection rather than leaving it to notice:
whatever skills, tools, plugins and MCP servers fit the task get picked and
named. That is the difference between having a catalog and using one.

COST, stated because it is real and was accepted rather than hidden. This rides
on every turn of every session forever, roughly 1.6 kB or 400 tokens a prompt.
Charles was told the price and asked for it anyway, so the budget test tracks
the number rather than arguing with the decision. The four LANES stay
conditional on top, because a lane firing on a prompt it does not fit is noise
rather than enforcement.

IT CANNOT BE DELETED. scripts/hooks/ is protected by both guards, so this file
cannot be removed, truncated or compressed without the explicit override. A
guard that protects every capability except its own source is one command from
protecting nothing.

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

# MANDATORY, every prompt, no condition, no slash. Charles asked for this as
# LAYERS rather than a list: one pass before reading the request, one before
# producing anything, and a third while acting that RE-APPLIES the first.
#
# The repetition in layer 3 is deliberate and was asked for. A rule read once at
# the top of a long turn has stopped applying by the end of it, which is exactly
# where the skeleton and the em dash get written.
CORE = """Standing pipeline. Three layers, every prompt and every command, no slash and no exception.

LAYER 1, before reading the request:
1. CAVEMAN. Compress repeatedly-loaded prose with the caveman skills; route commands through rtk. Retrieve matching entries only, never a whole catalog, file tree or log.
2. FULL OUTPUT. No "rest of code", no "similar to above", no skeleton where an implementation was asked for. Out of room means stop at a clean break and say exactly what remains.
3. ANTI-SLOP. No em dashes. One theme, one accent, one radius scale per surface. No AI-purple, no three-equal-cards, no generic names, no invented precision, no filler verbs, no fake screenshots.

LAYER 2, before producing anything:
4. PLAN. State the read and the approach first. More than a couple of steps means write the plan down and work it.
5. DESIGN. Anything a person will see goes through the design taste skills: state the design read and the dials, then build.

LAYER 3, while acting and again before answering:
6. CAPABILITIES. Pick and apply whatever skills, tools, plugins and MCP servers fit this task. Do not ask when the catalog already answers it, and name what you picked.
7. AGENTS AND ACTIONS. Independent pieces of work fan out, then get verified adversarially rather than trusted on the first pass.
8. RE-APPLY LAYER 1 to what you produced: caveman, full output, anti-slop, again.
9. NEVER COMPACT a skill, tool, agent, plugin, MCP server or catalog entry. Global, every conversation and command. Only Charles asking in that message lifts it.
10. VERIFY. Run the check, quote real output, report a failure first."""

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
     "11. Security-relevant: findings need evidence that can be quoted. A pattern match is a reason to look, never a reason to delete."),

    (r"\b(ui|ux|design|css|html|page|site|website|layout|theme|palette|"
     r"typograph|figma|landing|frontend|front-end|visual|mockup|style)\w*",
     "11. UI work specifically: audit the existing surface before replacing it, and name the aesthetic family you are reaching for rather than defaulting."),

    (r"\b(install|clone|dependenc|package|npm|pip|repositor|third.?party|"
     r"skill pack|marketplace|mcp server)\w*",
     "11. Adding anything third-party: run the dep-audit path first. Catalogued is not vetted, and scripts/install_catalog_skill.py is the reviewed route into a skill root."),

    (r"\b(pricing|version|latest|current|today|release|changelog|"
     r"model name|quota)\w*",
     "11. This asks for something that changes: retrieve it, do not recall it. Cite what you read."),
)

ORCHESTRATION = ("12. More than about three independent pieces of work here: fan them out, "
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

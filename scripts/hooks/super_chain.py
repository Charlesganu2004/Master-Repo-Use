#!/usr/bin/env python3
"""The super harness chain: ten named passes on top of the three layers.

WHY THIS IS ITS OWN MODULE. The chain used to live in scripts/harness_super.py,
which imports every other harness so it can install, serve, wrap and route. That
is fine for a command and wrong for a per-prompt hook: skill_pipeline runs on
every prompt of every client, and making it import five harnesses to render ten
lines would put all of them on the hot path of every turn.

So the definition lives here, beside the hook, with no imports beyond the
standard library. The hook reads it when the machine is in super mode, and
harness_super re-exports it. There is still exactly one copy of the chain.

That split is also what makes the super harness automatic. Before it, the chain
reached a model only through `harness_super --run`, `--serve` or `--context`.
Every Claude Code, Codex, Gemini, Cursor and Copilot session ran the per-prompt
hook, and the hook had no idea the chain existed, so in those sessions the super
harness had never fired at all.
"""
from __future__ import annotations

# Each pass names the SKILL that carries it and, where the base pipeline already
# carries that rule, the RULE NUMBER instead of a second copy of the words.
#
# The first version wrote all ten rules out in full. It read well and it was
# wrong: seven of the ten already exist in skill_pipeline.CORE, so the chain was
# a second copy of most of the standing pipeline. Two copies of one rule is the
# drift this repository keeps paying for, and it cost 4.3 kB a prompt to carry.
#
# So a pass that extends the base points at it, and only a pass that adds
# something new spells the new thing out. All ten are still named, in the order
# Charles gave them, because the ORDER is the thing this harness contributes.
#
# (label, skill, base_rule or None, when, rule text when base_rule is None)
PASSES = (
    ("CAVEMAN", "master-caveman", 1, "before reading the request", ""),
    ("FULL OUTPUT", "master-full-output", 2, "before reading the request", ""),
    ("ANTI-SLOP", "master-anti-slop", 3, "before reading the request", ""),
    ("PLAN", "master-plan", 4, "before producing anything", ""),
    ("DESIGN", "master-design-taste", 5, "before producing anything", ""),

    ("ARCHITECT", "master-architect", None, "before producing anything",
     "If getting the shape wrong would mean a rewrite rather than an edit, decide the shape first. Name what each piece owns, which way the dependencies point, and where each piece of state lives exactly once. Sort decisions by what they cost to undo and deliberate only over the expensive ones."),

    ("REFACTOR", "master-refactor", 8, "on what you produced", ""),

    ("COMPRESS", "master-token-reducer", None, "throughout, not at the end",
     "Build a compact retrieval packet before loading detail, and measure the reduction. This is not a step at the end: compressing a finished answer is the least valuable place to do it, because the tokens were already spent getting there."),

    ("REVIEW", "master-review", None, "before answering",
     "Re-read the original request and count its deliverables against what you produced; name anything that shrank. Then read the work as an adversary: every claim either carries evidence or gets downgraded to what you know. Check the empty case, the error path and the second caller. Report a failure first."),

    ("VERIFY", "verify-before-complete", 11, "before answering", ""),
)

# The capabilities every super-harness session carries, beyond the enforced set
# the surface harness already installs.
EXTRA_SKILLS = ("master-architect", "master-review", "master-super-harness")

SUPER_BLOCK = """SUPER HARNESS. The chain above is the floor. These passes run on top of it, in this order, on every prompt and every command.

{passes}

TOKEN REDUCTION is not a step in this list even though it appears as one. It applies at every retrieval, every catalog read and every long output. Compressing a finished answer is the least valuable place to do it: the tokens were already spent getting there.

ARCHITECT is before producing and REVIEW is after, on purpose. A plan for the wrong shape builds the wrong thing efficiently, and the person best placed to find the defect is the one who just wrote it and already believes it is right.

NAME the skills, tools, plugins and MCP servers you used. A pass you did not name is a pass the reader cannot check. The full procedure for every pass is in the master-super-harness skill."""


def pass_lines() -> str:
    """The chain, as the model reads it.

    A pass that extends a base rule renders as a pointer to that rule. A pass
    that adds something renders its own text. Nothing is written twice.
    """
    lines = []
    for index, (label, skill, base_rule, when, rule) in enumerate(PASSES, start=1):
        body = f"rule {base_rule} above, applied here" if base_rule else rule
        lines.append(f"S{index}. {label} ({skill}), {when}: {body}")
    return "\n".join(lines)


def super_block() -> str:
    return SUPER_BLOCK.format(passes=pass_lines())

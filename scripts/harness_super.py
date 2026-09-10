#!/usr/bin/env python3
"""One harness that does what all four do, with a longer chain of passes.

WHY THIS EXISTS. The four injection harnesses each stand in a different place,
and where a harness stands decides what it can reach. That is a real distinction
and it is worth keeping. It is also four commands to learn, four checks to run,
and four chances to set a machine up most of the way.

This is the one command. It installs the surfaces, serves the proxy, wraps a
command, carries the standing goal and routes computer control, by CALLING the
four rather than reimplementing any of them. A fifth copy of the injection logic
would drift from the other four the first week it existed, and the whole point of
a shared pipeline is that there is one.

WHAT IS ACTUALLY NEW. The layer chain. The standing pipeline is three layers and
eleven rules, which is the floor for every prompt on every surface. This adds a
longer chain on top, in the order Charles named it:

    caveman -> full output -> anti-slop      the floor, unchanged
    plan -> design -> ARCHITECT              shape before sequence
    refactor -> caveman compress -> REVIEW   what you do to finished work
    token reduction                          throughout, not as a step

ARCHITECT and REVIEW are the two new ones and they sit at the two ends of the
work for a reason. Architecture is the decision that is expensive to reverse, so
it goes before anything is produced; a plan for the wrong shape is a plan to
build the wrong thing efficiently. Review goes last because the person best
placed to find the defect is the one who just wrote it, and by then they already
believe the work is right.

TOKEN REDUCTION IS NOT A STEP. It reads as one in a list, which is why it is
called out here: it applies at every retrieval, every catalog read and every long
output, not once at the end. Compressing a finished answer is the least valuable
place to do it, because the tokens were already spent getting there.

FOR EVERY MODEL, NOT A CLIENT. The chain is text, injected by whichever mechanism
the surface has: a hook where there is one, a system message through the proxy,
an argument or stdin through the wrapper, a pasted bundle for a browser product.
A local model behind Ollama and a hosted model behind a chat box get the same
chain, because the chain does not depend on any client feature.

COST. Every figure below states the input that produced it, because the previous
version did not and one of them turned out to be unreproducible: it published
"6452 bytes plus a standing goal" without saying which goal, and the goal text
is interpolated into the block, so the total moves with its length. Reproducing
6452 needed an undisclosed 52-character goal, and the harness's own --check
printed a different number for the same quantity.

Measured on the prompt "refactor the retry module and check it", which fires the
refactor lane:

    1912 bytes   the core, eleven rules in three layers
    2254 bytes   plus the matching lane
    4595 bytes   plus this chain
    + a goal      the goal block on top, whose size depends on the goal text

So the chain roughly DOUBLES the standing pipeline: 4595 over 2254 is 2.04x. An
earlier version of this docstring said "roughly three times", which was reached
by comparing the goal-carrying total against the base; the standing goal is a
separate opt-in and not part of the chain's cost, so that overstated it by about
half. A goal, when one is set, adds its block on top of all of this.

These numbers move whenever the core, a lane or the goal block changes, and they
have. Rather than trusting the table, print the real ones:

    python scripts/harness_super.py --check

which measures and reports the current figures for this machine, and

    python scripts/harness_super.py --context "<your prompt>" | wc -c

which gives the exact bytes that prompt would carry, goal included.

It is the trade: more passes named explicitly, paid every turn. Use the surface
harness when that price is not worth it, which is most short tasks. Use this one
for work that spans turns, where the cost of the model forgetting the chain is
larger than the cost of carrying it.

The chain itself is about 2.3 kB of that. It was 4.3 kB in the first version,
which restated seven rules the core already carries; those seven now point at
their rule number instead. Same ten passes, same order, one copy of each rule.

Usage:
    python scripts/harness_super.py --check
    python scripts/harness_super.py --context "refactor the retry module"
    python scripts/harness_super.py --install all
    python scripts/harness_super.py --install all --dry-run
    python scripts/harness_super.py --bundle chatgpt
    python scripts/harness_super.py --goal "finish the designs"
    python scripts/harness_super.py --show-goal
    python scripts/harness_super.py --clear-goal
    python scripts/harness_super.py --route browser-js
    python scripts/harness_super.py --serve --port 11500
    python scripts/harness_super.py --run -- ollama run qwen3:4b "plan a page"
"""
from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "hooks"))

import skill_pipeline  # noqa: E402
import auto_mode_harness as surface  # noqa: E402
import harness_goal as goal  # noqa: E402
import harness_proxy as proxy  # noqa: E402
import harness_wrap as wrap  # noqa: E402
import harness_computer as computer  # noqa: E402

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
EXTRA_SKILLS = ("master-architect", "master-review")

SUPER_BLOCK = """SUPER HARNESS. The chain above is the floor. These passes run on top of it, in this order, on every prompt and every command.

{passes}

TOKEN REDUCTION is not a step in this list even though it appears as one. It applies at every retrieval, every catalog read and every long output. Compressing a finished answer is the least valuable place to do it: the tokens were already spent getting there.

ARCHITECT is before producing and REVIEW is after, on purpose. A plan for the wrong shape builds the wrong thing efficiently, and the person best placed to find the defect is the one who just wrote it and already believes it is right.

NAME the skills, tools, plugins and MCP servers you used. A pass you did not name is a pass the reader cannot check."""


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


def context_for(prompt: str, session: str | None = None,
                capturing: bool = True) -> str:
    """The full super-harness context for one prompt.

    Base pipeline first, then the standing goal, then this chain. The order is
    the argument: the base layers say how any turn is done, the goal says what
    the session is for, and the chain says which named passes this harness adds.
    Reversing it would put the additions in front of the floor they extend.

    `capturing=False` renders without setting the goal, for the commands that
    exist to SHOW what a prompt would receive.
    """
    base = goal.context_for(prompt, session, capturing)
    return base + "\n\n" + super_block()


def missing_skills() -> list[str]:
    """Enforced skills plus this harness's own, that are not on disk."""
    names = list(surface.ENFORCED_SKILLS) + list(EXTRA_SKILLS)
    return [name for name in names
            if not surface.harness_paths.skill_path(name).is_file()]


def check() -> int:
    """Verify without changing what is being verified.

    Rendering the chain captures a goal from the fixture prompt, so this runs
    against an isolated store for the same reason every other harness check
    does: a verifier that changes the thing it verifies is not a verifier.
    """
    with skill_pipeline.isolated_store():
        return _check_isolated()


def _check_isolated() -> int:
    failures = []

    base = skill_pipeline.context_for("Plan and design a settings page.")
    for marker in ("LAYER 1", "LAYER 2", "LAYER 3"):
        if marker not in base:
            failures.append(f"the base pipeline is missing {marker}")
    print(f"base pipeline     {len(base.encode('utf-8'))} bytes, all three layers")

    block = super_block()
    for label, skill, _base, _when, _rule in PASSES:
        if label not in block:
            failures.append(f"the chain is missing the {label} pass")
        if skill not in block:
            failures.append(f"the {label} pass does not name a skill")
    added = [p for p in PASSES if p[2] is None]
    print(f"chain             {len(PASSES)} passes, {len(added)} adding a rule, "
          f"{len(PASSES) - len(added)} pointing at the base")

    # A pass claiming to extend rule N has to point at a rule that exists, and a
    # pass adding a rule must not restate one the base already carries. The
    # first version of this chain restated seven, which read fine and cost
    # 4.3 kB a prompt to carry two copies of the standing pipeline.
    import re as _re
    base_numbers = {int(m) for m in _re.findall(r"^(\d+)\. ", skill_pipeline.CORE,
                                                _re.MULTILINE)}
    for label, skill, base_rule, _when, rule in PASSES:
        if base_rule is not None and base_rule not in base_numbers:
            failures.append(f"the {label} pass points at rule {base_rule}, which is not in the core")
        if base_rule is None and label in skill_pipeline.CORE:
            failures.append(f"the {label} pass restates a rule the core already carries")
        if base_rule is None and not rule:
            failures.append(f"the {label} pass adds nothing and points at nothing")

    # Every pass must name a skill that exists. A chain that points at a missing
    # skill reads exactly like one that works, right up to the moment a model
    # tries to load it.
    for label, skill, _base, _when, _rule in PASSES:
        if not surface.harness_paths.skill_path(skill).is_file():
            failures.append(f"the {label} pass names {skill}, which is not on disk")
    gone = missing_skills()
    if gone:
        failures.append("skills missing: " + ", ".join(gone))
    total = len(surface.ENFORCED_SKILLS) + len(EXTRA_SKILLS)
    print(f"skills            {total - len(gone)} of {total} present")

    full = context_for("Refactor the retry module and check it.", capturing=False)
    if not full.startswith(base.split("\n")[0]):
        failures.append("the base pipeline is not first in the super context")
    if full.index("LAYER 1") > full.index("SUPER HARNESS"):
        failures.append("the chain comes before the layers it extends")
    print(f"super context     {len(full.encode('utf-8'))} bytes for one prompt")

    # It has to actually do what the other four do, or the claim is false.
    delegations = {
        "install": hasattr(surface, "install_surfaces"),
        "repo files": hasattr(surface, "install_repo_instructions"),
        "bundle": hasattr(surface, "write_bundles"),
        "goal": hasattr(goal, "set_goal") and hasattr(skill_pipeline, "clear_goal"),
        "proxy": hasattr(proxy, "inject") and hasattr(proxy, "Handler"),
        "wrapper": hasattr(wrap, "build") and hasattr(wrap, "PROFILES"),
        "computer": hasattr(computer, "ROUTES"),
    }
    for name, present in delegations.items():
        if not present:
            failures.append(f"cannot delegate {name}; the underlying harness moved")
    print(f"delegates to      {len(delegations)} capabilities of the other harnesses")

    # The proxy and wrapper must carry THE CHAIN, not just the base pipeline.
    # They did not, at first. Both spawn as subprocesses, so rebinding a context
    # function in this process reached nothing, and "does what the others do and
    # more" was true of the doing and false of the more. Each now takes --super.
    # Checked here in-process through the same seam the flag flips.
    original_proxy, original_wrap = proxy.CONTEXT, wrap.CONTEXT
    try:
        proxy.use_super_context()
        wrap.use_super_context()
        proxied, _ = proxy.inject({"model": "m", "messages": [
            {"role": "user", "content": "refactor the loader and review it"}]})
        served = proxied["messages"][0]["content"]
        wrapped = wrap.rules_for("refactor the loader and review it")
        for name, text in (("proxy", served), ("wrapper", wrapped)):
            if "LAYER 1" not in text:
                failures.append(f"the {name} does not carry the base pipeline")
            if "SUPER HARNESS" not in text:
                failures.append(f"the {name} does not carry the chain")
            for label in ("ARCHITECT", "REVIEW"):
                if label not in text:
                    failures.append(f"the {name} is missing the {label} pass")
    finally:
        proxy.CONTEXT, wrap.CONTEXT = original_proxy, original_wrap
    print(f"proxy and wrapper  both carry the chain, {len(served)} and {len(wrapped)} bytes")

    # The flag has to be on the argv this file actually builds, or the check
    # above passes in-process while the real subprocess sends the base only.
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    for target in ('"--super", "--port"', '"--super", "--profile"'):
        if target not in source:
            failures.append(f"the subprocess argv is missing {target}")
    print("subprocess argv    passes --super to both")

    if failures:
        print("\nFAILED", file=sys.stderr)
        for line in failures:
            print("  " + line, file=sys.stderr)
        return 1
    print("\nsuper harness ready; it installs, serves, wraps, carries the goal and routes")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true",
                        help="verify the chain, the skills and every delegation")
    parser.add_argument("--context", metavar="PROMPT",
                        help="print exactly what this harness would inject; sets nothing")
    parser.add_argument("--chain", action="store_true",
                        help="print the pass chain on its own")
    parser.add_argument("--install", metavar="SURFACES",
                        help="install hooks, skills and instruction files, all surfaces")
    parser.add_argument("--bundle", metavar="SURFACES",
                        help="write the paste bundle for a surface with no hook")
    parser.add_argument("--goal", metavar="TEXT", help="set the standing goal")
    parser.add_argument("--show-goal", action="store_true", help="print the standing goal")
    parser.add_argument("--clear-goal", action="store_true", help="lift the standing goal")
    parser.add_argument("--route", metavar="ROUTE",
                        help="computer-control route: native, browser-js or browser-rust")
    parser.add_argument("--serve", action="store_true", help="run the injecting proxy")
    parser.add_argument("--port", type=int, default=11500)
    parser.add_argument("--upstream", default="http://127.0.0.1:11434")
    parser.add_argument("--run", action="store_true",
                        help="wrap the command after --, e.g. --run -- ollama run qwen3:4b \"...\"")
    parser.add_argument("--profile", default="generic", help="wrapper profile for --run")
    parser.add_argument("--out", default="dist/auto-mode")
    parser.add_argument("--dry-run", action="store_true")
    # Split on the first standalone "--" BEFORE argparse sees it. REMAINDER was
    # the obvious way to do this and it does not work: argparse consumes the
    # separator itself, so `--run -- python -c "..."` came back as unrecognized
    # arguments and the wrapper never ran. Splitting first is unambiguous and
    # leaves the wrapped command untouched, quotes and flags included.
    argv = sys.argv[1:]
    command: list[str] = []
    if "--" in argv:
        cut = argv.index("--")
        argv, command = argv[:cut], argv[cut + 1:]
    args = parser.parse_args(argv)

    if args.check:
        return check()

    if args.chain:
        print(super_block())
        return 0

    if args.context is not None:
        print(context_for(args.context, capturing=False))
        return 0

    if args.goal:
        data = goal.set_goal(args.goal)
        print(f"goal set: {data['goal']}")
        print("it now rides every prompt, through all five harnesses.")
        return 0

    if args.show_goal:
        data = skill_pipeline.load_goal()
        print(f"goal: {data.get('goal') or 'none set'}")
        return 0

    if args.clear_goal:
        skill_pipeline.clear_goal()
        print("goal cleared. The layers and the chain still apply.")
        return 0

    if args.install:
        hooked = surface.resolve(args.install, mechanisms=(surface.HOOK,))
        committed = surface.resolve(args.install, mechanisms=(surface.REPO_FILE,))
        status = surface.install_surfaces(hooked, args.dry_run) if hooked else 0
        for line in surface.install_repo_files(committed, args.dry_run):
            print(line)
        for line in surface.install_repo_instructions(args.dry_run):
            print(line)
        for line in surface.install_project_files(args.dry_run):
            print(line)
        return status

    if args.bundle:
        ids = surface.resolve(args.bundle,
                              mechanisms=(surface.BUNDLE, surface.REPO_FILE))
        for line in surface.write_bundles(ids, pathlib.Path(args.out), args.dry_run):
            print(line)
        return 0

    if args.route:
        return computer.main_route(args.route) if hasattr(computer, "main_route") else _route(args.route)

    if args.serve:
        return _serve(args.port, args.upstream)

    if args.run:
        return _run(args.profile, command)

    parser.print_help()
    return 2


def _route(route: str) -> int:
    """Delegate to the computer router without reimplementing its probes."""
    argv = surface.harness_paths.harness_command("harness_computer") + ["--route", route]
    import subprocess
    return subprocess.run(argv, cwd=surface.harness_paths.work_dir()).returncode


def _serve(port: int, upstream: str) -> int:
    argv = surface.harness_paths.harness_command("harness_proxy") + [
        "--super", "--port", str(port), "--upstream", upstream]
    import subprocess
    return subprocess.run(argv, cwd=surface.harness_paths.work_dir()).returncode


def _run(profile: str, command: list[str]) -> int:
    """Wrap one invocation, with the chain in front of the prompt.

    `command` is everything after the first standalone "--", already separated
    in main() so argparse never touches it.
    """
    if not command:
        print("nothing to run after --run", file=sys.stderr)
        return 2
    prompt = command[-1]
    argv = surface.harness_paths.harness_command("harness_wrap") + [
        "--super", "--profile", profile, "--prompt", prompt, "--"] + command
    import subprocess
    return subprocess.run(argv, cwd=surface.harness_paths.work_dir()).returncode


if __name__ == "__main__":
    raise SystemExit(main())

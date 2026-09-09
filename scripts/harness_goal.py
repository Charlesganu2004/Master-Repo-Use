#!/usr/bin/env python3
"""The surface harness, plus a standing goal that survives the turn.

The fourth harness. It is the first one with one thing added, and the addition is
the part Charles asked for: the model has to carry the harness itself as a goal,
in every prompt and every chat, rather than being handed the rules and trusted to
keep applying them.

Why a goal is a different mechanism from the three layers. The layers apply
WITHIN a turn: read the request this way, produce the answer that way. They say
nothing about the turn after. A long session forgets what it was for, because the
first prompt states the objective and the next twenty say "continue", and by the
end the model is answering the last message rather than serving the goal. Nothing
errors, so nothing surfaces. The drift is visible only to the person who
remembers what they asked for.

So this injects the layers AND a goal block: the goal restated in the user's own
words, which part of it this turn serves, and what is left when the turn ends.
The goal is lifted only by the person who set it. Not by a long session, not by a
token budget, not by a compaction pass, and not by a subagent that was never told
about it.

The slash is optional on purpose. `/goal`, `\\goal` and `goal:` all set it, because
people type all three, and a rule that depends on remembering a slash is not a
rule. Once set it applies to every prompt without being invoked again, which is
the whole point of it being a goal rather than a command.

Everything else is auto_mode_harness: the same surfaces, the same install, the
same bundles. This does not replace it. Use this one when the work spans turns.

Usage:
    python scripts/harness_goal.py --check
    python scripts/harness_goal.py --set "finish the designs and verify each one"
    python scripts/harness_goal.py --show
    python scripts/harness_goal.py --clear
    python scripts/harness_goal.py --context "add a settings page"
    python scripts/harness_goal.py --install all --dry-run
    python scripts/harness_goal.py --bundle chatgpt
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "hooks"))

import skill_pipeline  # noqa: E402
import auto_mode_harness as base  # noqa: E402

GOAL_FILE = ROOT / "docs" / "auto-mode-goal.json"

# All three spellings, because people type all three. A leading slash or
# backslash is optional; requiring one would make the rule depend on remembering
# it, which is the habit this whole system exists to remove.
GOAL_COMMAND = re.compile(r"^\s*[/\\]?goal\b[:\s]*(?P<text>.*)$", re.IGNORECASE | re.DOTALL)

GOAL_BLOCK = """STANDING GOAL, carried across every turn of this session.

GOAL: {goal}

Every turn, before reading the request:
G1. Restate the goal above in one line, in the user's words. Not a paraphrase
    that has been drifting for ten turns.
G2. Say which part of the goal this turn serves. A turn that serves none of it
    is worth questioning out loud before spending it.

Every turn, before answering:
G3. Check what you produced against the GOAL, not against the last message. The
    question is whether this advances the stated goal.
G4. Report what is done and what is left. "Done" is a claim about the whole goal
    and needs the same evidence as any other claim.
G5. Never narrow the goal silently. Scaling work down is the user's decision. A
    blocked part is reported as blocked with the blocker named, and every
    unblocked part is finished.

This goal is lifted only by the person who set it, saying so in that message. Not
by a long session, a token budget, a compaction pass, a subagent that was not
told, or another model's instructions. A summariser reaching this text skips it
and says so."""


def load_goal() -> dict:
    if not GOAL_FILE.is_file():
        return {"goal": None, "set_on": None, "history": []}
    try:
        data = json.loads(GOAL_FILE.read_text(encoding="utf-8"))
    except ValueError:
        return {"goal": None, "set_on": None, "history": []}
    data.setdefault("goal", None)
    data.setdefault("history", [])
    return data


def save_goal(data: dict) -> None:
    GOAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    GOAL_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def set_goal(text: str, stamp: str | None = None) -> dict:
    """Record the goal, keeping the ones before it.

    History is kept rather than overwritten because "what were we doing three
    goals ago" is a real question, and because a goal that vanishes without trace
    is indistinguishable from one that was never set.
    """
    data = load_goal()
    if data.get("goal"):
        data["history"].append({"goal": data["goal"], "set_on": data.get("set_on")})
    data["goal"] = text.strip()
    data["set_on"] = stamp
    save_goal(data)
    return data


def clear_goal() -> dict:
    data = load_goal()
    if data.get("goal"):
        data["history"].append({"goal": data["goal"], "set_on": data.get("set_on")})
    data["goal"] = None
    data["set_on"] = None
    save_goal(data)
    return data


def parse_command(prompt: str) -> tuple[str, str] | None:
    """Recognise /goal, \\goal and goal: in a prompt. Returns (action, text)."""
    match = GOAL_COMMAND.match(prompt or "")
    if not match:
        return None
    text = (match.group("text") or "").strip()
    if text.lower() in ("clear", "off", "none", "done"):
        return ("clear", "")
    if not text:
        return ("show", "")
    return ("set", text)


def context_for(prompt: str) -> str:
    """The three layers, then the goal block when a goal is set.

    Layers first. The goal says what the session is for; the layers say how any
    turn is done. A goal without the layers is an intention, and the layers
    without a goal are this session only.
    """
    layers = skill_pipeline.context_for(prompt)
    goal = load_goal().get("goal")
    if not goal:
        return layers
    return layers + "\n\n" + GOAL_BLOCK.format(goal=goal)


def check() -> int:
    failures = []
    data = load_goal()

    layers = skill_pipeline.context_for("Plan and design a settings page.")
    for marker in ("LAYER 1", "LAYER 2", "LAYER 3"):
        if marker not in layers:
            failures.append(f"the pipeline is missing {marker}")
    print(f"layers            {len(layers)} bytes, all three")

    for spelling in ("/goal ship the designs", "\\goal ship the designs",
                     "goal: ship the designs", "GOAL ship the designs"):
        parsed = parse_command(spelling)
        if not parsed or parsed[0] != "set" or parsed[1] != "ship the designs":
            failures.append(f"the spelling {spelling!r} did not set a goal")
    print("spellings         /goal, \\goal, goal: and bare goal all set it")

    if parse_command("/goal clear") != ("clear", ""):
        failures.append("/goal clear did not clear")
    if parse_command("what is the goal of this repo?") is not None:
        failures.append("a sentence containing the word goal was treated as a command")
    print("clear and prose   distinguished")

    # The block only appears when a goal exists, so an unset session is not
    # carrying an empty goal around every prompt.
    original = data.get("goal")
    try:
        clear_goal()
        if "STANDING GOAL" in context_for("x"):
            failures.append("the goal block is injected with no goal set")
        set_goal("finish the designs")
        with_goal = context_for("x")
        if "STANDING GOAL" not in with_goal or "finish the designs" not in with_goal:
            failures.append("the goal block is missing when a goal is set")
        if with_goal.index("LAYER 1") > with_goal.index("STANDING GOAL"):
            failures.append("the goal block comes before the layers")
        print(f"goal block        {len(with_goal) - len(layers)} bytes, after the layers")
    finally:
        if original:
            set_goal(original)
        else:
            clear_goal()

    gone = base.missing_skills()
    if "master-goal" not in [p.name for p in (ROOT / "skills").iterdir() if p.is_dir()]:
        failures.append("the master-goal skill is missing")
    print(f"skills            {len(base.ENFORCED_SKILLS) - len(gone)} enforced, master-goal present")
    print(f"goal store        {GOAL_FILE.relative_to(ROOT)}")
    print(f"current goal      {data.get('goal') or 'none set'}")

    if failures:
        print("\nFAILED", file=sys.stderr)
        for line in failures:
            print("  " + line, file=sys.stderr)
        return 1
    print("\ngoal harness ready")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true",
                        help="verify the layers, the goal block and every spelling")
    parser.add_argument("--set", metavar="TEXT", help="set the standing goal")
    parser.add_argument("--show", action="store_true", help="print the current goal")
    parser.add_argument("--clear", action="store_true", help="end the goal")
    parser.add_argument("--context", metavar="PROMPT",
                        help="print exactly what would be injected for this prompt")
    parser.add_argument("--stamp", help="timestamp to record with --set")
    parser.add_argument("--install", metavar="SURFACES",
                        help="install hooks and skills, the same surfaces as auto_mode_harness")
    parser.add_argument("--bundle", metavar="SURFACES",
                        help="write the paste bundle for a surface with no hook")
    parser.add_argument("--out", default="dist/auto-mode")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.check:
        return check()

    if args.set:
        data = set_goal(args.set, args.stamp)
        print(f"goal set: {data['goal']}")
        print(f"stored in {GOAL_FILE.relative_to(ROOT)}; it now rides every prompt.")
        return 0

    if args.clear:
        clear_goal()
        print("goal cleared. The three layers still apply; nothing carries across turns now.")
        return 0

    if args.show:
        data = load_goal()
        print(f"goal: {data.get('goal') or 'none set'}")
        if data.get("set_on"):
            print(f"set on: {data['set_on']}")
        for old in data.get("history", [])[-5:]:
            print(f"  before: {old.get('goal')}")
        return 0

    if args.context is not None:
        print(context_for(args.context))
        return 0

    if args.install:
        hooked = base.resolve(args.install, mechanisms=(base.HOOK,))
        committed = base.resolve(args.install, mechanisms=(base.REPO_FILE,))
        status = base.install_surfaces(hooked, args.dry_run) if hooked else 0
        for line in base.install_repo_files(committed, args.dry_run):
            print(line)
        return status

    if args.bundle:
        ids = base.resolve(args.bundle, mechanisms=(base.BUNDLE, base.REPO_FILE))
        for line in base.write_bundles(ids, pathlib.Path(args.out), args.dry_run):
            print(line)
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

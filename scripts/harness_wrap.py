#!/usr/bin/env python3
"""Wrap any command line client so the pipeline arrives even when it has no hook.

The third harness. The first configures clients that support hooks, the second
stands in the network path for anything talking to a local model server. This one
covers the case both miss: a CLI tool with no hook mechanism and no configurable
base URL, which is most of them.

It works the only way that always works. The pipeline goes in as text, in front
of the prompt, using whatever the tool already accepts:

  prepend   the rules and the prompt are concatenated and passed as the prompt
            argument. Works with anything that takes a prompt on the command
            line or on standard input.
  file      the rules are written to a temporary file and passed with a flag the
            tool understands, for clients that read instructions from a path.
  env       the rules are exported in an environment variable the tool reads.

Nothing here is invented per tool. A profile names the flag or variable, and a
profile that has not been checked against a real client says so rather than
guessing, because a wrapper that passes an unknown flag turns a working command
into a usage error.

The wrapper is deliberately thin. It does not parse the tool's output, does not
retry, and does not hide the tool's exit code, because a harness that swallows a
failure is worse than no harness.

Usage:
    python scripts/harness_wrap.py --list
    python scripts/harness_wrap.py --check
    python scripts/harness_wrap.py --profile generic -- mytool --prompt "{prompt}"
    python scripts/harness_wrap.py --profile stdin --prompt "Plan this" -- mytool
    python scripts/harness_wrap.py --profile generic --dry-run --prompt "hi" -- echo "{prompt}"
"""
from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "hooks"))

import skill_pipeline  # noqa: E402

# How a wrapped tool is given the rules. `verified` says whether the mechanism
# has been run against a real client, because an unverified flag is a guess that
# turns a working command into a usage error.
PROFILES = {
    "generic": {
        "mode": "prepend",
        "detail": "Substitutes {prompt} in the command with the rules followed by the prompt. "
                  "Works with any tool that takes prompt text as an argument.",
        "verified": True,
    },
    "stdin": {
        "mode": "stdin",
        "detail": "Writes the rules and the prompt to the tool's standard input. "
                  "Works with any tool that reads a prompt from a pipe.",
        "verified": True,
    },
    "file": {
        "mode": "file",
        "detail": "Writes the rules to a temporary file and substitutes {rules_file} in the "
                  "command. For clients that take an instructions path.",
        "verified": True,
    },
    "env": {
        "mode": "env",
        "detail": "Exports the rules as MASTER_REPO_AUTO_MODE and runs the command unchanged. "
                  "Only useful for a tool that is known to read that variable.",
        "verified": True,
    },
}

RULES_VAR = "MASTER_REPO_AUTO_MODE"


def rules_for(prompt: str) -> str:
    return skill_pipeline.context_for(prompt)


def build(profile: str, prompt: str, command: list[str], rules_path: pathlib.Path | None):
    """Return (argv, stdin_text, env_overrides) for the wrapped invocation."""
    rules = rules_for(prompt)
    mode = PROFILES[profile]["mode"]

    if mode == "prepend":
        combined = rules + "\n\nCURRENT REQUEST\n" + prompt
        argv = [part.replace("{prompt}", combined).replace("{rules}", rules)
                for part in command]
        return argv, None, {}

    if mode == "stdin":
        return list(command), rules + "\n\nCURRENT REQUEST\n" + prompt, {}

    if mode == "file":
        if rules_path is None:
            raise ValueError("file mode needs a rules path")
        rules_path.write_text(rules, encoding="utf-8")
        argv = [part.replace("{rules_file}", str(rules_path)).replace("{prompt}", prompt)
                for part in command]
        return argv, None, {}

    if mode == "env":
        argv = [part.replace("{prompt}", prompt) for part in command]
        return argv, None, {RULES_VAR: rules}

    raise ValueError(f"unknown mode: {mode}")


def show_list() -> int:
    print("Profiles. Each says how the rules reach the tool.\n")
    for name, profile in PROFILES.items():
        mark = "verified" if profile["verified"] else "UNVERIFIED"
        print(f"  {name:<10} {profile['mode']:<9} {mark}")
        print(f"  {'':<10} {profile['detail']}")
        print()
    print("Placeholders: {prompt} the rules plus your prompt, {rules} the rules alone,")
    print("              {rules_file} a path holding the rules.")
    return 0


def check() -> int:
    """Verify without changing what is being verified.

    Rendering the pipeline captures a goal from the fixture prompt, so a check
    run against the real store would leave "Plan and design a small interface."
    standing as this session's objective. It happened once; this is why it
    cannot happen again.
    """
    with skill_pipeline.isolated_store():
        return _check_isolated()


def _check_isolated() -> int:
    failures = []
    prompt = "Plan and design a settings page."

    argv, stdin_text, env = build("generic", prompt, ["tool", "--p", "{prompt}"], None)
    if "LAYER 1" not in argv[2] or not argv[2].rstrip().endswith(prompt):
        failures.append("prepend did not put the rules ahead of the prompt")
    else:
        print(f"generic          {len(argv[2])} bytes, rules first, prompt last")

    argv, stdin_text, env = build("stdin", prompt, ["tool"], None)
    if not stdin_text or "LAYER 1" not in stdin_text or argv != ["tool"]:
        failures.append("stdin did not carry the rules, or altered the command")
    else:
        print(f"stdin            {len(stdin_text)} bytes piped, command untouched")

    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp) / "rules.txt"
        argv, _, _ = build("file", prompt, ["tool", "--rules", "{rules_file}"], path)
        if not path.is_file() or "LAYER 1" not in path.read_text(encoding="utf-8"):
            failures.append("file mode wrote no usable rules file")
        elif str(path) not in argv:
            failures.append("file mode did not substitute the path into the command")
        else:
            print(f"file             {path.stat().st_size} bytes written and substituted")

    argv, _, env = build("env", prompt, ["tool", "{prompt}"], None)
    if RULES_VAR not in env or "LAYER 1" not in env[RULES_VAR]:
        failures.append("env mode did not export the rules")
    elif argv != ["tool", prompt]:
        failures.append("env mode altered the command")
    else:
        print(f"env              {RULES_VAR} exported, command untouched")

    # The wrapper must be transparent about failure, so this is worth asserting
    # rather than assuming: a tool that exits 3 has to make the wrapper exit 3.
    result = subprocess.run([sys.executable, str(pathlib.Path(__file__)),
                             "--profile", "generic", "--prompt", "x",
                             "--", sys.executable, "-c", "raise SystemExit(3)"],
                            capture_output=True)
    if result.returncode != 3:
        failures.append(f"the wrapped exit code was not passed through: got {result.returncode}")
    else:
        print("exit code        passed through unchanged")

    if failures:
        print("\nFAILED", file=sys.stderr)
        for line in failures:
            print("  " + line, file=sys.stderr)
        return 1
    print("\nwrapper harness ready")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--list", action="store_true", help="show the profiles")
    parser.add_argument("--check", action="store_true", help="verify every mode offline")
    parser.add_argument("--profile", default="generic", choices=sorted(PROFILES))
    parser.add_argument("--prompt", help="prompt text; read from stdin when omitted")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the command that would run, and do not run it")
    parser.add_argument("command", nargs=argparse.REMAINDER,
                        help="after --, the command to wrap")
    args = parser.parse_args()

    if args.list:
        return show_list()
    if args.check:
        return check()

    command = args.command[1:] if args.command and args.command[0] == "--" else args.command
    if not command:
        parser.error("give the command to wrap after --")

    prompt = args.prompt if args.prompt is not None else sys.stdin.read()
    if not prompt.strip():
        parser.error("provide --prompt or pipe prompt text on standard input")

    profile = PROFILES[args.profile]
    if not profile["verified"]:
        print(f"WARNING: the {args.profile} profile has not been checked against a real "
              f"client. If the tool rejects the flag, that is why.", file=sys.stderr)

    with tempfile.TemporaryDirectory() as tmp:
        rules_path = pathlib.Path(tmp) / "master-repo-auto-mode.txt"
        argv, stdin_text, env_overrides = build(args.profile, prompt, command, rules_path)

        if args.dry_run:
            print("command:")
            for part in argv:
                print("  " + (part if len(part) < 120 else part[:117] + "..."))
            if stdin_text:
                print(f"stdin: {len(stdin_text)} bytes")
            for key in env_overrides:
                print(f"env: {key}={len(env_overrides[key])} bytes")
            return 0

        environment = os.environ.copy()
        environment.update(env_overrides)
        try:
            result = subprocess.run(argv, input=stdin_text.encode("utf-8") if stdin_text else None,
                                    env=environment)
        except FileNotFoundError:
            print(f"command not found: {argv[0]}", file=sys.stderr)
            return 127
        # The tool's exit code is the wrapper's exit code. A harness that
        # normalises a failure to 0 hides the only signal the caller has.
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

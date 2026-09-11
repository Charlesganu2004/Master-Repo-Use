#!/usr/bin/env python3
"""Measure what the super harness changes: the same prompt, with and without it.

Two arms, one prompt, the same model:

    without    the model gets the prompt and nothing else from this repository
    with       the model gets the super harness context first: the layers, the
               chain, and the goal and token limit if set

Two modes:

    --measure  no model at all. The exact bytes each arm would inject, from the
               real context functions, with a token ESTIMATE labelled as one.
               Runs anywhere, always, and is what the numbers in the docs cite.

    --run      calls a real model twice and records what actually came back:
               input and output tokens as the API reports them, cost, time, and
               measurable features of each response. Uses the Claude Code CLI on
               your logged-in account (backend "claude"), or the Anthropic API
               when ANTHROPIC_API_KEY is set (backend "api").

THE BASELINE HAS TO BE CLEAN, and that is the hard part. On a machine with the
harness installed, a plain `claude -p` gets the pipeline from the global hook and
the managed block from ~/.claude/CLAUDE.md, so the "without" arm is secretly
"with". The CLI backend therefore runs both arms from an empty temporary
directory with only project settings loaded and every tool disallowed, and it
PROBES first: it asks the baseline arm whether it can see the pipeline's own
words. If it can, the run stops and says so rather than reporting a comparison
between two harnessed arms as if one were bare.

What the response features measure is deliberately simple and countable: em
dashes, code blocks, whether tests appear, whether a plan is stated, length. A
feature list is not a quality verdict. Read both responses; the numbers say
where to look.

Usage:
    python scripts/harness_ab_test.py --measure
    python scripts/harness_ab_test.py --measure --prompt "your prompt"
    python scripts/harness_ab_test.py --run --out docs/ab-tests
    python scripts/harness_ab_test.py --run --backend api --model claude-sonnet-5
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "hooks"))

import skill_pipeline  # noqa: E402
import harness_super  # noqa: E402

DEFAULT_PROMPT = ("Write a Python function that parses a human duration string such as "
                  "'1h30m', '45s' or '2d4h' into a number of seconds. Reject malformed "
                  "input with a clear error. Include unit tests.")

HARDER_PROMPT = ("Implement a thread-safe sliding-window rate limiter in Python that "
                 "allows N requests per T seconds per key. Include unit tests, one of "
                 "which exercises concurrent callers, then write a three-sentence note "
                 "on why you chose the data structure, and finish by listing any edge "
                 "case you did not handle.")

# A rough rule of thumb for English prose and code, used ONLY by --measure and
# labelled as an estimate wherever it appears. --run replaces it with the counts
# the API actually reports.
BYTES_PER_TOKEN_ESTIMATE = 4.0

PROBE = ("Answer with exactly one word, YES or NO: does any text you were given "
         "before this message contain the phrase 'Standing pipeline' or 'THREE LAYERS'?")

CLI_TOOLS = "Bash,Read,Write,Edit,MultiEdit,Glob,Grep,WebFetch,WebSearch,Task,Agent,NotebookEdit,TodoWrite"


# ------------------------------------------------------------------ measuring
def arm_contexts(prompt: str) -> dict[str, str]:
    """What each arm injects ahead of the prompt, rendered by the real code.

    Rendered inside an isolated store so measuring never sets a goal or a limit
    on this machine, and never reads the one that happens to be standing.
    """
    with skill_pipeline.isolated_store():
        return {
            "without": "",
            "base": skill_pipeline.context_for(prompt, capturing=False, mode="base"),
            "super": harness_super.context_for(prompt, capturing=False),
        }


def measure(prompt: str) -> dict:
    contexts = arm_contexts(prompt)
    prompt_bytes = len(prompt.encode("utf-8"))
    arms = {}
    for name, context in contexts.items():
        injected = len(context.encode("utf-8"))
        arms[name] = {
            "injectedBytes": injected,
            "totalInputBytes": injected + prompt_bytes,
            "estimatedInputTokens": round((injected + prompt_bytes) / BYTES_PER_TOKEN_ESTIMATE),
        }
    return {
        "prompt": prompt,
        "promptBytes": prompt_bytes,
        "arms": arms,
        "note": ("estimatedInputTokens is bytes / 4, a rule of thumb and NOT a "
                 "tokenizer count. --run reports what the API actually counted."),
    }


# ------------------------------------------------------------ response features
def features(text: str) -> dict:
    """Countable properties of a response. Not a quality score."""
    lowered = text.lower()
    return {
        "chars": len(text),
        "words": len(text.split()),
        "emDashes": text.count("—"),
        "codeBlocks": text.count("```") // 2,
        "hasTests": bool(re.search(r"\bdef test_|\bassert\b|unittest|pytest", text)),
        "statesPlan": bool(re.search(r"\b(plan|approach|steps?)\b\s*[:\n]", lowered)),
        "namesSkills": bool(re.search(r"master-[a-z-]+|verify-before-complete", lowered)),
        "statesWhatIsLeft": bool(re.search(r"(not handled|did not handle|left out|remaining|limitations?)", lowered)),
    }


# --------------------------------------------------------------- backends
class BackendUnavailable(RuntimeError):
    pass


def claude_cli() -> str:
    for candidate in (shutil.which("claude"),
                      str(pathlib.Path.home() / ".local" / "bin" / "claude.exe"),
                      str(pathlib.Path.home() / ".local" / "bin" / "claude")):
        if candidate and pathlib.Path(candidate).is_file():
            return candidate
    raise BackendUnavailable("the Claude Code CLI is not installed")


def run_cli(prompt: str, system: str, model: str | None, workdir: pathlib.Path) -> dict:
    """One isolated `claude -p` call. Returns usage, cost, time and text."""
    command = [claude_cli(), "-p", prompt, "--output-format", "json",
               "--setting-sources", "project", "--disallowedTools", CLI_TOOLS]
    if system:
        command += ["--append-system-prompt", system]
    if model:
        command += ["--model", model]
    started = time.time()
    proc = subprocess.run(command, cwd=workdir, capture_output=True, text=True,
                          timeout=600, encoding="utf-8")
    try:
        data = json.loads(proc.stdout)
    except ValueError:
        raise BackendUnavailable(f"the CLI returned no JSON: {proc.stderr[-300:] or proc.stdout[-300:]}")
    if data.get("is_error"):
        message = str(data.get("result", ""))
        if "authenticate" in message.lower() or "oauth" in message.lower():
            raise BackendUnavailable(f"{message}. Run `claude auth login` in a terminal, then retry.")
        raise BackendUnavailable(message)
    usage = data.get("usage", {})
    return {
        "inputTokens": usage.get("input_tokens", 0),
        "cacheCreationTokens": usage.get("cache_creation_input_tokens", 0),
        "cacheReadTokens": usage.get("cache_read_input_tokens", 0),
        "outputTokens": usage.get("output_tokens", 0),
        "costUsd": data.get("total_cost_usd"),
        "seconds": round(time.time() - started, 1),
        "text": data.get("result", ""),
    }


def run_api(prompt: str, system: str, model: str | None, workdir: pathlib.Path) -> dict:
    """One Messages API call. Exact usage, no CLI system prompt in either arm."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise BackendUnavailable("ANTHROPIC_API_KEY is not set")
    body = {"model": model or "claude-sonnet-5", "max_tokens": 4000,
            "messages": [{"role": "user", "content": prompt}]}
    if system:
        body["system"] = system
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=json.dumps(body).encode("utf-8"),
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            data = json.load(response)
    except urllib.error.HTTPError as problem:
        raise BackendUnavailable(f"API HTTP {problem.code}: {problem.read()[:300]!r}")
    usage = data.get("usage", {})
    text = "".join(part.get("text", "") for part in data.get("content", [])
                   if part.get("type") == "text")
    return {
        "inputTokens": usage.get("input_tokens", 0),
        "cacheCreationTokens": usage.get("cache_creation_input_tokens", 0),
        "cacheReadTokens": usage.get("cache_read_input_tokens", 0),
        "outputTokens": usage.get("output_tokens", 0),
        "costUsd": None,
        "seconds": round(time.time() - started, 1),
        "text": text,
    }


BACKENDS = {"claude": run_cli, "api": run_api}


def run(prompt: str, backend: str, model: str | None) -> dict:
    call = BACKENDS[backend]
    contexts = arm_contexts(prompt)
    with tempfile.TemporaryDirectory(prefix="harness-ab-") as tmp:
        workdir = pathlib.Path(tmp)
        # The probe. A "without" arm that can see the pipeline is not a baseline,
        # and a comparison built on it would publish two harnessed runs as one
        # bare and one harnessed. Only the CLI backend can leak like this; the
        # raw API has nothing injected unless we send it.
        if backend == "claude":
            answer = call(PROBE, "", model, workdir)["text"].strip().upper()
            if not answer.startswith("NO"):
                raise BackendUnavailable(
                    f"the baseline is NOT clean: it answered {answer[:20]!r} to the "
                    "probe, so the harness is reaching it through a global hook or "
                    "~/.claude/CLAUDE.md. Use --backend api with ANTHROPIC_API_KEY "
                    "for a clean baseline.")
        arms = {}
        for name in ("without", "super"):
            result = call(prompt, contexts[name], model, workdir)
            result["features"] = features(result["text"])
            result["injectedBytes"] = len(contexts[name].encode("utf-8"))
            arms[name] = result
    return {
        "prompt": prompt,
        "backend": backend,
        "model": model or "default",
        "ranAt": datetime.datetime.now().isoformat(timespec="seconds"),
        "probe": "clean" if backend == "claude" else "not needed (raw API)",
        "arms": arms,
    }


def summary_lines(result: dict) -> list[str]:
    a, b = result["arms"]["without"], result["arms"]["super"]
    rows = [("input tokens", a["inputTokens"], b["inputTokens"]),
            ("output tokens", a["outputTokens"], b["outputTokens"]),
            ("em dashes", a["features"]["emDashes"], b["features"]["emDashes"]),
            ("code blocks", a["features"]["codeBlocks"], b["features"]["codeBlocks"]),
            ("tests present", a["features"]["hasTests"], b["features"]["hasTests"]),
            ("states a plan", a["features"]["statesPlan"], b["features"]["statesPlan"]),
            ("names what is left", a["features"]["statesWhatIsLeft"], b["features"]["statesWhatIsLeft"]),
            ("seconds", a["seconds"], b["seconds"])]
    lines = [f"{'':<20}{'without':>12}{'super':>12}"]
    lines += [f"{label:<20}{str(x):>12}{str(y):>12}" for label, x, y in rows]
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--measure", action="store_true", help="bytes per arm, no model")
    parser.add_argument("--run", action="store_true", help="call a real model twice")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--harder", action="store_true", help="use the harder prompt")
    parser.add_argument("--backend", choices=sorted(BACKENDS), default="claude")
    parser.add_argument("--model")
    parser.add_argument("--out", metavar="DIR", help="write result JSON (and the responses) here")
    args = parser.parse_args()
    prompt = HARDER_PROMPT if args.harder else args.prompt

    if args.measure:
        result = measure(prompt)
        print(f"prompt: {prompt}\n")
        print(f"{'arm':<10}{'injected bytes':>16}{'input bytes':>14}{'est. tokens':>14}")
        for name, arm in result["arms"].items():
            print(f"{name:<10}{arm['injectedBytes']:>16,}{arm['totalInputBytes']:>14,}"
                  f"{arm['estimatedInputTokens']:>14,}")
        print(f"\n{result['note']}")
        if args.out:
            out = pathlib.Path(args.out)
            out.mkdir(parents=True, exist_ok=True)
            (out / "measure.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return 0

    if args.run:
        try:
            result = run(prompt, args.backend, args.model)
        except BackendUnavailable as problem:
            print(f"cannot run the live comparison: {problem}", file=sys.stderr)
            return 3
        for line in summary_lines(result):
            print(line)
        if args.out:
            out = pathlib.Path(args.out)
            out.mkdir(parents=True, exist_ok=True)
            stamp = result["ranAt"].replace(":", "")
            (out / f"ab-{stamp}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print(f"\nwritten to {out / f'ab-{stamp}.json'}")
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

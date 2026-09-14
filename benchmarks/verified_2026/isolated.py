"""Opt-in, audited generation set. The legacy coding command remains closed."""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import random
import shutil
import subprocess
import time
from datetime import datetime, timezone

from .audit import digest
from .run import HERE, capture, extract_answer, isolated_env, usage_metrics
from .tasks import ARMS, TASKS

SENTINEL = "__benchmark_no_tools__"
CEILING = 16


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def invocation(cli, prompt, cell):
    return [
        str(cli), "--available-tools", SENTINEL,
        "--allow-all-tools", "--disable-builtin-mcps",
        "--disable-mcp-server", "playwright", "--disable-mcp-server", "rustwright",
        "--no-custom-instructions", "--no-auto-update", "--no-ask-user",
        "--no-experimental", "--no-bash-env", "--model", "claude-sonnet-5",
        "--output-format", "json", "--stream", "off",
        "--usage-output-file", str(cell / "usage.json"),
        "--log-dir", str(cell / "logs"), "-p", prompt,
    ]


def validate_invocation(argv):
    required = invocation("cli", "prompt", pathlib.Path("cell"))[1:]
    variable_flags = {"--usage-output-file", "--log-dir", "-p"}
    for index, value in enumerate(required):
        if index and required[index - 1] in variable_flags:
            continue
        if index + 1 >= len(argv) or argv[index + 1] != value:
            raise ValueError("Unisolated invocation rejected before execution")
    if len(argv) != len(required) + 1:
        raise ValueError("Unexpected arguments rejected before execution")


def observe(events):
    inventories = [
        event["data"].get("servers")
        for event in events if event.get("type") == "session.mcp_servers_loaded"
    ]
    active = None
    if inventories and all(isinstance(items, list) for items in inventories):
        active = sum(server.get("status") != "disabled"
                     for items in inventories for server in items)
    return {
        "model_call_start_events": sum(e.get("type") == "model.call_start" for e in events),
        "tool_calls": sum(e.get("type") == "tool.execution_start" for e in events),
        "subagents": sum(e.get("type") == "subagent.started" for e in events),
        "active_mcp_servers": active,
        "mcp_inventory": inventories,
    }


def audit(events, usage, argv, *, exit_code=0, timed_out=False):
    validate_invocation(argv)
    result = observe(events)
    models = usage.get("modelMetrics", {}) if isinstance(usage, dict) else {}
    counts = [model.get("requests", {}).get("count") for model in models.values()]
    finalized = sum(counts) if counts and all(type(n) is int and n >= 0 for n in counts) else None
    result["finalized_requests"] = finalized
    result["control_valid"] = (
        exit_code == 0 and not timed_out and finalized == 1
        and result["model_call_start_events"] == 1
        and result["tool_calls"] == 0 and result["subagents"] == 0
        and result["active_mcp_servers"] == 0
        and set(models) == {"claude-sonnet-5"}
    )
    result["validity_reason"] = (
        "One observed start and finalized request; zero tool calls, subagents and active MCP servers"
        if result["control_valid"] else
        "Isolation/accounting gate failed; no further invocation is permitted"
    )
    return result


def headroom(ledger):
    if any(not entry.get("audit", {}).get("control_valid") for entry in ledger):
        raise ValueError("Unfinished or invalid prior invocation: spend is not safe to extend")
    spent = sum(entry["audit"]["finalized_requests"] for entry in ledger)
    if spent >= CEILING:
        raise ValueError("Finalized-request ceiling reached")
    return CEILING - spent


def response_contract(raw):
    messages = []
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "assistant.message":
            messages.append(event.get("data", {}).get("content"))
    if not messages or not isinstance(messages[-1], str):
        return False
    try:
        answer = json.loads(messages[-1])
    except json.JSONDecodeError:
        return False
    return (isinstance(answer, dict) and set(answer) == {"solution", "tests", "explanation"}
            and all(isinstance(value, str) for value in answer.values()))


def stop_owned_process(process):
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True, timeout=15, check=True,
        )
    else:
        import signal
        os.killpg(process.pid, signal.SIGKILL)
    process.wait(timeout=15)


def run_one(output, cli, prompt, *, task="complex", arm="bare", timeout=240):
    """One invocation only. No retry, automatic continuation or hidden batch."""
    if timeout <= 0 or timeout > 300:
        raise ValueError("Per-invocation timeout must be between 1 and 300 seconds")
    output.mkdir(parents=True, exist_ok=True)
    lock = output / "run.lock"
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    try:
        ledger_path = output / "generation-ledger.json"
        ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else []
        headroom(ledger)
        if any(row["task"] == task and row["arm"] == arm for row in ledger):
            raise ValueError("This cell was already attempted; automatic retries are prohibited")
        cell = output / f"{len(ledger) + 1:02d}-{task}-{arm}"
        cell.mkdir()
        env = isolated_env(cell, inherit_auth=True)
        for key in list(env):
            if key.startswith("COPILOT_") and key not in ("COPILOT_HOME", "COPILOT_AUTO_UPDATE"):
                env.pop(key)
        config = {"disableAllHooks": True, "continueOnAutoMode": False,
                  "ide": {"autoConnect": False}, "model": "claude-sonnet-5"}
        for name in ("config.json", "settings.json"):
            save(pathlib.Path(env["COPILOT_HOME"]) / name, config)
        cwd = cell / "fixture"
        cwd.mkdir()
        (cell / "prompt.txt").write_text(prompt, encoding="utf-8")
        argv = invocation(cli, prompt, cell)
        validate_invocation(argv)
        entry = {"task": task, "arm": arm, "at": datetime.now(timezone.utc).isoformat(),
                 "status": "started", "argv": argv, "timeout_seconds": timeout,
                 "prompt_sha256": digest(prompt.encode()), "cli_sha256": digest(cli.read_bytes())}
        ledger.append(entry)
        save(ledger_path, ledger)
        events, pending = [], b""
        start = time.perf_counter()
        timed_out, stop_reason = False, None
        stdout_path, stderr_path = cell / "stdout.jsonl", cell / "stderr.txt"
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            process = subprocess.Popen(
                argv, cwd=cwd, env=env, stdout=stdout, stderr=stderr,
                start_new_session=os.name != "nt",
            )
            entry["pid"] = process.pid
            save(ledger_path, ledger)
            try:
                with stdout_path.open("rb") as reader:
                    while True:
                        pending += reader.read()
                        lines = pending.split(b"\n")
                        pending = lines.pop()
                        for line in lines:
                            try:
                                events.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
                        live = observe(events)
                        if (live["model_call_start_events"] > 1 or live["tool_calls"]
                                or live["subagents"] or live["active_mcp_servers"]):
                            stop_reason = "Live isolation violation; owned process tree terminated"
                            stop_owned_process(process)
                        if process.poll() is not None:
                            break
                        if time.perf_counter() - start > timeout:
                            timed_out = True
                            stop_reason = "Per-invocation timeout; no retry"
                            stop_owned_process(process)
                            break
                        time.sleep(0.1)
            finally:
                stop_owned_process(process)
        events = []
        for line in stdout_path.read_bytes().splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        usage_path = cell / "usage.json"
        usage = json.loads(usage_path.read_text()) if usage_path.exists() else None
        outcome = audit(events, usage, argv, exit_code=process.returncode, timed_out=timed_out)
        entry.update(status="completed", audit=outcome, exit_code=process.returncode,
                     timed_out=timed_out, stop_reason=stop_reason,
                     seconds=time.perf_counter() - start)
        save(ledger_path, ledger)
        save(cell / "audit.json", entry)
        save(output / "execution-audit.json", {
            "set": "generation-set-2", "v1_finalized_requests": 28,
            "ceiling_including_canary": CEILING, "invocations": len(ledger),
            "finalized_requests": (
                sum(row["audit"]["finalized_requests"] for row in ledger)
                if all(row.get("audit", {}).get("finalized_requests") is not None for row in ledger)
                else None),
            "latest": outcome,
        })
        return entry
    finally:
        lock.unlink()


def score(output):
    """Evaluate saved synthetic answers offline; never issue a model request."""
    rows = []
    for cell in sorted(output.glob("[0-9][0-9]-*")):
        entry = json.loads((cell / "audit.json").read_text())
        row = {key: entry[key] for key in ("task", "arm", "seconds", "timed_out", "exit_code")}
        row.update(entry["audit"])
        usage_path = cell / "usage.json"
        if usage_path.exists():
            row.update(usage_metrics(json.loads(usage_path.read_text())))
        raw_text = (cell / "stdout.jsonl").read_text(encoding="utf-8")
        row["response_contract_valid"] = response_contract(raw_text)
        row["scoring_revision"] = "strict JSON-only response checked separately from recovered-code correctness"
        try:
            answer = extract_answer(raw_text)
        except ValueError as error:
            row["scoring_blocker"] = str(error)
        else:
            solution = cell / "solution.py"
            solution.write_text(answer["solution"], encoding="utf-8")
            if isinstance(answer.get("tests"), str):
                (cell / "agent_tests.py.txt").write_text(answer["tests"], encoding="utf-8")
            evaluation = capture(
                [os.sys.executable, str(HERE / "hidden.py"), entry["task"], str(solution)],
                cell, isolated_env(cell / "evaluation"), 30,
            )
            save(cell / "evaluation.json", evaluation)
            row["loc"] = len(answer["solution"].splitlines())
            try:
                row["correctness"] = json.loads(evaluation["stdout"])
            except json.JSONDecodeError:
                row["scoring_blocker"] = "Hidden evaluator emitted no complete JSON result"
        save(cell / "metrics.json", row)
        rows.append(row)
    save(output / "coding-runs.json", rows)
    return rows


def remaining(output, prompts, cli, *, timeout=240):
    """Continue a verified canary, stopping on the first invalid or unknown result."""
    ledger_path = output / "generation-ledger.json"
    ledger = json.loads(ledger_path.read_text())
    if not ledger or (ledger[0]["task"], ledger[0]["arm"]) != ("complex", "bare"):
        raise ValueError("The complex/bare canary must run and be reported first")
    headroom(ledger)
    attempted = {(row["task"], row["arm"]) for row in ledger}
    schedule = [(task, arm) for task in TASKS for arm in ARMS if (task, arm) not in attempted]
    random.Random(20260914).shuffle(schedule)
    save(output / "schedule.json", {"seed": 20260914, "remaining": schedule})
    for task, arm in schedule:
        result = run_one(
            output, cli, (prompts / task / f"{arm}.txt").read_text(encoding="utf-8"),
            task=task, arm=arm, timeout=timeout,
        )
        print(json.dumps({"task": task, "arm": arm, **result["audit"]}), flush=True)
        if not result["audit"]["control_valid"]:
            score(output)
            return False
        ledger = json.loads(ledger_path.read_text())
        if sum(row["audit"]["finalized_requests"] for row in ledger) > CEILING:
            raise RuntimeError("Finalized-request ceiling exceeded; batch aborted")
    score(output)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--cli", type=pathlib.Path, default=shutil.which("copilot"))
    parser.add_argument("--prompt", type=pathlib.Path, required=True)
    parser.add_argument("--task", choices=("complex", "super_complex"), default="complex")
    parser.add_argument("--arm", default="bare")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--authorize-one-invocation", action="store_true", required=True)
    args = parser.parse_args()
    if not args.cli or not args.cli.is_file():
        parser.error("An existing Copilot executable is required")
    result = run_one(args.output.resolve(), args.cli, args.prompt.read_text(encoding="utf-8"),
                     task=args.task, arm=args.arm, timeout=args.timeout)
    print(json.dumps(result["audit"], indent=2))
    return 0 if result["audit"]["control_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

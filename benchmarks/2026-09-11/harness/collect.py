"""Turn the workflow transcripts into per-run metrics. Every number is traced.

Sources, all written by the workflow runner, none by a model:

    <run>/journal.jsonl        label -> agent id, and each agent's return value
    <run>/agent-<id>.jsonl     the full transcript: every API response with its
                               usage, every tool call, timestamps

Tokens are counted once per API response. A response that holds thinking and a
tool call is written as several transcript lines that repeat its usage, with the
final output count on the last one, so summing lines would double count; this
groups by message id and keeps the last line of each.

Cost is computed from those counts at the published per-token prices below. It
is what the same traffic would cost on the API, not an invoice.

    python benchmarks/2026-09-11/harness/collect.py --coding <run dir> --browser <run dir>
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile
from datetime import datetime

BENCH = pathlib.Path(__file__).resolve().parents[1]
RESULTS = BENCH / "results"

# USD per million tokens, from platform.claude.com/docs/en/about-claude/pricing,
# read 2026-09-11. cw5m/cw1h are 5-minute and 1-hour cache writes.
PRICES = {
    "claude-sonnet-5": {"input": 2.00, "cw5m": 2.50, "cw1h": 4.00, "read": 0.20, "output": 10.00},
    "claude-opus-5": {"input": 5.00, "cw5m": 6.25, "cw1h": 10.00, "read": 0.50, "output": 25.00},
}


# ------------------------------------------------------------- transcripts
def journal(run: pathlib.Path) -> tuple[dict, dict]:
    labels, results = {}, {}
    for line in (run / "journal.jsonl").read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        if entry.get("type") == "started":
            labels[entry["label"]] = entry["agentId"]
        elif entry.get("type") == "result":
            results[entry["agentId"]] = entry.get("result")
    return labels, results


def transcript(path: pathlib.Path) -> dict:
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_id, order, tools, stamps, models = {}, [], {}, [], set()
    first_user = None
    for row in rows:
        if row.get("timestamp"):
            stamps.append(datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")))
        if row.get("type") == "user" and first_user is None:
            content = row["message"]["content"]
            first_user = content if isinstance(content, str) else "".join(
                block.get("text", "") for block in content if isinstance(block, dict))
        if row.get("type") != "assistant":
            continue
        message = row["message"]
        models.add(message.get("model"))
        if message["id"] not in by_id:
            order.append(message["id"])
        by_id[message["id"]] = message
        for block in message.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                tools[block["id"]] = {"name": block["name"], "input": block.get("input", {})}
    usage = {"input": 0, "cw5m": 0, "cw1h": 0, "read": 0, "output": 0}
    for message in by_id.values():
        u = message.get("usage") or {}
        created = u.get("cache_creation") or {}
        usage["input"] += u.get("input_tokens", 0)
        usage["read"] += u.get("cache_read_input_tokens", 0)
        usage["output"] += u.get("output_tokens", 0)
        if created:
            usage["cw5m"] += created.get("ephemeral_5m_input_tokens", 0)
            usage["cw1h"] += created.get("ephemeral_1h_input_tokens", 0)
        else:
            usage["cw5m"] += u.get("cache_creation_input_tokens", 0)
    model = sorted(m for m in models if m)[0] if models else "unknown"
    price = PRICES.get(model)
    cost = (sum(usage[k] * price[k] for k in usage) / 1e6) if price else None
    last = by_id[order[-1]] if order else {}
    final = "".join(b.get("text", "") for b in last.get("content") or []
                    if isinstance(b, dict) and b.get("type") == "text")
    # The last response's own output tokens: what a per-answer ceiling caps, as
    # distinct from everything the run emitted along the way.
    final_tokens = (last.get("usage") or {}).get("output_tokens", 0)
    first_call = by_id[order[0]].get("usage", {}) if order else {}
    return {
        "model": model,
        "tokens": usage,
        "tokensTotal": sum(usage.values()),
        "firstCallContext": (first_call.get("input_tokens", 0) + first_call.get("cache_read_input_tokens", 0)
                             + first_call.get("cache_creation_input_tokens", 0)),
        "costUsd": round(cost, 5) if cost is not None else None,
        "seconds": round((max(stamps) - min(stamps)).total_seconds(), 1) if stamps else None,
        "apiCalls": len(by_id),
        "toolCalls": len(tools),
        "toolNames": sorted({t["name"] for t in tools.values()}),
        "skillCalls": sum(1 for t in tools.values() if t["name"] == "Skill"),
        "fileToolCalls": sum(1 for t in tools.values() if t["name"] in ("Read", "Write", "Edit")),
        "bashInputs": [t["input"].get("command", "") for t in tools.values() if t["name"] == "Bash"],
        "firstUserSha256": hashlib.sha256((first_user or "").encode("utf-8")).hexdigest(),
        "finalText": final,
        "finalAnswerTokens": final_tokens,
    }


# -------------------------------------------------------------- answers
FENCE = re.compile(r"```(?:python|py)?[ \t]*\n(.*?)```", re.S)


def blocks(text: str) -> list[str]:
    return FENCE.findall(text or "")


def pick(text: str, marker: str, fallback: str) -> tuple[str, str]:
    found = blocks(text)
    for body in found:
        first = next((l.strip() for l in body.splitlines() if l.strip()), "")
        if first.lower().replace(" ", "") == f"#{marker}":
            return body, "marked"
    for body in found:
        if re.search(fallback, body):
            return body, "fallback"
    return "", "missing"


def sloc(code: str) -> int:
    """Lines that are code: not blank, not a comment, not a docstring."""
    doc_lines = set()
    try:
        for node in ast.walk(ast.parse(code)):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                body = getattr(node, "body", [])
                if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
                        and isinstance(body[0].value.value, str):
                    doc_lines.update(range(body[0].lineno, body[0].end_lineno + 1))
    except SyntaxError:
        pass
    return sum(1 for n, line in enumerate(code.splitlines(), 1)
               if line.strip() and not line.strip().startswith("#") and n not in doc_lines)


def prose(text: str) -> str:
    return re.sub(r"```.*?```", " ", text or "", flags=re.S)


def run_checks(task: str, solution: str, tests: str) -> dict:
    """Hidden tests and the answer's own tests, in a scratch directory outside
    the repository so nothing here is ever collected by the repo's pytest."""
    with tempfile.TemporaryDirectory(prefix="bench-check-") as tmp:
        work = pathlib.Path(tmp)
        (work / "solution.py").write_text(solution, encoding="utf-8")
        hidden = {"passed": 0, "total": None, "failures": ["no solution block"]}
        if solution:
            try:
                out = subprocess.run([sys.executable, str(BENCH / "hidden" / f"hidden_{task}.py"), str(work)],
                                     capture_output=True, text=True, timeout=180).stdout.strip().splitlines()
                hidden = json.loads(out[-1]) if out else {"passed": 0, "total": None, "failures": ["no output"]}
            except subprocess.TimeoutExpired:
                hidden = {"passed": 0, "total": None, "failures": ["hidden tests timed out"]}
        own = {"ran": False}
        if tests and solution:
            (work / "agent_tests.py").write_text(tests, encoding="utf-8")
            try:
                proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                                       "agent_tests.py"], cwd=work, capture_output=True, text=True, timeout=180)
                tail = (proc.stdout or "").strip().splitlines()[-1:] or [""]
                counts = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed|error|errors)", tail[0])}
                own = {"ran": True, "exit": proc.returncode, "passed": counts.get("passed", 0),
                       "failed": counts.get("failed", 0) + counts.get("error", 0) + counts.get("errors", 0),
                       "summary": tail[0][:160]}
            except subprocess.TimeoutExpired:
                own = {"ran": True, "exit": None, "passed": 0, "failed": 0, "summary": "timed out"}
    return {"hidden": hidden, "own": own}


# ----------------------------------------------------------------- coding
def collect_coding(run: pathlib.Path) -> list[dict]:
    manifest = json.loads((BENCH / "arms" / "manifest.json").read_text(encoding="utf-8"))
    labels, results = journal(run)
    judges = {}
    for label, agent_id in labels.items():
        if label.startswith("judge|"):
            _, task, arm, rep, which = label.split("|")
            judges.setdefault((task, arm, rep), []).append(results.get(agent_id))
    rows = []
    for label, agent_id in sorted(labels.items()):
        if not label.startswith("code|"):
            continue
        _, task, arm, rep = label.split("|")
        path = run / f"agent-{agent_id}.jsonl"
        if not path.exists():
            continue
        t = transcript(path)
        answer = t["finalText"] or (results.get(agent_id) or "")
        solution, how_s = pick(answer, "solution.py", r"def parse_duration|class RateLimiter")
        tests, how_t = pick(answer, "test_solution.py", r"import unittest|def test_|import pytest")
        checks = run_checks(task, solution, tests)
        js = [j for j in judges.get((task, arm, rep), []) if j]
        dims = ["correctness", "code_quality", "test_quality", "instruction_following", "communication", "overall"]
        judge_mean = {d: round(sum(j[d] for j in js) / len(js), 2) for d in dims} if js else {}
        out_dir = RESULTS / "coding" / task / arm / rep
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "answer.md").write_text(answer, encoding="utf-8")
        (out_dir / "solution.py.txt").write_text(solution, encoding="utf-8")
        (out_dir / "agent_tests.py.txt").write_text(tests, encoding="utf-8")
        text_prose = prose(answer)
        rows.append({
            "task": task, "arm": arm, "rep": rep, "agentId": agent_id,
            # Only a run the workflow recorded a result for is finished; a
            # transcript without one is still running or died, and is excluded
            # from every aggregate rather than counted as a zero.
            "completed": agent_id in results and bool(answer),
            "promptVerified": t["firstUserSha256"] == manifest["tasks"][task][arm]["sha256"],
            **{k: t[k] for k in ("model", "tokens", "tokensTotal", "firstCallContext", "costUsd",
                                 "seconds", "apiCalls", "toolCalls", "toolNames", "skillCalls",
                                 "fileToolCalls")},
            "solutionLoc": sloc(solution), "testLoc": sloc(tests),
            "extraction": {"solution": how_s, "tests": how_t},
            "answerChars": len(answer), "proseWords": len(text_prose.split()),
            "emDashes": answer.count("—"),
            "hidden": checks["hidden"], "ownTests": checks["own"],
            "judges": js, "judgeMean": judge_mean,
            "judgeCostUsd": round(sum((transcript(run / f"agent-{labels[l]}.jsonl")["costUsd"] or 0)
                                      for l in labels if l.startswith(f"judge|{task}|{arm}|{rep}|")
                                      and (run / f"agent-{labels[l]}.jsonl").exists()), 5),
        })
        print(f"{task} {arm:26} {rep} hidden {rows[-1]['hidden'].get('passed')}/{rows[-1]['hidden'].get('total')}"
              f" own {checks['own'].get('passed')}/{checks['own'].get('failed')} ${rows[-1]['costUsd']}"
              f" {rows[-1]['seconds']}s loc {rows[-1]['solutionLoc']} judge {judge_mean.get('overall')}"
              f" verified {rows[-1]['promptVerified']}")
    return rows


# ---------------------------------------------------------------- browser
def heredocs(command: str) -> list[str]:
    return re.findall(r"<<-?\s*'?EOF'?\s*\n(.*?)\nEOF", command, re.S)


def collect_browser(run: pathlib.Path) -> list[dict]:
    answers = json.loads((BENCH / "fixtures" / "answers.json").read_text(encoding="utf-8"))
    expected = {"lookup": ["1,066.33", "1066.33"], "count": [str(answers["count"]["count"])],
                "checkout": [answers["checkout"]["code"]]}
    labels, results = journal(run)
    rows = []
    for label, agent_id in sorted(labels.items()):
        if not label.startswith("browse|"):
            continue
        _, task, tool, rep = label.split("|")
        path = run / f"agent-{agent_id}.jsonl"
        if not path.exists():
            continue
        t = transcript(path)
        returned = results.get(agent_id)
        text = t["finalText"] or (returned if isinstance(returned, str) else "")
        line = next((l for l in reversed(text.splitlines()) if "ANSWER:" in l), "")
        answer = line.split("ANSWER:", 1)[-1].strip().strip("`*")
        if task == "count":
            correct = bool(re.fullmatch(r"\D*27\D*", answer))
        else:
            correct = any(e in answer for e in expected[task])
        scripts = [body for cmd in t["bashInputs"] for body in heredocs(cmd)]
        cli_calls = sum(cmd.count("caveman-browse.exe") for cmd in t["bashInputs"])
        # Some runs refused the task on the scaffold's read-only grounds without
        # touching the tool at all. That is the Explore agent profile talking,
        # not the browser tool, so it is counted separately rather than as a
        # failure of the tool under test.
        declined = t["toolCalls"] == 0 and bool(re.search(r"read-only|not authori[sz]ed|cannot perform", text, re.I))
        rows.append({
            "task": task, "tool": tool, "rep": rep, "agentId": agent_id, "answer": answer, "correct": correct,
            "completed": agent_id in results and bool(text), "declined": declined,
            **{k: t[k] for k in ("model", "tokens", "tokensTotal", "costUsd", "seconds", "apiCalls",
                                 "toolCalls", "skillCalls", "fileToolCalls")},
            "scriptLocTotal": sum(sloc(s) for s in scripts), "scripts": len(scripts),
            "cliCalls": cli_calls,
            "codeLines": (sum(sloc(s) for s in scripts) if tool != "caveman-browse" else cli_calls),
        })
        print(f"{task:9} {tool:15} {rep} ok={correct!s:5} ans={answer[:24]!r:28} ${t['costUsd']} {t['seconds']}s"
              f" tools {t['toolCalls']} code {rows[-1]['codeLines']}{' DECLINED' if declined else ''}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coding", type=pathlib.Path)
    parser.add_argument("--browser", type=pathlib.Path)
    args = parser.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    if args.coding:
        rows = collect_coding(args.coding)
        (RESULTS / "coding-runs.json").write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
        print(f"coding: {len(rows)} runs; prompts verified {sum(r['promptVerified'] for r in rows)}/{len(rows)}")
    if args.browser:
        rows = collect_browser(args.browser)
        (RESULTS / "browser-runs.json").write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
        print(f"browser: {len(rows)} runs; correct {sum(r['correct'] for r in rows)}/{len(rows)}")


if __name__ == "__main__":
    main()

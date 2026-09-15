"""Score the graphify experiment: correctness, the 400-token ceiling, and tool use.

Correctness is checked against ground truth taken from the graph itself, not from
an opinion: the hubs are whatever god-nodes reports, and the caller is whatever
the edges say. The ceiling is checked twice, because they are different claims:
the FINAL answer's own token count is what rule 15 caps, and the run's total
output tokens are what it costs.

    python benchmarks/2026-09-15/harness/collect.py --run <workflow run dir>
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import statistics
import sys

BENCH = pathlib.Path(__file__).resolve().parents[1]
ROOT = BENCH.parents[1]
sys.path.insert(0, str(ROOT / "benchmarks" / "2026-09-11" / "harness"))
from collect import journal, transcript  # noqa: E402  the transcript reader, unchanged

ARMS = ["bare_strict", "bare_nograph", "bare_graph", "base_graph", "super_graph"]
TASKS = ["g1", "g2"]
# An actual invocation, not the word. Counting the word marked the strict arm as
# having used graphify when every hit was a grep EXCLUDING graphify-out from its
# search (-g '!graphify-out/**'), which is the opposite of using it.
from graphify_use import INVOKES_GRAPHIFY  # noqa: E402  shared detector


def scored(task: str, truth: dict, answer: str) -> dict:
    """One point per expected fact actually present in the answer."""
    text = answer.replace("\\", "/")
    hits, misses = [], []
    for item in truth["expect"]:
        needed = [item["symbol"], pathlib.PurePosixPath(item["file"]).name]
        if "caller" in item:
            needed.append(item["caller"])
        if all(re.search(rf"\b{re.escape(part)}\b", text) for part in needed):
            hits.append("/".join(needed))
        else:
            misses.append("/".join(needed))
    return {"found": len(hits), "expected": len(truth["expect"]), "hits": hits, "missed": misses}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=pathlib.Path, required=True)
    args = parser.parse_args()
    config = json.loads((BENCH / "prompts" / "tasks.json").read_text(encoding="utf-8"))
    manifest = json.loads((BENCH / "arms" / "manifest.json").read_text(encoding="utf-8"))
    limit = config["limit"]
    labels, results = journal(args.run)
    rows = []
    for label, agent_id in sorted(labels.items()):
        if not label.startswith("ask|"):
            continue
        _, task, arm, rep = label.split("|")
        path = args.run / f"agent-{agent_id}.jsonl"
        if not path.exists():
            continue
        t = transcript(path)
        answer = t["finalText"] or (results.get(agent_id) if isinstance(results.get(agent_id), str) else "") or ""
        used_graphify = sum(1 for cmd in t["bashInputs"] if INVOKES_GRAPHIFY.search(cmd))
        rows.append({
            "task": task, "arm": arm, "rep": rep, "agentId": agent_id,
            "completed": agent_id in results and bool(answer),
            "promptVerified": t["firstUserSha256"] == manifest["tasks"][task][arm]["sha256"],
            "answerTokens": t["finalAnswerTokens"], "withinLimit": t["finalAnswerTokens"] <= limit,
            "outputTokens": t["tokens"]["output"], "tokensTotal": t["tokensTotal"],
            "costUsd": t["costUsd"], "seconds": t["seconds"], "apiCalls": t["apiCalls"],
            "toolCalls": t["toolCalls"], "graphifyCalls": used_graphify,
            "score": scored(task, config["tasks"][task]["truth"], answer),
            "answerChars": len(answer), "answer": answer,
        })
        out_dir = BENCH / "results" / "answers" / task / arm
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"r{rep}.md").write_text(answer, encoding="utf-8")
        r = rows[-1]
        print(f"{task} {arm:14} {rep} score {r['score']['found']}/{r['score']['expected']} "
              f"answer {r['answerTokens']:>4} tok {'ok' if r['withinLimit'] else 'OVER'} "
              f"graphify {used_graphify} tools {r['toolCalls']} ${r['costUsd']} {r['seconds']}s "
              f"verified {r['promptVerified']}")
    (BENCH / "results").mkdir(exist_ok=True)
    (BENCH / "results" / "runs.json").write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")

    summary = {}
    for task in TASKS:
        for arm in ARMS:
            cell = [r for r in rows if r["task"] == task and r["arm"] == arm and r["completed"]]
            if not cell:
                continue
            summary[f"{task}:{arm}"] = {
                "n": len(cell),
                "scoreRate": round(sum(r["score"]["found"] for r in cell)
                                   / sum(r["score"]["expected"] for r in cell), 3),
                "withinLimit": sum(r["withinLimit"] for r in cell),
                "answerTokens": statistics.median(r["answerTokens"] for r in cell),
                "maxAnswerTokens": max(r["answerTokens"] for r in cell),
                "costUsd": round(statistics.median(r["costUsd"] for r in cell), 5),
                "seconds": statistics.median(r["seconds"] for r in cell),
                "toolCalls": statistics.median(r["toolCalls"] for r in cell),
                "graphifyRuns": sum(1 for r in cell if r["graphifyCalls"] > 0),
            }
    (BENCH / "results" / "summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print()
    for key, cell in summary.items():
        print(f"{key:22} n={cell['n']} score {cell['scoreRate']:.0%} within400 {cell['withinLimit']}/{cell['n']} "
              f"median answer {cell['answerTokens']:.0f} tok (max {cell['maxAnswerTokens']}) "
              f"graphify used {cell['graphifyRuns']}/{cell['n']} ${cell['costUsd']:.4f} {cell['seconds']:.0f}s")


if __name__ == "__main__":
    main()

"""Score the 600-token kit runs from their transcripts.

Used when the kit is run through the Workflow tool rather than by pasting. For
pasted answers use score.py, which reads answers/ instead.

    python benchmarks/run-it-yourself/harness/collect.py --run <workflow run dir>
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import statistics
import sys

KIT = pathlib.Path(__file__).resolve().parents[1]
ROOT = KIT.parents[1]
sys.path.insert(0, str(ROOT / "benchmarks" / "2026-09-11" / "harness"))
from collect import journal, transcript  # noqa: E402

ARMS = ["bare_strict", "bare_graph", "base_graph", "super_graph"]
TASKS = ["complex", "super_complex"]
from graphify_use import INVOKES_GRAPHIFY  # noqa: E402  shared detector


def found(answer: str, item: dict) -> bool:
    text = answer.replace("\\", "/")
    parts = item.get("all") or item.get("any") or []
    test = all if "all" in item else any
    return test(re.search(rf"\b{re.escape(part)}\b", text) for part in parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=pathlib.Path, required=True)
    args = parser.parse_args()
    config = json.loads((KIT / "prompts" / "tasks.json").read_text(encoding="utf-8"))
    manifest = json.loads((KIT / "arms" / "manifest.json").read_text(encoding="utf-8"))
    limit = config["limit"]
    labels, results = journal(args.run)
    rows = []
    for label, agent_id in sorted(labels.items()):
        if not label.startswith("riy|"):
            continue
        _, task, arm, rep = label.split("|")
        path = args.run / f"agent-{agent_id}.jsonl"
        if not path.exists():
            continue
        t = transcript(path)
        returned = results.get(agent_id)
        answer = t["finalText"] or (returned if isinstance(returned, str) else "") or ""
        expect = config["tasks"][task]["truth"]["expect"]
        hits = [item["label"] for item in expect if found(answer, item)]
        rows.append({
            "task": task, "arm": arm, "rep": rep,
            "completed": agent_id in results and bool(answer),
            "promptVerified": t["firstUserSha256"] == manifest["tasks"][task][arm]["sha256"],
            "answerTokens": t["finalAnswerTokens"], "withinLimit": t["finalAnswerTokens"] <= limit,
            "costUsd": t["costUsd"], "seconds": t["seconds"], "toolCalls": t["toolCalls"],
            "graphifyCalls": sum(1 for c in t["bashInputs"] if INVOKES_GRAPHIFY.search(c)),
            "score": {"found": len(hits), "expected": len(expect),
                      "missed": [i["label"] for i in expect if i["label"] not in hits]},
            "answer": answer,
        })
        out = KIT / "results" / "answers" / task / arm
        out.mkdir(parents=True, exist_ok=True)
        (out / f"r{rep}.md").write_text(answer, encoding="utf-8")
        r = rows[-1]
        print(f"{task:14} {arm:12} {rep} {r['score']['found']}/{r['score']['expected']} facts  "
              f"{r['answerTokens']:>4} tok {'ok' if r['withinLimit'] else 'OVER'}  "
              f"graphify {r['graphifyCalls']}  ${r['costUsd']}  {r['seconds']}s  "
              f"verified {r['promptVerified']}")
    (KIT / "results").mkdir(exist_ok=True)
    (KIT / "results" / "runs.json").write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    done = [r for r in rows if r["completed"]]
    print(f"\n{len(done)}/{len(rows)} completed; prompts verified "
          f"{sum(r['promptVerified'] for r in rows)}/{len(rows)}")
    for task in TASKS:
        for arm in ARMS:
            cell = [r for r in done if r["task"] == task and r["arm"] == arm]
            if not cell:
                continue
            print(f"{task:14} {arm:12} n={len(cell)} "
                  f"facts {sum(r['score']['found'] for r in cell)}/{sum(r['score']['expected'] for r in cell)} "
                  f"within {sum(r['withinLimit'] for r in cell)}/{len(cell)} "
                  f"median {statistics.median(r['answerTokens'] for r in cell):.0f} tok "
                  f"${statistics.median(r['costUsd'] for r in cell):.4f} "
                  f"{statistics.median(r['seconds'] for r in cell):.0f}s")


if __name__ == "__main__":
    main()

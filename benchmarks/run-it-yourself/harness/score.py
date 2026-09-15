"""Score answers you collected yourself, against ground truth from this repository.

Save each answer as answers/<task>/<arm>.md (or .txt), then:

    python benchmarks/run-it-yourself/harness/score.py

It prints a table: which facts each answer got, whether it stayed inside the
600-token ceiling (counted as words times 1.33, which is an estimate and is
labelled as one), and writes results/scores.json.

Ground truth is not an opinion: the hubs come from the repository's graph, the
harness scripts from scripts/build_atlas_data.py, and the caller from the graph's
own edges. If you change the repository, rebuild the graph and the truth moves
with it.
"""
from __future__ import annotations

import json
import pathlib
import re

KIT = pathlib.Path(__file__).resolve().parents[1]
WORDS_PER_TOKEN = 0.75          # a rule of thumb, not a tokenizer


def found(answer: str, item: dict) -> bool:
    text = answer.replace("\\", "/")
    if "all" in item:
        return all(re.search(rf"\b{re.escape(part)}\b", text) for part in item["all"])
    return any(re.search(rf"\b{re.escape(part)}\b", text) for part in item["any"])


def main() -> None:
    config = json.loads((KIT / "prompts" / "tasks.json").read_text(encoding="utf-8"))
    limit = config["limit"]
    rows = []
    for task, spec in config["tasks"].items():
        for arm in config["arms"]:
            candidates = [KIT / "answers" / task / f"{arm}{suffix}" for suffix in (".md", ".txt")]
            path = next((c for c in candidates if c.exists()), None)
            if path is None:
                continue
            answer = path.read_text(encoding="utf-8", errors="replace")
            hits = [item["label"] for item in spec["truth"]["expect"] if found(answer, item)]
            missed = [item["label"] for item in spec["truth"]["expect"] if item["label"] not in hits]
            estimate = round(len(answer.split()) / WORDS_PER_TOKEN)
            rows.append({"task": task, "arm": arm, "found": len(hits), "expected": len(spec["truth"]["expect"]),
                         "missed": missed, "estimatedTokens": estimate, "withinLimit": estimate <= limit,
                         "file": str(path.relative_to(KIT))})
            print(f"{task:14} {arm:14} {len(hits)}/{len(spec['truth']['expect'])} facts  "
                  f"~{estimate:>4} tokens {'ok' if estimate <= limit else 'OVER ' + str(limit)}  "
                  f"missed: {', '.join(missed) if missed else 'nothing'}")
    if not rows:
        print("no answers found. Save them as answers/<task>/<arm>.md first, for example:")
        print("  benchmarks/run-it-yourself/answers/complex/super_graph.md")
        return
    out = KIT / "results"
    out.mkdir(exist_ok=True)
    (out / "scores.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"\nwritten to {out / 'scores.json'}")
    print("token counts are words / 0.75, an estimate. Your provider's usage page has the real number.")


if __name__ == "__main__":
    main()
